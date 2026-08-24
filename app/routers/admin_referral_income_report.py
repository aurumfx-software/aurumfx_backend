from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import (
    User,
    ReferralCommission,
    Investment,
)
from app.utils.templates import templates


router = APIRouter(
    prefix="/admin/referral-income-report",
    tags=["Admin Referral Income Report"]
)


# ==========================================================
# REFERRAL INCOME REPORT API
# ==========================================================

@router.get("/")
def referral_income_report(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: str | None = Query(None),
    user_id: str | None = Query(None),

    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):

    query = (
        db.query(
            ReferralCommission,
            User,
            Investment,
        )
        .join(
            User,
            ReferralCommission.enroller_id == User.id
        )
        .join(
            Investment,
            ReferralCommission.investment_id
            == Investment.id
        )
    )

    # --------------------------------------------------
    # Filters
    # --------------------------------------------------

    if start_date:
        query = query.filter(
            ReferralCommission.created_at >= start_date
        )

    if end_date:
        next_day = date.fromordinal(
            end_date.toordinal() + 1
        )

        query = query.filter(
            ReferralCommission.created_at < next_day
        )

    if status:
        query = query.filter(
            ReferralCommission.status
            == status.upper()
        )

    if user_id:
        query = query.filter(
            User.user_id == user_id
        )

    # --------------------------------------------------
    # Results
    # --------------------------------------------------

    results = (
        query
        .order_by(
            ReferralCommission.id.desc()
        )
        .all()
    )

    # --------------------------------------------------
    # Report Data
    # --------------------------------------------------

    data = []

    total_investment_amount = Decimal("0")
    total_commission_amount = Decimal("0")
    total_paid_amount = Decimal("0")
    total_washout_amount = Decimal("0")

    for (
        commission,
        user,
        investment
    ) in results:

        investment_amount = Decimal(
            str(
                commission.investment_amount or 0
            )
        )

        commission_amount = Decimal(
            str(
                commission.commission_amount or 0
            )
        )

        paid_amount = Decimal(
            str(
                commission.paid_amount or 0
            )
        )

        washout_amount = Decimal(
            str(
                commission.washout_amount or 0
            )
        )

        total_investment_amount += (
            investment_amount
        )

        total_commission_amount += (
            commission_amount
        )

        total_paid_amount += (
            paid_amount
        )

        total_washout_amount += (
            washout_amount
        )

        user_name = (
            f"{user.first_name} "
            f"{user.last_name or ''}"
        ).strip()

        investor = (
            db.query(User)
            .filter(
                User.id == commission.investor_id
            )
            .first()
        )

        investor_name = ""

        if investor:
            investor_name = (
                f"{investor.first_name} "
                f"{investor.last_name or ''}"
            ).strip()

        data.append({

            "id":
                commission.id,

            "user_id":
                user.user_id,

            "user_name":
                user_name,

            "investor_id":
                investor.user_id
                if investor else "",

            "investor_name":
                investor_name,

            "investment_id":
                investment.investment_id,

            "investment_amount":
                commission.investment_amount,

            "commission_percentage":
                commission.commission_percentage,

            "commission_amount":
                commission.commission_amount,

            "paid_amount":
                commission.paid_amount,

            "washout_amount":
                commission.washout_amount,

            "status":
                commission.status,

            "payment_date":
                commission.payment_date,

            "created_at":
                commission.created_at,
        })

    return {

        "total_records":
            len(data),

        "total_investment_amount":
            float(total_investment_amount),

        "total_commission_amount":
            float(total_commission_amount),

        "total_paid_amount":
            float(total_paid_amount),

        "total_washout_amount":
            float(total_washout_amount),

        "data":
            data,
    }


# ==========================================================
# PRINT REFERRAL INCOME REPORT
# ==========================================================

@router.get(
    "/print",
    response_class=HTMLResponse
)
def print_referral_income_report(
    request: Request,

    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: str | None = Query(None),
    user_id: str | None = Query(None),

    db: Session = Depends(get_db),

    admin=Depends(get_current_admin),
):

    # --------------------------------------------------
    # Query
    # --------------------------------------------------

    query = (
        db.query(
            ReferralCommission,
            User,
            Investment,
        )
        .join(
            User,
            ReferralCommission.enroller_id == User.id
        )
        .join(
            Investment,
            ReferralCommission.investment_id
            == Investment.id
        )
    )

    # --------------------------------------------------
    # Filters
    # --------------------------------------------------

    if start_date:

        query = query.filter(
            ReferralCommission.created_at
            >= start_date
        )

    if end_date:

        next_day = date.fromordinal(
            end_date.toordinal() + 1
        )

        query = query.filter(
            ReferralCommission.created_at
            < next_day
        )

    if status:

        query = query.filter(
            ReferralCommission.status
            == status.upper()
        )

    if user_id:

        query = query.filter(
            User.user_id == user_id
        )

    # --------------------------------------------------
    # Results
    # --------------------------------------------------

    results = (
        query
        .order_by(
            ReferralCommission.id.desc()
        )
        .all()
    )

    # --------------------------------------------------
    # Report Data
    # --------------------------------------------------

    report_data = []

    total_investment_amount = Decimal("0")
    total_commission_amount = Decimal("0")
    total_paid_amount = Decimal("0")
    total_washout_amount = Decimal("0")

    for (
        commission,
        user,
        investment
    ) in results:

        user_name = (
            f"{user.first_name} "
            f"{user.last_name or ''}"
        ).strip()

        # ----------------------------------------------
        # Investor
        # ----------------------------------------------

        investor = (
            db.query(User)
            .filter(
                User.id == commission.investor_id
            )
            .first()
        )

        investor_name = ""

        if investor:

            investor_name = (
                f"{investor.first_name} "
                f"{investor.last_name or ''}"
            ).strip()

        # ----------------------------------------------
        # Totals
        # ----------------------------------------------

        investment_amount = Decimal(
            str(
                commission.investment_amount or 0
            )
        )

        commission_amount = Decimal(
            str(
                commission.commission_amount or 0
            )
        )

        paid_amount = Decimal(
            str(
                commission.paid_amount or 0
            )
        )

        washout_amount = Decimal(
            str(
                commission.washout_amount or 0
            )
        )

        total_investment_amount += (
            investment_amount
        )

        total_commission_amount += (
            commission_amount
        )

        total_paid_amount += (
            paid_amount
        )

        total_washout_amount += (
            washout_amount
        )

        # ----------------------------------------------
        # Report Row
        # ----------------------------------------------

        report_data.append({

            "id":
                commission.id,

            # Receiver
            "user_id":
                user.user_id,

            "user_name":
                user_name,

            # Investor
            "investor_id":
                investor.user_id
                if investor else "",

            "investor_name":
                investor_name,

            # Investment
            "investment_id":
                investment.investment_id,

            "investment_amount":
                commission.investment_amount,

            # Commission
            "commission_percentage":
                commission.commission_percentage,

            "commission_amount":
                commission.commission_amount,

            "paid_amount":
                commission.paid_amount,

            "washout_amount":
                commission.washout_amount,

            "status":
                commission.status,

            "payment_date":
                commission.payment_date,

            "created_at":
                commission.created_at,
        })

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    summary = {

        "total_records":
            len(report_data),

        "total_investment_amount":
            float(total_investment_amount),

        "total_commission_amount":
            float(total_commission_amount),

        "total_paid_amount":
            float(total_paid_amount),

        "total_washout_amount":
            float(total_washout_amount),
    }

    # --------------------------------------------------
    # Filters
    # --------------------------------------------------

    filters = {

        "start_date":
            start_date,

        "end_date":
            end_date,

        "status":
            status,

        "user_id":
            user_id,
    }

    # --------------------------------------------------
    # Template
    # --------------------------------------------------

    return templates.TemplateResponse(

        request=request,

        name="reports/referral_income_report.html",

        context={

            "title":
                "Referral Income Report",

            "report_data":
                report_data,

            "summary":
                summary,

            "filters":
                filters,

            "start_date":
                start_date,

            "end_date":
                end_date,

            "status":
                status,

            "user_id":
                user_id,

            "generated_at":
                datetime.now(),
        }
    )