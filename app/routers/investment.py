from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.models import User, Investment, InvestmentPlan, ReturnType
from app.schemas import (
    InvestmentCreate,
    InvestmentResponse
)
from app.core.security import get_current_user
from app.utils.investment_id import generate_investment_id
from app.utils.return_date import calculate_return_date

router = APIRouter(
    prefix="/investments",
    tags=["Investments"]
)


# -----------------------------------
# Create Investment
# -----------------------------------
@router.post("/", response_model=InvestmentResponse)
def create_investment(
    investment: InvestmentCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # Logged in User
    user = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Investment Plan
    plan = (
        db.query(InvestmentPlan)
        .filter(
            InvestmentPlan.id == investment.investment_plan_id,
            InvestmentPlan.status == True
        )
        .first()
    )

    if not plan:
        raise HTTPException(
            status_code=404,
            detail="Investment Plan not found"
        )

    # Minimum Amount
    if investment.amount < 5000:
        raise HTTPException(
            status_code=400,
            detail="Minimum investment amount is ₹5000."
        )

    # Multiple of 5000
    if investment.amount % 5000 != 0:
        raise HTTPException(
            status_code=400,
            detail="Investment amount must be a multiple of ₹5000."
        )

    # Validate Enroller
    enroller = (
        db.query(User)
        .filter(User.user_id == investment.enroller_id)
        .first()
    )

    if not enroller:
        raise HTTPException(
            status_code=400,
            detail="Invalid Enroller ID"
        )

    # Enroller should be Admin
    # if enroller.role != "ADMIN":
    #     raise HTTPException(
    #         status_code=400,
    #         detail="Enroller must be an Admin."
    #     )

    # Lots
    lots = int(investment.amount / 5000)

    # Monthly Return Amount
    monthly_return_amount = (
        investment.amount *
        plan.return_percentage
    ) / 100

    # Return Balance
    return_balance = plan.duration_months

    # Return Date
    return_date = calculate_return_date(
        investment.investment_date
    )

    # Return Type
    return_type = (
        db.query(ReturnType)
        .filter(
            ReturnType.id == investment.return_type_id,
            ReturnType.status == True
        )
        .first()
    )

    if not return_type:
        raise HTTPException(
            status_code=404,
            detail="Return type not found"
        )

    # Investment ID
    investment_id = generate_investment_id(db)

    # Save
    db_investment = Investment(

        investment_id=investment_id,

        user_id=user.id,
        
        return_type_id=return_type.id,

        investment_plan_id=plan.id,

        amount=investment.amount,

        lots=lots,

        monthly_return_percentage=plan.return_percentage,

        monthly_return_amount=monthly_return_amount,

        return_which=0,

        return_balance=return_balance,

        return_date=return_date,

        bank_transaction_id=investment.bank_transaction_id,

        payment_proof=None,

        enroller_id=investment.enroller_id,

        investment_status="PENDING",

        approval_status="PENDING",

        investment_date=investment.investment_date

    )

    db.add(db_investment)
    db.commit()
    db.refresh(db_investment)

    return InvestmentResponse(

        id=db_investment.id,

        investment_id=db_investment.investment_id,

        return_type=return_type.return_type,

        plan_name=plan.plan_name,

        amount=db_investment.amount,

        lots=db_investment.lots,

        monthly_return_percentage=db_investment.monthly_return_percentage,

        monthly_return_amount=db_investment.monthly_return_amount,

        return_which=db_investment.return_which,

        return_balance=db_investment.return_balance,

        return_date=db_investment.return_date,

        investment_status=db_investment.investment_status,

        approval_status=db_investment.approval_status,

        investment_date=db_investment.investment_date

    )


# -----------------------------------
# My Investments
# -----------------------------------
@router.get("/", response_model=list[InvestmentResponse])
def my_investments(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: str | None = Query(None),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # investments = (
    #     db.query(Investment)
    #     .filter(Investment.user_id == user.id)
    #     .all()
    # )

    query = db.query(Investment).filter(
    Investment.user_id == user.id
)

    # Filter by Start Date
    if start_date:
        query = query.filter(
            Investment.investment_date >= start_date
        )

    # Filter by End Date
    if end_date:
        query = query.filter(
            Investment.investment_date <= end_date
        )

    # Filter by Status
    if status:
        query = query.filter(
            Investment.investment_status == status.upper()
        )

    investments = query.order_by(
        Investment.id.desc()
    ).all()
     
    response = []

    for inv in investments:

        plan = (
            db.query(InvestmentPlan)
            .filter(
                InvestmentPlan.id == inv.investment_plan_id
            )
            .first()
        )

        return_type = (
            db.query(ReturnType)
            .filter(
                ReturnType.id == inv.return_type_id
            )
            .first()
        )

        response.append(
            InvestmentResponse(
                id=inv.id,
                investment_id=inv.investment_id,
                return_type=return_type.return_type if return_type else "",
                plan_name=plan.plan_name if plan else "",
                amount=inv.amount,
                lots=inv.lots,
                monthly_return_percentage=inv.monthly_return_percentage,
                monthly_return_amount=inv.monthly_return_amount,
                return_which=inv.return_which,
                return_balance=inv.return_balance,
                return_date=inv.return_date,
                investment_status=inv.investment_status,
                approval_status=inv.approval_status,
                investment_date=inv.investment_date,
            )
        )

    return response


# -----------------------------------
# Investment Details
# -----------------------------------
@router.get("/{id}", response_model=InvestmentResponse)
def investment_details(
    id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    investment = (
        db.query(Investment)
        .filter(
            Investment.id == id,
            Investment.user_id == user.id
        )
        .first()
    )

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found"
        )

    plan = (
        db.query(InvestmentPlan)
        .filter(
            InvestmentPlan.id == investment.investment_plan_id
        )
        .first()
    )
    return_type = (
        db.query(ReturnType)
        .filter(
            ReturnType.id == investment.return_type_id
        )
        .first()
    )

    return InvestmentResponse(
        id=investment.id,
        investment_id=investment.investment_id,
        return_type=return_type.return_type if return_type else "",
        plan_name=plan.plan_name,
        amount=investment.amount,
        lots=investment.lots,
        monthly_return_percentage=investment.monthly_return_percentage,
        monthly_return_amount=investment.monthly_return_amount,
        return_which=investment.return_which,
        return_balance=investment.return_balance,
        return_date=investment.return_date,
        investment_status=investment.investment_status,
        approval_status=investment.approval_status,
        investment_date=investment.investment_date,
    )