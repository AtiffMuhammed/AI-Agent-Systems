import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

from agent_workspace.server import make_server
from agent_workspace.store import Store


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.store = Store(Path(cls.tmp.name)/'workspace.db')
        cls.server = make_server(cls.store,0)
        cls.thread = threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.url = 'http://127.0.0.1:' + str(cls.server.server_port)
        _,cls.session,_ = cls.request('/api/session')

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        cls.tmp.cleanup()

    @classmethod
    def request(cls,path,body=None,headers=None,raw=False):
        request_headers = {}
        data = None
        if body is not None:
            data = json.dumps(body).encode('utf-8') if not raw else body
            request_headers = {'Content-Type':'application/json','X-Agent-Token':getattr(cls,'session',{}).get('token','')}
        request_headers.update(headers or {})
        request = urllib.request.Request(cls.url+path,data=data,headers=request_headers)
        try:
            response = urllib.request.urlopen(request,timeout=10)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            payload = response.read()
            return response.status, json.loads(payload) if response.headers['Content-Type'].startswith('application/json') else payload,dict(response.headers)

    def project(self):
        status,data,_ = self.request('/api/projects',{'name':'HTTP test'})
        self.assertEqual(status,201)
        return data['id']

    def test_complete_user_workflow_import_ask_export_task_and_history(self):
        project = self.project()
        status,doc,_ = self.request('/api/documents',{'project':project,'name':'notes.md','content':'The sensor samples every 30 seconds.'})
        self.assertEqual(status,201)
        status,run,_ = self.request('/api/ask',{'project':project,'question':'sensor samples'})
        self.assertEqual(status,201)
        self.assertIn('30 seconds',run['result']['claims'][0]['text'])
        query = f'?project={project}&id={run["id"]}'
        status,export,headers = self.request('/api/export'+query)
        self.assertEqual(status,200)
        self.assertIn(b'notes.md',export)
        self.assertIn('attachment;',headers['Content-Disposition'])
        status,export,_ = self.request('/api/export'+query+'&format=json')
        self.assertEqual(export['id'],run['id'])
        _,task,_ = self.request('/api/tasks',{'project':project,'title':'Calibrate sensor'})
        status,_,_ = self.request('/api/task-status',{'project':project,'id':task['id'],'status':'doing'})
        self.assertEqual(status,200)
        _,state,_ = self.request('/api/state?project='+project)
        self.assertEqual(state['tasks'][0]['status'],'doing')
        self.assertEqual(len(state['runs']),1)
        self.request('/api/delete-document',{'project':project,'id':doc['id']})
        self.assertEqual(self.request('/api/run'+query)[1]['result']['sources'][0]['body'],'The sensor samples every 30 seconds.')
        self.request('/api/clear-runs',{'project':project})
        self.assertEqual(self.request('/api/run'+query)[0],404)

    def test_rebinding_cross_site_and_invalid_session_are_rejected(self):
        self.assertEqual(self.request('/api/session',headers={'Host':'attacker.example'})[0],403)
        self.assertEqual(self.request('/api/session',headers={'Origin':'https://attacker.example'})[0],403)
        self.assertEqual(self.request('/api/projects',{'name':'blocked'},headers={'X-Agent-Token':'wrong'})[0],403)
        self.assertEqual(self.request('/api/projects',{'name':'blocked'},headers={'Sec-Fetch-Site':'cross-site'})[0],403)

    def test_invalid_json_fields_and_oversized_requests_are_reported(self):
        self.assertEqual(self.request('/api/projects',b'not json',raw=True)[0],400)
        self.assertEqual(self.request('/api/projects',{'name':[]})[0],400)
        self.assertEqual(self.request('/api/projects',b'[]',raw=True)[0],400)
        self.assertEqual(self.request('/api/projects',{'name':'x'},headers={'Content-Type':'text/plain'})[0],415)
        # Reject from declared length without racing a client still writing 2 MB.
        self.assertEqual(self.request('/api/projects',b'{}',headers={'Content-Length':'2100001'},raw=True)[0],413)

    def test_cloud_synthesis_requires_per_request_consent(self):
        project = self.project()
        status,data,_ = self.request('/api/ask',{'project':project,'question':'sensor','provider':'openrouter'})
        self.assertEqual(status,400)
        self.assertIn('Confirm',data['error'])

    def test_static_assets_and_missing_paths_are_safe(self):
        for path in ('/','/app.js','/style.css'):
            status,body,headers = self.request(path)
            self.assertEqual(status,200)
            self.assertTrue(body)
            self.assertIn("script-src 'self'",headers['Content-Security-Policy'])
            self.assertNotIn('Access-Control-Allow-Origin',headers)
        self.assertEqual(self.request('/../store.py')[0],404)
        self.assertEqual(self.request('/api/document?project=missing&id=missing')[0],404)

    def test_sample_is_real_indexed_data_not_canned_answers(self):
        status,project,_ = self.request('/api/sample',{})
        self.assertEqual(status,201)
        _,state,_ = self.request('/api/state?project='+project['id'])
        self.assertEqual(len(state['documents']),3)
        _,run,_ = self.request('/api/ask',{'project':project['id'],'question':'firmware samples soil moisture'})
        self.assertIn('30 seconds',run['result']['claims'][0]['text'])
