"""A dry-run task simulator. It does not perform the described actions."""


def execute_tasks(tasks):
    if not isinstance(tasks, list) or any(not isinstance(task, str) for task in tasks):
        raise ValueError("Tasks must be a list of strings.")
    return [{"task": task, "status": "simulated"} for task in tasks]
