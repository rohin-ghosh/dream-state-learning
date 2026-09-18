"""Read-only original-owner validation before any R170 selection or handoff."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time


HERE = Path(__file__).resolve().parent
STAGE = Path('/localhome/local-rohing/orch_r170_creative_replay_20260917_attempt1')
EXPECTED_PID = 1266769
EXPECTED_TICKS = '28048014'
DEPENDENCIES = {
    'OPERATOR.py': 'e2c0307936d8be5cde38633464641e921761369bf5c2ca3f65f960f69dbdd69f',
    'OPERATOR_RECOVERY_V2.py': '1a9b78c6044014ad1b69929e9a65cd34bbdc79130c77861a4152491f072f0dd4',
    'RECOVERY.py': '4864af9e8e21aa3fa5fc0b141bddbb09900908aabf52d8141a730375b3c7553a',
    'FAMILY.py': '014e23e330db36f0ef6a8da23f75084a7685e7e0663a1e9540759dac7fc0da5c',
    'BOUNDARY_API.py': 'f128becb34d95b6875e4283baa49b3504e2c6c589e67b93e858e07c98f593e60',
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checked_bytes(path, checksum):
    require(path.resolve() == path and path.is_file() and not path.is_symlink(),
            'canonical_dependency')
    require(path.stat().st_size <= 1024 * 1024, 'bounded_dependency')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == checksum, 'pinned_dependency')
    return raw


def load_operator():
    require(HERE == STAGE / 'bootstrap/research_loop/workers/r170_replay_boundary_20260917',
            'exact_bootstrap_location')
    for name, checksum in DEPENDENCIES.items():
        checked_bytes(HERE / name, checksum)
    specification = importlib.util.spec_from_file_location('r170_lifecycle_v2',
        HERE / 'OPERATOR_RECOVERY_V2.py')
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module.adapter_namespace()


def observe(adapter, now):
    family = adapter['family_namespace']()
    helper = family['api']()
    config_path = adapter['OLD_GUARD']
    config, plan, original = family['old_modules'](config_path)
    require(plan['hard_end_unix'] - now > 900, 'original_wall_margin')
    before = family['old_processes'](EXPECTED_PID, config_path, config, plan)
    require(before['actor']['pid'] == EXPECTED_PID
            and before['actor']['start_ticks'] == EXPECTED_TICKS, 'exact_original_instance')
    saved = original.saved.sleep_boundary(plan['root'])
    after = family['old_processes'](EXPECTED_PID, config_path, config, plan)
    require(before == after, 'stable_original_topology')
    return dict(schema='R170_LIFECYCLE_TOPOLOGY_PREPARATION_V1', observed_unix=now,
        lanes=[dict(physical=1, live=True, guard_path=str(config_path),
                    guard_sha256=helper.sha(config_path), processes=after)],
        hard_end_unix=plan['hard_end_unix'], source_root=plan['source_root'],
        head_completed_cycle=None if saved is None else saved['cycle'],
        source_validation='ORIGINAL_GUARD_AND_FULL_PINS_VALIDATED',
        signals_sent=0, model_calls=0, selection_created=False, main_go_created=False,
        source_ready_only=True, saved_state_handoff_authorized=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    require(arguments.output == STAGE / 'INVENTORY.json' and not arguments.output.exists(),
            'fresh_exact_inventory_only')
    result = observe(load_operator(), time.time())
    with arguments.output.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
