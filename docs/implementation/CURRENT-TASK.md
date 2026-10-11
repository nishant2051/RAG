# TASK-006 — Ollama Adapters and Local Model Validation

**Milestone:** M1 — Foundation
**Status:** Complete — lightweight checks and live Ollama checks passed.
**Depends on:** TASK-002 and TASK-005 (reported complete)
**Goal:** Add a small, configurable Ollama integration for connectivity, model discovery, one query/document embedding call, and one non-streaming generation call. Do **not** implement ingestion, indexing, retrieval, chat, or the RAG pipeline.

## Starting state (reported by Codex)

- FastAPI foundation, typed settings, errors, health endpoints, and `X-Request-ID` are implemented.
- SQLite/Alembic foundation and minimal Qdrant connection adapter exist.
- TASK-005 commit: `b08ed3f`; working tree reportedly clean.
- On the developer's Apple M4 Pro (24 GB), Ollama models are already installed: `nomic-embed-text:latest` and `qwen3:4b`. **Verify live availability; do not assume an installed tag means the service is running.**
- Docker was unavailable during TASK-005. Its Compose/live-Qdrant checks and TASK-001's combined smoke check remain **pending**. Neither is a prerequisite for TASK-006.

## Context and file boundaries

- Follow repository `AGENTS.md` and this task; consult only relevant `PROJECT-MAP.md` sections and source files for settings, dependencies, infrastructure adapters, error handling, and health diagnostics.
- Do **not** read the PRD, System Architecture, Database Design, API Specification, RAG Technical Design, full roadmap, or historical task documents.
- Inspect existing code before choosing file names. The names below are **suggestions**, not assertions about existing modules. Reuse existing settings and diagnostics rather than introducing duplicates.
- Keep changes limited to backend configuration, dependencies, Ollama infrastructure adapter(s), existing diagnostics integration, small developer commands/README, and handoff records.

## Required behavior

1. **Typed Ollama configuration**
   - Add validated settings using existing conventions: `OLLAMA_BASE_URL` (default `http://127.0.0.1:11434`), request timeout, `OLLAMA_EMBED_MODEL` (default `nomic-embed-text:latest`), and `OLLAMA_GENERATION_MODEL` (default `qwen3:4b`).
   - Update environment example. No cloud API, credentials, new database tables, or settings UI.
   - FastAPI must start even when Ollama is unavailable; avoid startup-time blocking model calls.

2. **Small Ollama adapter**
   - Prefer the project's existing HTTP-client conventions or use the official Ollama Python client only if it is the smallest coherent dependency choice. Use bounded async operations compatible with FastAPI; support proper client closure.
   - Implement bounded availability/model-discovery calls (e.g., list installed models) and explicit validation that the two configured model tags are present; present absent tags as a clear, typed dependency/model-unavailable result.
   - Provide one method to embed **documents** and one to embed a **query** via Ollama's embedding API. For Nomic, apply `search_document: ` / `search_query: ` respectively inside the adapter. Use `truncate=false` (or the equivalent API option). Do not add generic text rewriting.
   - Validate that the embedding response contains finite numeric vectors, nonempty output, and consistent dimensions; discover/record observed dimension dynamically rather than hardcoding 768. An oversized input must yield a typed error; **do not build chunk splitting here**.
   - Provide a minimal non-streaming text-generation method for `qwen3:4b` with optional, bounded generation settings (e.g., temperature and context size). No prompt templates, RAG orchestration, streaming, citations, chat persistence, or follow-up rewriting in this task.
   - Map connection errors, timeouts, missing models, and invalid model responses to the existing typed application-error conventions. Do not expose stack traces in API errors or logs.

3. **Diagnostics / developer usability**
   - Extend the existing dependency diagnostics surface to show Ollama availability and whether the configured embedding/generation models can be found. Keep `/health/live` independent of Ollama availability; follow existing readiness conventions without broad API redesign.
   - Add one concise README or Makefile example for checking `ollama list` and using the adapter through a short *manual* command. Never automatically pull large models.
   - Update `PROJECT-MAP.md` with only implemented adapters/contracts and the task-progress record with TASK-006 status.

## Boundaries / exclusions

- No automated tests, test files, test fixtures/mocks, benchmark suites, or test framework dependencies.
- No Qdrant schema/collection creation, SQLite models, document ingestion/parsing/chunking, vector upserts, retrieval, chat endpoints, SSE, frontend features, or UI changes.
- Do not expand into model installation, performance benchmarking, caching, background workers, or additional Ollama profiles.
- Do not modify unrelated changes; stop and report if a missing prerequisite requires an architectural redesign or broad repository exploration.

## Lightweight verification (no test files)

- Run Python compile/import and existing dependency/metadata checks.
- Check configuration defaults, invalid URL/timeout handling, and an API startup plus `/health/live` when Ollama is stopped/unavailable (if stopping the user's running service is undesirable, validate by temporarily pointing the adapter at an unused local port instead).
- If Ollama is running with both configured models, perform a **single manual** document embedding and query embedding, report observed dimensions, and perform one tiny non-streaming generation; confirm model-discovery diagnostics work. Don't print full embeddings or long model output.
- If Ollama isn't running or a model isn't installed, report which live checks remain pending; do not claim they passed or download the models automatically.
- Run scoped `git diff --check`; preserve pending TASK-001 combined smoke and TASK-005 Docker checks unless actually performed.

## Completion and handoff

- Configuration and typed adapter exist; local model discovery, embeddings, and non-streaming generation can be invoked independently of RAG features.
- Ollama outage does not prevent FastAPI startup; diagnostics report a degraded dependency state.
- Commit only focused changes after the checks available in the environment pass. Preserve unrelated work.
- Return **briefly**: commit hash, changed areas, checks passed/skipped, blockers, and pending manual checks. **Stop after TASK-006.**

## Verification handoff

- Python compile/import, package metadata, `uv sync --locked --offline`, `uv lock --check --offline`, and `uv pip check` passed. HTTPX was already installed transitively and is now declared directly; no package versions were upgraded.
- Configuration defaults and rejection of invalid remote/malformed URLs and out-of-range timeouts passed.
- API started on loopback port 18006 with Ollama pointed at unused port 1. Liveness returned 200/alive, diagnostics returned 200 with Ollama unavailable and both models not checked, and readiness retained dependencies not_checked. Temporary server stopped afterward.
- Live `ollama list` and adapter validation found nomic-embed-text:latest and qwen3:4b. One document and one query embedding each returned finite 768-dimensional vectors; observed dimension recorded dynamically.
- Initial tiny generation returned empty text and correctly raised invalid_model_response. After disabling thinking for this bounded text adapter, the generation retry returned nonempty text. Live diagnostics reported Ollama healthy and both models available. Output quality/instruction-following was not evaluated.
- Scoped git diff --check passed. No automated tests were added or run.
- TASK-001 combined backend/frontend smoke and TASK-005 Docker Compose/live-Qdrant checks remain pending; neither was performed in TASK-006. No blockers.
