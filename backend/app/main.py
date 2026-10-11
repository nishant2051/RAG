"""Minimal ASGI entry point; product endpoints are added in future tasks."""

from fastapi import FastAPI

app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
