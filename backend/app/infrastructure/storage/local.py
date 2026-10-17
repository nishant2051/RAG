"""Server-owned temporary files and atomic content-addressed publication."""
import codecs
import hashlib
import os
import tempfile
from pathlib import Path

from starlette.datastructures import UploadFile

from app.api.errors import AppError


async def stage_upload(file: UploadFile, root: Path, maximum: int) -> tuple[Path, str]:
    root.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".upload-", dir=root)
    temporary = Path(name)
    digest = hashlib.sha256()
    decoder = codecs.getincrementaldecoder("utf-8")("strict")
    size = 0
    try:
        with os.fdopen(descriptor, "wb") as output:
            while chunk := await file.read(64 * 1024):
                size += len(chunk)
                if size > maximum:
                    raise AppError("upload_too_large", "Upload exceeds size limit", 413)
                text = decoder.decode(chunk)
                if any(ord(c) < 32 and c not in "\t\n\r" for c in text) or "\x7f" in text:
                    raise AppError("unsupported_content", "Only UTF-8 text is supported", 415)
                digest.update(chunk)
                output.write(chunk)
            decoder.decode(b"", final=True)
            if not size:
                raise AppError("empty_file", "File must not be empty", 422)
            output.flush()
            os.fsync(output.fileno())
        return temporary, digest.hexdigest()
    except UnicodeDecodeError as exc:
        temporary.unlink(missing_ok=True)
        raise AppError("unsupported_content", "Only UTF-8 text is supported", 415) from exc
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def publish(temporary: Path, root: Path, digest: str) -> str:
    reference = f"objects/{digest[:2]}/{digest}"
    destination = root / reference
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Caller holds SQLite's write lock, serializing publication across uploads.
    if not destination.exists():
        os.replace(temporary, destination)
    return reference
