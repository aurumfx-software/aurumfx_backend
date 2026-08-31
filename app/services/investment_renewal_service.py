from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import Investment, UserNotification


def send_renewal_notifications(db: Session):

    today = date.today()

    reminder_date = today + timedelta(days=15)

    print("======================================")
    print("Investment Renewal Notification")
    print("Today:", today)
    print("Reminder date:", reminder_date)
    print("======================================")

    investments = (
        db.query(Investment)
        .filter(
            Investment.investment_status == "ACTIVE",
            Investment.return_balance == 1,
            Investment.return_date == reminder_date,
        )
        .all()
    )

    print("Investments found:", len(investments))

    notifications_created = 0

    for investment in investments:

        print(
            "Checking investment:",
            investment.investment_id,
            "user_id:",
            investment.user_id,
            "return_balance:",
            investment.return_balance,
            "return_date:",
            investment.return_date,
        )

        # -----------------------------------------
        # CHECK DUPLICATE
        # -----------------------------------------

        existing = (
            db.query(UserNotification)
            .filter(
                UserNotification.user_id
                == str(investment.user_id),

                UserNotification.notification_type
                == "INVESTMENT_RENEWAL",

                UserNotification.reference_id
                == investment.id,

                UserNotification.reference_type
                == "INVESTMENT",
            )
            .first()
        )

        if existing:

            print(
                "Notification already exists for:",
                investment.investment_id
            )

            continue

        # -----------------------------------------
        # CREATE NOTIFICATION
        # -----------------------------------------

        notification = UserNotification(
            user_id=str(investment.user_id),

            notification_type="INVESTMENT_RENEWAL",

            title="Investment Renewal Reminder",

            message=(
                f"Your investment {investment.investment_id} "
                f"will be completed on "
                f"{investment.return_date.strftime('%d-%m-%Y')}. "
                f"You have 1 monthly return remaining. "
                f"Please renew your investment to continue."
            ),

            reference_id=investment.id,

            reference_type="INVESTMENT",

            is_read=False,
        )

        db.add(notification)

        notifications_created += 1

        print(
            "Notification created for:",
            investment.investment_id
        )

    db.commit()

    print("======================================")
    print(
        "Notifications created:",
        notifications_created
    )
    print("======================================")

    return notifications_created