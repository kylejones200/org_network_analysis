"""
Utility functions and helpers.

DEPRECATED: This module is being phased out. Please use the focused modules instead:
- date_utils.py for date/time operations
- formatters.py for response formatting
- validators.py for validation functions
- export_utils.py for export operations

This module is kept for backwards compatibility only.
"""

# Re-export from focused modules for backwards compatibility
from .date_utils import parse_date_range
from .formatters import (
    calculate_percentile,
    format_metric_response,
    get_rating,
    get_recommendations,
)
from .validators import validate_communication_type
from .export_utils import export_metrics_to_json

__all__ = [
    "parse_date_range",
    "calculate_percentile",
    "format_metric_response",
    "get_rating",
    "get_recommendations",
    "validate_communication_type",
    "export_metrics_to_json",
]
