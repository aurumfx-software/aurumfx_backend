from sqlalchemy.orm import Session

from app.models import Investment


def generate_investment_id(db: Session):

    last = (
        db.query(Investment)
        .order_by(Investment.id.desc())
        .first()
    )

    if not last:
        return "INV000001"

    number = int(last.investment_id.replace("INV", ""))

    return f"INV{number + 1:06d}"