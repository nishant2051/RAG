# Local RAG

A local, single-user RAG application scaffold. Product features are not implemented yet.

Requires uv, Python 3.11+, Node.js 22.12+ and npm, and Make.
Backend dependencies are locked in `backend/uv.lock`. `uv sync --locked` creates
`backend/.venv`, which the startup script and VS Code debugger use.
The Makefile uses macOS/Linux virtual environment paths.

From the repository root:

```sh
make setup
make dev
```

Backend: http://127.0.0.1:8000. Frontend: http://127.0.0.1:5174.
The backend provides `/health/live`, `/health/ready`, and `/api/v1/system/dependencies` endpoints.
Use `make build-frontend` to type-check and produce `frontend/dist/`.
Run `make help` for available commands.

The backend reads explicitly exported environment variables, without loading `.env`.
SQLite storage is configured by `RAG_DATABASE_PATH` (default `data/rag.sqlite3`,
relative to `backend/`); run `make migrate` to apply its schema.
Ollama, document ingestion, and chat remain future tasks.
Implementation handoffs under `docs/implementation/` are tracked in Git.

Local Qdrant requires Docker with Compose:

```sh
make qdrant-start
make qdrant-status
export QDRANT_URL=http://127.0.0.1:6333
export QDRANT_TIMEOUT_SECONDS=3
make dev-backend
# In another terminal:
curl http://127.0.0.1:8000/api/v1/system/dependencies
make qdrant-stop
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8000/api/v1/system/dependencies
```

`docker/compose.yml` pins [Qdrant v1.15.5](https://github.com/qdrant/qdrant/releases/tag/v1.15.5),
with `QDRANT_IMAGE_TAG` configurable via an exported variable or root `.env`.
Only HTTP port 6333 is published, on `127.0.0.1`; gRPC is not published.
The `local-rag_qdrant_data` named volume persists across stop/start and Compose down;
do not use `down -v` unless intending to delete data. No collections are created.
The URL must use loopback HTTP(S); timeout is an integer from 1 to 60 seconds.
Defaults match the exports above. Qdrant is optional at API startup.
Dependency diagnostics return HTTP 200 with Qdrant `healthy` or `unavailable`,
using a bounded, request-scoped [server-info probe](https://api.qdrant.tech/api-reference/service/root).
SQLite/Ollama diagnostics remain placeholders. `/health/live` stays independent;
`/health/ready` retains its existing `dependencies: not_checked` response.
To validate Compose without starting it, run
`docker compose --project-directory . -f docker/compose.yml config`.

Manual smoke check: after setup, run both dev commands, confirm the backend reports
startup complete, and open the frontend URL to see the Local RAG scaffold page.

`make dev` starts both services and stops both with Ctrl+C. This combined command
runs without automatic backend reload; use `make dev-backend` and
`make dev-frontend` in separate terminals when you want backend reload.

For VS Code debugging, install the Python and Python Debugger extensions and
Chrome, open the repository root, and run `make setup` once. In Run and Debug,
select **Debug backend + frontend** and press F5. Set Python breakpoints in
`backend/app/` and TypeScript breakpoints in `frontend/src/`. Individual backend
and frontend debug configurations are also available. Stop existing dev servers
before debugging to free ports 8000 and 5173. Stopping the compound ends both
debug sessions; use **Tasks: Terminate Task** to stop the frontend Vite task.
