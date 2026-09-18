"""One source-only transport of four pinned additions to the existing bootstrap."""

import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RELATIVE = HERE.relative_to(REPO)
BOOTSTRAP = '/localhome/local-rohing/orch_r170_creative_replay_20260917_attempt1/bootstrap'
APPROVAL_SHA = '870d9a17b5e95c2b69f654904b2a6630dcc327e80884282a3bdf505c00708a7a'
ASSEMBLY_SHA = '3e9da0d121cb53b76ad1411f9c6e942923892363cb5dcde591674c7ac881347e'
NAMES = ('ASSEMBLY_V2.py', 'SCAFFOLD_V2_OPERATOR.py', 'REVIEW_ASSEMBLY_V2.md',
         'APPROVED_RECEIVING_CPU.json')
REMOTE = r'''
import base64, hashlib, json, os, stat, subprocess, sys
from pathlib import Path
payload = json.load(sys.stdin)
root = Path('/localhome/local-rohing/orch_r170_creative_replay_20260917_attempt1/bootstrap')
relative = Path('research_loop/workers/r170_replay_boundary_20260917')
expected = {str(relative / name) for name in ('ASSEMBLY_V2.py', 'SCAFFOLD_V2_OPERATOR.py',
    'REVIEW_ASSEMBLY_V2.md', 'APPROVED_RECEIVING_CPU.json')}
assert root.resolve() == root and set(payload['files']) == expected
def verify(path, checksum):
    assert path.resolve() == path and stat.S_ISREG(path.lstat().st_mode)
    assert path.stat().st_size <= 2 * 1024 * 1024
    assert hashlib.sha256(path.read_bytes()).hexdigest() == checksum
for name, checksum in payload['existing'].items():
    assert not Path(name).is_absolute() and '..' not in Path(name).parts
    verify(root / name, checksum)
for name in expected:
    path = root / name
    assert path.parent.resolve() == path.parent and not path.exists() and not path.is_symlink()
for name, item in payload['files'].items():
    raw = base64.b64decode(item['base64'], validate=True)
    assert len(raw) <= 2 * 1024 * 1024 and hashlib.sha256(raw).hexdigest() == item['sha256']
    path = root / name
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    verify(path, item['sha256'])
approval = root / relative / 'APPROVED_RECEIVING_CPU.json'
command = ['/localhome/local-rohing/v2/venv/bin/python', '-B',
    str(root / relative / 'SCAFFOLD_V2_OPERATOR.py'), '--approval', str(approval),
    '--approval-sha256', payload['approval_sha256'], '--assembly-sha256', payload['assembly_sha256']]
environment = dict(PATH='/usr/bin:/bin', PYTHONPATH=str(root), CUDA_VISIBLE_DEVICES='',
    PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
result = subprocess.run(command, cwd=root, env=environment, stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=False)
print(json.dumps(dict(returncode=result.returncode, stdout=result.stdout.decode(),
    stderr=result.stderr.decode(), files={name:item['sha256'] for name,item in payload['files'].items()},
    wrapper_action='IMMUTABLE_SOURCE_SCAFFOLD_ONLY', retry_permitted=False), sort_keys=True))
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_once(name, value):
    with (HERE / name).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)


if __name__ == '__main__':
    assert sha(HERE / 'APPROVED_RECEIVING_CPU.json') == APPROVAL_SHA
    assert sha(HERE / 'ASSEMBLY_V2.py') == ASSEMBLY_SHA
    payload = dict(existing=json.loads((HERE / 'BOOTSTRAP_MANIFEST.json').read_bytes()),
        files={str(RELATIVE / name): dict(sha256=sha(HERE / name),
              base64=base64.b64encode((HERE / name).read_bytes()).decode()) for name in NAMES},
        approval_sha256=APPROVAL_SHA, assembly_sha256=ASSEMBLY_SHA)
    approval = json.loads((HERE / 'APPROVED_RECEIVING_CPU.json').read_bytes())
    assert payload['files'][str(RELATIVE / 'REVIEW_ASSEMBLY_V2.md')]['sha256'] == approval['independent_review_ref']['sha256']
    assert payload['files'][str(RELATIVE / 'SCAFFOLD_V2_OPERATOR.py')]['sha256'] == approval['scaffold_operator_sha256']
    write_once('SOURCE_STAGE_V2_STARTED.json', dict(started_utc=datetime.now(timezone.utc).isoformat(),
        files={name:item['sha256'] for name,item in payload['files'].items()},
        approval_sha256=APPROVAL_SHA, retry_permitted=False, learner_signals_authorized=False))
    command = ['bash', str(REPO / 'gpu/ovx2_ssh.sh'),
        'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 '
        '/localhome/local-rohing/v2/venv/bin/python -I -B -c ' + shlex.quote(REMOTE)]
    result = subprocess.run(command, input=json.dumps(payload).encode(), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=150, check=False)
    with (HERE / 'SOURCE_STAGE_V2_STDOUT.txt').open('xb') as stream:
        stream.write(result.stdout)
    with (HERE / 'SOURCE_STAGE_V2_STDERR.txt').open('xb') as stream:
        stream.write(result.stderr)
    write_once('SOURCE_STAGE_V2_WRAPPER.json', dict(returncode=result.returncode,
        ended_utc=datetime.now(timezone.utc).isoformat(), retry_permitted=False))
    if result.returncode:
        raise SystemExit(result.returncode)
    receipt = json.loads(result.stdout)
    write_once('SOURCE_STAGE_V2_RESULT.json', receipt)
    if receipt['returncode']:
        print(json.dumps(receipt, indent=2))
        raise SystemExit(receipt['returncode'])
    projection = json.loads(receipt['stdout'])
    write_once('SOURCE_STAGE_V2_RECEIPT.json', projection)
    print(json.dumps(projection, indent=2))
