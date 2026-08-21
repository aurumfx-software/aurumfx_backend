from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User

from app.services.user_genealogy import (
    get_full_genealogy,
    get_user_genealogy,
    get_user_genealogy_list,
)


router = APIRouter(
    prefix="/admin/genealogy",
    tags=["Admin Genealogy"]
)


# ============================================================
# ADMIN AUTH
# ============================================================

def get_admin_user(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    admin = (
        db.query(User)
        .filter(
            User.user_id == current_user
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if admin.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return admin


# ============================================================
# COMPLETE GENEALOGY TREE
# ============================================================

@router.get("/")
def all_genealogy(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    result = get_full_genealogy(db)

    if result is None:
        return {}

    return result


# ============================================================
# COMPLETE GENEALOGY FLAT LIST
# ============================================================

@router.get("/list/all")
def all_genealogy_list(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Get all users in genealogy as a flat list.
    """

    result = get_user_genealogy_list(
        db,
        admin.user_id
    )

    if result is None:
        return []

    return result


# ============================================================
# GENEALOGY BY USER ID
# ============================================================

@router.get("/{user_id}")
def genealogy(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    result = get_user_genealogy(
        db,
        user_id
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return result


# ============================================================
# GENEALOGY LIST BY USER ID
# ============================================================

@router.get("/{user_id}/list")
def genealogy_list(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    result = get_user_genealogy_list(
        db,
        user_id
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return result