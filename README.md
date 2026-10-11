# Local RAG

A local, single-user RAG application scaffold. Product features are not implemented yet.

Requires Python 3.11+ (including venv/pip), Node.js 22.12+ and npm, and Make.
The Makefile uses macOS/Linux virtual environment paths.

From the repository root:

```sh
make setup
make dev-backend
```

In a second terminal:

```sh
make dev-frontend
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
