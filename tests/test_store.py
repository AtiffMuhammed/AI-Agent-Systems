import concurrent.futures
from pathlib import Path
import tempfile
import unittest

from agent_workspace.store import Store


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'memory.sqlite3'
        self.store = Store(self.path)
        self.project = self.store.create_project('Monitor')['id']

    def test_persistence_reindex_and_delete_remove_old_search_entries(self):
        doc = self.store.import_document(self.project, 'notes.md', 'Battery voltage is 3.3V.')
        self.assertTrue(doc['changed'])
        self.assertFalse(self.store.import_document(self.project, 'notes.md', 'Battery voltage is 3.3V.')['changed'])
        self.assertEqual(len(Store(self.path).search(self.project, 'battery')), 1)
        self.store.import_document(self.project, 'notes.md', 'Solar sensor reads temperature.')
        self.assertEqual(self.store.search(self.project, 'battery'), [])
        self.assertEqual(self.store.search(self.project, 'temperature')[0]['source_id'], 'S1')
        self.store.delete_document(self.project, doc['id'])
        self.assertEqual(self.store.search(self.project, 'temperature'), [])

    def test_projects_cannot_read_each_others_documents_runs_or_tasks(self):
        other = self.store.create_project('Other')['id']
        doc = self.store.import_document(self.project, 'design.md', 'Exclusive battery design')
        task = self.store.add_task(self.project, 'Measure the battery')
        report = self.store.save_run(self.project, {'question':'battery', 'sources':[]})
        self.assertEqual(self.store.search(other, 'battery'), [])
        for operation in (lambda: self.store.document(other,doc['id']),
                          lambda: self.store.run(other,report['id']),
                          lambda: self.store.update_task(other,task['id'],'done')):
            with self.assertRaises(KeyError):
                operation()

    def test_fts_punctuation_is_data_and_does_not_break_search(self):
        self.store.import_document(self.project, 'notes.md', 'ESP32 café test')
        self.assertTrue(self.store.search(self.project, '"ESP32" OR * NEAR(café)'))
        self.assertEqual(self.store.search(self.project, '?!'), [])

    def test_bad_import_preserves_current_content(self):
        doc = self.store.import_document(self.project, 'notes.md', 'Original evidence')
        for name,content in (('../outside.md','bad'),('.env','key'),('credentials.json','secret'),('notes.md','\x00bad'),('notes.md','a'*6001)):
            with self.assertRaises(ValueError):
                self.store.import_document(self.project,name,content)
        self.assertEqual(self.store.document(self.project,doc['id'])['content'], 'Original evidence')

    def test_line_numbers_reconstruct_exact_evidence_and_overlaps_are_deduplicated(self):
        text = '\n'.join(f'Line {n}: battery measurement.' for n in range(1, 100))
        self.store.import_document(self.project,'notes.md',text)
        hits = self.store.search(self.project,'battery')
        self.assertGreater(len(hits),1)
        for hit in hits:
            self.assertEqual(hit['body'], '\n'.join(text.splitlines()[hit['start_line']-1:hit['end_line']]))
        for left,right in zip(sorted(hits,key=lambda h:h['start_line']),sorted(hits,key=lambda h:h['start_line'])[1:]):
            self.assertLess(left['end_line'],right['start_line'])

    def test_concurrent_task_writes_and_status_changes(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(lambda i:self.store.add_task(self.project,f'Task {i}'),range(20)))
        tasks = self.store.tasks(self.project)
        self.assertEqual(len(tasks),20)
        self.store.update_task(self.project,tasks[0]['id'],'done')
        self.assertEqual(self.store.tasks(self.project)[0]['status'],'done')
        with self.assertRaises(ValueError):
            self.store.update_task(self.project,tasks[0]['id'],'pretend-complete')

    def test_run_snapshot_survives_source_changes_and_history_can_be_cleared(self):
        doc = self.store.import_document(self.project,'notes.md','Battery uses lithium.')
        hits = self.store.search(self.project,'battery')
        report = self.store.save_run(self.project,{'question':'battery','sources':hits})
        self.store.delete_document(self.project,doc['id'])
        self.assertEqual(self.store.run(self.project,report['id'])['result']['sources'][0]['body'],'Battery uses lithium.')
        self.store.clear_runs(self.project)
        self.assertEqual(self.store.runs(self.project),[])
