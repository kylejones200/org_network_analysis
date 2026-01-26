"""
Configuration and Constants.

Centralized configuration to eliminate magic numbers and maintain consistency.
"""

from typing import Dict
import os


# ============================================================================
# FLASK CONFIGURATION
# ============================================================================


class Config:
    """Flask application configuration."""
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///orgnet.db')
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # API settings
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '5000'))
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')


# ============================================================================
# SCORING THRESHOLDS
# ============================================================================


class ScoringThresholds:
    """Thresholds for scoring and rating metrics."""

    # Rating boundaries (0-100 scale)
    EXCELLENT_THRESHOLD = 80
    GOOD_THRESHOLD = 60
    FAIR_THRESHOLD = 40
    NEEDS_IMPROVEMENT_THRESHOLD = 20

    # Energy-specific thresholds
    ENERGY_EXCELLENT = 80
    ENERGY_GOOD = 60
    ENERGY_FAIR = 40

    # Engagement-specific thresholds
    ENGAGEMENT_EXCELLENT = 85
    ENGAGEMENT_GOOD = 65
    ENGAGEMENT_FAIR = 45

    # Exploration-specific thresholds
    EXPLORATION_EXCELLENT = 70
    EXPLORATION_GOOD = 50
    EXPLORATION_FAIR = 30


# ============================================================================
# NETWORK ANALYSIS THRESHOLDS
# ============================================================================


class NetworkThresholds:
    """Thresholds for network analysis metrics."""

    # Gini coefficient (communication balance)
    GINI_BALANCED = 0.3
    GINI_MODERATE = 0.5

    # Network density
    DENSITY_LOW = 0.3
    DENSITY_OPTIMAL_MIN = 0.4
    DENSITY_OPTIMAL_MAX = 0.6

    # Modularity (community structure)
    MODULARITY_INTEGRATED = 0.3
    MODULARITY_MODERATE = 0.5

    # Centrality analysis
    CENTRALITY_STD_MULTIPLIER = 1.5

    # Structural position
    EFFICIENCY_BROKER = 0.7
    EFFICIENCY_BRIDGE = 0.5
    EFFICIENCY_CONNECTOR = 0.3
    CONSTRAINT_BROKER = 0.3

    # Information flow
    FLOW_EFFICIENCY_LOW = 0.3
    AVG_PATH_LENGTH_HIGH = 3
    GATEKEEPER_RATIO = 0.5

    # Egocentric network
    MIN_NETWORK_SIZE_PERIPHERAL = 3

    # Partnership strength
    STRONG_PARTNERSHIP_THRESHOLD = 10

    # Reciprocity thresholds
    RECIPROCITY_HIGH = 0.5
    RECIPROCITY_MEDIUM = 0.3
    RECIPROCITY_LOW = 0.2

    # Clustering thresholds
    CLUSTERING_HIGH = 0.6
    CLUSTERING_MEDIUM = 0.4
    CLUSTERING_LOW = 0.3

    # Centralization thresholds
    CENTRALIZATION_HIGH = 0.6
    CENTRALIZATION_MEDIUM = 0.4

    # Assortativity thresholds
    ASSORTATIVITY_HIGH = 0.3
    ASSORTATIVITY_LOW = -0.1

    # Robustness thresholds
    BRITTLENESS_HIGH = 2  # components created by single node removal
    BRIDGE_EDGE_HIGH = 5  # number of bridge edges indicating risk


# ============================================================================
# TEMPORAL ANALYSIS CONSTANTS
# ============================================================================


class TemporalConstants:
    """Constants for temporal analysis."""

    # Working hours
    WORKING_HOURS_START = 9
    WORKING_HOURS_END = 17
    HOURS_PER_DAY = 24
    DAYS_PER_WEEK = 7

    # Day indices
    MONDAY = 0
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    # Thresholds
    WORKING_HOURS_RATIO_THRESHOLD = 0.8
    BURST_STD_MULTIPLIER = 2.0
    TREND_SLOPE_THRESHOLD = 1.0
    WEEKEND_DAY_INDICES = {5, 6}  # Saturday, Sunday


# ============================================================================
# ANOMALY DETECTION CONSTANTS
# ============================================================================


class AnomalyThresholds:
    """Thresholds for anomaly detection."""

    COMMUNICATION_DROP_THRESHOLD = 0.5  # 50% drop
    ISOLATION_THRESHOLD = 2  # connections
    METRIC_DECLINE_THRESHOLD = 10  # points
    CENTRALIZATION_THRESHOLD = 0.5
    AFTER_HOURS_RATIO_THRESHOLD = 0.3


# ============================================================================
# PREDICTIVE ANALYTICS CONSTANTS
# ============================================================================


class PredictiveConstants:
    """Constants for predictive analytics."""

    FORECAST_DAYS = 30
    MIN_HISTORY_WEEKS = 2
    MIN_HISTORY_DAYS = 7

    # At-risk thresholds
    COMMUNICATION_DECREASE_THRESHOLD = 0.5
    NO_COMMUNICATION_DAYS = 7
    ONE_WAY_THRESHOLD = 2

    # Trend thresholds
    INCREASING_SLOPE = 0.1
    DECREASING_SLOPE = -0.1

    # Risk scoring
    RISK_WEIGHT_PER_FACTOR = 33


# ============================================================================
# SENTIMENT ANALYSIS CONSTANTS
# ============================================================================


class SentimentThresholds:
    """Thresholds for sentiment analysis."""

    POSITIVE_THRESHOLD = 0.2
    NEGATIVE_THRESHOLD = -0.2

    # Intensity modifiers
    INTENSIFIER_MULTIPLIER = 1.5
    DIMINISHER_MULTIPLIER = 0.5

    # Alert thresholds
    NEGATIVE_SENTIMENT_ALERT = -0.3
    SENTIMENT_DROP_THRESHOLD = 0.2


# ============================================================================
# BENCHMARKING CONSTANTS
# ============================================================================


class BenchmarkingConstants:
    """Constants for benchmarking."""

    # Percentile boundaries
    TOP_QUARTILE = 75
    BOTTOM_QUARTILE = 25

    # Default industry benchmarks
    INDUSTRY_ENERGY = 70
    INDUSTRY_ENGAGEMENT = 75
    INDUSTRY_EXPLORATION = 60
    INDUSTRY_OVERALL = 70

    # Rating thresholds (percentile-based)
    EXCELLENT_PERCENTILE = 80
    GOOD_PERCENTILE = 60
    FAIR_PERCENTILE = 40


# ============================================================================
# RECOMMENDATION ENGINE CONSTANTS
# ============================================================================


class RecommendationConstants:
    """Constants for recommendation engine."""

    IMPACT_HIGH_THRESHOLD = 7
    IMPACT_MEDIUM_THRESHOLD = 4

    EFFORT_LOW = 3
    EFFORT_MEDIUM = 6

    QUICK_WIN_THRESHOLD = 5  # impact - effort


# ============================================================================
# RATING MAPS
# ============================================================================


class RatingMaps:
    """Lookup maps for ratings to avoid if/elif chains."""

    @staticmethod
    def get_rating_map() -> Dict[str, tuple]:
        """
        Get rating map for score-to-rating conversion.

        Returns dict with (threshold, rating) tuples in descending order.
        """
        return {
            "excellent": (ScoringThresholds.EXCELLENT_THRESHOLD, "Excellent"),
            "good": (ScoringThresholds.GOOD_THRESHOLD, "Good"),
            "fair": (ScoringThresholds.FAIR_THRESHOLD, "Fair"),
            "needs_improvement": (
                ScoringThresholds.NEEDS_IMPROVEMENT_THRESHOLD,
                "Needs Improvement",
            ),
            "poor": (0, "Poor"),
        }

    @staticmethod
    def get_performance_rating_map() -> Dict[str, tuple]:
        """Get performance rating boundaries."""
        return {
            "excellent": (80, 100, "excellent"),
            "good": (60, 79, "good"),
            "fair": (40, 59, "fair"),
            "poor": (0, 39, "poor"),
        }

    @staticmethod
    def get_benchmark_rating_map() -> Dict[str, tuple]:
        """Get benchmark rating boundaries (percentile-based)."""
        return {
            "excellent": (BenchmarkingConstants.EXCELLENT_PERCENTILE, "excellent"),
            "good": (BenchmarkingConstants.GOOD_PERCENTILE, "good"),
            "fair": (BenchmarkingConstants.FAIR_PERCENTILE, "fair"),
            "poor": (0, "poor"),
        }


# ============================================================================
# VALIDATION CONSTANTS
# ============================================================================


class ValidationConstants:
    """Constants for data validation."""

    VALID_COMMUNICATION_TYPES = {
        "face-to-face",
        "email",
        "chat",
        "meeting",
        "video-call",
        "phone",
        "other",
    }

    MAX_DURATION_HOURS = 8  # 480 minutes
    MAX_BULK_COMMUNICATIONS = 1000

    # Default time windows
    DEFAULT_ANALYSIS_DAYS = 30
    DEFAULT_FORECAST_DAYS = 30


# ============================================================================
# FORMATTING CONSTANTS
# ============================================================================


class FormattingConstants:
    """Constants for output formatting."""

    DECIMAL_PLACES_SCORE = 1
    DECIMAL_PLACES_RATIO = 2
    DECIMAL_PLACES_GINI = 3

    PERCENTILE_DECIMALS = 0
