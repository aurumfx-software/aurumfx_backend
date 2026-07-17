from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import (
    User,
    Wallet,
    ReferralCommission
)
from app.core.security import get_current_user

router = APIRouter(
    prefix="/wallet",
    tags=["Wallet"]
)


# ----------------------------------------------------
# Wallet Summary
# ----------------------------------------------------
@router.get("/summary")
def wallet_summary(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    enroller = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not enroller:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    wallet = (
        db.query(Wallet)
        .filter(Wallet.user_id == enroller.id)
        .first()
    )

    balance = wallet.balance if wallet else 0

    total_commission = (
        db.query(
            func.coalesce(
                func.sum(ReferralCommission.commission_amount),
                0
            )
        )
        .filter(
            ReferralCommission.enroller_id == enroller.id
        )
        .scalar()
    )

    total_washout = (
        db.query(
            func.coalesce(
                func.sum(ReferralCommission.washout_amount),
                0
            )
        )
        .filter(
            ReferralCommission.enroller_id == enroller.id
        )
        .scalar()
    )

    today_commission = (
        db.query(
            func.coalesce(
                func.sum(ReferralCommission.paid_amount),
                0
            )
        )
        .filter(
            ReferralCommission.enroller_id == enroller.id,
            func.date(ReferralCommission.created_at) == date.today()
        )
        .scalar()
    )

    return {
        "available_balance": balance,
        "total_commission": total_commission,
        "today_commission": today_commission,
        "washout_amount": total_washout
    }


# ----------------------------------------------------
# Commission History
# ----------------------------------------------------
@router.get("/commissions")
def commission_history(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    enroller = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not enroller:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    commissions = (
        db.query(ReferralCommission)
        .filter(
            ReferralCommission.enroller_id == enroller.id
        )
        .order_by(
            ReferralCommission.id.desc()
        )
        .all()
    )

    response = []

    for item in commissions:

        investor = (
            db.query(User)
            .filter(User.id == item.investor_id)
            .first()
        )

        response.append({

            "id": item.id,

            "investment_id": item.investment_id,

            "investor_id": investor.user_id,

            "investor_name": investor.first_name,

            "investment_amount": item.investment_amount,

            "commission_percentage": item.commission_percentage,

            "commission_amount": item.commission_amount,

            "paid_amount": item.paid_amount,

            "washout_amount": item.washout_amount,

            "status": item.status,

            "created_at": item.created_at

        })

    return response


# ----------------------------------------------------
# Today's Commission
# ----------------------------------------------------
@router.get("/today")
def today_commission(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    enroller = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not enroller:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    commissions = (
        db.query(ReferralCommission)
        .filter(
            ReferralCommission.enroller_id == enroller.id,
            func.date(ReferralCommission.created_at) == date.today()
        )
        .all()
    )

    return commissions


# ----------------------------------------------------
# Commission Details
# ----------------------------------------------------
@router.get("/commissions/{id}")
def commission_details(
    id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    enroller = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not enroller:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    commission = (
        db.query(ReferralCommission)
        .filter(
            ReferralCommission.id == id,
            ReferralCommission.enroller_id == enroller.id
        )
        .first()
    )

    if not commission:
        raise HTTPException(
            status_code=404,
            detail="Commission not found"
        )

    investor = (
        db.query(User)
        .filter(User.id == commission.investor_id)
        .first()
    )

    return {

        "id": commission.id,

        "investment_id": commission.investment_id,

        "investor_id": investor.user_id,

        "investor_name": investor.first_name,

        "investment_amount": commission.investment_amount,

        "commission_percentage": commission.commission_percentage,

        "commission_amount": commission.commission_amount,

        "paid_amount": commission.paid_amount,

        "washout_amount": commission.washout_amount,

        "status": commission.status,

        "created_at": commission.created_at

    }