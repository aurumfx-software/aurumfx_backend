# from sqlalchemy import func

# from app.models import (
#     Wallet,
#     WalletTransaction,
#     ReferralCommission,
#     ReferralCommissionSetting,
#     User,
#     Investment,
# )


# def create_referral_commission(
#     db,
#     investment,
#     plan,
# ):
#     """
#     Create referral commission for the sponsor.

#     Rules:
#     1. Sponsor is found from investment.enroller_id -> User.user_id
#     2. Sponsor must have ACTIVE + APPROVED investment
#     3. Referral setting plan must match INVESTOR's investment plan
#     4. Referral setting amount range is checked against SPONSOR's investment amount
#     5. Commission = SPONSOR investment amount × matched percentage
#     """

#     # ============================================================
#     # FIND INVESTOR
#     # ============================================================

#     investor = (
#         db.query(User)
#         .filter(User.id == investment.user_id)
#         .first()
#     )

#     if not investor:
#         return None

#     # ============================================================
#     # FIND SPONSOR / ENROLLER
#     # investment.enroller_id = sponsor's public user_id
#     # ============================================================

#     if not investment.enroller_id:
#         return None

#     enroller = (
#         db.query(User)
#         .filter(
#             User.user_id == investment.enroller_id,
#             User.status == "ACTIVE",
#         )
#         .first()
#     )

#     if not enroller:
#         return None

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
#         return None

#     # ============================================================
#     # SPONSOR INVESTMENT AMOUNT
#     # ============================================================

#     sponsor_investment_amount = float(
#         sponsor_investment.amount or 0
#     )

#     if sponsor_investment_amount <= 0:
#         return None

#     # ============================================================
#     # FIND REFERRAL COMMISSION SETTING
#     #
#     # PLAN:
#     #     Investor's investment plan
#     #
#     # AMOUNT:
#     #     Sponsor's investment amount
#     # ============================================================

#     referral_setting = (
#         db.query(ReferralCommissionSetting)
#         .filter(
#             # IMPORTANT:
#             # Setting plan = INVESTOR plan
#             ReferralCommissionSetting.investment_plan_id
#             == investment.investment_plan_id,

#             # Sponsor amount must be >= minimum
#             ReferralCommissionSetting.minimum_amount
#             <= sponsor_investment_amount,

#             # Setting must be active
#             ReferralCommissionSetting.status == True,
#         )
#         .filter(
#             # Maximum can be NULL = unlimited
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

#     if not referral_setting:
#         return None

#     # ============================================================
#     # COMMISSION PERCENTAGE
#     # ============================================================

#     commission_percentage = float(
#         referral_setting.commission_percentage or 0
#     )

#     if commission_percentage <= 0:
#         return None

#     # ============================================================
#     # CALCULATE GROSS COMMISSION
#     #
#     #  Investmenter Amount × Percentage
#     # ============================================================

#     gross_commission = (
#         investment.amount
#         * commission_percentage
#     ) / 100

#     if gross_commission <= 0:
#         return None

#     # ============================================================
#     # DAILY COMMISSION LIMIT / WASHOUT
#     # ============================================================

#     washout_amount = 0.0

#     daily_limit = float(
#         referral_setting.daily_commission_limit or 0
#     )

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
#                 ReferralCommission.enroller_id == enroller.id,

#                 ReferralCommission.status == "PENDING",

#                 func.date(
#                     ReferralCommission.created_at
#                 ) == func.current_date(),
#             )
#             .scalar()
#             or 0
#         )

#         today_commission = float(today_commission)

#         remaining_limit = (
#             daily_limit - today_commission
#         )

#         if remaining_limit <= 0:

#             washout_amount = gross_commission

#         elif gross_commission > remaining_limit:

#             washout_amount = (
#                 gross_commission
#                 - remaining_limit
#             )

#     else:

#         today_commission = 0.0
#         remaining_limit = 0.0

#     # ============================================================
#     # FINAL COMMISSION
#     # ============================================================

#     commission_amount = (
#         gross_commission
#         - washout_amount
#     )

#     if commission_amount < 0:
#         commission_amount = 0.0

#     # ============================================================
#     # GET / CREATE SPONSOR WALLET
#     # ============================================================

#     wallet = (
#         db.query(Wallet)
#         .filter(
#             Wallet.user_id == enroller.id
#         )
#         .first()
#     )

#     if not wallet:

#         wallet = Wallet(
#             user_id=enroller.id,
#             balance=0,
#             pending_balance=0,
#             admin_fee=0,
#         )

#         db.add(wallet)
#         db.flush()

#     # ============================================================
#     # UPDATE PENDING WALLET
#     # ============================================================

#     pending_before = float(
#         wallet.pending_balance or 0
#     )

#     wallet.pending_balance = (
#         pending_before
#         + commission_amount
#     )

#     # ============================================================
#     # CREATE REFERRAL COMMISSION HISTORY
#     # ============================================================

#     commission_history = ReferralCommission(
#         investment_id=investment.id,

#         investor_id=investor.id,

#         enroller_id=enroller.id,

#         # Store SPONSOR investment amount as commission base
#         investment_amount=sponsor_investment_amount,

#         commission_percentage=commission_percentage,

#         commission_amount=commission_amount,

#         paid_amount=0,

#         washout_amount=washout_amount,

#         status="PENDING",
#     )

#     db.add(commission_history)

#     # ============================================================
#     # CREATE WALLET TRANSACTION
#     # ============================================================

#     wallet_transaction = WalletTransaction(
#         wallet_id=wallet.id,

#         investment_id=investment.id,

#         amount=commission_amount,

#         transaction_type="REFERRAL",

#         status="PENDING",

#         remarks=(
#             f"Referral Commission from "
#             f"{investor.user_id}"
#         ),
#     )

#     db.add(wallet_transaction)

#     db.flush()

#     # ============================================================
#     # LOG
#     # ============================================================

#     print(
#         "============================================"
#     )
#     print("REFERRAL COMMISSION")
#     print(
#         f"Investor       : {investor.user_id}"
#     )
#     print(
#         f"Sponsor        : {enroller.user_id}"
#     )
#     print(
#         f"Investor Plan  : {investment.investment_plan_id}"
#     )
#     print(
#         f"Sponsor Invest : {sponsor_investment_amount}"
#     )
#     print(
#         f"Percentage     : {commission_percentage}%"
#     )
#     print(
#         f"Gross          : {gross_commission}"
#     )
#     print(
#         f"Daily Limit    : {daily_limit}"
#     )
#     print(
#         f"Today Income   : {today_commission}"
#     )
#     print(
#         f"Remaining      : {remaining_limit}"
#     )
#     print(
#         f"Washout        : {washout_amount}"
#     )
#     print(
#         f"Final Commission: {commission_amount}"
#     )
#     print(
#         f"Wallet Pending Before: {pending_before}"
#     )
#     print(
#         f"Wallet Pending After : {wallet.pending_balance}"
#     )
#     print(
#         "============================================"
#     )

#     return commission_history


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
    Create referral commission for the sponsor.

    Rules:

    1. Sponsor is found from investment.enroller_id -> User.user_id
    2. Sponsor must have ACTIVE + APPROVED investment
    3. Referral setting plan must match INVESTOR's investment plan
    4. Referral setting amount range is checked against
       SPONSOR's investment amount
    5. Commission percentage is selected based on SPONSOR investment
    6. Commission amount is calculated from INVESTOR investment
    7. Daily limit is applied using approval date
    8. All generated records use investment.approval_status_updated_at
    9. Admin fee is NOT deducted here
    10. This function does NOT commit the transaction
    """

    # ============================================================
    # CHECK INVESTMENT
    # ============================================================

    if not investment:
        print("Referral commission skipped: Investment not found")
        return None

    # ============================================================
    # APPROVAL TIMESTAMP
    #
    # This is the single timestamp used for:
    #
    # ReferralCommission.created_at
    # Wallet.created_at
    # Wallet.updated_at
    # WalletTransaction.created_at
    # ============================================================

    approval_timestamp = investment.approval_status_updated_at

    if not approval_timestamp:
        print(
            "Referral commission skipped: "
            "approval_status_updated_at is NULL"
        )
        return None

    # ============================================================
    # FIND INVESTOR
    # ============================================================

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
    # FIND SPONSOR / ENROLLER
    #
    # investment.enroller_id contains sponsor's public user_id
    # ============================================================

    if not investment.enroller_id:
        print(
            "Referral commission skipped: "
            "Enroller not found in investment"
        )
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
        print(
            "Referral commission skipped: "
            "Active sponsor not found"
        )
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
        print(
            "Referral commission skipped: "
            "Sponsor has no ACTIVE + APPROVED investment"
        )
        return None

    # ============================================================
    # SPONSOR INVESTMENT AMOUNT
    #
    # Used to select referral percentage
    # ============================================================

    sponsor_investment_amount = float(
        sponsor_investment.amount or 0
    )

    if sponsor_investment_amount <= 0:
        print(
            "Referral commission skipped: "
            "Sponsor investment amount is zero"
        )
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
            ReferralCommissionSetting.investment_plan_id
            == investment.investment_plan_id,

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

    if not referral_setting:
        print(
            "Referral commission skipped: "
            "No matching referral setting"
        )
        return None

    # ============================================================
    # COMMISSION PERCENTAGE
    # ============================================================

    commission_percentage = float(
        referral_setting.commission_percentage or 0
    )

    if commission_percentage <= 0:
        print(
            "Referral commission skipped: "
            "Commission percentage is zero"
        )
        return None

    # ============================================================
    # INVESTOR INVESTMENT AMOUNT
    #
    # This is the amount used to calculate commission.
    # ============================================================

    investor_investment_amount = float(
        investment.amount or 0
    )

    if investor_investment_amount <= 0:
        print(
            "Referral commission skipped: "
            "Investor investment amount is zero"
        )
        return None

    # ============================================================
    # CALCULATE GROSS COMMISSION
    #
    # Investor Investment × Referral Percentage
    # ============================================================

    gross_commission = (
        investor_investment_amount
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

        # ========================================================
        # CHECK COMMISSION FOR APPROVAL DATE
        # ========================================================

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
                ) == approval_timestamp.date(),
            )
            .scalar()
            or 0
        )

        today_commission = float(
            today_commission
        )

        # ========================================================
        # REMAINING DAILY LIMIT
        # ========================================================

        remaining_limit = (
            daily_limit
            - today_commission
        )

        # ========================================================
        # LIMIT ALREADY REACHED
        # ========================================================

        if remaining_limit <= 0:

            washout_amount = gross_commission

        # ========================================================
        # COMMISSION EXCEEDS LIMIT
        # ========================================================

        elif gross_commission > remaining_limit:

            washout_amount = (
                gross_commission
                - remaining_limit
            )

    else:

        today_commission = 0.0
        remaining_limit = 0.0

    # ============================================================
    # FINAL COMMISSION AFTER WASHOUT
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

    # ============================================================
    # CREATE WALLET IF NOT EXISTS
    # ============================================================

    if not wallet:

        wallet = Wallet(
            user_id=enroller.id,

            balance=0,

            pending_balance=0,

            admin_fee=0,

            # IMPORTANT:
            # Use investment approval timestamp
            created_at=approval_timestamp,

            updated_at=approval_timestamp,
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

    # IMPORTANT:
    # Do NOT allow SQLAlchemy onupdate=datetime.utcnow
    # to replace our approval timestamp.
    wallet.updated_at = approval_timestamp

    db.flush()

    # ============================================================
    # CREATE REFERRAL COMMISSION HISTORY
    # ============================================================

    commission_history = ReferralCommission(

        investment_id=investment.id,

        investor_id=investor.id,

        enroller_id=enroller.id,

        # Investor investment is the actual
        # commission calculation base.
        investment_amount=investor_investment_amount,

        commission_percentage=commission_percentage,

        commission_amount=commission_amount,

        paid_amount=0,

        washout_amount=washout_amount,

        status="PENDING",

        # IMPORTANT:
        # Same timestamp as investment approval
        created_at=approval_timestamp,
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

        # IMPORTANT:
        # Same timestamp as investment approval
        created_at=approval_timestamp,
    )

    db.add(wallet_transaction)

    # ============================================================
    # FLUSH
    #
    # No commit here.
    # Approval API should commit everything together.
    # ============================================================

    db.flush()

    # ============================================================
    # LOG
    # ============================================================

    print("============================================")
    print("REFERRAL COMMISSION")
    print(f"Investor       : {investor.user_id}")
    print(f"Sponsor        : {enroller.user_id}")
    print(
        f"Investor Plan  : "
        f"{investment.investment_plan_id}"
    )
    print(
        f"Sponsor Invest : "
        f"{sponsor_investment_amount}"
    )
    print(
        f"Investor Invest: "
        f"{investor_investment_amount}"
    )
    print(
        f"Percentage     : "
        f"{commission_percentage}%"
    )
    print(
        f"Gross          : "
        f"{gross_commission}"
    )
    print(
        f"Daily Limit    : "
        f"{daily_limit}"
    )
    print(
        f"Approval Date  : "
        f"{approval_timestamp}"
    )
    print(
        f"Today Income   : "
        f"{today_commission}"
    )
    print(
        f"Remaining      : "
        f"{remaining_limit}"
    )
    print(
        f"Washout        : "
        f"{washout_amount}"
    )
    print(
        f"Final Commission: "
        f"{commission_amount}"
    )
    print(
        f"History Created: "
        f"{commission_history.created_at}"
    )
    print(
        f"Wallet Created : "
        f"{wallet.created_at}"
    )
    print(
        f"Wallet Updated : "
        f"{wallet.updated_at}"
    )
    print(
        f"Transaction Created: "
        f"{wallet_transaction.created_at}"
    )
    print(
        f"Wallet Pending Before: "
        f"{pending_before}"
    )
    print(
        f"Wallet Pending After : "
        f"{wallet.pending_balance}"
    )
    print("Commission Status: PENDING")
    print("Admin Fee: NOT DEDUCTED")
    print("============================================")

    return commission_history

