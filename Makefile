.PHONY: dev help setup setup-backend setup-frontend dev-backend dev-frontend build-frontend migrate qdrant-start qdrant-stop qdrant-status

help:
	@echo "make qdrant-start/stop/status  Manage persistent local Qdrant (Docker Compose)"
	@echo "make migrate         Upgrade local SQLite schema (RAG_DATABASE_PATH optional)"
	@echo "make dev             Start both services; Ctrl+C stops both"
	@echo "make setup           Install backend and frontend dependencies"
	@echo "make dev-backend     Start backend on 127.0.0.1:8000"
	@echo "make dev-frontend    Start frontend on 127.0.0.1:5174"
	@echo "make build-frontend  Type-check and build frontend"

setup: setup-backend setup-frontend

setup-backend:
	cd backend && uv sync --locked

setup-frontend:
	cd frontend && npm install

dev-backend:
	cd backend && uv run --locked python -m app.main

dev-frontend:
	cd frontend && npm run dev -- --port 5174 --strictPort

build-frontend:
	cd frontend && npm run build

dev:
	bash scripts/start.sh

# Run from repository root; RAG_DATABASE_PATH is relative to backend/.
migrate:
	cd backend && uv run --locked alembic upgrade head

qdrant-start:
	docker compose --project-directory . -f docker/compose.yml up -d qdrant

qdrant-stop:
	docker compose --project-directory . -f docker/compose.yml stop qdrant

qdrant-status:
	docker compose --project-directory . -f docker/compose.yml ps -a qdrant
