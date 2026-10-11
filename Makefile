.PHONY: dev help setup setup-backend setup-frontend dev-backend dev-frontend build-frontend

help:
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
