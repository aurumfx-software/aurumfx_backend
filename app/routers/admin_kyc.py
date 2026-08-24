from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import User, UserKYC
from app.utils.spaces import generate_presigned_url
from app.schemas import KYCStatusUpdateRequest


router = APIRouter(
    prefix="/api/admin/members",
    tags=["Admin - Member KYC"]
)


# ==========================================================
# GET USER KYC
# ==========================================================

@router.get("/{user_id}/kyc")
def get_user_kyc(
    user_id: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    # ------------------------------------------------------
    # Find User
    # ------------------------------------------------------

    user = (
        db.query(User)
        .filter(
            User.user_id == user_id
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # ------------------------------------------------------
    # Find KYC
    # ------------------------------------------------------

    kyc = (
        db.query(UserKYC)
        .filter(
            UserKYC.user_id == user.id
        )
        .first()
    )

    if not kyc:
        raise HTTPException(
            status_code=404,
            detail="KYC details not found"
        )

    # ======================================================
    # GENERATE AADHAAR FRONT URL
    # ======================================================

    aadhar_front_url = None

    if kyc.aadhar_front:
        try:
            aadhar_front_url = generate_presigned_url(
                kyc.aadhar_front
            )
        except Exception:
            aadhar_front_url = None

    # ======================================================
    # GENERATE AADHAAR BACK URL
    # ======================================================

    aadhar_back_url = None

    if kyc.aadhar_back:
        try:
            aadhar_back_url = generate_presigned_url(
                kyc.aadhar_back
            )
        except Exception:
            aadhar_back_url = None

    # ======================================================
    # GENERATE PAN IMAGE URL
    # ======================================================

    pan_image_url = None

    if kyc.pan_image:
        try:
            pan_image_url = generate_presigned_url(
                kyc.pan_image
            )
        except Exception:
            pan_image_url = None

    # ======================================================
    # RESPONSE
    # ======================================================

    return {
        # --------------------------------------------------
        # User
        # --------------------------------------------------

        "user_id": user.user_id,

        "fullname": (
            f"{user.first_name} "
            f"{user.last_name or ''}"
        ).strip(),

        # --------------------------------------------------
        # KYC
        # --------------------------------------------------

        "kyc": {
            "id": kyc.id,

            "aadhar_no": kyc.aadhar_no,

            "pan_no": kyc.pan_no,

            "aadhar_front": aadhar_front_url,

            "aadhar_back": aadhar_back_url,

            "pan_image": pan_image_url,

            "status": kyc.status,

            "rejection_reason": (
                kyc.rejection_reason
            ),

            "uploaded_at": kyc.uploaded_at,

            "updated_at": kyc.updated_at,
        }
    }


# ==========================================================
# APPROVE / REJECT KYC
# ==========================================================

@router.patch("/{user_id}/kyc-status")
def update_kyc_status(
    user_id: str,
    data: KYCStatusUpdateRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    # ------------------------------------------------------
    # Find User
    # ------------------------------------------------------

    user = (
        db.query(User)
        .filter(
            User.user_id == user_id
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # ------------------------------------------------------
    # Find KYC
    # ------------------------------------------------------

    kyc = (
        db.query(UserKYC)
        .filter(
            UserKYC.user_id == user.id
        )
        .first()
    )

    if not kyc:
        raise HTTPException(
            status_code=404,
            detail="KYC details not found"
        )

    # ------------------------------------------------------
    # Normalize status
    # ------------------------------------------------------

    status_value = data.status.strip().upper()

    # ======================================================
    # REJECT
    # ======================================================

    if status_value == "REJECTED":

        if not data.rejection_reason:
            raise HTTPException(
                status_code=400,
                detail="Rejection reason is required"
            )

        if not data.rejection_reason.strip():
            raise HTTPException(
                status_code=400,
                detail="Rejection reason is required"
            )

        kyc.status = "REJECTED"

        kyc.rejection_reason = (
            data.rejection_reason.strip()
        )

    # ======================================================
    # APPROVE
    # ======================================================

    elif status_value == "APPROVED":

        kyc.status = "APPROVED"

        # Clear old rejection reason
        kyc.rejection_reason = None

    # ======================================================
    # INVALID STATUS
    # ======================================================

    else:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid status. "
                "Use APPROVED or REJECTED."
            )
        )

    # ------------------------------------------------------
    # Save
    # ------------------------------------------------------

    db.commit()
    db.refresh(kyc)

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "message": (
            "KYC approved"
            if status_value == "APPROVED"
            else "KYC rejected"
        ),

        "user_id": user.user_id,

        "kyc_id": kyc.id,

        "status": kyc.status,

        "rejection_reason": (
            kyc.rejection_reason
        ),
    }