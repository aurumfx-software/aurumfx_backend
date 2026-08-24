from datetime import date, datetime

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
                end_date.fromordinal(
                    end_date.toordinal() + 1
                )
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

    total_referral_income = 0
    total_level_income = 0
    total_rank_income = 0
    total_income = 0
    total_admin_fee = 0
    total_net_payable = 0

    for payout, user in results:

        referral_income = float(
            payout.referral_income or 0
        )

        level_income = float(
            payout.level_income or 0
        )

        rank_income = float(
            payout.rank_income or 0
        )

        total_payout_income = float(
            payout.total_income or 0
        )

        admin_fee = float(
            payout.admin_fee or 0
        )

        net_payable = float(
            payout.net_payable or 0
        )

        total_referral_income += referral_income
        total_level_income += level_income
        total_rank_income += rank_income
        total_income += total_payout_income
        total_admin_fee += admin_fee
        total_net_payable += net_payable

        user_name = (
            f"{user.first_name} "
            f"{user.last_name or ''}"
        ).strip()

        data.append({
            "id": payout.id,

            "user_id": user.user_id,

            "user_name": user_name,

            "referral_income": referral_income,

            "level_income": level_income,

            "rank_income": rank_income,

            "total_income": total_payout_income,

            "admin_fee_percentage": float(
                payout.admin_fee_percentage or 0
            ),

            "admin_fee": admin_fee,

            "net_payable": net_payable,

            "payout_method": payout.payout_method,

            "payout_information": payout.payout_information,

            "status": payout.status,

            "paid_at": payout.paid_at,

            "created_at": payout.created_at,
        })

    return {
        "total_records": len(data),

        "total_referral_income": total_referral_income,

        "total_level_income": total_level_income,

        "total_rank_income": total_rank_income,

        "total_income": total_income,

        "total_admin_fee": total_admin_fee,

        "total_net_payable": total_net_payable,

        "data": data,
    }


# ==========================================================
# PRINT PAYOUT REPORT
# ==========================================================

@router.get("/print", response_class=HTMLResponse)
def print_referral_income_report(
    request: Request,

    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: str | None = Query(None),
    user_id: str | None = Query(None),

    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):

    # ==================================================
    # QUERY
    # ==================================================

    query = (
        db.query(
            ReferralCommission,
            User
        )
        .join(
            User,
            ReferralCommission.enroller_id == User.id
        )
    )

    # ==================================================
    # FILTERS
    # ==================================================

    if start_date:
        query = query.filter(
            ReferralCommission.created_at >= start_date
        )

    if end_date:
        query = query.filter(
            ReferralCommission.created_at < end_date + timedelta(days=1)
        )

    if status:
        query = query.filter(
            ReferralCommission.status == status.upper()
        )

    if user_id:
        query = query.filter(
            User.user_id == user_id
        )

    # ==================================================
    # RESULTS
    # ==================================================

    results = (
        query
        .order_by(
            ReferralCommission.id.desc()
        )
        .all()
    )

    # ==================================================
    # REPORT DATA
    # ==================================================

    report_data = []

    total_investment_amount = Decimal("0")
    total_commission = Decimal("0")

    for commission, user in results:

        investment_amount = Decimal(
            str(commission.investment_amount or 0)
        )

        commission_amount = Decimal(
            str(commission.commission_amount or 0)
        )

        total_investment_amount += investment_amount
        total_commission += commission_amount

        user_name = (
            f"{user.first_name} {user.last_name or ''}"
        ).strip()

        report_data.append({

            "id": commission.id,

            "user_id": user.user_id,

            "user_name": user_name,

            "investment_id": commission.investment_id,

            "investment_amount": (
                commission.investment_amount
            ),

            "commission_percentage": (
                commission.commission_percentage
            ),

            "commission_amount": (
                commission.commission_amount
            ),

            "paid_amount": (
                commission.paid_amount
            ),

            "washout_amount": (
                commission.washout_amount
            ),

            "status": commission.status,

            "payment_date": (
                commission.payment_date
            ),

            "date": commission.created_at,
        })

    # ==================================================
    # SUMMARY
    # ==================================================

    summary = {
        "total_records": len(report_data),

        "total_investment_amount": float(
            total_investment_amount
        ),

        "total_commission": float(
            total_commission
        ),
    }

    # ==================================================
    # TEMPLATE
    # ==================================================

    return templates.TemplateResponse(
        request=request,

        name="reports/referral_income_report.html",

        context={
            "title": "Referral Income Report",

            "report_data": report_data,

            "summary": summary,

            "start_date": start_date,
            "end_date": end_date,
            "status": status,
            "user_id": user_id,

            "generated_at": datetime.now(),
        }
    )