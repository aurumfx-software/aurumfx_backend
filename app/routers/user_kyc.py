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

from app.utils.spaces import (
    s3_client,
    SPACES_BUCKET,
)


router = APIRouter(
    prefix="/api/user/kyc",
    tags=["User KYC"],
)


# ==========================================================
# SETTINGS
# ==========================================================

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "application/pdf",
}

MAX_FILE_SIZE = 10 * 1024 * 1024


# ==========================================================
# GET DATABASE USER
# ==========================================================

def get_database_user(
    current_user: str,
    db: Session,
) -> User:

    user = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    return user


# ==========================================================
# DELETE SPACES OBJECT
# ==========================================================

def delete_spaces_object(
    object_key: str | None,
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
            str(exc)
        )


# ==========================================================
# PRESIGNED URL
# ==========================================================

def generate_presigned_url(
    object_key: str | None,
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
            str(exc)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to generate document URL."
        )


# ==========================================================
# CREATE OBJECT KEY
# ==========================================================

def create_object_key(
    user_id: int,
    document_type: str,
    filename: str,
):

    extension = Path(
        filename
    ).suffix.lower()

    if not extension:
        extension = ".bin"

    unique_filename = (
        f"{uuid.uuid4().hex}{extension}"
    )

    return (
        f"user_kyc/"
        f"{user_id}/"
        f"{document_type}/"
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
            detail="File name is required."
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid file type. "
                "Only JPG, JPEG, PNG and PDF files "
                "are allowed."
            )
        )

    file_data = await file.read()

    if not file_data:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(file_data) > MAX_FILE_SIZE:

        raise HTTPException(
            status_code=400,
            detail="Maximum file size is 10 MB."
        )

    return file_data


# ==========================================================
# UPLOAD TO SPACES
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
            "Spaces upload error:",
            str(exc)
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to upload KYC document."
        )


# ==========================================================
# UPLOAD / UPDATE KYC
# ==========================================================

@router.post("/upload")
async def upload_kyc_document(
    # ======================================================
    # AADHAAR
    # ======================================================

    aadhar_no: str | None = Form(None),
    aadhar_front: UploadFile | None = File(None),
    aadhar_back: UploadFile | None = File(None),

    # ======================================================
    # PAN
    # ======================================================

    pan_no: str | None = Form(None),
    pan_image: UploadFile | None = File(None),

    # ======================================================
    # AUTH
    # ======================================================

    current_user: str = Depends(get_current_user),
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
    # GET EXISTING KYC
    # ======================================================

    kyc = (
        db.query(UserKYC)
        .filter(
            UserKYC.user_id == user.id
        )
        .first()
    )

    # ======================================================
    # CHECK WHETHER ANYTHING WAS PROVIDED
    # ======================================================

    has_aadhaar = any([
        aadhar_no,
        aadhar_front,
        aadhar_back,
    ])

    has_pan = any([
        pan_no,
        pan_image,
    ])

    if not has_aadhaar and not has_pan:
        raise HTTPException(
            status_code=400,
            detail=(
                "Please provide Aadhaar details "
                "or PAN details."
            )
        )

    # ======================================================
    # AADHAAR VALIDATION
    # ======================================================

    new_aadhar_front_key = None
    new_aadhar_back_key = None

    old_aadhar_front = None
    old_aadhar_back = None

    if has_aadhaar:

        if not aadhar_no:
            raise HTTPException(
                status_code=400,
                detail="Aadhaar number is required."
            )

        if not aadhar_front:
            raise HTTPException(
                status_code=400,
                detail="Aadhaar front document is required."
            )

        if not aadhar_back:
            raise HTTPException(
                status_code=400,
                detail="Aadhaar back document is required."
            )

        # --------------------------------------------------
        # NORMALIZE AADHAAR
        # --------------------------------------------------

        aadhar_no = (
            aadhar_no
            .replace(" ", "")
            .strip()
        )

        # --------------------------------------------------
        # VALIDATE AADHAAR
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
                )
            )

        # --------------------------------------------------
        # CHECK UNIQUE AADHAAR
        # --------------------------------------------------

        existing_aadhar = (
            db.query(UserKYC)
            .filter(
                UserKYC.aadhar_no == aadhar_no,
                UserKYC.user_id != user.id,
            )
            .first()
        )

        if existing_aadhar:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This Aadhaar number is already "
                    "registered with another user."
                )
            )

        # --------------------------------------------------
        # VALIDATE FRONT
        # --------------------------------------------------

        front_data = await validate_file(
            aadhar_front
        )

        # --------------------------------------------------
        # VALIDATE BACK
        # --------------------------------------------------

        back_data = await validate_file(
            aadhar_back
        )

        # --------------------------------------------------
        # CREATE OBJECT KEYS
        # --------------------------------------------------

        new_aadhar_front_key = create_object_key(
            user_id=user.id,
            document_type="aadhaar",
            filename=aadhar_front.filename,
        )

        new_aadhar_back_key = create_object_key(
            user_id=user.id,
            document_type="aadhaar",
            filename=aadhar_back.filename,
        )

        # --------------------------------------------------
        # UPLOAD FRONT
        # --------------------------------------------------

        upload_to_spaces(
            object_key=new_aadhar_front_key,
            file_data=front_data,
            content_type=aadhar_front.content_type,
        )

        # --------------------------------------------------
        # UPLOAD BACK
        # --------------------------------------------------

        try:

            upload_to_spaces(
                object_key=new_aadhar_back_key,
                file_data=back_data,
                content_type=aadhar_back.content_type,
            )

        except Exception:

            delete_spaces_object(
                new_aadhar_front_key
            )

            raise

        # --------------------------------------------------
        # SAVE OLD FILE KEYS
        # --------------------------------------------------

        if kyc:

            old_aadhar_front = kyc.aadhar_front
            old_aadhar_back = kyc.aadhar_back

    # ======================================================
    # PAN VALIDATION
    # ======================================================

    new_pan_key = None
    old_pan_key = None

    if has_pan:

        if not pan_no:
            raise HTTPException(
                status_code=400,
                detail="PAN number is required."
            )

        if not pan_image:
            raise HTTPException(
                status_code=400,
                detail="PAN document is required."
            )

        # --------------------------------------------------
        # NORMALIZE PAN
        # --------------------------------------------------

        pan_no = pan_no.strip().upper()

        # --------------------------------------------------
        # CHECK UNIQUE PAN
        # --------------------------------------------------

        existing_pan = (
            db.query(UserKYC)
            .filter(
                UserKYC.pan_no == pan_no,
                UserKYC.user_id != user.id,
            )
            .first()
        )

        if existing_pan:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This PAN number is already "
                    "registered with another user."
                )
            )

        # --------------------------------------------------
        # VALIDATE PAN FILE
        # --------------------------------------------------

        pan_data = await validate_file(
            pan_image
        )

        # --------------------------------------------------
        # CREATE PAN KEY
        # --------------------------------------------------

        new_pan_key = create_object_key(
            user_id=user.id,
            document_type="pan",
            filename=pan_image.filename,
        )

        # --------------------------------------------------
        # UPLOAD PAN
        # --------------------------------------------------

        upload_to_spaces(
            object_key=new_pan_key,
            file_data=pan_data,
            content_type=pan_image.content_type,
        )

        if kyc:
            old_pan_key = kyc.pan_image

    # ======================================================
    # CREATE KYC RECORD
    # ======================================================

    if not kyc:

        # Because Aadhaar is currently nullable=False
        if not aadhar_no:
            if new_pan_key:
                delete_spaces_object(new_pan_key)

            raise HTTPException(
                status_code=400,
                detail=(
                    "Aadhaar details are required "
                    "for the first KYC submission."
                )
            )

        kyc = UserKYC(
            user_id=user.id,

            aadhar_no=aadhar_no,
            aadhar_front=new_aadhar_front_key,
            aadhar_back=new_aadhar_back_key,

            pan_no=pan_no if has_pan else None,
            pan_image=new_pan_key if has_pan else None,

            status="PENDING",
            rejection_reason=None,
        )

        db.add(kyc)

    else:

        # --------------------------------------------------
        # UPDATE AADHAAR
        # --------------------------------------------------

        if has_aadhaar:

            kyc.aadhar_no = aadhar_no
            kyc.aadhar_front = new_aadhar_front_key
            kyc.aadhar_back = new_aadhar_back_key

        # --------------------------------------------------
        # UPDATE PAN
        # --------------------------------------------------

        if has_pan:

            kyc.pan_no = pan_no
            kyc.pan_image = new_pan_key

        # --------------------------------------------------
        # RESET STATUS
        # --------------------------------------------------

        kyc.status = "PENDING"
        kyc.rejection_reason = None

    # ======================================================
    # SAVE DATABASE
    # ======================================================

    try:

        db.commit()
        db.refresh(kyc)

    except Exception as exc:

        db.rollback()

        # Delete newly uploaded files
        delete_spaces_object(
            new_aadhar_front_key
        )

        delete_spaces_object(
            new_aadhar_back_key
        )

        delete_spaces_object(
            new_pan_key
        )

        print(
            "KYC database error:",
            str(exc)
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to save KYC details."
        )

    # ======================================================
    # DELETE OLD FILES
    # ======================================================

    if has_aadhaar:

        if old_aadhar_front:
            delete_spaces_object(
                old_aadhar_front
            )

        if old_aadhar_back:
            delete_spaces_object(
                old_aadhar_back
            )

    if has_pan:

        if old_pan_key:
            delete_spaces_object(
                old_pan_key
            )

    # ======================================================
    # RESPONSE
    # ======================================================

    return {
        "message": "KYC details uploaded successfully.",

        "kyc_id": kyc.id,

        "aadhar_no": kyc.aadhar_no,

        "pan_no": kyc.pan_no,

        "status": kyc.status,
    }
# ==========================================================
# GET MY KYC
# ==========================================================

@router.get("")
def get_my_kyc(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    user = get_database_user(
        current_user=current_user,
        db=db,
    )

    kyc = (
        db.query(UserKYC)
        .filter(
            UserKYC.user_id == user.id
        )
        .first()
    )

    if not kyc:

        return {
            "user_id": user.id,
            "aadhar_no": None,
            "pan_no": None,
            "documents": [],
        }

    documents = []

    # ------------------------------------------------------
    # AADHAAR
    # ------------------------------------------------------

    if (
        kyc.aadhar_front
        or kyc.aadhar_back
    ):

        documents.append({
            "document_type": "aadhaar",

            "front_url": generate_presigned_url(
                kyc.aadhar_front
            ),

            "back_url": generate_presigned_url(
                kyc.aadhar_back
            ),

            "status": kyc.status,

            "rejection_reason": (
                kyc.rejection_reason
            ),
        })

    # ------------------------------------------------------
    # PAN
    # ------------------------------------------------------

    if kyc.pan_image:

        documents.append({
            "document_type": "pan",

            "front_url": generate_presigned_url(
                kyc.pan_image
            ),

            "back_url": None,

            "status": kyc.status,

            "rejection_reason": (
                kyc.rejection_reason
            ),
        })

    return {
        "user_id": user.id,

        "aadhar_no": kyc.aadhar_no,

        "pan_no": kyc.pan_no,

        "documents": documents,

        "uploaded_at": kyc.uploaded_at,

        "updated_at": kyc.updated_at,
    }


# ==========================================================
# GET KYC
# ==========================================================

@router.get("/{kyc_id}")
def get_kyc_document(
    kyc_id: int,
    current_user: str = Depends(get_current_user),
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
            detail="KYC document not found."
        )

    return {
        "id": kyc.id,

        "user_id": kyc.user_id,

        "aadhar_no": kyc.aadhar_no,

        "pan_no": kyc.pan_no,

        "aadhar_front_url":
            generate_presigned_url(
                kyc.aadhar_front
            ),

        "aadhar_back_url":
            generate_presigned_url(
                kyc.aadhar_back
            ),

        "pan_url":
            generate_presigned_url(
                kyc.pan_image
            ),

        "status": kyc.status,

        "rejection_reason":
            kyc.rejection_reason,

        "uploaded_at":
            kyc.uploaded_at,

        "updated_at":
            kyc.updated_at,

        "expires_in": 300,
    }


# ==========================================================
# VIEW KYC
# ==========================================================

@router.get("/{kyc_id}/view")
def view_kyc_document(
    kyc_id: int,
    current_user: str = Depends(get_current_user),
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
            detail="KYC document not found."
        )

    return {
        "id": kyc.id,

        "aadhar_front_url":
            generate_presigned_url(
                kyc.aadhar_front
            ),

        "aadhar_back_url":
            generate_presigned_url(
                kyc.aadhar_back
            ),

        "pan_url":
            generate_presigned_url(
                kyc.pan_image
            ),

        "expires_in": 300,
    }


# ==========================================================
# DELETE KYC
# ==========================================================

@router.delete("/{kyc_id}")
def delete_kyc_document(
    kyc_id: int,
    current_user: str = Depends(get_current_user),
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
            detail="KYC document not found."
        )

    if kyc.status == "APPROVED":

        raise HTTPException(
            status_code=400,
            detail=(
                "Approved KYC documents "
                "cannot be deleted."
            )
        )

    # ------------------------------------------------------
    # SAVE FILE KEYS
    # ------------------------------------------------------

    aadhar_front = kyc.aadhar_front
    aadhar_back = kyc.aadhar_back
    pan_image = kyc.pan_image

    # ------------------------------------------------------
    # DELETE DATABASE
    # ------------------------------------------------------

    try:

        db.delete(kyc)
        db.commit()

    except Exception as exc:

        db.rollback()

        print(
            "KYC delete database error:",
            str(exc)
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to delete KYC document."
        )

    # ------------------------------------------------------
    # DELETE SPACES FILES
    # ------------------------------------------------------

    delete_spaces_object(aadhar_front)
    delete_spaces_object(aadhar_back)
    delete_spaces_object(pan_image)

    return {
        "message": "KYC documents deleted successfully.",
        "kyc_id": kyc_id,
    }