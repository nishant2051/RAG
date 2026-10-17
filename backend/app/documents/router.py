"""Exactly one multipart TXT/Markdown file, with bounded request consumption."""
import re
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile
from starlette.formparsers import MultiPartException
from starlette.exceptions import HTTPException

from app.api.errors import AppError
from app.documents.service import store_upload
from app.infrastructure.database import get_db_session

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


class UploadResult(BaseModel):
    document_id: UUID
    job_id: None = None
    status: Literal["stored_pending_indexing", "indexed"]


@router.post("", status_code=202, response_model=UploadResult)
async def upload_document(request: Request, session: Session = Depends(get_db_session)):
    settings = request.app.state.settings
    key = request.headers.get("Idempotency-Key")
    if key is not None and not re.fullmatch(r"[\x21-\x7e]{1,128}", key):
        raise AppError("validation_error", "Idempotency-Key must be 1–128 printable ASCII characters", 422)
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "multipart/form-data":
        raise AppError("unsupported_media_type", "Expected multipart/form-data", 415)
    received = 0

    async def limited_receive():
        nonlocal received
        message = await request.receive()
        received += len(message.get("body", b""))
        if received > settings.upload_max_bytes + 64 * 1024:
            raise MultiPartException("Upload exceeds size limit")
        return message

    bounded = Request(request.scope, receive=limited_receive)
    try:
        form = await bounded.form(max_files=1, max_fields=0)
    except HTTPException as exc:
        if received > settings.upload_max_bytes + 64 * 1024:
            raise AppError("upload_too_large", "Upload exceeds size limit", 413) from exc
        raise AppError("validation_error", "Invalid multipart upload; exactly one file is required", 422) from exc
    try:
        items = form.multi_items()
        if len(items) != 1 or items[0][0] != "file" or not isinstance(items[0][1], UploadFile):
            raise AppError("validation_error", "Exactly one file field is required", 422)
        file = items[0][1]
        filename = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
        if not filename or len(filename) > 255 or any(ord(c) < 32 or ord(c) == 127 for c in filename):
            raise AppError("validation_error", "Invalid display filename", 422)
        if not filename.lower().endswith((".txt", ".md")):
            raise AppError("unsupported_format", "Only .txt and .md files are supported", 415)
        return await store_upload(file, filename, key, settings, session, request.state.request_id)
    finally:
        await form.close()
