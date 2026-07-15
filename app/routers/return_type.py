from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ReturnType, User
from app.schemas import (
    ReturnTypeCreate,
    ReturnTypeUpdate,
    ReturnTypeResponse
)
from app.core.security import get_current_user

router = APIRouter(
    prefix="/return-types",
    tags=["Return Types"]
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

@router.post(
    "/",
    response_model=ReturnTypeResponse
)
def create_return_type(
    data: ReturnTypeCreate,
    admin=Depends(get_admin),
    db: Session = Depends(get_db)
):

    existing = (
        db.query(ReturnType)
        .filter(
            ReturnType.return_type == data.return_type
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Return Type already exists."
        )

    obj = ReturnType(

        return_type=data.return_type.upper(),

        status=True

    )

    db.add(obj)

    db.commit()

    db.refresh(obj)

    return obj

@router.get(
    "/",
    response_model=list[ReturnTypeResponse]
)
def list_return_types(

    db: Session = Depends(get_db)

):

    return db.query(ReturnType).all()

@router.get(
    "/{return_type_id}",
    response_model=ReturnTypeResponse
)
def get_return_type(

    return_type_id: int,

    db: Session = Depends(get_db)

):

    obj = (

        db.query(ReturnType)

        .filter(ReturnType.id == return_type_id)

        .first()

    )

    if not obj:

        raise HTTPException(

            status_code=404,

            detail="Return Type not found"

        )

    return obj

@router.put(
    "/{return_type_id}",
    response_model=ReturnTypeResponse
)
def update_return_type(

    return_type_id: int,

    data: ReturnTypeUpdate,

    admin=Depends(get_admin),

    db: Session = Depends(get_db)

):

    obj = (

        db.query(ReturnType)

        .filter(ReturnType.id == return_type_id)

        .first()

    )

    if not obj:

        raise HTTPException(

            status_code=404,

            detail="Return Type not found"

        )

    if data.return_type is not None:
        obj.return_type = data.return_type.upper()

    if data.status is not None:
        obj.status = data.status

    db.commit()

    db.refresh(obj)

    return obj

@router.delete("/{return_type_id}")
def delete_return_type(

    return_type_id: int,

    admin=Depends(get_admin),

    db: Session = Depends(get_db)

):

    obj = (

        db.query(ReturnType)

        .filter(ReturnType.id == return_type_id)

        .first()

    )

    if not obj:

        raise HTTPException(

            status_code=404,

            detail="Return Type not found"

        )

    db.delete(obj)

    db.commit()

    return {

        "message": "Return Type deleted successfully."

    }