"""Stage exact GRID dispatch plans; no process launch, signals, or selector access."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time


SOURCE = Path('/localhome/local-rohing/orch_r118_grid_parallel_candidate_source_20260915_v4')
EXPORT = Path('/localhome/local-rohing/orch_r118_grid_parallel_drain_20260915_1513')
RUNTIME = Path('/localhome/local-rohing/orch_r118_grid_shared_source_20260915_attempt2')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
BACKEND_SHA = 'c56bb57b69405877a65124b623316f9b8bd769aa8f51db6f2481ff65325c5cdb'
SELECTOR_PID = 1519259


def require(value, reason):
    if not value:
        raise ValueError(reason)


def ref(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def checked(reference):
    require(ref(reference['path']) == reference, 'exact_pinned_metadata')
    return json.loads(Path(reference['path']).read_bytes())


def write(path, document):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as output:
        json.dump(document, output, indent=2, sort_keys=True)
        output.write('\n')
    return ref(path)


def validate_campaign(campaign, owner, *, clock=time.time):
    require(campaign['root'] == owner['runtime_plan_bindings']['common_root'] and
            campaign['first_generation'] == 1, 'exact_gen1_COMMON_campaign')
    require(clock() < campaign['deadline_unix'] <= owner['inherited_bounds']['train_end_unix'],
            'original_training_deadline')
    require(all(campaign['source_files'].get(path) == digest
                for path, digest in owner['source_files'].items()), 'campaign_includes_exact_GRID_runtime_closure')


def assemble(owner, campaign_ref, final_ref, timer_identities, final_output):
    branch = owner['branch']
    require(branch in ('F4', 'A4'), 'owned_GRID_only')
    require(len(timer_identities) == 2 and len({item['pid'] for item in timer_identities}) == 2 and
            all(item['pid'] != SELECTOR_PID for item in timer_identities), 'two_own_timers_never_selector')
    plan = deepcopy(owner['runtime_plan_bindings'])
    plan.update(campaign=campaign_ref, previous_final_plan=final_ref,
                old_final_identities=deepcopy(timer_identities), final_output=str(final_output))
    require(Path(plan['directory']).is_relative_to(Path(owner['root'])) and
            not Path(final_output).is_relative_to(Path(owner['root'])), 'separate_eval_only_custody')
    return plan


def dispatch_owner(owner, plan_reference):
    result = {name:deepcopy(owner[name]) for name in
        ('branch', 'root', 'handoff', 'inherited_bounds', 'boundary', 'source_files', 'cwd', 'bootstrap_path', 'device')}
    result.update(command=[PYTHON, '-B', str(SOURCE / 'gpu/orch_r118_grid_parallel_run.py'),
        'guard', '--plan', plan_reference['path'], '--sha256', plan_reference['sha256']],
        env=dict(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                 PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(RUNTIME)),
        runtime_plan=plan_reference, runtime_staged=True, GPU_started=False)
    return result


def frozen_modules(owner):
    require(ref(SOURCE / 'gpu/orch_r118_parallel_consolidation.py')['sha256'] == BACKEND_SHA,
            'exact_final_c56_backend')
    spec = importlib.util.spec_from_file_location('GRID_frozen_stage_runtime',
                                                SOURCE / 'gpu/orch_r118_grid_parallel_run.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    handoff, unused = runner.modules(owner['runtime_plan_bindings'])
    return runner, handoff


def inspect_timers(branch, final_reference, process):
    expected = {'F4':(1533423,1533424), 'A4':(1533431,1533432)}[branch]
    result = []
    for pid in expected:
        require(pid != SELECTOR_PID, 'never_selector')
        identity = process.identity(pid)
        require(identity['uid'] == os.getuid() and identity['state'] not in ('Z', 'X'),
                'actual_live_owned_CPU_timer')
        directory = Path('/proc') / str(pid)
        command_bytes = (directory / 'cmdline').read_bytes()
        command = [part.decode() for part in command_bytes.split(b'\0') if part]
        require(command.count('--plan') == 1 and
                command[command.index('--plan') + 1] == final_reference['path'] and
                any(Path(part).name in ('orch_r118_grid_final.py', 'orch_r118_grid_final_drain.py')
                    for part in command) and 'readout' not in command, 'exact_own_FINAL_timer_command')
        require(b'CUDA_VISIBLE_DEVICES=' in (directory / 'environ').read_bytes().split(b'\0'),
                'CPU_only_FINAL_timer')
        result.append(dict(identity, command_sha256=hashlib.sha256(command_bytes).hexdigest()))
    return result


def prepare_final_custody(output):
    output = Path(output)
    require(not output.exists(), 'immutable_new_custody_receipt')
    records = {}
    for branch in ('F4', 'A4'):
        owner_path = EXPORT / (branch + '.FRESH_OWNER_INPUTS.json')
        owner = checked(ref(owner_path))
        runner, handoff = frozen_modules(owner)
        boundary = handoff.checked(owner['runtime_plan_bindings']['boundary'])
        handoff.validate_snapshot(boundary)
        for identity in handoff.checked(owner['handoff'])['predecessors']:
            handoff.parallel.predecessor_released(identity)
        final_path = Path('/localhome/local-rohing/orch_r118_grid_final_20260915_attempt2') / branch / 'PLAN.json'
        final_ref = ref(final_path)
        final, previous = runner.final_module(dict(previous_final_plan=final_ref))
        final.validate_plan(previous)
        require(previous['branch_root'] == owner['root'] and
                not (Path(previous['output']) / 'DISPATCH.json').exists(), 'same_own_unattempted_FINAL')
        from gpu import orch_r118_grid_final_drain as process
        records[branch] = dict(owner=ref(owner_path), previous_final_plan=final_ref,
            old_final_identities=inspect_timers(branch, final_ref, process),
            final_output=str(Path('/localhome/local-rohing/orch_r118_grid_final_parallel_20260915_attempt1') / branch))
        require(not Path(records[branch]['final_output']).exists(), 'new_uncreated_eval_output')
    return write(output, dict(schema='R118_GRID_FINAL_CUSTODY_STAGE_V1', status='PREPARED_NOT_REBOUND',
        branches=records, observed_unix=time.time(), selector_access=False, signals=0, GPU_starts=0))


def stage(campaign_ref, custody_ref, output):
    output = Path(output)
    require(not output.exists(), 'immutable_new_stage_export')
    custody = checked(custody_ref)
    require(custody['schema'] == 'R118_GRID_FINAL_CUSTODY_STAGE_V1' and
            set(custody['branches']) == {'F4','A4'}, 'exact_GRID_custody_receipt')
    owners = {}
    for branch in ('F4', 'A4'):
        record = custody['branches'][branch]
        owner = checked(record['owner'])
        runner, handoff = frozen_modules(owner)
        campaign, unused = handoff.parallel.campaign_document(campaign_ref['path'], campaign_ref['sha256'])
        validate_campaign(campaign, owner)
        boundary = handoff.checked(owner['runtime_plan_bindings']['boundary'])
        handoff.validate_snapshot(boundary)
        from gpu import orch_r118_grid_final_drain as process
        current = inspect_timers(branch, record['previous_final_plan'], process)
        for actual, expected in zip(current, record['old_final_identities']):
            require(process.same_process(actual, expected) and
                    actual['command_sha256'] == expected['command_sha256'], 'unchanged_FINAL_custody_identity')
        require(not Path(record['final_output']).exists(), 'FINAL_output_not_precreated_or_attempted')
        plan = assemble(owner, campaign_ref, record['previous_final_plan'], current, record['final_output'])
        plan_path = Path(plan['directory']) / 'PLAN.json'
        require(not (Path(plan['directory']) / 'GUARD_ONCE').exists(), 'no_preexisting_guard_run')
        plan_reference = write(plan_path, plan)
        final_owner = dispatch_owner(owner, plan_reference)
        owners[branch] = write(Path(plan['directory']) / 'FRESH_OWNER_FINAL.json', final_owner)
    return write(output, dict(schema='R118_GRID_FINAL_STAGE_V1', status='STAGED_NOT_DISPATCHED',
        campaign=campaign_ref, custody=custody_ref, owners=owners, observed_unix=time.time(),
        GPU_starts=0, provider_calls=0, signals=0, selector_access=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'stage'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--campaign', type=Path)
    parser.add_argument('--campaign-sha256')
    parser.add_argument('--custody', type=Path)
    parser.add_argument('--custody-sha256')
    args = parser.parse_args()
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_staging')
    if args.action == 'prepare':
        result = prepare_final_custody(args.output)
    else:
        require(all((args.campaign, args.campaign_sha256, args.custody, args.custody_sha256)),
                'actual_campaign_and_custody_pins_required')
        result = stage(dict(path=str(args.campaign), sha256=args.campaign_sha256),
            dict(path=str(args.custody), sha256=args.custody_sha256), args.output)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
