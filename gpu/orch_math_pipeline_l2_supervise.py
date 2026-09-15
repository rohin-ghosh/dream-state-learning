"""Non-material supervision repair: preserve native phases and original lifetime."""

import argparse
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time

from gpu import orch_math_pipeline_l2_run as original


def transient_admission(report):
    reasons = report['blocking_reasons']
    return bool(reasons) and all(reason.startswith(('process_identity_drift:',
        'minor_scan_process_drift:', 'minor_scan_identity_changed:')) for reason in reasons)


def completed_phase(campaign, arm, cycle, phase, identity):
    path = campaign / arm / f'cycle{cycle}' / phase
    receipt = original.read(path / 'COMPLETE.json')
    assert receipt['status'] == 'COMPLETE' and not (path / 'FAILED.json').exists()
    assert receipt['process'] == [identity['boot_id'], identity['pid'], int(identity['start_ticks'])]
    assert original.read(path / 'AFTER.json')['actual_mounted_identity_verified']


def clear_admission(root, campaign, arm, cycle, phase, lifetime):
    index, unused = original.policy.DEVICES[arm]
    until = min(time.time() + 60, lifetime['native_deadline_unix'])
    attempt = 0
    while True:
        report = original.scan(index, root / 'SERVICE_IDENTITY.json')
        original.write(campaign / f'REPAIR_ADMISSION_{arm}_C{cycle}_{phase}_{attempt}.json', report)
        if report['clear'] and report['scanner_euid'] == 0:
            return
        assert transient_admission(report) and time.time() < until, 'full_admission_failed_no_waiver'
        attempt += 1
        time.sleep(2)


def campaign(root, directory, lifetime, stages=None, native_driver=None):
    if stages is None:
        stages = [(0, 'readout')] + [(cycle, phase) for cycle in range(1, 4) for phase in ('experience', 'readout')]
    cursors, active = {arm: 0 for arm in original.policy.ARMS}, {}
    logs = []
    try:
        while not all(cursor == len(stages) for cursor in cursors.values()):
            assert time.time() < lifetime['hard_deadline_unix'] - 120, 'original_lifetime_expired'
            for arm in original.policy.ARMS:
                if cursors[arm] == len(stages):
                    continue
                cycle, phase = stages[cursors[arm]]
                launch_path = directory / f'LAUNCH_{arm}_C{cycle}_{phase}.json'
                if arm in active:
                    descriptor, identity, child = active[arm]
                    if not select.select([descriptor], [], [], 0)[0]:
                        continue
                    if child is not None:
                        assert child.wait() == 0, 'native_failure_no_retry'
                    completed_phase(directory, arm, cycle, phase, identity)
                    os.close(descriptor)
                    del active[arm]
                    cursors[arm] += 1
                    continue
                if launch_path.exists():
                    identity = original.read(launch_path)['identity']
                    process = Path('/proc') / str(identity['pid'])
                    if not process.exists():
                        completed_phase(directory, arm, cycle, phase, identity)
                        cursors[arm] += 1
                        continue
                    descriptor = os.pidfd_open(identity['pid'])
                    assert original.process_identity(process) == identity, 'adopt_exact_native_identity_only'
                    active[arm] = descriptor, identity, None
                    original.write(directory / f'ADOPTED_{arm}_C{cycle}_{phase}.json', dict(identity=identity,
                        original_launch_sha256=original.sha(launch_path), adopted_unix=time.time(), native_relaunch=False))
                    continue
                assert not (directory / arm / f'cycle{cycle}' / phase).exists(), 'partial_native_phase_never_retried'
                clear_admission(root, directory, arm, cycle, phase, lifetime)
                uuid = original.policy.DEVICES[arm][1]
                log = (directory / f'{arm}_C{cycle}_{phase}.log').open('x')
                logs.append(log)
                command = [original.PYTHON, '-B', str(native_driver)] if native_driver else [original.PYTHON, '-B', '-m', 'gpu.orch_math_pipeline_l2_native']
                child = subprocess.Popen(command + [
                    '--root', str(directory), '--arm', arm, '--cycle', str(cycle), '--phase', phase],
                    cwd=root / 'source', start_new_session=True,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=uuid, PYTHONPATH=str(root / 'source'),
                        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                        TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1'), stdout=log, stderr=subprocess.STDOUT)
                identity = original.process_identity(Path('/proc') / str(child.pid))
                original.write(launch_path, dict(identity=identity, uuid=uuid, started_unix=time.time(),
                    supervisor_repair=True, first_native_launch=True))
                active[arm] = os.pidfd_open(child.pid), identity, child
            original.write(directory / 'REPAIRED_PROGRESS.json', dict(stage_cursors=cursors, observed_unix=time.time()))
            time.sleep(2)
    finally:
        for descriptor, identity, child in active.values():
            if not select.select([descriptor], [], [], 0)[0]:
                assert original.process_identity(Path('/proc') / str(identity['pid'])) == identity
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                if not select.select([descriptor], [], [], 10)[0]:
                    signal.pidfd_send_signal(descriptor, signal.SIGKILL)
                    select.select([descriptor], [], [], 10)
            os.close(descriptor)
        for log in logs:
            log.close()
    original.write(directory / 'REPAIRED_TERMINAL.json', dict(status='COMPLETE', stage_cursors=cursors,
        finished_unix=time.time(), original_lifetime_unchanged=True, native_retries=0))
    return True


def remaining_stages():
    return [(cycle, phase) for cycle in range(1, 4) for phase in ('experience', 'readout')]


def continue_unattempted(root):
    original.validate(root)
    ready = original.read(root / 'CONTINUATION_READY.json')
    assert ready['supervisor_sha256'] == original.sha(Path(__file__))
    driver = root / 'orch_math_pipeline_l2_native_continue.py'
    assert original.sha(driver) == ready['native_driver_sha256'] and ready['cpu_tests_passed']
    assert original.sha(root / 'LIFETIME.json') == ready['original_lifetime_sha256']
    assert original.read(root / 'REPAIR_TERMINAL.json')['releases'] == {arm: True for arm in original.policy.ARMS}
    assert all(not (root / 'campaign_01_existing_rich' / arm / 'cycle1').exists() for arm in original.policy.ARMS)
    with (root / 'CONTINUATION_STARTED.json').open('x') as stream:
        json.dump(dict(process=original.process_identity(Path('/proc') / str(os.getpid())),
            ready_sha256=original.sha(root / 'CONTINUATION_READY.json'), started_unix=time.time()), stream)
    lifetime = original.read(root / 'LIFETIME.json')
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    status = 'FAILED'
    try:
        campaign(root, root / 'campaign_01_existing_rich', lifetime, remaining_stages(), driver)
        status = 'THREE_CYCLES_COMPLETE_BASELINE_PARTIAL_FAILED'
        original.write(root / 'EPOCH_BOUNDARY.json', dict(epoch=1, status=status,
            requires_explicit_main_dev_upgrade=True, automatic_foundation_upgrade=False,
            l2_experience_quarantined_from_l1=True, all_parent_transcripts_preserved=True))
    except BaseException as error:
        original.write(root / 'CONTINUATION_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        releases = original.release(root, 'CONTINUATION_FINAL')
        original.write(root / 'CONTINUATION_TERMINAL.json', dict(status=status, releases=releases,
            finished_unix=time.time(), lifetime_sha256=original.sha(root / 'LIFETIME.json'),
            baseline_retried=False, upgrades_require_explicit_main_dev_epoch=True))


def launch(root):
    original.validate(root)
    assert original.sha(Path(__file__)) == original.read(root / 'SUPERVISOR_REPAIR_READY.json')['source_sha256']
    lifetime = original.read(root / 'LIFETIME.json')
    takeover = original.read(root / 'SUPERVISOR_TAKEOVER.json')
    assert original.sha(root / 'LIFETIME.json') == takeover['lifetime_sha256']
    identity = takeover['old_guard_identity']
    descriptor = os.pidfd_open(identity['pid'])
    assert original.process_identity(Path('/proc') / str(identity['pid'])) == identity and identity['uid'] == os.getuid()
    assert (Path('/proc') / str(identity['pid']) / 'status').read_text().split('State:')[1].lstrip().startswith('T')
    original.write(root / 'REPAIR_GUARD_IDENTITY.json', original.process_identity(Path('/proc') / str(os.getpid())))
    signal.pidfd_send_signal(descriptor, signal.SIGKILL)
    os.close(descriptor)
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    status = 'FAILED'
    try:
        campaign(root, root / 'campaign_01_existing_rich', lifetime)
        releases = original.release(root, 'CAMPAIGN01')
        original.write(root / 'AWAITING_COMBINED.json', dict(released=releases,
            handoff_path=str(root / 'L1_FULL_HANDOFF.json'), no_model_wait=True))
        while time.time() < lifetime['native_deadline_unix'] - 600:
            handoff = root / 'L1_FULL_HANDOFF.json'
            if handoff.exists():
                document = original.read(handoff)
                receipt = original.check_handoff(document, original.read(root / 'COHORT.json'))
                original.verify_saved(receipt['output_adapter'])
                original.write(root / 'COMBINED_HANDOFF_VERIFIED.json', dict(handoff_sha256=original.sha(handoff),
                    ready_for_release=True, verified_unix=time.time()))
                if (root / 'COMBINED_GENERATOR_RELEASE.json').exists():
                    original.verify_release(original.read(root / 'COMBINED_GENERATOR_RELEASE.json'))
                    directory = original.initialize(root, 'campaign_02_combined', receipt, document['complete_receipt'])
                    campaign(root, directory, lifetime)
                    status = 'COMPLETE_TWO_CAMPAIGNS'
                    break
            time.sleep(5)
        else:
            status = 'COMPLETE_EXISTING_COMBINED_NOT_AVAILABLE_WITHIN_BOUND'
    except BaseException as error:
        original.write(root / 'REPAIR_GUARD_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        releases = original.release(root, 'REPAIR_FINAL')
        original.write(root / 'REPAIR_TERMINAL.json', dict(status=status, releases=releases,
            finished_unix=time.time(), lifetime_sha256=original.sha(root / 'LIFETIME.json')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=original.ROOT)
    parser.add_argument('--continue-unattempted', action='store_true')
    options = parser.parse_args()
    (continue_unattempted if options.continue_unattempted else launch)(options.root)
