import argparse
import json
import os
from pathlib import Path
import sqlite3

from .engine import answer, markdown_report
from .server import make_server, seed_sample
from .store import Store, SUFFIXES


def main(argv=None):
    parser = argparse.ArgumentParser(description='AI Agent Systems · local project memory and cited answers')
    parser.add_argument('--db',default=os.environ.get('AGENT_WORKSPACE_DB',str(Path.home()/'.agent-workspace'/'workspace.sqlite3')),
                        help='Local SQLite file (default: ~/.agent-workspace/workspace.sqlite3)')
    commands = parser.add_subparsers(dest='command',required=True)
    serve = commands.add_parser('serve',help='Start the loopback web application')
    serve.add_argument('--port',type=int,default=8765)
    commands.add_parser('sample',help='Create a sample project using bundled fictional notes')
    commands.add_parser('projects',help='List local projects')
    create = commands.add_parser('create',help='Create a project')
    create.add_argument('name')
    ingest = commands.add_parser('import',help='Import one file or supported files in a directory')
    ingest.add_argument('project')
    ingest.add_argument('path',type=Path)
    ask = commands.add_parser('ask',help='Ask a standalone question about a project')
    ask.add_argument('project')
    ask.add_argument('question')
    ask.add_argument('--provider',choices=('evidence','ollama','openrouter'),default='evidence')
    ask.add_argument('--allow-cloud',action='store_true',help='Allow sending selected sources to OpenRouter for this run')
    ask.add_argument('--markdown',action='store_true')
    args = parser.parse_args(argv)
    try:
        store = Store(args.db)
        if args.command == 'serve':
            if not 1 <= args.port <= 65535:
                raise ValueError('Port must be between 1 and 65535.')
            if not store.projects():
                store.create_project('My project')
            server = make_server(store,args.port)
            print(f'AI Agent Systems: http://127.0.0.1:{server.server_port}',flush=True)
            print(f'Data: {store.path}\nLocal personal use only. Press Ctrl+C to stop.',flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
            return
        if args.command == 'sample':
            result = seed_sample(store)
        elif args.command == 'projects':
            result = store.projects()
        elif args.command == 'create':
            result = store.create_project(args.name)
        elif args.command == 'ask':
            if args.provider == 'openrouter' and not args.allow_cloud:
                raise ValueError('Use --allow-cloud to send selected evidence to OpenRouter for this request.')
            result = answer(store,args.project,args.question,args.provider)
            if args.markdown:
                print(markdown_report(result))
                return
        else:
            root = args.path.expanduser().resolve()
            if not root.exists():
                raise ValueError('Import path does not exist.')
            if args.path.is_symlink():
                raise ValueError('Symlink imports are not supported.')
            files = [root] if root.is_file() else []
            if root.is_dir():
                for parent,folders,names in os.walk(root,followlinks=False):
                    folders[:] = [name for name in folders if not name.startswith('.') and name not in ('node_modules','venv','__pycache__','dist','build') and not (Path(parent)/name).is_symlink()]
                    files.extend(Path(parent)/name for name in sorted(names) if not name.startswith('.') and Path(name).suffix.lower() in SUFFIXES and not (Path(parent)/name).is_symlink())
                    if len(files)>250:
                        raise ValueError('Import at most 250 files at once. Choose a smaller folder.')
            if not files:
                raise ValueError('No supported text files found.')
            result = {'imported':[], 'skipped':[]}
            for file in sorted(files):
                name = file.name if root.is_file() else file.relative_to(root).as_posix()
                try:
                    if file.stat().st_size > 1_000_000:
                        raise ValueError('File exceeds 1 MB.')
                    result['imported'].append(store.import_document(args.project,name,file.read_text(encoding='utf-8')))
                except (ValueError,UnicodeError) as error:
                    result['skipped'].append({'name':name,'reason':str(error)})
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,KeyError,OSError,sqlite3.Error) as error:
        parser.exit(2,f'Error: {error}\n')


if __name__ == '__main__':
    main()
