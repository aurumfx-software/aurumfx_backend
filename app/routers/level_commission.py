from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.database import get_db
from app.models import LevelCommission, User
from app.schemas import (
    LevelCommissionCreate,
    LevelCommissionUpdate,
    LevelCommissionResponse,
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
    prefix="/admin/level-settings",
    tags=["Level Commission"],
    dependencies=[Depends(get_admin)]
)


@router.post(
    "/",
    response_model=LevelCommissionResponse
)
def create_commission(
    data: LevelCommissionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin)

):

    exists = (
        db.query(LevelCommission)
        .filter(LevelCommission.level == data.level)
        .first()
    )

    if exists:
        raise HTTPException(
            status_code=400,
            detail="Level already exists"
        )

    obj = LevelCommission(**data.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


@router.get(
    "/",
    response_model=list[LevelCommissionResponse]
)
def get_all(db: Session = Depends(get_db)):
    return (
        db.query(LevelCommission)
        .order_by(LevelCommission.level)
        .all()
    )


@router.get(
    "/{level}",
    response_model=LevelCommissionResponse
)
def get_level(level: int, db: Session = Depends(get_db)):

    obj = (
        db.query(LevelCommission)
        .filter(LevelCommission.level == level)
        .first()
    )

    if not obj:
        raise HTTPException(404, "Level not found")

    return obj


@router.put(
    "/{level}",
    response_model=LevelCommissionResponse
)
def update_level(
    level: int,
    data: LevelCommissionUpdate,
    db: Session = Depends(get_db)
):

    obj = (
        db.query(LevelCommission)
        .filter(LevelCommission.level == level)
        .first()
    )

    if not obj:
        raise HTTPException(404, "Level not found")

    obj.commission_percentage = data.commission_percentage
    obj.status = data.status

    db.commit()
    db.refresh(obj)

    return obj


@router.delete("/{level}")
def delete_level(level: int, db: Session = Depends(get_db)):

    obj = (
        db.query(LevelCommission)
        .filter(LevelCommission.level == level)
        .first()
    )

    if not obj:
        raise HTTPException(404, "Level not found")

    db.delete(obj)
    db.commit()

    return {
        "message": "Deleted successfully"
    }