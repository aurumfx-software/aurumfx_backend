from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import (
    User,
    Wallet,
    ReferralCommission,
    LevelIncome,
    LevelCommissionHistory,
    UserRankHistory,
    AdminFeeSetting,
    WalletTransaction,
    Investment
)
from app.core.security import get_current_user


router = APIRouter(
    prefix="/wallet",
    tags=["Wallet"]
)


# ============================================================
# Helper: Get Current User
# ============================================================

def get_logged_in_user(
    current_user: str,
    db: Session
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

# ============================================================
# Get Current Admin Fee Percentage
# ============================================================

def get_admin_fee_percentage(
    db: Session
) -> float:

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
        return 0.0

    return float(
        fee_setting.fee_percentage or 0
    )


# ============================================================
# Wallet Summary
# ============================================================

# @router.get("/summary")
# def wallet_summary(
#     current_user: str = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):

#     user = get_logged_in_user(
#         current_user,
#         db
#     )

#     # --------------------------------------------------------
#     # Wallet
#     # --------------------------------------------------------

#     wallet = (
#         db.query(Wallet)
#         .filter(
#             Wallet.user_id == user.id
#         )
#         .first()
#     )

#     available_balance = (
#         wallet.balance
#         if wallet
#         else 0
#     )

#     pending_balance = (
#         wallet.pending_balance
#         if wallet
#         else 0
#     )

#     admin_fee = (
#         wallet.admin_fee
#         if wallet
#         else 0
#     )

#     # ========================================================
#     # REFERRAL INCOME
#     # ========================================================

#     referral_gross = (
#         db.query(
#             func.coalesce(
#                 func.sum(
#                     ReferralCommission.commission_amount
#                 ),
#                 0
#             )
#         )
#         .filter(
#             ReferralCommission.enroller_id == user.id
#         )
#         .scalar()
#         or 0
#     )

#     referral_paid = (
#         db.query(
#             func.coalesce(
#                 func.sum(
#                     ReferralCommission.paid_amount
#                 ),
#                 0
#             )
#         )
#         .filter(
#             ReferralCommission.enroller_id == user.id,
#             ReferralCommission.status == "PAID"
#         )
#         .scalar()
#         or 0
#     )

#     referral_pending = (
#         db.query(
#             func.coalesce(
#                 func.sum(
#                     ReferralCommission.paid_amount
#                 ),
#                 0
#             )
#         )
#         .filter(
#             ReferralCommission.enroller_id == user.id,
#             ReferralCommission.status == "PENDING"
#         )
#         .scalar()
#         or 0
#     )

#     # ========================================================
#     # LEVEL INCOME
#     # ========================================================

#     level_income = (
#         db.query(
#             func.coalesce(
#                 func.sum(
#                     LevelIncome.commission_amount
#                 ),
#                 0
#             )
#         )
#         .filter(
#             LevelIncome.to_user_id == user.id
#         )
#         .scalar()
#         or 0
#     )

#     level_paid = (
#         db.query(
#             func.coalesce(
#                 func.sum(
#                     LevelCommissionHistory.commission_amount
#                 ),
#                 0
#             )
#         )
#         .filter(
#             LevelCommissionHistory.sponsor_id == user.id,
#             LevelCommissionHistory.status == "PAID"
#         )
#         .scalar()
#         or 0
#     )

#     # ========================================================
#     # RANK INCOME
#     # ========================================================

#     rank_income = (
#         db.query(
#             func.coalesce(
#                 func.sum(
#                     UserRankHistory.reward_income
#                 ),
#                 0
#             )
#         )
#         .filter(
#             UserRankHistory.user_id == user.id
#         )
#         .scalar()
#         or 0
#     )

#     rank_paid = (
#         db.query(
#             func.coalesce(
#                 func.sum(
#                     UserRankHistory.reward_income
#                 ),
#                 0
#             )
#         )
#         .filter(
#             UserRankHistory.user_id == user.id,
#             UserRankHistory.reward_paid == True
#         )
#         .scalar()
#         or 0
#     )

#     # ========================================================
#     # TOTAL GENERATED COMMISSION
#     # ========================================================

#     total_generated_commission = (
#         referral_gross
#         + level_income
#         + rank_income
#     )

#     # ========================================================
#     # TOTAL PAID COMMISSION
#     # ========================================================

#     total_paid_commission = (
#         referral_paid
#         + level_paid
#         + rank_paid
#     )

#     # ========================================================
#     # TODAY'S REFERRAL INCOME
#     # ========================================================

#     today_referral = (
#         db.query(
#             func.coalesce(
#                 func.sum(
#                     ReferralCommission.commission_amount
#                 ),
#                 0
#             )
#         )
#         .filter(
#             ReferralCommission.enroller_id == user.id,
#             func.date(
#                 ReferralCommission.created_at
#             ) == date.today()
#         )
#         .scalar()
#         or 0
#     )

#     # ========================================================
#     # TODAY'S LEVEL INCOME
#     # ========================================================

#     today_level = (
#         db.query(
#             func.coalesce(
#                 func.sum(
#                     LevelIncome.commission_amount
#                 ),
#                 0
#             )
#         )
#         .filter(
#             LevelIncome.to_user_id == user.id,
#             func.date(
#                 LevelIncome.created_at
#             ) == date.today()
#         )
#         .scalar()
#         or 0
#     )

#     # ========================================================
#     # TODAY'S RANK INCOME
#     # ========================================================

#     today_rank = (
#         db.query(
#             func.coalesce(
#                 func.sum(
#                     UserRankHistory.reward_income
#                 ),
#                 0
#             )
#         )
#         .filter(
#             UserRankHistory.user_id == user.id,
#             func.date(
#                 UserRankHistory.achieved_at
#             ) == date.today()
#         )
#         .scalar()
#         or 0
#     )

#     today_generated_commission = (
#         today_referral
#         + today_level
#         + today_rank
#     )

#     # ========================================================
#     # TODAY'S PAID
#     # ========================================================

#     today_referral_paid = (
#         db.query(
#             func.coalesce(
#                 func.sum(
#                     ReferralCommission.paid_amount
#                 ),
#                 0
#             )
#         )
#         .filter(
#             ReferralCommission.enroller_id == user.id,
#             ReferralCommission.status == "PAID",
#             func.date(
#                 ReferralCommission.payment_date
#             ) == date.today()
#         )
#         .scalar()
#         or 0
#     )

#     today_level_paid = (
#         db.query(
#             func.coalesce(
#                 func.sum(
#                     LevelCommissionHistory.commission_amount
#                 ),
#                 0
#             )
#         )
#         .filter(
#             LevelCommissionHistory.sponsor_id == user.id,
#             LevelCommissionHistory.status == "PAID",
#             func.date(
#                 LevelCommissionHistory.created_at
#             ) == date.today()
#         )
#         .scalar()
#         or 0
#     )

#     today_rank_paid = (
#         db.query(
#             func.coalesce(
#                 func.sum(
#                     UserRankHistory.reward_income
#                 ),
#                 0
#             )
#         )
#         .filter(
#             UserRankHistory.user_id == user.id,
#             UserRankHistory.reward_paid == True,
#             func.date(
#                 UserRankHistory.paid_at
#             ) == date.today()
#         )
#         .scalar()
#         or 0
#     )

#     today_paid_commission = (
#         today_referral_paid
#         + today_level_paid
#         + today_rank_paid
#     )

#     return {

#         "available_balance": available_balance,

#         "pending_balance": pending_balance,

#         "admin_fee": admin_fee,

#         # "gross_commission": total_generated_commission,

#         # "paid_commission": total_paid_commission,

#         # "pending_commission": (
#         #     total_generated_commission
#         #     - total_paid_commission
#         # ),

#         # "today_generated_commission":
#         #     today_generated_commission,

#         # "today_paid_commission":
#         #     today_paid_commission,

#         # # Breakdown
#         # "referral_income": referral_gross,

#         # "level_income": level_income,

#         # "rank_income": rank_income,
#     }
@router.get("/summary")
def wallet_summary(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_logged_in_user(
        current_user,
        db
    )

    wallet = (
        db.query(Wallet)
        .filter(
            Wallet.user_id == user.id
        )
        .first()
    )

    if not wallet:
        return {
            "total_amount": 0,
            "admin_fee": 0,
            "amount": 0,
            "pending_balance": 0
        }

    # ========================================================
    # WALLET VALUES
    # ========================================================

    balance = float(
        wallet.balance or 0
    )

    pending_balance = float(
        wallet.pending_balance or 0
    )

    actual_admin_fee = float(
        wallet.admin_fee or 0
    )

    # ========================================================
    # CURRENT ADMIN FEE %
    # ========================================================

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

    admin_fee_percentage = 0

    if fee_setting:

        admin_fee_percentage = float(
            fee_setting.fee_percentage or 0
        )

    # ========================================================
    # PENDING ADMIN FEE
    # ========================================================
    #
    # If income is still pending, admin fee has not yet
    # been deducted from it.
    #
    # Example:
    #
    # pending = 12000
    # fee = 2%
    # pending fee = 240
    # ========================================================

    pending_admin_fee = (
        pending_balance
        * admin_fee_percentage
        / 100
    )

    # ========================================================
    # TOTAL ADMIN FEE
    #
    # Already deducted fee
    # +
    # Expected fee from pending income
    # ========================================================

    total_admin_fee = (
        actual_admin_fee
        + pending_admin_fee
    )

    # ========================================================
    # TOTAL GROSS AMOUNT
    #
    # Already paid NET amount
    # +
    # already deducted admin fee
    # +
    # pending GROSS income
    #
    # But when pending exists, the pending amount is already
    # gross, so don't add pending admin fee again.
    # ========================================================

    total_amount = (
        balance
        + actual_admin_fee
        + pending_balance
    )

    # ========================================================
    # TOTAL AMOUNT AFTER ADMIN FEE
    # ========================================================
    #
    # Gross total - all admin fees
    # ========================================================

    amount = (
        total_amount
        - total_admin_fee
    )

    if amount < 0:
        amount = 0

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "total_amount": round(
            total_amount,
            2
        ),

        "admin_fee": round(
            total_admin_fee,
            2
        ),

        "amount": round(
            amount,
            2
        ),

        "pending_balance": round(
            pending_balance,
            2
        )
    }
# @router.get("/transactions")
# def wallet_transaction_history(
#     current_user: str = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):

#     user = get_logged_in_user(
#         current_user,
#         db
#     )

#     wallet = (
#         db.query(Wallet)
#         .filter(
#             Wallet.user_id == user.id
#         )
#         .first()
#     )

#     if not wallet:
#         return []

#     transactions = (
#         db.query(WalletTransaction)
#         .filter(
#             WalletTransaction.wallet_id == wallet.id
#         )
#         .order_by(
#             WalletTransaction.id.desc()
#         )
#         .all()
#     )

#     response = []

#     for transaction in transactions:

#         from_user = None

#         # ====================================================
#         # GET FROM USER
#         # ====================================================

#         if transaction.investment_id:

#             investment = (
#                 db.query(Investment)
#                 .filter(
#                     Investment.id == transaction.investment_id
#                 )
#                 .first()
#             )

#             if investment:

#                 investor = (
#                     db.query(User)
#                     .filter(
#                         User.id == investment.user_id
#                     )
#                     .first()
#                 )

#                 if investor:

#                     from_user = {
#                         "user_id": investor.user_id,
#                         "name": (
#                             f"{investor.first_name or ''} "
#                             f"{investor.last_name or ''}"
#                         ).strip()
#                     }

#         # ====================================================
#         # PAYMENT TYPE
#         # ====================================================

#         if transaction.status == "PAID":
#             payment_type = "CREDIT"

#         elif transaction.status == "PENDING":
#             payment_type = "DEBIT"

#         else:
#             payment_type = transaction.status

#         # ====================================================
#         # RESPONSE
#         # ====================================================

#         response.append({

#             "id": transaction.id,

#             "from_user": from_user,

#             "transaction_type":
#                 transaction.transaction_type,

#             "payment_type":
#                 payment_type,

#             "amount":
#                 float(transaction.amount or 0),

#             "status":
#                 transaction.status,

#             "date":
#                 transaction.created_at
#         })

#     return response


# ============================================================
# GET USER WALLET TRANSACTIONS
# ============================================================

@router.get("/transactions")
def wallet_transaction_history(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # ========================================================
    # GET LOGGED-IN USER
    # ========================================================

    user = get_logged_in_user(
        current_user,
        db
    )

    # ========================================================
    # GET USER WALLET
    # ========================================================

    wallet = (
        db.query(Wallet)
        .filter(
            Wallet.user_id == user.id
        )
        .first()
    )

    if not wallet:
        return []

    # ========================================================
    # GET TRANSACTIONS
    # ========================================================

    transactions = (
        db.query(WalletTransaction)
        .filter(
            WalletTransaction.wallet_id == wallet.id
        )
        .order_by(
            WalletTransaction.id.desc()
        )
        .all()
    )

    response = []

    for transaction in transactions:

        # ====================================================
        # FROM USER
        # ====================================================

        from_user = None

        if transaction.investment_id:

            investment = (
                db.query(Investment)
                .filter(
                    Investment.id ==
                    transaction.investment_id
                )
                .first()
            )

            if investment:

                investor = (
                    db.query(User)
                    .filter(
                        User.id ==
                        investment.user_id
                    )
                    .first()
                )

                if investor:

                    investor_name = (
                        f"{investor.first_name or ''} "
                        f"{investor.last_name or ''}"
                    ).strip()

                    from_user = {
                        "user_id": investor.user_id,
                        "name": investor_name
                    }

        # ====================================================
        # LEVEL
        # ====================================================

        level = None

        if (
            transaction.transaction_type
            == "LEVEL_INCOME"
            and transaction.investment_id
        ):

            level_history = (
                db.query(
                    LevelCommissionHistory
                )
                .filter(
                    LevelCommissionHistory.investment_id
                    ==
                    transaction.investment_id,

                    LevelCommissionHistory.sponsor_id
                    ==
                    user.id
                )
                .order_by(
                    LevelCommissionHistory.id.desc()
                )
                .first()
            )

            if level_history:

                level = level_history.level

        # ====================================================
        # PAYMENT TYPE
        # ====================================================

        if transaction.status == "PAID":

            payment_type = "CREDIT"

        elif transaction.status == "PENDING":

            payment_type = "PENDING"

        else:

            payment_type = transaction.status

        # ====================================================
        # RESPONSE
        # ====================================================

        response.append({

            "id":
                transaction.id,

            # ------------------------------------------------
            # FROM USER
            # ------------------------------------------------

            "from_user":
                from_user,

            # ------------------------------------------------
            # INVESTMENT
            # ------------------------------------------------

            "investment_id":
                transaction.investment_id,

            # ------------------------------------------------
            # LEVEL
            # ------------------------------------------------

            "level":
                level,

            # ------------------------------------------------
            # TRANSACTION TYPE
            # ------------------------------------------------

            "transaction_type":
                transaction.transaction_type,

            # ------------------------------------------------
            # PAYMENT TYPE
            # ------------------------------------------------

            "payment_type":
                payment_type,

            # ------------------------------------------------
            # AMOUNT
            # ------------------------------------------------

            "amount":
                float(
                    transaction.amount or 0
                ),

            # ------------------------------------------------
            # STATUS
            # ------------------------------------------------

            "status":
                transaction.status,

            # ------------------------------------------------
            # DATE
            # ------------------------------------------------

            "date":
                transaction.created_at
        })

    return response


# ============================================================
# Referral Commission History
# ============================================================

@router.get("/commissions")
def commission_history(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user = get_logged_in_user(
        current_user,
        db
    )

    commissions = (
        db.query(ReferralCommission)
        .filter(
            ReferralCommission.enroller_id == user.id
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
            .filter(
                User.id == item.investor_id
            )
            .first()
        )

        response.append({

            "id": item.id,

            "investment_id":
                item.investment_id,

            "investor_id":
                investor.user_id
                if investor
                else None,

            "investor_name":
                (
                    f"{investor.first_name} "
                    f"{investor.last_name}"
                )
                if investor
                else None,

            "investment_amount":
                item.investment_amount,

            "commission_percentage":
                item.commission_percentage,

            "gross_commission":
                item.commission_amount,

            "paid_amount":
                item.paid_amount,

            "status":
                item.status,

            "payment_date":
                item.payment_date,

            "created_at":
                item.created_at
        })

    return response


# ============================================================
# Today's Referral Commission
# ============================================================

@router.get("/today")
def today_commission(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user = get_logged_in_user(
        current_user,
        db
    )

    commissions = (
        db.query(ReferralCommission)
        .filter(
            ReferralCommission.enroller_id == user.id,
            func.date(
                ReferralCommission.created_at
            ) == date.today()
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
            .filter(
                User.id == item.investor_id
            )
            .first()
        )

        response.append({

            "investment_id":
                item.investment_id,

            "investor":
                (
                    f"{investor.first_name} "
                    f"{investor.last_name}"
                )
                if investor
                else None,

            "investment_amount":
                item.investment_amount,

            "gross_commission":
                item.commission_amount,

            "paid_amount":
                item.paid_amount,

            "status":
                item.status,

            "payment_date":
                item.payment_date,

            "created_at":
                item.created_at
        })

    return response


# ============================================================
# Referral Commission Details
# ============================================================

@router.get("/commissions/{id}")
def commission_details(
    id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user = get_logged_in_user(
        current_user,
        db
    )

    commission = (
        db.query(ReferralCommission)
        .filter(
            ReferralCommission.id == id,
            ReferralCommission.enroller_id == user.id
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

    return {

        "id":
            commission.id,

        "investment_id":
            commission.investment_id,

        "investor_id":
            investor.user_id
            if investor
            else None,

        "investor_name":
            (
                f"{investor.first_name} "
                f"{investor.last_name}"
            )
            if investor
            else None,

        "investment_amount":
            commission.investment_amount,

        "commission_percentage":
            commission.commission_percentage,

        "gross_commission":
            commission.commission_amount,

        "paid_amount":
            commission.paid_amount,

        "status":
            commission.status,

        "payment_date":
            commission.payment_date,

        "created_at":
            commission.created_at
    }