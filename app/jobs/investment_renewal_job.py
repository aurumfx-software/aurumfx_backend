from app.database import SessionLocal

from app.services.investment_renewal_service import (
    send_renewal_notifications
)


def run():

    db = SessionLocal()

    try:

        count = send_renewal_notifications(db)

        print(
            f"Renewal notification job completed. "
            f"Notifications created: {count}"
        )

    except Exception as e:

        db.rollback()

        print(
            f"Renewal notification job failed: {e}"
        )

    finally:

        db.close()


if __name__ == "__main__":
    run()