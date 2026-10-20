# AI Agent Systems · V3.0

**A local project copilot that turns scattered notes into searchable memory, cited answers, and concrete next steps.**

Import a README, specification, code file, test plan, or decision record. Ask about your project, inspect the exact source lines behind the result, and save useful next steps to a task board. Export the report and its evidence when you need to share your reasoning.

The default mode works immediately with Python. No API key, model download, Docker, JavaScript build, or third-party Python runtime dependency is required.

## Run in three minutes

Requires **Python 3.10+ with SQLite FTS5**, included in most standard Python builds.

```bash
git clone https://github.com/AtiffMuhammed/AI-Agent-Systems.git
cd AI-Agent-Systems
python -m agent_workspace serve
```

Open **http://127.0.0.1:8765** on the same computer. Click **Try sample project**, then **Find an answer**. The sample is a clearly labelled fictional ESP32 irrigation project, indexed by the same pipeline as your own imports.

Try these questions:

- `How often does the firmware sample soil moisture?`
- `What calibration tests are TODO?`
- `What do the notes say about battery current and runtime?`

For your own work, create a project and import its files. Matching filenames update existing sources. Use specific project terms: the search is lexical, so it may miss paraphrases.

## What you can actually do

| Feature | Result |
| --- | --- |
| Project memory | Store UTF-8 notes and code in SQLite; keep evidence separated by project |
| Ranked search | Retrieve matching passages with BM25, filenames, line ranges, and content hashes |
| Evidence mode | Read actual matching source lines without making a model request |
| Optional AI synthesis | Ask a configured Ollama or OpenRouter model for claims and suggested actions |
| Reference checks | Reject model claims citing unavailable source IDs; fall back visibly to excerpts |
| Task board | Add manual tasks or accept suggestions; update To do / In progress / Done yourself |
| Saved reports | Reopen original evidence snapshots after a source is changed or deleted |
| Export | Download Markdown or JSON containing the question, result, sources, and processing trace |
| CLI | Create projects, import a folder, ask questions, and print reports from a terminal |

Supported imports: `.md`, `.txt`, `.py`, `.js`, `.ts`, `.tsx`, `.jsx`, `.json`, `.csv`, `.yaml`, `.yml`, `.ino`, `.rst`, `.html`, `.css`. Each file must be UTF-8, at most 1 MB, with no line longer than 6,000 characters. PDFs, images, audio, and URLs are not ingested. Hidden and sensitive-looking filenames are rejected; this is **not a complete secret scanner**.

## Optional model synthesis

Evidence mode is intentionally labelled as retrieval, not generative AI. Enable a provider when you want a synthesized answer. The model sees the standalone question and up to six selected source passages, not the entire database or another project's notes.

### Ollama on the same computer

Install [Ollama](https://ollama.com), download a model your computer can run, and set `OLLAMA_MODEL` to that installed model's exact name. Start Ollama, then launch this app. The adapter calls `http://127.0.0.1:11434/api/chat` with a JSON schema, no redirects, and a 45-second socket timeout. Use a local model; cloud-backed Ollama models may forward inputs to a provider.

macOS / Linux:

```bash
export OLLAMA_MODEL='your-installed-model'
python -m agent_workspace serve
```

Windows PowerShell:

```powershell
$env:OLLAMA_MODEL = 'your-installed-model'
python -m agent_workspace serve
```

Choose **Ollama** in the app. A missing service, unsupported format, or invalid response produces a visible evidence-mode fallback.

### OpenRouter

Set `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` in the environment before starting the app. Choose a model supporting JSON responses, using its exact ID from [OpenRouter's model list](https://openrouter.ai/models). Keys are never sent to the browser or stored in the workspace database. This app does not automatically load `.env` files.

Select **OpenRouter** and confirm sending the question and selected passages for that request. Provider charges, retention, and routing policies apply. There are no automatic retries or background model calls.

## CLI and storage

```bash
python -m agent_workspace sample
python -m agent_workspace projects
python -m agent_workspace create "My build"
python -m agent_workspace import PROJECT_ID path/to/notes
python -m agent_workspace ask PROJECT_ID "What tests are TODO?" --markdown
python -m agent_workspace ask PROJECT_ID "How does calibration work?" --provider ollama
```

`PROJECT_ID` is the ID printed by `sample`, `create`, or `projects`. Folder import skips hidden folders, symlinks, dependency/build folders, and unsupported files; it reports skipped files and accepts at most 250 candidates at once. It does not interpret `.gitignore`; choose your notes directory rather than an entire private home folder. Web uploads accept up to 50 files at a time.

Data defaults to `~/.agent-workspace/workspace.sqlite3`. Choose another database with `python -m agent_workspace --db path/to/workspace.sqlite3 serve`. On POSIX the database file is set to owner-only access; the default data directory is private. Storage is **not encrypted**. Stop the server before copying the database for backup. Deleting a source preserves quotes in old reports; delete that project's report history separately to remove those snapshots. Backups may retain old content.

Optionally install the CLI with `python -m pip install .` and run `agent-workspace serve` from any folder. Package building may download build tooling; running directly from the checkout does not need installation.

## Scope and trust

This is a **single-user application bound to loopback**. It has no public account system and should not be exposed with a tunnel or hosted as a public server. Host checks, same-origin requests, a session token, output escaping, and a content security policy protect the local interface; they are not a replacement for multi-user authentication.

Valid source IDs do **not** prove an AI claim is true. Search can retrieve irrelevant matches, and models can misread evidence or follow malicious source text despite the prompt. Read the source snapshots. The model has no shell, file-writing, publishing, or external tool permissions; suggested actions never execute automatically.

The earlier examples remain available in [autonomous-memory-engine](autonomous-memory-engine/), [multi-agent-orchestrator](multi-agent-orchestrator/), and [content-pipeline-engine](content-pipeline-engine/). Their limitations are documented. The new `agent_workspace` package is the V3 product.

## Verify and contribute

```bash
python -m unittest discover -s tests -v
python scripts/evaluate.py
node --check agent_workspace/static/app.js
```

The evaluation uses a tiny authored sample; it is not a general accuracy benchmark. Provider contract tests use a local test server and mocks, not live model inference. See the [review and validation record](docs/REVIEW.md) for exact checks and unverified areas.

Read the [architecture](docs/system-architecture.md), [contributing guide](CONTRIBUTING.md), [AI assistance disclosure](AI_ASSISTANCE.md), and [release milestones/devlogs](docs/DEVLOGS.md). Licensed under [MIT](LICENSE).

If this helps you keep track of a real project, a star helps others discover it. More useful still: report an unclear answer with a small, shareable source file and the question that produced it.
