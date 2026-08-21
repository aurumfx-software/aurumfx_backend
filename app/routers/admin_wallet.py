from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date



from app.database import get_db
from app.models import (
    User,
    Wallet,
    ReferralCommission,
    LevelIncome,
    LevelCommissionHistory,
    UserRankHistory,
    AdminFeeSetting,
    WalletTransaction,
    Investment,
)
from app.core.security import get_current_user


router = APIRouter(
    prefix="/admin/wallet",
    tags=["Admin Wallet"]
)


# ============================================================
# Admin Fee
# ============================================================

def get_admin_fee_percentage(db: Session) -> float:

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
        return 0.0

    return float(
        fee_setting.fee_percentage or 0
    )





# ...


@router.get("/transactions")
def get_all_wallet_transactions(
    start_date: date | None = Query(
        None,
        description="Start date"
    ),
    end_date: date | None = Query(
        None,
        description="End date"
    ),
    user_id: str | None = Query(
        None,
        description="Filter by user ID"
    ),
    transaction_type: str | None = Query(
        None,
        description="Filter by transaction type"
    ),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # ========================================================
    # ADMIN
    # ========================================================

    admin = (
        db.query(User)
        .filter(
            User.user_id == current_user
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="Admin user not found"
        )

    # ========================================================
    # VALIDATE DATE RANGE
    # ========================================================

    if start_date and end_date:

        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date cannot be greater than end_date"
            )

    # ========================================================
    # BASE QUERY
    # ========================================================

    query = (
        db.query(
            WalletTransaction,
            Wallet,
            User
        )
        .join(
            Wallet,
            WalletTransaction.wallet_id == Wallet.id
        )
        .join(
            User,
            Wallet.user_id == User.id
        )
    )

    # ========================================================
    # USER FILTER
    # ========================================================

    if user_id:

        query = query.filter(
            User.user_id == user_id
        )

    # ========================================================
    # TRANSACTION TYPE FILTER
    # ========================================================

    if transaction_type:

        query = query.filter(
            WalletTransaction.transaction_type ==
            transaction_type
        )

    # ========================================================
    # START DATE
    # ========================================================

    if start_date:

        query = query.filter(
            func.date(
                WalletTransaction.created_at
            ) >= start_date
        )

    # ========================================================
    # END DATE
    # ========================================================

    if end_date:

        query = query.filter(
            func.date(
                WalletTransaction.created_at
            ) <= end_date
        )

    # ========================================================
    # ORDER
    # ========================================================

    transactions = (
        query
        .order_by(
            WalletTransaction.id.desc()
        )
        .all()
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    response = []

    for transaction, wallet, user in transactions:

        # ----------------------------------------------------
        # FROM USER
        # ----------------------------------------------------

        from_user = None

        if transaction.investment_id:

            investment = (
                db.query(Investment)
                .filter(
                    Investment.id ==
                    transaction.investment_id
                )
                .first()
            )

            if investment:

                investor = (
                    db.query(User)
                    .filter(
                        User.id ==
                        investment.user_id
                    )
                    .first()
                )

                if investor:

                    from_user = {
                        "user_id":
                            investor.user_id,

                        "name":
                            (
                                f"{investor.first_name or ''} "
                                f"{investor.last_name or ''}"
                            ).strip()
                    }

        # ----------------------------------------------------
        # PAYMENT TYPE
        # ----------------------------------------------------

        if transaction.status == "PAID":

            payment_type = "CREDIT"

        elif transaction.status == "PENDING":

            payment_type = "PENDING"

        else:

            payment_type = transaction.status

        # ----------------------------------------------------
        # USER NAME
        # ----------------------------------------------------

        user_name = (
            f"{user.first_name or ''} "
            f"{user.last_name or ''}"
        ).strip()

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        response.append({

            "id":
                transaction.id,

            "user": {
                "user_id":
                    user.user_id,

                "name":
                    user_name
            },

            "wallet_id":
                wallet.id,

            "from_user":
                from_user,

            "investment_id":
                transaction.investment_id,

            "transaction_type":
                transaction.transaction_type,

            "payment_type":
                payment_type,

            "amount":
                float(
                    transaction.amount or 0
                ),

            "status":
                transaction.status,

            "date":
                transaction.created_at
        })

    return response