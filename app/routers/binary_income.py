from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import (
    User,
    BinaryWallet,
    BinaryIncome
)
from app.core.security import get_current_user

router = APIRouter(
    prefix="/binary-income",
    tags=["Binary Income"]
)

def get_admin(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.user_id == current_user
    ).first()

    if not user:
        raise HTTPException(404, "User not found")

    if user.role != "ADMIN":
        raise HTTPException(403, "Admin only")

    return user

def get_login_user(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.user_id == current_user
    ).first()

    if not user:
        raise HTTPException(404, "User not found")

    return user

@router.get("/my-wallet")
def my_binary_wallet(
    current=Depends(get_login_user),
    db: Session = Depends(get_db)
):

    wallet = db.query(BinaryWallet).filter(
        BinaryWallet.user_id == current.id
    ).first()

    if not wallet:
        return {
            "left_business":0,
            "right_business":0,
            "left_carry":0,
            "right_carry":0
        }

    return wallet

@router.get("/my-history")
def my_binary_history(
    current=Depends(get_login_user),
    db: Session = Depends(get_db)
):

    return (
        db.query(BinaryIncome)
        .filter(
            BinaryIncome.user_id == current.id
        )
        .order_by(desc(BinaryIncome.created_at))
        .all()
    )

@router.get(
    "/admin/wallets",
    dependencies=[Depends(get_admin)]
)
def all_binary_wallets(
    db: Session = Depends(get_db)
):

    return db.query(BinaryWallet).all()

@router.get(
    "/admin/history",
    dependencies=[Depends(get_admin)]
)
def binary_history(
    db: Session = Depends(get_db)
):

    return (
        db.query(BinaryIncome)
        .order_by(desc(BinaryIncome.created_at))
        .all()
    )

@router.get(
    "/admin/{user_id}",
    dependencies=[Depends(get_admin)]
)
def user_binary(
    user_id: str,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.user_id == user_id
    ).first()

    if not user:
        raise HTTPException(404, "User not found")

    wallet = db.query(BinaryWallet).filter(
        BinaryWallet.user_id == user.id
    ).first()

    history = db.query(BinaryIncome).filter(
        BinaryIncome.user_id == user.id
    ).all()

    return {
        "wallet": wallet,
        "history": history
    }