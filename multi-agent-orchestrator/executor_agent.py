def execute_tasks(tasks):
    completed = []

    for task in tasks:
        completed.append({
            "task": task,
            "status": "completed"
        })

    return completed
