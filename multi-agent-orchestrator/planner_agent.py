"""Deterministic planning template; no model call."""


def plan_tasks(goal):
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("Goal must be a non-empty string.")
    return [
        f"Analyze goal: {goal.strip()}",
        "Generate execution strategy",
        "Execute workflow",
        "Store results",
    ]
