"""Drain only the identified A2 broker after every charged call is published."""

import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import signal
import subprocess
import time


OLD = Path('/tmp/orch_math_feedback_uptake_r115_broker_source_20260915_attempt1')
LANE = '/localhome/local-rohing/orch_math_feedback_uptake_r115_f2_20260915_attempt1/lane5'


def snapshot(root):
    root = Path(root)
    ledger = root / 'parent_claude'
    claims = sorted(ledger.glob('*.claim'))
    pending, statuses = [], {}
    for claim in claims:
        identifier = claim.name.removesuffix('.claim')
        published = claim/'PUBLISHED.json'
        response = root/'parent_queue'/(identifier+'.response.json')
        if not published.exists() or not response.exists() or not (claim/'RESERVATION.json').exists():
            pending.append(identifier)
            continue
        record = json.loads(published.read_text())
        value = json.loads(response.read_text())
        valid = record['response_sha256'] == hashlib.sha256(response.read_bytes()).hexdigest()
        archive = value['transcript_receipt']
        directory = Path(archive['remote_root'])
        valid = valid and directory == root/'parent_transcripts'/identifier and bool(archive['files'])
        for name, digest in archive['files'].items():
            valid = valid and Path(name).name == name
            if not valid or not (directory/name).is_file() or hashlib.sha256((directory/name).read_bytes()).hexdigest() != digest:
                valid = False
                break
        if not valid:
            pending.append(identifier)
        statuses[value['status']] = statuses.get(value['status'], 0)+1
    partials = sorted(path.name for path in (root/'parent_queue').glob('*.partial'))
    return dict(claims=len(claims), pending=pending, partials=partials, statuses=statuses,
        safe=bool(claims) and not pending and not partials,
        config_sha256=hashlib.sha256((ledger/'CONFIG.json').read_bytes()).hexdigest())


def identity(proc):
    fields = (proc/'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=int(proc.name), start_ticks=fields[19], uid=proc.stat().st_uid,
        command_sha256=hashlib.sha256((proc/'cmdline').read_bytes()).hexdigest(),
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def validate_target(runtime):
    if Path(runtime) != OLD:
        raise ValueError('only_original_owned_A2_runtime')
    launch = json.loads((OLD/'ASTRA_BROKER_ATTEMPT2_PROCESS.json').read_text())
    proc = Path('/proc')/str(launch['pid'])
    pinned = identity(proc)
    command = (proc/'cmdline').read_bytes().split(b'\0')
    if (pinned['uid'] != os.getuid() or pinned['start_ticks'] != str(launch['start_ticks'])
            or (proc/'cwd').resolve() != OLD or str(OLD/'gpu/orch_math_feedback_uptake_r115_broker.py').encode() not in command
            or str(OLD/'ASTRA_CONFIG.json').encode() not in command or b'ASTRA' not in command):
        raise ValueError('exact_owned_broker_identity_required')
    if b'CUDA_VISIBLE_DEVICES=' not in (proc/'environ').read_bytes().split(b'\0'):
        raise ValueError('cpu_broker_only')
    return proc, pinned


def remote_snapshot():
    script = 'import hashlib,json\nfrom pathlib import Path\n'+inspect.getsource(snapshot)+'\nprint(json.dumps(snapshot('+repr(LANE)+')))\n'
    result = subprocess.run(['bash', str(OLD/'gpu/ovx3_ssh.sh'), "python3 - <<'PY'\n"+script+'PY'],
        capture_output=True, text=True, timeout=20, check=True)
    return json.loads(result.stdout)


def drain(output, *, timeout=180):
    output = Path(output)
    if output.exists():
        raise ValueError('preserve_prior_migration_receipt')
    proc, pinned = validate_target(OLD)
    config_sha = hashlib.sha256((OLD/'ASTRA_CONFIG.json').read_bytes()).hexdigest()
    descriptor = os.pidfd_open(pinned['pid'])
    stopped = False
    try:
        deadline = time.time()+min(timeout, 180)
        while time.time() < deadline:
            if identity(proc) != pinned:
                raise ValueError('broker_identity_changed')
            children = proc/'task'/proc.name/'children'
            if children.read_text().strip() or (proc/'wchan').read_text().strip() != 'hrtimer_nanosleep':
                time.sleep(.1)
                continue
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            stopped = True
            for unused in range(100):
                if (proc/'stat').read_text().rsplit(')', 1)[1].split()[0] in ('T', 't'):
                    break
                time.sleep(.001)
            if (proc/'stat').read_text().rsplit(')', 1)[1].split()[0] not in ('T', 't'):
                raise ValueError('broker_not_stopped_for_boundary_check')
            state = None if children.read_text().strip() else remote_snapshot()
            if state is None or not state['safe']:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                stopped = False
                time.sleep(.2)
                continue
            if state['config_sha256'] != config_sha or identity(proc) != pinned:
                raise ValueError('same_config_and_identity_at_completed_boundary')
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            stopped = False
            until = time.time()+15
            while proc.exists() and time.time() < until:
                time.sleep(.1)
            if proc.exists():
                raise ValueError('old_broker_exit_pending_no_force_kill')
            after = remote_snapshot()
            if after != state:
                raise ValueError('ledger_changed_after_owned_exit')
            subprocess.run(['bash', str(OLD/'gpu/ovx3_ssh.sh'), 'rmdir '+LANE+'/parent_claude/RUNNER.lock'],
                capture_output=True, text=True, timeout=20, check=True)
            receipt = dict(prior_identity=pinned, released_unix=time.time(), boundary=state,
                old_config_sha256=config_sha, same_ledger_preserved=True, all_transcript_hashes_verified=True,
                charged_calls_retried=0, native_processes_signalled=0, fable_processes_signalled=0)
            with output.open('x') as stream:
                json.dump(receipt, stream, sort_keys=True, indent=2)
            return receipt
        raise TimeoutError('completed_call_boundary_wait_bounded_old_broker_unchanged')
    finally:
        if stopped:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(drain(args.output), sort_keys=True))
