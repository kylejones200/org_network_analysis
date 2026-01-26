"""
Presentation Layer (Layer 4)
============================
This layer provides the REST API using Flask.
Handles HTTP requests and responses, input validation, and error handling.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import IntegrityError, OperationalError
from datetime import datetime, timedelta, timezone
from functools import wraps
import traceback
import os

from .database import init_db
from .data_access.repositories import (
    TeamRepository,
    TeamMemberRepository,
    CommunicationRepository,
    TeamMetricsRepository,
    ExternalTeamRepository,
)
from .business_logic import ThreeEsCalculator, NetworkAnalyzer
from .config import Config
from .validation import (
    TeamCreate,
    TeamUpdate,
    MemberCreate,
    CommunicationCreate,
    CommunicationBulkCreate,
    MetricsCalculate,
    validate_request,
)


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS
    CORS(app)

    # Initialize rate limiting
    # Get storage URL from environment or use in-memory
    storage_uri = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=storage_uri,
        default_limits=["200 per day", "50 per hour"],
        strategy="fixed-window",
        headers_enabled=True,
    )

    # Initialize database
    engine = init_db(app.config["DATABASE_URL"])
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)

    # Store session factory in app context
    app.session_factory = Session

    # Cleanup session after request
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        Session.remove()

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    # Helper decorator for database sessions
    def with_session(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            session = Session()
            try:
                result = f(session, *args, **kwargs)
                session.commit()
                return result
            except IntegrityError as e:
                session.rollback()
                app.logger.warning(f"Integrity error in {f.__name__}: {str(e)}")
                return (
                    jsonify(
                        {
                            "error": "Data integrity violation",
                            "detail": "This operation conflicts with existing data (duplicate or missing reference)",
                        }
                    ),
                    409,
                )
            except OperationalError as e:
                session.rollback()
                app.logger.error(f"Database error in {f.__name__}: {str(e)}")
                return (
                    jsonify(
                        {
                            "error": "Database error",
                            "detail": "Database operation failed. Please try again later.",
                        }
                    ),
                    500,
                )
            except ValueError as e:
                session.rollback()
                app.logger.info(f"Validation error in {f.__name__}: {str(e)}")
                return jsonify({"error": "Validation error", "detail": str(e)}), 400
            except Exception as e:
                session.rollback()
                app.logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
                app.logger.error(traceback.format_exc())
                return (
                    jsonify(
                        {"error": "Internal server error", "detail": "An unexpected error occurred"}
                    ),
                    500,
                )
            finally:
                session.close()

        return decorated_function

    # ==================== Routes ====================

    @app.route("/")
    @limiter.exempt  # Don't rate limit the info endpoint
    def index():
        """API information endpoint"""
        return jsonify(
            {
                "name": "Three Es Organizational Network API",
                "version": "1.0.0",
                "description": "Measures Energy, Engagement, and Exploration for high-performance teams",
                "api_version": "v1",
                "rate_limits": {
                    "default": "200 per day, 50 per hour",
                    "calculation": "10 per hour (resource intensive)",
                },
                "endpoints": {
                    "teams": "/api/v1/teams",
                    "members": "/api/v1/members",
                    "communications": "/api/v1/communications",
                    "metrics": "/api/v1/metrics",
                    "calculate": "/api/v1/calculate/<team_id>",
                    "network": "/api/v1/network/<team_id>",
                },
                "legacy_endpoints_note": "Unversioned /api/* endpoints are supported for backward compatibility but deprecated",
            }
        )

    @app.route("/health")
    @limiter.exempt  # Don't rate limit health checks
    def health_check():
        """Health check endpoint for load balancers and monitoring"""
        try:
            # Test database connection
            session = Session()
            session.execute("SELECT 1")
            session.close()
            
            return jsonify({
                "status": "healthy",
                "service": "orgnet-api",
                "version": "1.0.0",
                "database": "connected"
            }), 200
        except Exception as e:
            app.logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                "status": "unhealthy",
                "service": "orgnet-api",
                "version": "1.0.0",
                "database": "disconnected",
                "error": str(e)
            }), 503

    @app.route("/metrics")
    @limiter.exempt  # Don't rate limit metrics endpoint for monitoring
    def metrics_endpoint():
        """Prometheus-style metrics endpoint"""
        try:
            session = Session()
            
            # Get basic stats
            team_repo = TeamRepository(session)
            member_repo = TeamMemberRepository(session)
            comm_repo = CommunicationRepository(session)
            
            teams = team_repo.get_all()
            
            metrics_lines = [
                "# HELP orgnet_teams_total Total number of teams",
                "# TYPE orgnet_teams_total gauge",
                f"orgnet_teams_total {len(teams)}",
                "",
                "# HELP orgnet_members_total Total number of team members",
                "# TYPE orgnet_members_total gauge",
                f"orgnet_members_total {len(member_repo.get_all())}",
                "",
            ]
            
            # Per-team metrics
            for team in teams:
                members = member_repo.get_by_team(team.id)
                team_name = team.name.replace(" ", "_").lower()
                
                metrics_lines.extend([
                    f'orgnet_team_members{{team="{team_name}",team_id="{team.id}"}} {len(members)}',
                ])
            
            session.close()
            
            from flask import Response
            return Response("\n".join(metrics_lines), mimetype="text/plain")
            
        except Exception as e:
            app.logger.error(f"Metrics endpoint failed: {str(e)}")
            return Response("# Error generating metrics\n", mimetype="text/plain"), 500

    # ==================== Team Endpoints ====================
    # API v1 - All endpoints are versioned for future compatibility

    @app.route("/api/v1/teams", methods=["GET"])
    @app.route("/api/teams", methods=["GET"])  # Backward compatibility
    @with_session
    def get_teams(session):
        """Get all teams"""
        repo = TeamRepository(session)
        teams = repo.get_all()
        return jsonify(
            [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "created_at": t.created_at.isoformat(),
                    "member_count": len(t.members),
                }
                for t in teams
            ]
        )

    @app.route("/api/v1/teams/<int:team_id>", methods=["GET"])
    @app.route("/api/teams/<int:team_id>", methods=["GET"])  # Backward compatibility
    @with_session
    def get_team(session, team_id):
        """Get specific team"""
        repo = TeamRepository(session)
        team = repo.get_by_id(team_id)
        if not team:
            return jsonify({"error": "Team not found"}), 404

        return jsonify(
            {
                "id": team.id,
                "name": team.name,
                "description": team.description,
                "created_at": team.created_at.isoformat(),
                "members": [
                    {"id": m.id, "name": m.name, "email": m.email, "role": m.role}
                    for m in team.members
                ],
            }
        )

    @app.route("/api/v1/teams", methods=["POST"])
    @app.route("/api/teams", methods=["POST"])  # Backward compatibility
    @with_session
    def create_team(session):
        """Create a new team"""
        data = request.get_json()
        validated, errors = validate_request(TeamCreate, data or {})

        if errors:
            return jsonify({"error": "Validation failed", "details": errors}), 422

        repo = TeamRepository(session)
        team = repo.create(name=validated.name, description=validated.description)

        return (
            jsonify(
                {
                    "id": team.id,
                    "name": team.name,
                    "description": team.description,
                    "created_at": team.created_at.isoformat(),
                }
            ),
            201,
        )

    @app.route("/api/v1/teams/<int:team_id>", methods=["PUT"])
    @app.route("/api/teams/<int:team_id>", methods=["PUT"])  # Backward compatibility
    @with_session
    def update_team(session, team_id):
        """Update a team"""
        data = request.get_json()
        repo = TeamRepository(session)
        team = repo.update(team_id, **data)

        if not team:
            return jsonify({"error": "Team not found"}), 404

        return jsonify({"id": team.id, "name": team.name, "description": team.description})

    @app.route("/api/v1/teams/<int:team_id>", methods=["DELETE"])
    @app.route("/api/teams/<int:team_id>", methods=["DELETE"])  # Backward compatibility
    @with_session
    def delete_team(session, team_id):
        """Delete a team"""
        repo = TeamRepository(session)
        success = repo.delete(team_id)

        if not success:
            return jsonify({"error": "Team not found"}), 404

        return jsonify({"message": "Team deleted successfully"})

    # ==================== Team Member Endpoints ====================

    @app.route("/api/v1/members", methods=["GET"])
    @app.route("/api/members", methods=["GET"])  # Backward compatibility
    @with_session
    def get_members(session):
        """Get all members, optionally filtered by team"""
        team_id = request.args.get("team_id", type=int)
        repo = TeamMemberRepository(session)

        if team_id:
            members = repo.get_by_team(team_id)
        else:
            members = repo.get_all()

        return jsonify(
            [
                {
                    "id": m.id,
                    "name": m.name,
                    "email": m.email,
                    "role": m.role,
                    "team_id": m.team_id,
                    "joined_at": m.joined_at.isoformat(),
                }
                for m in members
            ]
        )

    @app.route("/api/v1/members", methods=["POST"])
    @app.route("/api/members", methods=["POST"])  # Backward compatibility
    @with_session
    def create_member(session):
        """Create a new team member"""
        data = request.get_json()
        validated, errors = validate_request(MemberCreate, data or {})

        if errors:
            return jsonify({"error": "Validation failed", "details": errors}), 422

        repo = TeamMemberRepository(session)
        member = repo.create(
            name=validated.name,
            email=validated.email,
            team_id=validated.team_id,
            role=validated.role,
        )

        return (
            jsonify(
                {
                    "id": member.id,
                    "name": member.name,
                    "email": member.email,
                    "role": member.role,
                    "team_id": member.team_id,
                }
            ),
            201,
        )

    @app.route("/api/v1/members/<int:member_id>", methods=["DELETE"])
    @app.route("/api/members/<int:member_id>", methods=["DELETE"])  # Backward compatibility
    @with_session
    def delete_member(session, member_id):
        """Delete a team member"""
        repo = TeamMemberRepository(session)
        success = repo.delete(member_id)

        if not success:
            return jsonify({"error": "Member not found"}), 404

        return jsonify({"message": "Member deleted successfully"})

    # ==================== Communication Endpoints ====================

    @app.route("/api/v1/communications", methods=["GET"])
    @app.route("/api/communications", methods=["GET"])  # Backward compatibility
    @with_session
    def get_communications(session):
        """Get communications, optionally filtered"""
        team_id = request.args.get("team_id", type=int)
        member_id = request.args.get("member_id", type=int)
        days = request.args.get("days", type=int, default=30)

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        repo = CommunicationRepository(session)

        if member_id:
            comms = repo.get_by_member(member_id, start_date, end_date)
        elif team_id:
            comms = repo.get_by_team(team_id, start_date, end_date)
        else:
            return jsonify({"error": "team_id or member_id required"}), 400

        # Serialize communications
        return jsonify(
            [
                {
                    "id": c.id,
                    "sender_id": c.sender_id,
                    "receiver_id": c.receiver_id,
                    "team_id": c.team_id,
                    "type": c.communication_type,
                    "duration_minutes": c.duration_minutes,
                    "is_group": bool(c.is_group_communication),
                    "is_cross_team": bool(c.is_cross_team),
                    "timestamp": c.timestamp.isoformat(),
                }
                for c in comms
            ]
        )

    @app.route("/api/v1/communications", methods=["POST"])
    @app.route("/api/communications", methods=["POST"])  # Backward compatibility
    @with_session
    def create_communication(session):
        """Record a new communication event"""
        data = request.get_json()
        validated, errors = validate_request(CommunicationCreate, data or {})

        if errors:
            return jsonify({"error": "Validation failed", "details": errors}), 422

        repo = CommunicationRepository(session)
        comm = repo.create(
            sender_id=validated.sender_id,
            team_id=validated.team_id,
            communication_type=validated.communication_type,
            receiver_id=validated.receiver_id,
            duration_minutes=validated.duration_minutes,
            is_group_communication=1 if validated.is_group else 0,
            is_cross_team=1 if validated.is_cross_team else 0,
            message_content=validated.message_content,
        )

        return (
            jsonify(
                {
                    "id": comm.id,
                    "sender_id": comm.sender_id,
                    "receiver_id": comm.receiver_id,
                    "team_id": comm.team_id,
                    "type": comm.communication_type,
                    "timestamp": comm.timestamp.isoformat(),
                }
            ),
            201,
        )

    @app.route("/api/v1/communications/bulk", methods=["POST"])
    @app.route("/api/communications/bulk", methods=["POST"])  # Backward compatibility
    @limiter.limit("20 per hour")  # Limit bulk operations
    @with_session
    def create_bulk_communications(session):
        """Create multiple communication records at once"""
        data = request.get_json()
        if not data or "communications" not in data:
            return jsonify({"error": "communications array required"}), 400

        communications_data = data["communications"]
        
        # Validate array size
        from .config import ValidationConstants
        if len(communications_data) > ValidationConstants.MAX_BULK_COMMUNICATIONS:
            return jsonify({
                "error": "Too many communications",
                "detail": f"Maximum {ValidationConstants.MAX_BULK_COMMUNICATIONS} communications per request"
            }), 400

        # Validate each communication
        errors = []
        for idx, comm_data in enumerate(communications_data):
            validated, validation_errors = validate_request(CommunicationCreate, comm_data)
            if validation_errors:
                errors.append({
                    "index": idx,
                    "errors": validation_errors
                })
        
        if errors:
            return jsonify({
                "error": "Validation failed",
                "details": errors
            }), 422

        # Create all communications
        repo = CommunicationRepository(session)
        created = []

        for comm_data in communications_data:
            validated, _ = validate_request(CommunicationCreate, comm_data)
            comm = repo.create(
                sender_id=validated.sender_id,
                team_id=validated.team_id,
                communication_type=validated.communication_type,
                receiver_id=validated.receiver_id,
                duration_minutes=validated.duration_minutes,
                is_group_communication=1 if validated.is_group else 0,
                is_cross_team=1 if validated.is_cross_team else 0,
                message_content=validated.message_content,
            )
            created.append(comm.id)

        app.logger.info(f"Bulk created {len(created)} communications")
        return jsonify({"message": f"Created {len(created)} communications", "ids": created}), 201

    # ==================== Metrics & Analysis Endpoints ====================

    @app.route("/api/v1/calculate/<int:team_id>", methods=["POST"])
    @app.route("/api/calculate/<int:team_id>", methods=["POST"])  # Backward compatibility
    @limiter.limit("10 per hour")  # More restrictive for calculation endpoint
    @with_session
    def calculate_metrics(session, team_id):
        """Calculate Three E's metrics for a team"""
        data = request.get_json() or {}

        # Parse date range
        days = data.get("days", 30)
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        if "start_date" in data:
            start_date = datetime.fromisoformat(data["start_date"])
        if "end_date" in data:
            end_date = datetime.fromisoformat(data["end_date"])

        # Calculate metrics
        calculator = ThreeEsCalculator(session)
        results = calculator.calculate_all_metrics(
            team_id=team_id, start_date=start_date, end_date=end_date, save_to_db=True
        )

        return jsonify(results)

    @app.route("/api/v1/metrics/<int:team_id>", methods=["GET"])
    @app.route("/api/metrics/<int:team_id>", methods=["GET"])  # Backward compatibility
    @with_session
    def get_team_metrics(session, team_id):
        """Get latest metrics for a team"""
        repo = TeamMetricsRepository(session)
        metrics = repo.get_latest_by_team(team_id)

        if not metrics:
            return jsonify({"error": "No metrics found for this team"}), 404

        return jsonify(
            {
                "team_id": metrics.team_id,
                "energy_score": metrics.energy_score,
                "engagement_score": metrics.engagement_score,
                "exploration_score": metrics.exploration_score,
                "overall_score": metrics.overall_score,
                "total_communications": metrics.total_communications,
                "participation_rate": metrics.participation_rate,
                "period_start": metrics.calculation_period_start.isoformat(),
                "period_end": metrics.calculation_period_end.isoformat(),
                "calculated_at": metrics.calculated_at.isoformat(),
            }
        )

    @app.route("/api/v1/metrics/<int:team_id>/history", methods=["GET"])
    @app.route("/api/metrics/<int:team_id>/history", methods=["GET"])  # Backward compatibility
    @with_session
    def get_metrics_history(session, team_id):
        """Get metrics history for a team"""
        limit = request.args.get("limit", type=int, default=10)
        repo = TeamMetricsRepository(session)
        metrics_list = repo.get_by_team(team_id, limit=limit)

        return jsonify(
            [
                {
                    "energy_score": m.energy_score,
                    "engagement_score": m.engagement_score,
                    "exploration_score": m.exploration_score,
                    "overall_score": m.overall_score,
                    "calculated_at": m.calculated_at.isoformat(),
                }
                for m in metrics_list
            ]
        )

    @app.route("/api/v1/metrics/all", methods=["GET"])
    @app.route("/api/metrics/all", methods=["GET"])  # Backward compatibility
    @with_session
    def get_all_metrics(session):
        """Get latest metrics for all teams"""
        repo = TeamMetricsRepository(session)
        metrics_list = repo.get_all_latest()

        return jsonify(
            [
                {
                    "team_id": m.team_id,
                    "team_name": m.team.name if m.team else None,
                    "energy_score": m.energy_score,
                    "engagement_score": m.engagement_score,
                    "exploration_score": m.exploration_score,
                    "overall_score": m.overall_score,
                    "calculated_at": m.calculated_at.isoformat(),
                }
                for m in metrics_list
            ]
        )

    @app.route("/api/v1/network/<int:team_id>", methods=["GET"])
    @app.route("/api/network/<int:team_id>", methods=["GET"])  # Backward compatibility
    @limiter.limit("30 per hour")  # Network analysis is computationally expensive
    @with_session
    def analyze_network(session, team_id):
        """Analyze team communication network"""
        days = request.args.get("days", type=int, default=30)
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        analyzer = NetworkAnalyzer(session)
        network_metrics = analyzer.analyze_network_metrics(team_id, start_date, end_date)

        return jsonify(network_metrics)

    @app.route("/api/v1/network/<int:team_id>/communities", methods=["GET"])
    @app.route("/api/network/<int:team_id>/communities", methods=["GET"])  # Backward compatibility
    @limiter.limit("30 per hour")  # Community detection is expensive
    @with_session
    def detect_communities(session, team_id):
        """Detect sub-communities and potential silos within the team"""
        days = request.args.get("days", type=int, default=30)
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        analyzer = NetworkAnalyzer(session)
        communities = analyzer.detect_communities(team_id, start_date, end_date)

        return jsonify(communities)

    @app.route("/api/v1/network/<int:team_id>/centrality", methods=["GET"])
    @app.route("/api/network/<int:team_id>/centrality", methods=["GET"])  # Backward compatibility
    @limiter.limit("30 per hour")  # Centrality calculation is expensive
    @with_session
    def analyze_centrality(session, team_id):
        """Calculate advanced centrality metrics to identify key players"""
        days = request.args.get("days", type=int, default=30)
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        analyzer = NetworkAnalyzer(session)
        centrality = analyzer.calculate_advanced_centrality(team_id, start_date, end_date)

        return jsonify(centrality)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host=app.config.get("API_HOST", "0.0.0.0"),
        port=app.config.get("API_PORT", 5000),
        debug=app.config.get("DEBUG", True),
    )
