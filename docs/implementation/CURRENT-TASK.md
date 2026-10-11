# TASK-005 — Local Qdrant Service and Connection Adapter

**Milestone:** M1 — Foundation
**Status:** Complete — available lightweight checks passed; Docker verification pending (Docker CLI unavailable).
**Depends on:** TASK-002 and TASK-004 (completed)
**Goal:** Run Qdrant locally through Docker Compose and provide a small typed Python adapter to check connectivity. No collections, vectors, indexing, or retrieval yet.

## Starting state (reported)

- FastAPI backend exists with typed settings, structured errors, and `/health/live`.
- SQLite, SQLAlchemy, and Alembic foundation is complete (commit `0112df0`).
- Frontend scaffold exists. Working tree reported clean.
- TASK-001 combined backend/frontend smoke check remains pending; do not mark it complete unless actually performed.

## Context boundaries

- Follow repository `AGENTS.md`.
- Read this file, relevant `PROJECT-MAP.md` entries, and only the files needed for settings, dependencies, health routing, Docker configuration, and development commands.
- **Do not read** PRD, System Architecture, Database Design, API Specification, RAG Technical Design, completed tasks, or the full implementation plan.
- The paths below are suggestions: inspect the existing repository structure first and adapt naming to actual conventions. Do not create duplicate settings, error or health modules.

## Work to implement

1. **Local Qdrant service**
   - Add or update a narrowly scoped Docker Compose configuration (for example `docker/compose.yml` or the repository's existing Compose file) with a single `qdrant/qdrant` service.
   - Use an explicit, configurable image tag rather than `latest`, and document the chosen tag.
   - Bind Qdrant HTTP port **6333** to `127.0.0.1` only. Expose gRPC port 6334 only if needed; otherwise omit it.
   - Persist Qdrant data to a named volume or a project-owned data directory that is ignored by Git.
   - Do not add Redis, PostgreSQL, authentication infrastructure, cloud services, or unrelated containers.

2. **Typed configuration**
   - Extend the existing backend settings with `QDRANT_URL` (default `http://127.0.0.1:6333`) and a reasonable, configurable request timeout.
   - Update the example environment file and README with local startup/configuration instructions.
   - Keep external-service configuration optional at application startup; FastAPI must still start when Qdrant is stopped.

3. **Minimal Qdrant connection adapter**
   - Add the `qdrant-client` dependency using the project's existing dependency-management style.
   - Create a small infrastructure adapter that constructs/closes the client and performs a bounded connectivity/health probe. Prefer the client's available lightweight health/check operation or an appropriate documented HTTP health endpoint.
   - Handle connection errors/timeouts as typed dependency-unavailable failures using existing error conventions; don't leak raw exception details through HTTP responses.
   - Avoid creating collections, payload indexes, inserting test vectors, or defining the final vector-store interface in this task.

4. **Health integration**
   - If an existing readiness/dependency diagnostics route exists, add Qdrant status there without changing the published liveness semantics.
   - Otherwise add only the smallest appropriate diagnostics integration within the current health-route conventions. Don't invent the full final health API prematurely.
   - `/health/live` must remain available with Qdrant offline. A Qdrant failure should be reported as degraded/unavailable, not crash startup.

5. **Development commands and handoff**
   - Add concise Makefile commands for Qdrant start/stop/status if consistent with existing conventions.
   - Update `PROJECT-MAP.md` only with modules and interfaces actually implemented; update current task status in the normal local progress records.

## Boundaries / non-goals

- No automated tests, test files, fixtures, mocks, or test frameworks.
- No application-specific Qdrant collections, vector dimensions, embedding models, document schema, indexing, or retrieval logic. TASK-006 introduces Ollama integration.
- No frontend changes, UI features, unrelated refactoring, or dependency upgrades.
- Do not modify unrelated staged/untracked work. If an unexpected architectural dependency requires broad exploration, **stop and report the blocker**.

## Lightweight verification (without writing tests)

- Run Python syntax/import checks and the existing dependency/metadata checks.
- Validate Docker Compose configuration (`docker compose config`, using the correct compose path).
- If Docker is available, bring Qdrant up and confirm the adapter reports healthy; stop Qdrant and confirm the API still starts and reports Qdrant unavailable through the chosen diagnostics route.
- Verify `/health/live` works with Qdrant unavailable.
- Run `git diff --check` on the scoped changes.
- If Docker is unavailable, report the exact verification not performed; do not claim service connectivity was checked.
- The combined TASK-001 smoke check remains pending unless independently completed.

## Done when

- A developer can start persistent, loopback-bound Qdrant locally through the documented command.
- Backend configuration and the adapter can detect a healthy or unavailable Qdrant without crashing FastAPI.
- No app collections or vector operations have been introduced.
- Changes pass the available lightweight checks, and one **focused Git commit** is created only after prescribed verification succeeds. Preserve unrelated changes.
- Return a brief handoff: commit hash, changed areas, checks run/skipped, blockers, and pending manual checks. **Stop after TASK-005.**

## Verification handoff

- Python compile/import and package metadata checks, `uv lock --check`, and `uv pip check` passed.
- FastAPI started on loopback port 18005 (8000 already occupied). With Qdrant unavailable, `/health/live` returned 200/alive and dependency diagnostics returned 200 with `qdrant: unavailable`; readiness retained `dependencies: not_checked`. The smoke-check server was stopped afterward.
- Makefile Qdrant command dry runs and scoped `git diff --check` passed.
- Docker CLI is not installed: Compose configuration validation, container startup, healthy adapter connectivity, persistence across restart, and container stop/offline verification remain pending. No live Qdrant connectivity is claimed.
- TASK-001 combined backend/frontend smoke check remains pending. No automated tests were added or run.
