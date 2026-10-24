# V3 development milestones and devlog drafts

These drafts describe actual code changes in this upgrade. They are grouped by feature, not assigned to invented days or coding hours. No devlogs have been posted to Terra or Stardance. Add only personal testing, learning, screenshots, and tracked time that you actually completed.

The earlier V1/V2 devlogs were not available for review. These entries therefore cover the new implementation; they do not rewrite the past.

## 1. Making project memory persistent and searchable

The first V3 milestone replaces disconnected memory demonstrations with a real project memory layer. Notes and source files are stored in SQLite, split into line-preserving passages, and indexed with FTS5/BM25. Projects are kept separate, unchanged imports are detected by hash, and updating a file removes its old search entries in the same transaction. Sources now carry filenames and exact line ranges so results can be inspected rather than taken on trust. Automated checks cover reindexing, deletion, project separation, concurrent task writes, and preserved source snapshots. Earlier demonstration scripts were also corrected to label their simulations accurately.

**Evidence to show:** import a note, search it, change it, and show that the old text stops matching. Code: `agent_workspace/store.py`, `tests/test_store.py`. Commit subject: `feat: add transactional project memory and ranked source search`.

## 2. Building an answer pipeline with traceable sources

The second milestone connects retrieval to a bounded answer pipeline. Evidence mode returns actual source excerpts without a model call. Optional Ollama and OpenRouter adapters request structured claims and suggestions; a validator rejects missing or invalid source references. When a provider fails or returns unusable output, the result visibly falls back to excerpts instead of pretending the model succeeded. Each run saves its question, source snapshots, selected mode, warnings, and processing trace. Suggestions remain proposals and never execute tasks. Provider contracts and invalid-reference cases are covered by automated tests; live model quality still needs testing with a configured model.

**Evidence to show:** ask a question, open its source reference, then compare evidence mode with an actually configured model. Code: `engine.py`, `providers.py`, `tests/test_engine.py`. Commit subject: `feat: add evidence-grounded answer pipeline and optional model adapters`.

## 3. Turning the components into a usable workspace

The third milestone delivers a browser workspace and a command-line interface. Users can create projects, import files, inspect source text, ask questions, reopen reports, and download Markdown or JSON exports. A persistent task board supports To do, In progress, and Done, with every move controlled by the user. Explicit TODOs in retrieved notes can be offered as tasks even in offline mode. The bundled fictional ESP32 sample goes through the real import/search pipeline. An HTTP integration test exercises importing, asking, exporting, updating a task, and reopening saved evidence after the original source is deleted. Browser visual checks remain a separate verification step.

**Evidence to show:** a screen recording of the sample question, source inspection, accepted TODO, task status change, and downloaded report. Code: `server.py`, `cli.py`, `static/`, `tests/test_http.py`. Commit subject: `feat: ship local web workspace with source inspection reports and task board`.

## 4. Reviewing reliability, privacy, and release readiness

The final milestone reviews the application as a usable local tool. Requests are restricted to loopback hosts and same-origin sessions, imported text renders as text, provider redirects are refused, and response sizes are bounded. The review fixed provider-response resource cleanup and UI state restoration after failed saves. A small reproducible evaluation checks seven questions against the bundled sample, including a no-evidence question. Documentation now explains setup, provider configuration, data storage, exports, and the distinction between valid citations and factual accuracy. The full automated suite passes, but live model inference and visual browser checks are explicitly unverified in this environment.

**Evidence to show:** your own test output, the retrieval evaluation, and a model-backed run if you have configured one. Code: `tests/test_provider_transport.py`, `scripts/evaluate.py`, `docs/REVIEW.md`. Commit subject: `fix: harden provider failures and document the V3 release`.

## Before publishing any entry

Use screenshots from the actual running application. Add a sentence about what you personally tested or changed, if applicable. These are technical milestone updates, not evidence of multiple separate work sessions. Do not assign the same work or time repeatedly to multiple projects or programs.
