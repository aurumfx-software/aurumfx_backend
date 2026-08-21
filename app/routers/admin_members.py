from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import User, RankSetting

router = APIRouter(
    prefix="/api/admin/members",
    tags=["Admin - Member Management"]
)


@router.get("/")
def get_members(
    start_date: date | None = Query(
        None,
        description="Filter members joined from this date"
    ),
    end_date: date | None = Query(
        None,
        description="Filter members joined until this date"
    ),
    user_id: str | None = Query(
        None,
        description="Search by user ID"
    ),
    rank: str | None = Query(
        None,
        description="Filter by rank"
    ),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    query = (
    db.query(
        User.id,

        User.user_id,

        func.concat(
            User.first_name,
            " ",
            User.last_name
        ).label("fullname"),

        User.profile_image,

        RankSetting.rank_name.label("rank"),

        func.date(User.created_at).label("join_date"),
    )
    .outerjoin(
        RankSetting,
        RankSetting.id == User.current_rank_id
    )
)

    # User ID filter
    if user_id:
        query = query.filter(
            User.user_id.ilike(f"%{user_id}%")
        )

    # Start date
    if start_date:
        query = query.filter(
            User.created_at >= start_date
        )

    # End date
    if end_date:
        query = query.filter(
            User.created_at < end_date + timedelta(days=1)
        )

    # Rank filter
    if rank:
        query = query.filter(
            RankSetting.name.ilike(f"%{rank}%")
        )

    users = (
        query
        .order_by(User.created_at.desc())
        .all()
    )

    return [
        {
            "id": user.id,
            "user_id": user.user_id,
            "fullname": user.fullname,
            "profile_image": user.profile_image,
            "rank": user.rank or "No Rank",
            "join_date": user.join_date,
        }
        for user in users
    ]