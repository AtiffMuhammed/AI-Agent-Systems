# Architecture and next steps

These three examples are independent scripts, not an integrated production platform.

| Module | Input | Processing | Output |
| --- | --- | --- | --- |
| Memory | Text and query | Validate, atomically persist, substring-match | JSON with retrieved text and context |
| Orchestrator | Goal text | Fixed planner and simulated task statuses | JSON run log |
| Content | Filename | Template title and word-based tags | Editable JSON metadata |

All use the standard library and have no network dependencies. Each example has an importable function and an argparse CLI. Generated state goes under ignored `.local/` directories. Tests run the CLIs from an unrelated working directory.

## Candidate contributions

1. Memory: add a SQLite implementation and tests for concurrent writes and migrations.
2. Orchestrator: register a few safe Python functions as real tasks, then represent real success/failure and bounded retries.
3. Content: accept a batch CSV, validate rows, and produce per-item drafts.
4. Optional model adapter: add explicit opt-in configuration, timeouts, mocked tests, and transparent cost/error handling.

These are planned features, not claims about the current implementation. Any time-based program submission should describe the work actually completed by the participant.
