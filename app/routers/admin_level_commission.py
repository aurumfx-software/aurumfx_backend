from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.security import get_current_user

from app.database import get_db
from app.models import (
    User,
    LevelCommissionHistory,
)

router = APIRouter(
    prefix="/admin/level-commission",
    tags=["Admin Level Commission"],
    
)

# ----------------------------------------------------------------------------
# Admin Authentication
# ----------------------------------------------------------------------------
# def get_admin(
#     current_user: str = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
def get_admin(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    print("CURRENT USER:", current_user)
    user = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only Admin can access."
        )

    return user

#------------------------------------------------------------------------------------------------------------------
#All Level Commission History
#------------------------------------------------------------------------------------------------------------------
@router.get("/history")
def all_level_income(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin)
):

    history = (
        db.query(LevelCommissionHistory)
        .order_by(LevelCommissionHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []

    for row in history:

        investor = db.query(User).filter(
            User.id == row.investor_id
        ).first()

        sponsor = db.query(User).filter(
            User.id == row.sponsor_id
        ).first()

        result.append({

            "id": row.id,

            "investment_id": row.investment_id,

            "investor_id": investor.user_id if investor else None,

            "investor_name": (
                f"{investor.first_name} {investor.last_name}"
                if investor else None
            ),

            "sponsor_id": sponsor.user_id if sponsor else None,

            "sponsor_name": (
                f"{sponsor.first_name} {sponsor.last_name}"
                if sponsor else None
            ),

            "level": row.level,

            "investment_amount": row.investment_amount,

            "commission_percentage": row.commission_percentage,

            "commission_amount": row.commission_amount,

            "status": row.status,

            "created_at": row.created_at

        })

    return result
#------------------------------------------------------------------------------------------------------------------
# Commission History By User
#------------------------------------------------------------------------------------------------------------------
@router.get("/history/{user_id}")
def user_level_income(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin)

):

    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    history = (
        db.query(LevelCommissionHistory)
        .filter(
            LevelCommissionHistory.sponsor_id == user.id
        )
        .order_by(
            LevelCommissionHistory.created_at.desc()
        )
        .all()
    )

    return history
#------------------------------------------------------------------------------------------------------------------
# invesment history
#------------------------------------------------------------------------------------------------------------------
@router.get("/investment/{investment_id}")
def investment_history(
    investment_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin)

):

    history = (
        db.query(LevelCommissionHistory)
        .filter(
            LevelCommissionHistory.investment_id == investment_id
        )
        .all()
    )

    return history

#------------------------------------------------------------------------------------------------------------------
# invesment Summary
#------------------------------------------------------------------------------------------------------------------
@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin)

):

    total_commission = (
        db.query(
            func.coalesce(
                func.sum(
                    LevelCommissionHistory.commission_amount
                ),
                0
            )
        )
        .scalar()
    )

    total_transactions = (
        db.query(LevelCommissionHistory)
        .count()
    )

    total_investment = (
        db.query(
            func.coalesce(
                func.sum(
                    LevelCommissionHistory.investment_amount
                ),
                0
            )
        )
        .scalar()
    )

    return {

        "total_commission": total_commission,

        "total_transactions": total_transactions,

        "total_investment": total_investment

    }

#-----------------------------------------------------------------------------------------------------------
# Today income
#-----------------------------------------------------------------------------------------------------------
@router.get("/today")
def today_income(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin)

):

    today = date.today()

    history = (
        db.query(LevelCommissionHistory)
        .filter(
            func.date(
                LevelCommissionHistory.created_at
            ) == today
        )
        .all()
    )

    total = sum(
        row.commission_amount
        for row in history
    )

    return {

        "today": today,

        "total_income": total,

        "transactions": history

    }

#-------------------------------------------------------------------------------------------------------
# Monthly income
#-------------------------------------------------------------------------------------------------------
@router.get("/month")
def monthly_income(
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin)

):

    history = (
        db.query(LevelCommissionHistory)
        .filter(
            func.extract(
                "year",
                LevelCommissionHistory.created_at
            ) == year,

            func.extract(
                "month",
                LevelCommissionHistory.created_at
            ) == month
        )
        .all()
    )

    total = sum(
        row.commission_amount
        for row in history
    )

    return {

        "year": year,

        "month": month,

        "total_income": total,

        "transactions": history

    }

#--------------------------------------------------------------------------------------------------------------
# Level wise report
#--------------------------------------------------------------------------------------------------------------
@router.get("/level/{level}")
def level_report(
    level: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin)

):

    history = (
        db.query(LevelCommissionHistory)
        .filter(
            LevelCommissionHistory.level == level
        )
        .all()
    )

    total = sum(
        row.commission_amount
        for row in history
    )

    return {

        "level": level,

        "total_commission": total,

        "transactions": history

    }

#------------------------------------------------------------------------------------------------------------------------
# Top earners
#------------------------------------------------------------------------------------------------------------------------
@router.get("/top-earners")
def top_earners(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin)

):

    data = (

        db.query(

            LevelCommissionHistory.sponsor_id,

            func.sum(
                LevelCommissionHistory.commission_amount
            ).label("income")

        )

        .group_by(
            LevelCommissionHistory.sponsor_id
        )

        .order_by(
            func.sum(
                LevelCommissionHistory.commission_amount
            ).desc()
        )

        .limit(10)

        .all()

    )

    result = []

    for row in data:

        user = (
            db.query(User)
            .filter(User.id == row.sponsor_id)
            .first()
        )

        result.append({

            "user_id": user.user_id,

            "name": f"{user.first_name} {user.last_name}",

            "income": row.income

        })

    return result

