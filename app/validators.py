"""Data validation utilities."""

from .config import ValidationConstants


def validate_communication_type(comm_type: str) -> bool:
    """
    Validate communication type.

    Args:
        comm_type: Communication type string

    Returns:
        True if valid, False otherwise
    """
    return comm_type.lower() in ValidationConstants.VALID_COMMUNICATION_TYPES
