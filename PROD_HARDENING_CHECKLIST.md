# Production Hardening Checklist

Concrete, verifiable items. Check each before production deployment.

---

## Must Fix Before Production

- [ ] **SECRET_KEY** — Set from secure secret store; never use default (warning logged if default in non-DEBUG)
- [ ] **Authentication** — Add API key, JWT, or auth proxy; API is currently unauthenticated
- [x] **update_team** — Validate with TeamUpdate schema; restrict updatable fields ✓
- [x] **calculate_metrics** — Validate with MetricsCalculate schema ✓
- [x] **Health check** — Use `text("SELECT 1")` for SQLAlchemy 2.0 ✓
- [x] **Health 503** — Do not expose internal error detail ✓
- [x] **Docker HEALTHCHECK** — Use curl, not requests ✓
- [x] **docker-compose** — Uses ${POSTGRES_PASSWORD}, ${SECRET_KEY}, ${CORS_ORIGINS}; set in .env for prod ✓
- [ ] **CORS_ORIGINS** — Set to actual allowed origins in prod (e.g. `https://app.example.com`)
- [x] **DEBUG** — Config default False; ensure `DEBUG=False` in prod ✓

---

## Verify

- [ ] Run `uv sync --frozen` and `uv run pytest` — all tests pass
- [ ] Run `uv run ruff check .` — no errors
- [ ] Run `docker build .` and `docker run` — container starts
- [ ] Hit `/health` — returns 200 when DB connected
- [ ] Hit `/health` with DB down — returns 503 with generic message (no stack trace)
- [ ] PUT /api/v1/teams/1 with `{"id": 999}` — id not changed (validation)
- [ ] POST /api/v1/calculate/1 with `{"days": 999999}` — rejected or bounded

---

## Should Fix (Pre-Production)

- [ ] Add pagination to GET /api/v1/teams, /members, /communications
- [ ] Run Alembic migrations in Docker startup (not just init_db)
- [x] Add `load_dotenv()` in config ✓
- [ ] Consider structured logging (JSON) for log aggregation

---

## Optional (Post-Launch)

- [ ] Request ID / correlation ID for tracing
- [ ] APM or distributed tracing
- [x] Remove unused modules (utils, formatters, export_utils, validators) ✓
- [ ] Consolidate date range parsing
