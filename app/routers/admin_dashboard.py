# app/routers/admin_dashboard.py

from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin

from app.models import (
    User,
    Wallet,
    Investment,
    PayoutHistory,
    RankSetting,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/admin/dashboard",
    tags=["Admin Dashboard"],
)


# ============================================================
# HELPERS
# ============================================================

def decimal_to_float(value):
    if value is None:
        return 0.0

    if isinstance(value, Decimal):
        return float(value)

    return float(value)


def build_date_filter(
    column,
    start_date: date | None,
    end_date: date | None,
):
    """
    Build SQLAlchemy date filters.

    start_date:
        >= start_date 00:00:00

    end_date:
        < next day 00:00:00
    """

    filters = []

    if start_date:
        filters.append(
            column >= datetime.combine(
                start_date,
                datetime.min.time(),
            )
        )

    if end_date:
        next_day = end_date + timedelta(days=1)

        filters.append(
            column < datetime.combine(
                next_day,
                datetime.min.time(),
            )
        )

    return filters


# ============================================================
# SUMMARY
# ============================================================

def get_dashboard_summary(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
):
    """
    Get overall admin dashboard statistics.
    """

    # ========================================================
    # TOTAL USERS
    # ========================================================

    total_users = (
        db.query(
            func.count(User.id)
        )
        .scalar()
        or 0
    )

    # ========================================================
    # ACTIVE USERS
    # ========================================================
    #
    # A user is considered active if they have at least one
    # approved investment.
    #
    # This avoids depending on a particular User.status value.
    # ========================================================

    active_users = (
        db.query(
            func.count(
                func.distinct(
                    Investment.user_id
                )
            )
        )
        .filter(
            Investment.approval_status == "APPROVED"
        )
    )

    investment_date_filters = build_date_filter(
        Investment.created_at,
        start_date,
        end_date,
    )

    if investment_date_filters:
        active_users = active_users.filter(
            *investment_date_filters
        )

    active_users = (
        active_users
        .scalar()
        or 0
    )

    # ========================================================
    # TOTAL ACTIVE INVESTMENT
    # ========================================================

    total_active_investment_query = (
        db.query(
            func.coalesce(
                func.sum(
                    Investment.amount
                ),
                0,
            )
        )
        .filter(
            Investment.approval_status == "APPROVED"
        )
    )

    if investment_date_filters:
        total_active_investment_query = (
            total_active_investment_query.filter(
                *investment_date_filters
            )
        )

    total_active_investment = (
        total_active_investment_query
        .scalar()
        or 0
    )

    # ========================================================
    # TOTAL ACTIVE LOTS
    # ========================================================

    total_active_lots_query = (
        db.query(
            func.coalesce(
                func.sum(
                    Investment.lots
                ),
                0,
            )
        )
        .filter(
            Investment.approval_status == "APPROVED"
        )
    )

    if investment_date_filters:
        total_active_lots_query = (
            total_active_lots_query.filter(
                *investment_date_filters
            )
        )

    total_active_lots = (
        total_active_lots_query
        .scalar()
        or 0
    )

    # ========================================================
    # TOTAL WALLET BALANCE
    # ========================================================

    total_wallet_balance = (
        db.query(
            func.coalesce(
                func.sum(
                    Wallet.balance
                ),
                0,
            )
        )
        .scalar()
        or 0
    )

    # ========================================================
    # TOTAL PENDING BALANCE
    # ========================================================

    total_pending_balance = (
        db.query(
            func.coalesce(
                func.sum(
                    Wallet.pending_balance
                ),
                0,
            )
        )
        .scalar()
        or 0
    )

    # ========================================================
    # PAYOUT QUERY
    # ========================================================

    payout_query = (
        db.query(
            func.coalesce(
                func.sum(
                    PayoutHistory.net_payable
                ),
                0,
            ).label("net_payable"),

            func.coalesce(
                func.sum(
                    PayoutHistory.total_income
                ),
                0,
            ).label("total_income"),

            func.coalesce(
                func.sum(
                    PayoutHistory.referral_income
                ),
                0,
            ).label("referral_income"),

            func.coalesce(
                func.sum(
                    PayoutHistory.level_income
                ),
                0,
            ).label("level_income"),

            func.coalesce(
                func.sum(
                    PayoutHistory.rank_income
                ),
                0,
            ).label("rank_income"),

            func.coalesce(
                func.sum(
                    PayoutHistory.admin_fee
                ),
                0,
            ).label("admin_fee"),
        )
        .filter(
            PayoutHistory.status == "PAID"
        )
    )

    payout_date_filters = build_date_filter(
        PayoutHistory.paid_at,
        start_date,
        end_date,
    )

    if payout_date_filters:
        payout_query = payout_query.filter(
            *payout_date_filters
        )

    payout = payout_query.first()

    if payout:

        total_payout = decimal_to_float(
            payout.net_payable
        )

        total_income = decimal_to_float(
            payout.total_income
        )

        referral_income = decimal_to_float(
            payout.referral_income
        )

        level_income = decimal_to_float(
            payout.level_income
        )

        rank_income = decimal_to_float(
            payout.rank_income
        )

        admin_fee = decimal_to_float(
            payout.admin_fee
        )

    else:

        total_payout = 0.0
        total_income = 0.0
        referral_income = 0.0
        level_income = 0.0
        rank_income = 0.0
        admin_fee = 0.0

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "total_users": int(
            total_users
        ),

        "active_users": int(
            active_users
        ),

        "total_active_investment": round(
            decimal_to_float(
                total_active_investment
            ),
            2,
        ),

        "total_active_lots": int(
            total_active_lots
        ),

        "total_wallet_balance": round(
            decimal_to_float(
                total_wallet_balance
            ),
            2,
        ),

        "total_pending_balance": round(
            decimal_to_float(
                total_pending_balance
            ),
            2,
        ),

        "total_payout": round(
            total_payout,
            2,
        ),

        "total_income": round(
            total_income,
            2,
        ),

        "total_referral_income": round(
            referral_income,
            2,
        ),

        "total_level_income": round(
            level_income,
            2,
        ),

        "total_rank_income": round(
            rank_income,
            2,
        ),

        "total_admin_fee": round(
            admin_fee,
            2,
        ),
    }


# ============================================================
# CURRENT MONTH SUMMARY
# ============================================================

def get_current_month_summary(
    db: Session,
):
    """
    Current calendar month payout statistics.
    """

    now = datetime.utcnow()

    month_start = datetime(
        now.year,
        now.month,
        1,
    )

    if now.month == 12:

        next_month = datetime(
            now.year + 1,
            1,
            1,
        )

    else:

        next_month = datetime(
            now.year,
            now.month + 1,
            1,
        )

    # ========================================================
    # INVESTMENT
    # ========================================================

    investment = (
        db.query(
            func.coalesce(
                func.sum(
                    Investment.amount
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    Investment.lots
                ),
                0,
            ),
        )
        .filter(
            Investment.approval_status == "APPROVED",
            Investment.created_at >= month_start,
            Investment.created_at < next_month,
        )
        .first()
    )

    month_investment = (
        decimal_to_float(
            investment[0]
        )
        if investment
        else 0.0
    )

    month_lots = (
        int(
            investment[1] or 0
        )
        if investment
        else 0
    )

    # ========================================================
    # PAYOUT
    # ========================================================

    payout = (
        db.query(
            func.coalesce(
                func.sum(
                    PayoutHistory.total_income
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    PayoutHistory.referral_income
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    PayoutHistory.level_income
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    PayoutHistory.rank_income
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    PayoutHistory.admin_fee
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    PayoutHistory.net_payable
                ),
                0,
            ),
        )
        .filter(
            PayoutHistory.status == "PAID",
            PayoutHistory.paid_at >= month_start,
            PayoutHistory.paid_at < next_month,
        )
        .first()
    )

    if payout:

        return {

            "investment": round(
                month_investment,
                2,
            ),

            "lots": month_lots,

            "total_income": round(
                decimal_to_float(
                    payout[0]
                ),
                2,
            ),

            "referral_income": round(
                decimal_to_float(
                    payout[1]
                ),
                2,
            ),

            "level_income": round(
                decimal_to_float(
                    payout[2]
                ),
                2,
            ),

            "rank_income": round(
                decimal_to_float(
                    payout[3]
                ),
                2,
            ),

            "admin_fee": round(
                decimal_to_float(
                    payout[4]
                ),
                2,
            ),

            "net_payable": round(
                decimal_to_float(
                    payout[5]
                ),
                2,
            ),
        }

    return {

        "investment": round(
            month_investment,
            2,
        ),

        "lots": month_lots,

        "total_income": 0.0,
        "referral_income": 0.0,
        "level_income": 0.0,
        "rank_income": 0.0,
        "admin_fee": 0.0,
        "net_payable": 0.0,
    }


# ============================================================
# INCOME CHART
# ============================================================

def get_income_chart(
    db: Session,
):
    """
    Last 6 months payout income chart.
    """

    now = datetime.utcnow()

    # ========================================================
    # CREATE MONTH LIST
    # ========================================================

    months = []

    year = now.year
    month = now.month

    for _ in range(6):

        months.append(
            (
                year,
                month,
            )
        )

        month -= 1

        if month == 0:

            month = 12
            year -= 1

    months.reverse()

    # ========================================================
    # QUERY
    # ========================================================

    rows = (
        db.query(

            extract(
                "year",
                PayoutHistory.paid_at,
            ).label("year"),

            extract(
                "month",
                PayoutHistory.paid_at,
            ).label("month"),

            func.coalesce(
                func.sum(
                    PayoutHistory.referral_income
                ),
                0,
            ).label(
                "referral_income"
            ),

            func.coalesce(
                func.sum(
                    PayoutHistory.level_income
                ),
                0,
            ).label(
                "level_income"
            ),

            func.coalesce(
                func.sum(
                    PayoutHistory.rank_income
                ),
                0,
            ).label(
                "rank_income"
            ),

            func.coalesce(
                func.sum(
                    PayoutHistory.total_income
                ),
                0,
            ).label(
                "total_income"
            ),

            func.coalesce(
                func.sum(
                    PayoutHistory.admin_fee
                ),
                0,
            ).label(
                "admin_fee"
            ),

            func.coalesce(
                func.sum(
                    PayoutHistory.net_payable
                ),
                0,
            ).label(
                "net_payable"
            ),
        )
        .filter(
            PayoutHistory.status == "PAID"
        )
        .group_by(

            extract(
                "year",
                PayoutHistory.paid_at,
            ),

            extract(
                "month",
                PayoutHistory.paid_at,
            ),
        )
        .order_by(

            extract(
                "year",
                PayoutHistory.paid_at,
            ).asc(),

            extract(
                "month",
                PayoutHistory.paid_at,
            ).asc(),
        )
        .all()
    )

    # ========================================================
    # MAP
    # ========================================================

    row_map = {}

    for row in rows:

        key = (
            int(row.year),
            int(row.month),
        )

        row_map[key] = row

    month_names = [
        "",
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    # ========================================================
    # BUILD
    # ========================================================

    chart = []

    for year, month in months:

        row = row_map.get(
            (
                year,
                month,
            )
        )

        if row:

            referral_income = decimal_to_float(
                row.referral_income
            )

            level_income = decimal_to_float(
                row.level_income
            )

            rank_income = decimal_to_float(
                row.rank_income
            )

            total_income = decimal_to_float(
                row.total_income
            )

            admin_fee = decimal_to_float(
                row.admin_fee
            )

            net_payable = decimal_to_float(
                row.net_payable
            )

        else:

            referral_income = 0.0
            level_income = 0.0
            rank_income = 0.0
            total_income = 0.0
            admin_fee = 0.0
            net_payable = 0.0

        chart.append({

            "year": year,

            "month": month,

            "month_name": month_names[
                month
            ],

            "label": (
                f"{month_names[month]} {year}"
            ),

            "referral_income": round(
                referral_income,
                2,
            ),

            "level_income": round(
                level_income,
                2,
            ),

            "rank_income": round(
                rank_income,
                2,
            ),

            "total_income": round(
                total_income,
                2,
            ),

            "admin_fee": round(
                admin_fee,
                2,
            ),

            "net_payable": round(
                net_payable,
                2,
            ),
        })

    return chart


# ============================================================
# RANK DISTRIBUTION
# ============================================================

def get_rank_distribution(
    db: Session,
):
    """
    Number of users in each rank.
    """

    rows = (
        db.query(

            RankSetting.rank_no,

            RankSetting.rank_name,

            func.count(
                User.id
            ).label(
                "user_count"
            ),
        )
        .outerjoin(
            User,
            User.current_rank_id
            == RankSetting.id,
        )
        .filter(
            RankSetting.status == True
        )
        .group_by(

            RankSetting.id,

            RankSetting.rank_no,

            RankSetting.rank_name,
        )
        .order_by(
            RankSetting.rank_no.asc()
        )
        .all()
    )

    result = []

    for row in rows:

        result.append({

            "rank_no": int(
                row.rank_no
            ),

            "rank_name": row.rank_name,

            "user_count": int(
                row.user_count or 0
            ),
        })

    return result


# ============================================================
# TOP USERS
# ============================================================

def get_top_users(
    db: Session,
    limit: int = 5,
):
    """
    Top users based on total approved investment.
    """

    rows = (
        db.query(

            User.id,

            User.user_id,

            User.first_name,

            User.last_name,

            User.profile_image,

            User.current_rank_id,

            func.coalesce(
                func.sum(
                    Investment.amount
                ),
                0,
            ).label(
                "total_investment"
            ),

            func.coalesce(
                func.sum(
                    Investment.lots
                ),
                0,
            ).label(
                "total_lots"
            ),

            func.max(
                Investment.amount
            ).label(
                "max_investment"
            ),
        )
        .outerjoin(
            Investment,
            (
                Investment.user_id == User.id
            )
            & (
                Investment.approval_status
                == "APPROVED"
            ),
        )
        .group_by(

            User.id,

            User.user_id,

            User.first_name,

            User.last_name,

            User.profile_image,

            User.current_rank_id,
        )
        .order_by(
            func.coalesce(
                func.sum(
                    Investment.amount
                ),
                0,
            ).desc()
        )
        .limit(limit)
        .all()
    )

    result = []

    for row in rows:

        rank_name = None

        if row.current_rank_id:

            rank = (
                db.query(RankSetting)
                .filter(
                    RankSetting.id
                    == row.current_rank_id
                )
                .first()
            )

            if rank:
                rank_name = rank.rank_name

        result.append({

            "user_id": row.user_id,

            "user_name": (
                f"{row.first_name or ''} "
                f"{row.last_name or ''}"
            ).strip(),

            "profile_image": row.profile_image,

            "rank": rank_name,

            "total_investment": round(
                decimal_to_float(
                    row.total_investment
                ),
                2,
            ),

            "max_investment": round(
                decimal_to_float(
                    row.max_investment
                ),
                2,
            ),

            "total_lots": int(
                row.total_lots or 0
            ),
        })

    return result


# ============================================================
# RECENT INVESTMENTS
# ============================================================

def get_recent_investments(
    db: Session,
    limit: int = 10,
):
    """
    Latest investments.
    """

    rows = (
        db.query(

            Investment,

            User.user_id.label(
                "member_user_id"
            ),

            User.first_name,

            User.last_name,
        )
        .join(
            User,
            User.id == Investment.user_id,
        )
        .order_by(
            Investment.created_at.desc()
        )
        .limit(limit)
        .all()
    )

    result = []

    for investment, user_id, first_name, last_name in rows:

        result.append({

            "investment_id": getattr(
                investment,
                "investment_id",
                investment.id,
            ),

            "user_id": user_id,

            "user_name": (
                f"{first_name or ''} "
                f"{last_name or ''}"
            ).strip(),

            "amount": round(
                decimal_to_float(
                    investment.amount
                ),
                2,
            ),

            "lots": int(
                investment.lots or 0
            ),

            "approval_status": (
                investment.approval_status
            ),

            "created_at": (
                investment.created_at
            ),
        })

    return result


# ============================================================
# RECENT PAYOUTS
# ============================================================

def get_recent_payouts(
    db: Session,
    limit: int = 10,
):
    """
    Latest paid payouts.
    """

    rows = (
        db.query(

            PayoutHistory,

            User.user_id.label(
                "member_user_id"
            ),

            User.first_name,

            User.last_name,
        )
        .join(
            User,
            User.id == PayoutHistory.user_id,
        )
        .filter(
            PayoutHistory.status == "PAID"
        )
        .order_by(
            PayoutHistory.paid_at.desc()
        )
        .limit(limit)
        .all()
    )

    result = []

    for payout, user_id, first_name, last_name in rows:

        result.append({

            "user_id": user_id,

            "user_name": (
                f"{first_name or ''} "
                f"{last_name or ''}"
            ).strip(),

            "referral_income": round(
                decimal_to_float(
                    payout.referral_income
                ),
                2,
            ),

            "level_income": round(
                decimal_to_float(
                    payout.level_income
                ),
                2,
            ),

            "rank_income": round(
                decimal_to_float(
                    payout.rank_income
                ),
                2,
            ),

            "total_income": round(
                decimal_to_float(
                    payout.total_income
                ),
                2,
            ),

            "admin_fee": round(
                decimal_to_float(
                    payout.admin_fee
                ),
                2,
            ),

            "net_payable": round(
                decimal_to_float(
                    payout.net_payable
                ),
                2,
            ),

            "paid_at": (
                payout.paid_at
            ),

            "status": (
                payout.status
            ),
        })

    return result


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@router.get("")
def admin_dashboard(

    start_date: date | None = Query(
        None,
        description="Filter start date",
    ),

    end_date: date | None = Query(
        None,
        description="Filter end date",
    ),

    current_admin=Depends(
        get_current_admin
    ),

    db: Session = Depends(
        get_db
    ),
):
    """
    Admin dashboard.

    Optional filters:

        ?start_date=2026-08-01
        &end_date=2026-08-22
    """

    # ========================================================
    # SUMMARY
    # ========================================================

    summary = get_dashboard_summary(
        db,
        start_date,
        end_date,
    )

    # ========================================================
    # CURRENT MONTH
    # ========================================================

    current_month = (
        get_current_month_summary(
            db
        )
    )

    # ========================================================
    # INCOME CHART
    # ========================================================

    income_chart = (
        get_income_chart(
            db
        )
    )

    # ========================================================
    # RANK DISTRIBUTION
    # ========================================================

    rank_distribution = (
        get_rank_distribution(
            db
        )
    )

    # ========================================================
    # TOP USERS
    # ========================================================

    top_users = (
        get_top_users(
            db,
            limit=5,
        )
    )

    # ========================================================
    # RECENT INVESTMENTS
    # ========================================================

    recent_investments = (
        get_recent_investments(
            db,
            limit=10,
        )
    )

    # ========================================================
    # RECENT PAYOUTS
    # ========================================================

    recent_payouts = (
        get_recent_payouts(
            db,
            limit=10,
        )
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        # ====================================================
        # FILTER
        # ====================================================

        "filter": {

            "start_date": start_date,

            "end_date": end_date,
        },

        # ====================================================
        # SUMMARY
        # ====================================================

        "summary": summary,

        # ====================================================
        # CURRENT MONTH
        # ====================================================

        "current_month": current_month,

        # ====================================================
        # INCOME CHART
        # ====================================================

        "income_chart": income_chart,

        # ====================================================
        # RANK DISTRIBUTION
        # ====================================================

        "rank_distribution": (
            rank_distribution
        ),

        # ====================================================
        # TOP USERS
        # ====================================================

        "top_users": top_users,

        # ====================================================
        # RECENT INVESTMENTS
        # ====================================================

        "recent_investments": (
            recent_investments
        ),

        # ====================================================
        # RECENT PAYOUTS
        # ====================================================

        "recent_payouts": (
            recent_payouts
        ),
    }