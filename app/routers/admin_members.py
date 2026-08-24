from datetime import date, timedelta

from fastapi import (
    APIRouter,
    Depends,
    Query,
    HTTPException,
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)

from jose import jwt, JWTError

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import User, RankSetting
from app.schemas import UserStatusUpdateRequest
from app.utils.jwt import create_access_token
from app.utils.jwt import (
    create_access_token,
    decode_access_token,
)

security = HTTPBearer()

router = APIRouter(
    prefix="/api/admin/members",
    tags=["Admin - Member Management"]
)


@router.get("/")
def get_members(
    start_date: date | None = Query(
        None,
        description="Filter members joined from this date"
    ),
    end_date: date | None = Query(
        None,
        description="Filter members joined until this date"
    ),
    user_id: str | None = Query(
        None,
        description="Search by user ID"
    ),
    rank: str | None = Query(
        None,
        description="Filter by rank"
    ),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    query = (
    db.query(
        User.id,

        User.user_id,

        func.concat(
            User.first_name,
            " ",
            User.last_name
        ).label("fullname"),

        User.profile_image,

        RankSetting.rank_name.label("rank"),

        func.date(User.created_at).label("join_date"),
    )
    .outerjoin(
        RankSetting,
        RankSetting.id == User.current_rank_id
    )
)

    # User ID filter
    if user_id:
        query = query.filter(
            User.user_id.ilike(f"%{user_id}%")
        )

    # Start date
    if start_date:
        query = query.filter(
            User.created_at >= start_date
        )

    # End date
    if end_date:
        query = query.filter(
            User.created_at < end_date + timedelta(days=1)
        )

    # Rank filter
    if rank:
        query = query.filter(
            RankSetting.name.ilike(f"%{rank}%")
        )

    users = (
        query
        .order_by(User.created_at.desc())
        .all()
    )

    return [
        {
            "id": user.id,
            "user_id": user.user_id,
            "fullname": user.fullname,
            "profile_image": user.profile_image,
            "rank": user.rank or "No Rank",
            "join_date": user.join_date,
        }
        for user in users
    ]

# @router.post("/members/{user_id}/impersonate")
# def impersonate_user(
#     user_id: str,
#     current_admin=Depends(get_current_admin),
#     db: Session = Depends(get_db),
# ):
#     user = (
#         db.query(User)
#         .filter(User.user_id == user_id)
#         .first()
#     )

#     if not user:
#         raise HTTPException(
#             status_code=404,
#             detail="User not found"
#         )

#     # Create temporary token
#     token = create_access_token(
#         data={
#             "sub": user.user_id,
#             "role": "USER",
#             "impersonated_by": current_admin.user_id,
#         }
#     )

#     return {
#         "access_token": token,
#         "token_type": "bearer",
#         "user_id": user.user_id,
#     }

# # ==========================================================
# # BLOCK / ACTIVATE USER
# # ==========================================================

@router.post("/members/{user_id}/impersonate")
def impersonate_user(
    user_id: str,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    # ======================================================
    # FIND USER
    # ======================================================

    user = (
        db.query(User)
        .filter(
            User.user_id == user_id,
            User.role == "USER",
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # ======================================================
    # CHECK USER STATUS
    # ======================================================

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=403,
            detail="Cannot impersonate a blocked or inactive user.",
        )

    # ======================================================
    # CREATE IMPERSONATION TOKEN
    # ======================================================

    token = create_access_token(
        data={
            "sub": user.user_id,
            "role": "USER",

            # IMPORTANT
            "is_impersonation": True,

            # Original admin
            "impersonated_by": current_admin.user_id,

            # Original role
            "original_role": "ADMIN",
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "role": "USER",
        "is_impersonation": True,
        "impersonated_by": current_admin.user_id,
    }

@router.post("/switch-back")
def switch_back_to_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    # ======================================================
    # DECODE TOKEN
    # ======================================================

    payload = decode_access_token(
        credentials.credentials
    )

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    # DEBUG - temporarily keep this
    print("SWITCH BACK PAYLOAD:", payload)

    # ======================================================
    # VERIFY IMPERSONATION
    # ======================================================

    if payload.get("is_impersonation") is not True:
        raise HTTPException(
            status_code=403,
            detail="This is not an impersonation session."
        )

    # ======================================================
    # GET ORIGINAL ADMIN
    # ======================================================

    admin_user_id = payload.get("impersonated_by")

    if not admin_user_id:
        raise HTTPException(
            status_code=403,
            detail="Original admin information not found."
        )

    # ======================================================
    # FIND ADMIN
    # ======================================================

    admin = (
        db.query(User)
        .filter(
            User.user_id == admin_user_id,
            User.role == "ADMIN",
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=403,
            detail="Original admin account not found."
        )

    # ======================================================
    # CHECK ADMIN STATUS
    # ======================================================

    if admin.status != "ACTIVE":
        raise HTTPException(
            status_code=403,
            detail="Admin account is not active."
        )

    # ======================================================
    # CREATE ADMIN TOKEN
    # ======================================================

    admin_token = create_access_token(
        data={
            "sub": admin.user_id,
            "role": "ADMIN",
        }
    )

    return {
        "access_token": admin_token,
        "token_type": "bearer",
        "user_id": admin.user_id,
        "role": "ADMIN",
    }

@router.patch("/{user_id}/status")
def update_user_status(
    user_id: str,
    data: UserStatusUpdateRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):

    # ======================================================
    # FIND USER
    # ======================================================

    user = (
        db.query(User)
        .filter(
            User.user_id == user_id
        )
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # ======================================================
    # NORMALIZE STATUS
    # ======================================================

    status_value = (
        data.status
        .strip()
        .upper()
    )

    # ======================================================
    # VALIDATE STATUS
    # ======================================================

    if status_value not in {
        "ACTIVE",
        "BLOCKED",
    }:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid status. "
                "Use ACTIVE or BLOCKED."
            ),
        )

    # ======================================================
    # UPDATE
    # ======================================================

    user.status = status_value

    db.commit()
    db.refresh(user)

    # ======================================================
    # RESPONSE
    # ======================================================

    return {
        "message": (
            "User activated successfully."
            if status_value == "ACTIVE"
            else "User blocked successfully."
        ),

        "user_id": user.user_id,

        "status": user.status,
    }