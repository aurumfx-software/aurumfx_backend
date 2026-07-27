from datetime import date
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    User,
    Investment,
    Wallet,
    WalletTransaction,
    BinaryWallet,
    BinaryIncome
)

#-------------------------------------------------------------------------------------------------
# Create Binary wallet
#-------------------------------------------------------------------------------------------------
def get_binary_wallet(db: Session, user_id: int):

    wallet = (
        db.query(BinaryWallet)
        .filter(BinaryWallet.user_id == user_id)
        .first()
    )

    if wallet:
        return wallet

    wallet = BinaryWallet(
        user_id=user_id,
        left_business=0,
        right_business=0,
        left_carry=0,
        right_carry=0
    )

    db.add(wallet)
    db.flush()

    return wallet

#------------------------------------------------------------------------------------------------------------
# Get / Create wallet
#------------------------------------------------------------------------------------------------------------
def get_wallet(db: Session, user_id: int):

    wallet = (
        db.query(Wallet)
        .filter(Wallet.user_id == user_id)
        .first()
    )

    if wallet:
        return wallet

    wallet = Wallet(
        user_id=user_id,
        balance=0
    )

    db.add(wallet)
    db.flush()

    return wallet

#-------------------------------------------------------------------------------------------------------------------
#Find placement parent
#-------------------------------------------------------------------------------------------------------------------
def get_parent(db: Session, user: User):

    if not user.placement_parent:
        return None

    return (
        db.query(User)
        .filter(User.user_id == user.placement_parent)
        .first()
    )

#----------------------------------------------------------------------------------------------------------------------
#Add buisiness to parent
#----------------------------------------------------------------------------------------------------------------------
def add_business(
    db: Session,
    parent: User,
    side: str,
    amount: float
):

    wallet = get_binary_wallet(
        db,
        parent.id
    )

    if side == "Left":
        wallet.left_business += amount
    else:
        wallet.right_business += amount
#----------------------------------------------------------------------------------------------------------------------------
#Users total approved investment
#----------------------------------------------------------------------------------------------------------------------------
def get_total_investment(
    db: Session,
    user_id: int
):

    result = (
        db.query(
            func.coalesce(
                func.sum(Investment.amount),
                0
            )
        )
        .filter(
            Investment.user_id == user_id,
            Investment.approval_status == "APPROVED"
        )
        .scalar()
    )

    return result
#--------------------------------------------------------------------------------------------------------------------------------
#Daily binary limit
#--------------------------------------------------------------------------------------------------------------------------------
def get_daily_limit(total):

    if total >= 1000000:
        return 20000

    elif total >= 500000:
        return 15000

    elif total >= 200000:
        return 10000

    elif total >= 5000:
        return 5000

    return 0
#------------------------------------------------------------------------------------------------------------------------------------------
#Todays paid binary income
#------------------------------------------------------------------------------------------------------------------------------------------
def get_today_binary(
    db: Session,
    user_id: int
):

    return (
        db.query(
            func.coalesce(
                func.sum(BinaryIncome.paid_income),
                0
            )
        )
        .filter(
            BinaryIncome.user_id == user_id,
            func.date(BinaryIncome.created_at) == date.today()
        )
        .scalar()
    )
#-------------------------------------------------------------------------------------------------------------------------------------------------
#Propagate business
#-------------------------------------------------------------------------------------------------------------------------------------------------
def propagate_business(
    db: Session,
    investment: Investment
):

    user = (
        db.query(User)
        .filter(User.id == investment.user_id)
        .first()
    )

    current = user

    while current:

        parent = get_parent(
            db,
            current
        )

        if not parent:
            break

        print(
            f"Adding {investment.amount} to {parent.user_id} ({current.club})"
        )

        add_business(
            db,
            parent,
            current.club,
            investment.amount
        )

        process_matching(
            db,
            parent,
            investment
        )

        current = parent

    db.commit()
#-------------------------------------------------------------------------------------------------------------------------------------------------
#Matching Function Skeleton
#-------------------------------------------------------------------------------------------------------------------------------------------------
def process_matching(
    db: Session,
    user: User,
    investment: Investment
    
):
    
    wallet = get_binary_wallet(
        db,
        user.id
    )

    left = wallet.left_business
    right = wallet.right_business

    print("--------------------------------")
    print("User :", user.user_id)
    print("Left :", wallet.left_business)
    print("Right:", wallet.right_business)

    matched = min(left, right)

    # No matching business
    if matched <= 0:
        return
    print(f"User : {user.user_id}")
    print(f"Left : {left}")
    print(f"Right: {right}")

    matched = min(left, right)

    print(f"Matched : {matched}")
    # STEP 11: Calculate binary income (4%)
    binary_income = matched * 0.04

    # STEP 12: Get user's total approved investment
    total = get_total_investment(
        db,
        user.id
    )

    # Get daily limit
    daily_limit = get_daily_limit(total)

    # Today's already paid binary income
    today_paid = get_today_binary(
        db,
        user.id
    )

    available = max(
        daily_limit - today_paid,
        0
    )

    paid_income = min(
        binary_income,
        available
    )

    paid_income = min(
    binary_income,
    available
)

    print("========== BINARY DEBUG ==========")
    print("User            :", user.user_id)
    print("Matched         :", matched)
    print("Binary Income   :", binary_income)
    print("Total Investment:", total)
    print("Daily Limit     :", daily_limit)
    print("Today Paid      :", today_paid)
    print("Available       :", available)
    print("Paid Income     :", paid_income)
    print("==================================")

    

    # Credit wallet
    member_wallet = get_wallet(
        db,
        user.id
    )

    if paid_income <= 0:
        return

    # Update carry forward
    wallet.left_business -= matched
    wallet.right_business -= matched
    
    wallet.left_carry = wallet.left_business
    wallet.right_carry = wallet.right_business

    member_wallet.balance += paid_income
    
    
    # matched = min(wallet.left_business, wallet.right_business)
    
    # print("Matched :", matched)

    # Wallet transaction
    transaction = WalletTransaction(
        wallet_id=member_wallet.id,
        investment_id=investment.id,
        amount=paid_income,
        transaction_type="BINARY",
        remarks="Binary Income"
    )

    
    # Save binary income history
    history = BinaryIncome(
        user_id=user.id,
        investment_id=investment.id,
        matched_amount=matched,
        percentage=4,
        income=binary_income,
        paid_income=paid_income,
        daily_limit=daily_limit,
        left_before=left,
        right_before=right,
        left_after=wallet.left_business,
        right_after=wallet.right_business
    )

    db.add(transaction)
    db.add(history)
    db.commit()

    

    