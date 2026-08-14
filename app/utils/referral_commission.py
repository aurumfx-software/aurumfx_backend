from sqlalchemy import func

from app.models import (
    Wallet,
    WalletTransaction,
    ReferralCommission,
    ReferralCommissionSetting,
    User,
    Investment
)


# ==========================================================
# CREATE REFERRAL COMMISSION
# ==========================================================

def create_referral_commission(
    db,
    investment,
    plan
):
    """
    Create referral commission when an investment is approved.

    Flow:

        Investment Approved
                |
                v
        Calculate Referral Income
                |
                v
        Apply Daily Commission Limit
                |
                v
        Store ReferralCommission as PENDING
                |
                v
        Add amount to Wallet.pending_balance
                |
                v
        Create WalletTransaction as PENDING

    IMPORTANT:

    Admin fee is NOT deducted here.

    Admin fee will be deducted later during admin payout
    from the user's TOTAL pending income:

        Referral
        + Level
        + Rank
    """

    # ======================================================
    # INVESTOR
    # ======================================================

    investor = (
        db.query(User)
        .filter(
            User.id == investment.user_id
        )
        .first()
    )

    if not investor:
        print(
            "Referral commission skipped: "
            "Investor not found"
        )
        return None

    # ======================================================
    # ENROLLER
    # ======================================================

    enroller = (
        db.query(User)
        .filter(
            User.user_id == investment.enroller_id
        )
        .first()
    )

    if not enroller:
        print(
            "Referral commission skipped: "
            "Enroller not found"
        )
        return None

    # ======================================================
# CHECK ENROLLER ACTIVE INVESTMENT
# ======================================================

    active_investment = (
        db.query(Investment)
        .filter(
            Investment.user_id == enroller.id,
            Investment.investment_status == "ACTIVE"
        )
        .first()
    )

    if not active_investment:
        print(
            "Referral commission skipped: "
            f"Enroller {enroller.user_id} has no active investment"
        )
        return None

    # ======================================================
    # REFERRAL COMMISSION SETTING
    # ======================================================

    referral_setting = (
        db.query(
            ReferralCommissionSetting
        )
        .filter(
            ReferralCommissionSetting.investment_plan_id
            == investment.investment_plan_id,

            ReferralCommissionSetting.minimum_amount
            <= investment.amount,

            ReferralCommissionSetting.status == True
        )
        .filter(
            (
                ReferralCommissionSetting.maximum_amount
                == None
            )
            |
            (
                ReferralCommissionSetting.maximum_amount
                >= investment.amount
            )
        )
        .order_by(
            ReferralCommissionSetting.minimum_amount.desc()
        )
        .first()
    )

    # ======================================================
    # NO REFERRAL SETTING
    # ======================================================

    if not referral_setting:

        print(
            "Referral commission skipped: "
            "No matching referral setting"
        )

        return None

    # ======================================================
    # COMMISSION PERCENTAGE
    # ======================================================

    commission_percentage = float(
        referral_setting.commission_percentage
        or 0
    )

    # ======================================================
    # GROSS REFERRAL COMMISSION
    # ======================================================

    investment_amount = float(
        investment.amount or 0
    )

    gross_commission = (
        investment_amount
        * commission_percentage
    ) / 100

    # ======================================================
    # DAILY COMMISSION LIMIT
    #
    # Admin fee is NOT considered here.
    #
    # Daily limit is applied to referral income itself.
    # ======================================================

    washout_amount = 0.0

    daily_limit = float(
        referral_setting.daily_commission_limit or 0
    )

    if daily_limit > 0:

        today_pending = (
            db.query(
                func.coalesce(
                    func.sum(
                        ReferralCommission.commission_amount
                    ),
                    0
                )
            )
            .filter(
                ReferralCommission.enroller_id
                == enroller.id,

                ReferralCommission.status
                == "PENDING",

                func.date(
                    ReferralCommission.created_at
                )
                == func.current_date()
            )
            .scalar()
            or 0
        )

        today_pending = float(
            today_pending
        )

        remaining_limit = (
            daily_limit
            - today_pending
        )

        # --------------------------------------------------
        # Daily limit already reached
        # --------------------------------------------------

        if remaining_limit <= 0:

            washout_amount = (
                gross_commission
            )

        # --------------------------------------------------
        # Commission exceeds remaining limit
        # --------------------------------------------------

        elif gross_commission > remaining_limit:

            washout_amount = (
                gross_commission
                - remaining_limit
            )

    # ======================================================
    # FINAL REFERRAL INCOME
    # ======================================================

    final_amount = (
        gross_commission
        - washout_amount
    )

    # Prevent negative value
    if final_amount < 0:
        final_amount = 0.0

    # ======================================================
    # WALLET
    # ======================================================

    wallet = (
        db.query(Wallet)
        .filter(
            Wallet.user_id
            == enroller.id
        )
        .first()
    )

    # ======================================================
    # CREATE WALLET IF NOT EXISTS
    # ======================================================

    if not wallet:

        wallet = Wallet(
            user_id=enroller.id,

            # Paid/available balance
            balance=0,

            # Pending income
            pending_balance=0,

            # Admin fee accumulated during payout
            admin_fee=0
        )

        db.add(wallet)

        db.flush()

    # ======================================================
    # PENDING WALLET BALANCE
    # ======================================================

    pending_before = float(
        wallet.pending_balance or 0
    )

    # ------------------------------------------------------
    # IMPORTANT
    #
    # Referral income is PENDING.
    #
    # Therefore:
    #
    #     pending_balance += final_amount
    #
    # NOT:
    #
    #     balance += final_amount
    # ------------------------------------------------------

    wallet.pending_balance = (
        pending_before
        + final_amount
    )

    # ======================================================
    # REFERRAL COMMISSION HISTORY
    # ======================================================

    commission_history = ReferralCommission(

        investment_id=investment.id,

        investor_id=investor.id,

        enroller_id=enroller.id,

        investment_amount=investment.amount,

        commission_percentage=commission_percentage,

        commission_amount=gross_commission,

        # --------------------------------------------------
        # Admin fee is intentionally NOT stored here.
        # --------------------------------------------------
        #
        # admin_fee_percentage = removed
        # admin_fee_amount = removed
        #
        # Admin fee is calculated during payout from:
        #
        # referral + level + rank
        #

        paid_amount=0,

        washout_amount=washout_amount,

        status="PENDING"
    )

    db.add(
        commission_history
    )

    # ======================================================
    # WALLET TRANSACTION
    # ======================================================

    wallet_transaction = WalletTransaction(

        wallet_id=wallet.id,

        investment_id=investment.id,

        amount=final_amount,

        transaction_type="REFERRAL",

        # --------------------------------------------------
        # IMPORTANT
        #
        # Income is generated but not paid yet.
        # --------------------------------------------------

        status="PENDING",

        remarks=(
            f"Referral Commission from "
            f"{investor.user_id}"
        )
    )

    db.add(
        wallet_transaction
    )

    # ======================================================
    # FLUSH
    # ======================================================

    db.flush()

    # ======================================================
    # LOG
    # ======================================================

    print(
        "--------------------------------------"
    )

    print(
        "REFERRAL COMMISSION"
    )

    print(
        "--------------------------------------"
    )

    print(
        "Investor:",
        investor.user_id
    )

    print(
        "Enroller:",
        enroller.user_id
    )

    print(
        "Investment:",
        investment_amount
    )

    print(
        "Referral %:",
        commission_percentage
    )

    print(
        "Gross Commission:",
        gross_commission
    )

    print(
        "Daily Limit:",
        daily_limit
    )

    print(
        "Washout:",
        washout_amount
    )

    print(
        "Final Referral Income:",
        final_amount
    )

    print(
        "Commission Status:",
        "PENDING"
    )

    print(
        "Wallet Pending Before:",
        pending_before
    )

    print(
        "Wallet Pending After:",
        wallet.pending_balance
    )

    print(
        "Admin Fee:",
        "NOT DEDUCTED"
    )

    print(
        "--------------------------------------"
    )

    return commission_history