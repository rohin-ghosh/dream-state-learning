"""One-shot, READY-bound retirement of only the owned ovx7 generator."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import time


ROOT = Path('/localhome/local-rohing/orch_r119_l1_generation_20260915_attempt2')
HANDOVER = Path('/localhome/local-rohing/orch_r119_l1_gen7_handover_20260915_attempt1')
DEST = HANDOVER / 'release_attempt2'
EVALUATOR = Path('/localhome/local-rohing/orch_r124_route_behavior_20260915')
PINS = {'READY.json': '7bf4694f3b7ef8fea593100743c5b1d886a2c70e56479c62de8107d6f3184a36',
        'PLAN.json': '83933ffcd185a3721f0fb3b6b62d4845a64f47072a7b092ae436bd3eb0203654'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    temporary = path.with_name(path.name + '.pending')
    with temporary.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    assert not path.exists(), 'immutable_receipt_exists'
    os.rename(temporary, path)


def identity(pid):
    directory = Path('/proc') / str(pid)
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, uid=directory.stat().st_uid, start_ticks=fields[19],
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def owned_descriptor(expected, root, role, uuid):
    assert identity(expected['pid']) == expected and expected['uid'] == os.getuid()
    process = Path('/proc') / str(expected['pid'])
    arguments = (process / 'cmdline').read_bytes().split(b'\0')
    assert str(root).encode() in arguments and role.encode() in arguments
    assert arguments[arguments.index(b'--index') + 1] == b'7'
    if role == 'generate':
        assert ('CUDA_VISIBLE_DEVICES=' + uuid).encode() in (process / 'environ').read_bytes().split(b'\0')
    descriptor = os.pidfd_open(expected['pid'])
    try:
        assert identity(expected['pid']) == expected
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def gone(expected):
    try:
        if identity(expected['pid']) != expected:
            return True
        fields = (Path('/proc') / str(expected['pid']) / 'stat').read_text().rsplit(')', 1)[1].split()
        return fields[0] == 'Z'
    except FileNotFoundError:
        return True


def candidate_progress(directory):
    progress = read(directory / 'PROGRESS.json')
    count = progress['calls']
    return ((directory / f'CALL_{count:06d}.json').exists()
            and not (directory / f'INTENT_{count+1:06d}.json').exists()), progress


def execute():
    spec = importlib.util.spec_from_file_location('handover', HANDOVER / 'source' / 'orch_r119_l1_gen7_handover.py')
    handover = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(handover)
    for name, expected in PINS.items():
        assert sha(EVALUATOR / name) == expected
    plan = read(EVALUATOR / 'PLAN.json')
    assert plan['physical'] == 7 and plan['uuid'] == handover.UUID
    config = read(ROOT / 'FORKS.json')
    assert config['node'] == 'ovx' and config['uuid_by_index'][7] == handover.UUID
    assert config['hard_deadline_unix'] == config['lease_end_unix'] - 21600
    deadline = min(read(HANDOVER / 'PRE_SIGNAL.json')['deadline_unix'], config['hard_deadline_unix'])
    assert time.time() < deadline and not (HANDOVER / 'RELEASED.json').exists()
    assert read(HANDOVER / 'EXECUTOR_CANCELLED.json')['status'] == 'CANCELLED_PRE_RETIREMENT_SUPERVISOR_AND_NATIVE_CONTINUED'
    supervisor = read(ROOT / 'gpu7' / 'START.json')['identity']
    supervisor_fd = owned_descriptor(supervisor, ROOT, 'supervise', handover.UUID)
    native_fd = None
    supervisor_paused = False
    native_paused = False
    retired = False
    try:
        write(DEST / 'PRE_SIGNAL.json', dict(status='MAIN_READY_BOUND', evaluator_pins=PINS,
              supervisor=supervisor, release_source_sha256=sha(__file__),
              handover_source_sha256=sha(handover.__file__), deadline_unix=deadline,
              other13_unchanged=True, observed_unix=time.time()))
        signal.pidfd_send_signal(supervisor_fd, signal.SIGSTOP)
        supervisor_paused = True
        handover.generation.wait_stopped(supervisor['pid'])
        heartbeat = read(ROOT / 'gpu7' / 'HEARTBEAT.json')
        stage = ROOT / 'gpu7' / ('segment%04d' % heartbeat['segment'])
        native = read(stage / 'LAUNCH.json')['identity']
        native_fd = owned_descriptor(native, ROOT, 'generate', handover.UUID)
        output = stage / 'gpu7'
        while time.time() < deadline:
            assert identity(native['pid']) == native
            candidate, before = candidate_progress(output)
            if candidate:
                signal.pidfd_send_signal(native_fd, signal.SIGSTOP)
                native_paused = True
                handover.generation.wait_stopped(native['pid'])
                boundary = handover.boundary_status(output)
                if boundary['candidate'] and boundary['progress'] == before:
                    break
                signal.pidfd_send_signal(native_fd, signal.SIGCONT)
                native_paused = False
            time.sleep(.0005)
        else:
            raise TimeoutError('no_complete_task_boundary_within600s')
        captures = {str(path.relative_to(ROOT)): sha(path) for path in sorted(output.iterdir()) if path.is_file()}
        write(DEST / 'CAPTURE_HASHES.json', dict(files=captures, progress=boundary['progress'],
              pending_calls=[], boundary=boundary, native=native, supervisor=supervisor,
              plan_sha256=sha(stage/'PLAN.json'), launch_sha256=sha(stage/'LAUNCH.json'),
              forks_sha256=sha(ROOT/'FORKS.json'), checkpoint_commit_sha256=config['checkpoint_commit_sha256'],
              checkpoint_state_sha256=config['checkpoint_state_sha256'], observed_unix=time.time()))
        for descriptor in (supervisor_fd, native_fd):
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        supervisor_paused = native_paused = False
        retired = True
        until = min(time.time() + 30, deadline)
        while not (gone(supervisor) and gone(native)):
            if time.time() >= until:
                raise TimeoutError('owned_retirement_not_confirmed')
            time.sleep(.1)
        write(DEST / 'RETIRED.json', dict(status='EXTERNAL_SAFE_TASK_BOUNDARY_RETIREMENT',
              native=native, supervisor=supervisor, evaluator_pins=PINS, no_replay=True,
              capture_manifest_sha256=sha(DEST/'CAPTURE_HASHES.json'), observed_unix=time.time()))
        from gpu.orch_rich_hot_node2_scan import scan
        while time.time() < deadline:
            snapshot = scan(7, Path(config['service_identity']))
            report_path = DEST / ('ADMISSION_%d.json' % time.time_ns())
            write(report_path, snapshot)
            if snapshot['clear']:
                assert snapshot['scanner_euid'] == 0 and snapshot['gpu']['uuid'] == handover.UUID
                assert gone(supervisor) and gone(native)
                write(DEST / 'RELEASED.json', dict(status='RELEASED', physical=7, uuid=handover.UUID,
                      root=str(ROOT), native=native, supervisor=supervisor, evaluator_pins=PINS,
                      boundary=boundary, no_replay=True, no_training_changes=True, other13_unchanged=True,
                      capture_manifest=dict(path=str(DEST/'CAPTURE_HASHES.json'), sha256=sha(DEST/'CAPTURE_HASHES.json'),files=len(captures)),
                      admission=dict(path=str(report_path),sha256=sha(report_path),clear=True,scanner_euid=0),
                      service_identity_sha256=sha(config['service_identity']),hard_deadline_unix=config['hard_deadline_unix'],
                      retired_receipt_sha256=sha(DEST/'RETIRED.json'),observed_unix=time.time()))
                write(HANDOVER / 'RELEASED.json', dict(read(DEST/'RELEASED.json'),
                      release_attempt=str(DEST),release_source_sha256=sha(__file__),
                      release_attempt_receipt_sha256=sha(DEST/'RELEASED.json')))
                print(json.dumps(dict(status='RELEASED',path=str(HANDOVER/'RELEASED.json'),sha256=sha(HANDOVER/'RELEASED.json'))),flush=True)
                return
            time.sleep(2)
        raise TimeoutError('strict_admission_not_clear')
    except BaseException as failure:
        write(DEST / 'NOT_RELEASED.json', dict(status='NOT_RELEASED',error_type=type(failure).__name__,
              error=str(failure),retired=retired,observed_unix=time.time()))
        raise
    finally:
        for descriptor, paused in ((native_fd, native_paused),(supervisor_fd, supervisor_paused)):
            if descriptor is not None:
                if paused:
                    try:
                        signal.pidfd_send_signal(descriptor,signal.SIGCONT)
                    except ProcessLookupError:
                        pass
                os.close(descriptor)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.default_int_handler)
    execute()
