"""
Tests for Flask API endpoints.
"""

import pytest
import json
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


class TestHealthEndpoints:
    """Tests for health and monitoring endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.content_type == "text/plain; charset=utf-8"

    def test_root_endpoint(self, client):
        """Test API info endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["name"] == "Three Es Organizational Network API"
        assert "endpoints" in data


class TestTeamEndpoints:
    """Tests for team CRUD endpoints"""

    def test_create_team(self, client):
        """Test creating a new team"""
        response = client.post(
            "/api/teams",
            data=json.dumps({"name": "Test Team", "description": "A test team"}),
            content_type="application/json"
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["name"] == "Test Team"
        assert "id" in data

    def test_create_team_missing_name(self, client):
        """Test validation when creating team without name"""
        response = client.post(
            "/api/teams",
            data=json.dumps({"description": "No name"}),
            content_type="application/json"
        )
        
        assert response.status_code == 422  # Validation error

    def test_list_teams(self, client):
        """Test listing all teams"""
        # Create a team first
        client.post(
            "/api/teams",
            data=json.dumps({"name": "Team 1", "description": "First team"}),
            content_type="application/json"
        )
        
        response = client.get("/api/teams")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_team_by_id(self, client):
        """Test getting specific team"""
        # Create team
        create_response = client.post(
            "/api/teams",
            data=json.dumps({"name": "Team X", "description": "Test"}),
            content_type="application/json"
        )
        team_id = json.loads(create_response.data)["id"]
        
        # Get team
        response = client.get(f"/api/teams/{team_id}")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["name"] == "Team X"

    def test_get_nonexistent_team(self, client):
        """Test getting team that doesn't exist"""
        response = client.get("/api/teams/99999")
        assert response.status_code == 404

    def test_delete_team(self, client):
        """Test deleting a team"""
        # Create team
        create_response = client.post(
            "/api/teams",
            data=json.dumps({"name": "Delete Me", "description": "Temp"}),
            content_type="application/json"
        )
        team_id = json.loads(create_response.data)["id"]
        
        # Delete team
        response = client.delete(f"/api/teams/{team_id}")
        assert response.status_code == 200
        
        # Verify deleted
        get_response = client.get(f"/api/teams/{team_id}")
        assert get_response.status_code == 404


class TestMemberEndpoints:
    """Tests for team member endpoints"""

    def test_create_member(self, client):
        """Test adding member to team"""
        # Create team first
        team_response = client.post(
            "/api/teams",
            data=json.dumps({"name": "Team", "description": "Test"}),
            content_type="application/json"
        )
        team_id = json.loads(team_response.data)["id"]
        
        # Add member
        response = client.post(
            "/api/members",
            data=json.dumps({
                "name": "John Doe",
                "email": "john@test.com",
                "team_id": team_id,
                "role": "Engineer"
            }),
            content_type="application/json"
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["name"] == "John Doe"

    def test_list_team_members(self, client):
        """Test listing members of a team"""
        # Create team and member
        team_response = client.post(
            "/api/teams",
            data=json.dumps({"name": "Team", "description": "Test"}),
            content_type="application/json"
        )
        team_id = json.loads(team_response.data)["id"]
        
        client.post(
            "/api/members",
            data=json.dumps({
                "name": "Member 1",
                "email": "m1@test.com",
                "team_id": team_id,
                "role": "Engineer"
            }),
            content_type="application/json"
        )
        
        # List members
        response = client.get(f"/api/members?team_id={team_id}")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) == 1


class TestCommunicationEndpoints:
    """Tests for communication recording endpoints"""

    def test_create_communication(self, client):
        """Test recording a communication"""
        # Setup: Create team and members
        team_response = client.post(
            "/api/teams",
            data=json.dumps({"name": "Team", "description": "Test"}),
            content_type="application/json"
        )
        team_id = json.loads(team_response.data)["id"]
        
        member1_response = client.post(
            "/api/members",
            data=json.dumps({
                "name": "Alice",
                "email": "alice@test.com",
                "team_id": team_id,
                "role": "Engineer"
            }),
            content_type="application/json"
        )
        member1_id = json.loads(member1_response.data)["id"]
        
        member2_response = client.post(
            "/api/members",
            data=json.dumps({
                "name": "Bob",
                "email": "bob@test.com",
                "team_id": team_id,
                "role": "Engineer"
            }),
            content_type="application/json"
        )
        member2_id = json.loads(member2_response.data)["id"]
        
        # Record communication
        response = client.post(
            "/api/communications",
            data=json.dumps({
                "sender_id": member1_id,
                "receiver_id": member2_id,
                "team_id": team_id,
                "communication_type": "face-to-face",
                "duration_minutes": 30,
                "is_group": False,
                "is_cross_team": False
            }),
            content_type="application/json"
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["type"] == "face-to-face"

    def test_bulk_create_communications(self, client):
        """Test bulk communication recording"""
        # Setup
        team_response = client.post(
            "/api/teams",
            data=json.dumps({"name": "Team", "description": "Test"}),
            content_type="application/json"
        )
        team_id = json.loads(team_response.data)["id"]
        
        m1 = json.loads(client.post(
            "/api/members",
            data=json.dumps({"name": "M1", "email": "m1@test.com", "team_id": team_id, "role": "Eng"}),
            content_type="application/json"
        ).data)["id"]
        
        m2 = json.loads(client.post(
            "/api/members",
            data=json.dumps({"name": "M2", "email": "m2@test.com", "team_id": team_id, "role": "Eng"}),
            content_type="application/json"
        ).data)["id"]
        
        # Bulk create
        response = client.post(
            "/api/communications/bulk",
            data=json.dumps({
                "communications": [
                    {"sender_id": m1, "receiver_id": m2, "team_id": team_id, "communication_type": "chat"},
                    {"sender_id": m2, "receiver_id": m1, "team_id": team_id, "communication_type": "email"}
                ]
            }),
            content_type="application/json"
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert len(data["ids"]) == 2


class TestMetricsEndpoints:
    """Tests for metrics calculation endpoints"""

    def test_calculate_metrics(self, client):
        """Test calculating metrics for a team"""
        # Setup team with communications
        team_response = client.post(
            "/api/teams",
            data=json.dumps({"name": "Metrics Team", "description": "Test"}),
            content_type="application/json"
        )
        team_id = json.loads(team_response.data)["id"]
        
        # Calculate metrics
        response = client.post(
            f"/api/calculate/{team_id}",
            data=json.dumps({"days": 30}),
            content_type="application/json"
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "energy" in data
        assert "engagement" in data
        assert "exploration" in data
        assert "overall_score" in data
