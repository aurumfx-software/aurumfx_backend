from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models import (
    User,
    Investment,
    Wallet,
    BinaryIncome,
    LevelCommissionHistory,
    ReferralCommission,
)

router = APIRouter(
    prefix="/admin/dashboard",
    tags=["Admin Dashboard"]
)


# -------------------------------------------------------------------
# Admin Authentication
# -------------------------------------------------------------------
def get_admin(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only Admin can access."
        )

    return user


# -------------------------------------------------------------------
# Admin Dashboard
# -------------------------------------------------------------------
@router.get("/")
def dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin)
):

    # Total Users
    total_users = db.query(User).count()

    # Active Users
    active_users = (
        db.query(User)
        .join(
            Investment,
            Investment.user_id == User.id
        )
        .filter(
            Investment.approval_status == "APPROVED"
        )
        .distinct()
        .count()
    )

    # Pending Investments
    pending_investments = (
        db.query(Investment)
        .filter(
            Investment.approval_status == "PENDING"
        )
        .count()
    )

    # Approved Investments
    approved_investments = (
        db.query(Investment)
        .filter(
            Investment.approval_status == "APPROVED"
        )
        .count()
    )

    # Total Investment Amount
    total_investment_amount = (
        db.query(
            func.coalesce(
                func.sum(Investment.amount),
                0
            )
        )
        .filter(
            Investment.approval_status == "APPROVED"
        )
        .scalar()
    )

    # Binary Income
    total_binary_income = (
        db.query(
            func.coalesce(
                func.sum(BinaryIncome.paid_income),
                0
            )
        )
        .scalar()
    )

    # Level Income
    total_level_income = (
        db.query(
            func.coalesce(
                func.sum(
                    LevelCommissionHistory.commission_amount
                ),
                0
            )
        )
        .scalar()
    )

    # Referral Income
    total_referral_income = (
        db.query(
            func.coalesce(
                func.sum(
                    ReferralCommission.commission_amount
                ),
                0
            )
        )
        .scalar()
    )

    # Wallet Balance
    wallet_balance = (
        db.query(
            func.coalesce(
                func.sum(Wallet.balance),
                0
            )
        )
        .scalar()
    )

    # Today's Users
    today_users = (
        db.query(User)
        .filter(
            func.date(User.created_at) == date.today()
        )
        .count()
    )

    # Today's Investments
    today_investments = (
        db.query(Investment)
        .filter(
            func.date(
                Investment.investment_date
            ) == date.today()
        )
        .count()
    )

    return {
        "users": {
            "total_users": total_users,
            "active_users": active_users,
            "today_users": today_users
        },
        "investments": {
            "approved": approved_investments,
            "pending": pending_investments,
            "today": today_investments,
            "total_amount": total_investment_amount
        },
        "income": {
            "binary_income": total_binary_income,
            "level_income": total_level_income,
            "referral_income": total_referral_income
        },
        "wallet": {
            "total_balance": wallet_balance
        }
    }