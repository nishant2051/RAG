"""Resource-shaped JSON errors; unexpected exceptions never expose internals."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def error_response(request: Request, error: AppError) -> JSONResponse:
    request_id = request.state.request_id
    return JSONResponse(status_code=error.status_code, content={"error": {
        "code": error.code, "message": error.message,
        "details": error.details, "request_id": request_id,
    }}, headers={"X-Request-ID": request_id})


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def application_error(request: Request, exc: AppError) -> JSONResponse:
        return error_response(request, exc)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        response = error_response(request, AppError(f"http_{exc.status_code}", str(exc.detail), exc.status_code))
        if exc.headers:
            response.headers.update({key: value for key, value in exc.headers.items() if key.lower() != "x-request-id"})
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(request, AppError("validation_error", "Request validation failed", 422))
