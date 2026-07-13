from sqlalchemy.orm import Session
from app.models import User


def generate_user_id(db: Session):

    last_user = (
        db.query(User)
        .order_by(User.id.desc())
        .first()
    )

    if not last_user:
        return "FX001"

    number = int(last_user.user_id.replace("FX", ""))

    return f"FX{number + 1:03d}"