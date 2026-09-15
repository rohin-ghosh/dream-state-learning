"""Publish the common handoff certificate only after actual pinned math release."""

import argparse
from pathlib import Path
import time

from gpu import orch_math_feedback_uptake_r118_shared_boundary as boundary


shared, ready, require = boundary.shared, boundary.ready, boundary.require


def publish(root):
    root = Path(root).resolve(strict=True)
    release_path = root/'shared_handoff_r118'/'release'/'RELEASED.json'
    release_ref = ready.reference(release_path)
    saved = boundary.verify_release(root, release_ref)
    release = shared.read(release_path)
    cycle = saved['cycle']
    paths = {root/name for name in ('CONFIG.json', 'ACTIVATION.json', 'COUNTERS.json',
        'BROKER_CONFIG.json', 'LAUNCH.json', 'SHARED_CLIENT_READY.json')}
    paths.update(Path(saved[key]['path']) for key in ('carry', 'complete', 'readout', 'counters_file'))
    paths.update(root/'reservations'/name for name in saved['reservations'])
    paths.update((root/f'cycle{cycle:03d}').glob('*.json'))
    paths.update((root/'readouts'/f'cycle_{cycle:03d}').glob('*.json'))
    for directory in ('delivered', 'parent_queue'):
        paths.update((root/directory).glob(f'C{cycle:03d}_*.json'))
    require(all(path.resolve() == path and path.is_relative_to(root) for path in paths), 'own_absolute_preserved_files')
    preserved = {str(path.relative_to(root)): shared.sha(path) for path in sorted(paths)}
    document = dict(root=str(root), bounds=ready.bounds(), release=release_ref,
        predecessors=[release['actor'], release['supervisor']], preserved_files=preserved,
        next_cycle=saved['next_cycle'], completed_cycle=cycle, counters=saved['counters'],
        source_mode='FROZEN_BASE_CONTEXT_ONLY', prior_local_optimizer_steps=0,
        no_replay_or_quota_reset=True, empty_successor=saved['empty_successor'])
    path = root/'R118_SHARED_HANDOFF_BRANCH.json'
    if path.exists():
        previous = shared.read(path)
        require({key:value for key,value in previous.items() if key != 'published_unix'} == document,
            'immutable_branch_handoff')
        return previous
    document['published_unix'] = time.time()
    shared.write(path, document)
    return document


def wait(root, deadline):
    root = Path(root)
    require(time.time() < deadline <= ready.math.HARD, 'bounded_certificate_wait')
    output = root/'shared_handoff_r118'/'release'
    while time.time() < deadline:
        require(not (output/'ERROR.json').exists(), 'boundary_failure_requires_explicit_recovery')
        if (output/'RELEASED.json').exists():
            return publish(root)
        time.sleep(min(1, max(0, deadline-time.time())))
    raise TimeoutError('no_actual_release_certificate_not_written')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--wait-until', type=float)
    args = parser.parse_args()
    result = wait(args.root, args.wait_until) if args.wait_until else publish(args.root)
    print(result['root'], result['completed_cycle'], result['next_cycle'], result['counters'])
