"""Process-local teaching example with explicit run isolation."""
from copy import deepcopy

memory_store = []


def save_memory(data):
    memory_store.append(deepcopy(data))


def get_memory():
    return deepcopy(memory_store)


def reset_memory():
    memory_store.clear()
