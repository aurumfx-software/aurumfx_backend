from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.core.security import get_current_user

from app.services.tree_service import (
    build_tree,
    build_tree_from_user
)


def get_admin(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.user_id == current_user
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    return user


router = APIRouter(
    prefix="/admin/binary-tree",
    tags=["Admin Binary Tree"],
    dependencies=[Depends(get_admin)]
)


# Complete tree from Admin
@router.get("/")
def get_complete_tree(
    db: Session = Depends(get_db)
):
    return build_tree(db)


# Subtree from any user
@router.get("/{user_id}")
def get_user_tree(
    user_id: str,
    db: Session = Depends(get_db)
):
    return build_tree_from_user(db, user_id)