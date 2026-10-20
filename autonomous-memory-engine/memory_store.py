"""Single-process JSON memory store with atomic replacement."""
import json
import os
from pathlib import Path
import tempfile

MEMORY_FILE = Path(__file__).resolve().parent / ".local" / "memories.json"


def load_memories(path=None):
    target = Path(path) if path is not None else MEMORY_FILE
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise ValueError("Memory file is invalid JSON; repair it before saving.") from error
    if not isinstance(data, list) or any(not isinstance(item, str) for item in data):
        raise ValueError("Memory file must contain a JSON list of strings.")
    return data


def save_memory(memory, path=None):
    if not isinstance(memory, str) or not memory.strip():
        raise ValueError("Memory must be a non-empty string.")
    memory = memory.strip()
    target = Path(path) if path is not None else MEMORY_FILE
    data = load_memories(target)  # Fail before writing if existing data is corrupt.
    if memory in data:
        return False
    data.append(memory)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                         dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return True
