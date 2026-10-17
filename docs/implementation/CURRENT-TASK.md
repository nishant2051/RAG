TASK-010 — Nomic Embeddings and Qdrant Indexing
Milestone: M2 — First Working RAG
Scope: Backend internal indexing service only
Status: Implemented — lightweight checks passed; live Qdrant acceptance pending
Goal
Implement the smallest internal pipeline that accepts the existing immutable chunks from TASK-009, obtains document embeddings from the existing Ollama adapter using nomic-embed-text:latest, and upserts points into Qdrant through the existing Qdrant integration. Leave persistent asynchronous ingestion jobs and advanced index-generation activation for M3.
Do not create a new architecture or broad abstraction layer. Reuse actual existing APIs; the names below describe desired behavior, not assumed signatures.
Read only what is necessary
1. AGENTS.md and this docs/implementation/CURRENT-TASK.md.
2. The ingestion, Ollama, Qdrant, and upload/storage sections of docs/implementation/PROJECT-MAP.md.
3. Targeted source files only:
   - backend/app/ingestion/chunking.py and existing parsed-document models as necessary.
   - Existing Ollama embedding adapter and its settings/errors.
   - Existing Qdrant adapter and its settings/errors.
   - Upload/content identity model or storage interfaces only if needed to establish stable content IDs.
   - backend/pyproject.toml only to check installed library versions.
Do not read the five architectural documents, full implementation plan, previous task files, or unrelated source.
Preflight: preserve existing work
- Check git status --short before editing. TASK-007, TASK-008, and possibly TASK-009 are not known to be committed.
- Do not stage, commit, reset, clean, discard, or overwrite unrelated work.
- Confirm that the existing chunk API chunk_document(document, config) returns ordered immutable chunks with source offsets and SHA-256 hashes, default target 500, overlap 75, and maximum 1000 estimated tokens.
- Inspect existing adapter signatures and implement against them rather than guessing names.
- Qdrant prerequisite: Attempt the previously pending Docker Compose validation and live Qdrant connection check if Docker/Qdrant is available. Record what was actually verified. An unavailable Docker/Qdrant environment is not permission to fake an end-to-end pass. Implement offline-verifiable code, report live indexing as pending, and stop rather than broadening scope to install/configure Docker.
Required implementation
1. Internal indexing entry point
Create a small backend indexing module under backend/app/ingestion/ (or the closest established module), exposing a typed asynchronous operation that indexes an ordered sequence of already-created chunks for a stable content identity and an explicit embedding profile. If existing code supports retrieving/parsing/chunking a stored document cheaply, a thin composition wrapper is acceptable; avoid coupling vector indexing to HTTP endpoints or job orchestration.
- Validate nonempty chunk input; reject missing content identity and unsupported profile/dimensions with typed, actionable errors consistent with the backend.
- Preserve the chunk's original text, hash, order/index, section context, and source location metadata in Qdrant payloads where those fields exist. Represent unknown/nullable line ranges as null or omit them; never invent values.
- Return a concise internal result (e.g. count, collection/profile, point identities) that a future ingestion orchestration task can use. Do not imply durable activation or job completion.
2. Ollama embeddings
- Reuse the existing async Ollama adapter, not a second HTTP client.
- Default embedding model: nomic-embed-text:latest. Use the existing model/settings mechanism where supported.
- Batch deterministically in document order; default batch size 16, configurable through the smallest existing configuration mechanism.
- Use the document embedding mode/input convention already established by the adapter. Do not silently truncate chunks.
- Check the number of vectors equals the number of submitted chunks. Validate every vector is numeric, finite, and 768-dimensional for the active Nomic profile. Surface model/network/mismatch errors without partially reporting success.
- Do not add another tokenizer or claim exact token counts; the TASK-009 counts are estimates.
3. Qdrant collection and upsert
- Reuse the existing Qdrant client/settings and established distance metric if present. If none exists, use cosine similarity for the 768-dimensional collection.
- Ensure/verify the target collection exists with the expected vector dimension and metric; reject incompatible existing configuration explicitly, never silently recreate or delete a collection.
- Build deterministic, Qdrant-valid point IDs (UUID or uint64) from stable content identity + embedding profile + chunk identity/index. Identical reindex inputs should map to the same point IDs; distinct chunks must not overwrite each other accidentally. Do not use random IDs.
- Upsert in bounded batches and await/verify acknowledgments using the installed Qdrant client API. Use payload keys that support later semantic retrieval filtering by content/profile (and generation ID only if already available); do not fabricate active-generation records.
- Keep the implementation idempotent for the same content/profile/chunks. Reuse of embeddings across logical documents should remain possible because identities are content-based, not upload-specific.
- Avoid deleting an earlier valid index or marking a new one active if embedding/upsert fails. Report partial failures as errors; full atomic activation belongs to a later task.
4. Configuration and errors
- Prefer existing typed settings and error types; add only narrowly necessary configuration.
- Do not install dependencies unless a required package is genuinely absent; explain any dependency change.
- Keep identifiers/profile fields explicit and stable for TASK-011 semantic retrieval.
Explicitly out of scope
- No new or modified HTTP API route and no upload-triggered indexing yet.
- No worker process, polling, persistent ingestion job/checkpoint/retry scheduling, or cancellation framework.
- No SQLite migration, durable index-generation activation/switching, replacement semantics, cleanup, or rollback orchestration unless an existing required interface makes a minimal addition unavoidable; if so, stop and report the dependency before implementing it.
- No semantic search, reranking, generation, citations, chat, or UI.
- No PDF/DOCX support.
- No tests of any kind: no unit/integration/E2E tests or test frameworks.
- No general refactors, optional libraries, or unrelated documentation rewrites.
- No git add/commit operations without permission.
Lightweight acceptance checks (no automated test files)
1. Python compilation and import check for changed modules.
2. Run a short disposable/manual embedding invocation against the locally available Ollama model when available; verify count and 768 dimensions. If the model is unavailable, clearly mark that check pending.
3. If live Qdrant is available: manually index a small TXT/Markdown chunk sample, inspect collection dimension and stored payload/count, reindex exactly the same input to demonstrate stable IDs/no duplicate points, and verify a mismatched dimension is rejected without destructive changes. Use a disposable collection or otherwise avoid modifying valuable existing data.
4. If Qdrant is unavailable: validate deterministic point/payload construction without asserting a live upsert passed. Explicitly record Docker Compose/Qdrant checks as pending.
5. Confirm failures (empty input, dimension mismatch, unavailable model/Qdrant) give bounded, actionable errors; do not add automated test code to do so.
6. Review git diff --check, git status --short, and modified-file scope; keep pre-existing changes.
Handoff updates
Update only the relevant sections of docs/implementation/PROJECT-MAP.md and this CURRENT-TASK.md with the actual public internal entry point, files changed, verification evidence, and any known limits. Do not claim TASK-001 combined frontend/backend startup or TASK-005 live Docker/Qdrant checks passed unless you actually ran them.
Completion report to return
- Internal indexing API and precise files changed.
- How point IDs, profile, collection name, and payload metadata are represented.
- Verification performed: compile/import, Ollama live, Docker Compose, Qdrant live/upsert/reindex; distinguish passed / failed / pending.
- Limitations or blockers, including any temporary partial-upsert behavior.
- Final git status --short; state explicitly whether anything was staged or committed.
Stop after TASK-010. Do not start TASK-011, clean the working tree, or commit without explicit authorization.

TASK-010 completion handoff
- Added backend/app/ingestion/indexing.py: async index_chunks(chunks, *, content_id, profile, ollama, qdrant, config=IndexingConfig()) with immutable EmbeddingProfile, IndexingConfig and IndexingResult; typed IndexingError. No routes, upload behavior, jobs, schema changes or dependencies changed.
- Explicit supported profile: nomic-embed-text-latest-document-v1 / nomic-embed-text:latest / 768 dimensions / search_document prefix through the existing adapter (truncate=false). Config defaults: collection rag_nomic_documents_v1, batch size 16 (1–256).
- UUIDv5 IDs derive from a versioned tuple of stable content identity, profile ID, original chunk index and text hash. Payloads retain content/profile/model, original text/hash/index, section paths, nullable lines, exact source spans, source reference, warnings and estimated tokens. No generation/activation records.
- Collection existence, unnamed vector size and cosine metric are checked without recreation/deletion. All embeddings validate before point writes; bounded upserts wait for COMPLETED. A later upsert failure can leave partial or uncertain writes; errors report acknowledged counts and safe identical-input retry guidance. Embeddings are held in memory for the document. Changed chunk sets do not delete old points; latest model tags are not digest-pinned.
- Passed compile/import, manual deterministic/distinct point construction and payload inspection, empty input/missing identity, unsupported profile/dimensions, invalid vector count/size/nonfinite values, and typed unavailable-Qdrant handling. Live Ollama sample returned two finite 768-dimensional vectors; deliberately missing model returned model_unavailable. No automated tests or mocks.
- Docker Compose config validation passed. Docker daemon is unavailable (confirmed outside sandbox); local Qdrant probe failed. Live collection creation, upsert/payload/count inspection, repeat-index duplicate check, and incompatible live collection rejection remain pending. No live indexing success claimed; TASK-001 combined startup remains pending.
- Preserved the pre-existing CURRENT-TASK.md modification. Nothing staged or committed.
