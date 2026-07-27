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

    # -------------------------
    # Investor
    # -------------------------
    investor = (
        db.query(User)
        .filter(User.id == investment.user_id)
        .first()
    )

    if not investor:
        return

    # -------------------------
    # Enroller
    # -------------------------
    enroller = (
        db.query(User)
        .filter(User.user_id == investment.enroller_id)
        .first()
    )

    if not enroller:
        return

    # -------------------------
    # Commission %
    # -------------------------
    commission_percentage = plan.commission_percentage

    gross_commission = (
        investment.amount *
        commission_percentage
    ) / 100

    # -------------------------
    # Admin Fee %
    # -------------------------
    admin_fee_percentage = plan.admin_fee_percentage

    admin_fee_amount = (
        gross_commission *
        admin_fee_percentage
    ) / 100

    # Commission after admin fee
    net_commission = (
        gross_commission -
        admin_fee_amount
    )

    paid = net_commission
    washout = 0

    # -------------------------
    # Daily Commission Limit
    # -------------------------
    if plan.daily_commission_limit:

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

        remaining_limit = (
            plan.daily_commission_limit -
            today_paid
        )

        if remaining_limit <= 0:

            paid = 0
            washout = net_commission

        elif net_commission > remaining_limit:

            paid = remaining_limit
            washout = net_commission - remaining_limit

    # -------------------------
    # Wallet
    # -------------------------
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

    wallet.balance += paid

    # -------------------------
    # Commission History
    # -------------------------
    commission_history = ReferralCommission(

        investment_id=investment.id,

        investor_id=investor.id,

        enroller_id=enroller.id,

        investment_amount=investment.amount,

        commission_percentage=commission_percentage,

        commission_amount=gross_commission,

        admin_fee_percentage=admin_fee_percentage,

        admin_fee_amount=admin_fee_amount,

        paid_amount=paid,

        washout_amount=washout,

        status="PENDING"

    )

    db.add(commission_history)

    # -------------------------
    # Wallet Transaction
    # -------------------------
    wallet_transaction = WalletTransaction(

        wallet_id=wallet.id,

        investment_id=investment.id,

        amount=paid,

        transaction_type="REFERRAL",

        remarks=f"Referral Commission from {investor.user_id}"

    )
    print("Investor :", investor.user_id)
    print("Enroller :", enroller.user_id)
    print("Paid :", paid)
    print("Wallet Before :", wallet.balance - paid)
    print("Wallet After :", wallet.balance)

    db.add(wallet_transaction)

    db.commit()