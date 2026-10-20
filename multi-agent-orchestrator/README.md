# Task-planning simulator

A small teaching example that separates a deterministic planner, simulated executor, process-local memory, and JSON logger.

```bash
python multi-agent-orchestrator/main.py "Review a workflow"
python multi-agent-orchestrator/main.py "Review a workflow" --output /path/to/run.json
```

The result contains `mode: "simulation"` and task status `simulated`. **No described task is actually performed.** The planner produces four fixed task labels; there is no LLM, tool invocation, scheduler, or autonomous execution.

The default log is `multi-agent-orchestrator/.local/output_log.json`. Each run resets memory; callers receive copies to avoid accidental state mutation. This demonstration uses process-global memory and is not a concurrent service.

The tracked `tasks.json` and `output_log.json` are examples. They are not runtime configuration or output destinations. A useful next contribution would be a small registry of explicitly allowed actions with real results, clear errors, and tests.
