# from sqlalchemy.orm import Session

# from app.models import (
#     User,
#     Wallet,
#     WalletTransaction,
#     Investment,
#     LevelCommission,
#     LevelCommissionHistory,
# )


# # ==========================================================
# # GET LEVEL COMMISSION PERCENTAGE
# # ==========================================================

# def get_level_percentage(
#     db: Session,
#     level: int
# ):
#     """
#     Get commission percentage configured for a level.

#     Example:

#         Level 1 -> 10%
#         Level 2 -> 5%
#         Level 3 -> 3%

#     Only active commission settings are considered.
#     """

#     commission = (
#         db.query(LevelCommission)
#         .filter(
#             LevelCommission.level == level,
#             LevelCommission.status == 1
#         )
#         .first()
#     )

#     if not commission:
#         return 0.0

#     return float(
#         commission.commission_percentage or 0
#     )


# # ==========================================================
# # CHECK ACTIVE INVESTMENT
# # ==========================================================

# def has_active_investment(
#     db: Session,
#     user_id: int
# ):
#     """
#     Check whether a user has at least one ACTIVE investment.

#     Level commission is allowed only when the sponsor
#     has an active investment.
#     """

#     active_investment = (
#         db.query(Investment)
#         .filter(
#             Investment.user_id == user_id,
#             Investment.investment_status == "ACTIVE"
#         )
#         .first()
#     )

#     return active_investment is not None


# # ==========================================================
# # GET / CREATE USER WALLET
# # ==========================================================

# def get_or_create_wallet(
#     db: Session,
#     user_id: int
# ):
#     """
#     Get user's wallet.

#     If wallet does not exist, create it.

#     Wallet:

#         balance
#             = Paid / available balance

#         pending_balance
#             = Pending referral + level + rank income

#         admin_fee
#             = Admin fee accumulated during payout
#     """

#     wallet = (
#         db.query(Wallet)
#         .filter(
#             Wallet.user_id == user_id
#         )
#         .first()
#     )

#     if not wallet:

#         wallet = Wallet(
#             user_id=user_id,
#             balance=0,
#             pending_balance=0,
#             admin_fee=0
#         )

#         db.add(wallet)

#         db.flush()

#     return wallet


# # ==========================================================
# # ADD PENDING INCOME TO WALLET
# # ==========================================================

# def update_wallet(
#     db: Session,
#     user_id: int,
#     amount: float
# ):
#     """
#     Add level commission to pending_balance.

#     IMPORTANT:

#         wallet.balance is NOT changed.

#         wallet.pending_balance is increased.

#     Admin fee is NOT deducted here.
#     """

#     amount = float(
#         amount or 0
#     )

#     wallet = get_or_create_wallet(
#         db=db,
#         user_id=user_id
#     )

#     pending_before = float(
#         wallet.pending_balance or 0
#     )

#     wallet.pending_balance = (
#         pending_before + amount
#     )

#     db.flush()

#     return wallet


# # ==========================================================
# # CREATE PENDING WALLET TRANSACTION
# # ==========================================================

# def create_wallet_transaction(
#     db: Session,
#     wallet_id: int,
#     investment_id: int,
#     amount: float,
#     level: int
# ):
#     """
#     Create wallet transaction for level income.

#     Newly generated income is PENDING.
#     """

#     transaction = WalletTransaction(
#         wallet_id=wallet_id,

#         investment_id=investment_id,

#         amount=float(
#             amount or 0
#         ),

#         transaction_type="LEVEL_INCOME",

#         status="PENDING",

#         remarks=(
#             f"Level {level} Commission"
#         )
#     )

#     db.add(transaction)

#     db.flush()

#     return transaction


# # ==========================================================
# # SAVE LEVEL COMMISSION HISTORY
# # ==========================================================

# def save_level_history(
#     db: Session,
#     investment,
#     sponsor,
#     level: int,
#     percentage: float,
#     commission: float
# ):
#     """
#     Save level commission history.

#     Status remains PENDING until admin payout.
#     """

#     history = LevelCommissionHistory(
#         investment_id=investment.id,

#         investor_id=investment.user_id,

#         sponsor_id=sponsor.id,

#         level=level,

#         investment_amount=investment.amount,

#         commission_percentage=percentage,

#         commission_amount=commission,

#         status="PENDING"
#     )

#     db.add(history)

#     db.flush()

#     return history


# # ==========================================================
# # CALCULATE LEVEL COMMISSION
# # ==========================================================

# def calculate_level_commission(
#     db: Session,
#     investment: Investment
# ):
#     """
#     Calculate up to 15 levels of level commission.

#     BUSINESS RULE:

#         A sponsor receives level income ONLY when
#         that sponsor has at least one ACTIVE investment.

#     Example:

#         Investor
#            |
#            | Level 1
#            v
#         Sponsor A
#         ACTIVE investment
#         -> Gets Level 1 commission
#            |
#            | Level 2
#            v
#         Sponsor B
#         NO active investment
#         -> No Level 2 commission
#            |
#            | Level 3
#            v
#         Sponsor C
#         ACTIVE investment
#         -> Gets Level 3 commission

#     IMPORTANT:

#         If one sponsor has no active investment,
#         we SKIP that sponsor's commission but
#         continue traversing the genealogy.

#     Income flow:

#         Level Commission
#               |
#               v
#         LevelCommissionHistory
#               |
#               | PENDING
#               v
#         Wallet.pending_balance
#               |
#               v
#         WalletTransaction
#               |
#               | PENDING
#               v
#         Admin Payout

#     Admin fee is NOT calculated here.
#     """

#     # ======================================================
#     # VALIDATE INVESTMENT
#     # ======================================================

#     if not investment:

#         print(
#             "Level commission skipped: "
#             "Investment not provided"
#         )

#         return None

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
#             "Level commission skipped: "
#             "Investor not found"
#         )

#         return None

#     # ======================================================
#     # START FROM INVESTOR
#     # ======================================================

#     current_user = investor

#     level = 1

#     generated_histories = []

#     # ======================================================
#     # MAXIMUM 15 LEVELS
#     # ======================================================

#     while level <= 15:

#         # ==================================================
#         # CHECK CURRENT USER ENROLLER
#         # ==================================================

#         if not current_user.enroller_id:

#             print(
#                 f"No enroller found at level {level}"
#             )

#             break

#         # ==================================================
#         # FIND SPONSOR
#         # ==================================================

#         sponsor = (
#             db.query(User)
#             .filter(
#                 User.user_id
#                 == current_user.enroller_id
#             )
#             .first()
#         )

#         if not sponsor:

#             print(
#                 f"Sponsor not found at level {level}"
#             )

#             break

#         # ==================================================
#         # CHECK SPONSOR ACTIVE INVESTMENT
#         # ==================================================

#         sponsor_has_active_investment = (
#             has_active_investment(
#                 db=db,
#                 user_id=sponsor.id
#             )
#         )

#         if not sponsor_has_active_investment:

#             print(
#                 "--------------------------------------"
#             )

#             print(
#                 "LEVEL COMMISSION SKIPPED"
#             )

#             print(
#                 "--------------------------------------"
#             )

#             print(
#                 "Investor:",
#                 investor.user_id
#             )

#             print(
#                 "Sponsor:",
#                 sponsor.user_id
#             )

#             print(
#                 "Level:",
#                 level
#             )

#             print(
#                 "Reason:",
#                 "Sponsor has no ACTIVE investment"
#             )

#             print(
#                 "Commission:",
#                 0
#             )

#             print(
#                 "--------------------------------------"
#             )

#             # IMPORTANT:
#             #
#             # Do NOT break.
#             #
#             # Continue to next sponsor in genealogy.

#             current_user = sponsor

#             level += 1

#             continue

#         # ==================================================
#         # GET LEVEL COMMISSION %
#         # ==================================================

#         percentage = get_level_percentage(
#             db=db,
#             level=level
#         )

#         # ==================================================
#         # NO COMMISSION CONFIGURATION
#         # ==================================================

#         if percentage <= 0:

#             print(
#                 f"Level {level}: "
#                 f"No commission percentage configured"
#             )

#             current_user = sponsor

#             level += 1

#             continue

#         # ==================================================
#         # INVESTMENT AMOUNT
#         # ==================================================

#         investment_amount = float(
#             investment.amount or 0
#         )

#         # ==================================================
#         # CALCULATE COMMISSION
#         # ==================================================

#         commission = (
#             investment_amount
#             * percentage
#         ) / 100

#         # ==================================================
#         # SAFETY CHECK
#         # ==================================================

#         if commission <= 0:

#             print(
#                 f"Level {level}: "
#                 f"Commission amount is zero"
#             )

#             current_user = sponsor

#             level += 1

#             continue

#         # ==================================================
#         # SAVE LEVEL COMMISSION HISTORY
#         # ==================================================

#         history = save_level_history(
#             db=db,
#             investment=investment,
#             sponsor=sponsor,
#             level=level,
#             percentage=percentage,
#             commission=commission
#         )

#         generated_histories.append(
#             history
#         )

#         # ==================================================
#         # UPDATE SPONSOR PENDING WALLET
#         # ==================================================

#         wallet = update_wallet(
#             db=db,
#             user_id=sponsor.id,
#             amount=commission
#         )

#         # ==================================================
#         # CREATE PENDING WALLET TRANSACTION
#         # ==================================================

#         transaction = create_wallet_transaction(
#             db=db,
#             wallet_id=wallet.id,
#             investment_id=investment.id,
#             amount=commission,
#             level=level
#         )

#         # ==================================================
#         # LOG
#         # ==================================================

#         print(
#             "--------------------------------------"
#         )

#         print(
#             "LEVEL COMMISSION"
#         )

#         print(
#             "--------------------------------------"
#         )

#         print(
#             "Investor:",
#             investor.user_id
#         )

#         print(
#             "Sponsor:",
#             sponsor.user_id
#         )

#         print(
#             "Level:",
#             level
#         )

#         print(
#             "Sponsor Active Investment:",
#             "YES"
#         )

#         print(
#             "Investment:",
#             investment_amount
#         )

#         print(
#             "Percentage:",
#             percentage
#         )

#         print(
#             "Commission:",
#             commission
#         )

#         print(
#             "History Status:",
#             "PENDING"
#         )

#         print(
#             "Transaction Status:",
#             "PENDING"
#         )

#         print(
#             "Wallet Balance:",
#             wallet.balance
#         )

#         print(
#             "Wallet Pending Balance:",
#             wallet.pending_balance
#         )

#         print(
#             "Admin Fee:",
#             "NOT DEDUCTED"
#         )

#         print(
#             "--------------------------------------"
#         )

#         # ==================================================
#         # MOVE TO NEXT SPONSOR
#         # ==================================================

#         current_user = sponsor

#         level += 1

#     # ======================================================
#     # COMMIT
#     # ======================================================

#     db.commit()

#     # ======================================================
#     # REFRESH HISTORIES
#     # ======================================================

#     for history in generated_histories:

#         db.refresh(history)

#     # ======================================================
#     # FINAL LOG
#     # ======================================================

#     print(
#         "======================================"
#     )

#     print(
#         "LEVEL COMMISSION COMPLETED"
#     )

#     print(
#         "======================================"
#     )

#     print(
#         "Investor:",
#         investor.user_id
#     )

#     print(
#         "Levels Generated:",
#         len(generated_histories)
#     )

#     print(
#         "======================================"
#     )

#     return generated_histor
from sqlalchemy.orm import Session

from app.models import (
    User,
    Wallet,
    WalletTransaction,
    Investment,
    LevelCommission,
    LevelCommissionHistory,
)


# ==========================================================
# GET LEVEL COMMISSION PERCENTAGE
# ==========================================================

def get_level_percentage(
    db: Session,
    level: int
):
    commission = (
        db.query(LevelCommission)
        .filter(
            LevelCommission.level == level,
            LevelCommission.status == 1
        )
        .first()
    )

    if not commission:
        return 0.0

    return float(
        commission.commission_percentage or 0
    )


# ==========================================================
# CHECK ACTIVE + APPROVED INVESTMENT
# ==========================================================

def has_active_investment(
    db: Session,
    user_id: int
):
    """
    Sponsor must have an ACTIVE + APPROVED investment
    to receive level commission.
    """

    active_investment = (
        db.query(Investment)
        .filter(
            Investment.user_id == user_id,
            Investment.investment_status == "ACTIVE",
            Investment.approval_status == "APPROVED"
        )
        .first()
    )

    return active_investment is not None


# ==========================================================
# GET / CREATE USER WALLET
# ==========================================================

def get_or_create_wallet(
    db: Session,
    user_id: int,
    transaction_date
):
    """
    Get wallet.

    If wallet does not exist:
        created_at = investment approval timestamp
        updated_at = investment approval timestamp
    """

    wallet = (
        db.query(Wallet)
        .filter(
            Wallet.user_id == user_id
        )
        .first()
    )

    if not wallet:

        wallet = Wallet(
            user_id=user_id,
            balance=0,
            pending_balance=0,
            admin_fee=0,
            created_at=transaction_date,
            updated_at=transaction_date,
        )

        db.add(wallet)
        db.flush()

    return wallet


# ==========================================================
# ADD PENDING INCOME TO WALLET
# ==========================================================

def update_wallet(
    db: Session,
    user_id: int,
    amount: float,
    transaction_date
):
    """
    Add level commission to pending_balance.

    Wallet balance is NOT changed.

    Wallet updated_at uses the investment approval timestamp.
    """

    amount = float(
        amount or 0
    )

    wallet = get_or_create_wallet(
        db=db,
        user_id=user_id,
        transaction_date=transaction_date
    )

    pending_before = float(
        wallet.pending_balance or 0
    )

    wallet.pending_balance = (
        pending_before + amount
    )

    # IMPORTANT
    # Override SQLAlchemy onupdate=datetime.utcnow
    wallet.updated_at = transaction_date

    db.flush()

    return wallet


# ==========================================================
# CREATE PENDING WALLET TRANSACTION
# ==========================================================

def create_wallet_transaction(
    db: Session,
    wallet_id: int,
    investment_id: int,
    amount: float,
    level: int,
    transaction_date
):
    """
    Create wallet transaction.

    created_at = investment approval timestamp.
    """

    transaction = WalletTransaction(
        wallet_id=wallet_id,

        investment_id=investment_id,

        amount=float(
            amount or 0
        ),

        transaction_type="LEVEL_INCOME",

        status="PENDING",

        remarks=(
            f"Level {level} Commission"
        ),

        created_at=transaction_date,
    )

    db.add(transaction)

    db.flush()

    return transaction


# ==========================================================
# SAVE LEVEL COMMISSION HISTORY
# ==========================================================

def save_level_history(
    db: Session,
    investment,
    sponsor,
    level: int,
    percentage: float,
    commission: float,
    created_at
):
    """
    Save level commission history.

    created_at = investment approval timestamp.
    """

    history = LevelCommissionHistory(
        investment_id=investment.id,

        investor_id=investment.user_id,

        sponsor_id=sponsor.id,

        level=level,

        investment_amount=investment.amount,

        commission_percentage=percentage,

        commission_amount=commission,

        status="PENDING",

        created_at=created_at,
    )

    db.add(history)

    db.flush()

    return history


# ==========================================================
# CALCULATE LEVEL COMMISSION
# ==========================================================

def calculate_level_commission(
    db: Session,
    investment: Investment
):
    """
    Calculate up to 15 levels of level commission.

    Rules:

    1. Sponsor must have ACTIVE + APPROVED investment.
    2. If sponsor has no active investment, skip commission.
    3. Continue traversing genealogy.
    4. Income goes to Wallet.pending_balance.
    5. Wallet transaction remains PENDING.
    6. Level history remains PENDING.
    7. All timestamps use investment.approval_status_updated_at.
    8. This function does NOT commit.
    """

    # ======================================================
    # VALIDATE INVESTMENT
    # ======================================================

    if not investment:

        print(
            "Level commission skipped: "
            "Investment not provided"
        )

        return None

    # ======================================================
    # APPROVAL TIMESTAMP
    # ======================================================

    approval_timestamp = (
        investment.approval_status_updated_at
    )

    if not approval_timestamp:

        print(
            "Level commission skipped: "
            "approval_status_updated_at is NULL"
        )

        return None

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
            "Level commission skipped: "
            "Investor not found"
        )

        return None

    # ======================================================
    # START FROM INVESTOR
    # ======================================================

    current_user = investor

    level = 1

    generated_histories = []

    # ======================================================
    # MAXIMUM 15 LEVELS
    # ======================================================

    while level <= 15:

        # ==================================================
        # CHECK CURRENT USER ENROLLER
        # ==================================================

        if not current_user.enroller_id:

            print(
                f"No enroller found at level {level}"
            )

            break

        # ==================================================
        # FIND SPONSOR
        # ==================================================

        sponsor = (
            db.query(User)
            .filter(
                User.user_id
                == current_user.enroller_id
            )
            .first()
        )

        if not sponsor:

            print(
                f"Sponsor not found at level {level}"
            )

            break

        # ==================================================
        # CHECK SPONSOR ACTIVE + APPROVED INVESTMENT
        # ==================================================

        sponsor_has_active_investment = (
            has_active_investment(
                db=db,
                user_id=sponsor.id
            )
        )

        if not sponsor_has_active_investment:

            print("--------------------------------------")
            print("LEVEL COMMISSION SKIPPED")
            print("--------------------------------------")
            print("Investor:", investor.user_id)
            print("Sponsor:", sponsor.user_id)
            print("Level:", level)
            print(
                "Reason:",
                "Sponsor has no ACTIVE + APPROVED investment"
            )
            print("Commission:", 0)
            print("--------------------------------------")

            # Continue genealogy
            current_user = sponsor
            level += 1

            continue

        # ==================================================
        # GET LEVEL COMMISSION %
        # ==================================================

        percentage = get_level_percentage(
            db=db,
            level=level
        )

        if percentage <= 0:

            print(
                f"Level {level}: "
                f"No commission percentage configured"
            )

            current_user = sponsor
            level += 1

            continue

        # ==================================================
        # INVESTMENT AMOUNT
        # ==================================================

        investment_amount = float(
            investment.amount or 0
        )

        # ==================================================
        # CALCULATE COMMISSION
        # ==================================================

        commission = (
            investment_amount
            * percentage
        ) / 100

        # ==================================================
        # SAFETY CHECK
        # ==================================================

        if commission <= 0:

            print(
                f"Level {level}: "
                f"Commission amount is zero"
            )

            current_user = sponsor
            level += 1

            continue

        # ==================================================
        # SAVE LEVEL COMMISSION HISTORY
        # ==================================================

        history = save_level_history(
            db=db,
            investment=investment,
            sponsor=sponsor,
            level=level,
            percentage=percentage,
            commission=commission,
            created_at=approval_timestamp,
        )

        generated_histories.append(
            history
        )

        # ==================================================
        # UPDATE SPONSOR PENDING WALLET
        # ==================================================

        wallet = update_wallet(
            db=db,
            user_id=sponsor.id,
            amount=commission,
            transaction_date=approval_timestamp,
        )

        # ==================================================
        # CREATE PENDING WALLET TRANSACTION
        # ==================================================

        transaction = create_wallet_transaction(
            db=db,
            wallet_id=wallet.id,
            investment_id=investment.id,
            amount=commission,
            level=level,
            transaction_date=approval_timestamp,
        )

        # ==================================================
        # LOG
        # ==================================================

        print("--------------------------------------")
        print("LEVEL COMMISSION")
        print("--------------------------------------")

        print(
            "Investor:",
            investor.user_id
        )

        print(
            "Sponsor:",
            sponsor.user_id
        )

        print(
            "Level:",
            level
        )

        print(
            "Investment:",
            investment_amount
        )

        print(
            "Percentage:",
            percentage
        )

        print(
            "Commission:",
            commission
        )

        print(
            "Approval Timestamp:",
            approval_timestamp
        )

        print(
            "History Created At:",
            history.created_at
        )

        print(
            "Wallet Created At:",
            wallet.created_at
        )

        print(
            "Wallet Updated At:",
            wallet.updated_at
        )

        print(
            "Transaction Created At:",
            transaction.created_at
        )

        print(
            "History Status:",
            history.status
        )

        print(
            "Transaction Status:",
            transaction.status
        )

        print(
            "Wallet Balance:",
            wallet.balance
        )

        print(
            "Wallet Pending Balance:",
            wallet.pending_balance
        )

        print(
            "Admin Fee:",
            "NOT DEDUCTED"
        )

        print("--------------------------------------")

        # ==================================================
        # MOVE TO NEXT SPONSOR
        # ==================================================

        current_user = sponsor

        level += 1

    # ======================================================
    # DO NOT COMMIT HERE
    # ======================================================
    #
    # The approval endpoint should perform:
    #
    #     db.commit()
    #
    # after referral + level + rank are completed.
    #
    # ======================================================

    print("======================================")
    print("LEVEL COMMISSION COMPLETED")
    print("======================================")

    print(
        "Investor:",
        investor.user_id
    )

    print(
        "Levels Generated:",
        len(generated_histories)
    )

    print(
        "Approval Timestamp:",
        approval_timestamp
    )

    print("======================================")

    return generated_histories

