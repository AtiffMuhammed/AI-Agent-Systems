"""A loopback-only personal web application. No external asset or script loads."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import sqlite3
import sys
from urllib.parse import parse_qs, urlsplit

from . import __version__, providers
from .engine import answer, markdown_report

ROOT = Path(__file__).resolve().parent
MAX_REQUEST = 2_100_000


def seed_sample(store):
    project = store.create_project('Sample · irrigation monitor')
    for path in sorted((ROOT/'sample').glob('*.md')):
        store.import_document(project['id'],path.name,path.read_text(encoding='utf-8'))
    return project


def make_server(store, port=8765):
    token = secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def log_message(self, *_):
            # Do not log user questions, filenames, or query strings.
            pass

        def send_body(self, data, status=200, content_type='application/json; charset=utf-8', attachment=None):
            if isinstance(data,(dict,list)):
                data = json.dumps(data,ensure_ascii=False).encode('utf-8')
            elif isinstance(data,str):
                data = data.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if attachment:
                self.send_header('Content-Disposition',f'attachment; filename="{attachment}"')
            self.end_headers()
            self.wfile.write(data)

        def guard(self, mutation=False):
            port = self.server.server_port
            host = self.headers.get('Host','')
            if host not in (f'127.0.0.1:{port}',f'localhost:{port}'):
                self.send_body({'error':'Untrusted host. Open the loopback URL printed by the server.'},403)
                return False
            origin = self.headers.get('Origin')
            if (origin and origin != 'http://' + host) or self.headers.get('Sec-Fetch-Site') == 'cross-site':
                self.send_body({'error':'Cross-origin access refused.'},403)
                return False
            if mutation and not secrets.compare_digest(self.headers.get('X-Agent-Token',''),token):
                self.send_body({'error':'Refresh this page to obtain a valid local session.'},403)
                return False
            return True

        def safe_dispatch(self, action):
            try:
                action()
            except KeyError:
                self.send_body({'error':'Requested project, source, report, or task was not found.'},404)
            except (ValueError,TypeError) as error:
                self.send_body({'error':str(error) if isinstance(error,ValueError) else 'Invalid request fields.'},400)
            except RecursionError:
                self.send_body({'error':'JSON nesting is too deep.'},400)
            except (BrokenPipeError,ConnectionResetError,TimeoutError):
                pass
            except sqlite3.Error:
                self.send_body({'error':'The local database could not complete this operation. Check available storage and the database file.'},500)
            except Exception as error:
                print(f'Local request failed: {type(error).__name__}',file=sys.stderr)
                self.send_body({'error':'The operation failed. Your saved data was not intentionally removed.'},500)

        def do_GET(self):
            self.safe_dispatch(self.get)

        def get(self):
            if not self.guard():
                return
            parsed = urlsplit(self.path)
            params = parse_qs(parsed.query)
            def param(name):
                return params.get(name,[''])[0]
            path = parsed.path
            if path in ('/','/app.js','/style.css'):
                file = {'/':'index.html','/app.js':'app.js','/style.css':'style.css'}[path]
                mime = {'/':'text/html','/app.js':'text/javascript','/style.css':'text/css'}[path]
                return self.send_body((ROOT/'static'/file).read_bytes(),content_type=mime+'; charset=utf-8')
            if path == '/api/session':
                return self.send_body({'token':token,'version':__version__,'providers':providers.config()})
            if path == '/api/state':
                project = param('project')
                return self.send_body({'projects':store.projects(),'documents':store.documents(project) if project else [],
                                       'tasks':store.tasks(project) if project else [],'runs':store.runs(project) if project else []})
            if path == '/api/document':
                return self.send_body(store.document(param('project'),param('id')))
            if path == '/api/run':
                return self.send_body(store.run(param('project'),param('id')))
            if path == '/api/export':
                run = store.run(param('project'),param('id'))
                if param('format') == 'json':
                    return self.send_body(run,attachment=f'report-{run["id"]}.json')
                return self.send_body(markdown_report(run),content_type='text/markdown; charset=utf-8',attachment=f'report-{run["id"]}.md')
            self.send_body({'error':'Not found.'},404)

        def do_POST(self):
            self.safe_dispatch(self.post)

        def post(self):
            if not self.guard(mutation=True):
                return
            if self.headers.get('Content-Type','').split(';')[0].strip() != 'application/json':
                return self.send_body({'error':'Expected application/json.'},415)
            try:
                length = int(self.headers.get('Content-Length','0'))
            except ValueError:
                return self.send_body({'error':'Invalid request length.'},400)
            if not 0 < length <= MAX_REQUEST:
                return self.send_body({'error':'Request exceeds the upload limit or has no body.'},413)
            data = json.loads(self.rfile.read(length).decode('utf-8'))
            if not isinstance(data,dict):
                raise ValueError('Expected a JSON object.')
            project = data.get('project','')
            path = urlsplit(self.path).path
            if path == '/api/projects':
                return self.send_body(store.create_project(data.get('name')),201)
            if path == '/api/sample':
                return self.send_body(seed_sample(store),201)
            if path == '/api/documents':
                return self.send_body(store.import_document(project,data.get('name'),data.get('content')),201)
            if path == '/api/delete-document':
                store.delete_document(project,data.get('id'))
            elif path == '/api/ask':
                provider = data.get('provider','evidence')
                if provider == 'openrouter' and data.get('allow_cloud') is not True:
                    raise ValueError('Confirm sending this question and selected source passages to OpenRouter.')
                return self.send_body(answer(store,project,data.get('question'),provider),201)
            elif path == '/api/tasks':
                return self.send_body(store.add_task(project,data.get('title')),201)
            elif path == '/api/task-status':
                store.update_task(project,data.get('id'),data.get('status'))
            elif path == '/api/delete-task':
                store.delete_task(project,data.get('id'))
            elif path == '/api/clear-runs':
                store.clear_runs(project)
            else:
                return self.send_body({'error':'Not found.'},404)
            self.send_body({'ok':True})

    return ThreadingHTTPServer(('127.0.0.1',port),Handler)
