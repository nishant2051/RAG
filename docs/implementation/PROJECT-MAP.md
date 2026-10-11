# Project Map — Actual Codebase Inventory

**Status:** TASK-003 completed. TASK-001 combined scaffold manual smoke check remains pending.

## Root layout

- `backend/pyproject.toml`, `backend/uv.lock` — Python 3.11+ package; uv-managed, locked FastAPI/Uvicorn dependencies.
- `backend/app/__init__.py`, `backend/app/main.py` — backend package and minimal ASGI entry point.
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

`backend/app/main.py` exports `app` and `create_app`; `python -m app.main` and `make dev-backend` bind using validated `RAG_*` settings from `config/settings.py` (`Settings`, `load_settings`). `api/health.py` exports `router` for liveness, readiness and unconfigured dependency status; `api/errors.py` provides `AppError`, `error_response`, and `register_error_handlers`. Request IDs, local host/CORS restrictions, JSON errors and generated OpenAPI documentation are implemented. `frontend/src/main.tsx` renders `App` from `frontend/src/App.tsx`; three accessible placeholder views use local React state. `frontend/src/config.ts` exports `getApiBaseUrl`; invalid configuration is displayed in the shell. No API calls or feature integrations exist yet.

## Task authoring notes

- Task file lists real paths discovered in the repository; planned paths must be marked `proposed`.
- Only include relevant map sections in the Codex read scope.
- When a code path or interface changes, update its map entry in one or two lines, including file path and symbol name.
- Do not copy design documents into this map.
