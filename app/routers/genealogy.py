from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.genealogy import (
    get_full_genealogy,
    get_user_genealogy
)

router = APIRouter(
    prefix="/genealogy",
    tags=["Genealogy"]
)


@router.get("/")
def all_genealogy(db: Session = Depends(get_db)):
    return get_full_genealogy(db)


@router.get("/{user_id}")
def genealogy(user_id: str, db: Session = Depends(get_db)):
    tree = get_user_genealogy(db, user_id)

    if not tree:
        raise HTTPException(status_code=404, detail="User not found")

    return tree