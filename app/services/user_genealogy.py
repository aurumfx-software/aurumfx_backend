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

def get_user_genealogy_list(
    db: Session,
    user_id: str
):
    """
    Return logged-in user's genealogy as a flat list.

    Level 1 = direct enrollers
    Level 2 = their direct enrollers
    Level 3 = next level
    """

    root_user = (
        db.query(User)
        .filter(
            User.user_id == user_id
        )
        .first()
    )

    if not root_user:
        return None

    result = []

    def collect_members(
        current_user: User,
        current_level: int
    ):
        children = (
            db.query(User)
            .filter(
                User.enroller_id == current_user.user_id
            )
            .all()
        )

        for child in children:

            # Total investment
            total_investment = (
                db.query(
                    func.coalesce(
                        func.sum(Investment.amount),
                        0
                    )
                )
                .filter(
                    Investment.user_id == child.id,
                    Investment.approval_status == "APPROVED"
                )
                .scalar()
            )

            # Total lots
            total_lots = (
                db.query(
                    func.coalesce(
                        func.sum(Investment.lots),
                        0
                    )
                )
                .filter(
                    Investment.user_id == child.id,
                    Investment.approval_status == "APPROVED"
                )
                .scalar()
            )

            result.append({
                "user_id": child.user_id,

                "full_name": (
                    f"{child.first_name} {child.last_name}"
                ).strip(),

                "date_of_join": child.created_at,

                "level": current_level,

                "rank": (
                    child.current_rank.rank_name
                    if child.current_rank
                    else None
                ),

                "total_investment": float(
                    total_investment or 0
                ),

                "total_lots": int(
                    total_lots or 0
                )
            })

            # Continue to next level
            collect_members(
                child,
                current_level + 1
            )

    collect_members(
        root_user,
        1
    )

    return result