# TASK-003 — React Application Shell

**Milestone:** M1 — Foundation
**Depends on:** TASK-001 (`1879792`, reported complete) and existing FastAPI foundation TASK-002 (`e322247`, reported complete)
**Status:** Complete — TypeScript/build, browser navigation and keyboard focus, development default and invalid remote URL checks passed. No automated tests added.
**Manual follow-up:** TASK-001 combined scaffold smoke check is still pending. Do not mark it passed unless actually performed.

## Objective

Turn the existing React + TypeScript + Vite scaffold into a small, usable **application shell** with minimal navigation, a typed frontend API configuration, and clear placeholders for future RAG features. Keep all implementation local-first, lightweight, and scoped to the frontend. Do **not** implement document upload, chat, API integration, or visual polish in this task.

## Required context and discovery budget

1. Follow the root `AGENTS.md` and this file (`docs/implementation/CURRENT-TASK.md`).
2. Inspect only the relevant `PROJECT-MAP.md` frontend section, `frontend/package.json`, Vite config, `src/main.*`, `src/App.*`, existing styles, and any existing frontend configuration file. Confirm actual paths before changing them; the examples below are **proposed**, not verified against your local repository.
3. Check root `.env.example` and the existing FastAPI base path only if needed for URL naming; do not read backend feature modules.
4. Do not read `docs/reference/`, completed tasks, the full implementation plan, or unrelated backend files.
5. If the scaffold differs significantly from these assumptions, adapt only within the current frontend scope; stop and report if substantial redesign is necessary.

## Suggested file changes (use actual matching paths)

- `frontend/src/App.tsx`: shell layout and minimal navigation.
- `frontend/src/App.css` or existing stylesheet: basic responsive styling.
- `frontend/src/index.css`: lightweight global defaults if already present.
- `frontend/src/config.ts` (new if useful): validated API base URL accessor.
- `frontend/.env.example` (new if needed): example `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`.
- `frontend/README.md` or root `README.md`: only if a short clarification is needed for frontend startup/configuration.
- `docs/implementation/PROJECT-MAP.md`: update implemented frontend entry points after confirming actual files.
- `docs/implementation/IMPLEMENTATION-PLAN.md`: mark TASK-003 completed *only after required checks pass*.

Avoid creating unrelated files, new libraries, icon kits, design systems, or empty feature modules.

## Functional requirements

1. Display a clear app title (e.g. **Local RAG**) and minimal persistent navigation with three destinations: **Documents**, **Chat**, and **Diagnostics**.
2. The Documents view presents a short *Coming later* description for document upload/library (TASK-014 and later); Chat similarly indicates questions and answers are not yet implemented; Diagnostics indicates future retrieval inspection. These are placeholders, not simulated working features.
3. Use simple local React state to switch views. Do not add React Router, state-management packages, or component libraries unless they were already installed in TASK-001. Do not create a fake backend or fake document data.
4. Provide a responsive, keyboard-accessible layout: semantic landmarks, labeled navigation controls, visible keyboard focus, and clear selected view state. A minimal functional style is enough; premium Stitch-based design is deferred.
5. Centralize the frontend API base URL via Vite environment configuration. Default to `http://127.0.0.1:8000/api/v1` only for local development. Validate that configured URLs are well formed and use loopback hosts for the initial local-only app; fail clearly on invalid config rather than silently using a remote service. Do not make network calls in this task.
6. Preserve the existing TypeScript/Vite startup and build behavior. Keep the implementation simple and easy to replace when actual API-connected views arrive.
7. Do not change FastAPI, database, Docker, Ollama, or Qdrant code.

## Explicit exclusions

- No upload forms, ingest-progress polling, document listing, chat sessions, SSE, model-selection settings, or API fetches.
- No complex routing, authentication, design frameworks, production deployment, or speculative abstractions.
- **No automated tests**, test framework configuration, mocks, fixtures, or test scripts added.
- No reference-document scanning or work on TASK-004.

## Lightweight verification (no automated tests)

- Run the frontend's existing TypeScript check and production build (`npm run build` and any existing typecheck script). Do not add new test scripts.
- Start the Vite dev server locally and manually verify that the app loads, the three views switch, keyboard navigation/focus is apparent, and there are no visible runtime errors. If unable to run a browser, say which checks remain pending.
- Inspect local API URL configuration behavior (valid default + clear invalid-config failure) without implementing an automated test.
- Run `git diff --check`, review short Git status, and avoid staging unrelated changes.
- If practical, also close TASK-001's pending combined scaffold smoke check by starting the *existing* backend and frontend using documented commands. Report separately; don't expand TASK-003 to fix unrelated backend problems.

## Handoff and completion

- Update `PROJECT-MAP.md` only with actual implemented frontend modules/entry points. Mark TASK-003 completed in the roadmap if present; do not edit historical tasks.
- Make a single focused Git commit on the current branch **after** required task checks pass, excluding unrelated changes. If blocked, do not commit and report the blocker.
- Final response: task status + commit; files changed; checks passed/pending; blockers or deviations. Keep it to approximately four lines.
- **Stop after TASK-003. Do not start TASK-004.**
