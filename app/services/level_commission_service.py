from datetime import datetime

from sqlalchemy.orm import Session

from app.models import (
    User,
    Wallet,
    WalletTransaction,
    Investment,
    LevelCommission,
    LevelCommissionHistory,
)

def get_level_percentage(db: Session, level: int):

    commission = (
        db.query(LevelCommission)
        .filter(
            LevelCommission.level == level,
            LevelCommission.status == 1
        )
        .first()
    )

    if not commission:
        return 0

    return commission.commission_percentage

def update_wallet(
    db: Session,
    user_id: int,
    amount: float
):

    wallet = (
        db.query(Wallet)
        .filter(Wallet.user_id == user_id)
        .first()
    )

    if wallet:

        wallet.balance += amount

    else:

        wallet = Wallet(
            user_id=user_id,
            balance=amount
        )

        db.add(wallet)

    db.flush()

    return wallet

def create_wallet_transaction(
    db: Session,
    wallet_id: int,
    investment_id: int,
    amount: float,
    level: int
):

    transaction = WalletTransaction(

        wallet_id=wallet_id,

        investment_id=investment_id,

        amount=amount,

        transaction_type="LEVEL_INCOME",

        remarks=f"Level {level} Commission"

    )

    db.add(transaction)

def save_level_history(
    db: Session,
    investment,
    sponsor,
    level,
    percentage,
    commission
):

    history = LevelCommissionHistory(

        investment_id=investment.id,

        investor_id=investment.user_id,

        sponsor_id=sponsor.id,

        level=level,

        investment_amount=investment.amount,

        commission_percentage=percentage,

        commission_amount=commission,

        status="PAID"

    )

    db.add(history)

def calculate_level_commission(
    db: Session,
    investment: Investment
):

    investor = (
        db.query(User)
        .filter(User.id == investment.user_id)
        .first()
    )

    if not investor:
        return

    current_user = investor

    level = 1

    while level <= 15:

        if not current_user.enroller_id:
            break

        sponsor = (
            db.query(User)
            .filter(
                User.user_id == current_user.enroller_id
            )
            .first()
        )

        if not sponsor:
            break

        percentage = get_level_percentage(
            db,
            level
        )

        if percentage > 0:

            commission = (
                investment.amount *
                percentage
            ) / 100

            save_level_history(
                db,
                investment,
                sponsor,
                level,
                percentage,
                commission
            )

            wallet = update_wallet(
                db,
                sponsor.id,
                commission
            )

            create_wallet_transaction(
                db,
                wallet.id,
                investment.id,
                commission,
                level
            )

        current_user = sponsor

        level += 1

    db.commit()