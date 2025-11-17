from datetime import date


def format_date(raw_date: date):
    return raw_date.strftime("%Y-%m-%d")
