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
# GET ALL USERS KYC
# ==========================================================

# ==========================================================
# GET ALL USERS KYC
# ==========================================================

@router.get("/kyc")
def get_all_users_kyc(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):

    # ======================================================
    # GET ALL USERS WITH KYC
    # ======================================================

    users = (
        db.query(User)
        .join(
            UserKYC,
            UserKYC.user_id == User.id
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

        kyc = (
            db.query(UserKYC)
            .filter(
                UserKYC.user_id == user.id
            )
            .first()
        )

        if not kyc:
            continue

        # ==================================================
        # AADHAAR FRONT URL
        # ==================================================

        aadhar_front_url = None

        if kyc.aadhar_front:

            try:

                aadhar_front_url = generate_presigned_url(
                    kyc.aadhar_front,
                    expires_in=300,
                )

            except Exception:

                aadhar_front_url = None

        # ==================================================
        # AADHAAR BACK URL
        # ==================================================

        aadhar_back_url = None

        if kyc.aadhar_back:

            try:

                aadhar_back_url = generate_presigned_url(
                    kyc.aadhar_back,
                    expires_in=300,
                )

            except Exception:

                aadhar_back_url = None

        # ==================================================
        # PAN IMAGE URL
        # ==================================================

        pan_image_url = None

        if kyc.pan_image:

            try:

                pan_image_url = generate_presigned_url(
                    kyc.pan_image,
                    expires_in=300,
                )

            except Exception:

                pan_image_url = None

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

                # ------------------------------------------
                # KYC
                # ------------------------------------------

                "kyc": {
                    "id": kyc.id,

                    "aadhar_no": kyc.aadhar_no,

                    "pan_no": kyc.pan_no,

                    "aadhar_front": (
                        aadhar_front_url
                    ),

                    "aadhar_back": (
                        aadhar_back_url
                    ),

                    "pan_image": (
                        pan_image_url
                    ),

                    "status": kyc.status,

                    "rejection_reason": (
                        kyc.rejection_reason
                    ),

                    "uploaded_at": (
                        kyc.uploaded_at
                    ),

                    "updated_at": (
                        kyc.updated_at
                    ),

                    "expires_in": 300,
                }
            }
        )

    return response
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

# ==========================================================
# GET PENDING KYC
# Only users with complete KYC documents
# ==========================================================

@router.get("/kyc/pending")
def get_pending_users_kyc(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):

    # ======================================================
    # GET USERS WITH COMPLETE PENDING KYC
    # ======================================================

    users = (
        db.query(User)
        .join(
            UserKYC,
            UserKYC.user_id == User.id
        )
        .filter(

            # ------------------------------------------------
            # KYC STATUS
            # ------------------------------------------------

            UserKYC.status == "PENDING",

            # ------------------------------------------------
            # AADHAAR NUMBER
            # ------------------------------------------------

            UserKYC.aadhar_no.isnot(None),
            UserKYC.aadhar_no != "",

            # ------------------------------------------------
            # AADHAAR FRONT
            # ------------------------------------------------

            UserKYC.aadhar_front.isnot(None),
            UserKYC.aadhar_front != "",

            # ------------------------------------------------
            # AADHAAR BACK
            # ------------------------------------------------

            UserKYC.aadhar_back.isnot(None),
            UserKYC.aadhar_back != "",

            # ------------------------------------------------
            # PAN NUMBER
            # ------------------------------------------------

            UserKYC.pan_no.isnot(None),
            UserKYC.pan_no != "",

            # ------------------------------------------------
            # PAN IMAGE
            # ------------------------------------------------

            UserKYC.pan_image.isnot(None),
            UserKYC.pan_image != "",
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
        # GET KYC
        # --------------------------------------------------

        kyc = (
            db.query(UserKYC)
            .filter(
                UserKYC.user_id == user.id
            )
            .first()
        )

        if not kyc:
            continue

        # ==================================================
        # AADHAAR FRONT URL
        # ==================================================

        aadhar_front_url = None

        if kyc.aadhar_front:

            try:

                aadhar_front_url = (
                    generate_presigned_url(
                        kyc.aadhar_front,
                        expires_in=300,
                    )
                )

            except Exception:

                aadhar_front_url = None

        # ==================================================
        # AADHAAR BACK URL
        # ==================================================

        aadhar_back_url = None

        if kyc.aadhar_back:

            try:

                aadhar_back_url = (
                    generate_presigned_url(
                        kyc.aadhar_back,
                        expires_in=300,
                    )
                )

            except Exception:

                aadhar_back_url = None

        # ==================================================
        # PAN IMAGE URL
        # ==================================================

        pan_image_url = None

        if kyc.pan_image:

            try:

                pan_image_url = (
                    generate_presigned_url(
                        kyc.pan_image,
                        expires_in=300,
                    )
                )

            except Exception:

                pan_image_url = None

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
                # KYC
                # ------------------------------------------

                "kyc": {

                    "id":
                        kyc.id,

                    "aadhar_no":
                        kyc.aadhar_no,

                    "pan_no":
                        kyc.pan_no,

                    "aadhar_front":
                        aadhar_front_url,

                    "aadhar_back":
                        aadhar_back_url,

                    "pan_image":
                        pan_image_url,

                    "status":
                        kyc.status,

                    "rejection_reason":
                        kyc.rejection_reason,

                    "uploaded_at":
                        kyc.uploaded_at,

                    "updated_at":
                        kyc.updated_at,

                    "expires_in":
                        300,
                }
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