from planner_agent import plan_tasks
from executor_agent import execute_tasks
from memory_system import save_memory, get_memory
from logger_agent import log_output


def run_workflow(goal):
    tasks = plan_tasks(goal)

    save_memory({"goal": goal, "tasks": tasks})

    results = execute_tasks(tasks)

    workflow_output = {
        "goal": goal,
        "tasks": results,
        "memory": get_memory()
    }

    log_output(workflow_output)

    print("🚀 Multi-agent workflow completed")


if __name__ == "__main__":
    goal = input("Enter workflow goal: ")
    run_workflow(goal)
