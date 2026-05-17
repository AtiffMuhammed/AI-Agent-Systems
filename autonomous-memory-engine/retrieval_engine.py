import json

MEMORY_FILE = 'memories.json'


def retrieve_memories(keyword):
    try:
        with open(MEMORY_FILE, 'r') as f:
            memories = json.load(f)
    except:
        return []

    results = []

    for memory in memories:
        if keyword.lower() in memory.lower():
            results.append(memory)

    return results
