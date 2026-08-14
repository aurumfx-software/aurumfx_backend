from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.database import get_db
from app.models import User, LotSetting
from sqlalchemy.orm import Session
from app.schemas import (
    LotSettingCreate,
    LotSettingUpdate,
    LotSettingResponse,
)

def get_admin(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.user_id == current_user
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    return user


router = APIRouter(
    prefix="/admin/lots",
    tags=["Admin Lots"],
    dependencies=[Depends(get_admin)]
)


@router.post(
    "/",
    response_model=LotSettingResponse
)
def create_lot(
    data: LotSettingCreate,
    db: Session = Depends(get_db)
):
# Check if  lot already exists
    # existing_lot = db.query(LotSetting).first()

    # if existing_lot:
    #     raise HTTPException(
    #         status_code=400,
    #         detail="Lot is already configured. Please update the existing Lot."
    #     )

    # Create  lot only if no record exists
# Check if Lot already exists
    existing_fee = db.query(LotSetting).first()

    if existing_fee:
        raise HTTPException(
            status_code=400,
            detail="Lot is already configured. Please update the existing admin fee."
        )

    # Create  lot only if no record exists
        
    lot = LotSetting(
        lot_number=data.lot_number,
        amount=data.amount,
        status=data.status
    )

    db.add(lot)
    db.commit()
    db.refresh(lot)

    return lot


@router.get(
    "/",
    response_model=list[LotSettingResponse]
)
def get_lots(
    db: Session = Depends(get_db)
):

    return db.query(LotSetting).all()


@router.get(
    "/{lot_id}",
    response_model=LotSettingResponse
)
def get_lot(
    lot_id:int,
    db:Session=Depends(get_db)
):

    lot = db.query(LotSetting).filter(
        LotSetting.id == lot_id
    ).first()

    if not lot:
        raise HTTPException(
            status_code=404,
            detail="Lot not found"
        )

    return lot


@router.put(
    "/{lot_id}",
    response_model=LotSettingResponse
)
def update_lot(
    lot_id:int,
    data:LotSettingUpdate,
    db:Session=Depends(get_db)
):

    lot = db.query(LotSetting).filter(
        LotSetting.id == lot_id
    ).first()

    if not lot:
        raise HTTPException(
            status_code=404,
            detail="Lot not found"
        )


    if data.lot_number:
        lot.lot_number=data.lot_number

    if data.amount:
        lot.amount=data.amount

    if data.status is not None:
        lot.status=data.status


    db.commit()
    db.refresh(lot)

    return lot



@router.delete(
    "/{lot_id}"
)
def delete_lot(
    lot_id:int,
    db:Session=Depends(get_db)
):

    lot=db.query(LotSetting).filter(
        LotSetting.id==lot_id
    ).first()


    if not lot:
        raise HTTPException(
            status_code=404,
            detail="Lot not found"
        )


    db.delete(lot)
    db.commit()


    return {
        "message":"Lot deleted successfully"
    }