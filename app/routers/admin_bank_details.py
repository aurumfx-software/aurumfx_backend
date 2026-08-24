# app/routers/admin_bank_details.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import User, UserBankDetails
from app.utils.spaces import generate_presigned_url
from app.schemas import BankStatusUpdateRequest


router = APIRouter(
    prefix="/api/admin/members",
    tags=["Admin - Member Bank Details"]
)

# ==========================================================
# GET ALL USERS BANK + NOMINEE DETAILS
# ==========================================================

@router.get("/bank-details")
def get_all_users_bank_details(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    # ======================================================
    # GET USERS HAVING BANK DETAILS
    # ======================================================

    users = (
        db.query(User)
        .join(
            UserBankDetails,
            UserBankDetails.user_id == User.id
        )
        .order_by(
            User.created_at.desc()
        )
        .all()
    )

    response = []

    # ======================================================
    # LOOP USERS
    # ======================================================

    for user in users:

        # --------------------------------------------------
        # GET BANK DETAILS
        # --------------------------------------------------

        bank_details = (
            db.query(UserBankDetails)
            .filter(
                UserBankDetails.user_id == user.id
            )
            .first()
        )

        if not bank_details:
            continue

        # ==================================================
        # BANK PROOF URL
        # ==================================================

        bank_proof_url = None

        if bank_details.bank_proof:

            try:

                bank_proof_url = generate_presigned_url(
                    bank_details.bank_proof,
                    expires_in=300,
                )

            except Exception:

                bank_proof_url = None

        # ==================================================
        # NOMINEE AADHAAR FRONT URL
        # ==================================================

        nominee_aadhar_front_url = None

        if bank_details.nominee_aadhar_front:

            try:

                nominee_aadhar_front_url = (
                    generate_presigned_url(
                        bank_details.nominee_aadhar_front,
                        expires_in=300,
                    )
                )

            except Exception:

                nominee_aadhar_front_url = None

        # ==================================================
        # NOMINEE AADHAAR BACK URL
        # ==================================================

        nominee_aadhar_back_url = None

        if bank_details.nominee_aadhar_back:

            try:

                nominee_aadhar_back_url = (
                    generate_presigned_url(
                        bank_details.nominee_aadhar_back,
                        expires_in=300,
                    )
                )

            except Exception:

                nominee_aadhar_back_url = None

        # ==================================================
        # RESPONSE
        # ==================================================

        response.append(
            {
                # ------------------------------------------
                # USER
                # ------------------------------------------

                "user_id": user.user_id,

                "fullname": (
                    f"{user.first_name} "
                    f"{user.last_name or ''}"
                ).strip(),

                # ------------------------------------------
                # BANK DETAILS
                # ------------------------------------------

                "bank_details": {
                    "bank_account": (
                        bank_details.bank_account
                    ),

                    "bank_name": (
                        bank_details.bank_name
                    ),

                    "ifsc": (
                        bank_details.ifsc
                    ),

                    "bank_proof": (
                        bank_proof_url
                    ),

                    "status": (
                        bank_details.status
                    ),

                    "rejection_reason": (
                        bank_details.rejection_reason
                    ),
                },

                # ------------------------------------------
                # NOMINEE DETAILS
                # ------------------------------------------

                "nominee_details": {
                    "nominee_name": (
                        bank_details.nominee_name
                    ),

                    "nominee_relation": (
                        bank_details.nominee_relation
                    ),

                    "nominee_gender": (
                        bank_details.nominee_gender
                    ),

                    "nominee_dob": (
                        bank_details.nominee_dob
                    ),

                    "nominee_address": (
                        bank_details.nominee_address
                    ),

                    "nominee_aadhar": (
                        bank_details.nominee_aadhar
                    ),

                    "nominee_mobile": (
                        bank_details.nominee_mobile
                    ),

                    "nominee_aadhar_front": (
                        nominee_aadhar_front_url
                    ),

                    "nominee_aadhar_back": (
                        nominee_aadhar_back_url
                    ),
                },

                # ------------------------------------------
                # PRESIGNED URL EXPIRY
                # ------------------------------------------

                "expires_in": 300,
            }
        )

    return response

# ==========================================================
# GET USER BANK + NOMINEE DETAILS
# ==========================================================

@router.get("/{user_id}/bank-details")
def get_user_bank_details(
    user_id: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    # ------------------------------------------------------
    # Find User
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # Find Bank Details
    # ------------------------------------------------------

    bank_details = (
        db.query(UserBankDetails)
        .filter(
            UserBankDetails.user_id == user.id
        )
        .first()
    )

    if not bank_details:
        return {
            "user_id": user.user_id,
            "fullname": (
                f"{user.first_name} "
                f"{user.last_name or ''}"
            ).strip(),

            "bank_details": None,
            "nominee_details": None,
        }

    # ======================================================
    # BANK PROOF URL
    # ======================================================

    bank_proof_url = None

    if bank_details.bank_proof:
        try:
            bank_proof_url = generate_presigned_url(
                bank_details.bank_proof
            )
        except Exception:
            bank_proof_url = None

    # ======================================================
    # NOMINEE AADHAAR FRONT URL
    # ======================================================

    nominee_aadhar_front_url = None

    if bank_details.nominee_aadhar_front:
        try:
            nominee_aadhar_front_url = generate_presigned_url(
                bank_details.nominee_aadhar_front
            )
        except Exception:
            nominee_aadhar_front_url = None

    # ======================================================
    # NOMINEE AADHAAR BACK URL
    # ======================================================

    nominee_aadhar_back_url = None

    if bank_details.nominee_aadhar_back:
        try:
            nominee_aadhar_back_url = generate_presigned_url(
                bank_details.nominee_aadhar_back
            )
        except Exception:
            nominee_aadhar_back_url = None

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
        # Bank Details
        # --------------------------------------------------

        "bank_details": {
            "bank_account": bank_details.bank_account,
            "bank_name": bank_details.bank_name,
            "ifsc": bank_details.ifsc,
            "bank_proof": bank_proof_url,

            "status": bank_details.status,
            "rejection_reason": (
                bank_details.rejection_reason
            ),
        },

        # --------------------------------------------------
        # Nominee Details
        # --------------------------------------------------

        "nominee_details": {
            "nominee_name": (
                bank_details.nominee_name
            ),

            "nominee_relation": (
                bank_details.nominee_relation
            ),

            "nominee_gender": (
                bank_details.nominee_gender
            ),

            "nominee_dob": (
                bank_details.nominee_dob
            ),

            "nominee_address": (
                bank_details.nominee_address
            ),

            "nominee_aadhar": (
                bank_details.nominee_aadhar
            ),

            "nominee_mobile": (
                bank_details.nominee_mobile
            ),

            "nominee_aadhar_front": (
                nominee_aadhar_front_url
            ),

            "nominee_aadhar_back": (
                nominee_aadhar_back_url
            ),
        },
    }


# ==========================================================
# UPDATE BANK STATUS
# ==========================================================

@router.patch("/{user_id}/bank-status")
def update_bank_status(
    user_id: str,
    data: BankStatusUpdateRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    # ------------------------------------------------------
    # Find User
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # Find Bank Details
    # ------------------------------------------------------

    bank_details = (
        db.query(UserBankDetails)
        .filter(
            UserBankDetails.user_id == user.id
        )
        .first()
    )

    if not bank_details:
        raise HTTPException(
            status_code=404,
            detail="Bank details not found"
        )

    # ------------------------------------------------------
    # Normalize Status
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

        bank_details.status = "REJECTED"

        bank_details.rejection_reason = (
            data.rejection_reason.strip()
        )

    # ======================================================
    # APPROVE
    # ======================================================

    elif status_value == "APPROVED":

        bank_details.status = "APPROVED"

        # Clear previous rejection reason
        bank_details.rejection_reason = None

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
    db.refresh(bank_details)

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "message": (
            "Bank details approved"
            if status_value == "APPROVED"
            else "Bank details rejected"
        ),

        "user_id": user.user_id,

        "bank_status": (
            bank_details.status
        ),

        "rejection_reason": (
            bank_details.rejection_reason
        ),
    }