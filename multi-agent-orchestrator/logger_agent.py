import json
from pathlib import Path

DEFAULT_LOG = Path(__file__).resolve().parent / ".local" / "output_log.json"


def log_output(data, path=None):
    target = Path(path) if path is not None else DEFAULT_LOG
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target
