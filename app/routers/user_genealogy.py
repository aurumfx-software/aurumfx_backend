from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.services.user_genealogy import (
    get_logged_in_user_genealogy,
    get_user_genealogy_list
)

router = APIRouter(
    prefix="/user/genealogy",
    tags=["User Genealogy"]
)


@router.get("/")
def user_genealogy(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    return get_logged_in_user_genealogy(
        db,
        current_user
    )

@router.get("/list")
def user_genealogy_list(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    result = get_user_genealogy_list(
        db,
        current_user
    )

    if result is None:
        return []

    return result