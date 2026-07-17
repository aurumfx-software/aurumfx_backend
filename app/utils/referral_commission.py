from datetime import date

from sqlalchemy import func

from app.models import (
    Wallet,
    WalletTransaction,
    ReferralCommission,
    User
)


def create_referral_commission(
    db,
    investment,
    plan
):

    # Investor
    investor = (
        db.query(User)
        .filter(User.id == investment.user_id)
        .first()
    )

    if not investor:
        return

    # Enroller
    enroller = (
        db.query(User)
        .filter(User.user_id == investment.enroller_id)
        .first()
    )

    if not enroller:
        return

    # Commission Percentage
    if plan.duration_months == 10:
        percentage = 5

    elif plan.duration_months == 30:
        percentage = 10

    else:
        return

    commission = (investment.amount * percentage) / 100

    paid = commission
    washout = 0

    # 10 Month Plan Daily Limit
    if plan.duration_months == 10:

        today_paid = (
            db.query(
                func.coalesce(
                    func.sum(
                        ReferralCommission.paid_amount
                    ),
                    0
                )
            )
            .filter(
                ReferralCommission.enroller_id == enroller.id,
                func.date(
                    ReferralCommission.created_at
                ) == date.today()
            )
            .scalar()
        )

        remaining_limit = 25000 - today_paid

        if remaining_limit <= 0:

            paid = 0
            washout = commission

        elif commission > remaining_limit:

            paid = remaining_limit
            washout = commission - remaining_limit

    # Wallet
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
            balance=0
        )

        db.add(wallet)
        db.flush()

    # Credit wallet
    wallet.balance += paid

    # Commission History
    commission_history = ReferralCommission(

        investment_id=investment.id,

        investor_id=investor.id,

        enroller_id=enroller.id,

        investment_amount=investment.amount,

        commission_percentage=percentage,

        commission_amount=commission,

        paid_amount=paid,

        washout_amount=washout,

        status="PAID"

    )

    db.add(commission_history)

    # Wallet Transaction
    wallet_transaction = WalletTransaction(

        wallet_id=wallet.id,

        investment_id=investment.id,

        amount=paid,

        transaction_type="REFERRAL",

        remarks=f"Referral Commission from {investor.user_id}"

    )

    db.add(wallet_transaction)

    db.commit()