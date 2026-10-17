"""Persist uploads and transactional, 24-hour idempotency reservations."""
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile
from starlette.concurrency import run_in_threadpool

from app.api.errors import AppError
from app.config.settings import Settings
from app.documents.models import Document, UploadKey
from app.infrastructure.storage.local import publish, stage_upload

logger = logging.getLogger(__name__)


def persist(session: Session, temporary: Path, digest: str, filename: str,
            key: str | None, settings: Settings) -> dict:
    try:
        session.execute(text("BEGIN IMMEDIATE"))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        previous = session.get(UploadKey, key) if key else None
        if previous and previous.expires_at > now:
            document = session.get(Document, previous.document_id)
            if document.content_sha256 != digest or document.original_filename != filename:
                raise AppError("idempotency_conflict", "Key already used for a different upload", 409)
        else:
            if previous:
                session.delete(previous)
                session.flush()
            reference = publish(temporary, settings.storage_root, digest)
            document = Document(document_id=str(uuid4()), original_filename=filename,
                                content_sha256=digest, object_reference=reference,
                                created_at=now, status="stored_pending_indexing")
            session.add(document)
            session.flush()
            if key:
                session.add(UploadKey(key=key, document_id=document.document_id,
                                      expires_at=now + timedelta(hours=24)))
        result = {"document_id": document.document_id, "job_id": None, "status": document.status}
        session.commit()
        return result
    except BaseException:
        session.rollback()
        raise


async def store_upload(file: UploadFile, filename: str, key: str | None,
                       settings: Settings, session: Session, request_id: str) -> dict:
    temporary = None
    try:
        temporary, digest = await stage_upload(file, settings.storage_root, settings.upload_max_bytes)
        return await run_in_threadpool(persist, session, temporary, digest, filename, key, settings)
    except AppError:
        raise
    except Exception as exc:
        logger.error("Upload persistence failed request_id=%s error_type=%s", request_id, type(exc).__name__)
        raise AppError("upload_failed", "Unable to store upload", 500) from exc
    finally:
        if temporary is not None:
            # Published objects are retained on DB failure: another record may use them.
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                logger.error("Upload temporary cleanup failed request_id=%s", request_id)
