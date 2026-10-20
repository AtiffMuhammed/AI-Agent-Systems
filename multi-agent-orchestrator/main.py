import argparse
import json
from pathlib import Path

from planner_agent import plan_tasks
from executor_agent import execute_tasks
from memory_system import save_memory, get_memory, reset_memory
from logger_agent import log_output


def run_workflow(goal, output_path=None):
    tasks = plan_tasks(goal)
    reset_memory()
    save_memory({"goal": goal.strip(), "tasks": tasks})
    workflow_output = {
        "mode": "simulation",
        "goal": goal.strip(),
        "tasks": execute_tasks(tasks),
        "memory": get_memory(),
    }
    log_output(workflow_output, output_path)
    return workflow_output


def main():
    parser = argparse.ArgumentParser(description="Run a deterministic task-planning simulation.")
    parser.add_argument("goal")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = run_workflow(args.goal, args.output)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Workflow error: {error}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
