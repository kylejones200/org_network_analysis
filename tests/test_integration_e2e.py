"""
End-to-End Integration Tests for Three E's Application

These tests verify complete workflows from start to finish,
simulating real-world usage scenarios.
"""

import pytest
import json
from datetime import datetime, timedelta, timezone
from app import create_app
from app.database import init_db


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = create_app()
    app.config["TESTING"] = True
    app.config["DATABASE_URL"] = "sqlite:///:memory:"
    
    with app.app_context():
        init_db(app.config["DATABASE_URL"])
    
    yield app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestCompleteTeamWorkflow:
    """Test complete workflow from team creation to metrics analysis"""

    def test_full_team_lifecycle(self, client):
        """
        E2E Test: Complete team lifecycle
        1. Create team
        2. Add members
        3. Record communications
        4. Calculate metrics
        5. Analyze network
        6. Get history
        7. Clean up
        """
        # Step 1: Create team
        team_response = client.post(
            "/api/v1/teams",
            data=json.dumps({
                "name": "Product Engineering Team",
                "description": "Core product development team"
            }),
            content_type="application/json"
        )
        assert team_response.status_code == 201
        team = json.loads(team_response.data)
        team_id = team["id"]
        assert team["name"] == "Product Engineering Team"

        # Step 2: Add 5 team members
        members = []
        member_data = [
            {"name": "Alice Johnson", "email": "alice@company.com", "role": "Tech Lead"},
            {"name": "Bob Smith", "email": "bob@company.com", "role": "Senior Engineer"},
            {"name": "Carol Davis", "email": "carol@company.com", "role": "Engineer"},
            {"name": "David Wilson", "email": "david@company.com", "role": "Engineer"},
            {"name": "Eve Martinez", "email": "eve@company.com", "role": "Junior Engineer"}
        ]
        
        for member in member_data:
            member["team_id"] = team_id
            response = client.post(
                "/api/v1/members",
                data=json.dumps(member),
                content_type="application/json"
            )
            assert response.status_code == 201
            members.append(json.loads(response.data))

        # Verify all members added
        members_response = client.get(f"/api/v1/members?team_id={team_id}")
        assert members_response.status_code == 200
        team_members = json.loads(members_response.data)
        assert len(team_members) == 5

        # Step 3: Record various communications
        communications = [
            # Face-to-face meetings (high energy)
            {
                "sender_id": members[0]["id"],
                "receiver_id": members[1]["id"],
                "team_id": team_id,
                "communication_type": "face-to-face",
                "duration_minutes": 30,
                "is_group": False,
                "is_cross_team": False
            },
            {
                "sender_id": members[0]["id"],
                "receiver_id": members[2]["id"],
                "team_id": team_id,
                "communication_type": "face-to-face",
                "duration_minutes": 15,
                "is_group": False,
                "is_cross_team": False
            },
            # Group meeting
            {
                "sender_id": members[0]["id"],
                "receiver_id": None,
                "team_id": team_id,
                "communication_type": "meeting",
                "duration_minutes": 60,
                "is_group": True,
                "is_cross_team": False
            },
            # Video calls
            {
                "sender_id": members[1]["id"],
                "receiver_id": members[3]["id"],
                "team_id": team_id,
                "communication_type": "video-call",
                "duration_minutes": 45,
                "is_group": False,
                "is_cross_team": False
            },
            # Cross-team communication (exploration)
            {
                "sender_id": members[2]["id"],
                "receiver_id": members[3]["id"],
                "team_id": team_id,
                "communication_type": "face-to-face",
                "duration_minutes": 20,
                "is_group": False,
                "is_cross_team": True
            },
            # Various other communications for engagement balance
            {
                "sender_id": members[3]["id"],
                "receiver_id": members[4]["id"],
                "team_id": team_id,
                "communication_type": "chat",
                "duration_minutes": 10,
                "is_group": False,
                "is_cross_team": False
            },
            {
                "sender_id": members[4]["id"],
                "receiver_id": members[0]["id"],
                "team_id": team_id,
                "communication_type": "email",
                "duration_minutes": 5,
                "is_group": False,
                "is_cross_team": False
            }
        ]

        # Use bulk endpoint for efficiency
        bulk_response = client.post(
            "/api/v1/communications/bulk",
            data=json.dumps({"communications": communications}),
            content_type="application/json"
        )
        assert bulk_response.status_code == 201
        bulk_result = json.loads(bulk_response.data)
        assert len(bulk_result["ids"]) == len(communications)

        # Step 4: Calculate Three E's metrics
        calc_response = client.post(
            f"/api/v1/calculate/{team_id}",
            data=json.dumps({"days": 30}),
            content_type="application/json"
        )
        assert calc_response.status_code == 200
        metrics = json.loads(calc_response.data)

        # Verify all metrics present
        assert "energy" in metrics
        assert "engagement" in metrics
        assert "exploration" in metrics
        assert "overall_score" in metrics

        # Verify energy metrics
        assert metrics["energy"]["energy_score"] >= 0
        assert metrics["energy"]["energy_score"] <= 100
        assert metrics["energy"]["total_communications"] == 7
        assert metrics["energy"]["face_to_face_ratio"] > 0

        # Verify engagement metrics
        assert metrics["engagement"]["engagement_score"] >= 0
        assert metrics["engagement"]["engagement_score"] <= 100
        assert metrics["engagement"]["participation_rate"] > 0

        # Verify exploration metrics
        assert metrics["exploration"]["exploration_score"] >= 0
        assert metrics["exploration"]["exploration_score"] <= 100
        assert metrics["exploration"]["cross_team_communications"] > 0

        # Overall score should be weighted average
        assert 0 <= metrics["overall_score"] <= 100

        # Step 5: Analyze communication network
        network_response = client.get(f"/api/v1/network/{team_id}?days=30")
        assert network_response.status_code == 200
        network = json.loads(network_response.data)

        assert "density" in network
        assert "num_nodes" in network
        assert "num_edges" in network
        assert network["num_nodes"] == 5  # 5 team members

        # Step 6: Get centrality analysis
        centrality_response = client.get(f"/api/v1/network/{team_id}/centrality?days=30")
        assert centrality_response.status_code == 200
        centrality = json.loads(centrality_response.data)

        assert "centrality_metrics" in centrality
        assert "key_roles" in centrality

        # Step 7: Get metrics history
        history_response = client.get(f"/api/v1/metrics/{team_id}/history?limit=5")
        assert history_response.status_code == 200
        history = json.loads(history_response.data)
        assert isinstance(history, list)
        assert len(history) > 0

        # Step 8: Get latest metrics directly
        latest_response = client.get(f"/api/v1/metrics/{team_id}")
        assert latest_response.status_code == 200
        latest = json.loads(latest_response.data)
        assert latest["energy_score"] == metrics["energy"]["energy_score"]

        # Step 9: Compare with all teams
        all_metrics_response = client.get("/api/v1/metrics/all")
        assert all_metrics_response.status_code == 200
        all_metrics = json.loads(all_metrics_response.data)
        assert len(all_metrics) >= 1
        assert any(m["team_id"] == team_id for m in all_metrics)

        # Step 10: Update team info
        update_response = client.put(
            f"/api/v1/teams/{team_id}",
            data=json.dumps({
                "name": "Product Engineering Team - Updated",
                "description": "Updated description"
            }),
            content_type="application/json"
        )
        assert update_response.status_code == 200

        # Step 11: Delete a member
        delete_member_response = client.delete(f"/api/v1/members/{members[4]['id']}")
        assert delete_member_response.status_code == 200

        # Verify member deleted
        members_check = client.get(f"/api/v1/members?team_id={team_id}")
        updated_members = json.loads(members_check.data)
        assert len(updated_members) == 4

        # Step 12: Clean up - delete team
        delete_response = client.delete(f"/api/v1/teams/{team_id}")
        assert delete_response.status_code == 200

        # Verify team deleted
        verify_response = client.get(f"/api/v1/teams/{team_id}")
        assert verify_response.status_code == 404


class TestMultiTeamScenario:
    """Test scenarios with multiple teams interacting"""

    def test_multiple_teams_with_cross_team_communication(self, client):
        """
        E2E Test: Multiple teams with cross-team collaboration
        Tests exploration metrics across teams
        """
        # Create Team A
        team_a_response = client.post(
            "/api/v1/teams",
            data=json.dumps({"name": "Engineering", "description": "Dev team"}),
            content_type="application/json"
        )
        team_a_id = json.loads(team_a_response.data)["id"]

        # Create Team B
        team_b_response = client.post(
            "/api/v1/teams",
            data=json.dumps({"name": "Product", "description": "Product team"}),
            content_type="application/json"
        )
        team_b_id = json.loads(team_b_response.data)["id"]

        # Add members to Team A
        team_a_members = []
        for i in range(3):
            response = client.post(
                "/api/v1/members",
                data=json.dumps({
                    "name": f"Engineer {i}",
                    "email": f"eng{i}@company.com",
                    "team_id": team_a_id,
                    "role": "Engineer"
                }),
                content_type="application/json"
            )
            team_a_members.append(json.loads(response.data))

        # Add members to Team B
        team_b_members = []
        for i in range(3):
            response = client.post(
                "/api/v1/members",
                data=json.dumps({
                    "name": f"PM {i}",
                    "email": f"pm{i}@company.com",
                    "team_id": team_b_id,
                    "role": "Product Manager"
                }),
                content_type="application/json"
            )
            team_b_members.append(json.loads(response.data))

        # Record internal Team A communications
        for i in range(5):
            client.post(
                "/api/v1/communications",
                data=json.dumps({
                    "sender_id": team_a_members[0]["id"],
                    "receiver_id": team_a_members[1]["id"],
                    "team_id": team_a_id,
                    "communication_type": "face-to-face",
                    "duration_minutes": 15,
                    "is_group": False,
                    "is_cross_team": False
                }),
                content_type="application/json"
            )

        # Record cross-team communications (exploration)
        cross_team_comms = [
            {
                "sender_id": team_a_members[0]["id"],
                "receiver_id": team_b_members[0]["id"],
                "team_id": team_a_id,
                "communication_type": "meeting",
                "duration_minutes": 60,
                "is_group": False,
                "is_cross_team": True
            },
            {
                "sender_id": team_a_members[1]["id"],
                "receiver_id": team_b_members[1]["id"],
                "team_id": team_a_id,
                "communication_type": "video-call",
                "duration_minutes": 30,
                "is_group": False,
                "is_cross_team": True
            }
        ]

        for comm in cross_team_comms:
            client.post(
                "/api/v1/communications",
                data=json.dumps(comm),
                content_type="application/json"
            )

        # Calculate metrics for Team A
        calc_response = client.post(
            f"/api/v1/calculate/{team_a_id}",
            data=json.dumps({"days": 30}),
            content_type="application/json"
        )
        assert calc_response.status_code == 200
        metrics_a = json.loads(calc_response.data)

        # Verify exploration score reflects cross-team activity
        assert metrics_a["exploration"]["cross_team_communications"] == 2
        assert metrics_a["exploration"]["exploration_score"] > 0

        # Compare all teams
        all_teams_response = client.get("/api/v1/metrics/all")
        all_teams = json.loads(all_teams_response.data)
        assert len(all_teams) >= 2


class TestRateLimitingE2E:
    """Test rate limiting in real scenarios"""

    def test_rate_limits_enforced(self, client):
        """
        E2E Test: Verify rate limits work across requests
        Note: This test may be slow due to rate limiting
        """
        # Create a team
        team_response = client.post(
            "/api/v1/teams",
            data=json.dumps({"name": "Test Team", "description": "Test"}),
            content_type="application/json"
        )
        team_id = json.loads(team_response.data)["id"]

        # Health endpoint should NOT be rate limited
        for i in range(10):
            response = client.get("/health")
            assert response.status_code == 200

        # Regular endpoints ARE rate limited (but our limits are generous)
        # Just verify rate limit headers are present
        response = client.get("/api/v1/teams")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers


class TestErrorHandlingE2E:
    """Test error handling in complete workflows"""

    def test_validation_errors_throughout_workflow(self, client):
        """
        E2E Test: Verify validation errors are caught at each step
        """
        # Try to create team with invalid data
        response = client.post(
            "/api/v1/teams",
            data=json.dumps({"description": "No name"}),
            content_type="application/json"
        )
        assert response.status_code == 422
        error = json.loads(response.data)
        assert "error" in error

        # Create valid team
        team_response = client.post(
            "/api/v1/teams",
            data=json.dumps({"name": "Valid Team", "description": "Test"}),
            content_type="application/json"
        )
        team_id = json.loads(team_response.data)["id"]

        # Try to add member with invalid email
        response = client.post(
            "/api/v1/members",
            data=json.dumps({
                "name": "John",
                "email": "not-an-email",
                "team_id": team_id,
                "role": "Engineer"
            }),
            content_type="application/json"
        )
        assert response.status_code == 422

        # Add valid member
        member_response = client.post(
            "/api/v1/members",
            data=json.dumps({
                "name": "John",
                "email": "john@test.com",
                "team_id": team_id,
                "role": "Engineer"
            }),
            content_type="application/json"
        )
        member_id = json.loads(member_response.data)["id"]

        # Try invalid communication (sender = receiver)
        response = client.post(
            "/api/v1/communications",
            data=json.dumps({
                "sender_id": member_id,
                "receiver_id": member_id,
                "team_id": team_id,
                "communication_type": "face-to-face",
                "duration_minutes": 15,
                "is_group": False,
                "is_cross_team": False
            }),
            content_type="application/json"
        )
        assert response.status_code == 422

        # Try invalid communication type
        response = client.post(
            "/api/v1/communications",
            data=json.dumps({
                "sender_id": member_id,
                "receiver_id": None,
                "team_id": team_id,
                "communication_type": "invalid-type",
                "duration_minutes": 15,
                "is_group": True,
                "is_cross_team": False
            }),
            content_type="application/json"
        )
        assert response.status_code == 422


class TestPerformanceScenario:
    """Test performance with realistic data volumes"""

    def test_large_team_with_many_communications(self, client):
        """
        E2E Test: Large team (20 members) with many communications
        Verifies system can handle realistic data volumes
        """
        # Create team
        team_response = client.post(
            "/api/v1/teams",
            data=json.dumps({"name": "Large Team", "description": "20 member team"}),
            content_type="application/json"
        )
        team_id = json.loads(team_response.data)["id"]

        # Add 20 members
        members = []
        for i in range(20):
            response = client.post(
                "/api/v1/members",
                data=json.dumps({
                    "name": f"Member {i}",
                    "email": f"member{i}@company.com",
                    "team_id": team_id,
                    "role": "Team Member"
                }),
                content_type="application/json"
            )
            members.append(json.loads(response.data))

        # Create 100 communications using bulk endpoint
        communications = []
        for i in range(100):
            sender = members[i % 20]
            receiver = members[(i + 1) % 20]
            communications.append({
                "sender_id": sender["id"],
                "receiver_id": receiver["id"],
                "team_id": team_id,
                "communication_type": ["face-to-face", "email", "chat", "video-call"][i % 4],
                "duration_minutes": 15,
                "is_group": False,
                "is_cross_team": False
            })

        # Bulk create in batches of 50
        for batch_start in range(0, 100, 50):
            batch = communications[batch_start:batch_start + 50]
            response = client.post(
                "/api/v1/communications/bulk",
                data=json.dumps({"communications": batch}),
                content_type="application/json"
            )
            assert response.status_code == 201

        # Calculate metrics (should complete in reasonable time)
        calc_response = client.post(
            f"/api/v1/calculate/{team_id}",
            data=json.dumps({"days": 30}),
            content_type="application/json"
        )
        assert calc_response.status_code == 200
        metrics = json.loads(calc_response.data)

        # Verify calculations completed
        assert metrics["energy"]["total_communications"] == 100
        assert metrics["engagement"]["participation_rate"] > 0

        # Network analysis should also complete
        network_response = client.get(f"/api/v1/network/{team_id}?days=30")
        assert network_response.status_code == 200
        network = json.loads(network_response.data)
        assert network["num_nodes"] == 20


class TestBackwardCompatibility:
    """Test that legacy /api/* endpoints still work"""

    def test_legacy_endpoints_work(self, client):
        """
        E2E Test: Verify /api/* (non-versioned) endpoints still work
        for backward compatibility
        """
        # Legacy endpoint should work
        response = client.post(
            "/api/teams",  # Old style
            data=json.dumps({"name": "Legacy Team", "description": "Test"}),
            content_type="application/json"
        )
        assert response.status_code == 201
        team = json.loads(response.data)

        # New endpoint should also work
        response_v1 = client.get(f"/api/v1/teams/{team['id']}")
        assert response_v1.status_code == 200

        # Legacy endpoint should still work
        response_legacy = client.get(f"/api/teams/{team['id']}")
        assert response_legacy.status_code == 200

        # Both should return same data
        assert json.loads(response_v1.data)["name"] == json.loads(response_legacy.data)["name"]
