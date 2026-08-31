from datetime import date, datetime, timedelta
from decimal import Decimal


from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import (
    User,
    RankSetting,
    UserRankHistory,
)
from app.utils.templates import templates


router = APIRouter(
    prefix="/admin/rank-income-report",
    tags=["Admin Rank Income Report"]
)


# ==========================================================
# RANK INCOME REPORT
# ==========================================================

@router.get("/")
def rank_income_report(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: str | None = Query(None),
    user_id: str | None = Query(None),
    rank_id: int | None = Query(None),

    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):

    query = (
        db.query(
            UserRankHistory,
            User,
            RankSetting,
        )
        .join(
            User,
            UserRankHistory.user_id == User.id
        )
        .join(
            RankSetting,
            UserRankHistory.rank_id == RankSetting.id
        )
    )

    # ------------------------------------------------------
    # DATE FILTER
    # ------------------------------------------------------

    if start_date:
        query = query.filter(
            UserRankHistory.achieved_at >= start_date
        )

    if end_date:
        query = query.filter(
            UserRankHistory.achieved_at < (
                end_date.fromordinal(end_date.toordinal() + 1)
            )
        )

    # ------------------------------------------------------
    # STATUS FILTER
    # ------------------------------------------------------

    if status:
        query = query.filter(
            UserRankHistory.reward_paid ==
            (
                status.upper() == "PAID"
            )
        )

    # ------------------------------------------------------
    # USER FILTER
    # ------------------------------------------------------

    if user_id:
        query = query.filter(
            User.user_id == user_id
        )

    # ------------------------------------------------------
    # RANK FILTER
    # ------------------------------------------------------

    if rank_id:
        query = query.filter(
            UserRankHistory.rank_id == rank_id
        )

    results = (
        query
        .order_by(
            UserRankHistory.id.desc()
        )
        .all()
    )

    # ------------------------------------------------------
    # RESPONSE DATA
    # ------------------------------------------------------

    data = []

    total_income = 0
    total_paid = 0
    total_pending = 0

    for history, user, rank in results:

        reward_income = float(
            history.reward_income or 0
        )

        total_income += reward_income

        if history.reward_paid:
            total_paid += reward_income
            reward_status = "PAID"
        else:
            total_pending += reward_income
            reward_status = "PENDING"

        user_name = (
            f"{user.first_name} "
            f"{user.last_name or ''}"
        ).strip()

        data.append({
            "id": history.id,

            "user_id": user.user_id,

            "user_name": user_name,

            "rank_id": rank.id,

            "rank_name": rank.rank_name,

            "rank_no": rank.rank_no,

            "reward_income": reward_income,

            "reward_paid": history.reward_paid,

            "status": reward_status,

            "achieved_at": history.achieved_at,

            "paid_at": history.paid_at,
        })

    return {
        "total_records": len(data),
        "total_income": total_income,
        "total_paid": total_paid,
        "total_pending": total_pending,
        "data": data,
    }


# ==========================================================
# PRINT RANK INCOME REPORT
# ==========================================================

@router.get(
    "/print",
    response_class=HTMLResponse,
)
def print_rank_income_report(
    request: Request,

    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: str | None = Query(None),
    user_id: str | None = Query(None),
    rank_id: int | None = Query(None),

    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):

    # ==================================================
    # QUERY
    # ==================================================

    query = (
        db.query(
            UserRankHistory,
            User,
            RankSetting,
        )
        .join(
            User,
            UserRankHistory.user_id == User.id,
        )
        .join(
            RankSetting,
            UserRankHistory.rank_id == RankSetting.id,
        )
    )

    # ==================================================
    # DATE FILTERS
    # ==================================================

    if start_date:
        start_datetime = datetime.combine(
            start_date,
            datetime.min.time(),
        )

        query = query.filter(
            UserRankHistory.achieved_at >= start_datetime
        )

    if end_date:
        end_datetime = datetime.combine(
            end_date + timedelta(days=1),
            datetime.min.time(),
        )

        query = query.filter(
            UserRankHistory.achieved_at < end_datetime
        )

    # ==================================================
    # STATUS FILTER
    # ==================================================

    if status:
        query = query.filter(
            UserRankHistory.reward_paid
            == (status.upper() == "PAID")
        )

    # ==================================================
    # USER FILTER
    # ==================================================

    if user_id:
        query = query.filter(
            User.user_id == user_id
        )

    # ==================================================
    # RANK FILTER
    # ==================================================

    if rank_id:
        query = query.filter(
            UserRankHistory.rank_id == rank_id
        )

    # ==================================================
    # RESULTS
    # ==================================================

    results = (
        query
        .order_by(
            UserRankHistory.id.desc()
        )
        .all()
    )

    # ==================================================
    # REPORT DATA
    # ==================================================

    report_data = []

    total_reward_income = Decimal("0")
    total_paid = Decimal("0")
    total_pending = Decimal("0")

    for history, user, rank in results:

        user_name = (
            f"{user.first_name or ''} "
            f"{user.last_name or ''}"
        ).strip()

        reward_income = Decimal(
            str(history.reward_income or 0)
        )

        total_reward_income += reward_income

        if history.reward_paid:
            reward_status = "PAID"
            total_paid += reward_income
        else:
            reward_status = "PENDING"
            total_pending += reward_income

        report_data.append({

            "id": history.id,

            "user_id": user.user_id,

            "user_name": user_name,

            "rank_id": rank.id,

            "rank_name": rank.rank_name,

            "rank_no": rank.rank_no,

            "reward_income": history.reward_income,

            "status": reward_status,

            "achieved_at": history.achieved_at,

            "paid_at": history.paid_at,
        })

    # ==================================================
    # SUMMARY
    # ==================================================

    summary = {

        "total_records": len(report_data),

        "total_reward_income": float(
            total_reward_income
        ),

        "total_paid": float(
            total_paid
        ),

        "total_pending": float(
            total_pending
        ),
    }

    # ==================================================
    # TEMPLATE
    # ==================================================

    return templates.TemplateResponse(

        request=request,

        name="reports/rank_income_report.html",

        context={

            "title": "Rank Income Report",

            "report_data": report_data,

            "summary": summary,

            "start_date": start_date,

            "end_date": end_date,

            "status": status,

            "user_id": user_id,

            "rank_id": rank_id,

            "generated_at": datetime.now(),
        },
    )