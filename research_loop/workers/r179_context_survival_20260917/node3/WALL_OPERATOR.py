"""Separate existing-lease continuation plus exact R179 source; saved boundary only."""

import argparse
import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD_ROOT = Path('/localhome/local-rohing/orch_r179_node3_context_20260917t1715z_1')
OLD_BOOTSTRAP = OLD_ROOT / 'bootstrap'
ADAPTER_SHA = '936be4e977f2ef27ab12e98afdfd420f7343b23347d7b6b4e83b61e228042030'
AUTH_SHA = 'e74fe583bc75cb8e02e67abd13e570f199bdfc9dcd578f9e6765e600b86ea7c2'
LEASE_SHA = '919e9fb3f9cfd6cadb57af90844319e50eb114068eb52cd75aa3ab715f9c3770'
OLD_WALL = 1789668000
NEW_WALL = 1789689000
CEILING = 1789689600


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path == path.resolve(), 'canonical_path')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def proposed_plan(old, source, saved):
    require(old['hard_end_unix'] == saved['state']['deadline_unix'] == OLD_WALL
            and old['lease_end_unix'] == CEILING, 'exact_existing_wall_ceiling')
    result = deepcopy(old)
    result.update(source_root=str(source), hard_end_unix=NEW_WALL,
        authorized_wall_extension=dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1',
            previous_deadline_unix=OLD_WALL, previous_stream_sha256=saved['state_sha256'],
            new_deadline_unix=NEW_WALL, lease_end_unix=CEILING, safety_margin_seconds=600))
    if old.get('startup_context'):
        relative = Path(old['startup_context']['path']).relative_to(old['source_root'])
        result['startup_context']['path'] = str(Path(source) / relative)
    return result


def wall_plan_delta(original_delta, old, new):
    normalized = deepcopy(new)
    authorization = normalized.pop('authorized_wall_extension')
    require(set(authorization) == {'schema', 'previous_deadline_unix', 'previous_stream_sha256',
            'new_deadline_unix', 'lease_end_unix', 'safety_margin_seconds'}
            and authorization['schema'] == 'R131_SAVED_STATE_WALL_EXTENSION_V1'
            and authorization['previous_deadline_unix'] == old['hard_end_unix'] == OLD_WALL
            and authorization['new_deadline_unix'] == new['hard_end_unix'] == NEW_WALL
            and authorization['lease_end_unix'] == new['lease_end_unix'] == old['lease_end_unix'] == CEILING
            and authorization['safety_margin_seconds'] == 600
            and re.fullmatch(r'[0-9a-f]{64}', authorization['previous_stream_sha256']), 'exact_wall_extension_fields')
    normalized['hard_end_unix'] = old['hard_end_unix']
    original_delta(old, normalized)


def wall_guard_delta(original_delta, old, new):
    require(old['hard_end_unix'] == OLD_WALL and new['hard_end_unix'] == NEW_WALL
            and new['next_reserved_unix'] == old['next_reserved_unix'] == CEILING
            and old['lease_sha256'] == LEASE_SHA and sha(old['lease_path']) == LEASE_SHA, 'same_existing_lease_ceiling')
    lease = read(old['lease_path'])
    require(lease['lease_end_unix'] == CEILING and lease['hard_end_unix'] == OLD_WALL, 'old_internal_budget_not_machine_extension')
    expected = dict(schema='R131_EXISTING_LEASE_RUNTIME_BUDGET_V1', authority_path=str(HERE / 'CONTINUATION.md'),
        authority_sha256=AUTH_SHA, previous_receipt_path=old['lease_path'], previous_receipt_sha256=LEASE_SHA,
        lease_end_unix=CEILING, hard_end_unix=NEW_WALL, safety_margin_seconds=600, lease_extended=False)
    require(read(new['lease_path']) == expected and sha(new['lease_path']) == new['lease_sha256'], 'exact_new_runtime_budget')
    normalized = deepcopy(new)
    for key in ('hard_end_unix', 'lease_path', 'lease_sha256'):
        normalized[key] = old[key]
    original_delta(old, normalized)


def handoff_source(source):
    tree = ast.parse(source)
    handoff = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'handoff')
    matches = [node for node in ast.walk(handoff) if isinstance(node, ast.Constant) and node.value == 900]
    require(len(matches) == 1, 'single_old_cutoff_constant')
    matches[0].value = 180
    return ast.unparse(tree)


def family_namespace():
    require(sha(HERE / 'CONTINUATION.md') == AUTH_SHA and sha(OLD_BOOTSTRAP / 'OPERATOR.py') == ADAPTER_SHA,
            'exact_separate_authority_and_prior_adapter')
    adapter = dict(__name__='r179_wall_private_adapter', __file__=str(Path(__file__).resolve()))
    exec(compile((OLD_BOOTSTRAP / 'OPERATOR.py').read_bytes(), str(__file__), 'exec'), adapter)
    adapter.update(HERE=OLD_BOOTSTRAP, ROOT=OLD_ROOT)
    family = adapter['family_namespace']()
    original_plan_delta, original_guard_delta = family['plan_delta'], family['guard_delta']
    family['plan_delta'] = lambda old, new: wall_plan_delta(original_plan_delta, old, new)
    family['guard_delta'] = lambda old, new: wall_guard_delta(original_guard_delta, old, new)
    adapter['load']('RECOVERY_ADAPTER.py').repaired_handoff(family,
        handoff_source((OLD_BOOTSTRAP / 'FAMILY.py').read_bytes()))
    original_saved = family['saved_evidence']
    def saved_evidence(plan, saved, original):
        evidence = original_saved(plan, saved, original)
        bound = family.get('selected_state_sha256')
        if bound is not None:
            require(saved['state_sha256'] == bound, 'selected_actual_boundary_no_catchup')
        return evidence
    family['saved_evidence'] = saved_evidence
    original_monitor = family['monitor']
    def monitor(output, saved, unlock):
        result = original_monitor(output, saved, unlock)
        if result.get('status') != 'SUCCESSOR_EXACT_STATE_LOADED':
            return result
        helper = family['api']()
        proof = helper.read(output / 'STATE_CPU.json')
        loaded = Path(result['record_path']).name
        matches = []
        for path in sorted((Path(helper.read(helper.read(output / 'GUARD.json')['plan_path'])['root']) / 'stream/records').glob('*.json')):
            if re.fullmatch(r'\d{20}\.json', path.name) and Path(saved['record_path']).name < path.name < loaded:
                record = helper.read(path)
                if record['kind'] == 'WALL_EXTENDED':
                    require(record['document'] == proof['wall_record'] and record['sha256'] ==
                        helper.digest({key: value for key, value in record.items() if key != 'sha256'}), 'exact_actual_wall_event')
                    matches.append(dict(path=str(path), sha256=helper.sha(path)))
        require(len(matches) == 1, 'one_actual_wall_extension_before_loaded')
        result.update(status='WALL_EXTENDED_AND_R179_SOURCE_LOADED', wall_event=matches[0], hard_end_unix=NEW_WALL,
            lease_end_unix=CEILING, authority_sha256=AUTH_SHA, uninterrupted_saved_boundary=True)
        helper.write(output / 'WALL_LOADED_RECEIPT.json', result)
        return result
    family['monitor'] = monitor
    return family, adapter


def state_cpu(output):
    config = read(output / 'GUARD.json')
    plan = read(config['plan_path'])
    sys.path.insert(0, plan['source_root'])
    from gpu import orch_r125_continual_native as native
    import random
    import torch
    torch.set_num_threads(1)
    native.require(Path(native.__file__).resolve() == Path(plan['source_root']) / 'gpu/orch_r125_continual_native.py',
                   'actual_candidate_native')
    boundary = read(output / 'SAVED.json')
    envelope = dict(state=boundary['state'], sha256=boundary['state_sha256'])
    stream = native.ContinualStream.restore(envelope, expected_sha256=envelope['sha256'])
    commit = Path(plan['root']) / 'checkpoints' / ('sleep_%06d' % boundary['cycle']) / 'COMMIT.json'
    checkpoint = native.read(commit)
    native.NativeChild.verify_checkpoint(checkpoint)
    require(native.digest(checkpoint['checkpoint_sha256']) == stream.model_state_sha256, 'saved_adapter_optimizer_RNG_binding')
    payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == checkpoint['optimizer_steps'] > 0 and payload['optimizer']['state']
            and payload['optimizer']['param_groups'] and payload['parameter_names'], 'full_AdamW_not_reset')
    require(len(payload['cuda_rng']) == 1 and payload['cuda_rng'][0].device.type == 'cpu', 'one_saved_device_RNG')
    torch.Generator(device='cpu').set_state(payload['cpu_rng'])
    random.Random().setstate(payload['python_rng'])
    before = stream.checkpoint()
    extension = native.prepare_wall_extension(plan, stream, resume=True, plan_sha256=native.sha(config['plan_path']))
    require(stream.checkpoint() == before and extension['state']['state'] == dict(before['state'], deadline_unix=NEW_WALL),
            'only_deadline_changes_no_state_mutation')
    require(not torch.cuda.is_initialized(), 'CPU_only')
    return dict(status='PASS', wall_record=extension, optimizer_steps=checkpoint['optimizer_steps'],
        checkpoint_ref=dict(path=str(commit), sha256=sha(commit)), adapter_state_sha256=checkpoint['adapter_state_sha256'],
        native_sha256=sha(native.__file__), no_CUDA=True, no_reset=True, observed_unix=time.time())


def stage_boundary(family, adapter, physical, saved, output, historical):
    helper = family['api']()
    lane = adapter['lane_for'](physical)
    old_config, old_plan, original = family['old_modules'](lane['guard_ref']['path'])
    require(sha(HERE / 'CPU_LOCAL.json') == read(HERE / 'CPU_LOCAL_REF.json')['sha256'], 'new_CPU_receipt_bound')
    local_cpu = read(HERE / 'CPU_LOCAL.json')
    require(local_cpu['status'] == 'PASS' and local_cpu['operator_sha256'] == sha(__file__)
            and local_cpu['authority_sha256'] == AUTH_SHA, 'tested_specific_wall_operator')
    processes = family['old_processes'](lane['identity']['pid'], lane['guard_ref']['path'], old_config, old_plan)
    evidence = family['saved_evidence'](old_plan, saved, original)
    output.mkdir()
    helper.write(output / 'SAVED.json', saved)
    source_stage = OLD_ROOT / ('physical' + str(physical))
    plan = proposed_plan(old_plan, source_stage / 'source', saved)
    helper.write(output / 'PLAN.json', plan)
    helper.write(output / 'LEASE_BUDGET.json', dict(schema='R131_EXISTING_LEASE_RUNTIME_BUDGET_V1',
        authority_path=str(HERE / 'CONTINUATION.md'), authority_sha256=AUTH_SHA,
        previous_receipt_path=old_config['lease_path'], previous_receipt_sha256=LEASE_SHA,
        lease_end_unix=CEILING, hard_end_unix=NEW_WALL, safety_margin_seconds=600, lease_extended=False))
    helper.write(output / 'ALLOCATION.json', dict(helper.read(old_config['allocation_path']), plan_sha256=sha(output / 'PLAN.json')))
    config = family['readmission_guard'](old_config, old_plan, output / 'runtime')
    config.update(attempt_dir=str(output), plan_path=str(output / 'PLAN.json'), plan_sha256=sha(output / 'PLAN.json'),
        hard_end_unix=NEW_WALL, lease_path=str(output / 'LEASE_BUDGET.json'), lease_sha256=sha(output / 'LEASE_BUDGET.json'),
        allocation_path=str(output / 'ALLOCATION.json'), allocation_sha256=sha(output / 'ALLOCATION.json'),
        source_pins=helper.read(source_stage / 'PROPOSED_GUARD.json')['source_pins'])
    helper.write(output / 'GUARD.json', config)
    family['verify_source'](source_stage / 'PROPOSED_GUARD.json', old_config, old_plan, config, plan)
    validation = family['validate_fresh'](output / 'GUARD.json', plan['source_root'])
    require(validation['status'] == 'PASS', 'fresh_extended_guard_validator')
    helper.write(output / 'VALIDATED_NEW_SOURCE.json', validation)
    command = [str(helper.PYTHON), '-I', '-B', str(__file__), '--action', 'state-cpu', '--output', str(output)]
    proof = json.loads(subprocess.check_output(command, text=True, timeout=100, env=family['environment'](plan['source_root'])))
    helper.write(output / 'STATE_CPU.json', proof)
    helper.write(output / 'CPU.json', dict(status='PASS', operator_sha256=sha(__file__), authority_sha256=AUTH_SHA,
        local_cpu_path=str(HERE / 'CPU_LOCAL.json'), local_cpu_sha256=sha(HERE / 'CPU_LOCAL.json'),
        state_cpu_sha256=sha(output / 'STATE_CPU.json'), historical_only=historical, signals_sent=0))
    request = dict(physical=physical, old_config=lane['guard_ref']['path'], old_config_sha256=lane['guard_ref']['sha256'],
        new_config=str(output / 'GUARD.json'), new_config_sha256=sha(output / 'GUARD.json'), processes=processes,
        old_plan_sha256=old_config['plan_sha256'], plan_sha256=config['plan_sha256'], old_source=old_plan['source_root'],
        new_source=plan['source_root'], source_binding=str(source_stage / 'PROPOSED_GUARD.json'),
        cpu_path=str(output / 'CPU.json'), cpu_sha256=sha(output / 'CPU.json'), operator_path=str(Path(__file__).resolve()),
        operator_sha256=sha(__file__), authority_sha256=AUTH_SHA, selected_state_sha256=saved['state_sha256'],
        historical_only=historical, staged_unix=time.time(), signals_sent=0)
    helper.write(output / 'STAGED.json', request)
    device_command = [str(helper.PYTHON), '-B', str(__file__), '--action', 'device', '--output', str(output)]
    device = json.loads(subprocess.check_output(device_command, text=True, timeout=100, cwd=plan['source_root'],
        env=family['environment'](plan['source_root'])))
    require(device['status'] == 'PASS', 'actual_device_before_any_STOP')
    helper.write(output / 'BUILDER_LAUNCH_RECEIPT.json', dict(author='Builder/node3', observed_unix=time.time(),
        operator_sha256=sha(__file__), authority_sha256=AUTH_SHA, state_cpu_sha256=sha(output / 'STATE_CPU.json'),
        local_cpu_sha256=sha(HERE / 'CPU_LOCAL.json'), source_pins=config['source_pins'],
        device_sha256=sha(output / 'DEVICE_PREFLIGHT.json'), historical_only=historical, signals_sent=0))
    return dict(status='EXTENDED_SUCCESSOR_PREFLIGHT_PASS', physical=physical, output=str(output), historical_only=historical,
        selected_state_sha256=saved['state_sha256'], optimizer_steps=evidence['optimizer_steps'])


def run(physical, preflight):
    family, adapter = family_namespace()
    helper = family['api']()
    lane = adapter['lane_for'](physical)
    config, plan, original = family['old_modules'](lane['guard_ref']['path'])
    processes = family['old_processes'](lane['identity']['pid'], lane['guard_ref']['path'], config, plan)
    if preflight:
        records = sorted(path for path in (Path(plan['root']) / 'stream/records').glob('*.json')
                         if re.fullmatch(r'\d{20}\.json', path.name))
        for path in reversed(records):
            record = helper.read(path)
            if record['kind'] == 'SLEEP_COMPLETE':
                envelope = record['document']['resume_state']
                saved = dict(path=str(path), state=envelope['state'], state_sha256=envelope['sha256'], cycle=record['document']['cycle'])
                return stage_boundary(family, adapter, physical, saved, ROOT / ('preflight' + str(physical)), True)
        raise ValueError('historical_saved_protocol_missing')
    prior = ROOT / ('preflight' + str(physical))
    require(read(prior / 'CPU.json')['status'] == 'PASS' and read(prior / 'DEVICE_PREFLIGHT.json')['status'] == 'PASS',
            'actual_preflight_required')
    (ROOT / ('RUN_ONCE_' + str(physical))).mkdir()
    deadline = min(time.monotonic()+1200, time.monotonic()+OLD_WALL-time.time()-180)
    while time.monotonic() < deadline:
        saved = original.saved.sleep_boundary(plan['root'])
        if saved is not None and original.saved.readout_started(plan['root'], saved['cycle'],
                plan.get('readout_revision', 1), processes['timer']['pid']):
            output = ROOT / ('control' + str(physical))
            stage_boundary(family, adapter, physical, saved, output, False)
            require(original.saved.sleep_boundary(plan['root']) == saved, 'actual_boundary_moved_no_pause')
            family['selected_state_sha256'] = saved['state_sha256']
            return family['handoff'](output, 1200)
        time.sleep(.25)
    result = dict(status='NO_CLEAN_BOUNDARY_BEFORE_OLD_WALL_MARGIN', physical=physical, observed_unix=time.time(),
        signals_sent=0, source_or_wall_applied=False, recovery_not_inferred=True)
    helper.write(ROOT / ('NO_BOUNDARY_' + str(physical) + '.json'), result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', choices=('preflight', 'run', 'state-cpu', 'validate', 'device', 'supervise', 'contained'), required=True)
    parser.add_argument('--physical', type=int, choices=(0, 1, 2, 3, 4, 7))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.action == 'state-cpu':
        result = state_cpu(args.output)
    elif args.action in ('preflight', 'run'):
        result = run(args.physical, args.action == 'preflight')
    else:
        family, adapter = family_namespace()
        if args.action == 'validate':
            result = family['validate_new'](args.output)
        elif args.action == 'device':
            result = adapter['device_preflight'](family, args.output)
        else:
            try:
                require(read(args.output / 'STAGED.json')['historical_only'] is False, 'never_dispatch_CPU_fixture')
                result = family[args.action](args.output)
            except BaseException as error:
                family['api']().write(args.output / 'SUPERVISOR_FAILED.json', dict(error=str(error),
                    error_type=type(error).__name__, observed_unix=time.time(), no_retry=True))
                raise
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
