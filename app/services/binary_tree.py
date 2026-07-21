from sqlalchemy.orm import Session
from app.models import User


def find_placement_parent(db: Session, sponsor: User, club: str) -> User:
    """
    Find the next available placement parent on the selected side.
    """

    current = sponsor

    while True:
        child = (
            db.query(User)
            .filter(
                User.placement_parent == current.user_id,
                User.club == club
            )
            .first()
        )

        if child:
            current = child
        else:
            return current