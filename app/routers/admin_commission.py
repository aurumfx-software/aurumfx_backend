# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session

# from app.database import get_db
# from app.models import User, LotSetting
# from app.schemas import (
#     LotSettingCreate,
#     LotSettingUpdate,
#     LotSettingResponse,
# )
# from app.core.security import get_current_user


# # ------------------------------------------------------------------
# # Admin Authentication
# # ------------------------------------------------------------------
# def get_admin(
#     current_user: str = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     user = (
#         db.query(User)
#         .filter(User.user_id == current_user)
#         .first()
#     )

#     if not user:
#         raise HTTPException(
#             status_code=404,
#             detail="User not found"
#         )

#     if user.role != "ADMIN":
#         raise HTTPException(
#             status_code=403,
#             detail="Admin only"
#         )

#     return user


# # ------------------------------------------------------------------
# # Router
# # ------------------------------------------------------------------
# router = APIRouter(
#     prefix="/admin/lot-settings",
#     tags=["Admin Lot Settings"],
#     dependencies=[Depends(get_admin)]
# )


# # ------------------------------------------------------------------
# # Create Lot
# # ------------------------------------------------------------------
# @router.post(
#     "/",
#     response_model=LotSettingResponse
# )
# def create_lot(
#     data: LotSettingCreate,
#     db: Session = Depends(get_db),
# ):
#     existing = (
#         db.query(LotSetting)
#         .filter(LotSetting.lot_number == data.lot_number)
#         .first()
#     )

#     if existing:
#         raise HTTPException(
#             status_code=400,
#             detail="Lot number already exists"
#         )

#     lot = LotSetting(
#         lot_number=data.lot_number,
#         amount=data.amount,
#         status=data.status
#     )

#     db.add(lot)
#     db.commit()
#     db.refresh(lot)

#     return lot


# # ------------------------------------------------------------------
# # Get All Lots
# # ------------------------------------------------------------------
# @router.get(
#     "/",
#     response_model=list[LotSettingResponse]
# )
# def get_lots(
#     db: Session = Depends(get_db),
# ):
#     return db.query(LotSetting).all()


# # ------------------------------------------------------------------
# # Get Single Lot
# # ------------------------------------------------------------------
# @router.get(
#     "/{lot_id}",
#     response_model=LotSettingResponse
# )
# def get_lot(
#     lot_id: int,
#     db: Session = Depends(get_db),
# ):
#     lot = (
#         db.query(LotSetting)
#         .filter(LotSetting.id == lot_id)
#         .first()
#     )

#     if not lot:
#         raise HTTPException(
#             status_code=404,
#             detail="Lot not found"
#         )

#     return lot


# # ------------------------------------------------------------------
# # Update Lot
# # ------------------------------------------------------------------
# @router.put(
#     "/{lot_id}",
#     response_model=LotSettingResponse
# )
# def update_lot(
#     lot_id: int,
#     data: LotSettingUpdate,
#     db: Session = Depends(get_db),
# ):
#     lot = (
#         db.query(LotSetting)
#         .filter(LotSetting.id == lot_id)
#         .first()
#     )

#     if not lot:
#         raise HTTPException(
#             status_code=404,
#             detail="Lot not found"
#         )

#     if data.lot_number is not None:
#         lot.lot_number = data.lot_number

#     if data.amount is not None:
#         lot.amount = data.amount

#     if data.status is not None:
#         lot.status = data.status

#     db.commit()
#     db.refresh(lot)

#     return lot


# # ------------------------------------------------------------------
# # Delete Lot
# # ------------------------------------------------------------------
# @router.delete("/{lot_id}")
# def delete_lot(
#     lot_id: int,
#     db: Session = Depends(get_db),
# ):
#     lot = (
#         db.query(LotSetting)
#         .filter(LotSetting.id == lot_id)
#         .first()
#     )

#     if not lot:
#         raise HTTPException(
#             status_code=404,
#             detail="Lot not found"
#         )

#     db.delete(lot)
#     db.commit()

#     return {
#         "message": "Lot deleted successfully"
#     }