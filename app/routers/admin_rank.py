from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from app.database import get_db
from app.models import (
    RankSetting,
    RankCondition,
    User,
    UserRankHistory
)
from app.schemas import (
    RankSettingCreate,
    RankSettingUpdate,
    RankSettingResponse,
    RankHolderResponse,
    AdminRankSettingResponse
)
from app.core.security import get_current_user

router = APIRouter(
    prefix="/admin/ranks",
    tags=["Admin Rank"]
)

# --------------------------------------------------
# Admin Authentication
# --------------------------------------------------
def get_admin(
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

    if user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only Admin can access."
        )

    return user

#--------------------------------------------------------------------------
#Create post API
#--------------------------------------------------------------------------
@router.post(
    "/",
    response_model=RankSettingResponse
)
def create_rank(
    request: RankSettingCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin)
):

    existing = (
        db.query(RankSetting)
        .filter(
            RankSetting.rank_name == request.rank_name
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Rank name already exists"
        )

    existing = (
        db.query(RankSetting)
        .filter(
            RankSetting.rank_no == request.rank_no
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Rank number already exists"
        )

    rank = RankSetting(
        rank_name=request.rank_name,
        rank_no=request.rank_no,
        minimum_total_lots=request.minimum_total_lots,
        minimum_direct_sponsors=request.minimum_direct_sponsors,
        reward_income=request.reward_income,
        status=request.status,
        criteria=request.criteria
    )

    db.add(rank)
    db.commit()
    db.refresh(rank)

    for condition in request.conditions:

        db.add(
            RankCondition(
                rank_id=rank.id,
                minimum_group_lots=condition.minimum_group_lots,
                required_group_count=condition.required_group_count,
                order_no=condition.order_no
            )
        )

    db.commit()

    db.refresh(rank)

    return rank
#--------------------------------------------------------------------------------------------------
# Get all rank
#--------------------------------------------------------------------------------------------------
@router.get(
    "/",
    response_model=list[AdminRankSettingResponse]
)
def get_all_ranks(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin)
):
    ranks = (
        db.query(RankSetting)
        .options(
            joinedload(RankSetting.conditions)
        )
        .order_by(
            RankSetting.rank_no
        )
        .all()
    )

    return ranks
#-------------------------------------------------------------------------------------------------------
# Get single rank
#-------------------------------------------------------------------------------------------------------
@router.get(
    "/{rank_id}",
    response_model=RankSettingResponse
)
def get_rank(
    rank_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin)
):

    rank = (
        db.query(RankSetting)
        .options(
            joinedload(RankSetting.conditions)
        )
        .filter(
            RankSetting.id == rank_id
        )
        .first()
    )

    if not rank:
        raise HTTPException(
            status_code=404,
            detail="Rank not found"
        )

    return rank
#----------------------------------------------------------------------------------------------------
# Update rank
#----------------------------------------------------------------------------------------------------
@router.put(
    "/{rank_id}",
    response_model=RankSettingResponse
)
def update_rank(
    rank_id: int,
    request: RankSettingUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin)
):
    rank = (
        db.query(RankSetting)
        .filter(
            RankSetting.id == rank_id
        )
        .first()
    )

    if not rank:
        raise HTTPException(
            status_code=404,
            detail="Rank not found"
        )
        rank.rank_name = request.rank_name
    rank.rank_no = request.rank_no
    rank.minimum_total_lots = request.minimum_total_lots
    rank.minimum_direct_sponsors = request.minimum_direct_sponsors
    rank.reward_income = request.reward_income
    rank.status = request.status
    rank.criteria = request.criteria

    db.commit()
    rank.rank_name = request.rank_name
    rank.rank_no = request.rank_no
    rank.minimum_total_lots = request.minimum_total_lots
    rank.minimum_direct_sponsors = request.minimum_direct_sponsors
    rank.reward_income = request.reward_income
    rank.status = request.status
    rank.criteria = request.criteria


    db.commit()
    db.query(
        RankCondition
    ).filter(
        RankCondition.rank_id == rank.id
    ).delete()

    db.commit()

    for item in request.conditions:
    
            db.add(
                RankCondition(
                    rank_id=rank.id,
                    minimum_group_lots=item.minimum_group_lots,
                    required_group_count=item.required_group_count,
                    order_no=item.order_no
                )
            )
    
    db.commit()

    rank = (
        db.query(RankSetting)
        .options(
            joinedload(RankSetting.conditions)
        )
        .filter(
            RankSetting.id == rank.id
        )
        .first()
    )

    return rank

#--------------------------------------------------------------------------------------------
# Delete rank
#--------------------------------------------------------------------------------------------
@router.delete(
    "/{rank_id}"
)
def delete_rank(
    rank_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin)
):

    rank = (
        db.query(RankSetting)
        .filter(
            RankSetting.id == rank_id
        )
        .first()
    )

    if not rank:
        raise HTTPException(
            status_code=404,
            detail="Rank not found"
        )

    db.delete(rank)

    db.commit()

    return {
        "message":"Rank deleted successfully"
    }



@router.get(
    "/{rank_id}/holders",
    response_model=list[RankHolderResponse]
)
def get_rank_holders(
    rank_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all users who currently hold the specified rank,
    including the date they achieved the rank.
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

    holders = (
        db.query(User, UserRankHistory.achieved_at)
        .join(
            UserRankHistory,
            UserRankHistory.user_id == User.id
        )
        .filter(
            User.current_rank_id == rank_id,
            UserRankHistory.rank_id == rank_id
        )
        .order_by(
            User.id.asc()
        )
        .all()
    )

    return [
        RankHolderResponse(
            id=user.id,
            user_id=user.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            rank_id=user.current_rank_id,
            image=user.profile_image,
            achieved_at=achieved_at,
        )
        for user, achieved_at in holders
    ]