"""Fresh exact native/guard/ledger/owner checks; never calls the model."""

import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import runner


REMOTE = r'''
import hashlib,json,os,sys,time
from pathlib import Path
root=Path('/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical3')
sys.path.insert(0,str(root/'r233_recovery'))
import p3_retry_endpoint as endpoint
transport,binding=endpoint.configure()
loaded=endpoint.observer.record(root/'life/stream/records'/f'{binding["loaded_index"]:020d}.json')
assert loaded['sha256']==binding['loaded_sha256'] and loaded['document']['pid']==699464
processes=[]
for directory in Path('/proc').glob('[0-9]*'):
    try:
        args=directory.joinpath('cmdline').read_bytes().decode().rstrip('\0').split('\0')
        if not args or 'python' not in Path(args[0]).name:
            continue
        module=args[args.index('-m')+1] if '-m' in args else None
        scripts=[arg for arg in args if arg.endswith('.py')]
        if not any('parent' in value or 'p3' in value or 'feedback' in value or 'lease_bridge' in value for value in scripts+([module] if module else [])):
            continue
        fields=directory.joinpath('stat').read_text().rsplit(') ',1)[1].split()
        processes.append(dict(pid=int(directory.name),start_ticks=fields[19],state=fields[0],module=module,scripts=scripts))
    except (FileNotFoundError,ProcessLookupError,PermissionError):
        continue
print(json.dumps(dict(observed_unix=time.time(),native=endpoint.observer.process(699464),binding=binding,
    node_boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
    endpoint_sha256=endpoint.observer.digest(Path(endpoint.__file__)),related_python_processes=processes,
    remote_writes=0,native_signals=0,provider_calls=0)))
'''


def main():
    os.umask(0o077)
    old = json.loads((runner.OLD / 'P3_RETRY_PARENT_STARTED.json').read_text())
    actual = runner.process(old['pid'])
    if actual and actual['start_ticks'] == old['start_ticks'] and actual['state'] != 'Z':
        raise ValueError('old_model_parent_still_alive')
    active = runner.HERE / 'PROCESS.json'
    if active.exists():
        previous = json.loads(active.read_text())['process']
        observed = runner.process(previous['pid'])
        if observed and all(observed[key] == previous[key] for key in ('boot_id','pid','start_ticks')) and observed['state'] != 'Z':
            raise ValueError('recovery_parent_already_alive')
    with (runner.LEDGER / 'PARENT_OPERATOR.lock').open('r') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock = os.fstat(handle.fileno())
        validation = subprocess.run([sys.executable, '-B', str(runner.OLD/'p3_retry_parent.py'), 'validate'],
            text=True, capture_output=True, check=True, timeout=30)
        manifest = json.loads(validation.stdout)
        if manifest != json.loads((runner.OLD/'P3_RETRY_PARENT_MANIFEST.json').read_text()):
            raise ValueError('original_exact_manifest_required')
        for name, expected in manifest['source_pins'].items():
            if runner.sha(runner.HERE/name) != expected:
                raise ValueError('original_source_pin_changed')
        repo = runner.HERE.parents[2]
        result = subprocess.run(['bash', str(repo/'gpu/a40r_ssh.sh'), 'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -'],
            input=REMOTE,text=True,capture_output=True,check=True,timeout=30)
        remote = json.loads(result.stdout)
        if remote['binding'] != manifest['binding'] or remote['endpoint_sha256'] != manifest['source_pins']['p3_retry_endpoint.py']:
            raise ValueError('current_guard_endpoint_binding_changed')
        for item in remote['related_python_processes']:
            tokens = item['scripts'] + ([item['module']] if item['module'] else [])
            if any('p3_retry_parent' in value or 'p3_parent' in value or 'r210_parent.py' in value for value in tokens):
                raise ValueError('node_model_parent_candidate_requires_reconciliation')
        folders = sorted((runner.LEDGER/'turns').glob('parent_*'))
        if any(not (folder/'RESULT.json').is_file() for folder in folders):
            raise ValueError('unfinished_parent_attempt_requires_reconciliation')
        pins = {str(path.relative_to(runner.LEDGER)): runner.sha(path)
            for folder in folders for path in folder.iterdir() if path.is_file()}
        runner.save(runner.HERE/'private/PRIOR_LEDGER_PINS.json', pins)
        runner.save(runner.HERE/'PREFLIGHT.json', dict(observed_unix=time.time(),observed_utc=runner.utc(time.time()),
            local_boot_id=runner.process(os.getpid())['boot_id'],old_parent=old,old_parent_observed=actual,
            existing_parent_lock_free=True,existing_lock_identity=[lock.st_dev,lock.st_ino],
            prior_attempt_count=len(folders),prior_ledger_file_count=len(pins),seed_sha256=runner.sha(runner.LEDGER/'SEED.json'),
            original_manifest_sha256=runner.sha(runner.OLD/'P3_RETRY_PARENT_MANIFEST.json'),fresh_native=remote,
            runner_pins={name:runner.sha(runner.HERE/name) for name in ('runner.py','preflight.py')},
            native_signals=0,provider_calls=0,model=runner.MODEL,reasoning_effort='xhigh',
            credential_present=bool(os.environ.get('NVIDIA_API_KEY')),credentials_persisted=False,
            scope='P3_CPU_MODEL_PARENT_ONLY_EXISTING_LEDGER_NO_NATIVE_CONTROL'))
    print(json.dumps(dict(preflight='PASS',native_pid=699464,old_parent_absent=actual is None,original_parent_lock_free=True,
        original_manifest='EXACT_MATCH',prior_attempts=len(folders),fresh_native_binding='PASS',provider_calls=0)))


if __name__ == '__main__':
    main()
