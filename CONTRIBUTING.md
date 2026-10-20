# Contributing

Run `python -m unittest discover -s tests -v` from the root. Keep changes focused and update the relevant example's README when behavior changes.

For bugs, include the command, Python version, expected result, and a small example with no private memories or credentials. Tests should use temporary paths and preserve existing data on failure.

Do not describe simulated actions as completed work. New integrations should be opt-in, have bounded failure handling, and use mocked tests. See `docs/system-architecture.md` for proposed next steps.
