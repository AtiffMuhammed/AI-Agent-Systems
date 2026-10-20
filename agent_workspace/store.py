"""Transactional project memory and durable run/task records, with FTS5 search."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import unicodedata
import uuid

MAX_BYTES = 1_000_000
SUFFIXES = {'.md', '.txt', '.py', '.js', '.ts', '.tsx', '.jsx', '.json', '.csv', '.yaml', '.yml', '.ino', '.rst', '.html', '.css'}
STOP = set('a an and are as at be by can do does for from how i in is it me my of on or our should that the their this to was we what when where which who why will with you your'.split())


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def identifier():
    return uuid.uuid4().hex


def clean_text(value, label, maximum=8000):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} must be non-empty text.')
    if len(value) > maximum or '\x00' in value:
        raise ValueError(f'{label} is too long or contains a NUL character.')
    return value.strip()


def terms(text):
    return list(dict.fromkeys(t for t in re.findall(r'\w+', unicodedata.normalize('NFKC', text).casefold()) if t not in STOP))[:32]


def chunks(text, lines=28, overlap=4):
    """Preserve exact source lines; split unusually long lines to bound context."""
    rows = text.splitlines()
    start = 0
    while start < len(rows):
        end = min(start + lines, len(rows))
        # A single source line is kept intact; import rejects excessive lines.
        while end > start + 1 and len('\n'.join(rows[start:end])) > 6000:
            end -= 1
        body = '\n'.join(rows[start:end])
        if body.strip():
            yield start + 1, end, body
        if end == len(rows):
            break
        start = max(start + 1, end - overlap)


class Store:
    def __init__(self, path):
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''
              CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, name TEXT NOT NULL, created TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                name TEXT NOT NULL, content TEXT NOT NULL, digest TEXT NOT NULL, updated TEXT NOT NULL, UNIQUE(project_id,name));
              CREATE TABLE IF NOT EXISTS chunks(id INTEGER PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                start_line INTEGER NOT NULL, end_line INTEGER NOT NULL, body TEXT NOT NULL);
              CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(body, tokenize='unicode61');
              CREATE TRIGGER IF NOT EXISTS chunk_delete AFTER DELETE ON chunks BEGIN DELETE FROM search_index WHERE rowid=old.id; END;
              CREATE TRIGGER IF NOT EXISTS chunk_insert AFTER INSERT ON chunks BEGIN INSERT INTO search_index(rowid,body) VALUES(new.id,new.body); END;
              CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                created TEXT NOT NULL, question TEXT NOT NULL, result TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                title TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('todo','doing','done')), created TEXT NOT NULL, updated TEXT NOT NULL);
              PRAGMA user_version=1;
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def require_project(db, project):
        if not db.execute('SELECT 1 FROM projects WHERE id=?', (project,)).fetchone():
            raise KeyError('Project not found.')

    def projects(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM projects ORDER BY created,id')]

    def create_project(self, name):
        item = {'id': identifier(), 'name': clean_text(name, 'Project name', 80), 'created': now()}
        with self.connect() as db:
            db.execute('INSERT INTO projects VALUES(:id,:name,:created)', item)
        return item

    def import_document(self, project, name, content):
        name = clean_text(name, 'Filename', 240).replace('\\', '/')
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or any(p.startswith('.') for p in path.parts):
            raise ValueError('Use a relative, non-hidden document path.')
        if path.suffix.lower() not in SUFFIXES or re.search(r'(^|[_.-])(secret|credentials?|private|token|password)([_.-]|$)', name, re.I):
            raise ValueError('Unsupported file type or sensitive filename.')
        if not isinstance(content, str) or not content.strip() or '\x00' in content:
            raise ValueError('Document must contain readable text.')
        if len(content.encode('utf-8')) > MAX_BYTES or any(len(line) > 6000 for line in content.splitlines()):
            raise ValueError('Document exceeds 1 MB or a line exceeds 6,000 characters. Split it into smaller text files.')
        digest = hashlib.sha256(content.encode('utf-8')).hexdigest()
        with self.connect() as db:
            self.require_project(db, project)
            existing = db.execute('SELECT id,digest FROM documents WHERE project_id=? AND name=?', (project,name)).fetchone()
            if existing and existing['digest'] == digest:
                return {'id': existing['id'], 'name': name, 'changed': False}
            doc = existing['id'] if existing else identifier()
            if existing:
                db.execute('DELETE FROM chunks WHERE document_id=?', (doc,))
                db.execute('UPDATE documents SET content=?,digest=?,updated=? WHERE id=?', (content,digest,now(),doc))
            else:
                db.execute('INSERT INTO documents VALUES(?,?,?,?,?,?)', (doc,project,name,content,digest,now()))
            db.executemany('INSERT INTO chunks(document_id,start_line,end_line,body) VALUES(?,?,?,?)',
                           ((doc,a,b,text) for a,b,text in chunks(content)))
            return {'id': doc, 'name': name, 'changed': True}

    def documents(self, project):
        with self.connect() as db:
            self.require_project(db, project)
            return [dict(r) for r in db.execute('SELECT id,name,digest,updated,length(content) AS characters FROM documents WHERE project_id=? ORDER BY name', (project,))]

    def document(self, project, doc):
        with self.connect() as db:
            row = db.execute('SELECT * FROM documents WHERE project_id=? AND id=?', (project,doc)).fetchone()
            if row is None:
                raise KeyError('Document not found.')
            return dict(row)

    def delete_document(self, project, doc):
        with self.connect() as db:
            if not db.execute('DELETE FROM documents WHERE project_id=? AND id=?', (project,doc)).rowcount:
                raise KeyError('Document not found.')

    def search(self, project, query, limit=6):
        query = clean_text(query, 'Question', 2000)
        tokens = terms(query)
        with self.connect() as db:
            self.require_project(db, project)
            if not tokens:
                return []
            # Quote each token: user input is never an FTS query language fragment.
            match = ' OR '.join('"' + t.replace('"','""') + '"' for t in tokens)
            rows = db.execute('''SELECT c.id AS chunk_id,c.document_id,c.start_line,c.end_line,c.body,
                      d.name,d.digest,bm25(search_index) AS rank
                      FROM search_index JOIN chunks c ON c.id=search_index.rowid JOIN documents d ON d.id=c.document_id
                      WHERE search_index MATCH ? AND d.project_id=? ORDER BY rank,c.id LIMIT ?''', (match,project,limit*4)).fetchall()
            selected = []
            for row in rows:
                item = dict(row)
                if any(s['document_id'] == item['document_id'] and not (item['end_line'] < s['start_line'] or item['start_line'] > s['end_line']) for s in selected):
                    continue
                item['source_id'] = 'S' + str(len(selected) + 1)
                selected.append(item)
                if len(selected) >= limit:
                    break
            return selected

    def save_run(self, project, result):
        run = {'id': identifier(), 'project_id': project, 'created': now(), 'question': result['question'], 'result': result}
        with self.connect() as db:
            self.require_project(db, project)
            db.execute('INSERT INTO runs VALUES(?,?,?,?,?)', (run['id'],project,run['created'],run['question'],json.dumps(result,ensure_ascii=False)))
        return run

    def runs(self, project):
        with self.connect() as db:
            self.require_project(db, project)
            return [dict(r) for r in db.execute('SELECT id,created,question FROM runs WHERE project_id=? ORDER BY created DESC,rowid DESC LIMIT 100', (project,))]

    def run(self, project, run):
        with self.connect() as db:
            row = db.execute('SELECT * FROM runs WHERE project_id=? AND id=?', (project,run)).fetchone()
            if not row:
                raise KeyError('Report not found.')
            result = dict(row)
            result['result'] = json.loads(result['result'])
            return result

    def clear_runs(self, project):
        with self.connect() as db:
            self.require_project(db, project)
            db.execute('DELETE FROM runs WHERE project_id=?', (project,))

    def tasks(self, project):
        with self.connect() as db:
            self.require_project(db, project)
            return [dict(r) for r in db.execute('SELECT * FROM tasks WHERE project_id=? ORDER BY created,rowid', (project,))]

    def add_task(self, project, title):
        item = {'id': identifier(), 'project_id': project, 'title': clean_text(title,'Task',300), 'status':'todo', 'created': now(), 'updated': now()}
        with self.connect() as db:
            self.require_project(db, project)
            db.execute('INSERT INTO tasks VALUES(:id,:project_id,:title,:status,:created,:updated)', item)
        return item

    def update_task(self, project, task, status):
        if status not in ('todo','doing','done'):
            raise ValueError('Unknown task status.')
        with self.connect() as db:
            if not db.execute('UPDATE tasks SET status=?,updated=? WHERE id=? AND project_id=?', (status,now(),task,project)).rowcount:
                raise KeyError('Task not found.')

    def delete_task(self, project, task):
        with self.connect() as db:
            if not db.execute('DELETE FROM tasks WHERE id=? AND project_id=?', (task,project)).rowcount:
                raise KeyError('Task not found.')
