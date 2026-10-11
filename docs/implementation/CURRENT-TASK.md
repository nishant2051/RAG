# TASK-004 — SQLite, SQLAlchemy & Alembic Foundation

**Milestone:** M1 — Foundation
**Depends on:** TASK-002 (`e322247`, reported complete). TASK-003 (`b89160d`) is also complete but does not need modification.
**Status:** Complete — compile/import, validated path, disposable migration/repeat upgrade, SQLite pragma/session and backend liveness checks passed; no automated tests added.
**Carryover:** TASK-001 combined backend/frontend smoke check remains pending; do not mark complete unless actually performed.

## Objective

Add the **persistence infrastructure only**: a local SQLite database engine and session factory, SQLite connection pragmas, shared SQLAlchemy declarative metadata, and an operational Alembic migration setup. Do not create application/domain tables yet. This task must not change the existing FastAPI health/error contracts or frontend shell.

## Read scope and discovery budget

1. Follow root `AGENTS.md` and `docs/implementation/CURRENT-TASK.md` (this file).
2. Read the **relevant backend section only** of `docs/implementation/PROJECT-MAP.md`; inspect actual `backend/pyproject.toml`, existing configuration/settings, backend package layout and entry point, existing `.env.example`, `.gitignore`, and Makefile targets as necessary.
3. Examine Alembic or SQLAlchemy files *if already present* and adapt instead of creating parallel infrastructure.
4. Do **not** read `docs/reference/`, prior tasks, the full implementation roadmap, or unrelated frontend code. Keep shell output bounded.
5. Paths and names below are **suggested**, not verified against the developer's local checkout. Confirm actual locations before editing. If major restructuring is required, stop and report.

## Suggested changes (adjust to real structure)

- `backend/pyproject.toml` — add only necessary compatible `SQLAlchemy` and `alembic` dependencies.
- `backend/app/infrastructure/database.py` or `backend/app/infrastructure/database/{engine.py,base.py}` — synchronous SQLite engine, `sessionmaker`, shared declarative `Base`/metadata, and a scoped `get_db_session()` FastAPI dependency if useful. Prefer a small implementation over premature repository abstractions.
- `backend/app/config/settings.py` — add a validated local SQLite path/database URL setting, preserving existing environment validation.
- `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/<revision>_initial.py` — migration setup and one **empty baseline migration**. Avoid creating any product tables.
- `.env.example`, `.gitignore`, Makefile/README — only minimal local configuration, data-directory ignore, migration commands, and startup instructions if needed.
- `docs/implementation/PROJECT-MAP.md` — add *verified* exported persistence entry points and migration paths.
- `docs/implementation/IMPLEMENTATION-PLAN.md` — mark TASK-004 complete after checks, preserving unrelated edits.

## Required behavior

1. Use **SQLite with SQLAlchemy 2.x** and a single configured local database file (e.g. under an ignored `data/` directory); do not hardcode a developer-specific absolute path. Resolve relative paths predictably from a documented project/backend root and create the parent directory when appropriate. Do not permit an accidental production remote DB URL for this local-first task.
2. Keep settings validated and consistent with TASK-002's configuration conventions. Missing optional settings should yield a usable local default; malformed configuration must fail with a clear error.
3. Configure SQLite connections with `PRAGMA foreign_keys=ON`, a reasonable `busy_timeout` (e.g. 5000 ms), and WAL journal mode for file-backed SQLite. Account for WAL's file-backed requirement rather than assuming it works with `:memory:`. Keep transactions short; **do not** turn on broad autocommit or keep a session open across long-running calls.
4. Expose a reusable engine/session factory and declarative metadata that subsequent document/chat tasks can import. Ensure per-operation sessions are closed or returned to the pool; do not store a mutable global Session instance.
5. Configure Alembic to use the **same DB path/settings and shared metadata** as the application, with an initial empty revision. Migrations must be executable from a documented working directory/command. Do not automatically run schema migrations on every API startup.
6. Migration should be repeatable: upgrading a fresh disposable database to head succeeds, and repeating the upgrade does not create duplicate objects. Keep migration code free of product entities and seed data.
7. Preserve `/health/live`, `/health/ready`, `/api/v1/system/dependencies`, existing `X-Request-ID`, CORS, and error behavior. Database integration with readiness/diagnostics is **not** required in this task; do not misreport dependency health as checked.
8. Protect local runtime data: ignore SQLite `.db`/`.sqlite` files, WAL/SHM sidecars, and local storage directories without ignoring Alembic scripts or project implementation docs.

## Exclusions

- No `documents`, `content_objects`, `index_generations`, `chat_*`, job, or other domain tables; those are later tasks.
- No Qdrant, Ollama, worker, ingestion, upload APIs, or frontend changes.
- No test files, test frameworks, fixtures, mocks, or permanent verification scripts.
- No broad refactoring, dependency upgrades unrelated to SQLAlchemy/Alembic, or speculative async/database repository layers.

## Lightweight verification (no automated test cases)

1. Install/update only necessary backend dependencies. Run Python compile/import checks for settings, database infrastructure, and Alembic configuration.
2. Using a **throwaway SQLite file/path**, run `alembic upgrade head`; verify the Alembic version table exists, and rerun to verify no-op behavior. Optionally inspect `alembic current`/`heads`. Do not use or overwrite a developer's existing database.
3. Inspect SQLite pragmas through a brief manual Python/SQLite command to confirm `foreign_keys=1`, WAL mode on file-backed DB, and configured busy timeout. This is a one-off smoke check, **not** a committed automated test.
4. If practical, launch the existing backend and manually check `/health/live` still responds. Report the pending TASK-001 combined scaffold smoke check separately; don't expand this task to fix unrelated frontend problems.
5. Run `git diff --check`; inspect short Git status and preserve unrelated staged/unstaged work. Note that the TASK-003 plan row may have been updated outside its prior commit; preserve it.

## Completion and stopping conditions

- SQLite engine, session factory/Base, validated local config, and Alembic baseline are present and documented with actual paths.
- Required lightweight checks pass or any unperformed manual checks are explicitly listed as pending.
- Update only necessary `PROJECT-MAP.md` entries and the TASK-004 status row. Commit **only** verified TASK-004 files plus its intended handoff updates; do not stage unrelated changes. If blocked, report without committing.
- Give a concise handoff: status/commit; files changed; checks passed/pending; blockers. **Stop after TASK-004. Do not start TASK-005.**
