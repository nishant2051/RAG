TASK-013 — FastAPI Ingestion and RAG Query Integration
Milestone: M2 — First Working RAG
Status: Implemented; live grounded answer success remains unverified
Scope: Minimal backend HTTP integration of already-implemented upload, parsing, chunking, indexing, retrieval, and grounded-generation primitives. No persistent jobs or UI.
Goal
Expose a small, working FastAPI path from an already uploaded TXT/Markdown document to a grounded question/answer response. Reuse TASK-007–012 code rather than recreating it. Keep the M2 orchestration synchronous-within-request (async I/O where existing operations are async), without claiming to provide background ingestion. The existing upload endpoint must remain compatible.
Known current state: TASK-012 added backend/app/rag/generation.py and async generate_grounded_answer(question, passages, *, ollama, config=GroundingConfig()) -> GroundedAnswer. Source IDs are deterministic; unknown citations cause citation-free abstention. Live Qwen3 produced repetitive analysis for a relevant question and a successful grounded answer has not yet been observed. TASK-010 live Qdrant checks were subsequently reported passed; TASK-001 combined frontend/backend smoke remains pending. TASK-011 was reported implemented without its exact interface or Git status. Inspect actual code; do not invent signatures.
Read only the required files
1. AGENTS.md; docs/implementation/CURRENT-TASK.md; relevant sections of docs/implementation/PROJECT-MAP.md.
2. Existing FastAPI app/router/error/request-ID and dependency setup; TASK-007 upload endpoint and SQLite document/content object access.
3. Existing TXT/Markdown parser dispatch, chunker, TASK-010 index_chunks(...), TASK-011 retrieval API/models, TASK-012 generate_grounded_answer(...), Ollama/Qdrant adapters and typed errors.
4. Minimal settings/schema modules necessary to wire the calls and confirm model/collection defaults.
Do not read all reference architecture documents or the full implementation plan. Inspect only what is needed for real contracts.
Preflight / worktree safety
- Run git status --short before modifying anything. TASK-007 onward may be uncommitted; preserve unrelated changes.
- Do not stage, commit, reset, clean, discard, or auto-format unrelated files.
- No automated tests or test frameworks; no new dependencies unless a real integration blocker demands one.
- Keep APIs under /api/v1, with existing error shape, request-ID handling, localhost constraints, and typed Pydantic schemas.
Required implementation
1. Thin application-level orchestration
Add a small module (suggested backend/app/rag/orchestration.py, adjust to existing layout) that composes existing interfaces without rewriting them:
- Given an existing, stored document ID, resolve its persisted content via the existing SQLite/storage APIs, verify it is an eligible TXT/Markdown document, and safely obtain the source bytes via the canonical content-addressed path. Do not accept arbitrary filesystem paths from requests.
- Parse, chunk, and invoke TASK-010 indexing using an explicit content ID and embedding profile according to the real index_chunks(...) signature. Reuse its deterministic IDs and retry behavior. If the document is empty/unindexable or dependencies fail, return a clear typed failure.
- Given a nonblank question and explicit scope of indexed document/content IDs, invoke TASK-011 retrieval and then TASK-012 grounded generation. Do not let the model answer from unrelated indexed content. Use the actual metadata/Qdrant filtering contract; do not invent an SQL-backed “active generation” filter that has not been implemented.
- Keep service logic focused, with typed results and clear handling of dependency errors. No global state beyond established app dependencies.
2. Minimal HTTP endpoints
Use names/routes that fit the current router patterns; suggested contracts:
- POST /api/v1/documents/{document_id}/index: triggers the inline TXT/Markdown parse → chunk → embedding → Qdrant upsert flow for one already uploaded document, returning document ID, indexed chunk count, collection/profile, and a truthful status. This is not an async background job: do not return 202 with a fake job ID. Prefer a normal 200 successful response. Idempotent identical-input repeats must reuse deterministic point IDs.
- POST /api/v1/rag/answer: JSON request with question and a required nonempty explicit list of document IDs. Resolve these documents to valid indexed content IDs using existing data/invariants. Return answer, outcome/abstention, and only validated citations with the available source/document metadata. The response must not claim factual entailment. On no eligible indexed documents, return a non-hallucinated no-evidence/abstention result (or an existing typed client error if that is consistent with established API contracts), without unscoped Qdrant search.
The upload API must retain its existing stored_pending_indexing behavior until a successful indexing request. If a durable status transition is supported by existing models, use it; otherwise avoid falsely updating persisted indexing/job status and document this M2 limitation. Do not fabricate a job_id, session ID, completion timestamp, or active generation.
3. Data mapping and failure semantics
- Preserve document IDs, source locations, passage hashes/point IDs, and deterministic evidence IDs end-to-end; only return citations that the generation result validated.
- Map generated evidence references to the requested source document(s) using trustworthy stored metadata. If content-addressed deduplication means several logical documents share a content ID, choose deterministic mapping within the caller's explicitly requested scope. Never expose unrelated documents through citation labels.
- Enforce requested scope at the vector-query filter layer via TASK-011's supported filter, not by fetching globally and filtering results afterwards.
- Reject malformed IDs, unsupported files, invalid/blank questions, and oversized inputs with existing standard error responses; avoid leaking filesystem paths or internal stack traces.
- Distinguish dependency errors and failed index/retrieval/generation operations from insufficient-evidence abstention. Preserve error/request-ID conventions.
- A partially completed TASK-010 Qdrant upsert may leave vectors behind. Do not treat partial writes as an activated index; if the current code cannot safely track activation, explicitly document that scoped retrieval relies on available indexed-content metadata and report the gap. No advanced transactional index lifecycle in M2.
- Do not mask TASK-012's observed generation problem or rewrite generation logic here. If a minimal adapter invocation fix is necessary to make endpoints callable, isolate it and report it; otherwise leave generation improvement for a separate tightly scoped follow-up.
4. Dependencies, OpenAPI and compatibility
- Wire existing dependency providers/settings for DB, Qdrant, and Ollama. Follow existing FastAPI dependency lifetime and exception handling conventions.
- Add small Pydantic request/response schemas with concrete fields that match actual service results.
- Confirm endpoints appear in FastAPI OpenAPI.
- Avoid introducing new worker queues, persistence tables, sessions, SSE, background tasks, collection admin, or generated TypeScript client changes. Avoid breaking existing upload and health endpoints.
Out of scope
- No PDF/DOCX, approved folder imports, persistent ingestion jobs, polling/job cancellation, scheduling, retries beyond current primitives, staged index activation or cleanup (M3).
- No persistent chat, query rewriting, historical citation resolution, streaming/SSE, regeneration, or session scopes (M4).
- No frontend/UI changes (TASK-014), advanced diagnostics/evaluation, or new auth.
- No automated unit/integration/E2E tests or test infrastructure.
Lightweight manual acceptance checks
1. python -m compileall or equivalent focused compile/import; FastAPI app import; OpenAPI contains the new endpoints; git diff --check.
2. Use disposable/manual HTTP commands where services are available: upload a small TXT or Markdown file (or reuse an existing safely stored document), index by ID, reindex the same document, and verify deterministic IDs/no duplicate Qdrant point growth. Do not alter unrelated user data or delete existing vectors.
3. Query with an explicit document-ID scope; inspect that TASK-011 filtering is scoped, source metadata is preserved, and the response uses only validated evidence IDs. Also check no-evidence abstention and unknown/unsupported document ID errors.
4. Verify health and existing upload endpoint behavior remain intact. If possible run the previously pending combined frontend/backend smoke check and report it distinctly; don't mark it passed without actually running it.
5. Generation is not fully verified: if live Qwen3 again produces repetitive analysis or abstention for relevant evidence, report answer_success: unverified instead of marking the end-to-end RAG path successful. Do not relax citation validation to force success.
6. If Docker/Qdrant/Ollama cannot be reached, still run compilation/schema/manual in-memory checks and explicitly label blocked end-to-end checks. Carry forward earlier verification status accurately; TASK-010 Qdrant checks were reported passed, not pending.
7. Do not add tests to the repository. Brief throwaway scripts/commands for manual checks are acceptable.
Documentation & final report
Update only docs/implementation/CURRENT-TASK.md and relevant docs/implementation/PROJECT-MAP.md sections with actual paths, HTTP contracts, functions and residual limitations. Preserve historical records.
Report changed files, exact endpoint contracts, verified end-to-end steps and observed results, errors/abstentions, outstanding Qwen3 success limitation, pending combined startup check, and final git status --short. State whether anything is staged/committed.
Stop after TASK-013. Do not implement TASK-014 or other milestones.

TASK-013 implementation / verification (2026-10-18)
- Added backend/app/rag/orchestration.py: resolve_sources, source_chunks, index_document, answer_question. Resolves UUIDs through SQLite, validates canonical SHA-256 object references, confines resolved paths to storage root, bounds reads and checks raw checksum. Reuses parser/chunker/index_chunks with explicit EmbeddingProfile and raw content SHA-256. Releases SQLite read transactions before dependency calls.
- Added backend/app/rag/router.py; registered in backend/app/main.py. POST /api/v1/documents/{document_id}/index (no body) returns 200 {document_id, status: indexed, indexed_chunk_count, content_id, collection_name, profile_id}. Only a fully acknowledged index result permits committing document.status=indexed. No job or background execution.
- POST /api/v1/rag/answer accepts {question, document_ids}; question must be nonblank and <=4096 UTF-8 bytes; 1–100 UUIDs required. Returns 200 {answer, outcome: answered|insufficient_evidence, citations, prompt_version}. Citations contain validated evidence_id, requested document_id/filename, text/raw score, point_id, content_id/hash/chunk index, embedding profile, source_reference (requested document UUID), heading/line/span metadata and warnings. Provenance validation does not establish entailment.
- Only requested documents with persisted indexed status enter RetrievalScope. Existing TASK-011 content/profile Qdrant filters enforce scope at query time; empty eligible scope skips external calls and returns citation-free abstention. Shared content maps to the lexicographically first indexed requested document UUID. Vector labels use content identity; generation labels are replaced with requested UUIDs to avoid unrelated upload labels.
- Existing upload still returns 202, null job, stored_pending_indexing for new uploads. UploadResult now also accepts indexed for replay of an idempotent upload after successful indexing. Malformed/blank/oversized input -> standard 422; unknown UUID -> 404; unsupported format -> 415; storage identity/unavailable ->409; dependency/index/retrieval/generation typed errors retain existing error/request-ID envelopes.
- Passed focused compileall, app import, OpenAPI route presence, git diff --check. No automated tests added or run.
- Disposable manual HTTP checks used ASGI HTTP transport with temporary SQLite/storage and real local Qdrant/Ollama: health 200; TXT upload 202; unindexed scope 200 insufficient_evidence/no citations; malformed UUID 422; missing UUID 404; PDF upload 415; blank question/empty scope list 422; index 200 with one chunk; identical reindex 200 and unchanged point ID 45a460d3-9f25-5b35-85e5-759d634b4b81, one matching point before/after. Qdrant manual content a9cecfab8119e2f806cec77c721dbce2565d92761a4cf54a83dfd21825353268 remains in default collection; no existing vectors were deleted. Temporary SQLite/storage removed by disposable script.
- Live Qwen3 relevant question (observatory named Cedar) and unrelated question both returned 200 insufficient_evidence with no citations. answer_success: unverified. Raw model analysis was not captured in this run; prior TASK-012 repetitive-analysis failure remains unresolved. No adapter, generation prompt, budget or citation validation changes. Successful citation-bearing HTTP output and multi-document deduplication mapping remain unverified live.
- Initial sandboxed indexing returned typed 503 qdrant_indexing_failed; rerun with local network permission passed. Existing TASK-010/011 live Qdrant verification remains passed.
- Combined scripts/start.sh smoke attempted: ports 8000 and 5174 already occupied, both new processes failed to bind. Existing endpoints returned HTTP 200, but that does not verify the new combined startup; combined startup remains pending. Existing processes left alone.
- M2 limitations: indexed is a coarse document status, with no profile/collection/version receipt or transactional activation. Failed first-time/partial upserts leave the upload pending and excluded; vectors can remain. A failed reindex of an already indexed document retains its previous status; changed parsing/profile, collection deletion/loss and partial reindex cannot be safely modeled by current metadata. Deduplicated TXT/Markdown interpretation can also leave old points if parsing produces different chunks. No cleanup or lifecycle redesign added. Local model tags remain mutable. Inline parsing/chunking uses existing synchronous primitives and can occupy the request event loop.
- Original uncommitted task contract preserved and extended. Nothing staged or committed. Stop after TASK-013.
