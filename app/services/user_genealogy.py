from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import User, Investment


def build_user_genealogy_tree(
    db: Session,
    user: User
):
    # -----------------------------------------
    # Total approved investment
    # -----------------------------------------
    total_investment = (
        db.query(
            func.coalesce(
                func.sum(Investment.amount),
                0
            )
        )
        .filter(
            Investment.user_id == user.id,
            Investment.approval_status == "APPROVED"
        )
        .scalar()
    )

    # -----------------------------------------
    # Total approved lots
    # -----------------------------------------
    total_lots = (
        db.query(
            func.coalesce(
                func.sum(Investment.lots),
                0
            )
        )
        .filter(
            Investment.user_id == user.id,
            Investment.approval_status == "APPROVED"
        )
        .scalar()
    )

    # -----------------------------------------
    # Direct members
    # -----------------------------------------
    children = (
        db.query(User)
        .filter(
            User.enroller_id == user.user_id
        )
        .all()
    )

    return {
        "user_id": user.user_id,

        "full_name": (
            f"{user.first_name} {user.last_name}"
        ).strip(),

        "date_of_join": user.created_at,

        "rank": (
            user.current_rank.rank_name
            if user.current_rank
            else None
        ),

        "total_investment": float(
            total_investment or 0
        ),

        "total_lots": int(
            total_lots or 0
        ),

        "children": [
            build_user_genealogy_tree(
                db,
                child
            )
            for child in children
        ]
    }


def get_logged_in_user_genealogy(
    db: Session,
    user_id: str
):
    # get_current_user returns user_id string
    user = (
        db.query(User)
        .filter(
            User.user_id == user_id
        )
        .first()
    )

    if not user:
        return None

    return build_user_genealogy_tree(
        db,
        user
    )