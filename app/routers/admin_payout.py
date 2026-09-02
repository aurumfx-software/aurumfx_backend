from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_admin
from fastapi.responses import HTMLResponse
from html import escape


from app.models import (
    User,
    Wallet,
    WalletTransaction,
    Investment,
    InvestmentPlan,
    AdminFeeSetting,
    ReferralCommission,
    LevelCommissionHistory,
    UserRankHistory,
    PayoutHistory,
)
from app.schemas import BulkPayoutRequest

router = APIRouter(
    prefix="/admin/payout",
    tags=["Admin Payout"]
)


# ============================================================
# DECIMAL HELPER
# ============================================================

def money(value):
    """
    Convert value to Decimal with 2 decimal places.
    """

    return Decimal(
        str(value or 0)
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


# ============================================================
# GET CURRENT ADMIN FEE
# ============================================================

def get_admin_fee_percentage(
    db: Session
) -> Decimal:
    """
    Get the latest active admin fee percentage.
    """

    fee_setting = (
        db.query(AdminFeeSetting)
        .filter(
            AdminFeeSetting.status == True
        )
        .order_by(
            AdminFeeSetting.id.desc()
        )
        .first()
    )

    if not fee_setting:
        return Decimal("0.00")

    return money(
        fee_setting.fee_percentage
    )


# ============================================================
# GET USER WALLET
# ============================================================

def get_user_wallet(
    db: Session,
    user_id: int,
    create: bool = False
):
    """
    Get user's wallet.

    If create=True and wallet doesn't exist,
    create it.

    Wallet is locked using FOR UPDATE.
    """

    wallet = (
        db.query(Wallet)
        .filter(
            Wallet.user_id == user_id
        )
        .with_for_update()
        .first()
    )

    if not wallet and create:

        wallet = Wallet(
            user_id=user_id,
            balance=0,
            pending_balance=0,
            admin_fee=0
        )

        db.add(wallet)
        db.flush()

    return wallet


# ============================================================
# GET USER LONGEST APPROVED INVESTMENT
# ============================================================

def get_longest_investment(
    db: Session,
    user_id: int
):
    """
    Get user's approved investment
    with the longest duration plan.
    """

    return (
        db.query(Investment)
        .join(
            InvestmentPlan,
            Investment.investment_plan_id
            == InvestmentPlan.id
        )
        .options(
            joinedload(
                Investment.investment_plan
            )
        )
        .filter(
            Investment.user_id == user_id,
            Investment.approval_status == "APPROVED"
        )
        .order_by(
            InvestmentPlan.duration_months.desc()
        )
        .first()
    )


# ============================================================
# GET PENDING REFERRAL
# ============================================================

def get_pending_referral(
    db: Session,
    user_id: int
):
    """
    Get and lock pending referral commissions.
    """

    return (
        db.query(ReferralCommission)
        .filter(
            ReferralCommission.enroller_id == user_id,
            ReferralCommission.status == "PENDING"
        )
        .with_for_update()
        .all()
    )


# ============================================================
# GET PENDING LEVEL
# ============================================================

def get_pending_level(
    db: Session,
    user_id: int
):
    """
    Get and lock pending level commissions.
    """

    return (
        db.query(LevelCommissionHistory)
        .filter(
            LevelCommissionHistory.sponsor_id == user_id,
            LevelCommissionHistory.status == "PENDING"
        )
        .with_for_update()
        .all()
    )


# ============================================================
# GET PENDING RANK
# ============================================================

def get_pending_rank(
    db: Session,
    user_id: int
):
    """
    Get and lock unpaid rank rewards.
    """

    return (
        db.query(UserRankHistory)
        .filter(
            UserRankHistory.user_id == user_id,
            UserRankHistory.reward_paid == False
        )
        .with_for_update()
        .all()
    )


# ============================================================
# GET BANK DETAILS
# ============================================================

def get_bank_details(
    user: User
):
    """
    Safely get user's bank details.

    Bank details are now stored in
    UserBankDetails, not directly in User.
    """

    bank = user.bank_details

    if not bank:
        return {
            "bank_account": None,
            "bank_name": None,
            "ifsc": None,
            "bank_proof": None,
            "status": None,
            "rejection_reason": None,
        }

    return {
        "bank_account": bank.bank_account,
        "bank_name": bank.bank_name,
        "ifsc": bank.ifsc,
        "bank_proof": bank.bank_proof,
        "status": bank.bank_status,
        "rejection_reason": bank.bank_rejection_reason,
    }


# ============================================================
# USER NAME
# ============================================================

def get_user_name(
    user: User
):
    return (
        f"{user.first_name or ''} "
        f"{user.last_name or ''}"
    ).strip()


# ============================================================
# GET PENDING PAYOUTS
# ============================================================

@router.get("/pending")
def get_pending_payouts(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    Get pending income for all users.

    Income:

        Referral
        Level
        Rank

    Admin fee:

        Calculated from total income.

    Bank details:

        Loaded from UserBankDetails.
    """

    # ========================================================
    # ADMIN FEE
    # ========================================================

    admin_fee_percentage = (
        get_admin_fee_percentage(db)
    )

    # ========================================================
    # USERS
    # ========================================================

    users = (
        db.query(User)
        .options(
            joinedload(
                User.bank_details
            )
        )
        .all()
    )

    result = []

    for user in users:

        # ====================================================
        # REFERRAL INCOME
        # ====================================================

        referral_pending = (
            db.query(
                func.coalesce(
                    func.sum(
                        ReferralCommission.commission_amount
                    ),
                    0
                )
            )
            .filter(
                ReferralCommission.enroller_id == user.id,
                ReferralCommission.status == "PENDING"
            )
            .scalar()
            or 0
        )

        # ====================================================
        # LEVEL INCOME
        # ====================================================

        level_pending = (
            db.query(
                func.coalesce(
                    func.sum(
                        LevelCommissionHistory.commission_amount
                    ),
                    0
                )
            )
            .filter(
                LevelCommissionHistory.sponsor_id == user.id,
                LevelCommissionHistory.status == "PENDING"
            )
            .scalar()
            or 0
        )

        # ====================================================
        # RANK INCOME
        # ====================================================

        rank_pending = (
            db.query(
                func.coalesce(
                    func.sum(
                        UserRankHistory.reward_income
                    ),
                    0
                )
            )
            .filter(
                UserRankHistory.user_id == user.id,
                UserRankHistory.reward_paid == False
            )
            .scalar()
            or 0
        )

        # ====================================================
        # DECIMAL CONVERSION
        # ====================================================

        referral_pending = money(
            referral_pending
        )

        level_pending = money(
            level_pending
        )

        rank_pending = money(
            rank_pending
        )

        # ====================================================
        # TOTAL INCOME
        # ====================================================

        total_income = money(
            referral_pending
            + level_pending
            + rank_pending
        )

        # No pending income
        if total_income <= 0:
            continue

        # ====================================================
        # WALLET
        # ====================================================

        wallet = (
            db.query(Wallet)
            .filter(
                Wallet.user_id == user.id
            )
            .first()
        )

        wallet_pending = Decimal("0.00")

        if wallet:
            wallet_pending = money(
                wallet.pending_balance
            )

        # ====================================================
        # ADMIN FEE
        # ====================================================

        admin_fee = money(
            total_income
            * admin_fee_percentage
            / Decimal("100")
        )

        # ====================================================
        # NET PAYABLE
        # ====================================================

        net_payable = money(
            total_income
            - admin_fee
        )

        # ====================================================
        # INVESTMENT PLAN
        # ====================================================

        investment = get_longest_investment(
            db,
            user.id
        )

        plan_name = None
        duration_months = None

        if investment:

            plan = investment.investment_plan

            if plan:

                plan_name = plan.plan_name

                duration_months = (
                    plan.duration_months
                )

        # ====================================================
        # BANK DETAILS
        # ====================================================

        bank_details = get_bank_details(
            user
        )

        # ====================================================
        # RESULT
        # ====================================================

        result.append({

            "user_id": user.id,

            "user_code": user.user_id,

            "user_name": get_user_name(
                user
            ),

            # ----------------------------------------------
            # Income
            # ----------------------------------------------

            "referral_income": float(
                referral_pending
            ),

            "level_income": float(
                level_pending
            ),

            "rank_income": float(
                rank_pending
            ),

            "user_balance": float(
                total_income
            ),

            # ----------------------------------------------
            # Wallet
            # ----------------------------------------------

            "wallet_pending_balance": float(
                wallet_pending
            ),

            # ----------------------------------------------
            # Investment
            # ----------------------------------------------

            "investment_plan": plan_name,

            "duration_months": duration_months,

            # ----------------------------------------------
            # Admin Fee
            # ----------------------------------------------

            "admin_fee_percentage": float(
                admin_fee_percentage
            ),

            "admin_fee": float(
                admin_fee
            ),

            # ----------------------------------------------
            # Net Payable
            # ----------------------------------------------

            "net_payable": float(
                net_payable
            ),

            # ----------------------------------------------
            # Bank Details
            # ----------------------------------------------

            "bank_details": bank_details,

            # ----------------------------------------------
            # Status
            # ----------------------------------------------

            "status": "PENDING"
        })

    return {
        "total": len(result),
        "items": result
    }
# ============================================================
# PRINT PENDING PAYOUTS - A4
# ============================================================



@router.get(
    "/pending/print",
    response_class=HTMLResponse
)
def print_pending_payouts(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    A4 printable report for all pending payouts.
    """

    # ========================================================
    # ADMIN FEE
    # ========================================================

    admin_fee_percentage = get_admin_fee_percentage(db)

    # ========================================================
    # USERS
    # ========================================================

    users = (
        db.query(User)
        .options(
            joinedload(
                User.bank_details
            )
        )
        .order_by(
            User.created_at.desc()
        )
        .all()
    )

    rows = ""

    # ========================================================
    # TOTALS
    # ========================================================

    total_referral = Decimal("0.00")
    total_level = Decimal("0.00")
    total_rank = Decimal("0.00")
    total_income = Decimal("0.00")
    total_admin_fee = Decimal("0.00")
    total_net_payable = Decimal("0.00")

    serial_no = 1

    # ========================================================
    # LOOP USERS
    # ========================================================

    for user in users:

        # ====================================================
        # REFERRAL
        # ====================================================

        referral_pending = (
            db.query(
                func.coalesce(
                    func.sum(
                        ReferralCommission.commission_amount
                    ),
                    0
                )
            )
            .filter(
                ReferralCommission.enroller_id == user.id,
                ReferralCommission.status == "PENDING"
            )
            .scalar()
            or 0
        )

        # ====================================================
        # LEVEL
        # ====================================================

        level_pending = (
            db.query(
                func.coalesce(
                    func.sum(
                        LevelCommissionHistory.commission_amount
                    ),
                    0
                )
            )
            .filter(
                LevelCommissionHistory.sponsor_id == user.id,
                LevelCommissionHistory.status == "PENDING"
            )
            .scalar()
            or 0
        )

        # ====================================================
        # RANK
        # ====================================================

        rank_pending = (
            db.query(
                func.coalesce(
                    func.sum(
                        UserRankHistory.reward_income
                    ),
                    0
                )
            )
            .filter(
                UserRankHistory.user_id == user.id,
                UserRankHistory.reward_paid == False
            )
            .scalar()
            or 0
        )

        # ====================================================
        # DECIMAL
        # ====================================================

        referral_pending = money(
            referral_pending
        )

        level_pending = money(
            level_pending
        )

        rank_pending = money(
            rank_pending
        )

        # ====================================================
        # TOTAL INCOME
        # ====================================================

        total_user_income = money(
            referral_pending
            + level_pending
            + rank_pending
        )

        # No pending income
        if total_user_income <= 0:
            continue

        # ====================================================
        # ADMIN FEE
        # ====================================================

        admin_fee = money(
            total_user_income
            * admin_fee_percentage
            / Decimal("100")
        )

        # ====================================================
        # NET PAYABLE
        # ====================================================

        net_payable = money(
            total_user_income
            - admin_fee
        )

        # ====================================================
        # USER NAME
        # ====================================================

        user_name = get_user_name(user)

        # ====================================================
        # BANK DETAILS
        # ====================================================

        bank = user.bank_details

        bank_account = ""
        bank_name = ""
        ifsc = ""
        bank_status = ""

        if bank:

            bank_account = (
                bank.bank_account or ""
            )

            bank_name = (
                bank.bank_name or ""
            )

            ifsc = (
                bank.ifsc or ""
            )

            bank_status = (
                bank.bank_status or ""
            )

        # ====================================================
        # ESCAPE HTML
        # ====================================================

        user_code = escape(
            str(user.user_id or "")
        )

        user_name = escape(
            str(user_name)
        )

        bank_account = escape(
            str(bank_account)
        )

        bank_name = escape(
            str(bank_name)
        )

        ifsc = escape(
            str(ifsc)
        )

        bank_status = escape(
            str(bank_status)
        )

        # ====================================================
        # TABLE ROW
        # ====================================================

        rows += f"""
        <tr>

            <td class="center">
                {serial_no}
            </td>

            <td>
                {user_code}
            </td>

            <td>
                {user_name}
            </td>

            <td class="amount">
                ₹ {referral_pending:,.2f}
            </td>

            <td class="amount">
                ₹ {level_pending:,.2f}
            </td>

            <td class="amount">
                ₹ {rank_pending:,.2f}
            </td>

            <td class="amount">
                ₹ {total_user_income:,.2f}
            </td>

            <td class="amount">
                ₹ {admin_fee:,.2f}
            </td>

            <td class="amount">
                ₹ {net_payable:,.2f}
            </td>

            <td>
                {bank_account}
            </td>

            <td>
                {bank_name}
            </td>

            <td>
                {ifsc}
            </td>

            <td>
                {bank_status}
            </td>

        </tr>
        """

        # ====================================================
        # TOTALS
        # ====================================================

        total_referral += referral_pending
        total_level += level_pending
        total_rank += rank_pending
        total_income += total_user_income
        total_admin_fee += admin_fee
        total_net_payable += net_payable

        serial_no += 1

    # ========================================================
    # REPORT DATE
    # ========================================================

    generated_at = datetime.now().strftime(
        "%d-%m-%Y %H:%M:%S"
    )

    # ========================================================
    # HTML
    # ========================================================

    html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>
    AurumFX - Pending Payout Report
</title>

<style>

    /* =====================================================
       A4 LANDSCAPE
       ===================================================== */

    @page {{
        size: A4 landscape;
        margin: 10mm;
    }}

    * {{
        box-sizing: border-box;
    }}

    body {{
        margin: 0;
        padding: 0;

        font-family:
            Arial,
            Helvetica,
            sans-serif;

        font-size: 8px;

        color: #222;

        background: #fff;
    }}

    .report {{
        width: 100%;
    }}

    /* =====================================================
       HEADER
       ===================================================== */

    .header {{
        text-align: center;

        margin-bottom: 10px;
    }}

    .company-name {{
        font-size: 22px;

        font-weight: bold;

        letter-spacing: 1px;
    }}

    .report-title {{
        font-size: 15px;

        font-weight: bold;

        margin-top: 3px;
    }}

    .generated {{
        font-size: 8px;

        margin-top: 3px;
    }}

    /* =====================================================
       INFO
       ===================================================== */

    .info {{
        display: flex;

        justify-content: space-between;

        border: 1px solid #999;

        padding: 6px 8px;

        margin-bottom: 8px;

        background: #f5f5f5;
    }}

    .info-item {{
        font-size: 8px;
    }}

    /* =====================================================
       TABLE
       ===================================================== */

    table {{
        width: 100%;

        border-collapse: collapse;

        table-layout: fixed;
    }}

    th {{
        border: 1px solid #888;

        background: #e9e9e9;

        padding: 5px 3px;

        text-align: center;

        font-size: 7.5px;

        font-weight: bold;
    }}

    td {{
        border: 1px solid #aaa;

        padding: 4px 3px;

        font-size: 7.5px;

        vertical-align: middle;

        word-wrap: break-word;
    }}

    .center {{
        text-align: center;
    }}

    .amount {{
        text-align: right;

        white-space: nowrap;
    }}

    .total-row {{
        font-weight: bold;

        background: #eeeeee;
    }}

    /* =====================================================
       SUMMARY
       ===================================================== */

    .summary {{
        display: flex;

        gap: 6px;

        margin-top: 10px;
    }}

    .summary-box {{
        flex: 1;

        border: 1px solid #999;

        padding: 6px;

        text-align: center;
    }}

    .summary-label {{
        font-size: 7px;

        font-weight: bold;
    }}

    .summary-value {{
        font-size: 10px;

        font-weight: bold;

        margin-top: 3px;
    }}

    /* =====================================================
       FOOTER
       ===================================================== */

    .footer {{
        display: flex;

        justify-content: space-between;

        margin-top: 12px;

        font-size: 7px;
    }}

    .signature {{
        margin-top: 25px;

        text-align: right;

        font-size: 8px;
    }}

    /* =====================================================
       PRINT
       ===================================================== */

    @media print {{

        body {{
            print-color-adjust: exact;

            -webkit-print-color-adjust: exact;
        }}

        thead {{
            display: table-header-group;
        }}

        tr {{
            page-break-inside: avoid;
        }}

    }}

</style>

</head>


<body>

<div class="report">

    <!-- =================================================
         HEADER
         ================================================= -->

    <div class="header">

        <div class="company-name">
            AurumFX
        </div>

        <div class="report-title">
            PENDING PAYOUT REPORT
        </div>

        <div class="generated">
            Generated on: {generated_at}
        </div>

    </div>


    <!-- =================================================
         INFORMATION
         ================================================= -->

    <div class="info">

        <div class="info-item">

            <strong>Status:</strong>
            PENDING

        </div>


        <div class="info-item">

            <strong>Admin Fee:</strong>
            {admin_fee_percentage:.2f}%

        </div>


        <div class="info-item">

            <strong>Total Users:</strong>
            {serial_no - 1}

        </div>

    </div>


    <!-- =================================================
         TABLE
         ================================================= -->

    <table>

        <thead>

            <tr>

                <th style="width: 3%;">
                    #
                </th>

                <th style="width: 7%;">
                    User ID
                </th>

                <th style="width: 10%;">
                    User Name
                </th>

                <th style="width: 8%;">
                    Referral
                </th>

                <th style="width: 8%;">
                    Level
                </th>

                <th style="width: 7%;">
                    Rank
                </th>

                <th style="width: 9%;">
                    Total Income
                </th>

                <th style="width: 8%;">
                    Admin Fee
                </th>

                <th style="width: 9%;">
                    Net Payable
                </th>

                <th style="width: 9%;">
                    Bank Account
                </th>

                <th style="width: 8%;">
                    Bank Name
                </th>

                <th style="width: 7%;">
                    IFSC
                </th>

                <th style="width: 7%;">
                    Bank Status
                </th>

            </tr>

        </thead>


        <tbody>

            {rows}


            <!-- =========================================
                 TOTAL
                 ========================================= -->

            <tr class="total-row">

                <td colspan="3" class="center">
                    TOTAL
                </td>

                <td class="amount">
                    ₹ {total_referral:,.2f}
                </td>

                <td class="amount">
                    ₹ {total_level:,.2f}
                </td>

                <td class="amount">
                    ₹ {total_rank:,.2f}
                </td>

                <td class="amount">
                    ₹ {total_income:,.2f}
                </td>

                <td class="amount">
                    ₹ {total_admin_fee:,.2f}
                </td>

                <td class="amount">
                    ₹ {total_net_payable:,.2f}
                </td>

                <td colspan="4">
                </td>

            </tr>

        </tbody>

    </table>


    <!-- =================================================
         SUMMARY
         ================================================= -->

    <div class="summary">

        <div class="summary-box">

            <div class="summary-label">
                TOTAL REFERRAL
            </div>

            <div class="summary-value">
                ₹ {total_referral:,.2f}
            </div>

        </div>


        <div class="summary-box">

            <div class="summary-label">
                TOTAL LEVEL
            </div>

            <div class="summary-value">
                ₹ {total_level:,.2f}
            </div>

        </div>


        <div class="summary-box">

            <div class="summary-label">
                TOTAL RANK
            </div>

            <div class="summary-value">
                ₹ {total_rank:,.2f}
            </div>

        </div>


        <div class="summary-box">

            <div class="summary-label">
                TOTAL PENDING
            </div>

            <div class="summary-value">
                ₹ {total_income:,.2f}
            </div>

        </div>


        <div class="summary-box">

            <div class="summary-label">
                TOTAL ADMIN FEE
            </div>

            <div class="summary-value">
                ₹ {total_admin_fee:,.2f}
            </div>

        </div>


        <div class="summary-box">

            <div class="summary-label">
                TOTAL NET PAYABLE
            </div>

            <div class="summary-value">
                ₹ {total_net_payable:,.2f}
            </div>

        </div>

    </div>


    <!-- =================================================
         FOOTER
         ================================================= -->

    <div class="footer">

        <div>
            AurumFX - Pending Payout Report
        </div>

        <div>
            Total Records: {serial_no - 1}
        </div>

    </div>


    <div class="signature">

        Authorized By:
        ______________________________

    </div>

</div>

</body>

</html>
"""

    return HTMLResponse(
        content=html
    )

# ============================================================
# PAY USER
# ============================================================

@router.post("/{user_id}/pay")
def pay_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    Pay all pending income for a user.

    Flow:

        Referral
             +
        Level
             +
        Rank
             =
        Gross Income

        Gross Income
             -
        Admin Fee
             =
        Net Payable

    Wallet:

        pending_balance -= gross income

        balance += net payable

        admin_fee += admin fee

    PayoutHistory:

        A history record is created.
    """

    try:

        # ====================================================
        # GET USER
        # ====================================================

        user = (
            db.query(User)
            .options(
                joinedload(
                    User.bank_details
                )
            )
            .filter(
                User.id == user_id
            )
            .first()
        )

        if not user:

            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # ====================================================
        # LOCK WALLET
        # ====================================================

        wallet = get_user_wallet(
            db,
            user.id,
            create=True
        )

        # ====================================================
        # LOCK PENDING REFERRAL
        # ====================================================

        referral_records = (
            get_pending_referral(
                db,
                user.id
            )
        )

        referral_amount = sum(
            (
                money(
                    record.commission_amount
                )
                for record in referral_records
            ),
            Decimal("0.00")
        )

        # ====================================================
        # LOCK PENDING LEVEL
        # ====================================================

        level_records = (
            get_pending_level(
                db,
                user.id
            )
        )

        level_amount = sum(
            (
                money(
                    record.commission_amount
                )
                for record in level_records
            ),
            Decimal("0.00")
        )

        # ====================================================
        # LOCK PENDING RANK
        # ====================================================

        rank_records = (
            get_pending_rank(
                db,
                user.id
            )
        )

        rank_amount = sum(
            (
                money(
                    record.reward_income
                )
                for record in rank_records
            ),
            Decimal("0.00")
        )

        # ====================================================
        # TOTAL GROSS INCOME
        # ====================================================

        total_income = money(
            referral_amount
            + level_amount
            + rank_amount
        )

        if total_income <= 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No pending income available "
                    "for payout"
                )
            )

        # ====================================================
        # CHECK WALLET PENDING BALANCE
        # ====================================================

        wallet_pending_before = money(
            wallet.pending_balance
        )

        if wallet_pending_before < total_income:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Wallet pending balance "
                    f"({wallet_pending_before}) is less "
                    f"than calculated pending income "
                    f"({total_income})."
                )
            )

        # ====================================================
        # GET LONGEST APPROVED INVESTMENT
        # ====================================================

        investment = get_longest_investment(
            db,
            user.id
        )

        if not investment:

            raise HTTPException(
                status_code=400,
                detail=(
                    "User has no approved investment"
                )
            )

        plan = investment.investment_plan

        if not plan:

            raise HTTPException(
                status_code=400,
                detail="Investment plan not found"
            )

        # ====================================================
        # GET ADMIN FEE %
        # ====================================================

        admin_fee_percentage = (
            get_admin_fee_percentage(db)
        )

        # ====================================================
        # ADMIN FEE
        # ====================================================

        admin_fee = money(
            total_income
            * admin_fee_percentage
            / Decimal("100")
        )

        # ====================================================
        # NET PAYABLE
        # ====================================================

        net_payable = money(
            total_income
            - admin_fee
        )

        if net_payable <= 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Net payable amount must be "
                    "greater than zero"
                )
            )

        # ====================================================
        # PAYMENT TIME
        # ====================================================

        payment_time = datetime.utcnow()

        # ====================================================
        # WALLET BEFORE VALUES
        # ====================================================

        balance_before = money(
            wallet.balance
        )

        admin_fee_before = money(
            wallet.admin_fee
        )

        pending_before = money(
            wallet.pending_balance
        )

        # ====================================================
        # UPDATE WALLET
        # ====================================================

        wallet.pending_balance = money(
            pending_before
            - total_income
        )

        wallet.balance = money(
            balance_before
            + net_payable
        )

        wallet.admin_fee = money(
            admin_fee_before
            + admin_fee
        )

        # ====================================================
        # REFERRAL → PAID
        # ====================================================

        for record in referral_records:

            record.status = "PAID"

            if hasattr(
                record,
                "payment_date"
            ):
                record.payment_date = (
                    payment_time
                )

        # ====================================================
        # LEVEL → PAID
        # ====================================================

        for record in level_records:

            record.status = "PAID"

            if hasattr(
                record,
                "payment_date"
            ):
                record.payment_date = (
                    payment_time
                )

        # ====================================================
        # RANK → PAID
        # ====================================================

        for record in rank_records:

            record.reward_paid = True

            if hasattr(
                record,
                "paid_at"
            ):
                record.paid_at = (
                    payment_time
                )

        # ====================================================
        # WALLET TRANSACTIONS → PAID
        # ====================================================

        transaction_types = (
            "REFERRAL",
            "LEVEL_INCOME",
            "RANK_REWARD"
        )

        wallet_transactions = (
            db.query(WalletTransaction)
            .filter(
                WalletTransaction.wallet_id
                == wallet.id,

                WalletTransaction.status
                == "PENDING",

                WalletTransaction.transaction_type
                .in_(transaction_types)
            )
            .with_for_update()
            .all()
        )

        for transaction in wallet_transactions:

            transaction.status = "PAID"

        # ====================================================
        # CREATE PAYOUT HISTORY
        # ====================================================

        payout_history = PayoutHistory(

            user_id=user.id,

            # ----------------------------------------------
            # Income
            # ----------------------------------------------

            referral_income=float(
                referral_amount
            ),

            level_income=float(
                level_amount
            ),

            rank_income=float(
                rank_amount
            ),

            total_income=float(
                total_income
            ),

            # ----------------------------------------------
            # Admin Fee
            # ----------------------------------------------

            admin_fee_percentage=float(
                admin_fee_percentage
            ),

            admin_fee=float(
                admin_fee
            ),

            net_payable=float(
                net_payable
            ),

            # ----------------------------------------------
            # Payout Details
            # ----------------------------------------------

            payout_method="BANK_TRANSFER",

            payout_information=None,

            # ----------------------------------------------
            # Status
            # ----------------------------------------------

            status="PAID",

            paid_at=payment_time,

            created_at=payment_time
        )

        db.add(
            payout_history
        )

        # ====================================================
        # COMMIT
        # ====================================================

        db.commit()

        # ====================================================
        # REFRESH
        # ====================================================

        db.refresh(wallet)

        db.refresh(
            payout_history
        )

        # ====================================================
        # BANK DETAILS
        # ====================================================

        bank_details = get_bank_details(
            user
        )

        # ====================================================
        # RESPONSE
        # ====================================================

        return {

            "message": (
                "Payout completed successfully"
            ),

            "payout_history_id": (
                payout_history.id
            ),

            "user_id": user.id,

            "user_code": user.user_id,

            "user_name": get_user_name(
                user
            ),

            # ----------------------------------------------
            # Income
            # ----------------------------------------------

            "referral_income": float(
                referral_amount
            ),

            "level_income": float(
                level_amount
            ),

            "rank_income": float(
                rank_amount
            ),

            "total_income": float(
                total_income
            ),

            # ----------------------------------------------
            # Investment
            # ----------------------------------------------

            "investment_plan": (
                plan.plan_name
            ),

            "duration_months": (
                plan.duration_months
            ),

            # ----------------------------------------------
            # Admin Fee
            # ----------------------------------------------

            "admin_fee_percentage": float(
                admin_fee_percentage
            ),

            "admin_fee": float(
                admin_fee
            ),

            # ----------------------------------------------
            # Net Payable
            # ----------------------------------------------

            "net_payable": float(
                net_payable
            ),

            # ----------------------------------------------
            # Wallet
            # ----------------------------------------------

            "wallet": {

                "balance_before": float(
                    balance_before
                ),

                "balance_after": float(
                    wallet.balance
                ),

                "pending_balance_before": float(
                    pending_before
                ),

                "pending_balance_after": float(
                    wallet.pending_balance
                ),

                "admin_fee_before": float(
                    admin_fee_before
                ),

                "admin_fee_after": float(
                    wallet.admin_fee
                )
            },

            # ----------------------------------------------
            # Bank Details
            # ----------------------------------------------

            "bank_details": bank_details,

            # ----------------------------------------------
            # Payout History
            # ----------------------------------------------

            "payout_history": {

                "id": payout_history.id,

                "payout_method": (
                    payout_history.payout_method
                ),

                "payout_information": (
                    payout_history.payout_information
                ),

                "status": (
                    payout_history.status
                ),

                "paid_at": (
                    payout_history.paid_at
                ),

                "created_at": (
                    payout_history.created_at
                )
            },

            "status": "PAID",

            "paid_at": payment_time
        }

    except HTTPException:

        db.rollback()

        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Payout failed: {str(e)}"
        )


# ============================================================
# BULK PAY SELECTED USERS
# ============================================================

@router.post("/bulk-pay")
def bulk_pay_users(
    payload: BulkPayoutRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    Pay multiple users selected by admin.

    Example request:

    {
        "user_ids": [12, 15, 18, 25]
    }

    Each user is processed independently.

    If one user fails, other users can still be paid.
    """

    if not payload.user_ids:
        raise HTTPException(
            status_code=400,
            detail="Please select at least one user"
        )

    # Remove duplicate IDs
    user_ids = list(set(payload.user_ids))

    results = []

    total_paid = Decimal("0.00")
    total_admin_fee = Decimal("0.00")

    success_count = 0
    failed_count = 0

    for user_id in user_ids:

        try:

            # ====================================================
            # GET USER
            # ====================================================

            user = (
                db.query(User)
                .options(
                    joinedload(
                        User.bank_details
                    )
                )
                .filter(
                    User.id == user_id
                )
                .first()
            )

            if not user:

                results.append({
                    "user_id": user_id,
                    "status": "FAILED",
                    "message": "User not found"
                })

                failed_count += 1
                continue

            # ====================================================
            # LOCK WALLET
            # ====================================================

            wallet = get_user_wallet(
                db,
                user.id,
                create=True
            )

            # ====================================================
            # PENDING REFERRAL
            # ====================================================

            referral_records = get_pending_referral(
                db,
                user.id
            )

            referral_amount = sum(
                (
                    money(record.commission_amount)
                    for record in referral_records
                ),
                Decimal("0.00")
            )

            # ====================================================
            # PENDING LEVEL
            # ====================================================

            level_records = get_pending_level(
                db,
                user.id
            )

            level_amount = sum(
                (
                    money(record.commission_amount)
                    for record in level_records
                ),
                Decimal("0.00")
            )

            # ====================================================
            # PENDING RANK
            # ====================================================

            rank_records = get_pending_rank(
                db,
                user.id
            )

            rank_amount = sum(
                (
                    money(record.reward_income)
                    for record in rank_records
                ),
                Decimal("0.00")
            )

            # ====================================================
            # TOTAL GROSS
            # ====================================================

            total_income = money(
                referral_amount
                + level_amount
                + rank_amount
            )

            if total_income <= 0:

                results.append({
                    "user_id": user.id,
                    "user_code": user.user_id,
                    "user_name": get_user_name(user),
                    "status": "FAILED",
                    "message": "No pending income available for payout"
                })

                failed_count += 1
                continue

            # ====================================================
            # CHECK PENDING BALANCE
            # ====================================================

            pending_before = money(
                wallet.pending_balance
            )

            if pending_before < total_income:

                results.append({
                    "user_id": user.id,
                    "user_code": user.user_id,
                    "user_name": get_user_name(user),
                    "status": "FAILED",
                    "message": (
                        f"Wallet pending balance "
                        f"({pending_before}) is less than "
                        f"calculated pending income "
                        f"({total_income})"
                    )
                })

                failed_count += 1
                continue

            # ====================================================
            # INVESTMENT
            # ====================================================

            investment = get_longest_investment(
                db,
                user.id
            )

            if not investment:

                results.append({
                    "user_id": user.id,
                    "user_code": user.user_id,
                    "user_name": get_user_name(user),
                    "status": "FAILED",
                    "message": "User has no approved investment"
                })

                failed_count += 1
                continue

            plan = investment.investment_plan

            if not plan:

                results.append({
                    "user_id": user.id,
                    "user_code": user.user_id,
                    "user_name": get_user_name(user),
                    "status": "FAILED",
                    "message": "Investment plan not found"
                })

                failed_count += 1
                continue

            # ====================================================
            # ADMIN FEE
            # ====================================================

            admin_fee_percentage = get_admin_fee_percentage(db)

            admin_fee = money(
                total_income
                * admin_fee_percentage
                / Decimal("100")
            )

            # ====================================================
            # NET PAYABLE
            # ====================================================

            net_payable = money(
                total_income
                - admin_fee
            )

            if net_payable <= 0:

                results.append({
                    "user_id": user.id,
                    "user_code": user.user_id,
                    "user_name": get_user_name(user),
                    "status": "FAILED",
                    "message": "Net payable amount must be greater than zero"
                })

                failed_count += 1
                continue

            # ====================================================
            # PAYMENT TIME
            # ====================================================

            payment_time = datetime.utcnow()

            # ====================================================
            # WALLET BEFORE
            # ====================================================

            balance_before = money(
                wallet.balance
            )

            admin_fee_before = money(
                wallet.admin_fee
            )

            # ====================================================
            # UPDATE WALLET
            # ====================================================

            wallet.pending_balance = money(
                pending_before
                - total_income
            )

            wallet.balance = money(
                balance_before
                + net_payable
            )

            wallet.admin_fee = money(
                admin_fee_before
                + admin_fee
            )

            # ====================================================
            # REFERRAL -> PAID
            # ====================================================

            for record in referral_records:

                record.status = "PAID"

                if hasattr(
                    record,
                    "payment_date"
                ):
                    record.payment_date = payment_time

            # ====================================================
            # LEVEL -> PAID
            # ====================================================

            for record in level_records:

                record.status = "PAID"

                if hasattr(
                    record,
                    "payment_date"
                ):
                    record.payment_date = payment_time

            # ====================================================
            # RANK -> PAID
            # ====================================================

            for record in rank_records:

                record.reward_paid = True

                if hasattr(
                    record,
                    "paid_at"
                ):
                    record.paid_at = payment_time

            # ====================================================
            # WALLET TRANSACTIONS -> PAID
            # ====================================================

            transaction_types = (
                "REFERRAL",
                "LEVEL_INCOME",
                "RANK_REWARD"
            )

            wallet_transactions = (
                db.query(WalletTransaction)
                .filter(
                    WalletTransaction.wallet_id == wallet.id,

                    WalletTransaction.status == "PENDING",

                    WalletTransaction.transaction_type.in_(
                        transaction_types
                    )
                )
                .with_for_update()
                .all()
            )

            for transaction in wallet_transactions:

                transaction.status = "PAID"

            # ====================================================
            # PAYOUT HISTORY
            # ====================================================

            payout_history = PayoutHistory(

                user_id=user.id,

                referral_income=float(
                    referral_amount
                ),

                level_income=float(
                    level_amount
                ),

                rank_income=float(
                    rank_amount
                ),

                total_income=float(
                    total_income
                ),

                admin_fee_percentage=float(
                    admin_fee_percentage
                ),

                admin_fee=float(
                    admin_fee
                ),

                net_payable=float(
                    net_payable
                ),

                payout_method="BANK_TRANSFER",

                payout_information=None,

                status="PAID",

                paid_at=payment_time,

                created_at=payment_time
            )

            db.add(
                payout_history
            )

            # ====================================================
            # FLUSH
            # ====================================================

            db.flush()

            # ====================================================
            # SUCCESS
            # ====================================================

            results.append({

                "user_id": user.id,

                "user_code": user.user_id,

                "user_name": get_user_name(user),

                "status": "PAID",

                "payout_history_id": (
                    payout_history.id
                ),

                "referral_income": float(
                    referral_amount
                ),

                "level_income": float(
                    level_amount
                ),

                "rank_income": float(
                    rank_amount
                ),

                "total_income": float(
                    total_income
                ),

                "admin_fee": float(
                    admin_fee
                ),

                "net_payable": float(
                    net_payable
                ),

                "investment_plan": (
                    plan.plan_name
                )
            })

            success_count += 1

            total_paid += net_payable

            total_admin_fee += admin_fee

        except Exception as e:

            results.append({

                "user_id": user_id,

                "status": "FAILED",

                "message": str(e)
            })

            failed_count += 1

            # Continue with next user
            continue

    # ========================================================
    # COMMIT ALL SUCCESSFUL PAYMENTS
    # ========================================================

    try:

        db.commit()

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Bulk payout failed: {str(e)}"
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "message": "Bulk payout processing completed",

        "total_selected": len(user_ids),

        "success_count": success_count,

        "failed_count": failed_count,

        "total_paid": float(
            total_paid
        ),

        "total_admin_fee": float(
            total_admin_fee
        ),

        "results": results
    }



# ============================================================
# GET PAID PAYOUTS
# ============================================================

@router.get("/paid")
def get_paid_payouts(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    Get all paid payouts.
    """

    payouts = (
        db.query(PayoutHistory)
        .join(
            User,
            PayoutHistory.user_id == User.id
        )
        .options(
            joinedload(
                PayoutHistory.user
            ).joinedload(
                User.bank_details
            )
        )
        .filter(
            PayoutHistory.status == "PAID"
        )
        .order_by(
            PayoutHistory.paid_at.desc()
        )
        .all()
    )

    result = []

    for payout in payouts:

        user = payout.user

        if not user:
            continue

        bank_details = get_bank_details(
            user
        )

        result.append({

            "payout_history_id": payout.id,

            "user_id": user.id,

            "user_code": user.user_id,

            "user_name": get_user_name(
                user
            ),

            # ----------------------------------------------
            # Income
            # ----------------------------------------------

            "referral_income": float(
                payout.referral_income or 0
            ),

            "level_income": float(
                payout.level_income or 0
            ),

            "rank_income": float(
                payout.rank_income or 0
            ),

            "total_income": float(
                payout.total_income or 0
            ),

            # ----------------------------------------------
            # Admin Fee
            # ----------------------------------------------

            "admin_fee_percentage": float(
                payout.admin_fee_percentage or 0
            ),

            "admin_fee": float(
                payout.admin_fee or 0
            ),

            # ----------------------------------------------
            # Net Payable
            # ----------------------------------------------

            "net_payable": float(
                payout.net_payable or 0
            ),

            # ----------------------------------------------
            # Bank Details
            # ----------------------------------------------

            "bank_details": bank_details,

            # ----------------------------------------------
            # Payout
            # ----------------------------------------------

            "payout_method": (
                payout.payout_method
            ),

            "payout_information": (
                payout.payout_information
            ),

            "status": payout.status,

            "paid_at": payout.paid_at,

            "created_at": payout.created_at,
        })

    return {
        "total": len(result),
        "items": result
    }


# ============================================================
# GET PAYOUT HISTORY
# ============================================================

@router.get("/history")
def get_payout_history(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: str | None = Query(None),
    user_id: int | None = Query(None),

    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    Get payout history with filters.

    Filters:

        start_date
        end_date
        status
        user_id
    """

    query = (
        db.query(PayoutHistory)
        .join(
            User,
            PayoutHistory.user_id == User.id
        )
        .options(
            joinedload(
                PayoutHistory.user
            ).joinedload(
                User.bank_details
            )
        )
    )

    # ========================================================
    # USER ID FILTER
    # ========================================================

    if user_id is not None:

        query = query.filter(
            PayoutHistory.user_id == user_id
        )

    # ========================================================
    # STATUS FILTER
    # ========================================================

    if status:

        query = query.filter(
            PayoutHistory.status
            == status.upper()
        )

    # ========================================================
    # START DATE FILTER
    # ========================================================

    if start_date:

        query = query.filter(
            PayoutHistory.paid_at
            >= datetime.combine(
                start_date,
                datetime.min.time()
            )
        )

    # ========================================================
    # END DATE FILTER
    # ========================================================

    if end_date:

        # Include the entire end_date.
        #
        # Example:
        #
        # end_date = 2026-08-28
        #
        # Includes:
        #
        # 2026-08-28 00:00:00
        # through
        # 2026-08-28 23:59:59.999999

        end_datetime = (
            datetime.combine(
                end_date,
                datetime.min.time()
            )
            + timedelta(days=1)
        )

        query = query.filter(
            PayoutHistory.paid_at
            < end_datetime
        )

    # ========================================================
    # ORDER
    # ========================================================

    payouts = (
        query
        .order_by(
            PayoutHistory.paid_at.desc()
        )
        .all()
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    result = []

    for payout in payouts:

        user = payout.user

        if not user:
            continue

        bank_details = get_bank_details(
            user
        )

        result.append({

            "payout_history_id": payout.id,

            "user_id": user.id,

            "user_code": user.user_id,

            "user_name": get_user_name(
                user
            ),

            # --------------------------------------------
            # Income
            # --------------------------------------------

            "referral_income": float(
                payout.referral_income or 0
            ),

            "level_income": float(
                payout.level_income or 0
            ),

            "rank_income": float(
                payout.rank_income or 0
            ),

            "total_income": float(
                payout.total_income or 0
            ),

            # --------------------------------------------
            # Admin Fee
            # --------------------------------------------

            "admin_fee_percentage": float(
                payout.admin_fee_percentage or 0
            ),

            "admin_fee": float(
                payout.admin_fee or 0
            ),

            # --------------------------------------------
            # Net Payable
            # --------------------------------------------

            "net_payable": float(
                payout.net_payable or 0
            ),

            # --------------------------------------------
            # Bank Details
            # --------------------------------------------

            "bank_details": bank_details,

            # --------------------------------------------
            # Payout
            # --------------------------------------------

            "payout_method": (
                payout.payout_method
            ),

            "payout_information": (
                payout.payout_information
            ),

            "status": payout.status,

            "paid_at": payout.paid_at,

            "created_at": payout.created_at,
        })

    return {
        "total": len(result),
        "items": result
    }