"""Publish lease-derived GRID owners; binding never launches processes."""

import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

from gpu import orch_r119_grid_shared_continue as runtime


def clock():
    path = runtime.CLOCK_SOURCE / 'gpu/orch_r119_lease_clock.py'
    spec = importlib.util.spec_from_file_location('grid_shared_lease', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate(runtime.CLOCK,
        backend_path=runtime.CLOCK_SOURCE / 'gpu/orch_r118_parallel_consolidation.py')


def prepare(branch):
    root = Path('/localhome/local-rohing/orch_r115_grid_pair_20260915') / branch
    previous = runtime.ref(root / 'parallel_recovery_1624/FRESH_OWNER_FINAL.json')
    owner = runtime.read(previous)
    plan = runtime.read(owner['runtime_plan'])
    bounds = clock()
    output = root / 'shared_continuation_r119'
    runtime.require(not output.exists(), 'new_immutable_execution_era')
    sources = deepcopy(owner['source_files'])
    for directory in (runtime.SOURCE / 'gpu', runtime.CLOCK_SOURCE / 'gpu'):
        for path in directory.glob('*.py'):
            sources[str(path)] = runtime.ref(path)['sha256']
    for name, digest in sources.items():
        runtime.require(runtime.ref(name)['sha256'] == digest, 'frozen_source:' + name)
    candidate = dict(schema='R118_GRID_PARALLEL_CANDIDATE_V1', status='CPU_ONLY_NOT_ARMED',
        source_files=sources, activation_authorized=False, completed_FINAL_no_rearm=True,
        clock=runtime.CLOCK, prior_candidate=plan['candidate'])
    candidate_ref = runtime.write(output / 'CANDIDATE.json', candidate)
    old_handoff = runtime.read(owner['handoff'])
    envelope = deepcopy(old_handoff)
    envelope['bounds'] = dict(envelope['bounds'], hard_end_unix=bounds['hard_end_unix'],
                              train_end_unix=bounds['train_end_unix'])
    envelope.update(continuation_clock=runtime.CLOCK, predecessor_handoff=owner['handoff'],
        continuation_scope='LEASE_CLOCK_ONLY_ORIGINAL_RELEASE_PRESERVED')
    handoff = runtime.write(output / 'HANDOFF.json', envelope)
    plan.update(directory=str(output), campaign=None, candidate=candidate_ref,
        bounds=runtime.overlay(plan['bounds'], bounds), continuation_clock=runtime.CLOCK,
        completed_final=runtime.final_metadata(branch), previous_owner=previous)
    prepared_plan = runtime.write(output / 'PREPARED_PLAN.json', plan)
    environment = dict(owner['env'], ORCH_R119_LEASE_CLOCK=runtime.CLOCK['path'],
        ORCH_R119_LEASE_CLOCK_SHA256=runtime.CLOCK['sha256'])
    owner.update(handoff=handoff, inherited_bounds=envelope['bounds'], source_files=sources,
        bootstrap_path=str(output / 'BOOTSTRAP.json'), env=environment,
        runtime_plan=prepared_plan, runtime_staged=False, GPU_started=False,
        command=[sys.executable, '-B', str(runtime.SOURCE / 'gpu/orch_r119_grid_shared_continue.py'),
            'guard', '--plan', prepared_plan['path'], '--sha256', prepared_plan['sha256']])
    owner_ref = runtime.write(output / 'OWNER_PREPARED.json', owner)
    return runtime.write(output / 'PREPARED_EXPORT.json', dict(owner=owner_ref,
        plan=prepared_plan, source_files=runtime.write(output / 'SOURCE_FILES.json', sources),
        common_campaign_bind_required=True, GPU_started=False, original_FINAL_calls=8,
        old_ledger=runtime.ref(root / 'LEDGER.jsonl'), old_carry=runtime.ref(root / 'CARRY.json')))


def bind(owner_ref, campaign_ref):
    owner, campaign = runtime.read(owner_ref), runtime.read(campaign_ref)
    plan = runtime.read(owner['runtime_plan'])
    runtime.require(plan['campaign'] is None and campaign['root'] == plan['common_root']
        and campaign['first_generation'] == 1, 'new_Main_campaign_gen1_no_reset')
    clock()
    runtime.require(all(campaign['source_files'].get(name) == digest
        for name, digest in owner['source_files'].items()), 'campaign_includes_GRID_source_closure')
    plan['campaign'] = campaign_ref
    reference = runtime.write(Path(plan['directory']) / 'PLAN.json', plan)
    owner.update(runtime_plan=reference, runtime_staged=True,
        command=[sys.executable, '-B', str(runtime.SOURCE / 'gpu/orch_r119_grid_shared_continue.py'),
                 'guard', '--plan', reference['path'], '--sha256', reference['sha256']])
    return runtime.write(Path(plan['directory']) / 'OWNER.json', owner)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'bind'))
    parser.add_argument('--branch', choices=('F4', 'A4'))
    parser.add_argument('--owner')
    parser.add_argument('--owner-sha256')
    parser.add_argument('--campaign')
    parser.add_argument('--campaign-sha256')
    args = parser.parse_args()
    if args.mode == 'prepare':
        result = prepare(args.branch)
    else:
        result = bind(dict(path=args.owner, sha256=args.owner_sha256),
                      dict(path=args.campaign, sha256=args.campaign_sha256))
    print(json.dumps(result))
