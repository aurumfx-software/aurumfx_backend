# from datetime import datetime

# from sqlalchemy.orm import Session

# from app.models import (
#     User,
#     Wallet,
#     WalletTransaction,
#     Investment,
#     LevelCommission,
#     LevelCommissionHistory,
# )

# def get_level_percentage(db: Session, level: int):

#     commission = (
#         db.query(LevelCommission)
#         .filter(
#             LevelCommission.level == level,
#             LevelCommission.status == 1
#         )
#         .first()
#     )

#     if not commission:
#         return 0

#     return commission.commission_percentage

# def update_wallet(
#     db: Session,
#     user_id: int,
#     amount: float
# ):

#     wallet = (
#         db.query(Wallet)
#         .filter(Wallet.user_id == user_id)
#         .first()
#     )

#     if wallet:

#         wallet.balance += amount

#     else:

#         wallet = Wallet(
#             user_id=user_id,
#             balance=amount
#         )

#         db.add(wallet)

#     db.flush()

#     return wallet

# def create_wallet_transaction(
#     db: Session,
#     wallet_id: int,
#     investment_id: int,
#     amount: float,
#     level: int
# ):

#     transaction = WalletTransaction(

#         wallet_id=wallet_id,

#         investment_id=investment_id,

#         amount=amount,

#         transaction_type="LEVEL_INCOME",

#         remarks=f"Level {level} Commission"

#     )

#     db.add(transaction)

# def save_level_history(
#     db: Session,
#     investment,
#     sponsor,
#     level,
#     percentage,
#     commission
# ):

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

# def calculate_level_commission(
#     db: Session,
#     investment: Investment
# ):

#     investor = (
#         db.query(User)
#         .filter(User.id == investment.user_id)
#         .first()
#     )

#     if not investor:
#         return

#     current_user = investor

#     level = 1

#     while level <= 15:

#         if not current_user.enroller_id:
#             break

#         sponsor = (
#             db.query(User)
#             .filter(
#                 User.user_id == current_user.enroller_id
#             )
#             .first()
#         )

#         if not sponsor:
#             break

#         percentage = get_level_percentage(
#             db,
#             level
#         )

#         if percentage > 0:

#             commission = (
#                 investment.amount *
#                 percentage
#             ) / 100

#             save_level_history(
#                 db,
#                 investment,
#                 sponsor,
#                 level,
#                 percentage,
#                 commission
#             )

#             wallet = update_wallet(
#                 db,
#                 sponsor.id,
#                 commission
#             )

#             create_wallet_transaction(
#                 db,
#                 wallet.id,
#                 investment.id,
#                 commission,
#                 level
#             )

#         current_user = sponsor

#         level += 1

#     db.commit()

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
    """
    Get commission percentage for a particular level.
    """

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
# GET / CREATE USER WALLET
# ==========================================================

def get_or_create_wallet(
    db: Session,
    user_id: int
):
    """
    Get user's wallet.

    If wallet does not exist, create it.

    Wallet structure:

        balance
            = Paid / available amount

        pending_balance
            = Pending referral + level + rank income

        admin_fee
            = Admin fee deducted during payout
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

            # Paid balance
            balance=0,

            # Pending income
            pending_balance=0,

            # Admin fee accumulated during payout
            admin_fee=0
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
    amount: float
):
    """
    Add generated level income to pending_balance.

    IMPORTANT:

        balance is NOT changed.

        pending_balance is increased.

    Admin fee is NOT deducted here.
    """

    amount = float(
        amount or 0
    )

    wallet = get_or_create_wallet(
        db,
        user_id
    )

    pending_before = float(
        wallet.pending_balance or 0
    )

    wallet.pending_balance = (
        pending_before
        + amount
    )

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
    level: int
):
    """
    Create wallet transaction for level income.

    Newly generated income is PENDING.
    """

    transaction = WalletTransaction(

        wallet_id=wallet_id,

        investment_id=investment_id,

        amount=float(
            amount or 0
        ),

        transaction_type="LEVEL_INCOME",

        # IMPORTANT
        status="PENDING",

        remarks=(
            f"Level {level} Commission"
        )
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
    commission: float
):
    """
    Save level commission history.

    The history remains PENDING until admin pays
    the user's total income.
    """

    history = LevelCommissionHistory(

        investment_id=investment.id,

        investor_id=investment.user_id,

        sponsor_id=sponsor.id,

        level=level,

        investment_amount=investment.amount,

        commission_percentage=percentage,

        commission_amount=commission,

        status="PENDING"
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
    Calculate up to 15 levels of commission.

    Flow:

        Investment Approved
                |
                v
        Find investor
                |
                v
        Find sponsor level by level
                |
                v
        Calculate commission
                |
                v
        Save LevelCommissionHistory = PENDING
                |
                v
        Wallet.pending_balance += commission
                |
                v
        WalletTransaction = PENDING

    IMPORTANT:

    Admin fee is NOT calculated here.

    Admin fee is calculated later by admin payout
    from:

        Referral Income
        +
        Level Income
        +
        Rank Income
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
            "Level commission skipped: "
            "Investor not found"
        )

        return None

    # ======================================================
    # CURRENT USER
    #
    # Start from investor.
    # ======================================================

    current_user = investor

    level = 1

    generated_histories = []

    # ======================================================
    # MAXIMUM 15 LEVELS
    # ======================================================

    while level <= 15:

        # ==================================================
        # CHECK ENROLLER
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
        # GET LEVEL COMMISSION %
        # ==================================================

        percentage = get_level_percentage(
            db,
            level
        )

        # ==================================================
        # NO COMMISSION FOR THIS LEVEL
        # ==================================================

        if percentage <= 0:

            print(
                f"Level {level}: "
                f"No commission percentage configured"
            )

            current_user = sponsor

            level += 1

            continue

        # ==================================================
        # CALCULATE COMMISSION
        # ==================================================

        investment_amount = float(
            investment.amount or 0
        )

        commission = (
            investment_amount
            * percentage
        ) / 100

        # Safety
        if commission <= 0:

            current_user = sponsor

            level += 1

            continue

        # ==================================================
        # SAVE LEVEL HISTORY
        #
        # STATUS = PENDING
        # ==================================================

        history = save_level_history(
            db=db,
            investment=investment,
            sponsor=sponsor,
            level=level,
            percentage=percentage,
            commission=commission
        )

        generated_histories.append(
            history
        )

        # ==================================================
        # UPDATE PENDING WALLET
        #
        # IMPORTANT:
        #
        # Do NOT update wallet.balance.
        #
        # Update only:
        #
        #     wallet.pending_balance
        # ==================================================

        wallet = update_wallet(
            db=db,
            user_id=sponsor.id,
            amount=commission
        )

        # ==================================================
        # CREATE PENDING WALLET TRANSACTION
        # ==================================================

        transaction = create_wallet_transaction(
            db=db,
            wallet_id=wallet.id,
            investment_id=investment.id,
            amount=commission,
            level=level
        )

        # ==================================================
        # LOG
        # ==================================================

        print(
            "--------------------------------------"
        )

        print(
            "LEVEL COMMISSION"
        )

        print(
            "--------------------------------------"
        )

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
            "History Status:",
            "PENDING"
        )

        print(
            "Transaction Status:",
            "PENDING"
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

        print(
            "--------------------------------------"
        )

        # ==================================================
        # MOVE TO NEXT SPONSOR
        # ==================================================

        current_user = sponsor

        level += 1

    # ======================================================
    # COMMIT ALL LEVEL COMMISSIONS TOGETHER
    # ======================================================

    db.commit()

    # ======================================================
    # REFRESH HISTORIES
    # ======================================================

    for history in generated_histories:

        db.refresh(history)

    # ======================================================
    # RESULT
    # ======================================================

    print(
        "======================================"
    )

    print(
        "LEVEL COMMISSION COMPLETED"
    )

    print(
        "Investor:",
        investor.user_id
    )

    print(
        "Levels Generated:",
        len(generated_histories)
    )

    print(
        "======================================"
    )

    return generated_histories