from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin

from app.models import (
    User,
    LevelCommissionHistory,
    Investment,
)

from app.utils.templates import templates


router = APIRouter(
    prefix="/admin/level-income-report",
    tags=["Admin Level Income Report"],
)


# ==========================================================
# LEVEL INCOME REPORT API
# ==========================================================

@router.get("/")
def level_income_report(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: str | None = Query(None),
    user_id: str | None = Query(None),
    level: int | None = Query(None),

    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):

    # ======================================================
    # QUERY
    # sponsor = user receiving level income
    # ======================================================

    query = (
        db.query(
            LevelCommissionHistory,
            User,
            Investment,
        )
        .join(
            User,
            LevelCommissionHistory.sponsor_id == User.id,
        )
        .join(
            Investment,
            LevelCommissionHistory.investment_id == Investment.id,
        )
    )

    # ======================================================
    # FILTERS
    # ======================================================

    if start_date:
        start_datetime = datetime.combine(
            start_date,
            datetime.min.time(),
        )

        query = query.filter(
            LevelCommissionHistory.created_at >= start_datetime
        )

    if end_date:
        end_datetime = datetime.combine(
            end_date + timedelta(days=1),
            datetime.min.time(),
        )

        query = query.filter(
            LevelCommissionHistory.created_at < end_datetime
        )

    if status:
        query = query.filter(
            LevelCommissionHistory.status == status.upper()
        )

    if user_id:
        query = query.filter(
            User.user_id == user_id
        )

    if level is not None:
        query = query.filter(
            LevelCommissionHistory.level == level
        )

    # ======================================================
    # RESULTS
    # ======================================================

    results = (
        query
        .order_by(LevelCommissionHistory.id.desc())
        .all()
    )

    # ======================================================
    # REPORT
    # ======================================================

    data = []

    total_income = Decimal("0")
    total_investment_amount = Decimal("0")

    for history, user, investment in results:

        commission_amount = Decimal(
            str(history.commission_amount or 0)
        )

        investment_amount = Decimal(
            str(history.investment_amount or 0)
        )

        total_income += commission_amount
        total_investment_amount += investment_amount

        user_name = (
            f"{user.first_name or ''} "
            f"{user.last_name or ''}"
        ).strip()

        data.append({

            "id": history.id,

            # Sponsor / receiver of level income
            "user_id": user.user_id,

            "user_name": user_name,

            "investment_id": investment.investment_id,

            "level": history.level,

            "investment_amount":
                history.investment_amount,

            "commission_percentage":
                history.commission_percentage,

            "commission_amount":
                history.commission_amount,

            "status":
                history.status,

            "created_at":
                history.created_at,
        })

    # ======================================================
    # RESPONSE
    # ======================================================

    return {
        "total_records": len(data),

        "total_income": float(
            total_income
        ),

        "total_investment_amount": float(
            total_investment_amount
        ),

        "data": data,
    }


# ==========================================================
# PRINT LEVEL INCOME REPORT
# ==========================================================

@router.get(
    "/print",
    response_class=HTMLResponse,
)
def print_level_income_report(
    request: Request,

    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: str | None = Query(None),
    user_id: str | None = Query(None),
    level: int | None = Query(None),

    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):

    # ======================================================
    # QUERY
    # ======================================================

    query = (
        db.query(
            LevelCommissionHistory,
            User,
            Investment,
        )
        .join(
            User,
            LevelCommissionHistory.sponsor_id == User.id,
        )
        .join(
            Investment,
            LevelCommissionHistory.investment_id == Investment.id,
        )
    )

    # ======================================================
    # FILTERS
    # ======================================================

    if start_date:
        start_datetime = datetime.combine(
            start_date,
            datetime.min.time(),
        )

        query = query.filter(
            LevelCommissionHistory.created_at >= start_datetime
        )

    if end_date:
        end_datetime = datetime.combine(
            end_date + timedelta(days=1),
            datetime.min.time(),
        )

        query = query.filter(
            LevelCommissionHistory.created_at < end_datetime
        )

    if status:
        query = query.filter(
            LevelCommissionHistory.status == status.upper()
        )

    if user_id:
        query = query.filter(
            User.user_id == user_id
        )

    if level is not None:
        query = query.filter(
            LevelCommissionHistory.level == level
        )

    # ======================================================
    # RESULTS
    # ======================================================

    results = (
        query
        .order_by(LevelCommissionHistory.id.desc())
        .all()
    )

    # ======================================================
    # REPORT DATA
    # ======================================================

    report_data = []

    total_commission = Decimal("0")
    total_investment_amount = Decimal("0")

    for history, user, investment in results:

        commission_amount = Decimal(
            str(history.commission_amount or 0)
        )

        investment_amount = Decimal(
            str(history.investment_amount or 0)
        )

        total_commission += commission_amount
        total_investment_amount += investment_amount

        user_name = (
            f"{user.first_name or ''} "
            f"{user.last_name or ''}"
        ).strip()

        report_data.append({

            "id": history.id,

            # Sponsor receiving the commission
            "user_id": user.user_id,

            "user_name": user_name,

            "investment_id":
                investment.investment_id,

            "level":
                history.level,

            "investment_amount":
                history.investment_amount,

            "commission_percentage":
                history.commission_percentage,

            "commission_amount":
                history.commission_amount,

            "status":
                history.status,

            "date":
                history.created_at,
        })

    # ======================================================
    # SUMMARY
    # ======================================================

    summary = {
        "total_records": len(report_data),

        "total_investment_amount": float(
            total_investment_amount
        ),

        "total_commission": float(
            total_commission
        ),
    }

    # ======================================================
    # TEMPLATE
    # ======================================================

    return templates.TemplateResponse(
        request=request,
        name="reports/level_income_report.html",

        context={
            "title": "Level Income Report",

            "report_data": report_data,

            "summary": summary,

            "start_date": start_date,

            "end_date": end_date,

            "status": status,

            "user_id": user_id,

            "level": level,

            "generated_at": datetime.now(),
        },
    )