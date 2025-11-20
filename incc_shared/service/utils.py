from datetime import date, datetime


def format_date(raw_date: date):
    return raw_date.strftime("%Y-%m-%d")


def format_datetime(raw_datetime: datetime):
    return raw_datetime.strftime("%Y-%m-%d %H:%M:%S")
