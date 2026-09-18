"""Bind and restart P3's sole parent immediately after its actual renewed LOAD."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
END_UNIX = 1790359200
REMOTE = '/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical3/r233_recovery/p3_continued_observe.py'


def ready(evidence):
    binding = evidence.get('binding')
    return (evidence.get('status') == 'LOADED_ALIVE_WALL_EXTENDED' and
        isinstance(binding, dict) and binding.get('hard_end_unix') == END_UNIX and
        binding.get('loaded_index') == evidence.get('loaded', {}).get('index') and
        binding.get('pid') == evidence.get('native', {}).get('pid'))


def immutable(path, value):
    if path.exists():
        if json.loads(path.read_bytes()) != value:
            raise ValueError('preserve_existing_different_recovery_artifact:' + path.name)
        return
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def status(value):
    temporary = HERE / 'P3_FINISH_STATUS.next'
    temporary.write_text(json.dumps(dict(observed_unix=time.time(), **value), sort_keys=True, indent=2) + '\n')
    temporary.replace(HERE / 'P3_FINISH_STATUS.json')


def remote(bind=False):
    command = '/localhome/local-rohing/v2/venv/bin/python -B ' + REMOTE
    if bind:
        command += ' --bind'
    result = subprocess.run(['bash', str(REPO / 'gpu/a40r_ssh.sh'), command],
        capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError('observation_or_idempotent_binding_failed')
    return json.loads(result.stdout)


def main():
    with (HERE / 'P3_FINISH.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (HERE / 'P3_CONTINUED_PARENT_STARTED.json').exists():
            raise ValueError('parent_already_launched_inspect_existing_receipt')
        immutable(HERE / 'P3_FINISH_STARTED.json', dict(pid=os.getpid(),
            start_ticks=Path('/proc/self/stat').read_text().rsplit(') ', 1)[1].split()[19],
            observed_unix=time.time(), native_signals=[], source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            action='WAIT_ACTUAL_LOAD_BIND_EXACT_INCARNATION_START_EXISTING_PARENT_LEDGER',
            hard_end_unix=END_UNIX))
        while time.time() < END_UNIX:
            try:
                evidence = remote()
            except (subprocess.TimeoutExpired, RuntimeError):
                status(dict(status='READ_POLL_FAILED_RETRYING', native_signals=[]))
                time.sleep(30)
                continue
            if not ready(evidence):
                status(dict(status='WAITING_ACTUAL_LOAD', evidence=evidence, native_signals=[]))
                time.sleep(30)
                continue
            evidence = remote(bind=True)
            if not ready(evidence) or not evidence.get('binding_persisted'):
                raise ValueError('actual_parent_binding_receipt_required')
            immutable(HERE / 'P3_CONTINUED_BINDING.json', evidence['binding'])
            immutable(HERE / 'P3_CONTINUED_LOADED.json', evidence)
            entrypoint = HERE / 'p3_continued_parent.py'
            validation = subprocess.run([sys.executable, '-B', str(entrypoint), 'validate'],
                cwd=REPO, capture_output=True, text=True, check=True, timeout=120)
            immutable(HERE / 'P3_CONTINUED_PARENT_MANIFEST.json', json.loads(validation.stdout))
            with (HERE / 'P3_CONTINUED_PARENT.private.log').open('ab') as log:
                parent = subprocess.Popen([sys.executable, '-B', str(entrypoint), 'serve'],
                    cwd=REPO, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True, close_fds=True)
            start_ticks = Path(f'/proc/{parent.pid}/stat').read_text().rsplit(') ', 1)[1].split()[19]
            receipt = dict(pid=parent.pid, start_ticks=start_ticks, started_unix=time.time(),
                native_pid=evidence['binding']['pid'], loaded_index=evidence['binding']['loaded_index'],
                hard_end_unix=END_UNIX, source_sha256=hashlib.sha256(entrypoint.read_bytes()).hexdigest(),
                credentials_inherited_not_persisted=True, native_signals=[], publication_claim=False)
            immutable(HERE / 'P3_CONTINUED_PARENT_STARTED.json', receipt)
            status(dict(status='PARENT_STARTED_NOT_YET_RENDERED', parent=receipt,
                native=evidence, native_signals=[]))
            return
        raise TimeoutError('authorized_lease_horizon_reached_without_LOAD')


if __name__ == '__main__':
    main()
