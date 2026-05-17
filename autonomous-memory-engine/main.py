from memory_store import save_memory
from retrieval_engine import retrieve_memories
from context_injector import inject_context


def run_memory_engine():
    memory = input("Enter new memory: ")
    save_memory(memory)

    query = input("Search keyword: ")

    results = retrieve_memories(query)

    context = inject_context(query, results)

    print("Injected Context")
    print(context)


if __name__ == "__main__":
    run_memory_engine()
