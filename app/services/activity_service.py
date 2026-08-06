from sqlalchemy.orm import Session
from app.models import UserActivityHistory


def get_activity_history(db: Session, user_id: int):
    return (
        db.query(UserActivityHistory)
        .filter(UserActivityHistory.user_id == user_id)
        .order_by(UserActivityHistory.created_at.desc())
        .all()
    )