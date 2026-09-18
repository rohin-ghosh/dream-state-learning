"""Create only the reviewed R170 source scaffold; no learner or GPU actions."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time


HERE = Path(__file__).resolve().parent
BOOTSTRAP = HERE.parents[2]
STAGE = Path('/localhome/local-rohing/orch_r170_creative_replay_20260917_attempt1')
SCOPE_SHA256 = '20743f990b673875241023681d811b4e24eefb32a1546174065353648928356b'
GUARD_REF = dict(
    path='/localhome/local-rohing/orch_r144_node3_target_physical1_20260916t1545z_5/GUARD.json',
    sha256='8bbb6c007083884574b427b318ef3e466f26e514452b5ee5e7972801aca8ce9d')


def execute(approval_ref, assembly_sha256):
    if (BOOTSTRAP != STAGE / 'bootstrap'
            or hashlib.sha256((HERE / 'SCOPE.json').read_bytes()).hexdigest() != SCOPE_SHA256
            or hashlib.sha256((HERE / 'ASSEMBLY_V2.py').read_bytes()).hexdigest() != assembly_sha256):
        raise ValueError('exact_scaffold_location_scope_and_source')
    specification = importlib.util.spec_from_file_location('r170_reviewed_assembly_v2', HERE / 'ASSEMBLY_V2.py')
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    assembly = module.assembly_namespace(approval_ref)
    approval = assembly['replay'].read_bound(approval_ref)
    if approval['old_guard_ref'] != GUARD_REF or approval['approved_intake_sha256'] != SCOPE_SHA256:
        raise ValueError('one_creative_life_Main_scope')
    result = assembly['scaffold_immutable_files'](
        old_guard_ref=GUARD_REF, old_plan_ref=approval['old_plan_ref'],
        new_source_root=STAGE / 'physical1/source', output_root=STAGE / 'physical1',
        approved_intake_sha256=SCOPE_SHA256, now=time.time(), helper_source_root=BOOTSTRAP,
        cpu_evidence_ref=approval['receiving_cpu_ref'])
    receipt = dict(status='REVIEWED_RECEIVING_SOURCE_SCAFFOLDED_CPU_ONLY',
        observed_unix=time.time(), scaffold_ref=result['scaffold_ref'],
        source_root=result['source_root'], source_files=len(result['source_pins']),
        plan_ref=result['plan_ref'], approval_ref=approval_ref,
        historical_cpu_ref=approval['historical_cpu_ref'],
        actual_receiving_cpu_ref=approval['receiving_cpu_ref'],
        independent_review_ref=approval['independent_review_ref'],
        assembly_sha256=assembly_sha256, main_go_created=False, signals_sent=0,
        gpu_used=False, model_called=False, targeted_dose_executed=False)
    assembly['_write'](STAGE / 'physical1/RECEIVING_GATE_BINDING.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--approval', required=True)
    parser.add_argument('--approval-sha256', required=True)
    parser.add_argument('--assembly-sha256', required=True)
    arguments = parser.parse_args()
    print(json.dumps(execute(dict(path=arguments.approval, sha256=arguments.approval_sha256),
                             arguments.assembly_sha256), sort_keys=True))
