# AI Agent Systems

**Small, runnable Python examples for learning memory, task planning, and content pipelines.**

[![Tests](https://github.com/AtiffMuhammed/AI-Agent-Systems/actions/workflows/tests.yml/badge.svg)](https://github.com/AtiffMuhammed/AI-Agent-Systems/actions/workflows/tests.yml)

These are transparent learning prototypes. The current code uses Python's standard library: it does not call an LLM, generate videos, publish content, or execute the actions described in a plan.

## Run the examples

Requires Python 3.10+. Clone this repository and run from its root; no dependencies or API keys are needed.

| Example | What it actually does |
| --- | --- |
| [Memory engine](autonomous-memory-engine/) | Stores text in JSON, retrieves case-insensitive substring matches, formats context |
| [Orchestrator](multi-agent-orchestrator/) | Builds a fixed task plan, simulates execution, and saves a per-run JSON log |
| [Content pipeline](content-pipeline-engine/) | Drafts editable titles, keywords, and hashtags from a filename |

```bash
python autonomous-memory-engine/main.py --add "Building n8n workflows" --query n8n
python multi-agent-orchestrator/main.py "Review my automation workflow"
python content-pipeline-engine/main.py "ESP32_workflow_demo.mp4"
```

Every command prints JSON. Generated files go into an ignored `.local/` directory beside the relevant script, independently of your current working directory. Use `--store` for a custom memory file or `--output` for a custom log/content package.

## Reliability details

- Memory writes use atomic replacement. Invalid existing data raises an error instead of being silently overwritten.
- Blank inputs are rejected; duplicate memories are not added twice.
- Orchestrator tasks are explicitly marked `simulated`. Each run starts with isolated process-local history.
- Metadata is a filename template, not media analysis or a claim of search-ranking performance.
- The scripts make no network calls. The legacy `.env.example` is not loaded by these examples.

The memory store is intended for a single process. Atomic replacement avoids partial writes, but does not prevent concurrent writers from losing updates. Use a transactional database before multi-user deployment.

## Development

```bash
python -m unittest discover -s tests -v
```

Tests cover corrupt-file preservation, interrupted writes, Unicode retrieval, run isolation, and all three command-line demos. CI is configured for Python 3.10, 3.12, and 3.14.

See [architecture and next steps](docs/system-architecture.md), [contributing](CONTRIBUTING.md), and [AI assistance disclosure](AI_ASSISTANCE.md).

For a practical n8n utility, see [FlowCheck](https://github.com/AtiffMuhammed/Python-Automation-Lab), an offline workflow export checker.
