"""
Organizational network analysis library.

Provides SQLAlchemy models, repositories, and calculators over team communication data.
There is no HTTP server in this package; integrate ``ThreeEsCalculator`` and
``NetworkAnalyzer`` in your own application or service.
"""

from .business_logic import (
    NetworkAnalyzer,
    ThreeEsCalculator,
    detect_team_metric_anomalies,
    detect_team_network_structural_anomalies,
)
from .config import Config
from .database import init_db

__all__ = [
    "ThreeEsCalculator",
    "NetworkAnalyzer",
    "detect_team_metric_anomalies",
    "detect_team_network_structural_anomalies",
    "Config",
    "init_db",
]
