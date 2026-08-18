import os
import uuid
from pathlib import Path

from botocore.exceptions import BotoCoreError, ClientError

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user
from app.models import User, UserKYC

# IMPORTANT:
# Use the SAME spaces.py used by support tickets.
from app.utils.spaces import (
    s3_client,
    SPACES_BUCKET,
)


# ==========================================================
# ROUTER
# ==========================================================

router = APIRouter(
    prefix="/api/user/kyc",
    tags=["User KYC"],
)


# ==========================================================
# KYC SETTINGS
# ==========================================================

ALLOWED_DOCUMENT_TYPES = {
    "aadhaar",
    "pan",
    "passport",
    "bank_proof",
    "other",
}

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "application/pdf",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ==========================================================
# GET DATABASE USER
# ==========================================================

def get_database_user(
    current_user,
    db: Session,
) -> User:

    user = (
        db.query(User)
        .filter(
            User.user_id == current_user
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return user


# ==========================================================
# DELETE SPACES OBJECT
# ==========================================================

def delete_spaces_object(
    object_key: str,
):

    if not object_key:
        return

    try:

        s3_client.delete_object(
            Bucket=SPACES_BUCKET,
            Key=object_key,
        )

    except (
        BotoCoreError,
        ClientError,
    ) as exc:

        print(
            "Spaces delete error:",
            str(exc),
        )


# ==========================================================
# GENERATE PRESIGNED URL
# ==========================================================

def generate_presigned_url(
    object_key: str,
    expires_in: int = 300,
):

    if not object_key:
        return None

    try:

        return s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": SPACES_BUCKET,
                "Key": object_key,
            },
            ExpiresIn=expires_in,
        )

    except (
        BotoCoreError,
        ClientError,
    ) as exc:

        print(
            "Presigned URL error:",
            str(exc),
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to generate document URL.",
        )


# ==========================================================
# CREATE OBJECT KEY
# ==========================================================

def create_object_key(
    user_id: int,
    document_type: str,
    filename: str,
    side: str = "front",
):

    extension = Path(
        filename
    ).suffix.lower()

    if not extension:
        extension = ".bin"

    unique_filename = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    return (
        f"user_kyc/"
        f"{user_id}/"
        f"{document_type}/"
        f"{side}/"
        f"{unique_filename}"
    )


# ==========================================================
# VALIDATE FILE
# ==========================================================

async def validate_file(
    file: UploadFile,
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="File name is required.",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid file type. "
                "Only JPG, JPEG, PNG and PDF "
                "files are allowed."
            ),
        )

    file_data = await file.read()

    if not file_data:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    if len(file_data) > MAX_FILE_SIZE:

        raise HTTPException(
            status_code=400,
            detail="Maximum file size is 10 MB.",
        )

    return file_data


# ==========================================================
# UPLOAD FILE TO SPACES
# ==========================================================

def upload_to_spaces(
    object_key: str,
    file_data: bytes,
    content_type: str,
):

    try:

        s3_client.put_object(
            Bucket=SPACES_BUCKET,
            Key=object_key,
            Body=file_data,
            ContentType=content_type,
        )

    except (
        BotoCoreError,
        ClientError,
    ) as exc:

        print(
            "KYC Spaces upload error:",
            str(exc),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to upload KYC document.",
        )


# ==========================================================
# UPLOAD KYC
# ==========================================================

@router.post(
    "/upload",
)
async def upload_kyc_document(

    document_type: str = Form(...),

    # Aadhaar number
    aadhar_no: str | None = Form(None),

    # PAN number
    pan: str | None = Form(None),

    # Aadhaar front
    front_file: UploadFile | None = File(None),

    # Aadhaar back
    back_file: UploadFile | None = File(None),

    # Used for PAN / passport / bank proof / other
    file: UploadFile | None = File(None),

    current_user=Depends(
        get_current_user
    ),

    db: Session = Depends(get_db),
):

    # ======================================================
    # GET USER
    # ======================================================

    user = get_database_user(
        current_user=current_user,
        db=db,
    )

    # ======================================================
    # NORMALIZE DOCUMENT TYPE
    # ======================================================

    document_type = (
        document_type
        .strip()
        .lower()
    )

    if document_type == "aadhar":
        document_type = "aadhaar"

    if document_type == "bankproof":
        document_type = "bank_proof"

    # ======================================================
    # VALIDATE DOCUMENT TYPE
    # ======================================================

    if document_type not in ALLOWED_DOCUMENT_TYPES:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid document type. "
                "Allowed types: "
                "aadhaar, pan, passport, "
                "bank_proof, other"
            ),
        )

    # ======================================================
    # AADHAAR
    # ======================================================

    if document_type == "aadhaar":

        # --------------------------------------------------
        # AADHAAR NUMBER REQUIRED
        # --------------------------------------------------

        if not aadhar_no:

            raise HTTPException(
                status_code=400,
                detail="Aadhaar number is required.",
            )

        aadhar_no = (
            aadhar_no
            .replace(" ", "")
            .strip()
        )

        # --------------------------------------------------
        # VALIDATE AADHAAR NUMBER
        # --------------------------------------------------

        if (
            not aadhar_no.isdigit()
            or len(aadhar_no) != 12
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Aadhaar number must contain "
                    "exactly 12 digits."
                ),
            )

        # --------------------------------------------------
        # CHECK UNIQUE AADHAAR
        # --------------------------------------------------

        existing_user = (
            db.query(User)
            .filter(
                User.aadhar_no == aadhar_no,
                User.id != user.id,
            )
            .first()
        )

        if existing_user:

            raise HTTPException(
                status_code=400,
                detail=(
                    "This Aadhaar number is already "
                    "registered with another user."
                ),
            )

        # --------------------------------------------------
        # BOTH FILES REQUIRED
        # --------------------------------------------------

        if not front_file:

            raise HTTPException(
                status_code=400,
                detail="Aadhaar front image is required.",
            )

        if not back_file:

            raise HTTPException(
                status_code=400,
                detail="Aadhaar back image is required.",
            )

        # --------------------------------------------------
        # VALIDATE FRONT
        # --------------------------------------------------

        front_data = await validate_file(
            front_file
        )

        # --------------------------------------------------
        # VALIDATE BACK
        # --------------------------------------------------

        back_data = await validate_file(
            back_file
        )

        # --------------------------------------------------
        # CREATE OBJECT KEYS
        # --------------------------------------------------

        front_object_key = create_object_key(
            user_id=user.id,
            document_type="aadhaar",
            filename=front_file.filename,
            side="front",
        )

        back_object_key = create_object_key(
            user_id=user.id,
            document_type="aadhaar",
            filename=back_file.filename,
            side="back",
        )

        # --------------------------------------------------
        # UPLOAD FRONT
        # --------------------------------------------------

        upload_to_spaces(
            object_key=front_object_key,
            file_data=front_data,
            content_type=front_file.content_type,
        )

        # --------------------------------------------------
        # UPLOAD BACK
        # --------------------------------------------------

        try:

            upload_to_spaces(
                object_key=back_object_key,
                file_data=back_data,
                content_type=back_file.content_type,
            )

        except Exception:

            # If back upload fails,
            # remove already uploaded front.

            delete_spaces_object(
                front_object_key
            )

            raise

        # --------------------------------------------------
        # FIND EXISTING AADHAAR KYC
        # --------------------------------------------------

        existing_kyc = (
            db.query(UserKYC)
            .filter(
                UserKYC.user_id == user.id,
                UserKYC.document_type == "aadhaar",
            )
            .first()
        )

        # --------------------------------------------------
        # UPDATE USER AADHAAR
        # --------------------------------------------------

        user.aadhar_no = aadhar_no

        # --------------------------------------------------
        # UPDATE EXISTING KYC
        # --------------------------------------------------

        if existing_kyc:

            old_front_key = (
                existing_kyc.front_file_url
            )

            old_back_key = (
                existing_kyc.back_file_url
            )

            existing_kyc.front_file_name = (
                front_file.filename
            )

            existing_kyc.front_file_url = (
                front_object_key
            )

            existing_kyc.back_file_name = (
                back_file.filename
            )

            existing_kyc.back_file_url = (
                back_object_key
            )

            existing_kyc.status = "PENDING"

            existing_kyc.rejection_reason = None

            try:

                db.commit()
                db.refresh(existing_kyc)

            except Exception as exc:

                db.rollback()

                delete_spaces_object(
                    front_object_key
                )

                delete_spaces_object(
                    back_object_key
                )

                print(
                    "KYC database update error:",
                    str(exc),
                )

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Failed to update KYC document."
                    ),
                )

            # Delete old files
            if old_front_key:
                delete_spaces_object(
                    old_front_key
                )

            if old_back_key:
                delete_spaces_object(
                    old_back_key
                )

            return {
                "message": (
                    "Aadhaar documents uploaded "
                    "successfully."
                ),
                "kyc_id": existing_kyc.id,
                "document_type": "aadhaar",
                "aadhar_no": user.aadhar_no,
                "status": existing_kyc.status,
            }

        # --------------------------------------------------
        # CREATE NEW KYC
        # --------------------------------------------------

        kyc = UserKYC(
            user_id=user.id,
            document_type="aadhaar",

            front_file_name=front_file.filename,
            front_file_url=front_object_key,

            back_file_name=back_file.filename,
            back_file_url=back_object_key,

            status="PENDING",
            rejection_reason=None,
        )

        db.add(kyc)

        try:

            db.commit()
            db.refresh(kyc)

        except Exception as exc:

            db.rollback()

            delete_spaces_object(
                front_object_key
            )

            delete_spaces_object(
                back_object_key
            )

            print(
                "KYC database insert error:",
                str(exc),
            )

            raise HTTPException(
                status_code=500,
                detail="Failed to save KYC document.",
            )

        return {
            "message": (
                "Aadhaar documents uploaded "
                "successfully."
            ),
            "kyc_id": kyc.id,
            "document_type": "aadhaar",
            "aadhar_no": user.aadhar_no,
            "status": kyc.status,
        }

    # ======================================================
    # PAN
    # ======================================================

    if document_type == "pan":

        # --------------------------------------------------
        # PAN REQUIRED
        # --------------------------------------------------

        if not pan:

            raise HTTPException(
                status_code=400,
                detail="PAN number is required.",
            )

        pan = pan.strip().upper()

        # --------------------------------------------------
        # BASIC PAN VALIDATION
        # --------------------------------------------------

        import re

        if not re.fullmatch(
            r"[A-Z]{5}[0-9]{4}[A-Z]",
            pan,
        ):

            raise HTTPException(
                status_code=400,
                detail="Invalid PAN number.",
            )

        # --------------------------------------------------
        # CHECK PAN UNIQUE
        # --------------------------------------------------

        existing_user = (
            db.query(User)
            .filter(
                User.pan == pan,
                User.id != user.id,
            )
            .first()
        )

        if existing_user:

            raise HTTPException(
                status_code=400,
                detail=(
                    "This PAN number is already "
                    "registered with another user."
                ),
            )

        # --------------------------------------------------
        # FILE REQUIRED
        # --------------------------------------------------

        if not file:

            raise HTTPException(
                status_code=400,
                detail="PAN document is required.",
            )

        file_data = await validate_file(
            file
        )

        # --------------------------------------------------
        # CREATE OBJECT KEY
        # --------------------------------------------------

        object_key = create_object_key(
            user_id=user.id,
            document_type="pan",
            filename=file.filename,
            side="front",
        )

        # --------------------------------------------------
        # UPLOAD
        # --------------------------------------------------

        upload_to_spaces(
            object_key=object_key,
            file_data=file_data,
            content_type=file.content_type,
        )

        # --------------------------------------------------
        # FIND EXISTING KYC
        # --------------------------------------------------

        existing_kyc = (
            db.query(UserKYC)
            .filter(
                UserKYC.user_id == user.id,
                UserKYC.document_type == "pan",
            )
            .first()
        )

        # --------------------------------------------------
        # UPDATE USER PAN
        # --------------------------------------------------

        user.pan = pan

        # --------------------------------------------------
        # UPDATE EXISTING
        # --------------------------------------------------

        if existing_kyc:

            old_object_key = (
                existing_kyc.front_file_url
            )

            existing_kyc.front_file_name = (
                file.filename
            )

            existing_kyc.front_file_url = (
                object_key
            )

            existing_kyc.back_file_name = None
            existing_kyc.back_file_url = None

            existing_kyc.status = "PENDING"
            existing_kyc.rejection_reason = None

            try:

                db.commit()
                db.refresh(existing_kyc)

            except Exception as exc:

                db.rollback()

                delete_spaces_object(
                    object_key
                )

                print(
                    "PAN database update error:",
                    str(exc),
                )

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Failed to update PAN document."
                    ),
                )

            if old_object_key:
                delete_spaces_object(
                    old_object_key
                )

            return {
                "message": (
                    "PAN document uploaded successfully."
                ),
                "kyc_id": existing_kyc.id,
                "document_type": "pan",
                "pan": user.pan,
                "status": existing_kyc.status,
            }

        # --------------------------------------------------
        # CREATE NEW PAN KYC
        # --------------------------------------------------

        kyc = UserKYC(
            user_id=user.id,
            document_type="pan",

            front_file_name=file.filename,
            front_file_url=object_key,

            back_file_name=None,
            back_file_url=None,

            status="PENDING",
            rejection_reason=None,
        )

        db.add(kyc)

        try:

            db.commit()
            db.refresh(kyc)

        except Exception as exc:

            db.rollback()

            delete_spaces_object(
                object_key
            )

            print(
                "PAN database insert error:",
                str(exc),
            )

            raise HTTPException(
                status_code=500,
                detail="Failed to save PAN document.",
            )

        return {
            "message": (
                "PAN document uploaded successfully."
            ),
            "kyc_id": kyc.id,
            "document_type": "pan",
            "pan": user.pan,
            "status": kyc.status,
        }

    # ======================================================
    # OTHER DOCUMENT TYPES
    # ======================================================

    if not file:

        raise HTTPException(
            status_code=400,
            detail="Document file is required.",
        )

    file_data = await validate_file(
        file
    )

    object_key = create_object_key(
        user_id=user.id,
        document_type=document_type,
        filename=file.filename,
        side="front",
    )

    upload_to_spaces(
        object_key=object_key,
        file_data=file_data,
        content_type=file.content_type,
    )

    existing_kyc = (
        db.query(UserKYC)
        .filter(
            UserKYC.user_id == user.id,
            UserKYC.document_type == document_type,
        )
        .first()
    )

    if existing_kyc:

        old_object_key = (
            existing_kyc.front_file_url
        )

        existing_kyc.front_file_name = (
            file.filename
        )

        existing_kyc.front_file_url = (
            object_key
        )

        existing_kyc.back_file_name = None
        existing_kyc.back_file_url = None

        existing_kyc.status = "PENDING"
        existing_kyc.rejection_reason = None

        try:

            db.commit()
            db.refresh(existing_kyc)

        except Exception as exc:

            db.rollback()

            delete_spaces_object(
                object_key
            )

            print(
                "KYC database update error:",
                str(exc),
            )

            raise HTTPException(
                status_code=500,
                detail="Failed to update KYC document.",
            )

        if old_object_key:
            delete_spaces_object(
                old_object_key
            )

        return {
            "message": (
                f"{document_type} uploaded successfully."
            ),
            "kyc_id": existing_kyc.id,
            "document_type": document_type,
            "status": existing_kyc.status,
        }

    kyc = UserKYC(
        user_id=user.id,
        document_type=document_type,

        front_file_name=file.filename,
        front_file_url=object_key,

        back_file_name=None,
        back_file_url=None,

        status="PENDING",
        rejection_reason=None,
    )

    db.add(kyc)

    try:

        db.commit()
        db.refresh(kyc)

    except Exception as exc:

        db.rollback()

        delete_spaces_object(
            object_key
        )

        print(
            "KYC database insert error:",
            str(exc),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to save KYC document.",
        )

    return {
        "message": (
            f"{document_type} uploaded successfully."
        ),
        "kyc_id": kyc.id,
        "document_type": document_type,
        "status": kyc.status,
    }


# ==========================================================
# GET MY KYC DOCUMENTS
# ==========================================================

@router.get("")
def get_my_kyc(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    user = get_database_user(
        current_user=current_user,
        db=db,
    )

    documents = (
        db.query(UserKYC)
        .filter(
            UserKYC.user_id == user.id
        )
        .order_by(
            UserKYC.uploaded_at.desc()
        )
        .all()
    )

    response = []

    for kyc in documents:

        front_url = generate_presigned_url(
            kyc.front_file_url,
            expires_in=300,
        )

        back_url = None

        if kyc.back_file_url:

            back_url = generate_presigned_url(
                kyc.back_file_url,
                expires_in=300,
            )

        response.append(
            {
                "id": kyc.id,
                "user_id": kyc.user_id,
                "document_type": kyc.document_type,

                "front_file_name": (
                    kyc.front_file_name
                ),

                "back_file_name": (
                    kyc.back_file_name
                ),

                "aadhar_no": user.aadhar_no,
                "pan": user.pan,

                "status": kyc.status,
                "rejection_reason": (
                    kyc.rejection_reason
                ),

                "uploaded_at": kyc.uploaded_at,
                "updated_at": kyc.updated_at,

                "front_url": front_url,
                "back_url": back_url,

                "expires_in": 300,
            }
        )

    return response


# ==========================================================
# GET SINGLE KYC
# ==========================================================

@router.get("/{kyc_id}")
def get_kyc_document(
    kyc_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    user = get_database_user(
        current_user=current_user,
        db=db,
    )

    kyc = (
        db.query(UserKYC)
        .filter(
            UserKYC.id == kyc_id,
            UserKYC.user_id == user.id,
        )
        .first()
    )

    if not kyc:

        raise HTTPException(
            status_code=404,
            detail="KYC document not found.",
        )

    front_url = generate_presigned_url(
        kyc.front_file_url,
        expires_in=300,
    )

    back_url = None

    if kyc.back_file_url:

        back_url = generate_presigned_url(
            kyc.back_file_url,
            expires_in=300,
        )

    return {
        "id": kyc.id,
        "user_id": kyc.user_id,
        "document_type": kyc.document_type,

        "front_file_name": kyc.front_file_name,
        "back_file_name": kyc.back_file_name,

        "aadhar_no": user.aadhar_no,
        "pan": user.pan,

        "status": kyc.status,
        "rejection_reason": kyc.rejection_reason,

        "uploaded_at": kyc.uploaded_at,
        "updated_at": kyc.updated_at,

        "front_url": front_url,
        "back_url": back_url,

        "expires_in": 300,
    }


# ==========================================================
# VIEW KYC DOCUMENT
# ==========================================================

@router.get("/{kyc_id}/view")
def view_kyc_document(
    kyc_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    user = get_database_user(
        current_user=current_user,
        db=db,
    )

    kyc = (
        db.query(UserKYC)
        .filter(
            UserKYC.id == kyc_id,
            UserKYC.user_id == user.id,
        )
        .first()
    )

    if not kyc:

        raise HTTPException(
            status_code=404,
            detail="KYC document not found.",
        )

    front_url = generate_presigned_url(
        kyc.front_file_url,
        expires_in=300,
    )

    back_url = None

    if kyc.back_file_url:

        back_url = generate_presigned_url(
            kyc.back_file_url,
            expires_in=300,
        )

    return {
        "id": kyc.id,
        "document_type": kyc.document_type,

        "front_url": front_url,
        "back_url": back_url,

        "expires_in": 300,
    }


# ==========================================================
# DELETE KYC
# ==========================================================

@router.delete("/{kyc_id}")
def delete_kyc_document(
    kyc_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    user = get_database_user(
        current_user=current_user,
        db=db,
    )

    kyc = (
        db.query(UserKYC)
        .filter(
            UserKYC.id == kyc_id,
            UserKYC.user_id == user.id,
        )
        .first()
    )

    if not kyc:

        raise HTTPException(
            status_code=404,
            detail="KYC document not found.",
        )

    if kyc.status == "APPROVED":

        raise HTTPException(
            status_code=400,
            detail=(
                "Approved KYC documents "
                "cannot be deleted."
            ),
        )

    front_object_key = kyc.front_file_url
    back_object_key = kyc.back_file_url

    try:

        db.delete(kyc)
        db.commit()

    except Exception as exc:

        db.rollback()

        print(
            "KYC delete database error:",
            str(exc),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to delete KYC document.",
        )

    if front_object_key:

        delete_spaces_object(
            front_object_key
        )

    if back_object_key:

        delete_spaces_object(
            back_object_key
        )

    return {
        "message": (
            "KYC document deleted successfully."
        ),
        "kyc_id": kyc_id,
    }