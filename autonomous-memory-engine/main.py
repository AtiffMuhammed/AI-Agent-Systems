import argparse
import json
from pathlib import Path

from memory_store import save_memory
from retrieval_engine import retrieve_memories
from context_injector import inject_context


def run_memory_engine(memory, query, path=None):
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query must be a non-empty string.")
    if memory is not None:
        save_memory(memory, path)
    results = retrieve_memories(query, path)
    return {"query": query, "retrieved_memories": results,
            "context": inject_context(query, results)}


def main():
    parser = argparse.ArgumentParser(description="Store and search local text memories.")
    parser.add_argument("--add", help="Optional memory to store")
    parser.add_argument("--query", required=True)
    parser.add_argument("--store", type=Path, help="Custom JSON storage file")
    args = parser.parse_args()
    try:
        result = run_memory_engine(args.add, args.query, args.store)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Memory error: {error}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
