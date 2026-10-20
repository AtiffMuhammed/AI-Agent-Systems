from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import unittest

from agent_workspace.providers import post_json, ProviderError


class ProviderTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.requests = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):
                pass
            def do_POST(self):
                content = self.rfile.read(int(self.headers.get('Content-Length','0')))
                cls.requests.append((self.path,json.loads(content)))
                if self.path == '/redirect':
                    self.send_response(302);self.send_header('Location','/unexpected');self.end_headers();return
                if self.path == '/error':
                    self.send_response(429);self.end_headers();self.wfile.write(b'PRIVATE PROVIDER ERROR DATA');return
                self.send_response(200);self.end_headers()
                if self.path == '/bad':
                    self.wfile.write(b'not-json')
                elif self.path == '/big':
                    self.wfile.write(b'x'*1_000_001)
                else:
                    self.wfile.write(json.dumps({'message':{'content':'{"claims": []}'}}).encode())
        cls.server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(3)

    def test_http_json_roundtrip_with_non_ascii_source_text(self):
        result = post_json(self.url+'/chat',{'question':'café · ESP32'}, {})
        self.assertEqual(result['message']['content'],'{"claims": []}')
        self.assertEqual(self.requests[-1][1]['question'],'café · ESP32')

    def test_redirect_does_not_forward_request_to_another_destination(self):
        before = len(self.requests)
        with self.assertRaises(ProviderError):
            post_json(self.url+'/redirect',{'evidence':'data'}, {'Authorization':'Bearer test-only-key'})
        self.assertEqual([path for path,_ in self.requests[before:]],['/redirect'])

    def test_bad_oversized_and_http_error_bodies_are_not_returned(self):
        for path in ('/bad','/big','/error'):
            with self.subTest(path=path),self.assertRaises(ProviderError) as raised:
                post_json(self.url+path,{}, {})
            self.assertNotIn('PRIVATE',str(raised.exception))
