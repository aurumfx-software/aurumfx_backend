from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RankSetting, User
from app.schemas import RankSettingResponse,RankHolderResponse


router = APIRouter(
    prefix="/user/rank",
    tags=["User Rank"]
)


@router.get(
    "",
    response_model=list[RankSettingResponse]
)
def get_all_rank_settings(
    db: Session = Depends(get_db)
):
    """
    Get all rank settings.
    """

    ranks = (
        db.query(RankSetting)
        .filter(
            RankSetting.status.is_(True)
        )
        .order_by(
            RankSetting.rank_no.asc()
        )
        .all()
    )

    return ranks

@router.get(
    "/{rank_id}/holders",
    response_model=list[RankHolderResponse]
)
def get_rank_holders(
    rank_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all users who currently hold the specified rank.
    """

    rank = (
        db.query(RankSetting)
        .filter(RankSetting.id == rank_id)
        .first()
    )

    if not rank:
        raise HTTPException(
            status_code=404,
            detail="Rank not found"
        )

    users = (
        db.query(User)
        .filter(
            User.current_rank_id == rank_id
        )
        .order_by(User.id.asc())
        .all()
    )

    return [
        RankHolderResponse(
            id=user.id,
            user_id=user.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            rank_id=user.current_rank_id
        )
        for user in users
    ]