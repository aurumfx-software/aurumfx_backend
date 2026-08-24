from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import PayoutHistory, User
from app.utils.templates import templates


router = APIRouter(
    prefix="/admin/payout-report",
    tags=["Admin Payout Report"]
)


# ==========================================================
# PAYOUT REPORT
# ==========================================================

@router.get("/")
def payout_report(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: str | None = Query(None),
    user_id: str | None = Query(None),

    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):

    query = (
        db.query(
            PayoutHistory,
            User
        )
        .join(
            User,
            PayoutHistory.user_id == User.id
        )
    )

    # ------------------------------------------------------
    # DATE FILTER
    # ------------------------------------------------------

    if start_date:
        query = query.filter(
            PayoutHistory.paid_at >= start_date
        )

    if end_date:
        query = query.filter(
            PayoutHistory.paid_at < (
                end_date + timedelta(days=1)
            )
        )

    # ------------------------------------------------------
    # STATUS FILTER
    # ------------------------------------------------------

    if status:
        query = query.filter(
            PayoutHistory.status == status.upper()
        )

    # ------------------------------------------------------
    # USER FILTER
    # ------------------------------------------------------

    if user_id:
        query = query.filter(
            User.user_id == user_id
        )

    # ------------------------------------------------------
    # RESULTS
    # ------------------------------------------------------

    results = (
        query
        .order_by(
            PayoutHistory.id.desc()
        )
        .all()
    )

    # ------------------------------------------------------
    # REPORT DATA
    # ------------------------------------------------------

    data = []

    total_referral_income = Decimal("0")
    total_level_income = Decimal("0")
    total_rank_income = Decimal("0")
    total_income = Decimal("0")
    total_admin_fee = Decimal("0")
    total_net_payable = Decimal("0")

    for payout, user in results:

        referral_income = Decimal(
            str(payout.referral_income or 0)
        )

        level_income = Decimal(
            str(payout.level_income or 0)
        )

        rank_income = Decimal(
            str(payout.rank_income or 0)
        )

        payout_income = Decimal(
            str(payout.total_income or 0)
        )

        admin_fee = Decimal(
            str(payout.admin_fee or 0)
        )

        net_payable = Decimal(
            str(payout.net_payable or 0)
        )

        # --------------------------------------------------
        # TOTALS
        # --------------------------------------------------

        total_referral_income += referral_income
        total_level_income += level_income
        total_rank_income += rank_income
        total_income += payout_income
        total_admin_fee += admin_fee
        total_net_payable += net_payable

        # --------------------------------------------------
        # USER NAME
        # --------------------------------------------------

        user_name = (
            f"{user.first_name} "
            f"{user.last_name or ''}"
        ).strip()

        # --------------------------------------------------
        # REPORT ROW
        # --------------------------------------------------

        data.append({
            "id": payout.id,

            "user_id": user.user_id,

            "user_name": user_name,

            "referral_income": referral_income,

            "level_income": level_income,

            "rank_income": rank_income,

            "total_income": payout_income,

            "admin_fee_percentage": Decimal(
                str(payout.admin_fee_percentage or 0)
            ),

            "admin_fee": admin_fee,

            "net_payable": net_payable,

            "payout_method": payout.payout_method,

            "payout_information": payout.payout_information,

            "status": payout.status,

            "paid_at": payout.paid_at,

            "created_at": payout.created_at,
        })

    # ------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------

    return {
        "total_records": len(data),

        "total_referral_income": float(
            total_referral_income
        ),

        "total_level_income": float(
            total_level_income
        ),

        "total_rank_income": float(
            total_rank_income
        ),

        "total_income": float(
            total_income
        ),

        "total_admin_fee": float(
            total_admin_fee
        ),

        "total_net_payable": float(
            total_net_payable
        ),

        "data": data,
    }


# ==========================================================
# PRINT PAYOUT REPORT
# ==========================================================

@router.get(
    "/print",
    response_class=HTMLResponse
)
def print_payout_report(
    request: Request,

    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: str | None = Query(None),
    user_id: str | None = Query(None),

    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):

    # ======================================================
    # QUERY
    # ======================================================

    query = (
        db.query(
            PayoutHistory,
            User
        )
        .join(
            User,
            PayoutHistory.user_id == User.id
        )
    )

    # ======================================================
    # DATE FILTER
    # ======================================================

    if start_date:
        query = query.filter(
            PayoutHistory.paid_at >= start_date
        )

    if end_date:
        query = query.filter(
            PayoutHistory.paid_at < (
                end_date + timedelta(days=1)
            )
        )

    # ======================================================
    # STATUS FILTER
    # ======================================================

    if status:
        query = query.filter(
            PayoutHistory.status == status.upper()
        )

    # ======================================================
    # USER FILTER
    # ======================================================

    if user_id:
        query = query.filter(
            User.user_id == user_id
        )

    # ======================================================
    # RESULTS
    # ======================================================

    results = (
        query
        .order_by(
            PayoutHistory.id.desc()
        )
        .all()
    )

    # ======================================================
    # REPORT DATA
    # ======================================================

    report_data = []

    total_referral_income = Decimal("0")
    total_level_income = Decimal("0")
    total_rank_income = Decimal("0")
    total_income = Decimal("0")
    total_admin_fee = Decimal("0")
    total_net_payable = Decimal("0")

    for payout, user in results:

        # --------------------------------------------------
        # AMOUNTS
        # --------------------------------------------------

        referral_income = Decimal(
            str(payout.referral_income or 0)
        )

        level_income = Decimal(
            str(payout.level_income or 0)
        )

        rank_income = Decimal(
            str(payout.rank_income or 0)
        )

        payout_income = Decimal(
            str(payout.total_income or 0)
        )

        admin_fee = Decimal(
            str(payout.admin_fee or 0)
        )

        net_payable = Decimal(
            str(payout.net_payable or 0)
        )

        admin_fee_percentage = Decimal(
            str(payout.admin_fee_percentage or 0)
        )

        # --------------------------------------------------
        # TOTALS
        # --------------------------------------------------

        total_referral_income += referral_income
        total_level_income += level_income
        total_rank_income += rank_income
        total_income += payout_income
        total_admin_fee += admin_fee
        total_net_payable += net_payable

        # --------------------------------------------------
        # USER NAME
        # --------------------------------------------------

        user_name = (
            f"{user.first_name} "
            f"{user.last_name or ''}"
        ).strip()

        # --------------------------------------------------
        # REPORT ROW
        # --------------------------------------------------

        report_data.append({

            "id": payout.id,

            "user_id": user.user_id,

            "user_name": user_name,

            "referral_income": referral_income,

            "level_income": level_income,

            "rank_income": rank_income,

            "total_income": payout_income,

            "admin_fee_percentage": admin_fee_percentage,

            "admin_fee": admin_fee,

            "net_payable": net_payable,

            "payout_method": payout.payout_method,

            "payout_information": payout.payout_information,

            "status": payout.status,

            "paid_at": payout.paid_at,

            "created_at": payout.created_at,
        })

    # ======================================================
    # SUMMARY
    # ======================================================

    summary = {

        "total_records": len(report_data),

        "total_referral_income": float(
            total_referral_income
        ),

        "total_level_income": float(
            total_level_income
        ),

        "total_rank_income": float(
            total_rank_income
        ),

        "total_income": float(
            total_income
        ),

        "total_admin_fee": float(
            total_admin_fee
        ),

        "total_net_payable": float(
            total_net_payable
        ),
    }

    # ======================================================
    # TEMPLATE
    # ======================================================

    return templates.TemplateResponse(
        request=request,

        name="reports/payout_report.html",

        context={

            "title": "Payout Report",

            "report_data": report_data,

            "summary": summary,

            "start_date": start_date,

            "end_date": end_date,

            "status": status,

            "user_id": user_id,

            "generated_at": datetime.now(),
        }
    )