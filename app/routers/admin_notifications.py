from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin

from app.models import AdminNotification


router = APIRouter(
    prefix="/admin/notifications",
    tags=["Admin Notifications"],
)


# ============================================================
# GET NOTIFICATIONS
# ============================================================

@router.get("/")
def get_admin_notifications(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):

    notifications = (
        db.query(AdminNotification)
        .order_by(
            AdminNotification.created_at.desc()
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
# GET UNREAD COUNT
# ============================================================

@router.get("/unread-count")
def get_unread_notification_count(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):

    count = (
        db.query(AdminNotification)
        .filter(
            AdminNotification.is_read == False
        )
        .count()
    )

    return {
        "unread_count": count
    }


# ============================================================
# MARK SINGLE NOTIFICATION AS READ
# ============================================================

@router.patch("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,

    db: Session = Depends(get_db),

    admin=Depends(get_current_admin),
):

    notification = (
        db.query(AdminNotification)
        .filter(
            AdminNotification.id == notification_id
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

    admin=Depends(get_current_admin),
):

    updated_count = (
        db.query(AdminNotification)
        .filter(
            AdminNotification.is_read == False
        )
        .update(
            {
                AdminNotification.is_read: True
            },
            synchronize_session=False,
        )
    )

    db.commit()

    return {
        "message": "All notifications marked as read",
        "updated_count": updated_count,
    }