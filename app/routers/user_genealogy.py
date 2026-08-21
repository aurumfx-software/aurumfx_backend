from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User

from app.services.user_genealogy import (
    get_logged_in_user_genealogy,
    get_user_genealogy,
    get_user_genealogy_list,
)


router = APIRouter(
    prefix="/user/genealogy",
    tags=["User Genealogy"]
)


# ============================================================
# MY GENEALOGY
# ============================================================

@router.get("/")
def user_genealogy(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    result = get_logged_in_user_genealogy(
        db,
        current_user
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return result


# ============================================================
# MY GENEALOGY LIST
# ============================================================

@router.get("/list")
def user_genealogy_list(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    result = get_user_genealogy_list(
        db,
        current_user
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return result


# ============================================================
# GENEALOGY BY USER ID
# ============================================================

@router.get("/{user_id}")
def user_genealogy_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    # --------------------------------------------------------
    # Requested user
    # --------------------------------------------------------

    requested_user = (
        db.query(User)
        .filter(
            User.user_id == user_id,
            User.role == "USER"
        )
        .first()
    )

    if not requested_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # --------------------------------------------------------
    # Logged-in user
    # --------------------------------------------------------

    logged_user = (
        db.query(User)
        .filter(
            User.user_id == current_user
        )
        .first()
    )

    if not logged_user:
        raise HTTPException(
            status_code=404,
            detail="Logged-in user not found"
        )

    # --------------------------------------------------------
    # Same user
    # --------------------------------------------------------

    if requested_user.user_id == logged_user.user_id:
        return get_user_genealogy(
            db,
            requested_user.user_id
        )

    # --------------------------------------------------------
    # Check whether requested user is
    # inside logged-in user's genealogy
    # --------------------------------------------------------

    def is_descendant(
        parent_user: User,
        target_user_id: str
    ):
        children = (
            db.query(User)
            .filter(
                User.enroller_id == parent_user.user_id,
                User.role == "USER"
            )
            .all()
        )

        for child in children:

            if child.user_id == target_user_id:
                return True

            if is_descendant(
                child,
                target_user_id
            ):
                return True

        return False

    allowed = is_descendant(
        logged_user,
        requested_user.user_id
    )

    if not allowed:
        raise HTTPException(
            status_code=403,
            detail="You can only view users in your genealogy"
        )

    # --------------------------------------------------------
    # Return selected user's subtree
    # --------------------------------------------------------

    return get_user_genealogy(
        db,
        requested_user.user_id
    )