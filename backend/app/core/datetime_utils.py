"""
DateTime utilities for consistent timezone handling across the application.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Get current UTC datetime as timezone-naive for database storage.

    Returns:
        datetime: Current UTC time without timezone info for database compatibility
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_now_aware() -> datetime:
    """
    Get current UTC datetime as timezone-aware.

    Returns:
        datetime: Current UTC time with timezone info
    """
    return datetime.now(timezone.utc)


def to_naive_utc(dt: datetime) -> datetime:
    """
    Convert a timezone-aware datetime to timezone-naive UTC.

    Args:
        dt: Timezone-aware datetime

    Returns:
        datetime: Timezone-naive UTC datetime
    """
    if dt.tzinfo is None:
        return dt  # Already naive
    return dt.utctimetuple() if hasattr(dt, "utctimetuple") else dt.replace(tzinfo=None)


def from_timestamp_utc(timestamp: float) -> datetime:
    """
    Convert Unix timestamp to timezone-naive UTC datetime for database storage.

    Args:
        timestamp: Unix timestamp

    Returns:
        datetime: Timezone-naive UTC datetime
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).replace(tzinfo=None)
