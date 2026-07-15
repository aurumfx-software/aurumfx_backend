from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dateutil.relativedelta import relativedelta
from app.database import get_db
from app.models import (
    User,
    Investment,
    InvestmentPlan,
    ReturnType,
    ReturnHistory
)
from app.schemas import (
    AdminInvestmentResponse,
    InvestmentApproval,
    ReturnApprove
)
from app.core.security import get_current_user

router = APIRouter(
    prefix="/admin/investments",
    tags=["Admin Investments"]
)


# --------------------------------------------------
# Admin Authentication
# --------------------------------------------------
def get_admin(
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

    if user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only Admin can access."
        )

    return user


# --------------------------------------------------
# All Investment Requests
# --------------------------------------------------
@router.get(
    "/",
    response_model=list[AdminInvestmentResponse]
)
def all_requests(
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    investments = (
        db.query(Investment)
        .order_by(Investment.id.desc())
        .all()
    )

    response = []

    for inv in investments:

        user = db.query(User).filter(User.id == inv.user_id).first()

        plan = (
            db.query(InvestmentPlan)
            .filter(InvestmentPlan.id == inv.investment_plan_id)
            .first()
        )

        return_type = (
            db.query(ReturnType)
            .filter(ReturnType.id == inv.return_type_id)
            .first()
        )

        response.append(
            AdminInvestmentResponse(
                id=inv.id,
                investment_id=inv.investment_id,
                user_id=user.user_id,
                user_name=user.first_name,
                plan_name=plan.plan_name,
                return_type=return_type.return_type,
                amount=inv.amount,
                lots=inv.lots,
                investment_status=inv.investment_status,
                approval_status=inv.approval_status,
                investment_date=inv.investment_date
            )
        )

    return response
# --------------------------------------------------
# Pending Investments
# --------------------------------------------------
@router.get(
    "/pending",
    response_model=list[AdminInvestmentResponse]
)
def pending_investments(
    user_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    query = (
        db.query(Investment)
        .filter(
            Investment.approval_status == "PENDING"
        )
    )

    if user_id:

        user = (
            db.query(User)
            .filter(User.user_id == user_id)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        query = query.filter(
            Investment.user_id == user.id
        )

    if start_date:
        query = query.filter(
            Investment.investment_date >= start_date
        )

    if end_date:
        query = query.filter(
            Investment.investment_date <= end_date
        )

    investments = (
        query.order_by(Investment.id.desc())
        .all()
    )

    response = []

    for inv in investments:

        user = (
            db.query(User)
            .filter(User.id == inv.user_id)
            .first()
        )

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
            AdminInvestmentResponse(
                id=inv.id,
                investment_id=inv.investment_id,
                user_id=user.user_id,
                user_name=user.first_name,
                plan_name=plan.plan_name,
                return_type=return_type.return_type,
                amount=inv.amount,
                lots=inv.lots,
                investment_status=inv.investment_status,
                approval_status=inv.approval_status,
                investment_date=inv.investment_date
            )
        )

    return response

# --------------------------------------------------
# Active Investments
# --------------------------------------------------
@router.get(
    "/active",
    response_model=list[AdminInvestmentResponse]
)
def active_investments(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    query = db.query(Investment)

    query = query.filter(
        Investment.approval_status == "APPROVED",
        Investment.investment_status == "ACTIVE"
    )

    if status:
        query = query.filter(
            Investment.investment_status == status.upper()
        )

    if user_id:

        user = (
            db.query(User)
            .filter(User.user_id == user_id)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        query = query.filter(
            Investment.user_id == user.id
        )

    if start_date:
        query = query.filter(
            Investment.investment_date >= start_date
        )

    if end_date:
        query = query.filter(
            Investment.investment_date <= end_date
        )

    investments = (
        query.order_by(Investment.id.desc())
        .all()
    )

    response = []

    for inv in investments:

        user = (
            db.query(User)
            .filter(User.id == inv.user_id)
            .first()
        )

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
            AdminInvestmentResponse(
                id=inv.id,
                investment_id=inv.investment_id,
                user_id=user.user_id,
                user_name=user.first_name,
                plan_name=plan.plan_name,
                return_type=return_type.return_type,
                amount=inv.amount,
                lots=inv.lots,
                investment_status=inv.investment_status,
                approval_status=inv.approval_status,
                investment_date=inv.investment_date
            )
        )

    return response

# --------------------------------------------------
# Todays Return
#---------------------------------------------------
from datetime import date

@router.get(
    "/today-returns",
    response_model=list[AdminInvestmentResponse]
)
def today_returns(
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):
    today = date.today()

    investments = (
        db.query(Investment)
        .filter(
            Investment.return_date == today,
            Investment.approval_status == "APPROVED",
            Investment.investment_status == "ACTIVE"
        )
        .order_by(Investment.id.desc())
        .all()
    )

    response = []

    for inv in investments:

        user = db.query(User).filter(User.id == inv.user_id).first()

        plan = db.query(InvestmentPlan).filter(
            InvestmentPlan.id == inv.investment_plan_id
        ).first()

        return_type = db.query(ReturnType).filter(
            ReturnType.id == inv.return_type_id
        ).first()

        response.append(
            AdminInvestmentResponse(
                id=inv.id,
                investment_id=inv.investment_id,
                user_id=user.user_id,
                user_name=user.first_name,
                plan_name=plan.plan_name,
                return_type=return_type.return_type,
                amount=inv.amount,
                lots=inv.lots,
                investment_status=inv.investment_status,
                approval_status=inv.approval_status,
                investment_date=inv.investment_date
            )
        )

    return response
#---------------------------------------------------
#Approve Return
#---------------------------------------------------

@router.put("/{id}/approve-return")
def approve_return(
    id: int,
    data: ReturnApprove,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):
    investment = (
        db.query(Investment)
        .filter(Investment.id == id)
        .first()
    )

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found"
        )

    if investment.investment_status != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail="Investment is not active."
        )

    if investment.return_balance <= 0:
        raise HTTPException(
            status_code=400,
            detail="All returns are already completed."
        )

    history = ReturnHistory(
        investment_id=investment.id,
        user_id=investment.user_id,
        return_number=investment.return_which + 1,
        return_percentage=investment.monthly_return_percentage,
        return_amount=investment.monthly_return_amount,
        approved_date=investment.return_date,
        status="PAID",
        remarks=data.remarks
    )

    db.add(history)

    investment.return_which += 1
    investment.return_balance -= 1

    investment.return_date = (
        investment.return_date +
        relativedelta(months=1)
    )

    if investment.return_balance == 0:
        investment.investment_status = "COMPLETED"

    db.commit()

    return {
        "message": "Return approved successfully"
    }
# --------------------------------------------------
# Investment Details
# --------------------------------------------------
@router.get(
    "/{id}",
    response_model=AdminInvestmentResponse
)
def investment_details(
    id: int,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    investment = (
        db.query(Investment)
        .filter(Investment.id == id)
        .first()
    )

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found"
        )

    user = (
        db.query(User)
        .filter(User.id == investment.user_id)
        .first()
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

    return AdminInvestmentResponse(
        id=investment.id,
        investment_id=investment.investment_id,
        user_id=user.user_id,
        user_name=user.first_name,
        plan_name=plan.plan_name,
        return_type=return_type.return_type,
        amount=investment.amount,
        lots=investment.lots,
        investment_status=investment.investment_status,
        approval_status=investment.approval_status,
        investment_date=investment.investment_date
    )


# --------------------------------------------------
# Approve / Reject Investment
# --------------------------------------------------
@router.put("/{id}")
def approve_reject(
    id: int,
    data: InvestmentApproval,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    investment = (
        db.query(Investment)
        .filter(Investment.id == id)
        .first()
    )

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found"
        )

    approval = data.approval_status.upper()

    if approval not in ["APPROVED", "REJECTED"]:
        raise HTTPException(
            status_code=400,
            detail="Approval status must be APPROVED or REJECTED"
        )

    investment.approval_status = approval

    if approval == "APPROVED":
        investment.investment_status = "ACTIVE"
    else:
        investment.investment_status = "REJECTED"

    db.commit()

    return {
        "message": f"Investment {approval.lower()} successfully."
    }