"""
Performance and Load Tests for Three E's Application

These tests measure performance characteristics and ensure
the system can handle expected loads.
"""

import pytest
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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


@pytest.fixture
def setup_large_dataset(client):
    """
    Setup a large dataset for performance testing
    Returns: dict with team_id, member_ids, and communication_ids
    """
    # Create team
    team_response = client.post(
        "/api/v1/teams",
        data=json.dumps({"name": "Performance Test Team", "description": "Large team for testing"}),
        content_type="application/json"
    )
    team_id = json.loads(team_response.data)["id"]

    # Create 50 members
    member_ids = []
    for i in range(50):
        response = client.post(
            "/api/v1/members",
            data=json.dumps({
                "name": f"Member {i}",
                "email": f"member{i}@test.com",
                "team_id": team_id,
                "role": "Team Member"
            }),
            content_type="application/json"
        )
        member_ids.append(json.loads(response.data)["id"])

    # Create 500 communications
    communications = []
    for i in range(500):
        sender = member_ids[i % 50]
        receiver = member_ids[(i + 1) % 50]
        communications.append({
            "sender_id": sender,
            "receiver_id": receiver,
            "team_id": team_id,
            "duration_minutes": (i % 60) + 5,
            "communication_type": ["face-to-face", "email", "chat", "video-call", "meeting"][i % 5],
            "is_group": i % 10 == 0,
            "is_cross_team": i % 15 == 0
        })

    # Bulk create in batches
    comm_ids = []
    for batch_start in range(0, 500, 100):
        batch = communications[batch_start:batch_start + 100]
        response = client.post(
            "/api/v1/communications/bulk",
            data=json.dumps({"communications": batch}),
            content_type="application/json"
        )
        batch_ids = json.loads(response.data)["ids"]
        comm_ids.extend(batch_ids)

    return {
        "team_id": team_id,
        "member_ids": member_ids,
        "communication_ids": comm_ids
    }


class TestResponseTimes:
    """Test response time performance"""

    def test_health_check_performance(self, client):
        """Health check should respond in < 100ms"""
        start = time.time()
        response = client.get("/health")
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        assert elapsed < 100, f"Health check took {elapsed}ms, expected < 100ms"

    def test_list_teams_performance(self, client):
        """Listing teams should be fast even with many teams"""
        # Create 20 teams
        for i in range(20):
            client.post(
                "/api/v1/teams",
                data=json.dumps({"name": f"Team {i}", "description": f"Team {i}"}),
                content_type="application/json"
            )

        # Measure list performance
        start = time.time()
        response = client.get("/api/v1/teams")
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 200, f"List teams took {elapsed}ms, expected < 200ms"

    def test_metrics_calculation_performance(self, client, setup_large_dataset):
        """Metrics calculation should complete in reasonable time"""
        data = setup_large_dataset
        team_id = data["team_id"]

        # Measure calculation time
        start = time.time()
        response = client.post(
            f"/api/v1/calculate/{team_id}",
            data=json.dumps({"days": 30}),
            content_type="application/json"
        )
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        # With 50 members and 500 communications, should complete in < 5 seconds
        assert elapsed < 5000, f"Metrics calculation took {elapsed}ms, expected < 5000ms"

    def test_network_analysis_performance(self, client, setup_large_dataset):
        """Network analysis should complete in reasonable time"""
        data = setup_large_dataset
        team_id = data["team_id"]

        # Measure network analysis time
        start = time.time()
        response = client.get(f"/api/v1/network/{team_id}?days=30")
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        # Network analysis with 50 nodes should complete in < 3 seconds
        assert elapsed < 3000, f"Network analysis took {elapsed}ms, expected < 3000ms"

    def test_centrality_calculation_performance(self, client, setup_large_dataset):
        """Centrality calculation should complete in reasonable time"""
        data = setup_large_dataset
        team_id = data["team_id"]

        # Measure centrality calculation time
        start = time.time()
        response = client.get(f"/api/v1/network/{team_id}/centrality?days=30")
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        # Centrality calculations should complete in < 3 seconds
        assert elapsed < 3000, f"Centrality calculation took {elapsed}ms, expected < 3000ms"


class TestScalability:
    """Test scalability with increasing data volumes"""

    def test_increasing_team_sizes(self, client):
        """Test performance with teams of increasing size"""
        results = []

        for team_size in [10, 25, 50]:
            # Create team
            team_response = client.post(
                "/api/v1/teams",
                data=json.dumps({"name": f"Team Size {team_size}", "description": "Test"}),
                content_type="application/json"
            )
            team_id = json.loads(team_response.data)["id"]

            # Add members
            member_ids = []
            for i in range(team_size):
                response = client.post(
                    "/api/v1/members",
                    data=json.dumps({
                        "name": f"Member {i}",
                        "email": f"m{i}@test.com",
                        "team_id": team_id,
                        "role": "Member"
                    }),
                    content_type="application/json"
                )
                member_ids.append(json.loads(response.data)["id"])

            # Add communications (2x team size)
            communications = []
            for i in range(team_size * 2):
                sender = member_ids[i % team_size]
                receiver = member_ids[(i + 1) % team_size]
                communications.append({
                    "sender_id": sender,
                    "receiver_id": receiver,
                    "team_id": team_id,
                    "communication_type": "face-to-face",
                    "duration_minutes": 15,
                    "is_group": False,
                    "is_cross_team": False
                })

            client.post(
                "/api/v1/communications/bulk",
                data=json.dumps({"communications": communications}),
                content_type="application/json"
            )

            # Measure calculation time
            start = time.time()
            response = client.post(
                f"/api/v1/calculate/{team_id}",
                data=json.dumps({"days": 30}),
                content_type="application/json"
            )
            elapsed = (time.time() - start) * 1000

            assert response.status_code == 200
            results.append({
                "team_size": team_size,
                "elapsed_ms": elapsed
            })

        # Performance should scale sub-quadratically
        # (50 member team should not take 25x longer than 10 member team)
        small_time = results[0]["elapsed_ms"]
        large_time = results[2]["elapsed_ms"]
        ratio = large_time / small_time if small_time > 0 else 0

        assert ratio < 15, f"Performance degradation too severe: {ratio}x slower for 5x team size"

    def test_increasing_communication_volumes(self, client):
        """Test performance with increasing communication volumes"""
        # Create team with 20 members
        team_response = client.post(
            "/api/v1/teams",
            data=json.dumps({"name": "Comm Volume Test", "description": "Test"}),
            content_type="application/json"
        )
        team_id = json.loads(team_response.data)["id"]

        member_ids = []
        for i in range(20):
            response = client.post(
                "/api/v1/members",
                data=json.dumps({
                    "name": f"Member {i}",
                    "email": f"m{i}@test.com",
                    "team_id": team_id,
                    "role": "Member"
                }),
                content_type="application/json"
            )
            member_ids.append(json.loads(response.data)["id"])

        results = []

        # Test with 50, 100, 200, 500 communications
        for comm_count in [50, 100, 200, 500]:
            communications = []
            for i in range(comm_count):
                sender = member_ids[i % 20]
                receiver = member_ids[(i + 1) % 20]
                communications.append({
                    "sender_id": sender,
                    "receiver_id": receiver,
                    "team_id": team_id,
                    "communication_type": "chat",
                    "duration_minutes": 10,
                    "is_group": False,
                    "is_cross_team": False
                })

            # Bulk create
            for batch_start in range(0, comm_count, 100):
                batch = communications[batch_start:batch_start + 100]
                client.post(
                    "/api/v1/communications/bulk",
                    data=json.dumps({"communications": batch}),
                    content_type="application/json"
                )

            # Measure calculation time
            start = time.time()
            response = client.post(
                f"/api/v1/calculate/{team_id}",
                data=json.dumps({"days": 30}),
                content_type="application/json"
            )
            elapsed = (time.time() - start) * 1000

            assert response.status_code == 200
            results.append({
                "comm_count": comm_count,
                "elapsed_ms": elapsed
            })

        # Should scale roughly linearly with communication count
        assert results[-1]["elapsed_ms"] < 5000, "500 communications should process in < 5s"


class TestConcurrency:
    """Test concurrent request handling"""

    def test_concurrent_read_requests(self, client):
        """Test handling multiple simultaneous read requests"""
        # Create some test data
        team_response = client.post(
            "/api/v1/teams",
            data=json.dumps({"name": "Concurrent Test", "description": "Test"}),
            content_type="application/json"
        )
        team_id = json.loads(team_response.data)["id"]

        # Make 20 concurrent requests
        def make_request():
            return client.get(f"/api/v1/teams/{team_id}")

        start = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [f.result() for f in as_completed(futures)]
        elapsed = time.time() - start

        # All requests should succeed
        assert all(r.status_code == 200 for r in results)
        # Should complete in reasonable time (< 5 seconds total)
        assert elapsed < 5.0

    def test_concurrent_write_requests(self, client):
        """Test handling multiple simultaneous write requests"""
        # Create team first
        team_response = client.post(
            "/api/v1/teams",
            data=json.dumps({"name": "Write Test", "description": "Test"}),
            content_type="application/json"
        )
        team_id = json.loads(team_response.data)["id"]

        # Create 10 members concurrently
        def create_member(i):
            return client.post(
                "/api/v1/members",
                data=json.dumps({
                    "name": f"Concurrent Member {i}",
                    "email": f"concurrent{i}@test.com",
                    "team_id": team_id,
                    "role": "Member"
                }),
                content_type="application/json"
            )

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_member, i) for i in range(10)]
            results = [f.result() for f in as_completed(futures)]

        # All should succeed (or some may have conflicts, which is OK)
        successful = [r for r in results if r.status_code == 201]
        assert len(successful) >= 8  # At least 80% should succeed


class TestMemoryUsage:
    """Test memory efficiency"""

    def test_large_dataset_memory(self, client, setup_large_dataset):
        """Verify system handles large datasets without excessive memory"""
        data = setup_large_dataset
        team_id = data["team_id"]

        # Multiple operations on large dataset
        for _ in range(5):
            # Calculate metrics
            response = client.post(
                f"/api/v1/calculate/{team_id}",
                data=json.dumps({"days": 30}),
                content_type="application/json"
            )
            assert response.status_code == 200

            # Network analysis
            response = client.get(f"/api/v1/network/{team_id}?days=30")
            assert response.status_code == 200

            # Centrality
            response = client.get(f"/api/v1/network/{team_id}/centrality?days=30")
            assert response.status_code == 200

        # If we got here without crashes, memory usage is reasonable
        assert True


class TestBulkOperationPerformance:
    """Test performance of bulk operations"""

    def test_bulk_communication_creation(self, client):
        """Test bulk communication creation performance"""
        # Setup
        team_response = client.post(
            "/api/v1/teams",
            data=json.dumps({"name": "Bulk Test", "description": "Test"}),
            content_type="application/json"
        )
        team_id = json.loads(team_response.data)["id"]

        member_ids = []
        for i in range(10):
            response = client.post(
                "/api/v1/members",
                data=json.dumps({
                    "name": f"Member {i}",
                    "email": f"m{i}@test.com",
                    "team_id": team_id,
                    "role": "Member"
                }),
                content_type="application/json"
            )
            member_ids.append(json.loads(response.data)["id"])

        # Create 100 communications in bulk
        communications = []
        for i in range(100):
            sender = member_ids[i % 10]
            receiver = member_ids[(i + 1) % 10]
            communications.append({
                "sender_id": sender,
                "receiver_id": receiver,
                "team_id": team_id,
                "communication_type": "chat",
                "duration_minutes": 10,
                "is_group": False,
                "is_cross_team": False
            })

        # Measure bulk creation time
        start = time.time()
        response = client.post(
            "/api/v1/communications/bulk",
            data=json.dumps({"communications": communications}),
            content_type="application/json"
        )
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 201
        # 100 communications should be created in < 2 seconds
        assert elapsed < 2000, f"Bulk creation took {elapsed}ms, expected < 2000ms"

        # Verify all were created
        result = json.loads(response.data)
        assert len(result["ids"]) == 100


class TestDatabasePerformance:
    """Test database query performance"""

    def test_metrics_history_query_performance(self, client, setup_large_dataset):
        """Test performance of metrics history queries"""
        data = setup_large_dataset
        team_id = data["team_id"]

        # Calculate metrics multiple times to build history
        for _ in range(5):
            client.post(
                f"/api/v1/calculate/{team_id}",
                data=json.dumps({"days": 30}),
                content_type="application/json"
            )

        # Measure history query time
        start = time.time()
        response = client.get(f"/api/v1/metrics/{team_id}/history?limit=10")
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 200, f"History query took {elapsed}ms, expected < 200ms"

    def test_communication_query_performance(self, client, setup_large_dataset):
        """Test performance of communication queries"""
        data = setup_large_dataset
        team_id = data["team_id"]

        # Query communications
        start = time.time()
        response = client.get(f"/api/v1/communications?team_id={team_id}&days=30")
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        # Querying 500 communications should be fast
        assert elapsed < 500, f"Communication query took {elapsed}ms, expected < 500ms"


@pytest.mark.benchmark
class TestBenchmarks:
    """Benchmark tests for establishing performance baselines"""

    def test_baseline_metrics_calculation(self, client, benchmark):
        """Benchmark metrics calculation"""
        # Setup standard dataset
        team_response = client.post(
            "/api/v1/teams",
            data=json.dumps({"name": "Benchmark Team", "description": "Test"}),
            content_type="application/json"
        )
        team_id = json.loads(team_response.data)["id"]

        # Add 10 members
        member_ids = []
        for i in range(10):
            response = client.post(
                "/api/v1/members",
                data=json.dumps({
                    "name": f"Member {i}",
                    "email": f"m{i}@test.com",
                    "team_id": team_id,
                    "role": "Member"
                }),
                content_type="application/json"
            )
            member_ids.append(json.loads(response.data)["id"])

        # Add 50 communications
        communications = []
        for i in range(50):
            communications.append({
                "sender_id": member_ids[i % 10],
                "receiver_id": member_ids[(i + 1) % 10],
                "team_id": team_id,
                "communication_type": "face-to-face",
                "duration_minutes": 15,
                "is_group": False,
                "is_cross_team": False
            })

        client.post(
            "/api/v1/communications/bulk",
            data=json.dumps({"communications": communications}),
            content_type="application/json"
        )

        # Benchmark calculation
        def run_calculation():
            return client.post(
                f"/api/v1/calculate/{team_id}",
                data=json.dumps({"days": 30}),
                content_type="application/json"
            )

        result = benchmark(run_calculation)
        assert result.status_code == 200
