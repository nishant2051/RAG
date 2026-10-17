# TASK-007 — Single-Document Upload and Content-Addressed Storage

**Milestone:** M2 — First Working RAG
**Status:** Complete — prescribed lightweight verification passed.
**Dependencies:** TASK-001–006 completed; Docker/Qdrant live check and combined frontend/backend smoke check remain pending and are **not** prerequisites for this task.

## Objective
Implement one-file upload through FastAPI with safe validation, SHA-256 content-addressed local storage, and an HTTP response identifying the uploaded document. This task establishes the upload/storage boundary only. Parsing, chunking, embeddings, Qdrant indexing, durable ingestion workers, and frontend upload UI belong to later tasks.

## Context and discovery budget
1. Read root `AGENTS.md`, this `docs/implementation/CURRENT-TASK.md`, and only the **documents/storage/API/configuration** sections of `docs/implementation/PROJECT-MAP.md`.
2. Inspect only existing FastAPI router registration, typed settings, error handling, persistence foundation, and relevant dependency declarations. Discover actual paths first: names below are **suggested locations**, not claims that these files exist.
3. Do **not** read `docs/reference/`, previous task files, or the full roadmap. If implementation requires broad repository exploration or architectural changes, stop and report the blocker.

## Files and change boundaries
**Suggested new files (adapt to existing module conventions):**
- `backend/app/documents/router.py` — POST upload route.
- `backend/app/documents/service.py` — upload coordination, hashes, and metadata.
- `backend/app/infrastructure/storage/local.py` — content-addressed filesystem operations.
- Minimal document ORM/schema and Alembic revision **only if necessary** to persist upload identity and storage references; use existing SQLAlchemy/Alembic conventions.

**Inspect/modify only as necessary:** application router registration, existing configuration/error schemas, backend dependencies/environment example, and concise project-map/task progress entries. Do not modify frontend or Ollama/Qdrant adapters.

## Required behavior
1. Implement `POST /api/v1/documents` accepting **exactly one** multipart file; successful accepted requests return **202 Accepted** and resource-shaped JSON with `document_id`, `job_id` (nullable for this temporary pre-ingestion slice), and a truthful `status` indicating **stored / pending indexing**, not indexed or ready. If a non-null `job_id` is returned, it must refer to a persisted job; never invent an ID or promise an indexing job that does not exist.
2. Enforce configurable upload size maximum **100 MB**, streaming/limited reads to prevent accepting oversized payloads. Reject unsupported formats with HTTP **415**, oversize with **413**, empty files with a stable validation error, and use existing standard error envelope/request ID behavior. Initial supported formats are `.txt` and `.md`; PDF/DOCX will follow in M3. Do not trust filename or client-provided MIME type alone; apply conservative lightweight content validation appropriate to TXT/Markdown.
3. Compute SHA-256 over raw file bytes and write once into a server-controlled, content-addressed directory under a configured storage root. Use temporary files and an atomic final rename (same filesystem); avoid partial final files, path traversal, and collisions. Never use a supplied filename as a storage path.
4. Store a logical upload/document record with a UUID, original display filename, content SHA-256, stored object reference, creation timestamp, and explicit **not-indexed** state. Identical bytes uploaded under different names must create distinct logical document identities while reusing the underlying content object. If the full final schema is not yet available, implement the smallest forward-compatible persistence slice using SQLAlchemy/Alembic, without inventing embeddings, generations or indexing state.
5. Accept an optional `Idempotency-Key` per agreed API. Within a 24-hour retention window, a repeated equivalent upload with the same key must resolve to the same logical operation; the same key with different content must return **409**. Enforce uniqueness transactionally for concurrent requests. If implementing this requires schema refinements, keep them focused here and document any necessary follow-up; don't replace idempotency with content-hash deduplication.
6. If file persistence succeeds but database persistence fails, perform best-effort cleanup only for unreferenced temporary content, and avoid deleting an object used by another document. Record failures with existing structured logging and sanitized API errors.
7. Do not start ingestion jobs or report searchability in this task. A later task will connect stored uploads to parsing and indexing. Keep the route and service ready to be extended without implementing that extension now.

## Explicit exclusions
- No document parser/chunker, Ollama or Qdrant calls, embeddings, vector collections, retrieval or generation.
- No background worker or staging index lifecycle in this task.
- No frontend work, bulk/folder import, collection management, soft delete, replacement, or reindex.
- **No automated tests**, fixtures, test frameworks, broad refactoring, or new dependencies without a clear need.

## Lightweight verification (no test files)
- Python compile/import check and Alembic migration applied to a disposable SQLite database, if schema added.
- Start backend on loopback and manually upload one small TXT and one Markdown file. Confirm 202, real UUIDs, saved content hashing correctly, and status accurately indicates not indexed.
- Repeat identical bytes under a different filename: confirm two logical IDs and one underlying content object. Repeat with identical idempotency key: confirm original logical result; reuse key with changed content: confirm 409.
- Manually confirm empty/unsupported/oversized file failure behavior with suitably lightweight commands (avoid generating or logging giant files).
- Confirm `/health/live` still works and `git diff --check` passes. Record skipped checks honestly.

## Handoff and Git
- Preserve unrelated changes. Keep task progress and `PROJECT-MAP.md` accurate; do not mark pending TASK-001 combined smoke or TASK-005 Docker/Qdrant checks as complete unless actually performed.
- Create one focused Git commit **only if prescribed checks pass**; otherwise stop with blockers and no commit.
- Completion response: commit hash, files changed (brief), checks run/pending, blockers. **Stop after TASK-007.**

## TASK-007 completion
- Implemented one-file TXT/Markdown upload, conservative UTF-8 validation, bounded reads, SHA-256 atomic local storage, logical document persistence and transactional 24-hour idempotency. Status is `stored_pending_indexing`; `job_id` is null.
- Idempotency equivalence includes raw content and sanitized display filename; MIME is not trusted. Published objects are retained on DB failure to avoid deleting shared content; temporary files receive best-effort cleanup. Orphan-object reclamation is a later follow-up.
- Passed: compile/import, Alembic upgrade on disposable SQLite, live loopback TXT/Markdown uploads, UUID/hash/status checks, separate identities sharing one object, idempotent replay and conflict, concurrent same-key replay, empty/unsupported/binary/multiple-file rejection, oversize rejection using a configured 1 KiB limit (including request-stream limit), `/health/live`, and diff whitespace check. No automated tests created or run.
- TASK-001 combined frontend/backend smoke and TASK-005 Docker/Qdrant checks remain pending. No blockers.
