"""CPU-only immutable source copy for the one declared R170 existing life."""

import hashlib
import importlib.util
import json
from pathlib import Path
import time


HERE = Path(__file__).resolve().parent
BOOTSTRAP = HERE.parents[2]
STAGE = Path('/localhome/local-rohing/orch_r170_creative_replay_20260917_attempt1')
OLD_GUARD = Path('/localhome/local-rohing/orch_r144_node3_target_physical1_20260916t1545z_5/GUARD.json')
OLD_GUARD_SHA256 = '8bbb6c007083884574b427b318ef3e466f26e514452b5ee5e7972801aca8ce9d'
SCOPE_SHA256 = '20743f990b673875241023681d811b4e24eefb32a1546174065353648928356b'


def main():
    scope_path = HERE / 'SCOPE.json'
    assert hashlib.sha256(scope_path.read_bytes()).hexdigest() == SCOPE_SHA256, 'exact_builder_scope'
    assert hashlib.sha256(OLD_GUARD.read_bytes()).hexdigest() == OLD_GUARD_SHA256, 'exact_old_guard'
    assert BOOTSTRAP == STAGE / 'bootstrap', 'one_bootstrap_location'
    guard = json.loads(OLD_GUARD.read_bytes())
    specification = importlib.util.spec_from_file_location('r170_assembly', HERE / 'ASSEMBLY.py')
    assembly = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(assembly)
    result = assembly.scaffold_immutable_files(
        old_guard_ref=dict(path=str(OLD_GUARD), sha256=OLD_GUARD_SHA256),
        old_plan_ref=dict(path=guard['plan_path'], sha256=guard['plan_sha256']),
        new_source_root=STAGE / 'physical1/source', output_root=STAGE / 'physical1',
        approved_intake_sha256=SCOPE_SHA256, now=time.time(), helper_source_root=BOOTSTRAP)
    print(json.dumps(dict(status='SOURCE_SCAFFOLDED_CPU_ONLY', scaffold_ref=result['scaffold_ref'],
                          source_root=result['source_root'], source_files=len(result['source_pins']),
                          plan_ref=result['plan_ref'], main_go_created=False,
                          signals_sent=0, gpu_used=False, model_called=False), sort_keys=True))


if __name__ == '__main__':
    main()
