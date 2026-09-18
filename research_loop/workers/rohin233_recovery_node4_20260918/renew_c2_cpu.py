"""Wait for the existing C2 replay, then renew only its drained CPU parent."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

from c2_parent_continue import FLEET, validate_config_change
from deadline_resume import sha


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[2]
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
REMOTE = '/localhome/local-rohing/orch_r233_C2_deadline_20260918/operator'
OLD_PID = 471781
OLD_START = '183179491'
OLD_CONFIG = FLEET / 'LIVE_CONVERSATION_PARENT14_CONFIG.json'
OLD_OUTPUT = FLEET / 'LIVE_CONVERSATION_PARENT14/run'


def write_once(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def remote(command, input_text=None):
    result = subprocess.run(['bash', str(REPO / 'gpu/ovx3_ssh.sh'), command],
        input=input_text, capture_output=True, text=True, timeout=45)
    if result.returncode:
        raise RuntimeError(result.stderr[-500:])
    return result.stdout


def stop_drained_parent():
    process = Path('/proc') / str(OLD_PID)
    expected = ['python3', str(FLEET / 'r202_parent.py'), '--config', str(OLD_CONFIG),
        '--output', str(OLD_OUTPUT), '--policy-addendum', str(FLEET / 'R230_PARENT_CURRICULUM.md'),
        '--priority-policy-update']
    descriptor = os.pidfd_open(OLD_PID)
    try:
        until = time.monotonic() + 180
        while time.monotonic() < until:
            fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
            argv = (process / 'cmdline').read_bytes().decode().strip('\0').split('\0')
            if fields[19] != OLD_START or argv != expected or process.stat().st_uid != os.getuid():
                raise ValueError('exact_C2_CPU_parent_only')
            children = (process / 'task' / str(OLD_PID) / 'children').read_text().strip()
            attempts = sorted(OLD_OUTPUT.glob('parent_*/SOURCE.json'))
            settled = bool(attempts) and (attempts[-1].parent / 'RESULT.json').exists()
            if not children and settled and (process / 'wchan').read_text().strip() == 'hrtimer_nanosleep':
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                poller = select.poll()
                poller.register(descriptor, select.POLLIN)
                if not poller.poll(10000):
                    raise RuntimeError('C2_CPU_exit_not_observed')
                return dict(pid=OLD_PID, start_ticks=OLD_START, exited_unix=time.time(),
                    settled_last_result=str(attempts[-1].parent / 'RESULT.json'),
                    exact_idle_no_subprocess=True, signal='EXACT_PIDFD_SIGTERM_CPU_ONLY', native_signals=[])
            time.sleep(.1)
        raise TimeoutError('old_C2_CPU_not_drained_no_signal')
    finally:
        os.close(descriptor)


def continue_parent(status):
    if status['status'] != 'LOADED' or status['native']['pid'] != 829798:
        raise ValueError('actual_C2_LOADED_required_before_CPU_handoff')
    binding_text = remote(PYTHON + ' -B -', '''import json,sys
from pathlib import Path
sys.path.insert(0, REMOTE)
from deadline_status import status
from deadline_resume import identity,write
binding=status('C2')
assert binding['status']=='LOADED'
binding['identity']=identity(binding['native']['pid'])
path=Path(REMOTE)/'C2_PARENT_NATIVE_BINDING.json'
write(path,binding)
print(json.dumps(binding,sort_keys=True,indent=2))
'''.replace('REMOTE', repr(REMOTE)))
    binding_path = OWN / 'private/C2_PARENT_NATIVE_BINDING.json'
    with binding_path.open('x') as stream:
        stream.write(binding_text)
    remote_binding_sha = remote('sha256sum ' + REMOTE + '/C2_PARENT_NATIVE_BINDING.json').split()[0]
    remote(PYTHON + ' -B -', 'import sys; sys.path.insert(0, ' + repr(REMOTE) + '); '
        'from c2_parent_binding import verify; verify(' + repr(REMOTE + '/C2_PARENT_NATIVE_BINDING.json')
        + ', ' + repr(remote_binding_sha) + ')')
    stopped = stop_drained_parent()
    write_once(OWN / 'private/C2_PARENT_DRAINED.json', stopped)
    previous = json.loads(OLD_CONFIG.read_bytes())
    reserved = max(json.loads(path.read_bytes())['response_count'] for path in OLD_OUTPUT.glob('parent_*/SOURCE.json'))
    config = dict(previous, hard_end_unix=1789927200, predecessor_output=str(OLD_OUTPUT),
        predecessor_started_sha256=sha(OLD_OUTPUT / 'STARTED.json'),
        start_after_response_count=max(previous['start_after_response_count'], reserved),
        native_binding_path=REMOTE + '/C2_PARENT_NATIVE_BINDING.json', native_binding_sha256=remote_binding_sha)
    validate_config_change(previous, config)
    config_path = OWN / 'private/C2_CPU_PARENT_CONFIG.json'
    write_once(config_path, config)
    source_files = [OWN / 'c2_parent_continue.py', FLEET / 'r202_parent.py',
        FLEET.parents[1] / 'provider_route.py', FLEET / 'R230_PARENT_CURRICULUM.md',
        REPO / 'gpu/orch_r133_programme_parent.py', REPO / 'gpu/orch_route_parent_campaign_providers.py']
    output = OWN / 'private/c2_parent'
    manifest = dict(config_path=str(config_path), predecessor_config_path=str(OLD_CONFIG),
        output=str(output), policy_addendum=str(FLEET / 'R230_PARENT_CURRICULUM.md'),
        remote_operator=REMOTE, local_source_sha256={str(path):sha(path) for path in source_files},
        hard_end_unix=1789927200, native_signals=[])
    write_once(OWN / 'private/C2_CPU_PARENT_MANIFEST.json', manifest)
    with (OWN / 'private/c2_parent.log').open('x') as log:
        child = subprocess.Popen([sys.executable, '-B', str(OWN / 'c2_parent_continue.py')], cwd=REPO,
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    until = time.monotonic() + 90
    while not (output / 'STARTED.json').exists():
        if child.poll() is not None or time.monotonic() >= until:
            raise RuntimeError('new_C2_CPU_parent_START_pending_or_failed')
        time.sleep(.5)
    fields = (Path('/proc') / str(child.pid) / 'stat').read_text().rsplit(') ',1)[1].split()
    receipt = dict(observed_utc=datetime.now(timezone.utc).isoformat(), cpu_predecessor=stopped,
        status='CPU_PARENT_STARTED_ACTUAL_NATIVE_BOUND_RENDER_PENDING', parent_pid=child.pid,
        parent_start_ticks=fields[19], hard_end_unix=1789927200, native=status['native'], loaded=status['loaded'],
        native_binding_sha256=remote_binding_sha, config_sha256=sha(config_path),
        started_sha256=sha(output / 'STARTED.json'), predecessor_reserved_response_count=reserved,
        source_policy_and_provider_preserved=True, old_ledgers_and_inboxes_preserved=True,
        native_signals=[], rendered_REQUEST_ACT_pending=True)
    write_once(OWN / 'C2_CPU_PARENT_CONTINUATION.json', receipt)
    print(json.dumps(receipt), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wait-seconds', type=int, default=5400)
    arguments = parser.parse_args()
    until = time.monotonic() + arguments.wait_seconds
    while time.monotonic() < until:
        result = json.loads(remote(PYTHON + ' -B ' + REMOTE + '/deadline_status.py C2'))
        temporary = OWN / 'private/C2_CURRENT.next.json'
        temporary.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
        os.replace(temporary, OWN / 'C2_CONTINUATION_STATUS.json')
        if result['status'] == 'LOADED':
            write_once(OWN / 'C2_NATIVE_READY.public.json', result)
            continue_parent(result)
            return
        time.sleep(30)
    raise TimeoutError('bounded_C2_LOAD_wait_expired_no_native_signal')


if __name__ == '__main__':
    main()
