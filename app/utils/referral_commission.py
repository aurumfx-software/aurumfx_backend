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

# def create_referral_commission(
#     db,
#     investment,
#     plan,
# ):
#     """
#     Create referral commission when an investment is approved.

#     Flow:

#         Investment Approved
#                 |
#                 v
#         Find Investor
#                 |
#                 v
#         Find Enroller
#                 |
#                 v
#         Check Enroller Active Investment
#                 |
#                 v
#         Find Referral Commission Setting
#                 |
#                 v
#         Calculate Gross Commission
#                 |
#                 v
#         Apply Daily Commission Limit
#                 |
#                 v
#         Calculate Washout
#                 |
#                 v
#         commission_amount = gross - washout
#                 |
#                 v
#         Save ReferralCommission as PENDING
#                 |
#                 v
#         Add commission_amount to Wallet.pending_balance
#                 |
#                 v
#         Create WalletTransaction as PENDING

#     IMPORTANT:

#     Admin fee is NOT deducted here.

#     Admin fee will be deducted later during admin payout
#     from the user's total pending income:

#         Referral
#         + Level
#         + Rank
#     """

#     # ======================================================
#     # INVESTOR
#     # ======================================================

#     investor = (
#         db.query(User)
#         .filter(
#             User.id == investment.user_id
#         )
#         .first()
#     )

#     if not investor:

#         print(
#             "Referral commission skipped: "
#             "Investor not found"
#         )

#         return None

#     # ============================================================
#     # FIND SPONSOR
#     # ============================================================

#     enroller = (
#         db.query(User)
#         .filter(
#             User.user_id == investment.enroller_id
#         )
#         .first()
#     )

#     if not enroller:
#         return


#     # ============================================================
#     # FIND SPONSOR ACTIVE + APPROVED INVESTMENT
#     # ============================================================

#     sponsor_investment = (
#         db.query(Investment)
#         .filter(
#             Investment.user_id == enroller.id,
#             Investment.investment_status == "ACTIVE",
#             Investment.approval_status == "APPROVED",
#         )
#         .order_by(
#             Investment.amount.desc()
#         )
#         .first()
#     )

#     if not sponsor_investment:
#         return


#     # ============================================================
#     # SPONSOR INVESTMENT DETAILS
#     # ============================================================

#     sponsor_plan_id = sponsor_investment.investment_plan_id

#     sponsor_investment_amount = float(
#         sponsor_investment.amount or 0
#     )


#     # ============================================================
#     # FIND REFERRAL COMMISSION SETTING
#     #
#     # Match:
#     #   1. Sponsor's investment plan
#     #   2. Sponsor's investment amount
#     # ============================================================

#     referral_setting = (
#         db.query(ReferralCommissionSetting)
#         .filter(
#             ReferralCommissionSetting.investment_plan_id
#             == sponsor_plan_id,

#             ReferralCommissionSetting.minimum_amount
#             <= sponsor_investment_amount,

#             ReferralCommissionSetting.status == True,
#         )
#         .filter(
#             (
#                 ReferralCommissionSetting.maximum_amount.is_(None)
#             )
#             |
#             (
#                 ReferralCommissionSetting.maximum_amount
#                 >= sponsor_investment_amount
#             )
#         )
#         .order_by(
#             ReferralCommissionSetting.minimum_amount.desc()
#         )
#         .first()
#     )


#     # ============================================================
#     # NO MATCHING REFERRAL SETTING
#     # ============================================================

#     if not referral_setting:
#         return

#     # ============================================================
#     # INVESTOR INVESTMENT AMOUNT
#     # This is the amount on which commission is calculated
#     # ============================================================

#     investment_amount = float(
#         investment.amount or 0
#     )
#     # ============================================================
#     # CALCULATE COMMISSION
#     #
#     # IMPORTANT:
#     # Percentage is selected using SPONSOR investment.
#     # Commission amount is calculated using INVESTOR investment.
#     # ============================================================

#     commission_percentage = float(
#         referral_setting.commission_percentage or 0
#     )

#     investor_investment_amount = float(
#         investment.amount or 0
#     )

#     gross_commission = (
#         investor_investment_amount
#         * commission_percentage
#     ) / 100

#     # ======================================================
#     # DAILY COMMISSION LIMIT
#     # ======================================================

#     washout_amount = 0.0

#     daily_limit = float(
#         referral_setting.daily_commission_limit
#         or 0
#     )

#     # ======================================================
#     # CHECK TODAY'S COMMISSION
#     # ======================================================

#     if daily_limit > 0:

#         today_commission = (
#             db.query(
#                 func.coalesce(
#                     func.sum(
#                         ReferralCommission.commission_amount
#                     ),
#                     0,
#                 )
#             )
#             .filter(
#                 ReferralCommission.enroller_id
#                 == enroller.id,

#                 ReferralCommission.status
#                 == "PENDING",

#                 func.date(
#                     ReferralCommission.created_at
#                 )
#                 == func.current_date(),
#             )
#             .scalar()
#             or 0
#         )

#         today_commission = float(
#             today_commission
#         )

#         # ==================================================
#         # REMAINING DAILY LIMIT
#         # ==================================================

#         remaining_limit = (
#             daily_limit
#             - today_commission
#         )

#         # ==================================================
#         # DAILY LIMIT ALREADY REACHED
#         # ==================================================

#         if remaining_limit <= 0:

#             washout_amount = (
#                 gross_commission
#             )

#         # ==================================================
#         # COMMISSION EXCEEDS REMAINING LIMIT
#         # ==================================================

#         elif gross_commission > remaining_limit:

#             washout_amount = (
#                 gross_commission
#                 - remaining_limit
#             )

#     else:

#         # No daily limit
#         today_commission = 0.0
#         remaining_limit = 0.0

#     # ======================================================
#     # FINAL COMMISSION AFTER WASHOUT
#     # ======================================================

#     commission_amount = (
#         gross_commission
#         - washout_amount
#     )

#     # ======================================================
#     # PREVENT NEGATIVE VALUE
#     # ======================================================

#     if commission_amount < 0:

#         commission_amount = 0.0

#     # ======================================================
#     # WALLET
#     # ======================================================

#     wallet = (
#         db.query(Wallet)
#         .filter(
#             Wallet.user_id
#             == enroller.id
#         )
#         .first()
#     )

#     # ======================================================
#     # CREATE WALLET IF NOT EXISTS
#     # ======================================================

#     if not wallet:

#         wallet = Wallet(
#             user_id=enroller.id,

#             # Paid / available balance
#             balance=0,

#             # Pending income
#             pending_balance=0,

#             # Admin fee accumulated during payout
#             admin_fee=0,
#         )

#         db.add(wallet)

#         db.flush()

#     # ======================================================
#     # PENDING WALLET BALANCE
#     # ======================================================

#     pending_before = float(
#         wallet.pending_balance or 0
#     )

#     # ======================================================
#     # ADD FINAL COMMISSION TO PENDING BALANCE
#     #
#     # IMPORTANT:
#     #
#     # commission_amount already excludes washout.
#     #
#     # Example:
#     #
#     # Gross       = 10,000
#     # Washout     = 3,000
#     # Commission  = 7,000
#     #
#     # Wallet gets only 7,000.
#     # ======================================================

#     wallet.pending_balance = (
#         pending_before
#         + commission_amount
#     )

#     # ======================================================
#     # REFERRAL COMMISSION HISTORY
#     # ======================================================

#     commission_history = ReferralCommission(

#         investment_id=investment.id,

#         investor_id=investor.id,

#         enroller_id=enroller.id,

#         investment_amount=investment.amount,

#         commission_percentage=commission_percentage,

#         # ==================================================
#         # IMPORTANT
#         #
#         # commission_amount is FINAL amount AFTER WASHOUT
#         # ==================================================

#         commission_amount=commission_amount,

#         # ==================================================
#         # Nothing paid yet
#         # ==================================================

#         paid_amount=0,

#         # ==================================================
#         # Amount removed because of daily limit
#         # ==================================================

#         washout_amount=washout_amount,

#         # ==================================================
#         # Income is pending
#         # ==================================================

#         status="PENDING",
#     )

#     db.add(
#         commission_history
#     )

#     # ======================================================
#     # WALLET TRANSACTION
#     # ======================================================

#     wallet_transaction = WalletTransaction(

#         wallet_id=wallet.id,

#         investment_id=investment.id,

#         # ==================================================
#         # Only final commission is added
#         # ==================================================

#         amount=commission_amount,

#         transaction_type="REFERRAL",

#         # ==================================================
#         # Income generated but not paid yet
#         # ==================================================

#         status="PENDING",

#         remarks=(
#             f"Referral Commission from "
#             f"{investor.user_id}"
#         ),
#     )

#     db.add(
#         wallet_transaction
#     )

#     # ======================================================
#     # FLUSH
#     # ======================================================

#     db.flush()

#     # ======================================================
#     # LOG
#     # ======================================================

#     print(
#         "--------------------------------------"
#     )

#     print(
#         "REFERRAL COMMISSION"
#     )

#     print(
#         "--------------------------------------"
#     )

#     print(
#         "Investor:",
#         investor.user_id
#     )

#     print(
#         "Enroller:",
#         enroller.user_id
#     )

#     print(
#         "Investment:",
#         investment_amount
#     )

#     print(
#         "Referral %:",
#         commission_percentage
#     )

#     print(
#         "Gross Commission:",
#         gross_commission
#     )

#     print(
#         "Daily Limit:",
#         daily_limit
#     )

#     print(
#         "Today's Commission:",
#         today_commission
#     )

#     print(
#         "Remaining Daily Limit:",
#         remaining_limit
#     )

#     print(
#         "Washout:",
#         washout_amount
#     )

#     print(
#         "Final Commission:",
#         commission_amount
#     )

#     print(
#         "Commission Status:",
#         "PENDING"
#     )

#     print(
#         "Wallet Pending Before:",
#         pending_before
#     )

#     print(
#         "Wallet Pending After:",
#         wallet.pending_balance
#     )

#     print(
#         "Admin Fee:",
#         "NOT DEDUCTED"
#     )

#     print(
#         "--------------------------------------"
#     )

#     return commission_history

def create_referral_commission(
    db,
    investment,
    plan,
):
    """
    Create referral commission for the sponsor.

    Rules:
    1. Sponsor is found from investment.enroller_id -> User.user_id
    2. Sponsor must have ACTIVE + APPROVED investment
    3. Referral setting plan must match INVESTOR's investment plan
    4. Referral setting amount range is checked against SPONSOR's investment amount
    5. Commission = SPONSOR investment amount × matched percentage
    """

    # ============================================================
    # FIND INVESTOR
    # ============================================================

    investor = (
        db.query(User)
        .filter(User.id == investment.user_id)
        .first()
    )

    if not investor:
        return None

    # ============================================================
    # FIND SPONSOR / ENROLLER
    # investment.enroller_id = sponsor's public user_id
    # ============================================================

    if not investment.enroller_id:
        return None

    enroller = (
        db.query(User)
        .filter(
            User.user_id == investment.enroller_id,
            User.status == "ACTIVE",
        )
        .first()
    )

    if not enroller:
        return None

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
        return None

    # ============================================================
    # SPONSOR INVESTMENT AMOUNT
    # ============================================================

    sponsor_investment_amount = float(
        sponsor_investment.amount or 0
    )

    if sponsor_investment_amount <= 0:
        return None

    # ============================================================
    # FIND REFERRAL COMMISSION SETTING
    #
    # PLAN:
    #     Investor's investment plan
    #
    # AMOUNT:
    #     Sponsor's investment amount
    # ============================================================

    referral_setting = (
        db.query(ReferralCommissionSetting)
        .filter(
            # IMPORTANT:
            # Setting plan = INVESTOR plan
            ReferralCommissionSetting.investment_plan_id
            == investment.investment_plan_id,

            # Sponsor amount must be >= minimum
            ReferralCommissionSetting.minimum_amount
            <= sponsor_investment_amount,

            # Setting must be active
            ReferralCommissionSetting.status == True,
        )
        .filter(
            # Maximum can be NULL = unlimited
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

    if not referral_setting:
        return None

    # ============================================================
    # COMMISSION PERCENTAGE
    # ============================================================

    commission_percentage = float(
        referral_setting.commission_percentage or 0
    )

    if commission_percentage <= 0:
        return None

    # ============================================================
    # CALCULATE GROSS COMMISSION
    #
    # Sponsor Investment Amount × Percentage
    # ============================================================

    gross_commission = (
        sponsor_investment_amount
        * commission_percentage
    ) / 100

    if gross_commission <= 0:
        return None

    # ============================================================
    # DAILY COMMISSION LIMIT / WASHOUT
    # ============================================================

    washout_amount = 0.0

    daily_limit = float(
        referral_setting.daily_commission_limit or 0
    )

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
                ReferralCommission.enroller_id == enroller.id,

                ReferralCommission.status == "PENDING",

                func.date(
                    ReferralCommission.created_at
                ) == func.current_date(),
            )
            .scalar()
            or 0
        )

        today_commission = float(today_commission)

        remaining_limit = (
            daily_limit - today_commission
        )

        if remaining_limit <= 0:

            washout_amount = gross_commission

        elif gross_commission > remaining_limit:

            washout_amount = (
                gross_commission
                - remaining_limit
            )

    else:

        today_commission = 0.0
        remaining_limit = 0.0

    # ============================================================
    # FINAL COMMISSION
    # ============================================================

    commission_amount = (
        gross_commission
        - washout_amount
    )

    if commission_amount < 0:
        commission_amount = 0.0

    # ============================================================
    # GET / CREATE SPONSOR WALLET
    # ============================================================

    wallet = (
        db.query(Wallet)
        .filter(
            Wallet.user_id == enroller.id
        )
        .first()
    )

    if not wallet:

        wallet = Wallet(
            user_id=enroller.id,
            balance=0,
            pending_balance=0,
            admin_fee=0,
        )

        db.add(wallet)
        db.flush()

    # ============================================================
    # UPDATE PENDING WALLET
    # ============================================================

    pending_before = float(
        wallet.pending_balance or 0
    )

    wallet.pending_balance = (
        pending_before
        + commission_amount
    )

    # ============================================================
    # CREATE REFERRAL COMMISSION HISTORY
    # ============================================================

    commission_history = ReferralCommission(
        investment_id=investment.id,

        investor_id=investor.id,

        enroller_id=enroller.id,

        # Store SPONSOR investment amount as commission base
        investment_amount=sponsor_investment_amount,

        commission_percentage=commission_percentage,

        commission_amount=commission_amount,

        paid_amount=0,

        washout_amount=washout_amount,

        status="PENDING",
    )

    db.add(commission_history)

    # ============================================================
    # CREATE WALLET TRANSACTION
    # ============================================================

    wallet_transaction = WalletTransaction(
        wallet_id=wallet.id,

        investment_id=investment.id,

        amount=commission_amount,

        transaction_type="REFERRAL",

        status="PENDING",

        remarks=(
            f"Referral Commission from "
            f"{investor.user_id}"
        ),
    )

    db.add(wallet_transaction)

    db.flush()

    # ============================================================
    # LOG
    # ============================================================

    print(
        "============================================"
    )
    print("REFERRAL COMMISSION")
    print(
        f"Investor       : {investor.user_id}"
    )
    print(
        f"Sponsor        : {enroller.user_id}"
    )
    print(
        f"Investor Plan  : {investment.investment_plan_id}"
    )
    print(
        f"Sponsor Invest : {sponsor_investment_amount}"
    )
    print(
        f"Percentage     : {commission_percentage}%"
    )
    print(
        f"Gross          : {gross_commission}"
    )
    print(
        f"Daily Limit    : {daily_limit}"
    )
    print(
        f"Today Income   : {today_commission}"
    )
    print(
        f"Remaining      : {remaining_limit}"
    )
    print(
        f"Washout        : {washout_amount}"
    )
    print(
        f"Final Commission: {commission_amount}"
    )
    print(
        f"Wallet Pending Before: {pending_before}"
    )
    print(
        f"Wallet Pending After : {wallet.pending_balance}"
    )
    print(
        "============================================"
    )

    return commission_history