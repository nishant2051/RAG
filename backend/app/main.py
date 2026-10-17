"""Local FastAPI entry point. Run python -m app.main to use RAG_* settings."""

import logging
import re
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from app.api.errors import AppError, error_response, register_error_handlers
from app.api.health import router
from app.documents.router import router as documents_router
from app.config.settings import Settings, load_settings

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    configured_host = f"[{settings.host}]" if ":" in settings.host else settings.host
    trusted_hosts = "|".join(re.escape(host) for host in {"localhost", "127.0.0.1", "[::1]", configured_host})
    application = FastAPI(title="Local RAG API")
    application.state.settings = settings
    register_error_handlers(application)
    application.include_router(router)
    application.include_router(documents_router)
    application.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                               allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["X-Request-ID", "Idempotency-Key", "Content-Type"],
                               expose_headers=["X-Request-ID"])

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        supplied = request.headers.get("X-Request-ID", "")
        request.state.request_id = supplied if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", supplied) else str(uuid4())
        host = request.headers.get("host", "")
        if not re.fullmatch(rf"(?:{trusted_hosts})(?::[0-9]{{1,5}})?", host):
            response = error_response(request, AppError("invalid_host", "Untrusted host", 400))
        else:
            try:
                response = await call_next(request)
            except Exception:
                logger.error("Unhandled server error request_id=%s", request.state.request_id)
                response = error_response(request, AppError("internal_error", "Internal server error", 500))
        response.headers["X-Request-ID"] = request.state.request_id
        logger.info("Request request_id=%s status=%s", request.state.request_id, response.status_code)
        return response

    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=app.state.settings.host, port=app.state.settings.port)
