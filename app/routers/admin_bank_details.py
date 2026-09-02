# app/routers/admin_bank_details.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import User, UserBankDetails
from app.utils.spaces import generate_presigned_url
from app.schemas import BankStatusUpdateRequest, NomineeStatusUpdateRequest


router = APIRouter(
    prefix="/api/admin/members",
    tags=["Admin - Member Bank Details"]
)



# ==========================================================
# GET ALL USERS BANK DETAILS
# ==========================================================

@router.get("/bank-details")
def get_all_users_bank_details(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
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

    for user in users:

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
        # RESPONSE
        # ==================================================

        response.append(
            {
                "user_id": user.user_id,

                "fullname": (
                    f"{user.first_name} "
                    f"{user.last_name or ''}"
                ).strip(),

                "bank_details": {
                    "bank_account": bank_details.bank_account,
                    "bank_name": bank_details.bank_name,
                    "ifsc": bank_details.ifsc,
                    "bank_proof": bank_proof_url,

                    # NEW
                    "bank_status": bank_details.bank_status,
                    "bank_rejection_reason": (
                        bank_details.bank_rejection_reason
                    ),
                },

                "expires_in": 300,
            }
        )

    return response


# ==========================================================
# GET ALL USERS NOMINEE DETAILS
# ==========================================================

@router.get("/nominee-details")
def get_all_users_nominee_details(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
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

    for user in users:

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
                "user_id": user.user_id,

                "fullname": (
                    f"{user.first_name} "
                    f"{user.last_name or ''}"
                ).strip(),

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

                    # NEW
                    "nominee_status": (
                        bank_details.nominee_status
                    ),

                    "nominee_rejection_reason": (
                        bank_details.nominee_rejection_reason
                    ),
                },

                "expires_in": 300,
            }
        )

    return response




# ==========================================================
# GET USER NOMINEE DETAILS
# ==========================================================

@router.get("/{user_id}/nominee-details")
def get_user_nominee_details(
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
    # Find Bank/Nominee Details
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

            "nominee_details": None,
        }

    # ======================================================
    # NOMINEE AADHAAR FRONT URL
    # ======================================================

    nominee_aadhar_front_url = None

    if bank_details.nominee_aadhar_front:
        try:
            nominee_aadhar_front_url = generate_presigned_url(
                bank_details.nominee_aadhar_front,
                expires_in=300,
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
                bank_details.nominee_aadhar_back,
                expires_in=300,
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
        # Nominee Details
        # --------------------------------------------------

        "nominee_details": {
            "nominee_name": bank_details.nominee_name,

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

            # Separate nominee status
            "nominee_status": (
                bank_details.nominee_status
            ),

            "nominee_rejection_reason": (
                bank_details.nominee_rejection_reason
            ),
        },

        "expires_in": 300,
    }


# ==========================================================
# GET USER BANK DETAILS
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
        }

    # ======================================================
    # BANK PROOF URL
    # ======================================================

    bank_proof_url = None

    if bank_details.bank_proof:
        try:
            bank_proof_url = generate_presigned_url(
                bank_details.bank_proof,
                expires_in=300,
            )
        except Exception:
            bank_proof_url = None

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

            # Separate bank status
            "bank_status": bank_details.bank_status,

            "bank_rejection_reason": (
                bank_details.bank_rejection_reason
            ),
        },

        "expires_in": 300,
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

    status_value = data.bank_status.strip().upper()

    # ======================================================
    # REJECT
    # ======================================================

    if status_value == "REJECTED":

        if not data.bank_rejection_reason:
            raise HTTPException(
                status_code=400,
                detail="Rejection reason is required"
            )

        if not data.bank_rejection_reason.strip():
            raise HTTPException(
                status_code=400,
                detail="Rejection reason is required"
            )

        bank_details.bank_status = "REJECTED"

        bank_details.bank_rejection_reason = (
            data.bank_rejection_reason.strip()
        )

    # ======================================================
    # APPROVE
    # ======================================================

    elif status_value == "APPROVED":

        bank_details.bank_status = "APPROVED"

        # Clear previous rejection reason
        bank_details.bank_rejection_reason = None

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
            bank_details.bank_status
        ),

        "rejection_reason": (
            bank_details.bank_rejection_reason
        ),
    }

# ==========================================================
# UPDATE NOMINEE STATUS
# ==========================================================

@router.patch("/{user_id}/nominee-status")
def update_bank_status(
    user_id: str,
    data: NomineeStatusUpdateRequest,
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

    nominee_details = (
        db.query(UserBankDetails)
        .filter(
            UserBankDetails.user_id == user.id
        )
        .first()
    )

    if not nominee_details:
        raise HTTPException(
            status_code=404,
            detail="Bank details not found"
        )

    # ------------------------------------------------------
    # Normalize Status
    # ------------------------------------------------------

    status_value = data.nominee_status.strip().upper()

    # ======================================================
    # REJECT
    # ======================================================

    if status_value == "REJECTED":

        if not data.nominee_rejection_reason:
            raise HTTPException(
                status_code=400,
                detail="Rejection reason is required"
            )

        if not data.nominee_rejection_reason.strip():
            raise HTTPException(
                status_code=400,
                detail="Rejection reason is required"
            )

        nominee_details.nominee_status = "REJECTED"

        nominee_details.nominee_rejection_reason = (
            data.nominee_rejection_reason.strip()
        )

    # ======================================================
    # APPROVE
    # ======================================================

    elif status_value == "APPROVED":

        nominee_details.nominee_status = "APPROVED"

        # Clear previous rejection reason
        nominee_details.nominee_rejection_reason = None

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
    db.refresh(nominee_details)

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "message": (
            "Nominee details approved"
            if status_value == "APPROVED"
            else "Nominee details rejected"
        ),

        "user_id": user.user_id,

        "bank_status": (
            nominee_details.nominee_status
        ),

        "rejection_reason": (
            nominee_details.nominee_rejection_reason
        ),
    }

# ==========================================================
# GET PENDING BANK DETAILS
# Only users with complete bank submission
# ==========================================================

@router.get("/bank-details/pending")
def get_pending_users_bank_details(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    # ======================================================
    # GET USERS WITH PENDING + COMPLETE BANK DETAILS
    # ======================================================

    users = (
        db.query(User)
        .join(
            UserBankDetails,
            UserBankDetails.user_id == User.id
        )
        .filter(
            # ----------------------------------------------
            # BANK STATUS MUST BE PENDING
            # ----------------------------------------------

            UserBankDetails.bank_status == "PENDING",

            # ----------------------------------------------
            # BANK ACCOUNT MUST BE UPLOADED
            # ----------------------------------------------

            UserBankDetails.bank_account.isnot(None),
            UserBankDetails.bank_account != "",

            # ----------------------------------------------
            # BANK NAME MUST BE UPLOADED
            # ----------------------------------------------

            UserBankDetails.bank_name.isnot(None),
            UserBankDetails.bank_name != "",

            # ----------------------------------------------
            # IFSC MUST BE UPLOADED
            # ----------------------------------------------

            UserBankDetails.ifsc.isnot(None),
            UserBankDetails.ifsc != "",

            # ----------------------------------------------
            # BANK PROOF MUST BE UPLOADED
            # ----------------------------------------------

            UserBankDetails.bank_proof.isnot(None),
            UserBankDetails.bank_proof != "",
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

        # ==================================================
        # GET BANK DETAILS
        # ==================================================

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
        # RESPONSE
        # ==================================================

        response.append(
            {
                # ------------------------------------------
                # USER
                # ------------------------------------------

                "user_id":
                    user.user_id,

                "fullname":
                    (
                        f"{user.first_name or ''} "
                        f"{user.last_name or ''}"
                    ).strip(),

                # ------------------------------------------
                # BANK DETAILS
                # ------------------------------------------

                "bank_details": {

                    "bank_account":
                        bank_details.bank_account,

                    "bank_name":
                        bank_details.bank_name,

                    "ifsc":
                        bank_details.ifsc,

                    "bank_proof":
                        bank_proof_url,

                    "bank_status":
                        bank_details.bank_status,

                    "rejection_reason":
                        bank_details.bank_rejection_reason,
                },

                # ------------------------------------------
                # EXPIRY
                # ------------------------------------------

                "expires_in":
                    300,
            }
        )

    # ======================================================
    # RETURN
    # ======================================================

    return {
        "success": True,
        "count": len(response),
        "data": response
    }


# ==========================================================
# GET PENDING NOMINEE DETAILS
# Only users with complete nominee submission
# Bank status is NOT checked
# ==========================================================

@router.get("/nominee-details/pending")
def get_pending_users_nominee_details(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    # ======================================================
    # GET USERS WITH PENDING + COMPLETE NOMINEE DETAILS
    # ======================================================

    users = (
        db.query(User)
        .join(
            UserBankDetails,
            UserBankDetails.user_id == User.id
        )
        .filter(
            # ----------------------------------------------
            # NOMINEE STATUS MUST BE PENDING
            # ----------------------------------------------

            UserBankDetails.nominee_status == "PENDING",

            # ----------------------------------------------
            # NOMINEE NAME
            # ----------------------------------------------

            UserBankDetails.nominee_name.isnot(None),
            UserBankDetails.nominee_name != "",

            # ----------------------------------------------
            # NOMINEE RELATION
            # ----------------------------------------------

            UserBankDetails.nominee_relation.isnot(None),
            UserBankDetails.nominee_relation != "",

            # ----------------------------------------------
            # NOMINEE GENDER
            # ----------------------------------------------

            UserBankDetails.nominee_gender.isnot(None),
            UserBankDetails.nominee_gender != "",

            # ----------------------------------------------
            # NOMINEE DOB
            # ----------------------------------------------

            UserBankDetails.nominee_dob.isnot(None),

            # ----------------------------------------------
            # NOMINEE ADDRESS
            # ----------------------------------------------

            UserBankDetails.nominee_address.isnot(None),
            UserBankDetails.nominee_address != "",

            # ----------------------------------------------
            # NOMINEE AADHAAR
            # ----------------------------------------------

            UserBankDetails.nominee_aadhar.isnot(None),
            UserBankDetails.nominee_aadhar != "",

            # ----------------------------------------------
            # NOMINEE MOBILE
            # ----------------------------------------------

            UserBankDetails.nominee_mobile.isnot(None),
            UserBankDetails.nominee_mobile != "",

            # ----------------------------------------------
            # NOMINEE AADHAAR FRONT
            # ----------------------------------------------

            UserBankDetails.nominee_aadhar_front.isnot(None),
            UserBankDetails.nominee_aadhar_front != "",

            # ----------------------------------------------
            # NOMINEE AADHAAR BACK
            # ----------------------------------------------

            UserBankDetails.nominee_aadhar_back.isnot(None),
            UserBankDetails.nominee_aadhar_back != "",
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

        # ==================================================
        # GET NOMINEE DETAILS
        # ==================================================

        nominee = (
            db.query(UserBankDetails)
            .filter(
                UserBankDetails.user_id == user.id
            )
            .first()
        )

        if not nominee:
            continue

        # ==================================================
        # NOMINEE AADHAAR FRONT URL
        # ==================================================

        nominee_aadhar_front_url = None

        if nominee.nominee_aadhar_front:

            try:
                nominee_aadhar_front_url = generate_presigned_url(
                    nominee.nominee_aadhar_front,
                    expires_in=300,
                )

            except Exception:
                nominee_aadhar_front_url = None

        # ==================================================
        # NOMINEE AADHAAR BACK URL
        # ==================================================

        nominee_aadhar_back_url = None

        if nominee.nominee_aadhar_back:

            try:
                nominee_aadhar_back_url = generate_presigned_url(
                    nominee.nominee_aadhar_back,
                    expires_in=300,
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

                "user_id":
                    user.user_id,

                "fullname":
                    (
                        f"{user.first_name or ''} "
                        f"{user.last_name or ''}"
                    ).strip(),

                # ------------------------------------------
                # NOMINEE DETAILS
                # ------------------------------------------

                "nominee_details": {

                    "nominee_name":
                        nominee.nominee_name,

                    "nominee_relation":
                        nominee.nominee_relation,

                    "nominee_gender":
                        nominee.nominee_gender,

                    "nominee_dob":
                        nominee.nominee_dob,

                    "nominee_address":
                        nominee.nominee_address,

                    "nominee_aadhar":
                        nominee.nominee_aadhar,

                    "nominee_mobile":
                        nominee.nominee_mobile,

                    "nominee_aadhar_front":
                        nominee_aadhar_front_url,

                    "nominee_aadhar_back":
                        nominee_aadhar_back_url,

                    "nominee_status":
                        nominee.nominee_status,

                    "nominee_rejection_reason":
                        nominee.nominee_rejection_reason,
                },

                # ------------------------------------------
                # URL EXPIRY
                # ------------------------------------------

                "expires_in": 300,
            }
        )

    # ======================================================
    # RETURN
    # ======================================================

    return {
        "success": True,
        "count": len(response),
        "data": response,
    }

