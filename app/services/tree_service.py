from sqlalchemy.orm import Session
from app.models import User


def create_tree(db: Session, user: User):
    if not user:
        return None

    left = (
        db.query(User)
        .filter(
            User.placement_parent == user.user_id,
            User.club == "Left"
        )
        .first()
    )

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