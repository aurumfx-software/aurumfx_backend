from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, AdminFeeSetting, InvestmentPlan
from app.schemas import (
    AdminFeeCreate,
    AdminFeeUpdate,
    AdminFeeResponse
)
from app.core.security import get_current_user


router = APIRouter(
    prefix="/admin/admin-fees",
    tags=["Admin Fee"]
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
# Create admin fee
# --------------------------------------------------

@router.post(
    "",
    response_model=AdminFeeResponse
)
def create_admin_fee(
    data: AdminFeeCreate,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):
    # Check if admin fee already exists
    existing_fee = db.query(AdminFeeSetting).first()

    if existing_fee:
        raise HTTPException(
            status_code=400,
            detail="Admin fee is already configured. Please update the existing admin fee."
        )

    # Create admin fee only if no record exists
    admin_fee = AdminFeeSetting(
        fee_percentage=data.fee_percentage,
        status=data.status
    )

    db.add(admin_fee)
    db.commit()
    db.refresh(admin_fee)

    return {
        "id": admin_fee.id,
        "fee_percentage": admin_fee.fee_percentage,
        "status": admin_fee.status,
        "created_at": admin_fee.created_at,
        "updated_at": admin_fee.updated_at
    }

# --------------------------------------------------
# Get all admin fee
# --------------------------------------------------
@router.get(
    "",
    response_model=list[AdminFeeResponse]
)
def get_admin_fees(
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    fees = (
        db.query(
            AdminFeeSetting
            # InvestmentPlan
        )
        # .join(
        #     InvestmentPlan,
        #     InvestmentPlan.id
        #     == AdminFeeSetting.investment_plan_id
        # )
        .order_by(
            AdminFeeSetting.id.desc()
        )
        .all()
    )

    response = []

    for fee in fees:

        response.append(
            {
                "id": fee.id,
                # "investment_plan_id": fee.investment_plan_id,
                # "plan_name": plan.plan_name,
                "fee_percentage": fee.fee_percentage,
                "status": fee.status,
                "created_at": fee.created_at,
                "updated_at": fee.updated_at
            }
        )

    return response

# --------------------------------------------------
# Get single admin fee
# --------------------------------------------------
router.get(
    "/{id}",
    response_model=AdminFeeResponse
)
def get_admin_fee(
    id: int,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    result = (
        db.query(
            AdminFeeSetting,
            # InvestmentPlan
        )
        # .join(
        #     InvestmentPlan,
        #     InvestmentPlan.id
        #     == AdminFeeSetting.investment_plan_id
        # )
        .filter(
            AdminFeeSetting.id == id
        )
        .first()
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Admin fee not found"
        )

    fee, plan = result

    return {
        "id": fee.id,
        # "investment_plan_id": fee.investment_plan_id,
        # "plan_name": plan.plan_name,
        "fee_percentage": fee.fee_percentage,
        "status": fee.status,
        "created_at": fee.created_at,
        "updated_at": fee.updated_at
    }

# --------------------------------------------------
# update admin fee
# --------------------------------------------------
@router.put(
    "/{id}",
    response_model=AdminFeeResponse
)
def update_admin_fee(
    id: int,
    data: AdminFeeUpdate,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    admin_fee = (
        db.query(AdminFeeSetting)
        .filter(
            AdminFeeSetting.id == id
        )
        .first()
    )

    if not admin_fee:
        raise HTTPException(
            status_code=404,
            detail="Admin fee not found"
        )

    # plan = (
    #     db.query(InvestmentPlan)
    #     .filter(
    #         InvestmentPlan.id == data.investment_plan_id
    #     )
    #     .first()
    # )

    # if not plan:
    #     raise HTTPException(
    #         status_code=404,
    #         detail="Investment plan not found"
    #     )

    # if data.status:

    #     existing_active = (
    #         db.query(AdminFeeSetting)
    #         .filter(
    #             AdminFeeSetting.investment_plan_id
    #             == data.investment_plan_id,
    #             AdminFeeSetting.status == True,
    #             AdminFeeSetting.id != id
    #         )
    #         .first()
    #     )

    #     if existing_active:
    #         raise HTTPException(
    #             status_code=400,
    #             detail=(
    #                 "An active admin fee already exists "
    #                 "for this investment plan."
    #             )
    #         )

    # admin_fee.investment_plan_id = data.investment_plan_id
    admin_fee.fee_percentage = data.fee_percentage
    admin_fee.status = data.status

    db.commit()
    db.refresh(admin_fee)

    return {
        "id": admin_fee.id,
        # "investment_plan_id": admin_fee.investment_plan_id,
        # "plan_name": plan.plan_name,
        "fee_percentage": admin_fee.fee_percentage,
        "status": admin_fee.status,
        "created_at": admin_fee.created_at,
        "updated_at": admin_fee.updated_at
    }
    



#------------------------------------------------------------------------------------------
# Delete admin fee
#------------------------------------------------------------------------------------------
@router.delete("/{id}")
def delete_admin_fee(
    id: int,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    admin_fee = (
        db.query(AdminFeeSetting)
        .filter(
            AdminFeeSetting.id == id
        )
        .first()
    )

    if not admin_fee:
        raise HTTPException(
            status_code=404,
            detail="Admin fee not found"
        )

    db.delete(admin_fee)
    db.commit()

    return {
        "message": "Admin fee deleted successfully"
    }