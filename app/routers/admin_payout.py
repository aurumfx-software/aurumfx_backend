from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin

from app.models import (
    User,
    Wallet,
    WalletTransaction,
    Investment,
    InvestmentPlan,
    AdminFeeSetting,
    ReferralCommission,
    LevelCommissionHistory,
    UserRankHistory,
)


router = APIRouter(
    prefix="/admin/payout",
    tags=["Admin Payout"]
)


# ============================================================
# DECIMAL HELPER
# ============================================================

def money(value):
    """
    Convert value to Decimal with 2 decimal places.
    """

    return Decimal(
        str(value or 0)
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


# ============================================================
# GET CURRENT ADMIN FEE
# ============================================================

def get_admin_fee_percentage(
    db: Session
) -> Decimal:
    """
    Get the latest active admin fee percentage.

    Admin fee is applied to:

        Referral
        +
        Level
        +
        Rank
    """

    fee_setting = (
        db.query(AdminFeeSetting)
        .filter(
            AdminFeeSetting.status == True
        )
        .order_by(
            AdminFeeSetting.id.desc()
        )
        .first()
    )

    if not fee_setting:
        return Decimal("0.00")

    return money(
        fee_setting.fee_percentage
    )


# ============================================================
# GET USER WALLET
# ============================================================

def get_user_wallet(
    db: Session,
    user_id: int,
    create: bool = False
):
    """
    Get user's wallet.

    If create=True and wallet doesn't exist,
    create it.
    """

    wallet = (
        db.query(Wallet)
        .filter(
            Wallet.user_id == user_id
        )
        .with_for_update()
        .first()
    )

    if not wallet and create:

        wallet = Wallet(
            user_id=user_id,
            balance=0,
            pending_balance=0,
            admin_fee=0
        )

        db.add(wallet)

        db.flush()

    return wallet


# ============================================================
# GET USER LONGEST APPROVED INVESTMENT
# ============================================================

def get_longest_investment(
    db: Session,
    user_id: int
):
    """
    Get user's approved investment with
    the longest duration plan.
    """

    return (
        db.query(Investment)
        .join(
            InvestmentPlan,
            Investment.investment_plan_id
            == InvestmentPlan.id
        )
        .filter(
            Investment.user_id == user_id,
            Investment.approval_status == "APPROVED"
        )
        .order_by(
            InvestmentPlan.duration_months.desc()
        )
        .first()
    )


# ============================================================
# GET PENDING REFERRAL
# ============================================================

def get_pending_referral(
    db: Session,
    user_id: int
):

    return (
        db.query(ReferralCommission)
        .filter(
            ReferralCommission.enroller_id == user_id,
            ReferralCommission.status == "PENDING"
        )
        .with_for_update()
        .all()
    )


# ============================================================
# GET PENDING LEVEL
# ============================================================

def get_pending_level(
    db: Session,
    user_id: int
):

    return (
        db.query(LevelCommissionHistory)
        .filter(
            LevelCommissionHistory.sponsor_id == user_id,
            LevelCommissionHistory.status == "PENDING"
        )
        .with_for_update()
        .all()
    )


# ============================================================
# GET PENDING RANK
# ============================================================

def get_pending_rank(
    db: Session,
    user_id: int
):

    return (
        db.query(UserRankHistory)
        .filter(
            UserRankHistory.user_id == user_id,
            UserRankHistory.reward_paid == False
        )
        .with_for_update()
        .all()
    )


# ============================================================
# GET WALLET PENDING TOTAL
# ============================================================

def get_wallet_pending_total(
    wallet
):
    """
    pending_balance should represent
    all generated but unpaid income.
    """

    return money(
        wallet.pending_balance
    )


# ============================================================
# GET PENDING PAYOUTS
# ============================================================

@router.get("/pending")
def get_pending_payouts(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    Get pending income for all users.

    Income:

        Referral
        Level
        Rank

    Admin fee is calculated from:

        Referral + Level + Rank
    """

    admin_fee_percentage = (
        get_admin_fee_percentage(db)
    )

    users = (
        db.query(User)
        .all()
    )

    result = []

    for user in users:

        # ====================================================
        # REFERRAL
        # ====================================================

        referral_pending = (
            db.query(
                func.coalesce(
                    func.sum(
                        ReferralCommission.commission_amount
                    ),
                    0
                )
            )
            .filter(
                ReferralCommission.enroller_id == user.id,
                ReferralCommission.status == "PENDING"
            )
            .scalar()
            or 0
        )

        # ====================================================
        # LEVEL
        # ====================================================

        level_pending = (
            db.query(
                func.coalesce(
                    func.sum(
                        LevelCommissionHistory.commission_amount
                    ),
                    0
                )
            )
            .filter(
                LevelCommissionHistory.sponsor_id == user.id,
                LevelCommissionHistory.status == "PENDING"
            )
            .scalar()
            or 0
        )

        # ====================================================
        # RANK
        # ====================================================

        rank_pending = (
            db.query(
                func.coalesce(
                    func.sum(
                        UserRankHistory.reward_income
                    ),
                    0
                )
            )
            .filter(
                UserRankHistory.user_id == user.id,
                UserRankHistory.reward_paid == False
            )
            .scalar()
            or 0
        )

        referral_pending = money(
            referral_pending
        )

        level_pending = money(
            level_pending
        )

        rank_pending = money(
            rank_pending
        )

        # ====================================================
        # TOTAL INCOME
        # ====================================================

        total_income = (
            referral_pending
            + level_pending
            + rank_pending
        )

        if total_income <= 0:
            continue

        # ====================================================
        # WALLET
        # ====================================================

        wallet = (
            db.query(Wallet)
            .filter(
                Wallet.user_id == user.id
            )
            .first()
        )

        wallet_pending = Decimal("0.00")

        if wallet:
            wallet_pending = money(
                wallet.pending_balance
            )

        # ====================================================
        # ADMIN FEE
        # ====================================================

        admin_fee = money(
            total_income
            * admin_fee_percentage
            / Decimal("100")
        )

        # ====================================================
        # NET PAYABLE
        # ====================================================

        net_payable = money(
            total_income
            - admin_fee
        )

        # ====================================================
        # INVESTMENT PLAN
        # ====================================================

        investment = get_longest_investment(
            db,
            user.id
        )

        plan_name = None
        duration_months = None

        if investment:

            plan = investment.investment_plan

            if plan:

                plan_name = (
                    plan.plan_name
                )

                duration_months = (
                    plan.duration_months
                )

        # ====================================================
        # RESULT
        # ====================================================

        result.append({

            "user_id": user.id,

            "user_code": user.user_id,

            "user_name": (
                f"{user.first_name or ''} "
                f"{user.last_name or ''}"
            ).strip(),

            # ------------------------------
            # Income
            # ------------------------------

            "referral_income": float(
                referral_pending
            ),

            "level_income": float(
                level_pending
            ),

            "rank_income": float(
                rank_pending
            ),

            "user_balance": float(
                total_income
            ),

            # ------------------------------
            # Wallet
            # ------------------------------

            "wallet_pending_balance": float(
                wallet_pending
            ),

            # ------------------------------
            # Investment
            # ------------------------------

            "investment_plan": plan_name,

            "duration_months": duration_months,

            # ------------------------------
            # Admin fee
            # ------------------------------

            "admin_fee_percentage": float(
                admin_fee_percentage
            ),

            "admin_fee": float(
                admin_fee
            ),

            # ------------------------------
            # Net
            # ------------------------------

            "net_payable": float(
                net_payable
            ),

            # ------------------------------
            # Bank
            # ------------------------------

            "bank_details": {

                "bank_account": user.bank_account,

                "bank_name": user.bank_name,

                "ifsc": user.ifsc,
            },

            "bank_proof": user.bank_proof,

            "status": "PENDING"
        })

    return {
        "total": len(result),
        "items": result
    }


# ============================================================
# PAY USER
# ============================================================

@router.post("/{user_id}/pay")
def pay_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    Pay all pending income for a user.

    Flow:

        Referral
             +
        Level
             +
        Rank
             =
        Gross Income

        Gross Income
             -
        Admin Fee
             =
        Net Payable

    Wallet:

        pending_balance -= gross income

        balance += net payable

        admin_fee += admin fee
    """

    try:

        # ====================================================
        # GET USER
        # ====================================================

        user = (
            db.query(User)
            .filter(
                User.id == user_id
            )
            .first()
        )

        if not user:

            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # ====================================================
        # LOCK WALLET
        # ====================================================

        wallet = get_user_wallet(
            db,
            user.id,
            create=True
        )

        # ====================================================
        # LOCK REFERRAL
        # ====================================================

        referral_records = (
            get_pending_referral(
                db,
                user.id
            )
        )

        referral_amount = sum(
            (
                money(
                    record.commission_amount
                )
                for record in referral_records
            ),
            Decimal("0.00")
        )
        
        # ====================================================
        # LOCK LEVEL
        # ====================================================

        level_records = (
            get_pending_level(
                db,
                user.id
            )
        )

        level_amount = sum(
            (
                money(
                    record.commission_amount
                )
                for record in level_records
            ),
            Decimal("0.00")
        )

        # ====================================================
        # LOCK RANK
        # ====================================================

        rank_records = (
            get_pending_rank(
                db,
                user.id
            )
        )

        rank_amount = sum(
            (
                money(
                    record.reward_income
                )
                for record in rank_records
            ),
            Decimal("0.00")
        )

        # ====================================================
        # TOTAL GROSS INCOME
        # ====================================================

        total_income = (
            referral_amount
            + level_amount
            + rank_amount
        )

        total_income = money(
            total_income
        )

        if total_income <= 0:

            raise HTTPException(
                status_code=400,
                detail="No pending income available for payout"
            )

        # ====================================================
        # CHECK WALLET PENDING BALANCE
        # ====================================================

        wallet_pending_before = money(
            wallet.pending_balance
        )

        if wallet_pending_before < total_income:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Wallet pending balance "
                    f"({wallet_pending_before}) is less than "
                    f"calculated pending income "
                    f"({total_income})."
                )
            )

        # ====================================================
        # GET LONGEST INVESTMENT
        # ====================================================

        investment = get_longest_investment(
            db,
            user.id
        )

        if not investment:

            raise HTTPException(
                status_code=400,
                detail="User has no approved investment"
            )

        plan = investment.investment_plan

        if not plan:

            raise HTTPException(
                status_code=400,
                detail="Investment plan not found"
            )

        # ====================================================
        # ADMIN FEE %
        # ====================================================

        admin_fee_percentage = (
            get_admin_fee_percentage(db)
        )

        # ====================================================
        # ADMIN FEE
        #
        # IMPORTANT:
        #
        # Admin fee is calculated from
        # COMPLETE income.
        #
        # Referral + Level + Rank
        # ====================================================

        admin_fee = money(
            total_income
            * admin_fee_percentage
            / Decimal("100")
        )

        # ====================================================
        # NET PAYABLE
        # ====================================================

        net_payable = money(
            total_income
            - admin_fee
        )

        if net_payable <= 0:

            raise HTTPException(
                status_code=400,
                detail="Net payable amount must be greater than zero"
            )

        # ====================================================
        # PAYMENT TIME
        # ====================================================

        payment_time = datetime.utcnow()

        # ====================================================
        # WALLET BEFORE
        # ====================================================

        balance_before = money(
            wallet.balance
        )

        admin_fee_before = money(
            wallet.admin_fee
        )

        pending_before = money(
            wallet.pending_balance
        )

        # ====================================================
        # UPDATE WALLET
        # ====================================================

        # Remove complete gross income
        # from pending balance.

        wallet.pending_balance = money(
            pending_before
            - total_income
        )

        # Add only NET income to available balance.

        wallet.balance = money(
            balance_before
            + net_payable
        )

        # Store deducted admin fee
        # at wallet level.

        wallet.admin_fee = money(
            admin_fee_before
            + admin_fee
        )

        # ====================================================
        # REFERRAL → PAID
        # ====================================================

        for record in referral_records:

            record.status = "PAID"

            # Only set this if your model has this column.
            if hasattr(
                record,
                "payment_date"
            ):
                record.payment_date = (
                    payment_time
                )

        # ====================================================
        # LEVEL → PAID
        # ====================================================

        for record in level_records:

            record.status = "PAID"

        # ====================================================
        # RANK → PAID
        # ====================================================

        for record in rank_records:

            record.reward_paid = True

            record.paid_at = (
                payment_time
            )

        # ====================================================
        # WALLET TRANSACTIONS → PAID
        # ====================================================

        transaction_types = (
            "REFERRAL",
            "LEVEL_INCOME",
            "RANK_REWARD"
        )

        wallet_transactions = (
            db.query(WalletTransaction)
            .filter(
                WalletTransaction.wallet_id
                == wallet.id,

                WalletTransaction.status
                == "PENDING",

                WalletTransaction.transaction_type
                .in_(transaction_types)
            )
            .with_for_update()
            .all()
        )

        for transaction in wallet_transactions:

            transaction.status = "PAID"

        # ====================================================
        # COMMIT
        # ====================================================

        db.commit()

        db.refresh(wallet)

        # ====================================================
        # RESPONSE
        # ====================================================

        return {

            "message": (
                "Payout completed successfully"
            ),

            "user_id": user.id,

            "user_code": user.user_id,

            "user_name": (
                f"{user.first_name or ''} "
                f"{user.last_name or ''}"
            ).strip(),

            # ----------------------------------------------
            # Income
            # ----------------------------------------------

            "referral_income": float(
                referral_amount
            ),

            "level_income": float(
                level_amount
            ),

            "rank_income": float(
                rank_amount
            ),

            "total_income": float(
                total_income
            ),

            # ----------------------------------------------
            # Investment
            # ----------------------------------------------

            "investment_plan": (
                plan.plan_name
            ),

            "duration_months": (
                plan.duration_months
            ),

            # ----------------------------------------------
            # Admin fee
            # ----------------------------------------------

            "admin_fee_percentage": float(
                admin_fee_percentage
            ),

            "admin_fee": float(
                admin_fee
            ),

            # ----------------------------------------------
            # Net
            # ----------------------------------------------

            "net_payable": float(
                net_payable
            ),

            # ----------------------------------------------
            # Wallet
            # ----------------------------------------------

            "wallet": {

                "balance_before": float(
                    balance_before
                ),

                "balance_after": float(
                    wallet.balance
                ),

                "pending_balance_before": float(
                    pending_before
                ),

                "pending_balance_after": float(
                    wallet.pending_balance
                ),

                "admin_fee_before": float(
                    admin_fee_before
                ),

                "admin_fee_after": float(
                    wallet.admin_fee
                )
            },

            "status": "PAID",

            "paid_at": payment_time
        }

    except HTTPException:

        db.rollback()

        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Payout failed: {str(e)}"
        )