import hashlib
import json
import os
from pathlib import Path
import sys
import time

root = Path('/localhome/local-rohing/orch_r166_retelling_C5_20260917_recovery2')
life = Path('/localhome/local-rohing/orch_r153_community_C5_20260916_attempt1/life')
budget = 64 * 1024 * 1024


def read(path):
    global budget
    size = path.stat().st_size
    assert size <= min(budget, 16 * 1024 * 1024)
    data = path.read_bytes()
    budget -= len(data)
    return dict(path=str(path), sha256=hashlib.sha256(data).hexdigest(), content=json.loads(data))


def identity(pid):
    proc = Path('/proc') / str(pid)
    try:
        fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        return dict(pid=pid, start_ticks=fields[19], state=fields[0], parent=int(fields[1]),
            group=int(fields[2]), uid=proc.stat().st_uid, cwd=str((proc / 'cwd').resolve()),
            argv=(proc / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0'),
            cgroup=(proc / 'cgroup').read_text().strip())
    except FileNotFoundError:
        return None


seconds = int(sys.argv[1])
assert 0 <= seconds <= 180
deadline = time.monotonic() + seconds
while True:
    result = dict(observed_unix=time.time(), root=str(root), operator=identity(4015531), files={})
    for name in ('RECOVERY_EXECUTION.json', 'RECOVERY_FAILED.json', 'control/SAVED_PROOF.json',
                 'control/PREPARED.json', 'control/EFFECTIVE_POLICY.json', 'attempt/LAUNCH.json',
                 'attempt/CONTAINMENT_VERIFIED.json', 'attempt/FAILED.json',
                 'attempt/NATIVE_EXIT.json', 'attempt/SERVICE_EXIT.json'):
        path = root / name
        if path.exists():
            result['files'][name] = read(path)
    result['loaded'] = None
    for index in range(2900, 2904):
        path = life / 'stream/records' / ('%020d.json' % index)
        if not path.exists():
            break
        record = read(path)
        if record['content']['kind'] == 'LOADED':
            result['loaded'] = record
            loaded = record['content']['document']
            proof = result['files']['control/SAVED_PROOF.json']['content']
            launch = result['files']['attempt/LAUNCH.json']['content']
            config = read(root / 'control/GUARD.json')
            plan = read(Path(config['content']['plan_path']))
            native = identity(loaded['pid'])
            assert native is not None and native['state'] not in ('T', 't', 'Z', 'X')
            timer = identity(native['parent'])
            assert timer is not None and timer['pid'] == launch['pid']
            assert timer['start_ticks'] == launch['parent_start_ticks']
            assert native['group'] == timer['group'] == timer['pid']
            assert native['argv'] == ['/localhome/local-rohing/v2/venv/bin/python', '-B', '-m',
                'gpu.orch_r125_continual_guard', 'native', '--config', str(root / 'control/GUARD.json')]
            assert native['cwd'] == str(root / 'source') and native['uid'] == 2524
            assert native['cgroup'] == '0::/system.slice/' + config['content']['device_containment']['unit'] + '.service'
            assert loaded['resume'] is True and loaded['optimizer_steps'] == proof['optimizer_steps'] == 2478
            assert loaded['adapter_sha256'] == proof['adapter_state_sha256'] == '2b91fc0e5a5fde368415a78db840646f583cbf4884d1756bf599582c91a61c5c'
            assert plan['content']['hard_end_unix'] == config['content']['hard_end_unix'] == launch['hard_end_unix'] == 1789776000
            assert config['content']['resume'] is True and launch['guard_sha256'] == config['sha256']
            assert launch['plan_sha256'] == plan['sha256']
            document = record['content']
            digest = hashlib.sha256(json.dumps({key: value for key, value in document.items() if key != 'sha256'},
                sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
            assert document['sha256'] == digest
            prior = read(life / 'stream/records' / ('%020d.json' % (index - 1)))
            assert document['previous_sha256'] == prior['content']['sha256']
            intent = read(path.with_name(path.stem + '.intent.json'))
            assert intent['content']['record_sha256'] == document['sha256']
            assert intent['content']['previous_sha256'] == document['previous_sha256']
            result.update(status='ACTUAL_LOADED_SAVED28_CONTINUITY_VERIFIED', native=native, timer=timer,
                config=dict(path=config['path'], sha256=config['sha256']),
                plan=dict(path=plan['path'], sha256=plan['sha256']),
                effective_invitation_observed=False, parent_handoff_performed=False,
                no_retirement_performed=True, no_retry=True)
            break
    failed = any(name in result['files'] for name in ('RECOVERY_FAILED.json', 'attempt/FAILED.json', 'attempt/NATIVE_EXIT.json'))
    if failed or result['operator'] is None:
        for name in ('MAIN_EXECUTE.log', 'attempt/NATIVE.log'):
            path = root / name
            if path.exists():
                with path.open('rb') as stream:
                    stream.seek(max(0, path.stat().st_size - 16384))
                    result[name] = stream.read(16384).decode(errors='replace')
    print(json.dumps(result, sort_keys=True), flush=True)
    if result['loaded'] or failed or time.monotonic() >= deadline:
        break
    time.sleep(min(10, max(0, deadline - time.monotonic())))
