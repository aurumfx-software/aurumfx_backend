from datetime import date


def calculate_return_date(investment_date: date) -> date:

    day = investment_date.day

    if day <= 5:
        payout_day = 5

    elif day <= 10:
        payout_day = 10

    elif day <= 15:
        payout_day = 15

    elif day <= 20:
        payout_day = 20

    elif day <= 25:
        payout_day = 25

    else:
        payout_day = 30

    month = investment_date.month + 1
    year = investment_date.year

    if month > 12:
        month = 1
        year += 1

    return date(year, month, payout_day)