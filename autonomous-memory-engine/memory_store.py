import json

MEMORY_FILE = 'memories.json'


def save_memory(memory):
    try:
        with open(MEMORY_FILE, 'r') as f:
            data = json.load(f)
    except:
        data = []

    data.append(memory)

    with open(MEMORY_FILE, 'w') as f:
        json.dump(data, f, indent=4)
