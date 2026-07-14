from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.core.security import get_current_user


def get_current_admin(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.user_id == current_user
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin can perform this action"
        )

    return user