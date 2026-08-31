from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import (
    User,
    Investment,
    InvestmentPlan,
    ReturnType,
)
from app.utils.templates import templates


router = APIRouter(
    prefix="/admin/investment-report",
    tags=["Admin Investment Report"]
)


# ==========================================================
# INVESTMENT REPORT API
# ==========================================================

@router.get("/")
def investment_report(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: str | None = Query(None),
    user_id: str | None = Query(None),
    investment_plan_id: int | None = Query(None),
    return_type_id: int | None = Query(None),

    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):

    query = (
        db.query(
            Investment,
            User,
            InvestmentPlan,
            ReturnType,
        )
        .join(
            User,
            Investment.user_id == User.id
        )
        .join(
            InvestmentPlan,
            Investment.investment_plan_id == InvestmentPlan.id
        )
        .join(
            ReturnType,
            Investment.return_type_id == ReturnType.id
        )
    )

    # --------------------------------------------------
    # Filters
    # --------------------------------------------------

    if start_date:
        query = query.filter(
            Investment.investment_date >= start_date
        )

    if end_date:
        query = query.filter(
            Investment.investment_date <= end_date
        )

    if status:
        query = query.filter(
            Investment.investment_status == status.upper()
        )

    if user_id:
        query = query.filter(
            User.user_id == user_id
        )

    if investment_plan_id:
        query = query.filter(
            Investment.investment_plan_id == investment_plan_id
        )

    if return_type_id:
        query = query.filter(
            Investment.return_type_id == return_type_id
        )

    investments = (
        query
        .order_by(Investment.id.desc())
        .all()
    )

    # --------------------------------------------------
    # Report
    # --------------------------------------------------

    data = []

    total_amount = Decimal("0")
    total_lots = 0

    for investment, user, plan, return_type in investments:

        amount = Decimal(
            str(investment.amount or 0)
        )

        total_amount += amount
        total_lots += investment.lots or 0

        user_name = (
            f"{user.first_name} {user.last_name or ''}"
        ).strip()

        data.append({
            "id": investment.id,

            "investment_id": investment.investment_id,

            "user_id": user.user_id,

            "user_name": user_name,

            "investment_plan_id": plan.id,

            "plan_name": plan.plan_name,

            "return_type_id": return_type.id,

            "return_type": return_type.return_type,

            "amount": investment.amount,

            "lots": investment.lots,

            "monthly_return_percentage": (
                investment.monthly_return_percentage
            ),

            "monthly_return_amount": (
                investment.monthly_return_amount
            ),

            "return_which": investment.return_which,

            "return_balance": investment.return_balance,

            "return_date": investment.return_date,

            "investment_status": (
                investment.investment_status
            ),

            "approval_status": (
                investment.approval_status
            ),

            "bank_transaction_id": (
                investment.bank_transaction_id
            ),

            "investment_date": (
                investment.investment_date
            ),
        })

    return {
        "total_records": len(data),
        "total_amount": float(total_amount),
        "total_lots": total_lots,
        "data": data,
    }


# ==========================================================
# PRINT INVESTMENT REPORT
# ==========================================================



@router.get(
    "/print",
    response_class=HTMLResponse
)
def print_investment_report(
    request: Request,

    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: str | None = Query(None),
    user_id: str | None = Query(None),
    investment_plan_id: int | None = Query(None),
    return_type_id: int | None = Query(None),

    db: Session = Depends(get_db),

    admin=Depends(get_current_admin),
):

    # ==========================================================
    # QUERY
    # ==========================================================

    query = (
        db.query(
            Investment,
            User,
            InvestmentPlan,
            ReturnType,
        )
        .join(
            User,
            Investment.user_id == User.id
        )
        .join(
            InvestmentPlan,
            Investment.investment_plan_id
            == InvestmentPlan.id
        )
        .join(
            ReturnType,
            Investment.return_type_id
            == ReturnType.id
        )
    )

    # ==========================================================
    # FILTERS
    # ==========================================================

    if start_date:
        query = query.filter(
            Investment.investment_date >= start_date
        )

    if end_date:
        next_day = date.fromordinal(
            end_date.toordinal() + 1
        )

        query = query.filter(
            Investment.investment_date < next_day
        )

    if status:
        query = query.filter(
            Investment.investment_status
            == status.upper()
        )

    if user_id:
        query = query.filter(
            User.user_id == user_id
        )

    if investment_plan_id:
        query = query.filter(
            Investment.investment_plan_id
            == investment_plan_id
        )

    if return_type_id:
        query = query.filter(
            Investment.return_type_id
            == return_type_id
        )

    # ==========================================================
    # RESULTS
    # ==========================================================

    results = (
        query
        .order_by(
            Investment.id.desc()
        )
        .all()
    )

    # ==========================================================
    # REPORT DATA
    # ==========================================================

    report_data = []

    total_amount = Decimal("0")
    total_lots = 0

    approved_count = 0
    pending_count = 0
    rejected_count = 0

    for (
        investment,
        user,
        plan,
        return_type
    ) in results:

        # ------------------------------------------------------
        # USER NAME
        # ------------------------------------------------------

        user_name = (
            f"{user.first_name} "
            f"{user.last_name or ''}"
        ).strip()

        # ------------------------------------------------------
        # AMOUNT
        # ------------------------------------------------------

        amount = Decimal(
            str(
                investment.amount or 0
            )
        )

        total_amount += amount

        # ------------------------------------------------------
        # LOTS
        # ------------------------------------------------------

        total_lots += (
            investment.lots or 0
        )

        # ------------------------------------------------------
        # STATUS COUNTS
        # ------------------------------------------------------

        investment_status = (
            investment.investment_status
            or ""
        ).upper()

        if investment_status == "APPROVED":
            approved_count += 1

        elif investment_status == "PENDING":
            pending_count += 1

        elif investment_status == "REJECTED":
            rejected_count += 1

        # ------------------------------------------------------
        # REPORT ROW
        # ------------------------------------------------------

        report_data.append({

            "investment_id":
                investment.investment_id,

            "user_id":
                user.user_id,

            "user_name":
                user_name,

            "plan_name":
                plan.plan_name,

            "return_type":
                return_type.return_type,

            "amount":
                investment.amount,

            "lots":
                investment.lots,

            "monthly_return_percentage":
                investment.monthly_return_percentage,

            "monthly_return_amount":
                investment.monthly_return_amount,

            "investment_date":
                investment.investment_date,

            "return_date":
                investment.return_date,

            "investment_status":
                investment.investment_status,

            "approval_status":
                investment.approval_status,

            "bank_transaction_id":
                investment.bank_transaction_id,
        })

    # ==========================================================
    # SUMMARY
    # ==========================================================

    summary = {

        "total_records":
            len(report_data),

        "total_amount":
            float(total_amount),

        "total_lots":
            total_lots,

        "approved_count":
            approved_count,

        "pending_count":
            pending_count,

        "rejected_count":
            rejected_count,
    }

    # ==========================================================
    # FILTERS
    # ==========================================================

    filters = {

        "start_date":
            start_date,

        "end_date":
            end_date,

        "status":
            status,

        "user_id":
            user_id,

        "investment_plan_id":
            investment_plan_id,

        "return_type_id":
            return_type_id,
    }

    # ==========================================================
    # TEMPLATE
    # ==========================================================

    return templates.TemplateResponse(

        request=request,

        name="reports/investment_report.html",

        context={

            "title":
                "Investment Report",

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

            "investment_plan_id":
                investment_plan_id,

            "return_type_id":
                return_type_id,

            "generated_at":
                datetime.now(),
        }
    )
