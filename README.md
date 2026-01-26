# Three E's Organizational Network Application

A sophisticated 4-layer Python application for measuring and analyzing the **Three E's of High-Performance Teams**: Energy, Engagement, and Exploration, based on MIT research published in Harvard Business Review.

## Overview

This application helps organizations measure and improve team performance by analyzing communication patterns. According to MIT's Human Dynamics Laboratory research, the key to high team performance is not the content of communication, but *how* teams communicate.

### The Three E's

1. **Energy** - The magnitude of formal and informal communication between team members
2. **Engagement** - The degree of interaction and balanced contribution to group discussions
3. **Exploration** - The extent to which team members engage with other teams and share findings

## Architecture

The application follows a clean 4-layer architecture pattern:

```
┌─────────────────────────────────────────────┐
│     Layer 4: Presentation Layer             │
│     (Flask REST API - app.py)               │
├─────────────────────────────────────────────┤
│     Layer 3: Business Logic Layer           │
│     (Three E's Calculations)                │
├─────────────────────────────────────────────┤
│     Layer 2: Data Access Layer              │
│     (Repository Pattern)                    │
├─────────────────────────────────────────────┤
│     Layer 1: Database Layer                 │
│     (SQLAlchemy ORM Models)                 │
└─────────────────────────────────────────────┘
```

### Layer Details

- **Layer 1 (Database)**: SQLAlchemy models defining teams, members, communications, and metrics
- **Layer 2 (Data Access)**: Repository pattern for clean data access abstraction
- **Layer 3 (Business Logic)**: Core algorithms for calculating Energy, Engagement, and Exploration scores
- **Layer 4 (Presentation)**: RESTful API built with Flask for easy integration

## Installation

### Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Ubuntu (recommended)

### Setup

1. Clone or download this repository:
```bash
cd orgnet
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file (copy from `env.example`):
```bash
# Copy the example file
cp env.example .env

# Edit .env with your settings
```

5. Initialize the database:
```bash
# Using Alembic migrations (recommended)
alembic upgrade head

# Or run the app once to create tables
python app.py
```

## Quick Start

### Start the API Server

```bash
python app.py
```

The API will be available at `http://localhost:5000`

### Generate Sample Data

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sample_data import generate_sample_data

# Create session
engine = create_engine('sqlite:///orgnet.db')
Session = sessionmaker(bind=engine)
session = Session()

# Generate sample data for 3 teams
generate_sample_data(session, num_teams=3)
```

### Calculate Metrics

```bash
# Using curl
curl -X POST http://localhost:5000/api/v1/calculate/1 \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'

# Using Python
import requests
response = requests.post('http://localhost:5000/api/v1/calculate/1', 
                        json={'days': 30})
print(response.json())
```

## API Reference

**Note:** All endpoints are versioned under `/api/v1/`. See `API.md` for complete documentation.

### Teams

- `GET /api/v1/teams` - List all teams
- `GET /api/v1/teams/<id>` - Get team details
- `POST /api/v1/teams` - Create new team
- `PUT /api/v1/teams/<id>` - Update team
- `DELETE /api/v1/teams/<id>` - Delete team

### Team Members

- `GET /api/v1/members?team_id=<id>` - List team members
- `POST /api/v1/members` - Add team member
- `DELETE /api/v1/members/<id>` - Remove member

### Communications

- `GET /api/v1/communications?team_id=<id>&days=30` - Get communications
- `POST /api/v1/communications` - Record communication event
- `POST /api/v1/communications/bulk` - Record multiple communications

### Metrics & Analysis

- `POST /api/v1/calculate/<team_id>` - Calculate Three E's metrics
- `GET /api/v1/metrics/<team_id>` - Get latest metrics
- `GET /api/v1/metrics/<team_id>/history` - Get metrics history
- `GET /api/v1/metrics/all` - Get metrics for all teams
- `GET /api/v1/network/<team_id>` - Analyze communication network

## Usage Examples

### 1. Create a Team

```python
import requests

BASE_URL = 'http://localhost:5000/api/v1'

response = requests.post(f'{BASE_URL}/teams', json={
    'name': 'Product Team',
    'description': 'Product development team'
})
team = response.json()
print(f"Created team: {team['id']}")
```

### 2. Add Team Members

```python
members = [
    {'name': 'Alice Smith', 'email': 'alice@company.com', 'role': 'Lead'},
    {'name': 'Bob Jones', 'email': 'bob@company.com', 'role': 'Engineer'},
    {'name': 'Carol White', 'email': 'carol@company.com', 'role': 'Designer'}
]

for member_data in members:
    member_data['team_id'] = team['id']
    requests.post(f'{BASE_URL}/members', json=member_data)
```

### 3. Record Communications

```python
# Record a face-to-face communication
requests.post(f'{BASE_URL}/communications', json={
    'sender_id': 1,
    'receiver_id': 2,
    'team_id': team['id'],
    'communication_type': 'face-to-face',
    'duration_minutes': 15,
    'is_group': False,
    'is_cross_team': False
})
```

### 4. Calculate and Retrieve Metrics

```python
# Calculate metrics for last 30 days
calc_response = requests.post(
    f'{BASE_URL}/calculate/{team["id"]}',
    json={'days': 30}
)
metrics = calc_response.json()

print(f"Energy Score: {metrics['energy']['energy_score']}")
print(f"Engagement Score: {metrics['engagement']['engagement_score']}")
print(f"Exploration Score: {metrics['exploration']['exploration_score']}")
print(f"Overall Score: {metrics['overall_score']}")
```

## Understanding the Metrics

### Energy Score (0-100)

Measures the magnitude and quality of team communication:
- **High (80-100)**: Frequent, face-to-face interactions
- **Medium (40-79)**: Regular communication with some face-to-face
- **Low (0-39)**: Infrequent or mostly electronic communication

**Key Research Finding**: Face-to-face communication is the most valuable form of communication.

### Engagement Score (0-100)

Measures balanced participation and two-way dialogue:
- **High (80-100)**: All members participate equally, balanced discussions
- **Medium (40-79)**: Most members participate, some imbalance
- **Low (0-39)**: Communication dominated by few members

**Key Research Finding**: Teams perform better when members "talk and listen in equal measure."

### Exploration Score (0-100)

Measures cross-team engagement and external learning:
- **High (80-100)**: Frequent cross-team collaboration and knowledge sharing
- **Medium (40-79)**: Some external engagement
- **Low (0-39)**: Isolated team with little external interaction

**Key Research Finding**: "Exploration outside the team" is critical for bringing in new ideas.

## Advanced Features

### Network Analysis

Analyze team communication networks using graph theory:

```python
response = requests.get(f'{BASE_URL}/network/{team_id}')
network = response.json()

print(f"Network Density: {network['density']}")
print(f"Most Central Member: {network['most_central_member_id']}")
print(f"Potential Bottlenecks: {network['potential_bottlenecks']}")
```

### Metrics History

Track team performance over time:

```python
response = requests.get(f'{BASE_URL}/metrics/{team_id}/history?limit=10')
history = response.json()

for metric in history:
    print(f"{metric['calculated_at']}: Overall Score = {metric['overall_score']}")
```

## Communication Types

The application recognizes these communication types (in order of value per research):

1. **face-to-face** - Most valuable (highest weight in Energy calculation)
2. **meeting** - High value group communication
3. **video-call** - Good for remote teams
4. **chat** - Real-time but less valuable than face-to-face
5. **email** - Least valuable form of communication
6. **phone** - One-on-one voice communication
7. **other** - Catch-all for other types

## Best Practices

### For High Team Performance

Based on MIT research findings:

1. **Prioritize face-to-face communication** over email and texting
2. **Ensure balanced participation** - everyone talks and listens equally
3. **Keep interventions short** and to the point
4. **Enable direct communication** between team members, not just through leaders
5. **Encourage back-channel** and side conversations within the team
6. **Promote exploration** - engage with other teams and share findings
7. **Design workspaces** to promote unplanned encounters and collaborations

### For Data Collection

1. Record communications consistently
2. Include communication duration when possible
3. Mark face-to-face interactions explicitly
4. Flag cross-team communications
5. Calculate metrics regularly (weekly or bi-weekly)

## Project Structure

```
orgnet/
├── database/
│   ├── __init__.py
│   └── models.py              # Layer 1: Database models
├── data_access/
│   ├── __init__.py
│   └── repositories.py        # Layer 2: Data access
├── business_logic/
│   ├── __init__.py
│   └── three_es_calculator.py # Layer 3: Business logic
├── tests/                     # Test suite
│   ├── conftest.py
│   ├── test_calculator.py
│   ├── test_network_analyzer.py
│   └── test_api.py
├── alembic/                   # Database migrations
│   └── versions/
├── app.py                     # Layer 4: Flask API
├── config.py                  # Configuration constants
├── validation.py              # Input validation
├── date_utils.py              # Date utilities
├── formatters.py              # Response formatting
├── validators.py              # Validation helpers
├── export_utils.py            # Export utilities
├── sample_data.py             # Sample data generator
├── examples.py                # Usage examples
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker container
├── docker-compose.yml         # Multi-container setup
├── alembic.ini                # Migration config
└── README.md                  # This file
```

## Database Schema

### Teams
- id, name, description, created_at

### Team Members
- id, name, email, role, team_id, joined_at

### Communications
- id, sender_id, receiver_id, team_id, communication_type
- duration_minutes, is_group_communication, is_cross_team
- message_content, timestamp

### Team Metrics
- id, team_id, energy_score, engagement_score, exploration_score
- overall_score, calculation_period_start, calculation_period_end
- calculated_at, total_communications, participation_rate

## Research Background

This application is based on research conducted at MIT's Human Dynamics Laboratory and published in the Harvard Business Review article "The New Science of Building Great Teams" by Alex Pentland (April 2012).

**Key Finding**: 
> "Patterns of communication are the most important predictor of a team's success."

The research used electronic badges to measure communication behavior and found that group dynamics and communication patterns matter more than individual intelligence or talent.

## Docker Deployment

The easiest way to run the application is with Docker:

```bash
# Start the full stack (API + PostgreSQL)
docker-compose up -d

# Check health
curl http://localhost:5000/health

# View logs
docker-compose logs -f api
```

## Contributing

See `CONTRIBUTING.md` for development setup and guidelines.

To extend the application:

1. Add new repositories to `data_access/repositories.py`
2. Extend business logic in `business_logic/three_es_calculator.py`
3. Add new API endpoints in `app.py`
4. Update models in `database/models.py` for new data structures
5. Create migrations with `alembic revision --autogenerate`
6. Write tests in `tests/` directory

## License

MIT License - Feel free to use this application in your organization.

## Support

For questions or issues, please refer to the API documentation at `http://localhost:5000/` when the server is running.

## Acknowledgments

Based on research by:
- Alex "Sandy" Pentland, MIT Media Lab
- MIT Human Dynamics Laboratory
- Published in Harvard Business Review

---

**Built with**: Python, Flask, SQLAlchemy, NetworkX, NumPy, Pandas
