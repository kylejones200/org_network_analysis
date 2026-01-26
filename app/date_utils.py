"""Date and time utilities."""

from datetime import datetime, timedelta, timezone
from typing import Tuple

from .config import ValidationConstants


def parse_date_range(
    days: int = ValidationConstants.DEFAULT_ANALYSIS_DAYS,
    start_date: str = None,
    end_date: str = None,
) -> Tuple[datetime, datetime]:
    """
    Parse date range from various inputs.

    Args:
        days: Number of days to look back
        start_date: ISO format start date string
        end_date: ISO format end date string

    Returns:
        Tuple of (start_date, end_date) as datetime objects
    """
    end = datetime.fromisoformat(end_date) if end_date else datetime.now(timezone.utc)
    start = datetime.fromisoformat(start_date) if start_date else end - timedelta(days=days)

    return start, end
