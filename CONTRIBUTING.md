# Contributing

Start with `python -m agent_workspace serve` and the bundled sample. Read `README.md`, `docs/system-architecture.md`, and `docs/REVIEW.md` before expanding the scope.

Run:

```bash
python -m unittest discover -s tests -v
python scripts/evaluate.py
node --check agent_workspace/static/app.js
```

Use temporary databases in tests. Test failure paths as well as happy paths. Never commit real memories, credentials, local databases, model outputs containing private data, or generated build directories.

For a bug, provide the command or UI steps, Python/browser versions, expected result, and a minimal shareable file/question. Tell us which answer mode and model you used. Provider contract tests should stay deterministic and offline; live model evaluation must be labelled with the actual model and conditions.

Preserve project separation and source references. A valid reference is not a factuality guarantee. Do not describe model suggestions or legacy simulations as completed actions. Keep integrations opt-in and document what leaves the machine.

Useful contributions: a regression case for a retrieval miss, accessibility feedback from the real UI, improved error messages, or evidence from a live provider run. Open an issue with the problem before adding a large new subsystem.
