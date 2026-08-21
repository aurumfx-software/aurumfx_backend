# app/routers/admin_bank_details.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_admin
from app.models import User
from app.utils.spaces import generate_presigned_url
from app.schemas import BankStatusUpdateRequest



router = APIRouter(
    prefix="/api/admin/members",
    tags=["Admin - Member Bank Details"]
)


@router.get("/{user_id}/bank-details")
def get_user_bank_details(
    user_id: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # -----------------------------
    # Bank proof URL
    # -----------------------------
    bank_proof_url = None

    if user.bank_proof:
        try:
            bank_proof_url = generate_presigned_url(
                user.bank_proof
            )
        except Exception:
            bank_proof_url = None

    # -----------------------------
    # Nominee Aadhaar URLs
    # -----------------------------
    nominee_aadhar_front_url = None
    nominee_aadhar_back_url = None

    if user.nominee_aadhar_front:
        try:
            nominee_aadhar_front_url = generate_presigned_url(
                user.nominee_aadhar_front
            )
        except Exception:
            nominee_aadhar_front_url = None

    if user.nominee_aadhar_back:
        try:
            nominee_aadhar_back_url = generate_presigned_url(
                user.nominee_aadhar_back
            )
        except Exception:
            nominee_aadhar_back_url = None

    return {
        # -----------------------------
        # User
        # -----------------------------
        "user_id": user.user_id,
        "fullname": f"{user.first_name} {user.last_name}",

        # -----------------------------
        # Bank Details
        # -----------------------------
        "bank_account": user.bank_account,
        "bank_name": user.bank_name,
        "ifsc": user.ifsc,
        "bank_proof": bank_proof_url,
        "bank_status": user.bank_status,

        # -----------------------------
        # Nominee Details
        # -----------------------------
        "nominee_name": user.nominee_name,
        "nominee_relation": user.nominee_relation,
        "nominee_gender": user.nominee_gender,
        "nominee_dob": user.nominee_dob,
        "nominee_address": user.nominee_address,
        "nominee_aadhar": user.nominee_aadhar,
        "nominee_mobile": user.nominee_mobile,

        # -----------------------------
        # Nominee Aadhaar Documents
        # -----------------------------
        "nominee_aadhar_front": nominee_aadhar_front_url,
        "nominee_aadhar_back": nominee_aadhar_back_url,
    }



@router.patch("/{user_id}/bank-status")
def update_bank_status(
    user_id: str,
    data: BankStatusUpdateRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # --------------------------------
    # Reject
    # --------------------------------
    if data.status == "REJECTED":

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

        user.bank_status = "REJECTED"
        user.bank_rejection_reason = (
            data.rejection_reason.strip()
        )

    # --------------------------------
    # Approve
    # --------------------------------
    elif data.status == "APPROVED":

        user.bank_status = "APPROVED"

        # Clear old rejection reason
        user.bank_rejection_reason = None

    db.commit()
    db.refresh(user)

    return {
        "message": (
            "Bank details approved"
            if data.status == "APPROVED"
            else "Bank details rejected"
        ),
        "user_id": user.user_id,
        "bank_status": user.bank_status,
        "rejection_reason": user.bank_rejection_reason,
    }