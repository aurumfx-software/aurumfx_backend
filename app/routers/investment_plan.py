from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import InvestmentPlan
from app.schemas import (
    InvestmentPlanCreate,
    InvestmentPlanUpdate,
    InvestmentPlanResponse
)
from app.dependencies import get_current_admin

router = APIRouter(
    prefix="/investment-plans",
    tags=["Investment Plans"]
)

@router.post(
    "/",
    response_model=InvestmentPlanResponse
)
def create_plan(
    plan: InvestmentPlanCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):

    existing = db.query(InvestmentPlan).filter(
        InvestmentPlan.plan_name == plan.plan_name
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Plan already exists"
        )

    new_plan = InvestmentPlan(
        plan_name=plan.plan_name,
        duration_months=plan.duration_months,
        return_percentage=plan.return_percentage,
        minimum_amount=plan.minimum_amount,
        # maximum_amount=plan.maximum_amount,
        commission_percentage=plan.commission_percentage,
        admin_fee_percentage=plan.admin_fee_percentage,
        status=True
        
        
    )

    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)

    return new_plan

@router.get(
    "/",
    response_model=list[InvestmentPlanResponse]
)
def get_plans(
    db: Session = Depends(get_db)
):

    return db.query(
        InvestmentPlan
    ).all()

@router.get(
    "/{plan_id}",
    response_model=InvestmentPlanResponse
)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db)
):

    plan = db.query(
        InvestmentPlan
    ).filter(
        InvestmentPlan.id == plan_id
    ).first()

    if not plan:
        raise HTTPException(
            status_code=404,
            detail="Plan not found"
        )

    return plan

@router.put(
    "/{plan_id}",
    response_model=InvestmentPlanResponse
)
def update_plan(
    plan_id: int,
    data: InvestmentPlanUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):

    plan = db.query(
        InvestmentPlan
    ).filter(
        InvestmentPlan.id == plan_id
    ).first()

    if not plan:
        raise HTTPException(
            status_code=404,
            detail="Plan not found"
        )

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(plan, key, value)

    db.commit()
    db.refresh(plan)

    return plan

@router.delete("/{plan_id}")
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):

    plan = db.query(
        InvestmentPlan
    ).filter(
        InvestmentPlan.id == plan_id
    ).first()

    if not plan:
        raise HTTPException(
            status_code=404,
            detail="Plan not found"
        )

    db.delete(plan)
    db.commit()

    return {
        "message": "Plan deleted successfully"
    }