from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user

from app.models import UserNotification


router = APIRouter(
    prefix="/user/notifications",
    tags=["User Notifications"],
)


# ============================================================
# GET MY NOTIFICATIONS
# ============================================================

@router.get("/")
def get_my_notifications(
    db: Session = Depends(get_db),

    current_user: str = Depends(get_current_user),
):

    notifications = (
        db.query(UserNotification)
        .filter(
            UserNotification.user_id == current_user
        )
        .order_by(
            UserNotification.created_at.desc()
        )
        .limit(50)
        .all()
    )

    return {
        "notifications": [
            {
                "id": notification.id,
                "type": notification.notification_type,
                "title": notification.title,
                "message": notification.message,
                "reference_id": notification.reference_id,
                "reference_type": notification.reference_type,
                "is_read": notification.is_read,
                "created_at": notification.created_at,
            }
            for notification in notifications
        ]
    }


# ============================================================
# UNREAD COUNT
# ============================================================

@router.get("/unread-count")
def get_my_unread_notification_count(
    db: Session = Depends(get_db),

    current_user: str = Depends(get_current_user),
):

    count = (
        db.query(UserNotification)
        .filter(
            UserNotification.user_id == current_user,
            UserNotification.is_read == False,
        )
        .count()
    )

    return {
        "unread_count": count
    }


# ============================================================
# MARK ONE AS READ
# ============================================================

@router.patch("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,

    db: Session = Depends(get_db),

    current_user: str = Depends(get_current_user),
):

    notification = (
        db.query(UserNotification)
        .filter(
            UserNotification.id == notification_id,
            UserNotification.user_id == current_user,
        )
        .first()
    )

    if not notification:

        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    notification.is_read = True

    db.commit()

    return {
        "message": "Notification marked as read",
        "notification_id": notification.id,
    }


# ============================================================
# MARK ALL AS READ
# ============================================================

@router.patch("/read-all")
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),

    current_user: str = Depends(get_current_user),
):

    updated_count = (
        db.query(UserNotification)
        .filter(
            UserNotification.user_id == current_user,
            UserNotification.is_read == False,
        )
        .update(
            {
                UserNotification.is_read: True
            },
            synchronize_session=False,
        )
    )

    db.commit()

    return {
        "message": "All notifications marked as read",
        "updated_count": updated_count,
    }