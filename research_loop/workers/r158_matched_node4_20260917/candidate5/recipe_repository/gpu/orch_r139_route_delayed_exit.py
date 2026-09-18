"""Resume a verified saved handoff after its original actor exits late."""

import argparse
import fcntl
import importlib.util
from pathlib import Path
import time


HANDOFF_SHA = '22b251d95498fa946d79aed690284c20fc5a2b9f70bb1f2597dde70944ab7fba'


def settle(handoff, stage, proc_root=Path('/proc')):
    stage = Path(stage)
    manifest, permission = handoff.authorize(stage)
    handoff.require(not (proc_root / str(manifest['actor']['pid'])).exists(), 'original_actor_still_present')
    handoff.require(not (stage / 'LAUNCH.json').exists(), 'successor_already_launched')
    handoff.require(not (stage / 'RELEASED.json').exists(), 'release_already_recorded')
    boundary = handoff.read(stage / 'BOUNDARY.json')
    handoff.require(boundary['root'] == str(handoff.ROOT), 'original_root_required')
    handoff.require(boundary['logical_life_reset'] is False, 'no_reset_required')
    for path, expected in boundary['preserved'].items():
        handoff.require(handoff.sha(path) == expected, 'boundary_data_changed_after_delayed_exit')
    handoff.bound(boundary['checkpoint'])
    handoff.require(handoff.sha(boundary['optimizer_rng']['path']) == boundary['optimizer_rng']['sha256'],
                    'optimizer_rng_changed')
    handoff.write(stage / 'RELEASED.json', dict(status='RELEASED', boundary=handoff.ref(stage / 'BOUNDARY.json'),
        actor=manifest['actor'], released_unix=time.time(), no_force_kill=True,
        old_signal_crash_receipt_expected=True, logical_life_reset=False, delayed_exit_verified=True,
        recovery_source=handoff.ref(__file__), new_signals=0))
    return dict(status='RELEASED', next_cycle=boundary['next_cycle'], sleeps=boundary['sleeps'],
                checkpoint=boundary['checkpoint'], release=handoff.ref(stage / 'RELEASED.json'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--python', required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('frozen_handoff', args.stage / 'handoff.py')
    handoff = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(handoff)
    handoff.require(handoff.sha(args.stage / 'handoff.py') == HANDOFF_SHA, 'frozen_handoff_pin')
    with (args.stage / 'CONTROLLER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        handoff.release = lambda stage: settle(handoff, stage)
        result = handoff.supervise(args.stage, args.python)
        print(result)


if __name__ == '__main__':
    main()
