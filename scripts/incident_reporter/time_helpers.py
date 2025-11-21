"""
Time and date utilities for incident reporting

Handles:
- Date range calculations (yesterday, weekly, monthly)
- Timestamp parsing
- Timezone conversions
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple


# Timezone used for reporting (Bangkok/Jakarta time)
GMT_PLUS_7 = timezone(timedelta(hours=7))


def get_yesterday_range() -> Tuple[datetime, datetime]:
    """Get yesterday's date range in GMT+7, returned as UTC"""
    now_local = datetime.now(GMT_PLUS_7)
    yesterday_local = now_local - timedelta(days=1)
    start_local = datetime.combine(
        yesterday_local.date(),
        datetime.min.time(),
    ).replace(tzinfo=GMT_PLUS_7)
    end_local = datetime.combine(
        yesterday_local.date(),
        datetime.max.time(),
    ).replace(tzinfo=GMT_PLUS_7)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def get_last_week_range(weeks_ago: int = 0) -> Tuple[datetime, datetime]:
    """Get week range (Monday 00:00 UTC to Sunday 23:59 UTC)

    Args:
        weeks_ago: Number of weeks back (0 = last completed week, 1 = week before that, etc.)
    """
    now_utc = datetime.now(timezone.utc)

    # Find last Sunday (completed week)
    # weekday(): Monday=0, Tuesday=1, ..., Sunday=6
    days_since_sunday = (now_utc.weekday() + 1) % 7  # 0 if Sunday, 1 if Monday, etc.
    if days_since_sunday == 0:
        # If today is Sunday, go back 7 days to get last Sunday
        days_since_sunday = 7

    last_sunday = now_utc - timedelta(days=days_since_sunday)

    # Go back additional weeks if specified
    target_sunday = last_sunday - timedelta(weeks=weeks_ago)

    # Week ends on Sunday 23:59:59 UTC
    end_utc = datetime.combine(
        target_sunday.date(),
        datetime.max.time(),
    ).replace(tzinfo=timezone.utc)

    # Week starts on Monday (6 days before Sunday)
    start_utc = datetime.combine(
        (target_sunday - timedelta(days=6)).date(),
        datetime.min.time(),
    ).replace(tzinfo=timezone.utc)

    return start_utc, end_utc


def get_last_month_range(months_ago: int = 0) -> Tuple[datetime, datetime]:
    """Get month range (1st 00:00 UTC to last day 23:59 UTC)

    Args:
        months_ago: Number of months back (0 = last completed month, 1 = month before that, etc.)
    """
    now_utc = datetime.now(timezone.utc)

    # Calculate target month
    target_year = now_utc.year
    target_month = now_utc.month - 1 - months_ago  # -1 for last month, then additional offset

    # Handle year rollover
    while target_month < 1:
        target_month += 12
        target_year -= 1
    while target_month > 12:
        target_month -= 12
        target_year += 1

    # First day of target month at 00:00:00 UTC
    first_day = datetime(target_year, target_month, 1, 0, 0, 0, tzinfo=timezone.utc)

    # Last day of target month (first day of next month - 1 day)
    if target_month == 12:
        next_month_first = datetime(target_year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    else:
        next_month_first = datetime(target_year, target_month + 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    last_day = next_month_first - timedelta(days=1)

    start_utc = first_day
    end_utc = datetime.combine(
        last_day.date(),
        datetime.max.time(),
    ).replace(tzinfo=timezone.utc)

    return start_utc, end_utc


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse timestamp string to datetime object with UTC timezone"""
    if not timestamp_str:
        return None
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(timestamp_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except Exception:
        return None
