"""Future A4 broker era; preserves all repaired-serial requests and captures."""

import argparse
from pathlib import Path
import shlex
from types import FunctionType

from gpu import orch_r118_a4_repair_broker as prior


TERMINAL = 'R118_GRID_PARALLEL_TERMINAL.json'


def validate_handoff(envelope, release, root):
    require = prior.transport.require
    require(envelope['status'] == release['status'] == 'RELEASED' and
            envelope['root'] == release['root'] == str(root), 'actual_owned_A4_release')
    require(release['original_FAILED_preserved'] is True and release['calls_replayed'] == 0 and
            release['parent_claims_discarded'] == 0, 'no_old_capture_replay_or_discard')
    bounds = envelope['bounds']
    require(bounds == release['bounds'] and bounds['parent_cap'] == 298 and bounds['native_cap'] == 1858 and
            bounds['hard_end_unix'] == 1789491720 and bounds['train_end_unix'] == 1789491300,
            'same_A4_caps_deadlines')
    require(type(bounds['parent_used']) is int and 0 <= bounds['parent_used'] <= 298, 'actual_old_parent_count')
    return bounds['parent_used']


def historical(name, cutoff):
    return name in {f'P{number:04d}.request.json' for number in range(1, cutoff + 1)}


def serve(config_path, launch_path, prompt_root, principles_path, handoff_path, handoff_sha256):
    transport = prior.transport
    store = transport.Store(transport.ROOT)
    root = prior.prior.ROOT
    handoff_path = Path(handoff_path)
    transport.require(handoff_path.is_absolute() and handoff_path.is_relative_to(root), 'own_node_handoff_only')
    transport.require(store.hash(handoff_path) == handoff_sha256, 'exact_Main_bound_handoff')
    envelope = transport.loads(store.shell('cat ' + shlex.quote(str(handoff_path))).stdout)
    reference = envelope['release']
    transport.require(Path(reference['path']).is_relative_to(root) and
                      store.hash(Path(reference['path'])) == reference['sha256'], 'actual_release_reference')
    release = transport.loads(store.shell('cat ' + shlex.quote(reference['path'])).stdout)
    cutoff = validate_handoff(envelope, release, root)
    namespace = dict(prior.serve.__globals__, TERMINAL=TERMINAL,
                     historical=lambda name:historical(name, cutoff))
    return FunctionType(prior.serve.__code__, namespace, 'prospective_A4_parallel_broker',
                        prior.serve.__defaults__)(config_path, launch_path, prompt_root, principles_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'launch-receipt', 'prompt-root', 'principles', 'handoff'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--handoff-sha256', required=True)
    args = parser.parse_args()
    serve(args.config, args.launch_receipt, args.prompt_root, args.principles,
          args.handoff, args.handoff_sha256)
