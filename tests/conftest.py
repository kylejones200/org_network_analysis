"""
Pytest fixtures and configuration for tests.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base, Team, TeamMember, Communication
from app.data_access.repositories import TeamRepository, TeamMemberRepository, CommunicationRepository


@pytest.fixture
def engine():
    """Create a test database engine"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create a test database session"""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def team_repo(session):
    """Team repository fixture"""
    return TeamRepository(session)


@pytest.fixture
def member_repo(session):
    """Member repository fixture"""
    return TeamMemberRepository(session)


@pytest.fixture
def comm_repo(session):
    """Communication repository fixture"""
    return CommunicationRepository(session)


@pytest.fixture
def sample_team(team_repo, member_repo):
    """Create a sample team with 5 members"""
    team = team_repo.create("Test Team", "A test team")
    
    members = []
    for i in range(5):
        member = member_repo.create(
            name=f"Member {i}",
            email=f"member{i}@test.com",
            team_id=team.id,
            role="Engineer"
        )
        members.append(member)
    
    return team, members


@pytest.fixture
def now():
    """Current datetime fixture"""
    return datetime.now(timezone.utc)


@pytest.fixture
def thirty_days_ago(now):
    """30 days ago datetime fixture"""
    return now - timedelta(days=30)
