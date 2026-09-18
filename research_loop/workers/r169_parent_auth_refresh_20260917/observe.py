"""Read-only parent health and bounded TRAIN-render metadata, without secrets."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def observe(home):
    binding = json.loads((home/'BINDING.json').read_text())
    config = json.loads(Path(binding['config']).read_text())
    row = dict(branch=binding['branch'], original_pid=binding['original']['pid'],
        reserved_cursor=binding['cursor'], started=False, alive=None, counts={}, attempts=[])
    started_path = home/'parent/STARTED.json'
    if not started_path.exists():
        return row
    started = json.loads(started_path.read_text())
    row.update(started=True, pid=started['pid'], started_unix=started['started_unix'])
    try:
        process = Path('/proc')/str(started['pid'])
        state = (process/'stat').read_text().rsplit(')', 1)[1].split()[0]
        argv = (process/'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
        row['alive'] = state not in ('Z', 'X') and str(home/'BINDING.json') in argv
        environment = dict(value.split(b'=',1) for value in (process/'environ').read_bytes().split(b'\0') if b'=' in value)
        row['credential_matches_current_environment'] = bool(os.environ.get('NVIDIA_API_KEY')) and environment.get(b'NVIDIA_API_KEY') == os.environ['NVIDIA_API_KEY'].encode()
    except OSError as error:
        row['health_read_error'] = dict(error_type=type(error).__name__, errno=error.errno)
    directories = sorted((home/'parent').glob('parent_*'))
    row['dispatches'] = sum((directory/'DISPATCH.json').exists() for directory in directories)
    for directory in directories:
        path = directory/'RESULT.json'
        if not path.exists():
            continue
        result = json.loads(path.read_text())
        status = result['status']
        row['counts'][status] = row['counts'].get(status, 0)+1
        item = dict(attempt=directory.name, status=status, finished_unix=result['finished_unix'],
                    model=result.get('actual_model'), error_type=result.get('error_type'))
        row['attempts'].append(item)
        if status != 'PUBLISHED' or sum('render' in earlier for earlier in row['attempts']) >= 2:
            continue
        source = json.loads((directory/'SOURCE.json').read_text())
        publication = result['inbox_publication']
        request = dict(root=config['root'], source_root=config['source_root'], inbox_id=publication['id'],
            publication_sha256=publication['sha256'], start_index=source['record_count']-1,
            start_record_sha256=source['head_sha256'])
        probe = REPO/'research_loop/workers/r167_legacy_parent_rollout/render_probe.py'
        remote = subprocess.run(['bash', str(REPO/'gpu'/(config['node']+'_ssh.sh')),
            'python3 - '+shlex.quote(json.dumps(request))], input=probe.read_bytes(),
            capture_output=True, timeout=45)
        if remote.returncode == 0:
            item['render'] = json.loads(remote.stdout)
        else:
            item['render'] = dict(status='READ_ONLY_RENDER_CHECK_FAILED', returncode=remote.returncode,
                stderr_sha256=hashlib.sha256(remote.stderr).hexdigest())
    return row


if __name__ == '__main__':
    homes = [home for home in HERE.glob('parent_*') if (home/'BINDING.json').exists()]
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(observe, homes))
    receipt = HERE/('OBSERVATION_'+str(time.time_ns())+'.json')
    with receipt.open('x') as output:
        json.dump(dict(observed_unix=time.time(), rows=rows, no_scientific_claim=True), output, indent=2)
    print(json.dumps(dict(receipt=str(receipt), parents=len(rows), alive=sum(row['alive'] is True for row in rows),
        health_unknown=sum(row['alive'] is None for row in rows),
        current_credential=sum(row.get('credential_matches_current_environment',False) for row in rows),
        dispatches=sum(row.get('dispatches',0) for row in rows),
        published=sum(row['counts'].get('PUBLISHED',0) for row in rows),
        missing=sum(row['counts'].get('MISSING',0) for row in rows),
        rendered=sum(item.get('render',{}).get('status')=='RENDERED_TEXT_VERIFIED' for row in rows for item in row['attempts']))))
