from datetime import date
from scripts.seed import month_days

def test_month_days_contains_weekdays_only():
    days = list(month_days(date(2026, 10, 14), months_back=3))
    assert days
    assert all(d.weekday() < 5 for d in days)
    assert all(d < date(2026, 10, 1) for d in days)
