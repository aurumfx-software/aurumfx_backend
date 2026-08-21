from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.core.security import get_current_user

from app.models import (
    User,
    Investment,
)

from app.schemas import (
    AdminEnrollerResponse,
    AdminEnrollerListResponse,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/admin",
    tags=["Admin Enrollers"]
)


# ============================================================
# ADMIN AUTHENTICATION
# ============================================================

def get_admin_user(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get logged-in user and verify that the user is ADMIN.
    """

    admin = (
        db.query(User)
        .filter(
            User.user_id == current_user
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if admin.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return admin


# ============================================================
# GET ALL ENROLLERS
# ============================================================

@router.get(
    "/enrollers",
    response_model=AdminEnrollerListResponse
)
def get_all_enrollers(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Get all users who have an enroller/sponsor.

    Returns:

    - User ID
    - Full name
    - Date of joining
    - Current rank
    - Total active investment
    - Total active lots
    - Enroller ID
    - Enroller name
    """

    # --------------------------------------------------------
    # Get all users having an enroller
    # --------------------------------------------------------

    users = (
        db.query(User)
        .filter(
            User.role == "USER",
            User.enroller_id.isnot(None),
            User.enroller_id != ""
        )
        .order_by(
            User.created_at.desc()
        )
        .all()
    )

    result = []

    # --------------------------------------------------------
    # Process users
    # --------------------------------------------------------

    for user in users:

        # ====================================================
        # FIND ENROLLER
        # ====================================================

        enroller = (
            db.query(User)
            .filter(
                User.user_id == user.enroller_id
            )
            .first()
        )

        # ====================================================
        # TOTAL INVESTMENT + LOTS
        # ====================================================

        investment_data = (
            db.query(
                func.coalesce(
                    func.sum(Investment.amount),
                    0
                ),
                func.coalesce(
                    func.sum(Investment.lots),
                    0
                )
            )
            .filter(
                Investment.user_id == user.id,

                # Only approved investments
                Investment.approval_status == "APPROVED",

                # Only active investments
                Investment.investment_status == "ACTIVE"
            )
            .first()
        )

        total_investment_amount = float(
            investment_data[0] or 0
        )

        total_lots = int(
            investment_data[1] or 0
        )

        # ====================================================
        # CURRENT RANK
        # ====================================================

        rank_name = None

        if user.current_rank:
            rank_name = user.current_rank.rank_name

        # ====================================================
        # FULL NAME
        # ====================================================

        fullname = (
            f"{user.first_name} {user.last_name}"
        ).strip()

        # ====================================================
        # ENROLLER NAME
        # ====================================================

        enroller_name = None

        if enroller:
            enroller_name = (
                f"{enroller.first_name} "
                f"{enroller.last_name}"
            ).strip()

        # ====================================================
        # RESPONSE
        # ====================================================

        result.append(
            AdminEnrollerResponse(
                user_id=user.user_id,

                fullname=fullname,

                date_of_joining=(
                    user.created_at.date()
                    if user.created_at
                    else None
                ),

                rank=rank_name,

                total_investment_amount=(
                    total_investment_amount
                ),

                total_lots=total_lots,

                enroller_id=user.enroller_id,

                enroller_name=enroller_name,
            )
        )

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return AdminEnrollerListResponse(
        total=len(result),
        enrollers=result
    )