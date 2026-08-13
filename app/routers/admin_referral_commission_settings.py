from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    User,
    InvestmentPlan,
    ReferralCommissionSetting
)

from app.schemas import (
    ReferralCommissionSettingCreate,
    ReferralCommissionSettingUpdate,
    ReferralCommissionSettingResponse
)

from app.core.security import get_current_user


router = APIRouter(
    prefix="/admin/referral-commission-settings",
    tags=["Admin Referral Commission settings"]
)

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

def check_overlapping_slab(
    db: Session,
    investment_plan_id: int,
    minimum_amount: float,
    maximum_amount: float | None,
    exclude_id: int | None = None
):

    query = (
        db.query(ReferralCommissionSetting)
        .filter(
            ReferralCommissionSetting.investment_plan_id
            == investment_plan_id,
            ReferralCommissionSetting.status == True
        )
    )

    if exclude_id:
        query = query.filter(
            ReferralCommissionSetting.id != exclude_id
        )

    existing_settings = query.all()

    for setting in existing_settings:

        existing_min = setting.minimum_amount
        existing_max = setting.maximum_amount

        # New range has no upper limit
        if maximum_amount is None:

            if existing_max is None:
                return True

            if minimum_amount <= existing_max:
                return True

        # Existing range has no upper limit
        elif existing_max is None:

            if maximum_amount >= existing_min:
                return True

        # Both ranges have upper limits
        else:

            if (
                minimum_amount <= existing_max
                and maximum_amount >= existing_min
            ):
                return True

    return False

#-------------------------------------------------------------------------------------------
# Create referral commission settings
#-------------------------------------------------------------------------------------------
@router.post(
    "",
    response_model=ReferralCommissionSettingResponse
)
def create_referral_commission_setting(
    data: ReferralCommissionSettingCreate,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    # ----------------------------------------
    # Validate amount range
    # ----------------------------------------

    if (
        data.maximum_amount is not None
        and data.maximum_amount <= data.minimum_amount
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Maximum amount must be greater "
                "than minimum amount."
            )
        )

    # ----------------------------------------
    # Check investment plan
    # ----------------------------------------

    plan = (
        db.query(InvestmentPlan)
        .filter(
            InvestmentPlan.id == data.investment_plan_id
        )
        .first()
    )

    if not plan:
        raise HTTPException(
            status_code=404,
            detail="Investment plan not found"
        )

    # ----------------------------------------
    # Check overlapping slabs
    # ----------------------------------------

    if data.status:

        overlapping = check_overlapping_slab(
            db=db,
            investment_plan_id=data.investment_plan_id,
            minimum_amount=data.minimum_amount,
            maximum_amount=data.maximum_amount
        )

        if overlapping:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This amount range overlaps "
                    "with an existing active referral "
                    "commission setting."
                )
            )

    # ----------------------------------------
    # Create
    # ----------------------------------------

    setting = ReferralCommissionSetting(
        investment_plan_id=data.investment_plan_id,
        minimum_amount=data.minimum_amount,
        maximum_amount=data.maximum_amount,
        commission_percentage=data.commission_percentage,
        status=data.status
    )

    db.add(setting)
    db.commit()
    db.refresh(setting)

    return {
        "id": setting.id,
        "investment_plan_id": setting.investment_plan_id,
        "plan_name": plan.plan_name,
        "minimum_amount": setting.minimum_amount,
        "maximum_amount": setting.maximum_amount,
        "commission_percentage": setting.commission_percentage,
        "status": setting.status,
        "created_at": setting.created_at,
        "updated_at": setting.updated_at
    }

#-------------------------------------------------------------------------------------------------------
# Get all settings
#-------------------------------------------------------------------------------------------------------
@router.get(
    "",
    response_model=list[ReferralCommissionSettingResponse]
)
def get_referral_commission_settings(
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    results = (
        db.query(
            ReferralCommissionSetting,
            InvestmentPlan
        )
        .join(
            InvestmentPlan,
            InvestmentPlan.id
            == ReferralCommissionSetting.investment_plan_id
        )
        .order_by(
            ReferralCommissionSetting.investment_plan_id,
            ReferralCommissionSetting.minimum_amount
        )
        .all()
    )

    response = []

    for setting, plan in results:

        response.append(
            {
                "id": setting.id,
                "investment_plan_id": setting.investment_plan_id,
                "plan_name": plan.plan_name,
                "minimum_amount": setting.minimum_amount,
                "maximum_amount": setting.maximum_amount,
                "commission_percentage":
                    setting.commission_percentage,
                "status": setting.status,
                "created_at": setting.created_at,
                "updated_at": setting.updated_at
            }
        )

    return response
#-----------------------------------------------------------------------------------------------------
# Get single settings
#-----------------------------------------------------------------------------------------------------

@router.get(
    "/{id}",
    response_model=ReferralCommissionSettingResponse
)
def get_referral_commission_setting(
    id: int,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    result = (
        db.query(
            ReferralCommissionSetting,
            InvestmentPlan
        )
        .join(
            InvestmentPlan,
            InvestmentPlan.id
            == ReferralCommissionSetting.investment_plan_id
        )
        .filter(
            ReferralCommissionSetting.id == id
        )
        .first()
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Referral commission setting not found"
        )

    setting, plan = result

    return {
        "id": setting.id,
        "investment_plan_id": setting.investment_plan_id,
        "plan_name": plan.plan_name,
        "minimum_amount": setting.minimum_amount,
        "maximum_amount": setting.maximum_amount,
        "commission_percentage":
            setting.commission_percentage,
        "status": setting.status,
        "created_at": setting.created_at,
        "updated_at": setting.updated_at
    }

#------------------------------------------------------------------------------------------------------
# Update settings
#------------------------------------------------------------------------------------------------------

@router.put(
    "/{id}",
    response_model=ReferralCommissionSettingResponse
)
def update_referral_commission_setting(
    id: int,
    data: ReferralCommissionSettingUpdate,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    setting = (
        db.query(ReferralCommissionSetting)
        .filter(
            ReferralCommissionSetting.id == id
        )
        .first()
    )

    if not setting:
        raise HTTPException(
            status_code=404,
            detail="Referral commission setting not found"
        )

    # ----------------------------------------
    # Validate range
    # ----------------------------------------

    if (
        data.maximum_amount is not None
        and data.maximum_amount <= data.minimum_amount
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Maximum amount must be greater "
                "than minimum amount."
            )
        )

    # ----------------------------------------
    # Check plan
    # ----------------------------------------

    plan = (
        db.query(InvestmentPlan)
        .filter(
            InvestmentPlan.id == data.investment_plan_id
        )
        .first()
    )

    if not plan:
        raise HTTPException(
            status_code=404,
            detail="Investment plan not found"
        )

    # ----------------------------------------
    # Check overlapping slab
    # ----------------------------------------

    if data.status:

        overlapping = check_overlapping_slab(
            db=db,
            investment_plan_id=data.investment_plan_id,
            minimum_amount=data.minimum_amount,
            maximum_amount=data.maximum_amount,
            exclude_id=id
        )

        if overlapping:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This amount range overlaps "
                    "with another active referral "
                    "commission setting."
                )
            )

    # ----------------------------------------
    # Update
    # ----------------------------------------

    setting.investment_plan_id = (
        data.investment_plan_id
    )

    setting.minimum_amount = (
        data.minimum_amount
    )

    setting.maximum_amount = (
        data.maximum_amount
    )

    setting.commission_percentage = (
        data.commission_percentage
    )

    setting.status = data.status

    db.commit()
    db.refresh(setting)

    return {
        "id": setting.id,
        "investment_plan_id": setting.investment_plan_id,
        "plan_name": plan.plan_name,
        "minimum_amount": setting.minimum_amount,
        "maximum_amount": setting.maximum_amount,
        "commission_percentage":
            setting.commission_percentage,
        "status": setting.status,
        "created_at": setting.created_at,
        "updated_at": setting.updated_at
    }

#------------------------------------------------------------------------------------
# Delete settings
#------------------------------------------------------------------------------------

@router.delete("/{id}")
def delete_referral_commission_setting(
    id: int,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    setting = (
        db.query(ReferralCommissionSetting)
        .filter(
            ReferralCommissionSetting.id == id
        )
        .first()
    )

    if not setting:
        raise HTTPException(
            status_code=404,
            detail="Referral commission setting not found"
        )

    db.delete(setting)
    db.commit()

    return {
        "message":
            "Referral commission setting deleted successfully"
    }