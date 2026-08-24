from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import ReturnDateSetting
from app.schemas import (
    ReturnDateSettingCreate,
    ReturnDateSettingUpdate,
    ReturnDateSettingResponse,
)


router = APIRouter(
    prefix="/admin/return-date-settings",
    tags=["Admin Return Date Settings"]
)
#-----------------------------------------------------------------------------------------------
# Helper for validation
#-----------------------------------------------------------------------------------------------
def validate_days(
    from_day: int,
    to_day: int,
    payout_day: int
):
    if from_day > to_day:
        raise HTTPException(
            status_code=400,
            detail="from_day cannot be greater than to_day"
        )

    if payout_day < 1 or payout_day > 31:
        raise HTTPException(
            status_code=400,
            detail="payout_day must be between 1 and 31"
        )

#-----------------------------------------------------------------------------------------------
# Create API
#-----------------------------------------------------------------------------------------------

@router.post(
    "/",
    response_model=ReturnDateSettingResponse
)
def create_return_date_setting(
    data: ReturnDateSettingCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):

    validate_days(
        data.from_day,
        data.to_day,
        data.payout_day
    )

    # Check overlapping range
    existing = (
        db.query(ReturnDateSetting)
        .filter(
            ReturnDateSetting.status == True,
            ReturnDateSetting.from_day <= data.to_day,
            ReturnDateSetting.to_day >= data.from_day
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Day range overlaps with existing setting "
                f"{existing.from_day}-{existing.to_day}"
            )
        )

    setting = ReturnDateSetting(
        from_day=data.from_day,
        to_day=data.to_day,
        payout_day=data.payout_day,
        status=data.status
    )

    db.add(setting)
    db.commit()
    db.refresh(setting)

    return setting

#-----------------------------------------------------------------------------------------------
# Get all settings
#-----------------------------------------------------------------------------------------------

@router.get(
    "/",
    response_model=list[ReturnDateSettingResponse]
)
def get_return_date_settings(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):

    return (
        db.query(ReturnDateSetting)
        .order_by(ReturnDateSetting.from_day.asc())
        .all()
    )

#-----------------------------------------------------------------------------------------------
# Get single setting
#-----------------------------------------------------------------------------------------------
@router.get(
    "/{setting_id}",
    response_model=ReturnDateSettingResponse
)
def get_return_date_setting(
    setting_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):

    setting = (
        db.query(ReturnDateSetting)
        .filter(ReturnDateSetting.id == setting_id)
        .first()
    )

    if not setting:
        raise HTTPException(
            status_code=404,
            detail="Return date setting not found"
        )

    return setting
#-----------------------------------------------------------------------------------------------
# Update API
#-----------------------------------------------------------------------------------------------

@router.put(
    "/{setting_id}",
    response_model=ReturnDateSettingResponse
)
def update_return_date_setting(
    setting_id: int,
    data: ReturnDateSettingUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):

    setting = (
        db.query(ReturnDateSetting)
        .filter(ReturnDateSetting.id == setting_id)
        .first()
    )

    if not setting:
        raise HTTPException(
            status_code=404,
            detail="Return date setting not found"
        )

    from_day = (
        data.from_day
        if data.from_day is not None
        else setting.from_day
    )

    to_day = (
        data.to_day
        if data.to_day is not None
        else setting.to_day
    )

    payout_day = (
        data.payout_day
        if data.payout_day is not None
        else setting.payout_day
    )

    validate_days(
        from_day,
        to_day,
        payout_day
    )

    # Check overlap with other settings
    existing = (
        db.query(ReturnDateSetting)
        .filter(
            ReturnDateSetting.id != setting_id,
            ReturnDateSetting.status == True,
            ReturnDateSetting.from_day <= to_day,
            ReturnDateSetting.to_day >= from_day
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Day range overlaps with existing setting "
                f"{existing.from_day}-{existing.to_day}"
            )
        )

    setting.from_day = from_day
    setting.to_day = to_day
    setting.payout_day = payout_day

    if data.status is not None:
        setting.status = data.status

    db.commit()
    db.refresh(setting)

    return setting

#-----------------------------------------------------------------------------------------------
# Delete API
#-----------------------------------------------------------------------------------------------

@router.delete("/{setting_id}")
def delete_return_date_setting(
    setting_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):

    setting = (
        db.query(ReturnDateSetting)
        .filter(ReturnDateSetting.id == setting_id)
        .first()
    )

    if not setting:
        raise HTTPException(
            status_code=404,
            detail="Return date setting not found"
        )

    setting.status = False

    db.commit()

    return {
        "message": "Return date setting disabled successfully"
    }