# Project Map — Actual Codebase Inventory

**Status:** TASK-006 implemented and live Ollama checks passed; Docker Compose/live Qdrant verification pending (Docker CLI unavailable). TASK-001 combined scaffold manual smoke check remains pending.

## Root layout

- `backend/pyproject.toml`, `backend/uv.lock` — Python 3.11+ package; uv-managed, locked FastAPI/Uvicorn, SQLAlchemy/Alembic qdrant-client and HTTPX dependencies.
- `backend/app/__init__.py`, `backend/app/main.py` — backend package and minimal ASGI entry point.
- `backend/app/config/settings.py` — `Settings`, `load_settings`, `BACKEND_ROOT`; `RAG_DATABASE_PATH` accepts local file paths, defaults to `backend/data/rag.sqlite3`, and resolves relative paths from `backend/`. Environment variables must be exported explicitly.
- `backend/app/infrastructure/database.py` — shared `engine`, `SessionLocal`, `Base.metadata`, and scoped `get_db_session`; file-backed SQLite with foreign keys, WAL and 5000 ms busy timeout. Callers own short transaction boundaries; sessions close on dependency exit.
- `backend/app/infrastructure/qdrant.py` — `QdrantConnection`, `QdrantUnavailable`, `get_qdrant_connection`; request-scoped async HTTP client, bounded server-info connectivity probe, typed 503 failure and guaranteed close. No startup probe or vector operations.
- `backend/app/infrastructure/ollama.py` — `OllamaConnection`, `OllamaError`, `GenerationOptions`, `get_ollama_connection`; closable async model discovery/validation, Nomic document/query prefixes, non-truncating finite embeddings with observed `embedding_dimension`, bounded non-streaming generation with thinking disabled, typed failures. No startup calls or automatic downloads.
- `backend/app/config/settings.py` — exported `OLLAMA_BASE_URL` (loopback HTTP(S)), `OLLAMA_TIMEOUT_SECONDS` (1–300, default 120), `OLLAMA_EMBED_MODEL` and `OLLAMA_GENERATION_MODEL`; defaults use installed Nomic/Qwen3 tags.
- `docker/compose.yml` — single Qdrant service, configurable `QDRANT_IMAGE_TAG` default v1.15.5, loopback-only HTTP 6333 and persistent named volume. Makefile provides `qdrant-start`, `qdrant-stop`, `qdrant-status`.
- `backend/app/config/settings.py` — optional exported `QDRANT_URL` (loopback HTTP(S), default `http://127.0.0.1:6333`) and `QDRANT_TIMEOUT_SECONDS` (1–60, default 3).
- `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/script.py.mako`, `backend/alembic/versions/0001_initial.py` — shared engine/metadata and empty baseline `0001`; no product tables. Run `make migrate` from repository root or `uv run --locked alembic upgrade head` from `backend/`. Migrations are explicit, never API startup actions.
- `frontend/package.json`, `frontend/package-lock.json`, `frontend/tsconfig.json`, `frontend/index.html` — React/TypeScript/Vite setup and dependency lock.
- `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/style.css` — responsive application shell with local Documents, Chat and Diagnostics navigation.
- `frontend/src/config.ts`, `frontend/.env.example` — `getApiBaseUrl` validates loopback-only Vite API configuration; development default, explicit production configuration.
- `docs/implementation/` — tracked task/progress records; reference documentation remains ignored.
- `AGENTS.md` — existing repository instructions.
- `Makefile`, `.env.example`, `.gitignore`, `README.md` — local-development entry points.
- `scripts/start.sh` — starts both local services via `make dev` and cleans up on exit.
- `.vscode/launch.json`, `.vscode/tasks.json` — backend/frontend debug configurations and Vite startup task.

## Planned backend domains (create only when tasked)

- `documents/`, `collections/` — logical document and collection lifecycle.
- `ingestion/`, `jobs/` — parsers, chunking, persistent worker and checkpoints.
- `indexing/`, `embeddings/` — generations, profiles, Qdrant and embedding calls.
- `retrieval/`, `generation/`, `chat/` — search, context/prompt, streamed responses and sessions.
- `infrastructure/` — external adapters (SQLite, Qdrant, Ollama and filesystem).
- `api/`, `config/` — HTTP endpoints and typed settings.

## Implemented modules / exported interfaces

`backend/app/main.py` exports `app` and `create_app`; `python -m app.main` and `make dev-backend` bind using validated `RAG_*` settings from `config/settings.py` (`Settings`, `load_settings`). `api/health.py` exports `router` for independent liveness, unchanged readiness and dependency diagnostics (Qdrant `healthy`/`unavailable`; Ollama `healthy`/`models_missing`/`unavailable` with per-model availability; SQLite placeholder); `api/errors.py` provides `AppError`, `error_response`, and `register_error_handlers`. Request IDs, local host/CORS restrictions, JSON errors and generated OpenAPI documentation are implemented. `frontend/src/main.tsx` renders `App` from `frontend/src/App.tsx`; three accessible placeholder views use local React state. `frontend/src/config.ts` exports `getApiBaseUrl`; invalid configuration is displayed in the shell. No API calls or feature integrations exist yet.

## Task authoring notes

- Task file lists real paths discovered in the repository; planned paths must be marked `proposed`.
- Only include relevant map sections in the Codex read scope.
- When a code path or interface changes, update its map entry in one or two lines, including file path and symbol name.
- Do not copy design documents into this map.
