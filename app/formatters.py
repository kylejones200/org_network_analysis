"""Response formatters and utilities."""

from typing import Dict, List

from .config import ScoringThresholds


def format_metric_response(metrics: Dict) -> Dict:
    """
    Format metrics for consistent API response.

    Args:
        metrics: Dictionary of metric values

    Returns:
        Formatted metrics dictionary
    """
    return {
        "energy": {
            "score": metrics.get("energy_score", 0),
            "rating": get_rating(metrics.get("energy_score", 0)),
            "details": metrics.get("energy", {}),
        },
        "engagement": {
            "score": metrics.get("engagement_score", 0),
            "rating": get_rating(metrics.get("engagement_score", 0)),
            "details": metrics.get("engagement", {}),
        },
        "exploration": {
            "score": metrics.get("exploration_score", 0),
            "rating": get_rating(metrics.get("exploration_score", 0)),
            "details": metrics.get("exploration", {}),
        },
        "overall": {
            "score": metrics.get("overall_score", 0),
            "rating": get_rating(metrics.get("overall_score", 0)),
        },
    }


def get_rating(score: float) -> str:
    """
    Convert numeric score to qualitative rating using threshold map.

    Args:
        score: Numeric score (0-100)

    Returns:
        Rating string (Excellent, Good, Fair, Needs Improvement, Poor)
    """
    # Rating thresholds in descending order
    rating_thresholds = [
        (ScoringThresholds.EXCELLENT_THRESHOLD, "Excellent"),
        (ScoringThresholds.GOOD_THRESHOLD, "Good"),
        (ScoringThresholds.FAIR_THRESHOLD, "Fair"),
        (ScoringThresholds.NEEDS_IMPROVEMENT_THRESHOLD, "Needs Improvement"),
        (0, "Poor"),
    ]

    return next(rating for threshold, rating in rating_thresholds if score >= threshold)


def calculate_percentile(value: float, min_val: float, max_val: float) -> float:
    """
    Calculate percentile of a value within a range.

    Args:
        value: The value to calculate percentile for
        min_val: Minimum value in range
        max_val: Maximum value in range

    Returns:
        Percentile (0-100)
    """
    MEDIAN_PERCENTILE = 50.0
    MIN_PERCENTILE = 0
    MAX_PERCENTILE = 100

    if max_val == min_val:
        return MEDIAN_PERCENTILE

    percentile = ((value - min_val) / (max_val - min_val)) * MAX_PERCENTILE
    return max(MIN_PERCENTILE, min(MAX_PERCENTILE, percentile))


def get_recommendations(energy: float, engagement: float, exploration: float) -> List[str]:
    """
    Generate recommendations based on Three E's scores using rule mapping.

    Args:
        energy: Energy score (0-100)
        engagement: Engagement score (0-100)
        exploration: Exploration score (0-100)

    Returns:
        List of recommendation strings
    """
    # Rule-based recommendation map
    recommendation_rules = [
        # Energy rules
        (
            energy < ScoringThresholds.ENERGY_FAIR,
            "Energy is low. Encourage more face-to-face communication and regular team interactions.",
        ),
        (
            ScoringThresholds.ENERGY_FAIR <= energy < ScoringThresholds.ENERGY_GOOD,
            "Increase communication frequency. Consider daily stand-ups or brief check-ins.",
        ),
        # Engagement rules
        (
            engagement < ScoringThresholds.ENGAGEMENT_FAIR,
            "Engagement needs improvement. Ensure all team members participate equally in discussions.",
        ),
        (
            engagement < ScoringThresholds.ENGAGEMENT_FAIR,
            "Avoid communication dominated by single individuals. Encourage two-way dialogue.",
        ),
        (
            ScoringThresholds.ENGAGEMENT_FAIR <= engagement < ScoringThresholds.ENGAGEMENT_GOOD,
            "Good engagement, but can improve. Foster more back-channel communications and peer interactions.",
        ),
        # Exploration rules
        (
            exploration < ScoringThresholds.EXPLORATION_FAIR,
            "Exploration is limited. Encourage team members to engage with other teams and share findings.",
        ),
        (
            exploration < ScoringThresholds.EXPLORATION_FAIR,
            "Set up cross-functional meetings and collaboration opportunities.",
        ),
        (
            ScoringThresholds.EXPLORATION_FAIR <= exploration < ScoringThresholds.EXPLORATION_GOOD,
            "Increase cross-team interactions. Promote serendipitous encounters through workspace design or events.",
        ),
        # Excellence rule
        (
            energy >= ScoringThresholds.ENERGY_EXCELLENT
            and engagement >= ScoringThresholds.ENGAGEMENT_EXCELLENT
            and exploration >= ScoringThresholds.EXPLORATION_EXCELLENT,
            "Excellent team performance! Maintain current communication patterns and continue to iterate.",
        ),
    ]

    recommendations = [rec for condition, rec in recommendation_rules if condition]

    return recommendations or [
        "Team performance is strong. Continue monitoring and maintain healthy communication patterns."
    ]
