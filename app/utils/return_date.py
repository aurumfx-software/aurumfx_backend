# from datetime import date


# def calculate_return_date(investment_date: date) -> date:

#     day = investment_date.day

#     if day <= 5:
#         payout_day = 5

#     elif day <= 10:
#         payout_day = 10

#     elif day <= 15:
#         payout_day = 15

#     elif day <= 20:
#         payout_day = 20

#     elif day <= 25:
#         payout_day = 25

#     else:
#         payout_day = 30

#     month = investment_date.month + 1
#     year = investment_date.year

#     if month > 12:
#         month = 1
#         year += 1

#     return date(year, month, payout_day)

from datetime import date
import calendar

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import ReturnDateSetting


def calculate_return_date(
    db: Session,
    investment_date: date
) -> date:

    day = investment_date.day

    setting = (
        db.query(ReturnDateSetting)
        .filter(
            ReturnDateSetting.status == True,
            ReturnDateSetting.from_day <= day,
            ReturnDateSetting.to_day >= day
        )
        .first()
    )

    if not setting:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Return date setting is not configured "
                f"for day {day}"
            )
        )

    payout_day = setting.payout_day

    # Next month
    if investment_date.month == 12:
        next_month = 1
        next_year = investment_date.year + 1
    else:
        next_month = investment_date.month + 1
        next_year = investment_date.year

    # Avoid invalid dates such as February 30
    last_day = calendar.monthrange(
        next_year,
        next_month
    )[1]

    payout_day = min(
        payout_day,
        last_day
    )

    return date(
        next_year,
        next_month,
        payout_day
    )