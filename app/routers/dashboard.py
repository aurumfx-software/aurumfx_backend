from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.core.security import get_current_user
from app.models import (
    User,
    Investment,
    Wallet,
    BinaryWallet,
    BinaryIncome,
    ReferralCommission,
    LevelCommissionHistory,
)
router = APIRouter(
    prefix="/dashboard",
    tags=["User Dashboard"]
)

def get_user(
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

    return user
@router.get("/")
def dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_user)
):
    total_investment = (
    db.query(
        func.coalesce(
            func.sum(Investment.amount),
            0
        )
    )
    .filter(
        Investment.user_id == user.id,
        Investment.approval_status == "APPROVED"
    )
    .scalar()
)
    active_investments = (
    db.query(Investment)
    .filter(
        Investment.user_id == user.id,
        Investment.approval_status == "APPROVED"
    )
    .count()
)
    wallet = (
    db.query(Wallet)
    .filter(
        Wallet.user_id == user.id
    )
    .first()
)

    wallet_balance = wallet.balance if wallet else 0
    binary = (
    db.query(BinaryWallet)
    .filter(
        BinaryWallet.user_id == user.id
    )
    .first()
)

    left_business = binary.left_business if binary else 0
    right_business = binary.right_business if binary else 0
    left_carry = binary.left_carry if binary else 0
    right_carry = binary.right_carry if binary else 0
    binary_income = (
    db.query(
        func.coalesce(
            func.sum(
                BinaryIncome.paid_income
            ),
            0
        )
    )
    .filter(
        BinaryIncome.user_id == user.id
    )
    .scalar()
)
    referral_income = (
    db.query(
        func.coalesce(
            func.sum(
                ReferralCommission.commission_amount
            ),
            0
        )
    )
    .filter(
        ReferralCommission.enroller_id == user.id
    )
    .scalar()
)
    level_income = (
    db.query(
        func.coalesce(
            func.sum(
                LevelCommissionHistory.commission_amount
            ),
            0
        )
    )
    .filter(
        LevelCommissionHistory.sponsor_id == user.id
    )
    .scalar()
)
    team_members = (
    db.query(User)
    .filter(
        User.enroller_id == user.user_id
    )
    .count()
)
    return {

    "user_id": user.user_id,

    "name": f"{user.first_name} {user.last_name}",

    "wallet_balance": wallet_balance,

    "total_investment": total_investment,

    "active_investments": active_investments,

    "binary_income": binary_income,

    "level_income": level_income,

    "referral_income": referral_income,

    "left_business": left_business,

    "right_business": right_business,

    "left_carry": left_carry,

    "right_carry": right_carry,

    "team_members": team_members

}
    