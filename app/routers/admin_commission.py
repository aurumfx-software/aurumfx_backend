from datetime import datetime, date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.schemas import CommissionIds
from app.database import get_db
from app.models import (
    User,
    Wallet,
    WalletTransaction,
    ReferralCommission
)


from app.core.security import get_current_user
router = APIRouter(
    prefix="/admin/commissions",
    tags=["Admin Commissions"]
)
def get_admin(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.user_id == current_user
    ).first()

    if not user:
        raise HTTPException(404, "User not found")

    if user.role != "ADMIN":
        raise HTTPException(403, "Admin only")

    return user
#---------------------------------------------------------------------------
#Pending commission
#---------------------------------------------------------------------------
@router.get("/pending")
def pending_commissions(
    enroller_id: Optional[str] = None,
    investor_id: Optional[str] = None,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    query = db.query(ReferralCommission).filter(
        ReferralCommission.status == "PENDING"
    )

    # Filter by Investor
    if investor_id:

        investor = (
            db.query(User)
            .filter(User.user_id == investor_id)
            .first()
        )

        if not investor:
            raise HTTPException(
                status_code=404,
                detail="Investor not found"
            )

        query = query.filter(
            ReferralCommission.investor_id == investor.id
        )

    # Filter by Enroller
    if enroller_id:

        enroller = (
            db.query(User)
            .filter(User.user_id == enroller_id)
            .first()
        )

        if not enroller:
            raise HTTPException(
                status_code=404,
                detail="Enroller not found"
            )

        query = query.filter(
            ReferralCommission.enroller_id == enroller.id
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

            "investor_id": investor.user_id if investor else None,

            "investor_name": investor.first_name if investor else None,

            "enroller_id": enroller.user_id if enroller else None,

            "enroller_name": enroller.first_name if enroller else None,

            "investment_amount": item.investment_amount,

            "gross_commission": item.commission_amount,

            "admin_fee": item.admin_fee_amount,

            "net_commission": item.paid_amount,

            "washout_amount": item.washout_amount,

            "status": item.status,

            "created_at": item.created_at,

            "payment_date": item.payment_date

        })

    return response
#-------------------------------------------------------------------------------------
# Pay One Commission
#-------------------------------------------------------------------------------------
@router.put("/{id}/pay")
def pay_commission(
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
            detail="Commission not found"
        )

    if commission.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Commission is already paid"
        )

    try:

        # -----------------------------------
        # Get or Create Wallet
        # -----------------------------------
        wallet = (
            db.query(Wallet)
            .filter(
                Wallet.user_id == commission.enroller_id
            )
            .first()
        )

        if not wallet:

            wallet = Wallet(
                user_id=commission.enroller_id,
                balance=0
            )

            db.add(wallet)
            db.flush()

        # -----------------------------------
        # Credit Wallet
        # -----------------------------------
        wallet.balance += commission.paid_amount

        # -----------------------------------
        # Wallet Transaction
        # -----------------------------------
        transaction = WalletTransaction(

            wallet_id=wallet.id,

            investment_id=commission.investment_id,

            amount=commission.paid_amount,

            transaction_type="REFERRAL",

            remarks=f"Weekly Commission Payment - Commission #{commission.id}"

        )

        db.add(transaction)

        # -----------------------------------
        # Update Commission
        # -----------------------------------
        commission.status = "PAID"
        commission.payment_date = datetime.utcnow()

        db.commit()
        db.refresh(commission)

        return {

            "message": "Commission paid successfully",

            "commission_id": commission.id,

            "investment_id": commission.investment_id,

            "enroller_id": commission.enroller_id,

            "paid_amount": commission.paid_amount,

            "wallet_balance": wallet.balance,

            "payment_date": commission.payment_date

        }

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
#------------------------------------------------------------------------------------------
# Pay Multiple
#------------------------------------------------------------------------------------------
@router.put("/pay")
def pay_multiple(
    data: CommissionIds,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    paid_count = 0
    total_amount = 0

    try:

        for commission_id in data.ids:

            commission = (
                db.query(ReferralCommission)
                .filter(
                    ReferralCommission.id == commission_id,
                    ReferralCommission.status == "PENDING"
                )
                .first()
            )

            if not commission:
                continue

            # -----------------------------------
            # Get or Create Wallet
            # -----------------------------------
            wallet = (
                db.query(Wallet)
                .filter(
                    Wallet.user_id == commission.enroller_id
                )
                .first()
            )

            if not wallet:

                wallet = Wallet(
                    user_id=commission.enroller_id,
                    balance=0
                )

                db.add(wallet)
                db.flush()

            # -----------------------------------
            # Credit Wallet
            # -----------------------------------
            wallet.balance += commission.paid_amount

            # -----------------------------------
            # Wallet Transaction
            # -----------------------------------
            transaction = WalletTransaction(

                wallet_id=wallet.id,

                investment_id=commission.investment_id,

                amount=commission.paid_amount,

                transaction_type="REFERRAL",

                remarks=f"Weekly Commission Payment - Commission #{commission.id}"

            )

            db.add(transaction)

            # -----------------------------------
            # Update Commission
            # -----------------------------------
            commission.status = "PAID"

            commission.payment_date = datetime.utcnow()

            paid_count += 1

            total_amount += commission.paid_amount

        db.commit()

        return {

            "message": "Commissions paid successfully",

            "paid_count": paid_count,

            "total_paid_amount": total_amount

        }

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
#-----------------------------------------------------------------------------------
# Pay all Pending
#-----------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------
# Pay All Pending Commissions
# -----------------------------------------------------------------------------------
@router.put("/pay-all")
def pay_all(
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    commissions = (
        db.query(ReferralCommission)
        .filter(
            ReferralCommission.status == "PENDING"
        )
        .all()
    )

    if not commissions:
        raise HTTPException(
            status_code=404,
            detail="No pending commissions found"
        )

    paid_count = 0

    for commission in commissions:

        # Get/Create Wallet
        wallet = (
            db.query(Wallet)
            .filter(
                Wallet.user_id == commission.enroller_id
            )
            .first()
        )

        if not wallet:

            wallet = Wallet(
                user_id=commission.enroller_id,
                balance=0
            )

            db.add(wallet)
            db.flush()

        # Credit Wallet
        wallet.balance += commission.paid_amount

        # Wallet Transaction
        transaction = WalletTransaction(

            wallet_id=wallet.id,

            investment_id=commission.investment_id,

            amount=commission.paid_amount,

            transaction_type="REFERRAL",

            remarks=f"Weekly Commission - Investment #{commission.investment_id}"

        )

        db.add(transaction)

        # Update Commission
        commission.status = "PAID"
        commission.payment_date = datetime.utcnow()

        paid_count += 1

    db.commit()

    return {
        "message": f"{paid_count} commissions paid successfully",
        "total_paid": paid_count
    }
# -----------------------------------------------------------------------------
# Payment History
# -----------------------------------------------------------------------------
@router.get("/history")
def history(
    status: Optional[str] = None,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    query = db.query(ReferralCommission)

    if status:
        query = query.filter(
            ReferralCommission.status == status.upper()
        )

    commissions = query.order_by(
        ReferralCommission.id.desc()
    ).all()

    response = []

    for item in commissions:

        investor = db.query(User).filter(
            User.id == item.investor_id
        ).first()

        enroller = db.query(User).filter(
            User.id == item.enroller_id
        ).first()

        response.append({

            "id": item.id,

            "investment_id": item.investment_id,

            "investor_id": investor.user_id if investor else None,

            "investor_name": investor.first_name if investor else None,

            "enroller_id": enroller.user_id if enroller else None,

            "enroller_name": enroller.first_name if enroller else None,

            "investment_amount": item.investment_amount,

            "gross_commission": item.commission_amount,

            "admin_fee": item.admin_fee_amount,

            "net_commission": item.paid_amount,

            "washout": item.washout_amount,

            "status": item.status,

            "created_at": item.created_at,

            "payment_date": item.payment_date

        })

    return response

# -----------------------------------------------------------------------------
# Commission Details
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Commission Details
# -----------------------------------------------------------------------------
@router.get("/{id}")
def commission_details(
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
            detail="Commission not found"
        )

    investor = (
        db.query(User)
        .filter(
            User.id == commission.investor_id
        )
        .first()
    )

    enroller = (
        db.query(User)
        .filter(
            User.id == commission.enroller_id
        )
        .first()
    )

    wallet = (
        db.query(Wallet)
        .filter(
            Wallet.user_id == commission.enroller_id
        )
        .first()
    )

    transaction = (
        db.query(WalletTransaction)
        .filter(
            WalletTransaction.investment_id == commission.investment_id,
            WalletTransaction.transaction_type == "REFERRAL"
        )
        .order_by(
            WalletTransaction.id.desc()
        )
        .first()
    )

    return {

        "commission_id": commission.id,

        "investment_id": commission.investment_id,

        "status": commission.status,

        "created_at": commission.created_at,

        "payment_date": commission.payment_date,

        "investor": {

            "id": investor.user_id if investor else None,

            "name": investor.first_name if investor else None,

            "email": investor.email if investor else None,

            "mobile": investor.mobile if investor else None

        },

        "enroller": {

            "id": enroller.user_id if enroller else None,

            "name": enroller.first_name if enroller else None,

            "email": enroller.email if enroller else None,

            "mobile": enroller.mobile if enroller else None

        },

        "commission": {

            "investment_amount": commission.investment_amount,

            "gross_commission": commission.commission_amount,

            "admin_fee": commission.admin_fee_amount,

            "net_commission": commission.paid_amount,

            "washout_amount": commission.washout_amount,

            "commission_percentage": commission.commission_percentage

        },

        "wallet": {

            "current_balance": wallet.balance if wallet else 0

        },

        "transaction": {

            "transaction_id": transaction.id if transaction else None,

            "amount": transaction.amount if transaction else None,

            "type": transaction.transaction_type if transaction else None,

            "remarks": transaction.remarks if transaction else None,

            "created_at": transaction.created_at if transaction else None

        }

    }