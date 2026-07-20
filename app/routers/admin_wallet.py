from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User, ReferralCommission
from app.core.security import get_current_user

router = APIRouter(
    prefix="/admin/wallet",
    tags=["Admin Wallet"]
)

def get_admin(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    admin = (
        db.query(User)
        .filter(User.user_id == current_user)
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
            detail="Only admin can access"
        )

    return admin

@router.get("/summary")
def wallet_summary(
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    total_admin_fee = (
        db.query(
            func.coalesce(
                func.sum(
                    ReferralCommission.admin_fee_amount
                ),
                0
            )
        )
        .scalar()
    )

    today_admin_fee = (
        db.query(
            func.coalesce(
                func.sum(
                    ReferralCommission.admin_fee_amount
                ),
                0
            )
        )
        .filter(
            func.date(
                ReferralCommission.created_at
            ) == date.today()
        )
        .scalar()
    )

    total_commissions = (
        db.query(func.count(ReferralCommission.id))
        .scalar()
    )

    return {

        "total_admin_fee": total_admin_fee,

        "today_admin_fee": today_admin_fee,

        "total_referral_commissions": total_commissions

    }

@router.get("/history")
def admin_fee_history(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):

    query = db.query(ReferralCommission)

    if start_date:
        query = query.filter(
            func.date(
                ReferralCommission.created_at
            ) >= start_date
        )

    if end_date:
        query = query.filter(
            func.date(
                ReferralCommission.created_at
            ) <= end_date
        )

    commissions = (
        query.order_by(
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

        enroller = (
            db.query(User)
            .filter(User.id == item.enroller_id)
            .first()
        )

        response.append({

            "id": item.id,

            "investment_id": item.investment_id,

            "investor": investor.user_id,

            "enroller": enroller.user_id,

            "investment_amount": item.investment_amount,

            "commission_percentage": item.commission_percentage,

            "commission_amount": item.commission_amount,

            "admin_fee_percentage": item.admin_fee_percentage,

            "admin_fee_amount": item.admin_fee_amount,

            "paid_amount": item.paid_amount,

            "washout_amount": item.washout_amount,

            "date": item.created_at

        })

    return response

@router.get("/today")
def today_admin_fee(
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    commissions = (
        db.query(ReferralCommission)
        .filter(
            func.date(
                ReferralCommission.created_at
            ) == date.today()
        )
        .all()
    )

    return commissions
@router.get("/{id}")
def admin_fee_details(
    id: int,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    commission = (
        db.query(ReferralCommission)
        .filter(
            ReferralCommission.id == id
        )
        .first()
    )

    if not commission:
        raise HTTPException(
            status_code=404,
            detail="Record not found"
        )

    investor = (
        db.query(User)
        .filter(User.id == commission.investor_id)
        .first()
    )

    enroller = (
        db.query(User)
        .filter(User.id == commission.enroller_id)
        .first()
    )

    return {

        "id": commission.id,

        "investment_id": commission.investment_id,

        "investor": investor.user_id,

        "enroller": enroller.user_id,

        "investment_amount": commission.investment_amount,

        "commission_percentage": commission.commission_percentage,

        "commission_amount": commission.commission_amount,

        "admin_fee_percentage": commission.admin_fee_percentage,

        "admin_fee_amount": commission.admin_fee_amount,

        "paid_amount": commission.paid_amount,

        "washout_amount": commission.washout_amount,

        "status": commission.status,

        "created_at": commission.created_at

    }