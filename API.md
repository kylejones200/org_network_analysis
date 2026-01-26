# API Reference

## Base URL
```
http://localhost:5000
```

## API Versioning

All endpoints are versioned under `/api/v1/`. Legacy unversioned endpoints (`/api/*`) are supported for backward compatibility but deprecated.

**Recommended:** Use `/api/v1/*` endpoints for all new development.

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Default:** 200 requests per day, 50 per hour
- **Calculations:** 10 per hour (resource intensive)
- **Bulk operations:** 20 per hour
- **Network analysis:** 30 per hour (computationally expensive)

Rate limit information is included in response headers:
- `X-RateLimit-Limit` - Request limit
- `X-RateLimit-Remaining` - Remaining requests
- `X-RateLimit-Reset` - Time when limit resets

### 429 Too Many Requests
When you exceed the rate limit, you'll receive:
```json
{
  "error": "Rate limit exceeded"
}
```

## Teams

### List All Teams
```http
GET /api/v1/teams
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Product Team",
    "description": "Product development team",
    "created_at": "2026-01-20T10:00:00Z",
    "member_count": 5
  }
]
```

### Get Team Details
```http
GET /api/v1/teams/{team_id}
```

### Create Team
```http
POST /api/v1/teams
Content-Type: application/json

{
  "name": "Product Team",
  "description": "Product development team"
}
```

### Update Team
```http
PUT /api/v1/teams/{team_id}
Content-Type: application/json

{
  "name": "Updated Team Name",
  "description": "Updated description"
}
```

### Delete Team
```http
DELETE /api/v1/teams/{team_id}
```

## Team Members

### List Members
```http
GET /api/v1/members?team_id={team_id}
```

### Add Member
```http
POST /api/v1/members
Content-Type: application/json

{
  "name": "Alice Smith",
  "email": "alice@company.com",
  "team_id": 1,
  "role": "Engineer"
}
```

### Delete Member
```http
DELETE /api/v1/members/{member_id}
```

## Communications

### Get Communications
```http
GET /api/v1/communications?team_id={team_id}&days=30
```

### Record Communication
```http
POST /api/v1/communications
Content-Type: application/json

{
  "sender_id": 1,
  "receiver_id": 2,
  "team_id": 1,
  "communication_type": "face-to-face",
  "duration_minutes": 15,
  "is_group": false,
  "is_cross_team": false,
  "message_content": "Optional message content"
}
```

**Communication Types:**
- `face-to-face` - Highest value (50 points in Energy score)
- `meeting` - Group communication
- `video-call` - Remote communication
- `phone` - One-on-one voice
- `chat` - Real-time messaging
- `email` - Asynchronous
- `other` - Other types

### Bulk Create Communications
**Rate Limit:** 20 per hour

```http
POST /api/v1/communications/bulk
Content-Type: application/json

{
  "communications": [
    {
      "sender_id": 1,
      "receiver_id": 2,
      "team_id": 1,
      "communication_type": "face-to-face",
      "duration_minutes": 15
    },
    ...
  ]
}
```

## Metrics

### Calculate Metrics
**Rate Limit:** 10 per hour (resource intensive)

```http
POST /api/v1/calculate/{team_id}
Content-Type: application/json

{
  "days": 30
}
```

**Response:**
```json
{
  "team_id": 1,
  "calculation_period": {
    "start": "2025-12-21T00:00:00Z",
    "end": "2026-01-20T00:00:00Z"
  },
  "energy": {
    "energy_score": 75.5,
    "total_communications": 150,
    "face_to_face_ratio": 0.6
  },
  "engagement": {
    "engagement_score": 82.3,
    "participation_rate": 1.0,
    "balance_score": 0.85,
    "gini_coefficient": 0.15
  },
  "exploration": {
    "exploration_score": 45.0,
    "cross_team_communications": 20,
    "members_exploring": 3
  },
  "overall_score": 70.2
}
```

### Get Latest Metrics
```http
GET /api/v1/metrics/{team_id}
```

### Get Metrics History
```http
GET /api/v1/metrics/{team_id}/history?limit=10
```

### Get All Teams Metrics
```http
GET /api/v1/metrics/all
```

## Network Analysis

### Analyze Network
**Rate Limit:** 30 per hour (computationally expensive)

```http
GET /api/v1/network/{team_id}?days=30
```

**Response:**
```json
{
  "density": 0.65,
  "is_connected": true,
  "num_nodes": 5,
  "num_edges": 8,
  "most_central_member_id": 3,
  "potential_bottlenecks": [3]
}
```

### Detect Communities
**Rate Limit:** 30 per hour

```http
GET /api/v1/network/{team_id}/communities?days=30
```

### Calculate Centrality
**Rate Limit:** 30 per hour

```http
GET /api/v1/network/{team_id}/centrality?days=30
```

**Response:**
```json
{
  "centrality_metrics": {
    "degree": {"1": 0.75, "2": 0.5, ...},
    "betweenness": {"1": 0.3, "2": 0.1, ...},
    "closeness": {"1": 0.8, "2": 0.7, ...}
  },
  "key_roles": {
    "connectors": [
      {"member_id": 3, "name": "Alice", "score": 0.45}
    ],
    "influencers": [...],
    "hubs": [...]
  }
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error type",
  "detail": "Detailed error message"
}
```

**Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `409` - Conflict (integrity violation)
- `422` - Validation Error
- `500` - Internal Server Error
