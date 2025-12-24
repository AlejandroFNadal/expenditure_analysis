"""
Utility functions for expenditure analysis
"""
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def parse_date(date_str: str, date_format: str = '%d.%m.%Y') -> datetime:
    """Parse date string to datetime object"""
    return datetime.strptime(date_str, date_format)


def get_custom_month_period(date: datetime, month_end_day: int) -> str:
    """
    Calculate custom month period based on start day

    For example, if month_end_day is 25 (first day of period):
    - Oct 25 to Nov 24 = "2025-11" (November period)
    - Nov 25 to Dec 24 = "2025-12" (December period)
    - Dec 25, 2024 to Jan 24, 2025 = "2025-01" (January period)

    Period is named after the month where it ends (the 24th).

    Args:
        date: The date to get the period for
        month_end_day: The day when the month period starts (e.g., 25)

    Returns:
        Month period in format YYYY-MM
    """
    if date.day >= month_end_day:
        # Date is on or after the start day, belongs to next month period
        next_month = date + relativedelta(months=1)
        return next_month.strftime('%Y-%m')
    else:
        # Date is before the start day, belongs to current month period
        return date.strftime('%Y-%m')


def get_period_label(period: str, month_end_day: int) -> str:
    """
    Get human-readable label for a custom month period

    Args:
        period: Period string in format YYYY-MM (represents the END month)
        month_end_day: The day when the month period starts

    Returns:
        Human-readable label like "Jan 2025 (25 Dec - 24 Jan)"
    """
    year, month = period.split('-')
    # Period is named after the end month, so start date is one month earlier
    end_month_date = datetime(int(year), int(month), month_end_day)
    start_date = end_month_date - relativedelta(months=1)
    end_date = end_month_date - timedelta(days=1)

    if month_end_day == 1:
        # Standard month - use the period month itself
        return datetime(int(year), int(month), 1).strftime('%b %Y')
    else:
        # Custom period - label is the END month name with date range
        period_month = datetime(int(year), int(month), 1)
        return f"{period_month.strftime('%b %Y')} ({start_date.strftime('%-d %b')} - {end_date.strftime('%-d %b')})"


if __name__ == "__main__":
    # Test custom month calculation
    test_dates = [
        "24.10.2025",  # Should be Oct 2025 period (before 25th)
        "25.10.2025",  # Should be Nov 2025 period (on 25th, starts Nov period)
        "24.11.2025",  # Should be Nov 2025 period (before 25th, last day of Nov period)
        "25.11.2025",  # Should be Dec 2025 period (on 25th, starts Dec period)
        "24.12.2025",  # Should be Dec 2025 period (before 25th, last day of Dec period)
        "25.12.2025",  # Should be Jan 2026 period (on 25th, starts Jan period)
    ]

    month_end = 25
    for date_str in test_dates:
        date = parse_date(date_str)
        period = get_custom_month_period(date, month_end)
        label = get_period_label(period, month_end)
        print(f"{date_str} -> {period} ({label})")
