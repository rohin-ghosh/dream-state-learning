"""Read-only gen7 handover checks; never signal, stop, or launch a process."""

import argparse
import json
from pathlib import Path

try:
    import orch_r109_l1_generation_v3 as generation
except ImportError:
    from gpu import orch_r109_l1_generation_v3 as generation


PHYSICAL = 7
UUID = 'GPU-7c213554-a6c0-5c5a-1117-0422c8eee4ed'


def boundary_status(directory):
    directory = Path(directory)
    candidate, progress = generation.complete_boundary(directory)
    result = dict(candidate=False, release_authorized=False,
                  requires_stopped_identity_bound_recheck=True, progress=progress)
    if not candidate:
        return dict(result, reason='pending_next_call_or_failure_or_missing_capture')
    count = progress['calls']
    inherited = progress['inherited_calls']
    if count <= inherited or progress['new_segment_calls'] != count - inherited:
        return dict(result, reason='inherited_counter_mismatch')
    expected = set(range(inherited + 1, count + 1))
    for label in ('CALL', 'INTENT'):
        actual = {int(path.stem.split('_')[1]) for path in directory.glob(label + '_*.json')}
        if actual != expected:
            return dict(result, reason=label.lower() + '_inventory_not_contiguous')
    last = generation.read(directory / f'CALL_{count:06d}.json')
    if last['cumulative_call'] != count:
        return dict(result, reason='last_capture_counter_mismatch')
    if last['family'] == 'route':
        episode = directory / ('EPISODE_%04d_%02d.json' % (progress['batch'], progress['position']))
        if not episode.is_file():
            return dict(result, reason='route_episode_not_persisted')
    after = generation.read(directory / 'PROGRESS.json')
    if after != progress or (directory / f'INTENT_{count+1:06d}.json').exists():
        return dict(result, reason='live_boundary_moved')
    return dict(result, candidate=True, reason='complete_task_candidate_not_release',
                new_response_count=count-inherited, inherited_count=inherited,
                next_cursor=dict(batch=progress['batch'], position=progress['position']+2),
                next_call=count+1)


def admission_status(service_path):
    from gpu.orch_rich_hot_node2_scan import scan
    report = scan(PHYSICAL, Path(service_path))
    if report['scanner_euid'] != 0 or report['gpu']['uuid'] != UUID:
        raise ValueError('privileged_exact_uuid_admission_required')
    return dict(clear=report['clear'], blocking_reasons=report['blocking_reasons'],
                scanner_euid=report['scanner_euid'], uuid=report['gpu']['uuid'],
                physical=PHYSICAL, release_authorized=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inspect', 'admission'))
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--service', type=Path)
    options = parser.parse_args()
    if options.action == 'inspect':
        if options.directory is None:
            parser.error('--directory required')
        print(json.dumps(boundary_status(options.directory)))
    else:
        if options.service is None:
            parser.error('--service required')
        print(json.dumps(admission_status(options.service)))
