# TASK-002 — FastAPI Entrypoint, Health, and Error Contracts

**Milestone:** M1 Foundation
**Depends on:** TASK-001 (`1879792`, reported complete; manual scaffold smoke check pending)
**Status:** Complete; TASK-002 installation, compile/import and loopback HTTP smoke checks passed. TASK-001 combined scaffold smoke check remains pending.

## Objective
Implement a minimal local-only FastAPI application with typed configuration, health endpoints, and consistent JSON errors. Do not integrate SQLite, Qdrant, Ollama, ingestion, or chat yet.

## Required context
1. Root `AGENTS.md`.
2. This `docs/implementation/CURRENT-TASK.md`.
3. Only backend scaffold files necessary to establish existing packaging, dependencies, app entry point, settings, and Makefile targets; relevant `PROJECT-MAP.md` entries only if necessary.

Do **not** read `docs/reference/`, the full implementation plan, prior tasks, or unrelated frontend files. Paths below are *suggested*, not assertions that they already exist. Adapt to actual TASK-001 scaffold layout rather than duplicating modules.

## Repository hygiene prerequisite
- Check `git status --short` and the relevant `.gitignore` rules without printing unrelated history.
- Ensure `AGENTS.md` and `docs/implementation/{CURRENT-TASK.md,PROJECT-MAP.md,IMPLEMENTATION-PLAN.md}` can be tracked. If blanket `docs/` ignores them, narrowly adjust `.gitignore` to unignore only `docs/implementation/` and keep `docs/reference/` ignored as intended. Do not force-add files blindly or commit reference documents.
- If this conflicts with the user's deliberate repository policy, stop and report it. Do not discard untracked files.
- Check that TASK-001's pending manual smoke check is documented; do not claim it passed unless actually performed.

## Suggested files (inspect before creating)
- `backend/app/main.py` — FastAPI application factory or app instance.
- `backend/app/config/settings.py` — typed environment-based settings.
- `backend/app/api/health.py` — liveness, readiness, diagnostics routes.
- `backend/app/api/errors.py` — typed app errors and exception handlers.
- `backend/pyproject.toml` — dependencies, only if needed.
- `.env.example` and `Makefile` — update only for app entry-point/config correctness.
- `docs/implementation/PROJECT-MAP.md` — actual entry points, only after verification.

## Required behavior
1. App serves locally (`127.0.0.1` by default). No credentials or cloud services required.
2. Implement validated settings for host, port, app environment, and allowed local CORS origins. Reject malformed settings with clear startup errors; no secrets committed.
3. `GET /health/live` returns `200` with a concise structured `alive` response whenever the process is running.
4. `GET /health/ready` reports basic API readiness. External dependency checks are **not** implemented here; reserve an explicit, non-misleading status field (e.g. `dependencies: not_checked`) instead of claiming Qdrant/Ollama healthy.
5. `GET /api/v1/system/dependencies` exposes dependency check status as `not_configured` or `not_checked` for SQLite/Qdrant/Ollama, without performing integrations prematurely. Exact payload may be simple and documented in code.
6. Add typed application errors mapped to resource-shaped standardized JSON:
   `{"error":{"code":"...","message":"...","details":{},"request_id":"..."}}`.
   Sanitize unexpected server errors; never return tracebacks in HTTP responses.
7. Generate/validate `X-Request-ID` (reasonable length/character bounds), include it in HTTP responses and error envelopes. Log concise request IDs rather than request bodies.
8. Enable CORS only for configured localhost development origins and sensible trusted hosts. No authentication at this stage.
9. Let FastAPI expose its generated OpenAPI documentation. Do not generate TypeScript clients in this task.

## Out of scope
- No SQLite engine/migrations or persistence models (TASK-004).
- No Qdrant, Docker configuration, or dependency probing (TASK-005).
- No Ollama/model adapters (TASK-006).
- No frontend changes unless needed to fix a direct scaffold blocker.
- No automated tests, test framework, fixtures, mocks, or test files.
- No unrelated refactoring or future endpoint implementations.

## Verification (no automated tests)
- Backend package installation/metadata and Python compile/import checks.
- Launch FastAPI on loopback; manually request `/health/live`, `/health/ready`, `/api/v1/system/dependencies`, and `/openapi.json`, and inspect expected status/content.
- Manually trigger one known application error path if practical and check standardized error plus `X-Request-ID`.
- `git diff --check` and a brief `git status --short` review.
- If manual server checks cannot be performed, report exactly which checks remain pending; do not report a full pass.

## Done when
- Backend starts locally without Qdrant or Ollama.
- Endpoints, typed settings, structured error handling, and request IDs function as specified.
- Only necessary files changed; `PROJECT-MAP.md` updated with **verified** actual symbols/paths.
- Repository tracking policy checked and resolved or reported as a blocker.
- After checks pass, make one focused commit excluding unrelated work; leave incomplete/blocking changes uncommitted.

## Completion response (brief)
- Status + commit hash
- Files changed
- Verification passed/pending
- Blockers/deviations, if any

**Stop after TASK-002. Do not begin TASK-003.**

## TASK-002 verification record

- Locked backend installation, package metadata, compile/import checks passed.
- Loopback HTTP checks passed for liveness, readiness, dependency placeholders and OpenAPI; invalid host exercised `AppError`, and unknown route returned the standard 404 envelope. Valid request ID echoed; malformed ID replaced.
- Local CORS and malformed settings manually checked; no automated tests created.
- Git tracking rules narrowed for the three implementation records; reference docs remain ignored. Existing user edits were preserved and excluded from the commit.
- TASK-001 combined backend/frontend scaffold smoke check remains pending; TASK-002 does not claim it passed.
