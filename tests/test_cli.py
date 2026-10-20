import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CliTests(unittest.TestCase):
    def test_sample_import_and_question_work_in_separate_processes(self):
        with tempfile.TemporaryDirectory() as directory:
            db = str(Path(directory)/'memory.db')
            def run(*args):
                return subprocess.run([sys.executable,'-m','agent_workspace','--db',db,*args],text=True,capture_output=True,timeout=15)
            sample = run('sample')
            self.assertEqual(sample.returncode,0,sample.stderr)
            project = json.loads(sample.stdout)['id']
            answer = run('ask',project,'soil moisture samples','--markdown')
            self.assertEqual(answer.returncode,0,answer.stderr)
            self.assertIn('30 seconds',answer.stdout)
            root = Path(directory)/'input';root.mkdir()
            (root/'notes.md').write_text('battery current is unknown',encoding='utf-8')
            (root/'.env').write_text('must-not-import')
            (root/'credentials.json').write_text('must-not-import')
            (root/'link.md').symlink_to(root/'notes.md')
            imported = run('import',project,str(root))
            self.assertEqual(imported.returncode,0,imported.stderr)
            payload = json.loads(imported.stdout)
            self.assertEqual([doc['name'] for doc in payload['imported']],['notes.md'])
            self.assertEqual([doc['name'] for doc in payload['skipped']],['credentials.json'])
            self.assertEqual(run('ask',project,'battery','--provider','openrouter').returncode,2)

    def test_bad_path_and_blank_project_report_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable,'-m','agent_workspace','--db',str(Path(directory)/'memory.db')]
            result = subprocess.run([*command,'create','   '],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,2)
