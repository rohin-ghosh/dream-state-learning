"""One bounded CPU waiter; actual retry LOAD gates original-parent attachment."""

import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import p3_retry_observe as observer


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
REMOTE = str(observer.CPU / 'p3_retry_observe.py')
POLL_SECONDS = 30


def ready(evidence):
    binding = evidence.get('binding')
    native = evidence.get('native') or {}
    loaded = evidence.get('loaded') or {}
    wall = evidence.get('wall_extended') or {}
    return bool(evidence.get('status') == 'RETRY_LOADED_ALIVE_WALL_VERIFIED' and isinstance(binding, dict)
        and binding.get('hard_end_unix') == observer.END_UNIX and binding.get('source') == str(observer.SOURCE)
        and binding.get('journal_id') == observer.JOURNAL_ID and binding.get('loaded_index') == loaded.get('index')
        and binding.get('loaded_sha256') == loaded.get('sha256') and binding.get('wall_index') == wall.get('index')
        and binding.get('wall_sha256') == wall.get('sha256')
        and loaded.get('pid') == binding.get('pid') and loaded.get('resume') is True
        and loaded.get('index', 0) > 5299 and binding.get('pid') not in (237705, 598987)
        and wall.get('deadline_unix') == observer.END_UNIX and observer.same_process(native, binding))


def public_evidence(evidence):
    native = evidence.get('native') or {}
    return dict(status=evidence.get('status'), observed_utc=evidence.get('observed_utc'),
        native={key:native[key] for key in ('pid','start_ticks','state','command_sha256') if key in native},
        loaded=evidence.get('loaded'), wall_extended=evidence.get('wall_extended'),
        recovery_sha256=evidence.get('recovery_sha256'), binding_present=evidence.get('binding') is not None)


def status(value):
    temporary = HERE / 'P3_RETRY_STATUS.next'
    temporary.write_text(json.dumps(dict(observed_unix=time.time(), **value), sort_keys=True, indent=2) + '\n')
    temporary.replace(HERE / 'P3_RETRY_STATUS.json')


def remote(bind=False):
    command = '/localhome/local-rohing/v2/venv/bin/python -B ' + REMOTE + (' --bind' if bind else '')
    result = subprocess.run(['bash', str(REPO / 'gpu/a40r_ssh.sh'), command],
        capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError('retry_observer_rejected_or_unavailable')
    return json.loads(result.stdout)


def start_parent(evidence):
    observer.require(ready(evidence) and evidence.get('binding_persisted'), 'actual_retry_binding_required')
    observer.require(not (HERE / 'P3_RETRY_PARENT_STARTED.json').exists(), 'no_duplicate_retry_parent')
    observer.require(not (HERE / 'P3_RETRY_PARENT_ATTEMPT.json').exists(), 'no_ambiguous_attachment_retry')
    observer.require(not (HERE / 'P3_CONTINUED_PARENT_STARTED.json').exists(), 'attempt1_parent_receipt_requires_reconciliation')
    observer.immutable(HERE / 'P3_RETRY_BINDING.json', evidence['binding'])
    observer.immutable(HERE / 'P3_RETRY_LOADED.json', evidence)
    entrypoint = HERE / 'p3_retry_parent.py'
    validation = subprocess.run([sys.executable, '-B', str(entrypoint), 'validate'],
        cwd=REPO, capture_output=True, text=True, check=True, timeout=120)
    observer.immutable(HERE / 'P3_RETRY_PARENT_MANIFEST.json', json.loads(validation.stdout))
    observer.immutable(HERE / 'P3_RETRY_PARENT_ATTEMPT.json', dict(attempted_unix=time.time(),
        loaded_index=evidence['binding']['loaded_index'], native_pid=evidence['binding']['pid'],
        manifest_sha256=observer.digest(HERE / 'P3_RETRY_PARENT_MANIFEST.json'), automatic_retry=False))
    with (HERE / 'P3_RETRY_PARENT.private.log').open('ab') as log:
        parent = subprocess.Popen([sys.executable, '-B', str(entrypoint), 'serve'], cwd=REPO,
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True, close_fds=True)
    ticks = Path(f'/proc/{parent.pid}/stat').read_text().rsplit(') ', 1)[1].split()[19]
    receipt = dict(pid=parent.pid, start_ticks=ticks, started_unix=time.time(),
        native_pid=evidence['binding']['pid'], loaded_index=evidence['binding']['loaded_index'],
        hard_end_unix=observer.END_UNIX, source_sha256=observer.digest(entrypoint),
        credentials_inherited_not_persisted=True, native_signals=[], publication_claim=False)
    observer.immutable(HERE / 'P3_RETRY_PARENT_STARTED.json', receipt)
    time.sleep(2)
    result = parent.poll()
    status(dict(status='PARENT_PROCESS_STARTED_RENDER_PENDING' if result is None else 'PARENT_EXITED_NO_AUTORETRY',
        parent=receipt, parent_exit_code=result, evidence=public_evidence(evidence), native_signals=[]))


def wait_for_load():
    while time.time() < observer.END_UNIX:
        try:
            evidence = remote()
        except (subprocess.TimeoutExpired, RuntimeError, json.JSONDecodeError) as error:
            status(dict(status='READ_POLL_FAILED_NO_PARENT_STARTED', error_type=type(error).__name__, native_signals=[]))
        else:
            if ready(evidence):
                try:
                    confirmed = remote(bind=True)
                    observer.require(confirmed.get('binding') == evidence['binding'], 'same_retry_between_observe_and_bind')
                    start_parent(confirmed)
                except Exception as error:
                    status(dict(status='ATTACHMENT_FAILED_NO_AUTORETRY', error_type=type(error).__name__,
                        parent_attempted=(HERE / 'P3_RETRY_PARENT_ATTEMPT.json').exists(), native_signals=[]))
                    raise
                return
            status(dict(status='WAITING_ACTUAL_RETRY_LOAD', evidence=public_evidence(evidence), native_signals=[]))
        time.sleep(min(POLL_SECONDS, max(0, observer.END_UNIX - time.time())))
    status(dict(status='LEASE_AWARE_WAITER_HORIZON_REACHED_NO_PARENT', native_signals=[]))


def main():
    with (HERE / 'P3_RETRY_WAITER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        observer.require(bool(os.environ.get('NVIDIA_API_KEY')), 'existing_provider_environment_required')
        observer.require(not (HERE / 'P3_RETRY_PARENT_STARTED.json').exists()
            and not (HERE / 'P3_RETRY_PARENT_ATTEMPT.json').exists()
            and not (HERE / 'P3_CONTINUED_PARENT_STARTED.json').exists(), 'no_existing_parent_start_receipt')
        observer.immutable(HERE / 'P3_RETRY_WAITER_STARTED.json', dict(pid=os.getpid(),
            start_ticks=Path('/proc/self/stat').read_text().rsplit(') ', 1)[1].split()[19],
            observed_unix=time.time(), hard_end_unix=observer.END_UNIX, poll_seconds=POLL_SECONDS,
            source_sha256=observer.digest(Path(__file__)), credentials_inherited_not_persisted=True,
            native_signals=[], gpu_launches=0, intake_sha256=observer.digest(HERE / 'P3_RETRY_INTAKE.md')))
        wait_for_load()


if __name__ == '__main__':
    main()
