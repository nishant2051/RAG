# Implementation Plan — Local RAG Application

**Version:** 1.0
**Date:** 2026-10-11
**Status:** TASK-001, TASK-002, TASK-003 and TASK-004 implemented; TASK-001 combined scaffold smoke check remains pending.

## Goal and scope

Build a single-user local RAG application on Apple M4 Pro (24 GB) with React/TypeScript/Vite, Python/FastAPI, SQLite/SQLAlchemy/Alembic, Qdrant, and Ollama (`nomic-embed-text:latest`, `qwen3:4b`). Deliver a vertical slice early, then add persistent jobs, document lifecycle, conversation-aware retrieval, diagnostics and recovery.

**Execution policy:** Codex reads only root `AGENTS.md`, `docs/implementation/CURRENT-TASK.md`, necessary portions of `docs/implementation/PROJECT-MAP.md`, and task-listed source files. `docs/reference/` is background reference for the human/task author, **not** routine Codex context. Begin each task in a fresh Codex session. Do not create automated tests, fixtures, mocks or test frameworks. Perform small syntax/type/build/migration checks and manual smoke checks instead. Do not let Codex silently broaden task scope.

## Task lifecycle

`Planned → Ready → In progress → Completed` or `Blocked`. Mark a task Completed only after required checks have run and the requested Git commit is created. Where a manual smoke check cannot be performed, record `Manual verification pending` rather than claiming completion. One CURRENT-TASK file only; after completion archive it under `docs/implementation/completed/TASK-NNN.md` and prepare the next task outside Codex. On a major blocker, stop and report instead of consulting all references or rewriting architecture.

## Milestone acceptance gates

- **M1:** Development servers and local dependencies start; basic health diagnostics work.
- **M2:** TXT/Markdown can be uploaded, indexed, queried and cited through minimal UI.
- **M3:** Durable background processing, PDF/DOCX, collections, shared indexes, replace/reindex/restore, cleanup work.
- **M4:** Persistent chat, scope, follow-ups, SSE/JSON, citations and safe regeneration work.
- **M5:** Retrieval is inspectable; curated dataset can be reviewed with a manual evaluation tool. This is *not* an automated test suite.
- **M6:** Local startup, recovery, safe import boundary and consistent manual backup/restore are documented and smoke-checked.

## Ordered task inventory

Each task below is a brief roadmap entry, **not a Codex instruction file**. Prepare a self-contained `CURRENT-TASK.md` for one task at a time with actual file paths and interface contracts. Dependencies refer to completed tasks, not just planned ones.

### M1 — Foundation

| Task | Deliverable | Depends on | Status |
|---|---|---|---|
| TASK-001 — Repository scaffold and configuration | Python backend and React/Vite frontend structure, dev scripts, environment examples; no app features. | None | Completed |
| TASK-002 — FastAPI entrypoint and health | Minimal FastAPI app, typed configuration, live/ready response shells and standard errors. | 001 | Completed |
| TASK-003 — React application shell | Vite UI shell, API base URL configuration and minimal navigation. | 001 | Completed |
| TASK-004 — SQLite engine and migrations | SQLAlchemy sessions, SQLite WAL/foreign keys, initial Alembic setup. | 002 | Completed |
| TASK-005 — Local Qdrant service | Docker Compose Qdrant, connection adapter, dependency diagnostic. | 001,002 | Complete — available checks passed; Docker Compose/connectivity checks pending (Docker unavailable). |
| TASK-006 — Ollama provider adapters | Embed/generate interfaces, Nomic and Qwen local adapters, model/dimension checks. | 002 | Planned |

### M2 — First working RAG

| Task | Deliverable | Depends on | Status |
|---|---|---|---|
| TASK-007 — Upload and content-addressed storage | Single TXT/MD multipart upload, 100 MB limit, basic document metadata and local storage. | 002,004 | Planned |
| TASK-008 — TXT and Markdown extraction | Format adapters return structured blocks and source locations. | 007 | Planned |
| TASK-009 — Structure-aware chunking | Deterministic ~500 token chunks, ~75 overlap, section-aware fallbacks. | 008 | Planned |
| TASK-010 — Embedding and basic Qdrant upsert | Nomic document embeddings, no truncation, deterministic point IDs and write validation. | 005,006,009 | Planned |
| TASK-011 — Dense scoped retrieval core | Query embedding, eligible index IDs, 2x Top-K candidates, final Top-K selection. | 010 | Planned |
| TASK-012 — Grounded generation and citations | Qwen3 evidence prompt, abstention, evidence ID validation. | 006,011 | Planned |
| TASK-013 — Minimal RAG HTTP integration | Wire upload/index/question route with temporary simple ingestion path; mark for M3 replacement. | 007,010,011,012 | Planned |
| TASK-014 — Minimal usable UI | Upload, ingest status, question input, answer and source references. | 003,013 | Planned |

### M3 — Document management

| Task | Deliverable | Depends on | Status |
|---|---|---|---|
| TASK-015 — Complete core document schema | Content objects, documents, collections, active generations, constraints and migrations. | 004,014 | Planned |
| TASK-016 — Durable jobs and worker loop | SQLite queued jobs, worker process, lease/recovery, bounded retries; remove temp inline ingestion. | 015 | Planned |
| TASK-017 — Checkpointed ingestion and staged activation | Batch checkpoints, staging generation, validation, atomic document reference activation. | 016,010 | Planned |
| TASK-018 — PDF and DOCX parsing | PyMuPDF/python-docx adapters, warnings and structured table/page metadata. | 008,017 | Planned |
| TASK-019 — Bulk folder import and job visibility | Approved-root relative imports, job listing/polling/cancellation and parent jobs. | 016,018 | Planned |
| TASK-020 — Collections and scoped retrieval | Collection CRUD, many-to-many membership and SQLite-derived Qdrant filters. | 015,011 | Planned |
| TASK-021 — Deduplication, replace and reindex | Reuse compatible content/index, multipart replacement, manual reindex and idempotency. | 017,020 | Planned |
| TASK-022 — Soft delete, restore and reconciliation | 30-day retention, reference-aware cleanup, orphan repair, restore before purge. | 021 | Planned |

### M4 — Conversational RAG

| Task | Deliverable | Depends on | Status |
|---|---|---|---|
| TASK-023 — Persistent chat sessions and messages | Session CRUD, ordering, roles and message status persistence. | 015 | Planned |
| TASK-024 — Chat RAG execution records and scope | Current session scope, effective per-run scope and execution metadata. | 023,020 | Planned |
| TASK-025 — Follow-up detection and query rewrite | Rules for dependent questions, conditional Qwen rewrite, small history window. | 024,012 | Planned |
| TASK-026 — SSE generation stream | POST streaming, typed events, final persistence before completed event. | 024,012 | Planned |
| TASK-027 — Citation verification and source UI | Structured citations, latest-document validation and changed/deleted warnings. | 026,021 | Planned |
| TASK-028 — Regeneration and interruption safety | One generation per session, cancellation, safe transactional replacement. | 026,027 | Planned |
| TASK-029 — Chat UX and JSON mode | Sessions/history/scope UI and non-streaming JSON response support. | 014,025,028 | Planned |

### M5 — Diagnostics and evaluation

| Task | Deliverable | Depends on | Status |
|---|---|---|---|
| TASK-030 — Retrieval diagnostics instrumentation | Durations, candidates, omissions, evidence IDs and model/profile metadata. | 029 | Planned |
| TASK-031 — Developer retrieval inspection panel | Display scores, passages, filters, context budget and stage times. | 030 | Planned |
| TASK-032 — Small relevance benchmark dataset | Hand-curated questions, expected source passages and unanswerable questions; no automated test suite. | 030 | Planned |
| TASK-033 — Manual evaluation runner and report | On-demand evaluation tool/report for retrieval and faithfulness review, not automated tests. | 031,032 | Planned |

### M6 — Reliability and packaging

| Task | Deliverable | Depends on | Status |
|---|---|---|---|
| TASK-034 — Typed errors and dependency degraded mode | Comprehensive error mapping, dependency status and restart handling. | 029 | Planned |
| TASK-035 — Index/job reconciliation hardening | Orphan cleanup, interrupted worker recovery and integrity checks. | 022,034 | Planned |
| TASK-036 — Manual export and restore workflow | Consistent SQLite backup, document manifest and Qdrant reindex instructions. | 035 | Planned |
| TASK-037 — Local security and configuration polish | Localhost host/CORS checks, approved import roots, upload bounds and settings. | 034,036 | Planned |
| TASK-038 — Single-command startup and milestone smoke pass | End-to-end local startup, operator README and manual smoke checklist. | 037,033 | Planned |

## Codex execution guardrails

1. A fresh session receives only: `Implement docs/implementation/CURRENT-TASK.md. Follow AGENTS.md. Stop after verification and handoff.`
2. Keep task scope to an explicit file allowlist, with `read-if-needed` and `modify` paths. The author must verify paths when code exists; label anticipated paths as **proposed**.
3. Stop before unplanned schema changes, new dependencies, broad exploration or interface redesign; report the blocker and suggested smallest follow-up task.
4. Source and runtime behavior take precedence over stale project-map entries; update the map with *implemented* interfaces only.
5. After successful checks, update this plan's task status and create one focused Git commit if Git is available and the working tree is safe; never include unrelated changes. If checks fail, do not commit.
6. Return only files changed, checks performed and blockers/manual checks pending. Do not proceed to next task.

## Planned architectural transition

M2 deliberately uses a simple temporary ingestion route to prove the RAG vertical slice. **TASK-016/017 must replace it** with durable SQLite-backed jobs, a separate worker, checkpoints, staged index activation and reference-aware cleanup. The two ingestion paths must not remain as competing production entry points. No earlier simplification weakens the final design's local-only, strict grounding, deduplication, or citation rules.

## Design invariants and exclusions

- Document-only answers; missing support means abstain. Evidence IDs are validated; citation existence does not guarantee factual support.
- Qdrant holds chunks/vectors; SQLite owns documents, memberships, jobs, active generations, chat and executions; originals/parsed artifacts reside in content-addressed storage.
- Current embedding profile only; profile changes reindex. Scope resolves in SQLite and filters in Qdrant **before** vector Top-K.
- Default 500-token target/75 overlap, 10 retrieval candidates/5 selected, bounded context budget, Qwen3 generation and Nomic query/document prefixes; all configurable and verified against model runtime.
- No query snapshots/active-reader tracking, multi-user auth, OCR, hybrid retrieval, external reranker, microservices, cloud inference or automated backup in first release.
- No automated test cases by user choice; manual checks are mandatory at appropriate milestones and do not provide the regression assurance of tests.

## Completion handoff format

`TASK-NNN — Completed / Blocked`
`Changed: <paths>`
`Checked: <commands and results>`
`Manual: <steps or pending>`
`Blockers: <none or concise detail>`
