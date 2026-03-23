"""
Example Usage Script
Demonstrates how to use the Three E's application
"""

import logging
import requests
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000"


def example_create_team():
    """Example: Create a new team"""
    logger.info("Creating a new team...")

    response = requests.post(
        f"{BASE_URL}/api/v1/teams",
        json={"name": "Innovation Lab", "description": "Cross-functional innovation team"},
    )

    team = response.json()
    logger.info(f"Created team: {team['name']} (ID: {team['id']})")
    return team["id"]


def example_add_members(team_id):
    """Example: Add team members"""
    logger.info("Adding team members...")

    members = [
        {"name": "Sarah Chen", "email": "sarah.chen@company.com", "role": "Team Lead"},
        {"name": "Mike Johnson", "email": "mike.johnson@company.com", "role": "Engineer"},
        {"name": "Lisa Park", "email": "lisa.park@company.com", "role": "Designer"},
        {"name": "David Kim", "email": "david.kim@company.com", "role": "Product Manager"},
    ]

    member_ids = []
    for member_data in members:
        member_data["team_id"] = team_id
        response = requests.post(f"{BASE_URL}/api/v1/members", json=member_data)
        member = response.json()
        member_ids.append(member["id"])
        logger.info(f"Added member: {member['name']} ({member['role']})")

    return member_ids


def example_record_communications(team_id, member_ids):
    """Example: Record various types of communications"""
    logger.info("Recording communications...")

    # Face-to-face meeting
    requests.post(
        f"{BASE_URL}/api/v1/communications",
        json={
            "sender_id": member_ids[0],
            "receiver_id": member_ids[1],
            "team_id": team_id,
            "communication_type": "face-to-face",
            "duration_minutes": 20,
            "is_group": False,
            "is_cross_team": False,
        },
    )
    logger.info("Recorded face-to-face meeting (20 min)")

    # Team meeting
    requests.post(
        f"{BASE_URL}/api/v1/communications",
        json={
            "sender_id": member_ids[0],
            "team_id": team_id,
            "communication_type": "meeting",
            "duration_minutes": 60,
            "is_group": True,
            "is_cross_team": False,
        },
    )
    logger.info("Recorded group meeting (60 min)")

    # Cross-team collaboration
    requests.post(
        f"{BASE_URL}/api/v1/communications",
        json={
            "sender_id": member_ids[2],
            "team_id": team_id,
            "communication_type": "face-to-face",
            "duration_minutes": 30,
            "is_group": False,
            "is_cross_team": True,
        },
    )
    logger.info("Recorded cross-team collaboration (30 min)")


def example_calculate_metrics(team_id):
    """Example: Calculate Three E's metrics"""
    logger.info("Calculating Three E's metrics...")

    response = requests.post(f"{BASE_URL}/api/v1/calculate/{team_id}", json={"days": 30})
    metrics = response.json()

    logger.info(f"Results for Team ID {team_id}:")
    logger.info(f"  Energy Score: {metrics['energy']['energy_score']:.2f}/100")
    logger.info(f"  Engagement Score: {metrics['engagement']['engagement_score']:.2f}/100")
    logger.info(f"  Exploration Score: {metrics['exploration']['exploration_score']:.2f}/100")
    logger.info(f"  Overall Score: {metrics['overall_score']:.2f}/100")

    logger.debug(f"Energy - Total Communications: {metrics['energy']['total_communications']}")
    logger.debug(f"Energy - Face-to-Face Ratio: {metrics['energy']['face_to_face_ratio']:.2%}")
    logger.debug(f"Engagement - Participation Rate: {metrics['engagement']['participation_rate']:.2%}")
    logger.debug(f"Engagement - Balance Score: {metrics['engagement']['balance_score']:.2f}")
    logger.debug(f"Exploration - Cross-team Communications: {metrics['exploration']['cross_team_communications']}")
    logger.debug(f"Exploration - Members Exploring: {metrics['exploration']['members_exploring']}")


def example_get_all_teams_metrics():
    """Example: Get metrics for all teams"""
    logger.info("Retrieving metrics for all teams...")

    response = requests.get(f"{BASE_URL}/api/v1/metrics/all")
    all_metrics = response.json()

    if not all_metrics:
        logger.warning("No metrics available. Calculate metrics first.")
        return

    logger.info("Team Performance Comparison:")
    for metric in all_metrics:
        team_name = metric.get("team_name", "Unknown")
        logger.info(
            f"  {team_name}: Overall={metric['overall_score']:.1f}, "
            f"Energy={metric['energy_score']:.1f}, "
            f"Engagement={metric['engagement_score']:.1f}, "
            f"Exploration={metric['exploration_score']:.1f}"
        )


def example_network_analysis(team_id):
    """Example: Analyze team communication network"""
    logger.info("Analyzing communication network...")

    response = requests.get(f"{BASE_URL}/api/v1/network/{team_id}")
    network = response.json()

    logger.info(f"Network metrics for Team {team_id}:")
    logger.info(f"  Density: {network.get('density', 0):.3f}")
    logger.info(f"  Nodes: {network.get('num_nodes', 0)}, Edges: {network.get('num_edges', 0)}")
    logger.info(f"  Connected: {network.get('is_connected', False)}")

    if "most_central_member_id" in network:
        logger.info(f"  Most Central Member: {network['most_central_member_id']}")

    if "potential_bottlenecks" in network and network["potential_bottlenecks"]:
        logger.warning(f"  Potential Bottlenecks: {network['potential_bottlenecks']}")


def run_examples():
    """Run all examples"""
    logger.info("Three E's Application - Usage Examples")
    logger.info("Make sure the API server is running (python app.py)")

    try:
        # Check if server is running
        response = requests.get(BASE_URL)
        if response.status_code != 200:
            logger.error("Cannot connect to API server")
            logger.error("Start the server with: python app.py")
            return

        # Use existing team (ID 1) if available, or create new one
        logger.info("Checking for existing teams...")
        teams_response = requests.get(f"{BASE_URL}/api/v1/teams")
        existing_teams = teams_response.json()

        if existing_teams:
            team_id = existing_teams[0]["id"]
            logger.info(f"Using existing team: {existing_teams[0]['name']} (ID: {team_id})")

            # Calculate metrics for existing team
            example_calculate_metrics(team_id)
            example_network_analysis(team_id)
            example_get_all_teams_metrics()
        else:
            logger.info("No existing teams found. Creating new team...")
            team_id = example_create_team()
            member_ids = example_add_members(team_id)
            example_record_communications(team_id, member_ids)
            example_calculate_metrics(team_id)
            example_network_analysis(team_id)

        logger.info("Examples completed successfully!")

    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to API server")
        logger.error("Start the server with: python app.py")
    except Exception as e:
        logger.error(f"Error running examples: {str(e)}", exc_info=True)


if __name__ == "__main__":
    run_examples()
