.PHONY: dev help setup setup-backend setup-frontend dev-backend dev-frontend build-frontend

help:
	@echo "make dev             Start both services; Ctrl+C stops both"
	@echo "make setup           Install backend and frontend dependencies"
	@echo "make dev-backend     Start backend on 127.0.0.1:8000"
	@echo "make dev-frontend    Start frontend on 127.0.0.1:5173"
	@echo "make build-frontend  Type-check and build frontend"

setup: setup-backend setup-frontend

setup-backend:
	python3 -m venv backend/.venv
	backend/.venv/bin/python -m pip install -e ./backend

setup-frontend:
	cd frontend && npm install

dev-backend:
	cd backend && .venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

dev-frontend:
	cd frontend && npm run dev -- --port 5173 --strictPort

build-frontend:
	cd frontend && npm run build

dev:
	bash scripts/start.sh
