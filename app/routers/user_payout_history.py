from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import PayoutHistory, User


router = APIRouter(
    prefix="/payout",
    tags=["User Payout"]
)


# ============================================================
# GET LOGGED-IN USER PAYOUT HISTORY
# ============================================================

@router.get("/history")
def get_my_payout_history(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Get payout history for the logged-in user.
    """

    # ========================================================
    # GET USER
    # ========================================================

    user = (
        db.query(User)
        .filter(
            User.user_id == current_user
        )
        .first()
    )

    if not user:

        return {
            "total": 0,
            "items": []
        }

    # ========================================================
    # GET PAYOUT HISTORY
    # ========================================================

    histories = (
        db.query(PayoutHistory)
        .filter(
            PayoutHistory.user_id == user.id
        )
        .order_by(
            PayoutHistory.paid_at.desc()
        )
        .all()
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    result = []

    for history in histories:

        result.append({

            "id": history.id,

            "user_id": history.user_id,

            # =================================================
            # Income
            # =================================================

            # "referral_income": history.referral_income,

            # "level_income": history.level_income,

            # "rank_income": history.rank_income,

            "total_income": history.total_income,

            # =================================================
            # Admin Fee
            # =================================================

            "admin_fee_percentage": (
                history.admin_fee_percentage
            ),

            "admin_fee": history.admin_fee,

            "net_payable": history.net_payable,

            # =================================================
            # Payout
            # =================================================

            "payout_method": history.payout_method,

            # "payout_information": (
            #     history.payout_information
            # ),

            # =================================================
            # Status
            # =================================================

            "status": history.status,

            "paid_at": history.paid_at,

            # "created_at": history.created_at,
        })

    return {
        "total": len(result),
        "items": result
    }