"""Admission-only slot5 recovery: preserve failed guardian, never replay a call."""

import argparse
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_r107_route_parent_run as original
from gpu import orch_r107_route_parent_broker as broker
from organism_v6 import orch_r107_route_parent as policy


R108_PARENT = (
    'R108 intervention classes are perception, persistence, metacognition, curiosity, '
    'goal/meta-goal regulation, reflection, action steering, and affective-value. '
    'Choose only classes warranted by the actual child experience and identify '
    'the chosen classes in your rationale. Intervene constructively on failure; '
    'never prescribe the answer or a solved route. Distinguish the observation '
    'that motivated coaching from the hoped-for behavioral change. Preserve '
    'the creative/supportive lineage policy. Encourage multi-angle perception '
    'during reflection when useful, not a mandatory checklist or longer prose.'
)
R108_REFLECTION = (
    'Consider the experience from useful different perspectives: what you '
    'actually perceived, what remains uncertain, how your goal and allocation '
    'of attention relate to your actions, and what should change next. Choose '
    'relevant angles rather than completing a checklist. An announced intention '
    'is not an observed behavioral change. Do not repeat passages or invent facts.'
)


def require_unlaunched(root):
    lane = root / 'campaign_route_parent_5'
    policy.require(original.read(lane / 'GUARDIAN_FAILED.json')['error'] == 'strict_privileged_clear_required',
                   'only_admission_exhaustion_recovery')
    policy.require(not (lane / 'LAUNCH.json').exists() and not (lane / 'native').exists(), 'no_native_replay')
    reservations = root / 'RESERVATIONS.jsonl'
    if reservations.exists():
        import json
        policy.require(not any(json.loads(line)['index'] == 5 for line in reservations.read_text().splitlines()),
                       'slot5_zero_prior_calls_required')
    return lane


def guard(root):
    original.verify(root)
    lane = require_unlaunched(root)
    publication = original.read(lane / 'RECOVERY_PUBLICATION.json')
    policy.require(publication['source_sha256'] == original.sha(Path(__file__))
        and publication['original_failure_sha256'] == original.sha(lane / 'GUARDIAN_FAILED.json')
        and publication['ready_sha256'] == original.sha(lane / 'READY.json'), 'exact_recovery_binding')
    deadline = original.read(root / 'LIFETIME.json')
    child = identity = None
    status = 'FAILED'
    try:
        for attempt in range(90):
            policy.require(time.time() < deadline['native_deadline_unix'], 'original_deadline')
            snapshot = original.admission.scan(5, root / 'SERVICE_IDENTITY.json')
            original.write(lane / f'RECOVERY_ADMISSION_{attempt:03d}.json', snapshot)
            if snapshot['clear']:
                break
            time.sleep(2)
        policy.require(snapshot['clear'] and snapshot['scanner_euid'] == 0, 'strict_clear_no_waiver')
        require_unlaunched(root)
        with (lane / 'recovery_native.log').open('x') as log:
            child = subprocess.Popen([original.common.PYTHON, '-B', str(Path(__file__)),
                'native108', '--root', str(root)], cwd=root / 'source',
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=policy.DEVICES[5], PYTHONPATH=str(root / 'source'),
                    PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                    OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false'),
                stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
            identity = original.common.process_identity(Path('/proc') / str(child.pid))
            original.write(lane / 'LAUNCH.json', dict(pid=child.pid, identity=identity, uuid=policy.DEVICES[5],
                started_unix=time.time(), recovery_source_sha256=original.sha(Path(__file__)), no_prior_native_calls=True))
            while child.poll() is None:
                policy.require(time.time() < deadline['hard_deadline_unix'] - 30, 'original_hard_end')
                time.sleep(1)
            policy.require(child.returncode == 0 and (lane / 'COMPLETE.json').exists(), 'no_failed_native_retry')
            status = 'COMPLETE'
    finally:
        if child is not None:
            original.common.stop_owned(child, identity)
        original.write(lane / 'RECOVERY_TERMINAL.json', dict(status=status, finished_unix=time.time(),
            original_terminal_preserved=True, original_deadlines_preserved=True))
        original.write(lane / 'RECOVERY_RELEASE.json', original.admission.scan(5, root / 'SERVICE_IDENTITY.json'))


def serve(repository, root, buffer, receipts):
    lane = root / 'campaign_route_parent_5'
    class RecoveryStore(broker.existing.transport.Store):
        def exists(self, path):
            if path == lane / 'TERMINAL.json':
                return super().exists(lane / 'RECOVERY_TERMINAL.json')
            return super().exists(path)
    broker.existing.transport.Store = RecoveryStore
    broker.policy.PARENT_INSTRUCTIONS += '\n\n' + R108_PARENT
    broker.serve(repository, lane, buffer, receipts, 5,
        '334df37a468dc57ef34aef04e84cfde627fc1e04222f157bd068c1407ec1897d', 1789465808.9901345)


def native108(root):
    publication = original.read(root / 'campaign_route_parent_5/RECOVERY_PUBLICATION.json')
    policy.require(publication['source_sha256'] == original.sha(Path(__file__)), 'R108_runtime_pin')
    original.policy.REFLECTION_SYSTEM += '\n\n' + R108_REFLECTION
    original.write(root / 'campaign_route_parent_5/R108_RUNTIME.json', dict(
        reflection_system_sha256=policy.digest(original.policy.REFLECTION_SYSTEM),
        parent_addendum_sha256=policy.digest(R108_PARENT), runtime_source_sha256=original.sha(Path(__file__)),
        original_lane1_unchanged=True, fixed_quota=True, started_unix=time.time()))
    original.native(root, 5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('guard', 'broker', 'native108'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--repository', type=Path)
    parser.add_argument('--buffer', type=Path)
    parser.add_argument('--receipts', type=Path)
    options = parser.parse_args()
    if options.phase == 'guard':
        guard(options.root)
    elif options.phase == 'native108':
        native108(options.root)
    else:
        serve(options.repository, options.root, options.buffer, options.receipts)
