from sqlalchemy.orm import Session

from app.models import AdminNotification, UserNotification


def create_admin_notification(
    db: Session,
    notification_type: str,
    title: str,
    message: str,
    reference_id: int | None = None,
    reference_type: str | None = None,
):
    notification = AdminNotification(
        notification_type=notification_type,
        title=title,
        message=message,
        reference_id=reference_id,
        reference_type=reference_type,
        is_read=False,
    )

    db.add(notification)

    return notification

# ============================================================
# USER NOTIFICATION
# ============================================================

def create_user_notification(
    db: Session,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    reference_id: int | None = None,
    reference_type: str | None = None,
):

    notification = UserNotification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        reference_id=reference_id,
        reference_type=reference_type,
        is_read=False,
    )

    db.add(notification)

    return notification