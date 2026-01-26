# Getting Started with Three E's Application

## What This Application Does

Measures the **Three E's of High-Performance Teams** based on MIT research:

- **Energy**: Communication magnitude and frequency
- **Engagement**: Balanced participation and two-way dialogue  
- **Exploration**: Cross-team collaboration and learning

## Installation Options

Choose one of these methods:

### Option 1: Docker (Recommended)

**Fastest way to get started** - includes PostgreSQL database.

```bash
# Clone/navigate to the project
cd orgnet

# Start everything
docker-compose up -d

# Check it's running
curl http://localhost:5000/health

# View logs
docker-compose logs -f api
```

That's it! The API is now running at `http://localhost:5000`.

### Option 2: Local Python with uv

For development or if you prefer running Python directly.

```bash
# Navigate to project
cd orgnet

# Install dependencies (creates .venv automatically)
uv sync

# Copy environment config
cp env.example .env

# Initialize database
uv run alembic upgrade head

# Start server
uv run python -m app.app
```

The API will be at `http://localhost:5000`.

## Quick Test

Run the examples script to see it in action:

```bash
# In a new terminal (with server running)
cd orgnet

# Generate sample data
uv run python -c "from sqlalchemy import create_engine; from sqlalchemy.orm import sessionmaker; from app.sample_data import generate_sample_data; engine = create_engine('sqlite:///orgnet.db'); Session = sessionmaker(bind=engine); session = Session(); generate_sample_data(session, num_teams=3)"

# Run examples
uv run python -m app.examples
```

You should see output like:

```
INFO - Team: High Performing Team (ID: 1)
INFO - Energy Score: 78.45/100
INFO - Engagement Score: 85.20/100
INFO - Exploration Score: 62.30/100
INFO - Overall Score: 76.82/100
```

## Using the API

### Basic Workflow

1. **Create a team**
2. **Add team members**
3. **Record communications**
4. **Calculate metrics**
5. **Analyze results**

### Example: Complete Workflow

```python
import requests

BASE_URL = 'http://localhost:5000/api/v1'

# 1. Create a team
team_response = requests.post(f'{BASE_URL}/teams', json={
    'name': 'Engineering Team',
    'description': 'Backend engineering team'
})
team_id = team_response.json()['id']
print(f"Created team: {team_id}")

# 2. Add team members
members = [
    {'name': 'Alice', 'email': 'alice@company.com', 'role': 'Lead'},
    {'name': 'Bob', 'email': 'bob@company.com', 'role': 'Engineer'},
    {'name': 'Carol', 'email': 'carol@company.com', 'role': 'Engineer'}
]

member_ids = []
for member in members:
    member['team_id'] = team_id
    response = requests.post(f'{BASE_URL}/members', json=member)
    member_ids.append(response.json()['id'])

# 3. Record some communications
requests.post(f'{BASE_URL}/communications', json={
    'sender_id': member_ids[0],
    'receiver_id': member_ids[1],
    'team_id': team_id,
    'communication_type': 'face-to-face',  # Most valuable!
    'duration_minutes': 15,
    'is_group': False,
    'is_cross_team': False
})

# 4. Calculate metrics
calc_response = requests.post(
    f'{BASE_URL}/calculate/{team_id}',
    json={'days': 30}
)
metrics = calc_response.json()

# 5. View results
print(f"Energy: {metrics['energy']['energy_score']}")
print(f"Engagement: {metrics['engagement']['engagement_score']}")
print(f"Exploration: {metrics['exploration']['exploration_score']}")
print(f"Overall: {metrics['overall_score']}")
```

## Understanding Your Scores

### Energy Score (0-100)
- **80-100**: Excellent - Frequent face-to-face communication
- **60-79**: Good - Regular communication mix
- **40-59**: Fair - Mostly electronic communication
- **0-39**: Poor - Infrequent or limited communication

### Engagement Score (0-100)
- **80-100**: Excellent - All members participate equally
- **60-79**: Good - Most members active
- **40-59**: Fair - Some imbalance in participation
- **0-39**: Poor - Few members dominate

### Exploration Score (0-100)
- **80-100**: Excellent - Frequent cross-team collaboration
- **60-79**: Good - Regular external engagement
- **40-59**: Fair - Some external interaction
- **0-39**: Poor - Isolated team

## Communication Types (By Value)

Record communications in order of research-proven value:

1. **face-to-face** - Most valuable (50 points)
2. **meeting** - Group discussions
3. **video-call** - Remote face-time
4. **phone** - Voice calls
5. **chat** - Quick messages
6. **email** - Least valuable (5 points)
7. **other** - Catch-all

## Key API Endpoints

All endpoints use the `/api/v1/` prefix:

### Teams
- `POST /api/v1/teams` - Create team
- `GET /api/v1/teams` - List all teams
- `GET /api/v1/teams/{id}` - Get team details

### Members
- `POST /api/v1/members` - Add member
- `GET /api/v1/members?team_id={id}` - List members

### Communications
- `POST /api/v1/communications` - Record single communication
- `POST /api/v1/communications/bulk` - Record multiple communications
- `GET /api/v1/communications?team_id={id}` - Get communications

### Metrics
- `POST /api/v1/calculate/{team_id}` - Calculate Three E's metrics
- `GET /api/v1/metrics/{team_id}` - Get latest metrics
- `GET /api/v1/metrics/{team_id}/history` - Get metrics over time
- `GET /api/v1/metrics/all` - Compare all teams

### Network Analysis
- `GET /api/v1/network/{team_id}` - Analyze communication network
- `GET /api/v1/network/{team_id}/centrality` - Find key communicators
- `GET /api/v1/network/{team_id}/communities` - Detect subgroups

**Full API documentation**: See `API.md`

## Health Monitoring

Check if the application is running:

```bash
# Health check
curl http://localhost:5000/health

# Expected response:
# {"status": "healthy", "database": "connected"}
```

## Rate Limits

The API has rate limits to prevent abuse:

- **Default**: 200 requests/day, 50/hour
- **Calculations**: 10/hour (resource intensive)
- **Bulk operations**: 20/hour
- **Network analysis**: 30/hour

Check headers in responses:
- `X-RateLimit-Limit` - Your limit
- `X-RateLimit-Remaining` - Requests remaining
- `X-RateLimit-Reset` - Reset time

## Development

### Running Tests

```bash
# Activate environment
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov

# Run specific test file
pytest tests/test_calculator.py -v
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "add new column"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

See `MIGRATIONS.md` for details.

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy app.py
```

## Troubleshooting

### "Cannot connect to database"
**Docker**: Check containers are running: `docker-compose ps`  
**Local**: Make sure database is initialized: `alembic upgrade head`

### "Port 5000 already in use"
Find and stop the process:
```bash
lsof -ti:5000 | xargs kill -9
```

### "Module not found"
Make sure dependencies are installed:
```bash
uv sync
```

### "Rate limit exceeded"
You've hit the API rate limit. Wait for the reset time shown in `X-RateLimit-Reset` header.

## Next Steps

1. ✅ **API is running** - You're ready to use it
2. 📊 **Read API.md** - Learn all endpoints
3. 🧪 **Try examples.py** - See real usage
4. 🔧 **Customize** - Add your teams and data
5. 📈 **Monitor** - Track metrics over time

## Production Deployment

For production use:

### Environment Variables

Edit `.env` file:

```bash
# Use PostgreSQL in production
DATABASE_URL=postgresql://user:password@host:5432/orgnet

# Use strong secret key
SECRET_KEY=your-long-random-secret-key-here

# Disable debug mode
DEBUG=False

# Set host/port
API_HOST=0.0.0.0
API_PORT=5000
```

### Docker Production

```bash
# Build and start
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head

# View logs
docker-compose logs -f

# Scale if needed
docker-compose up -d --scale api=3
```

### With Gunicorn (if not using Docker)

```bash
# Install gunicorn (if not already in dependencies)
uv add gunicorn

# Run with 4 workers
uv run gunicorn -w 4 -b 0.0.0.0:5000 app:create_app
```

## Resources

- **README.md** - Full documentation
- **API.md** - Complete API reference
- **CONTRIBUTING.md** - Development guidelines
- **MIGRATIONS.md** - Database migration guide
- **ROADMAP.md** - Future plans

## MIT Research Background

This application is based on research from MIT's Human Dynamics Laboratory:

> "Patterns of communication are the most important predictor of a team's success."  
> — Alex Pentland, MIT Media Lab

**Key Findings:**
1. Face-to-face communication is most valuable
2. Balanced participation drives performance
3. External exploration brings innovation
4. Content matters less than communication patterns

**Published in:** Harvard Business Review, "The New Science of Building Great Teams" (April 2012)

---

**You're ready to go!** 🚀

Start with: `docker-compose up -d` or `uv run python -m app.app`
