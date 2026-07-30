from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import User,Wallet,BinaryWallet,Investment,BinaryIncome,ReferralCommission,LevelCommissionHistory

def get_user_summary(db: Session, user: User):

    wallet = (
        db.query(Wallet)
        .filter(Wallet.user_id == user.id)
        .first()
    )

    binary_wallet = (
        db.query(BinaryWallet)
        .filter(BinaryWallet.user_id == user.id)
        .first()
    )

    total_investment = (
        db.query(
            func.coalesce(func.sum(Investment.amount), 0)
        )
        .filter(
            Investment.user_id == user.id,
            Investment.approval_status == "APPROVED"
        )
        .scalar()
    )

    binary_income = (
        db.query(
            func.coalesce(func.sum(BinaryIncome.paid_income), 0)
        )
        .filter(BinaryIncome.user_id == user.id)
        .scalar()
    )

    referral_income = (
        db.query(
            func.coalesce(
                func.sum(
                    ReferralCommission.commission_amount
                ),
                0
            )
        )
        .filter(
            ReferralCommission.enroller_id == user.id
        )
        .scalar()
    )

    level_income = (
        db.query(
            func.coalesce(
                func.sum(
                    LevelCommissionHistory.commission_amount
                ),
                0
            )
        )
        .filter(
            LevelCommissionHistory.sponsor_id == user.id
        )
        .scalar()
    )

    return {

        "wallet_balance": wallet.balance if wallet else 0,

        "total_investment": total_investment,

        "binary_income": binary_income,

        "referral_income": referral_income,

        "level_income": level_income,

        "left_business": (
            binary_wallet.left_business
            if binary_wallet else 0
        ),

        "right_business": (
            binary_wallet.right_business
            if binary_wallet else 0
        ),

        "left_carry": (
            binary_wallet.left_carry
            if binary_wallet else 0
        ),

        "right_carry": (
            binary_wallet.right_carry
            if binary_wallet else 0
        )

    }

def build_tree(db: Session, user: User):

    summary = get_user_summary(db, user)

    children = (
        db.query(User)
        .filter(User.enroller_id == user.user_id)
        .all()
    )

    return {

        "user_id": user.user_id,

        "name": f"{user.first_name} {user.last_name}",

        "role": user.role,

        "wallet_balance": summary["wallet_balance"],

        "total_investment": summary["total_investment"],

        "binary_income": summary["binary_income"],

        "referral_income": summary["referral_income"],

        "level_income": summary["level_income"],

        "left_business": summary["left_business"],

        "right_business": summary["right_business"],

        "left_carry": summary["left_carry"],

        "right_carry": summary["right_carry"],

        "children": [
            build_tree(db, child)
            for child in children
        ]

    }

def get_full_genealogy(db: Session):
    """
    Returns the complete genealogy tree.
    Root users are users without an enroller.
    """
    roots = (
        db.query(User)
        .filter(User.enroller_id == None)
        .all()
    )

    return [
        build_tree(db, root)
        for root in roots
    ]


def get_user_genealogy(db: Session, user_id: str):
    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if not user:
        return None

    return build_tree(db, user)