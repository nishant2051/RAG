# AGENTS.md — Codex working rules

Project: local, single-user RAG app. Stack: Python/FastAPI, React/TypeScript/Vite, SQLite/SQLAlchemy/Alembic, Qdrant, Ollama (Nomic embeddings, Qwen3 generation).

1. **Single task only.** Implement `docs/implementation/CURRENT-TASK.md` and stop. Treat it as the execution contract; follow its allowed read/write paths and explicit completion criteria.
2. **Smallest necessary context.** Read the task, relevant portions of `docs/implementation/PROJECT-MAP.md`, and necessary source/config files. Do **not** read `docs/reference/`, older completed tasks, or the full roadmap unless the current task explicitly authorizes it. Keep terminal output short.
3. **No automated tests.** Do not write unit, integration or E2E tests, fixtures, mocks, test runners, or test frameworks. Use only task-requested syntax, type, build, migration checks and minimal manual smoke checks. Never claim unrun verification passed.
4. **No scope creep.** Don't implement future tasks, add speculative abstraction, refactor unrelated code, introduce cloud dependencies, or upgrade packages unnecessarily. Interfaces for external systems only unless specified.
5. **Blockers.** Correct small local defects needed for the task. For missing major prerequisites, incompatible interfaces, unexpected dependencies, or wide repository exploration: stop and report a concise blocker. Do not consult all design docs or redesign the system independently.
6. **Maintain handoff.** On successful verification, make one focused Git commit on the current branch if Git is initialized and unrelated changes can be excluded. Update current task status and relevant project-map entries only when needed; do not overwrite unrelated edits. No commit on failed checks.
7. **Keep output brief.** Report status, changed files, checks (including pending manual checks), commit ID if any, and blockers. Do not begin the next task.

Security baseline: local-only networking, controlled filesystem paths, no secrets in Git, document text treated as untrusted, and strictly evidence-grounded answers.
