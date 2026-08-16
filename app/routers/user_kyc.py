# app/routers/user_kyc.py

import os
import uuid
from pathlib import Path

import boto3
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
from app.schemas import KYCResponse, KYCListResponse


# ==========================================================
# ROUTER
# ==========================================================

router = APIRouter(
    prefix="/api/user/kyc",
    tags=["User KYC"],
)


# ==========================================================
# DIGITALOCEAN SPACES CONFIGURATION
# ==========================================================

SPACES_BUCKET = os.getenv(
    "SPACES_BUCKET"
)

SPACES_REGION = os.getenv(
    "SPACES_REGION",
    "sgp1",
)

SPACES_ENDPOINT = os.getenv(
    "SPACES_ENDPOINT",
    f"https://{SPACES_REGION}.digitaloceanspaces.com",
)

SPACES_ACCESS_KEY = os.getenv(
    "SPACES_ACCESS_KEY"
)

SPACES_SECRET_KEY = os.getenv(
    "SPACES_SECRET_KEY"
)


# ==========================================================
# KYC SETTINGS
# ==========================================================

ALLOWED_DOCUMENT_TYPES = {
    "aadhaar",
    "aadhar",
    "pan",
    "passport",
    "bank_proof",
    "bankproof",
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
# DIGITALOCEAN SPACES CLIENT
# ==========================================================

def get_spaces_client():

    if not SPACES_BUCKET:
        raise RuntimeError(
            "SPACES_BUCKET is not configured."
        )

    if not SPACES_ACCESS_KEY:
        raise RuntimeError(
            "SPACES_ACCESS_KEY is not configured."
        )

    if not SPACES_SECRET_KEY:
        raise RuntimeError(
            "SPACES_SECRET_KEY is not configured."
        )

    return boto3.client(
        "s3",
        region_name=SPACES_REGION,
        endpoint_url=SPACES_ENDPOINT,
        aws_access_key_id=SPACES_ACCESS_KEY,
        aws_secret_access_key=SPACES_SECRET_KEY,
    )


# ==========================================================
# GET DATABASE USER
# ==========================================================

def get_database_user(
    current_user,
    db: Session,
) -> User:

    """
    Existing get_current_user() in AurumFX returns
    a string user_id.

    Example:

        current_user = "AURUM12345"

    We find the actual User record using users.user_id.
    """

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
# DELETE OBJECT FROM DIGITALOCEAN SPACES
# ==========================================================

def delete_spaces_object(
    object_key: str,
):

    if not object_key:
        return

    try:

        s3 = get_spaces_client()

        s3.delete_object(
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

    try:

        s3 = get_spaces_client()

        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": SPACES_BUCKET,
                "Key": object_key,
            },
            ExpiresIn=expires_in,
        )

        return url

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
        f"{unique_filename}"
    )


# ==========================================================
# UPLOAD KYC DOCUMENT
# ==========================================================

@router.post(
    "/upload",
    response_model=KYCResponse,
)
async def upload_kyc_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    # ======================================================
    # GET ACTUAL DATABASE USER
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

    # Support both spellings
    if document_type == "aadhar":
        document_type = "aadhaar"

    if document_type == "bankproof":
        document_type = "bank_proof"

    # ======================================================
    # VALIDATE DOCUMENT TYPE
    # ======================================================

    valid_document_types = {
        "aadhaar",
        "pan",
        "passport",
        "bank_proof",
        "other",
    }

    if document_type not in valid_document_types:

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
    # VALIDATE FILE NAME
    # ======================================================

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="File name is required.",
        )

    # ======================================================
    # VALIDATE CONTENT TYPE
    # ======================================================

    if file.content_type not in ALLOWED_CONTENT_TYPES:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid file type. "
                "Only JPG, JPEG, PNG and PDF "
                "files are allowed."
            ),
        )

    # ======================================================
    # READ FILE
    # ======================================================

    file_data = await file.read()

    if not file_data:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # ======================================================
    # VALIDATE FILE SIZE
    # ======================================================

    if len(file_data) > MAX_FILE_SIZE:

        raise HTTPException(
            status_code=400,
            detail="Maximum file size is 10 MB.",
        )

    # ======================================================
    # FIND EXISTING KYC
    # ======================================================

    existing_document = (
        db.query(UserKYC)
        .filter(
            UserKYC.user_id == user.id,
            UserKYC.document_type == document_type,
        )
        .first()
    )

    # ======================================================
    # CREATE NEW SPACES OBJECT KEY
    # ======================================================

    object_key = create_object_key(
        user_id=user.id,
        document_type=document_type,
        filename=file.filename,
    )

    # ======================================================
    # UPLOAD TO DIGITALOCEAN SPACES
    #
    # KYC FILES ARE PRIVATE
    # ======================================================

    try:

        s3 = get_spaces_client()

        s3.put_object(
            Bucket=SPACES_BUCKET,
            Key=object_key,
            Body=file_data,
            ContentType=file.content_type,
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

    # ======================================================
    # UPDATE EXISTING DOCUMENT
    # ======================================================

    if existing_document:

        old_object_key = (
            existing_document.file_url
        )

        existing_document.file_name = (
            file.filename
        )

        existing_document.file_url = (
            object_key
        )

        existing_document.status = (
            "PENDING"
        )

        existing_document.rejection_reason = None

        try:

            db.commit()
            db.refresh(
                existing_document
            )

        except Exception as exc:

            db.rollback()

            # Remove newly uploaded file
            delete_spaces_object(
                object_key
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

        # Delete old file only after DB update succeeds
        if old_object_key:
            delete_spaces_object(
                old_object_key
            )

        return existing_document

    # ======================================================
    # CREATE NEW KYC RECORD
    # ======================================================

    kyc = UserKYC(
        user_id=user.id,
        document_type=document_type,
        file_name=file.filename,
        file_url=object_key,
        status="PENDING",
        rejection_reason=None,
    )

    db.add(kyc)

    try:

        db.commit()
        db.refresh(kyc)

    except Exception as exc:

        db.rollback()

        # DB failed, so remove uploaded file
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

    return kyc


# ==========================================================
# GET MY KYC DOCUMENTS
# ==========================================================

@router.get(
    "",
    response_model=list[KYCListResponse],
)
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

        view_url = generate_presigned_url(
            object_key=kyc.file_url,
            expires_in=300,
        )

        response.append(
            {
                "id": kyc.id,
                "user_id": kyc.user_id,
                "document_type": kyc.document_type,
                "file_name": kyc.file_name,
                "status": kyc.status,
                "rejection_reason": kyc.rejection_reason,
                "uploaded_at": kyc.uploaded_at,
                "updated_at": kyc.updated_at,
                "view_url": view_url,
                "expires_in": 300,
            }
        )

    return response

# ==========================================================
# GET SINGLE KYC
# ==========================================================

@router.get(
    "/{kyc_id}",
    response_model=KYCResponse,
)
def get_kyc_document(
    kyc_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # ======================================================
    # GET ACTUAL DATABASE USER
    # ======================================================

    user = get_database_user(
        current_user=current_user,
        db=db,
    )

    # ======================================================
    # GET KYC DOCUMENT
    # ======================================================

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

    # ======================================================
    # GENERATE TEMPORARY SIGNED URL
    # ======================================================

    view_url = generate_presigned_url(
        object_key=kyc.file_url,
        expires_in=300,
    )

    # ======================================================
    # RESPONSE
    # ======================================================

    return {
        "id": kyc.id,
        "user_id": kyc.user_id,
        "document_type": kyc.document_type,
        "file_name": kyc.file_name,
        "status": kyc.status,
        "rejection_reason": kyc.rejection_reason,
        "uploaded_at": kyc.uploaded_at,
        "updated_at": kyc.updated_at,
        "view_url": view_url,
        "expires_in": 300,
    }

# ==========================================================
# VIEW KYC DOCUMENT
# ==========================================================

@router.get(
    "/{kyc_id}/view",
)
def view_kyc_document(
    kyc_id: int,
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
    # GET KYC
    # ======================================================

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

    # ======================================================
    # GENERATE TEMPORARY URL
    # ======================================================

    url = generate_presigned_url(
        object_key=kyc.file_url,
        expires_in=300,
    )

    return {
        "id": kyc.id,
        "user_id": kyc.user_id,
        "document_type": kyc.document_type,
        "file_name": kyc.file_name,
        "status": kyc.status,
        "url": url,
        "expires_in": 300,
    }


# ==========================================================
# DELETE KYC
# ==========================================================

@router.delete(
    "/{kyc_id}",
)
def delete_kyc_document(
    kyc_id: int,
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
    # GET KYC
    # ======================================================

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

    # ======================================================
    # APPROVED DOCUMENT CANNOT BE DELETED
    # ======================================================

    if kyc.status == "APPROVED":

        raise HTTPException(
            status_code=400,
            detail=(
                "Approved KYC documents "
                "cannot be deleted."
            ),
        )

    # ======================================================
    # SAVE OBJECT KEY
    # ======================================================

    object_key = kyc.file_url

    # ======================================================
    # DELETE DATABASE RECORD
    # ======================================================

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

    # ======================================================
    # DELETE SPACES OBJECT
    # ======================================================

    delete_spaces_object(
        object_key
    )

    return {
        "message": (
            "KYC document deleted successfully."
        ),
        "kyc_id": kyc_id,
    }