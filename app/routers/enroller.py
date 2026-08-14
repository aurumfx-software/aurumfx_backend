from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.core.security import get_current_user


from app.models import (
    User,
    Investment,
)

from app.schemas import (
    EnrollerResponse,
    EnrollerListResponse,
)


router = APIRouter(
    prefix="/user",
    tags=["User Enrollers"]
)
def get_user(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

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

    return user

@router.get(
    "/enrollers",
    response_model=EnrollerListResponse
)
def get_my_enrollers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user),
):

    # Find direct enrollers/sponsored users
    enrollers = (
        db.query(User)
        .filter(
            User.enroller_id == current_user.user_id,
            User.role == "USER"
        )
        .all()
    )

    result = []

    for user in enrollers:

        # Total investment amount
        investment_data = (
            db.query(
                func.coalesce(func.sum(Investment.amount), 0),
                func.coalesce(func.sum(Investment.lots), 0)
            )
            .filter(
                Investment.user_id == user.id,
                Investment.approval_status == "APPROVED",
                Investment.investment_status == "ACTIVE"
            )
            .first()
        )

        total_investment_amount = float(
            investment_data[0] or 0
        )

        total_lots = int(
            investment_data[1] or 0
        )

        # Current rank
        rank_name = None

        if user.current_rank:
            rank_name = user.current_rank.rank_name

        result.append(
            EnrollerResponse(
                user_id=user.user_id,
                fullname=f"{user.first_name} {user.last_name}",
                date_of_joining=(
                    user.created_at.date()
                    if user.created_at
                    else None
                ),
                rank=rank_name,
                total_investment_amount=total_investment_amount,
                total_lots=total_lots,
            )
        )

    return EnrollerListResponse(
        total=len(result),
        enrollers=result
    )