"""Export utilities for metrics data."""

import json
from datetime import datetime, timezone
from typing import Dict


def export_metrics_to_json(metrics: Dict, filename: str = None) -> str:
    """
    Export metrics to JSON file.

    Args:
        metrics: Metrics dictionary
        filename: Optional filename (default: metrics_TIMESTAMP.json)

    Returns:
        Filename of exported data
    """
    if not filename:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"metrics_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(metrics, f, indent=2, default=str)

    return filename
