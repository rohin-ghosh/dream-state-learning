"""Read-only V3 companion receipts without changing existing pinned observers."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time


END = 1789491360
REPO = Path(__file__).resolve().parents[1]
OUTPUT = REPO/'research_notes/analysis/orch_r109_l1_20260915'
NATIVE = '/localhome/local-rohing/orch_r109_l1_20260915'
COMMAND = ('env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 '
    f'PYTHONPATH={NATIVE}/source:{NATIVE}/generation_v3/source '
    '/localhome/local-rohing/v2/venv/bin/python -B '
    f'{NATIVE}/generation_v3/source/orch_r109_l1_generation_v3.py observe')


def snapshot():
    now = time.time()
    result = dict(observed_unix=now,hard_deadline_unix=END,raw_output=False,nodes={},errors=[])
    for node,wrapper in (('node1','gpu/a40r_ssh.sh'),('node2','gpu/ovx_ssh.sh')):
        try:
            process = subprocess.run(['bash',wrapper,COMMAND],cwd=REPO,capture_output=True,text=True,timeout=45,check=True)
            report = json.loads(process.stdout)
            assert report['node'] == node and report['raw_output'] is False and report['hard_deadline_unix'] == END
            result['nodes'][node] = report
            for lane in report['lanes']:
                if lane.get('failure') or ('launch' in lane and not lane.get('alive') and 'exit' not in lane):
                    result['errors'].append(dict(node=node,index=lane['index'],error='native_failure_or_unexpected_absence'))
        except Exception as failure:
            result['errors'].append(dict(node=node,error_type=type(failure).__name__))
    return result


def watch():
    source = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    while time.time() <= END:
        assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == source
        report = snapshot()
        label = datetime.fromtimestamp(report['observed_unix'],timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        with (OUTPUT/f'GENERATION_V3_WATCH_{label}.json').open('x') as stream:
            json.dump(dict(report,watcher_source_sha256=source),stream,indent=2)
        print(json.dumps(dict(observed_unix=report['observed_unix'],errors=report['errors'],receipt=label)),flush=True)
        remaining = END-time.time()
        if remaining <= 0:break
        time.sleep(min(300,remaining))


if __name__ == '__main__':watch()
