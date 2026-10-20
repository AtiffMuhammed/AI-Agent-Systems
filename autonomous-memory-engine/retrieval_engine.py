"""Case-insensitive substring retrieval, not semantic search."""
from memory_store import load_memories


def retrieve_memories(keyword, path=None):
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError("Search query must be a non-empty string.")
    query = keyword.strip().casefold()
    return [memory for memory in load_memories(path) if query in memory.casefold()]
