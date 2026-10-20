"""Small reproducible retrieval checks, not a general accuracy benchmark."""
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agent_workspace.engine import answer
from agent_workspace.server import seed_sample
from agent_workspace.store import Store

CASES = [
    ('firmware samples soil moisture','30 seconds'),
    ('hardware budget','1,250 INR'),
    ('MQTT TLS connection','TLS'),
    ('relay disconnected sensor','relay'),
    ('calibrate soil moisture','Calibrate'),
    ('battery current runtime','unknown'),
    ('quantum zebras',''),
]


def main():
    with tempfile.TemporaryDirectory() as directory:
        store = Store(Path(directory)/'eval.db')
        project = seed_sample(store)['id']
        results = []
        for question,expected in CASES:
            run = answer(store,project,question)['result']
            found = any(expected.casefold() in source['body'].casefold() for source in run['sources']) if expected else not run['sources']
            results.append({'question':question,'passed':found,'source_count':len(run['sources'])})
        report = {'suite':'Bundled sample retrieval checks','cases':results,'passed':sum(item['passed'] for item in results),'total':len(results),
                  'limits':'Tiny authored dataset; checks retrieved passages, not model answer accuracy. No live model call.'}
        print(json.dumps(report,indent=2))
        return 0 if all(item['passed'] for item in results) else 1


if __name__ == '__main__':
    sys.exit(main())
