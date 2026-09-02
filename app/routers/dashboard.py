from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.database import get_db
from app.dependencies import get_current_user

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
    prefix="/user/dashboard",
    tags=["User Dashboard"]
)


# ============================================================
# GET LOGGED-IN USER
# ============================================================

def get_user(
    current_user: str,
    db: Session
):
    user = (
        db.query(User)
        .filter(
            User.user_id == current_user
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


# ============================================================
# GET USER TOTAL ACTIVE INVESTMENT
# ============================================================

def get_user_total_investment(
    db: Session,
    user_id: int
):
    """
    Total approved investment amount.
    """

    total = (
        db.query(
            func.coalesce(
                func.sum(
                    Investment.amount
                ),
                0
            )
        )
        .filter(
            Investment.user_id == user_id,
            Investment.approval_status == "APPROVED"
        )
        .scalar()
    )

    return float(total or 0)


# ============================================================
# GET USER MAX INVESTMENT
# ============================================================

def get_user_max_investment(
    db: Session,
    user_id: int
):
    """
    Maximum approved investment amount.
    """

    max_amount = (
        db.query(
            func.coalesce(
                func.max(
                    Investment.amount
                ),
                0
            )
        )
        .filter(
            Investment.user_id == user_id,
            Investment.approval_status == "APPROVED"
        )
        .scalar()
    )

    return float(max_amount or 0)


# ============================================================
# GET USER TOTAL ACTIVE LOTS
# ============================================================

def get_user_total_lots(
    db: Session,
    user_id: int
):
    """
    Total lots from approved investments.
    """

    total_lots = (
        db.query(
            func.coalesce(
                func.sum(
                    Investment.lots
                ),
                0
            )
        )
        .filter(
            Investment.user_id == user_id,
            Investment.approval_status == "APPROVED"
        )
        .scalar()
    )

    return int(total_lots or 0)


# ============================================================
# GET ALL DESCENDANTS
# ============================================================

def get_all_level_users(
    db: Session,
    root_user_id: str
):
    """
    Get all users below logged-in user.

    User.enroller_id stores the sponsor's user_id.
    """

    all_users = (
        db.query(User)
        .filter(
            User.enroller_id.isnot(None)
        )
        .all()
    )

    # ========================================================
    # BUILD CHILDREN MAP
    # ========================================================

    children_map = {}

    for user in all_users:

        parent_id = user.enroller_id

        if parent_id not in children_map:
            children_map[parent_id] = []

        children_map[parent_id].append(
            user
        )

    # ========================================================
    # BFS LEVEL TRAVERSAL
    # ========================================================

    result = []

    queue = []

    # Direct referrals = Level 1

    for child in children_map.get(
        root_user_id,
        []
    ):

        queue.append(
            (child, 1)
        )

    while queue:

        user, level = queue.pop(0)

        result.append({
            "user": user,
            "level": level
        })

        children = children_map.get(
            user.user_id,
            []
        )

        for child in children:

            queue.append(
                (child, level + 1)
            )

    return result


# ============================================================
# FORMAT TEAM USER
# ============================================================

def format_team_user(
    db: Session,
    user: User,
    level: int
):
    """
    Format referral / level user.
    """

    max_investment = get_user_max_investment(
        db,
        user.id
    )

    total_investment = get_user_total_investment(
        db,
        user.id
    )

    total_lots = get_user_total_lots(
        db,
        user.id
    )

    return {

        "user_id": user.user_id,

        "user_name": (
            f"{user.first_name or ''} "
            f"{user.last_name or ''}"
        ).strip(),

        "profile_image": user.profile_image,

        "max_investment": max_investment,

        "total_investment": total_investment,

        "total_lots": total_lots,

        "level": level,

        "date_of_join": user.created_at,
    }


# ============================================================
# GET INCOME CHART
# ============================================================

def get_income_chart(
    db: Session,
    user_id: int
):
    """
    Get payout income chart for the last 6 months.

    Data:

        referral_income
        level_income
        rank_income
        total_income
        admin_fee
        net_payable

    PayoutHistory is grouped by year/month.
    """

    # ========================================================
    # QUERY LAST 6 MONTHS PAYOUT HISTORY
    # ========================================================

    rows = (
        db.query(
            extract(
                "year",
                PayoutHistory.paid_at
            ).label("year"),

            extract(
                "month",
                PayoutHistory.paid_at
            ).label("month"),

            func.coalesce(
                func.sum(
                    PayoutHistory.referral_income
                ),
                0
            ).label(
                "referral_income"
            ),

            func.coalesce(
                func.sum(
                    PayoutHistory.level_income
                ),
                0
            ).label(
                "level_income"
            ),

            func.coalesce(
                func.sum(
                    PayoutHistory.rank_income
                ),
                0
            ).label(
                "rank_income"
            ),

            func.coalesce(
                func.sum(
                    PayoutHistory.total_income
                ),
                0
            ).label(
                "total_income"
            ),

            func.coalesce(
                func.sum(
                    PayoutHistory.admin_fee
                ),
                0
            ).label(
                "admin_fee"
            ),

            func.coalesce(
                func.sum(
                    PayoutHistory.net_payable
                ),
                0
            ).label(
                "net_payable"
            ),
        )
        .filter(
            PayoutHistory.user_id == user_id,
            PayoutHistory.status == "PAID"
        )
        .group_by(
            extract(
                "year",
                PayoutHistory.paid_at
            ),
            extract(
                "month",
                PayoutHistory.paid_at
            )
        )
        .order_by(
            extract(
                "year",
                PayoutHistory.paid_at
            ).asc(),
            extract(
                "month",
                PayoutHistory.paid_at
            ).asc()
        )
        .all()
    )

    # ========================================================
    # CREATE LAST 6 MONTHS
    # ========================================================

    now = datetime.utcnow()

    months = []

    year = now.year
    month = now.month

    for _ in range(6):

        months.append(
            (
                year,
                month
            )
        )

        month -= 1

        if month == 0:
            month = 12
            year -= 1

    months.reverse()

    # ========================================================
    # MAP DATABASE RESULTS
    # ========================================================

    row_map = {}

    for row in rows:

        row_year = int(row.year)
        row_month = int(row.month)

        row_map[
            (row_year, row_month)
        ] = row

    # ========================================================
    # MONTH NAMES
    # ========================================================

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
    # BUILD CHART
    # ========================================================

    chart = []

    for year, month in months:

        row = row_map.get(
            (year, month)
        )

        if row:

            referral_income = float(
                row.referral_income or 0
            )

            level_income = float(
                row.level_income or 0
            )

            rank_income = float(
                row.rank_income or 0
            )

            total_income = float(
                row.total_income or 0
            )

            admin_fee = float(
                row.admin_fee or 0
            )

            net_payable = float(
                row.net_payable or 0
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

            "month_name": (
                month_names[month]
            ),

            "label": (
                f"{month_names[month]} {year}"
            ),

            "referral_income": (
                round(
                    referral_income,
                    2
                )
            ),

            "level_income": (
                round(
                    level_income,
                    2
                )
            ),

            "rank_income": (
                round(
                    rank_income,
                    2
                )
            ),

            "total_income": (
                round(
                    total_income,
                    2
                )
            ),

            "admin_fee": (
                round(
                    admin_fee,
                    2
                )
            ),

            "net_payable": (
                round(
                    net_payable,
                    2
                )
            ),
        })

    return chart


# ============================================================
# USER DASHBOARD
# ============================================================

@router.get("")
def user_dashboard(
    current_user: str = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    )
):
    """
    Logged-in user dashboard.
    """

    # ========================================================
    # GET LOGGED-IN USER
    # ========================================================

    user = get_user(
        current_user,
        db
    )

    # ========================================================
    # TOTAL ACTIVE INVESTMENT
    # ========================================================

    total_active_investment = (
        get_user_total_investment(
            db,
            user.id
        )
    )

    # ========================================================
    # TOTAL ACTIVE LOTS
    # ========================================================

    total_active_lots = (
        get_user_total_lots(
            db,
            user.id
        )
    )

    # ========================================================
    # WALLET
    # ========================================================

    wallet = (
        db.query(Wallet)
        .filter(
            Wallet.user_id == user.id
        )
        .first()
    )

    wallet_balance = 0.0

    if wallet:

        wallet_balance = float(
            wallet.balance or 0
        )

        pending_balance = float(
                    wallet.pending_balance or 0
        )

    # ========================================================
    # TOTAL PAYOUT AMOUNT
    # ========================================================

    payout_amount = (
        db.query(
            func.coalesce(
                func.sum(
                    PayoutHistory.net_payable
                ),
                0
            )
        )
        .filter(
            PayoutHistory.user_id == user.id,
            PayoutHistory.status == "PAID"
        )
        .scalar()
    )

    payout_amount = float(
        payout_amount or 0
    )

    # ========================================================
    # DIRECT REFERRALS
    # ========================================================

    direct_referrals = (
        db.query(User)
        .filter(
            User.enroller_id == user.user_id
        )
        .all()
    )

    total_referrals = len(
        direct_referrals
    )

    # ========================================================
    # ALL LEVEL USERS
    # ========================================================

    level_users = get_all_level_users(
        db,
        user.user_id
    )

    total_level_users = len(
        level_users
    )

    # ========================================================
    # CURRENT RANK NAME
    # ========================================================

    current_rank_name = None

    if user.current_rank:

        current_rank_name = (
            user.current_rank.rank_name
        )

    # ========================================================
    # NEXT RANK NAME
    # ========================================================

    next_rank_name = None

    if user.current_rank:

        next_rank = (
            db.query(RankSetting)
            .filter(
                RankSetting.status == True,
                RankSetting.rank_no
                > user.current_rank.rank_no
            )
            .order_by(
                RankSetting.rank_no.asc()
            )
            .first()
        )

    else:

        next_rank = (
            db.query(RankSetting)
            .filter(
                RankSetting.status == True
            )
            .order_by(
                RankSetting.rank_no.asc()
            )
            .first()
        )

    if next_rank:

        next_rank_name = (
            next_rank.rank_name
        )

    # ========================================================
    # TOP 5 DIRECT REFERRALS
    # ========================================================

    referral_list = []

    for referral in direct_referrals:

        referral_data = format_team_user(
            db,
            referral,
            level=1
        )

        referral_list.append(
            referral_data
        )

    referral_list.sort(
        key=lambda item: item[
            "max_investment"
        ],
        reverse=True
    )

    top_5_referrals = (
        referral_list[:5]
    )

    # ========================================================
    # TOP 5 LEVEL USERS
    # ========================================================

    level_list = []

    for item in level_users:

        level_user = item["user"]

        level = item["level"]

        level_data = format_team_user(
            db,
            level_user,
            level
        )

        level_list.append(
            level_data
        )

    level_list.sort(
        key=lambda item: item[
            "max_investment"
        ],
        reverse=True
    )

    top_5_level_users = (
        level_list[:5]
    )

    # ========================================================
    # INCOME CHART
    # ========================================================

    income_chart = get_income_chart(
        db,
        user.id
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        # ====================================================
        # USER
        # ====================================================

        "user": {

            "user_id": user.user_id,

            "user_name": (
                f"{user.first_name or ''} "
                f"{user.last_name or ''}"
            ).strip(),

            "profile_image": (
                user.profile_image
            ),
        },

        # ====================================================
        # DASHBOARD SUMMARY
        # ====================================================

        "summary": {

            "total_active_investment": (
                total_active_investment
            ),

            "total_active_lots": (
                total_active_lots
            ),

            "wallet_balance": (
                wallet_balance
            ),
            
             "pending_balance": (
                pending_balance
            ),
            
            "payout_amount": (
                payout_amount
            ),

            "total_referrals": (
                total_referrals
            ),

            "total_level_users": (
                total_level_users
            ),
        },

        # ====================================================
        # RANK
        # ====================================================

        "rank": {

            "current_rank": (
                current_rank_name
            ),

            "next_rank": (
                next_rank_name
            ),
        },

        # ====================================================
        # INCOME CHART
        # ====================================================

        "income_chart": income_chart,

        # ====================================================
        # TOP 5 DIRECT REFERRALS
        # ====================================================

        "top_referrals": (
            top_5_referrals
        ),

        # ====================================================
        # TOP 5 LEVEL USERS
        # ====================================================

        "top_level_users": (
            top_5_level_users
        ),
    }