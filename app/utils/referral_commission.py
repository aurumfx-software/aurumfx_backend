from sqlalchemy import func

from app.models import (
    Wallet,
    WalletTransaction,
    ReferralCommission,
    ReferralCommissionSetting,
    User,
    Investment,
)


# ==========================================================
# CREATE REFERRAL COMMISSION
# ==========================================================

def create_referral_commission(
    db,
    investment,
    plan,
):
    """
    Create referral commission when an investment is approved.

    Flow:

        Investment Approved
                |
                v
        Find Investor
                |
                v
        Find Enroller
                |
                v
        Check Enroller Active Investment
                |
                v
        Find Referral Commission Setting
                |
                v
        Calculate Gross Commission
                |
                v
        Apply Daily Commission Limit
                |
                v
        Calculate Washout
                |
                v
        commission_amount = gross - washout
                |
                v
        Save ReferralCommission as PENDING
                |
                v
        Add commission_amount to Wallet.pending_balance
                |
                v
        Create WalletTransaction as PENDING

    IMPORTANT:

    Admin fee is NOT deducted here.

    Admin fee will be deducted later during admin payout
    from the user's total pending income:

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

    # ============================================================
    # FIND SPONSOR
    # ============================================================

    enroller = (
        db.query(User)
        .filter(
            User.user_id == investment.enroller_id
        )
        .first()
    )

    if not enroller:
        return


    # ============================================================
    # FIND SPONSOR ACTIVE + APPROVED INVESTMENT
    # ============================================================

    sponsor_investment = (
        db.query(Investment)
        .filter(
            Investment.user_id == enroller.id,
            Investment.investment_status == "ACTIVE",
            Investment.approval_status == "APPROVED",
        )
        .order_by(
            Investment.amount.desc()
        )
        .first()
    )

    if not sponsor_investment:
        return


    # ============================================================
    # SPONSOR INVESTMENT DETAILS
    # ============================================================

    sponsor_plan_id = sponsor_investment.investment_plan_id

    sponsor_investment_amount = float(
        sponsor_investment.amount or 0
    )


    # ============================================================
    # FIND REFERRAL COMMISSION SETTING
    #
    # Match:
    #   1. Sponsor's investment plan
    #   2. Sponsor's investment amount
    # ============================================================

    referral_setting = (
        db.query(ReferralCommissionSetting)
        .filter(
            ReferralCommissionSetting.investment_plan_id
            == sponsor_plan_id,

            ReferralCommissionSetting.minimum_amount
            <= sponsor_investment_amount,

            ReferralCommissionSetting.status == True,
        )
        .filter(
            (
                ReferralCommissionSetting.maximum_amount.is_(None)
            )
            |
            (
                ReferralCommissionSetting.maximum_amount
                >= sponsor_investment_amount
            )
        )
        .order_by(
            ReferralCommissionSetting.minimum_amount.desc()
        )
        .first()
    )


    # ============================================================
    # NO MATCHING REFERRAL SETTING
    # ============================================================

    if not referral_setting:
        return

    # ============================================================
    # INVESTOR INVESTMENT AMOUNT
    # This is the amount on which commission is calculated
    # ============================================================

    investment_amount = float(
        investment.amount or 0
    )
    # ============================================================
    # CALCULATE COMMISSION
    #
    # IMPORTANT:
    # Percentage is selected using SPONSOR investment.
    # Commission amount is calculated using INVESTOR investment.
    # ============================================================

    commission_percentage = float(
        referral_setting.commission_percentage or 0
    )

    investor_investment_amount = float(
        investment.amount or 0
    )

    gross_commission = (
        investor_investment_amount
        * commission_percentage
    ) / 100

    # ======================================================
    # DAILY COMMISSION LIMIT
    # ======================================================

    washout_amount = 0.0

    daily_limit = float(
        referral_setting.daily_commission_limit
        or 0
    )

    # ======================================================
    # CHECK TODAY'S COMMISSION
    # ======================================================

    if daily_limit > 0:

        today_commission = (
            db.query(
                func.coalesce(
                    func.sum(
                        ReferralCommission.commission_amount
                    ),
                    0,
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
                == func.current_date(),
            )
            .scalar()
            or 0
        )

        today_commission = float(
            today_commission
        )

        # ==================================================
        # REMAINING DAILY LIMIT
        # ==================================================

        remaining_limit = (
            daily_limit
            - today_commission
        )

        # ==================================================
        # DAILY LIMIT ALREADY REACHED
        # ==================================================

        if remaining_limit <= 0:

            washout_amount = (
                gross_commission
            )

        # ==================================================
        # COMMISSION EXCEEDS REMAINING LIMIT
        # ==================================================

        elif gross_commission > remaining_limit:

            washout_amount = (
                gross_commission
                - remaining_limit
            )

    else:

        # No daily limit
        today_commission = 0.0
        remaining_limit = 0.0

    # ======================================================
    # FINAL COMMISSION AFTER WASHOUT
    # ======================================================

    commission_amount = (
        gross_commission
        - washout_amount
    )

    # ======================================================
    # PREVENT NEGATIVE VALUE
    # ======================================================

    if commission_amount < 0:

        commission_amount = 0.0

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

            # Paid / available balance
            balance=0,

            # Pending income
            pending_balance=0,

            # Admin fee accumulated during payout
            admin_fee=0,
        )

        db.add(wallet)

        db.flush()

    # ======================================================
    # PENDING WALLET BALANCE
    # ======================================================

    pending_before = float(
        wallet.pending_balance or 0
    )

    # ======================================================
    # ADD FINAL COMMISSION TO PENDING BALANCE
    #
    # IMPORTANT:
    #
    # commission_amount already excludes washout.
    #
    # Example:
    #
    # Gross       = 10,000
    # Washout     = 3,000
    # Commission  = 7,000
    #
    # Wallet gets only 7,000.
    # ======================================================

    wallet.pending_balance = (
        pending_before
        + commission_amount
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

        # ==================================================
        # IMPORTANT
        #
        # commission_amount is FINAL amount AFTER WASHOUT
        # ==================================================

        commission_amount=commission_amount,

        # ==================================================
        # Nothing paid yet
        # ==================================================

        paid_amount=0,

        # ==================================================
        # Amount removed because of daily limit
        # ==================================================

        washout_amount=washout_amount,

        # ==================================================
        # Income is pending
        # ==================================================

        status="PENDING",
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

        # ==================================================
        # Only final commission is added
        # ==================================================

        amount=commission_amount,

        transaction_type="REFERRAL",

        # ==================================================
        # Income generated but not paid yet
        # ==================================================

        status="PENDING",

        remarks=(
            f"Referral Commission from "
            f"{investor.user_id}"
        ),
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
        "Today's Commission:",
        today_commission
    )

    print(
        "Remaining Daily Limit:",
        remaining_limit
    )

    print(
        "Washout:",
        washout_amount
    )

    print(
        "Final Commission:",
        commission_amount
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