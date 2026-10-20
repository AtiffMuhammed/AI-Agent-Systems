# Memory engine

A single-process JSON store with case-insensitive substring retrieval and formatted context.

```bash
python autonomous-memory-engine/main.py --add "Built an ESP32 monitor" --query esp32
python autonomous-memory-engine/main.py --query monitor
python autonomous-memory-engine/main.py --query esp32 --store /path/to/memories.json
```

Run from the repository root. The default store is `autonomous-memory-engine/.local/memories.json`. It is created on the first write and is ignored by Git. A missing store is empty; invalid JSON or a value other than a list of strings raises an error. Existing corrupt files are preserved. Writes use a temporary file and atomic replacement; duplicate text is not appended.

`save_memory(text, path=None)` returns whether a value was added. `load_memories(path=None)` reads validated records. `retrieve_memories(query, path=None)` performs a substring search.

This does not use embeddings, semantic search, encryption, or concurrent-write locking. Treat memories as local plaintext. The tracked `memories.json` is a legacy empty example, not the new default store; migrate an existing file with `--store` if needed.
