# V3 code review and validation

Reviewed 2026-10-20. Review was performed directly against source and tests. A separate Code Review plugin was not callable in this session; no independent third-party audit is claimed.

## Verified locally

- **39 Python unittest cases pass** on Python 3.12, including the ten earlier example tests.
- The HTTP workflow imports evidence, asks a question, exports Markdown/JSON, changes a task status, deletes a source, reopens the saved evidence snapshot, and clears report history.
- Concurrent SQLite writes, source reindexing/deletion, project separation, malformed imports, bad model references, provider failures, and cloud-consent checks pass.
- Provider HTTP transport is exercised against a loopback test server. Redirects are refused; invalid JSON, oversized responses, and HTTP errors become bounded error messages. These are contract checks, not real LLM responses.
- `python scripts/evaluate.py`: **7/7** authored sample retrieval cases pass. This measures whether expected passages are retrieved, not answer truthfulness or general retrieval accuracy.
- `node --check agent_workspace/static/app.js` passes.
- A wheel can be built without dependency resolution; installed-package resource and CLI checks are recorded in the delivery validation manifest.

## Findings addressed

1. **Old task executor claimed completion without execution.** Legacy scripts now label simulation. New task statuses only change through explicit user updates.
2. **Source changes could invalidate later inspection.** Reports store evidence snapshots and content hashes, separate from live source records.
3. **Model references could be invented.** Each claim requires source IDs from that request's retrieval. Invalid output causes a visible excerpt fallback.
4. **Provider errors and redirects needed safe handling.** HTTP error responses are closed, redirects are refused before forwarding, and provider bodies/keys are not returned to the client.
5. **Failed UI saves could leave misleading selections.** Task status and project selectors restore their previous state when a request fails.
6. **Sensitive local data needed clear boundaries.** Loopback binding, Host/Origin checks, session tokens, output escaping, private database permissions on POSIX, explicit cloud consent, and documented plaintext storage are implemented.
7. **Exported suggestions could contain active Markdown.** Untrusted labels and suggested steps are escaped; source bodies and claim text use fences longer than any embedded backtick sequence.

## Not verified / limits

- No live Ollama or OpenRouter inference: no model service or API credentials were supplied. Model-specific compatibility, inference speed, and answer quality need a real run.
- The cloud browser could not connect to the local server (`ERR_CONNECTION_REFUSED`). No browser visual, mobile layout, screen-reader, or full browser interaction pass is claimed. API flows and JavaScript syntax were checked.
- Python 3.10/3.14 and GitHub Actions are configured targets; only Python 3.12 was run locally. Remote CI status must be checked after publishing.
- Search is lexical. Citation validation checks reference structure, not semantic entailment. Malicious or misleading sources can still influence a model's prose.
- This is a personal local application, with no public deployment authentication, encrypted storage, PDF/OCR, semantic embeddings, external tool execution, or multi-user permission system.
- No real-user adoption, benchmark superiority, GitHub stars, coding hours, or program eligibility is asserted.

## Useful next validation

Run the UI locally at desktop and phone widths. Configure one local model, answer five questions grounded in your own notes, and manually check every claim against its evidence. Ask three makers to try their own projects and record failures before expanding the feature list.
