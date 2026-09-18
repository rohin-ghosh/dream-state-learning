"""One bounded operational snapshot, without reading evaluator contents or state payloads."""

import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
REMOTE = r'''
import hashlib, json, os, re, stat, time
from pathlib import Path
root = Path('/localhome/local-rohing/orch_r133_creative_reread_20260916_attempt1/run1')
guard = Path('/localhome/local-rohing/orch_r144_node3_target_physical1_20260916t1545z_5/GUARD.json')
pid = 1266769
ticks = '28048014'
budget = 20 * 1024 * 1024
consumed = 0
def bounded(path, limit):
    global consumed
    size = path.lstat().st_size
    assert path.is_absolute() and path.resolve() == path and stat.S_ISREG(path.lstat().st_mode)
    assert 0 <= size <= limit and consumed + size <= budget
    consumed += size
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        raw = stream.read(size)
        after = os.fstat(stream.fileno())
    assert len(raw) == size and all(getattr(before, name) == getattr(after, name)
        for name in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))
    return raw
def process():
    path = Path('/proc') / str(pid) / 'stat'
    try:
        fields = path.read_text().rsplit(') ', 1)[1].split()
        return dict(pid=pid, start_ticks=fields[19], state=fields[0], exact=fields[19] == ticks)
    except FileNotFoundError:
        return dict(pid=pid, exact=False, status='NOT_PRESENT')
before = process()
raw = bounded(guard, 1024 * 1024)
assert hashlib.sha256(raw).hexdigest() == '8bbb6c007083884574b427b318ef3e466f26e514452b5ee5e7972801aca8ce9d'
config = json.loads(raw)
plan_raw = bounded(Path(config['plan_path']), 1024 * 1024)
assert hashlib.sha256(plan_raw).hexdigest() == config['plan_sha256']
plan = json.loads(plan_raw)
records = sorted(path for path in (root / 'stream/records').iterdir()
                 if re.fullmatch(r'\d{20}\.json', path.name))
assert records and len(records) <= 1000000
head = records[-1]
head_raw = bounded(head, 16 * 1024 * 1024)
record = json.loads(head_raw)
checkpoint_names = sorted(path.name for path in (root / 'checkpoints').iterdir()
                          if re.fullmatch(r'sleep_\d{6}', path.name) and (path / 'COMMIT.json').is_file())
after = process()
result = dict(schema='R170_TARGET_OPERATIONAL_OBSERVATION_V1', observed_unix=time.time(),
    process_before=before, process_after=after, same_instance=before == after,
    head=dict(path=str(head), kind=record['kind'], index=record['index'],
              sha256=hashlib.sha256(head_raw).hexdigest(), size=len(head_raw)),
    latest_checkpoint_name=checkpoint_names[-1] if checkpoint_names else None,
    hard_end_unix=plan['hard_end_unix'], bounded_file_bytes_reserved=consumed,
    clean_boundary_candidate=record['kind'] == 'SLEEP_COMPLETE',
    model_calls=0, signals_sent=0, saved_state_ownership_verified=False)
print(json.dumps(result, sort_keys=True))
'''


if __name__ == '__main__':
    marker = HERE / 'TARGET_OBSERVATION_STARTED.json'
    with marker.open('x') as stream:
        json.dump(dict(schema='R170_TARGET_ONCE_V1', retry_permitted=False), stream)
    command = ['bash', str(HERE.parents[2] / 'gpu/ovx2_ssh.sh'),
        'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 '
        '/localhome/local-rohing/v2/venv/bin/python -I -B -']
    result = subprocess.run(command, input=REMOTE.encode(), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=60, check=False)
    with (HERE / 'TARGET_OBSERVATION_STDOUT.txt').open('xb') as stream:
        stream.write(result.stdout)
    with (HERE / 'TARGET_OBSERVATION_STDERR.txt').open('xb') as stream:
        stream.write(result.stderr)
    if result.returncode:
        raise SystemExit(result.returncode)
    receipt = json.loads(result.stdout)
    with (HERE / 'TARGET_OBSERVATION.json').open('x') as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
    print(json.dumps(receipt, indent=2))
