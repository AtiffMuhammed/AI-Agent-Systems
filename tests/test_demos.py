import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "autonomous-memory-engine"))
from memory_store import load_memories, save_memory
from retrieval_engine import retrieve_memories


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "memories.json"

    def test_round_trip_unicode_and_duplicate(self):
        self.assertTrue(save_memory("  Building an ESP32 café monitor  ", self.path))
        self.assertFalse(save_memory("Building an ESP32 café monitor", self.path))
        self.assertEqual(retrieve_memories("CAFÉ", self.path), ["Building an ESP32 café monitor"])

    def test_missing_store_is_empty(self):
        self.assertEqual(load_memories(self.path), [])

    def test_corruption_never_gets_overwritten(self):
        for content in ("not json", '{"memories": []}', '[1, "valid"]'):
            self.path.write_text(content, encoding="utf-8")
            with self.assertRaises(ValueError):
                save_memory("new memory", self.path)
            self.assertEqual(self.path.read_text(), content)

    def test_empty_input_rejected(self):
        for value in ("", "  ", None):
            with self.assertRaises(ValueError):
                save_memory(value, self.path)
            with self.assertRaises(ValueError):
                retrieve_memories(value, self.path)
        self.assertFalse(self.path.exists())

    def test_interrupted_replace_preserves_previous_data(self):
        save_memory("original", self.path)
        with patch("memory_store.os.replace", side_effect=OSError("simulated write failure")):
            with self.assertRaises(OSError):
                save_memory("new", self.path)
        self.assertEqual(load_memories(self.path), ["original"])
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])


class DemoCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cwd = Path(self.temp.name)

    def run_demo(self, folder, *args):
        return subprocess.run([sys.executable, str(ROOT / folder / "main.py"), *args],
                              cwd=self.cwd, text=True, capture_output=True, timeout=10)

    def test_memory_runs_from_an_unrelated_directory(self):
        store = self.cwd / "state" / "memories.json"
        result = self.run_demo("autonomous-memory-engine", "--add", "n8n workflows", "--query", "n8n",
                               "--store", str(store))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["retrieved_memories"], ["n8n workflows"])

    def test_orchestrator_labels_simulation(self):
        target = self.cwd / "out.json"
        result = self.run_demo("multi-agent-orchestrator", "Review a workflow", "--output", str(target))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["mode"], "simulation")
        self.assertTrue(all(task["status"] == "simulated" for task in data["tasks"]))
        self.assertEqual(json.loads(target.read_text()), data)

    def test_content_returns_editable_draft_without_reading_video(self):
        target = self.cwd / "draft.json"
        result = self.run_demo("content-pipeline-engine", "ESP32_workflow_demo.mp4", "--output", str(target))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["metadata"]["title"], "ESP32 workflow demo")
        self.assertTrue(data["seo"]["needs_editorial_review"])
        self.assertEqual(json.loads(target.read_text()), data)

    def test_invalid_arguments_fail_without_writing_output(self):
        for folder in ("content-pipeline-engine", "multi-agent-orchestrator"):
            target = self.cwd / "out.json"
            result = self.run_demo(folder, "   ", "--output", str(target))
            self.assertEqual(result.returncode, 2)
            self.assertFalse(target.exists())

    def test_repeated_orchestrations_do_not_accumulate_history(self):
        script = """
import sys
sys.path.insert(0, sys.argv[1])
from main import run_workflow
first = run_workflow('First', sys.argv[2])
second = run_workflow('Second', sys.argv[2])
assert len(second['memory']) == 1
assert second['memory'][0]['goal'] == 'Second'
from memory_system import get_memory
copy = get_memory()
copy[0]['goal'] = 'changed'
assert get_memory()[0]['goal'] == 'Second'
assert first['memory'][0]['goal'] == 'First'
"""
        result = subprocess.run([sys.executable, "-c", script, str(ROOT / "multi-agent-orchestrator"),
                                 str(self.cwd / "out.json")], cwd=self.cwd, text=True,
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
