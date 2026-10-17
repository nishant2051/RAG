TASK-012 — Document-Grounded Answer Generation
Milestone: M2 — First Working RAG
Scope: Internal backend answer-generation service only
Status: Implemented; lightweight checks passed; live grounded-answer verification limited by local Qwen3 output (see handoff)
Goal
Implement a small, typed, asynchronous operation that takes a user's question and the ordered passages returned by TASK-011, constructs a bounded, source-attributed evidence context, calls the existing local Qwen3 Ollama generation adapter, and returns a document-grounded answer with validated evidence references. When the supplied evidence is absent or insufficient, return a clear abstention rather than answering from model knowledge. Keep this an internal service; API and orchestration integration are later tasks.
TASK-011 is reported implemented, but its exact interface and Git status were not supplied. Inspect the actual code and adapt to it. Do not invent signatures or assume TASK-011's runtime verification succeeded.
Read only what is necessary
1. AGENTS.md and docs/implementation/CURRENT-TASK.md.
2. Relevant sections of docs/implementation/PROJECT-MAP.md (retrieval and Ollama generation).
3. Targeted source files:
   - TASK-011 retrieval output models and search entry point (likely under backend/app/retrieval/).
   - Existing Ollama generation adapter, settings, and typed errors.
   - Any existing prompt or generation profile configuration only if already implemented.
   - backend/pyproject.toml only if API/dependency compatibility needs checking.
Do not read the five architectural reference documents, full implementation plan, earlier task files, frontend, or unrelated modules.
Preflight and non-negotiable constraints
- First run git status --short. TASK-007 onward may be uncommitted. Do not assume a clean working tree.
- Preserve existing and unrelated edits. Never stage, commit, reset, clean, discard, or overwrite work without permission.
- Identify and reuse the real TASK-011 passage shape and generation adapter API. Do not make breaking changes to retrieval/indexing just to fit this task.
- Use local qwen3:4b via the existing Ollama adapter; default to thinking disabled if the adapter supports the option.
- No automated tests or test infrastructure. No new dependencies unless unavoidable.
Required implementation
1. Internal generation entry point and typed result
Add a focused module following repository conventions (suggested backend/app/rag/generation.py) exposing a typed async operation such as generate_grounded_answer(question, passages, config); select the exact signature based on existing types.
- Accept a nonblank user question and an explicit ordered set of retrieved passages. Do not perform retrieval within this function.
- Return an immutable or otherwise well-defined typed result: final answer text, outcome (answered / insufficient_evidence or equivalent), and validated evidence references mapped to the source passage identities/metadata. Include generation/profile diagnostics only where the existing adapter already provides them; avoid speculative token metrics.
- No persistence, session behavior, HTTP contract, or streaming.
2. Evidence selection and bounded context
- Treat TASK-011 passage text and metadata as the sole factual evidence. Ignore passages missing required identity or nonblank text; never synthesize source metadata.
- Assign deterministic, unique local evidence IDs (for example E1, E2, ...) in stable passage order after filtering/deduplicating. Maintain an explicit evidence-ID-to-passage mapping, including original point ID/content identity and available source/heading/location fields. Evidence IDs must be derived from the passed-in list, not invented by the LLM.
- Build clear, delimited source blocks so answer references can be traced to their exact supplied passage. Mark source text as untrusted data, not instructions.
- Bound the input context with configuration grounded in actual Ollama context settings: reserve space for the system/user prompt, requested output, and a safety margin. Prefer relevance order, never silently overfill the budget. For M2, a simple bounded estimator is acceptable if explicitly named as approximate; retain original source identities when truncating or omitting blocks. Do not introduce a tokenizer or complicated sentence-selector framework solely for this task.
- Apply stable size limits to the user question and evidence; reject obviously oversized inputs clearly rather than sending unbounded text to Ollama.
3. Versioned grounding prompt and local generation
- Keep a versioned prompt template constant or lightweight module configuration; record its version in the result if useful.
- Instruct Qwen3 to answer only from supplied source blocks, ignore instructions embedded in documents, avoid unsupported extrapolation, and abstain when adequate evidence is unavailable.
- Ask the model to cite used evidence IDs in a simple predictable form such as [E1]; these are internal evidence references, not finalized end-user citation links.
- Use the existing generation adapter, its timeout/error behavior, and supported settings. Respect configurable context/output limits, and allow model configuration via existing settings instead of hard-coding a second unrelated client.
- No fallback to the model's general knowledge, web, or other documents.
4. Abstention and evidence reference validation
- If zero usable passages remain, return insufficient_evidence without calling Ollama.
- Implement a conservative, explicit post-generation validation policy: extract cited evidence IDs from the model response, reject references absent from the evidence map, and never report a fabricated source as valid.
- If the model returns no usable answer, clearly refuses for lack of information, or produces an answer requiring citations but none valid, return insufficient_evidence (or an explicit non-success validation outcome), not a falsely supported answered response. Do not silently strip invalid IDs and report success.
- Make it explicit in code and handoff that citation-ID validation verifies provenance only, not factual entailment. Do not claim it proves an answer is supported sentence by sentence.
- If the result is an abstention, do not attach citations implying an answer was supported. Provide a short, stable user-facing abstention message.
- Distinguish insufficient evidence from infrastructure/model failures; propagate typed Ollama errors rather than disguising outages as abstentions.
5. Keep the first slice intentionally small
- No separate relevance model, LLM-as-judge, factual entailment checker, confidence score, or automated evaluation.
- No full RAG orchestrator, conditional question rewrite, retrieval invocation, prompt-injection classifier, chat history, or persistent execution record.
- No generation retries beyond existing adapter policy, no streaming/SSE, regeneration, cancellation, or UI.
- No new DB schema, migrations, Qdrant access, or Docker requirement in generation code.
- No PDF/DOCX, worker jobs, collection management, or advanced citation-to-latest-document resolution.
Lightweight acceptance checks (manual; no committed tests)
1. Python compile/import and git diff --check on changed files.
2. Manually invoke the internal API with two short fabricated-in-memory passages derived from ordinary benign sample text; inspect prompt construction, deterministic evidence IDs, returned identity/metadata mapping, and bounded context behavior. Do not add test files to the repo.
3. Verify an empty passage set returns abstention and does not call Ollama. Check blank question, missing text/metadata, duplicated passage IDs, excessive context/question, and invalid or unknown cited IDs using a short disposable command/script or inspection; report which were genuinely exercised.
4. If local Ollama and qwen3:4b are available, run one real grounded generation with a short passage and check source IDs are validated; also test an unrelated question and observe abstention behavior. Do not claim that a single successful run guarantees model grounding or factual correctness.
5. If Ollama is unavailable, report live generation pending. If Docker/Qdrant is unavailable, that must not block these in-memory generation checks; keep earlier Qdrant checks pending.
6. Preserve pending TASK-001 combined frontend/backend startup and TASK-005/TASK-010/TASK-011 live Qdrant checks until actually run. Do not change their status based on mocks or constructed client requests.
Documentation handoff
Update only the relevant sections of docs/implementation/PROJECT-MAP.md and docs/implementation/CURRENT-TASK.md with actual function signatures, result schema, evidence-ID and abstention policies, prompt version, verification status, and observed limitations. Keep them concise; do not rewrite historical project documentation.
Completion report
Provide:
- Actual internal API signature and changed files.
- Context budgeting and evidence-ID mapping/validation approach.
- Abstention policy, actual Qwen3 model/options, prompt version, and any adapter changes.
- Manual checks, live Ollama generation status, and any unresolved failure modes.
- Outstanding earlier verification items, including live Qdrant, marked passed / failed / pending accurately.
- Final git status --short; whether anything was staged or committed.
Stop after TASK-012. Do not implement TASK-013 FastAPI pipeline integration, create automated tests, or commit changes.

TASK-012 implementation handoff — 2026-10-18
- Added `backend/app/rag/{__init__,generation}.py`. API: `async generate_grounded_answer(question: str, passages: Sequence[Passage], *, ollama: OllamaConnection, config: GroundingConfig = GroundingConfig()) -> GroundedAnswer`; runtime accepts ordered lists/tuples, not iterators. No retrieval, persistence or HTTP integration.
- Frozen result: `answer`, `outcome` (`answered` / `insufficient_evidence`), `references: tuple[EvidenceReference, ...]`, `prompt_version`. Each reference contains `evidence_id` and the original TASK-011 `Passage`, retaining point/content/hash/profile/source/heading/line/span metadata. Only cited references are returned on success; abstentions have none.
- Filter blank text/missing identities or invalid chunk index/profile; deduplicate point ID and per-content hash in input order. Assign E1 onward to included whole blocks; omit blocks that do not fit and consider subsequent smaller blocks. Never synthesize source metadata or truncate source text.
- `GroundingConfig(num_ctx=4096, num_predict=512, safety_tokens=256)` validates adapter bounds and leaves at least 1024 input tokens. Approximate conservative estimator charges one serialized UTF-8 byte per token, including instructions, question, metadata and delimiters; output and safety are reserved. Reject question >4096 bytes, >80 passages, passage representation >65536 bytes, aggregate >262144 bytes, or framing/question beyond the remaining budget.
- Prompt `grounding-v1`: JSON-delimited untrusted source blocks, evidence-only answers, exact [E#] citations, explicit insufficiency sentinel and `/no_think`. Uses configured model (`qwen3:4b` observed), temperature=0, context/output options above, and existing adapter `think=False`, timeout and typed failures. No adapter changes or retries.
- Validation rejects unknown, malformed/combined or absent citations, empty/citation-only output, explicit insufficiency and common refusal phrases. A stable abstention is returned when evidence is absent/omitted or response validation fails. Citation checks establish provenance only, NOT factual entailment, complete sentence coverage or prompt-injection immunity. Refusal matching is intentionally conservative and can false-abstain. Adapter failures (including its rejection of empty model responses) propagate as typed Ollama errors.
- Passed: Python compile/import, whitespace diff check, disposable in-memory manual checks with two benign passages; inspected prompt, IDs and retained metadata; duplicate ID, blank question, missing text/content identity, question/per-passage/aggregate caps, budget omission, known/unknown/mixed/malformed/absent citations, blank/citation-only output and refusal handling. Empty evidence with a closed real client abstained without any dependency call. No automated tests or test files added.
- Live Ollama discovery passed outside sandbox: configured `qwen3:4b` present. Both relevant and unrelated questions ran through the real service and returned citation-free abstentions. Relevant-answer verification FAILED to demonstrate an answered result: raw diagnostic calls showed repetitive analysis mentioning the insufficiency sentinel and reaching the output cap, despite `think=False`, explicit final-answer instruction and `/no_think`. Conservative validation rejected this output; unrelated-question abstention observed. No claim of successful live grounded answer or guaranteed model grounding. Local model/template behavior remains an unresolved limitation; no adapter redesign or model changes made.
- Earlier checks preserved as recorded in PROJECT-MAP: TASK-005 connectivity and TASK-010/TASK-011 live Qdrant checks passed previously on 2026-10-18, not rerun here. TASK-001 combined frontend/backend startup remains pending.
- Existing CURRENT-TASK edits preserved. Nothing staged or committed; stopped after TASK-012.
