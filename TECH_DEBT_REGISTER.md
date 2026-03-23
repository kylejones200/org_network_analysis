# Technical Debt Register

| ID | Title | Severity | Area | Impact | Recommended Fix | Effort |
|----|-------|----------|------|--------|-----------------|--------|
| T1 | Validate update_team with TeamUpdate schema | Critical | API | Arbitrary field overwrite (id, created_at) | Use validate_request(TeamUpdate, data); pass only allowed fields to repo | 1h |
| T2 | Validate calculate_metrics with MetricsCalculate | High | API | Invalid days/dates cause errors | Use validate_request(MetricsCalculate, data) | 1h |
| T3 | Use text() for SQLAlchemy raw SQL in health check | High | API | SQLAlchemy 2.0 rejects plain string | `from sqlalchemy import text`; `session.execute(text("SELECT 1"))` | 15m |
| T4 | Restrict TeamRepository.update to allowlist | Critical | Data | Client can overwrite id, created_at | Only allow `name`, `description` in update | 30m |
| T5 | Sanitize error in health 503 response | High | API | Internal details exposed | Return generic message; log full error | 15m |
| T6 | Docker HEALTHCHECK uses requests | Critical | Ops | requests not in prod deps; health fails | Use `curl -f http://localhost:5000/health` | 15m |
| T7 | Bound days/limit query params | Medium | API | Heavy queries possible | Use NetworkAnalysisParams; limit 1-100 for history | 1h |
| T8 | Remove or integrate formatters, export_utils, validators | Low | Code | Dead code, confusion | Delete if unused; or wire into API | 2h |
| T9 | Consolidate date range parsing | Low | Code | Duplication | Extract to date_utils; use in all endpoints | 1h |
| T10 | Add authentication | Critical | Security | API fully open | API key or JWT; or document proxy requirement | 4h+ |
| T11 | Load .env in Config | Medium | Config | python-dotenv installed but unused | `load_dotenv()` in config startup | 15m |
| T12 | Fail on default SECRET_KEY in production | Medium | Security | Accidental prod with dev key | Check env; raise if default and DEBUG=False | 30m |

---

## Resolved

| ID | Title | Resolution |
|----|-------|------------|
| T1 | update_team validation | Done |
| T2 | calculate_metrics validation | Done |
| T3 | Health check text() | Done |
| T4 | Repository update allowlist | Done |
| T5 | Health 503 sanitization | Done |
| T6 | Docker HEALTHCHECK | Done |
| T7 | Bound days/limit | Done (network, metrics history) |
