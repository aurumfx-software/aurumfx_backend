from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import User, BinaryWallet,BinaryIncome
from sqlalchemy.orm import Session
from app.models import User, BinaryWallet

def create_tree(db: Session, user: User):
    if not user:
        return None

    # ---------------------------------------
    # Binary Wallet
    # ---------------------------------------
    wallet = (
        db.query(BinaryWallet)
        .filter(BinaryWallet.user_id == user.id)
        .first()
    )

    if wallet:
        left_balance = wallet.left_carry
        right_balance = wallet.right_carry
    else:
        left_balance = 0
        right_balance = 0

    # ---------------------------------------
    # Total Matched Business
    # ---------------------------------------
    total_matched = (
        db.query(
            func.coalesce(
                func.sum(BinaryIncome.matched_amount),
                0
            )
        )
        .filter(BinaryIncome.user_id == user.id)
        .scalar()
    )

    # ---------------------------------------
    # Total Business
    # Formula:
    # Total Left = Matched + Current Left Carry
    # Total Right = Matched + Current Right Carry
    # ---------------------------------------
    left_business = total_matched + left_balance
    right_business = total_matched + right_balance

    # ---------------------------------------
    # Left Child
    # ---------------------------------------
    left = (
        db.query(User)
        .filter(
            User.placement_parent == user.user_id,
            User.club == "Left"
        )
        .first()
    )

    # ---------------------------------------
    # Right Child
    # ---------------------------------------
    right = (
        db.query(User)
        .filter(
            User.placement_parent == user.user_id,
            User.club == "Right"
        )
        .first()
    )

    return {
        "id": user.id,
        "user_id": user.user_id,
        "name": f"{user.first_name} {user.last_name}",
        "email": user.email,
        "club": user.club,
        "enroller_id": user.enroller_id,
        "placement_parent": user.placement_parent,

        # Binary Information
        "left_business": left_business,
        "right_business": right_business,
        "matched_business": total_matched,
        "left_balance": left_balance,
        "right_balance": right_balance,

        "left": create_tree(db, left),
        "right": create_tree(db, right)
    }


def build_tree(db: Session):
    root = (
        db.query(User)
        .filter(User.role == "ADMIN")
        .first()
    )

    if not root:
        return None

    return create_tree(db, root)


def build_tree_from_user(db: Session, user_id: str):
    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if not user:
        return None

    return create_tree(db, user)

def build_tree(db: Session):
    root = (
        db.query(User)
        .filter(User.role == "ADMIN")
        .first()
    )

    if not root:
        return None

    return create_tree(db, root)


def build_tree_from_user(db: Session, user_id: str):
    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if not user:
        return None

    return create_tree(db, user)