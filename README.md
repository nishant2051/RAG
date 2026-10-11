# Local RAG

A local, single-user RAG application scaffold. Product features are not implemented yet.

Requires Python 3.11+ (including venv/pip), Node.js 22.12+ and npm, and Make.
The Makefile uses macOS/Linux virtual environment paths.

From the repository root:

```sh
make setup
make dev
```

Backend: http://127.0.0.1:8000. Frontend: http://127.0.0.1:5173.
The backend currently has no endpoints, so HTTP requests return 404.
Use `make build-frontend` to type-check and produce `frontend/dist/`.
Run `make help` for available commands.

`.env.example` documents proposed local URLs; the scaffold does not consume them.
Qdrant, Ollama, database storage, document ingestion, and chat are future tasks.
Documentation under `docs/` is maintained locally and ignored by Git.

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
