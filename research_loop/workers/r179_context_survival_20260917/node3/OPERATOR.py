"""Six exact current node3 lives, R179 source delta, original saved-state lifecycle."""

import argparse
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import uuid


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
POLICY_SHA = 'b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b'
SEED_SHA = 'abc34ff2fd357be87e399132f42ff8c8964b065f60e268ed171a95c3678983d4'
DEPENDENCIES = {
    'FAMILY.py': '014e23e330db36f0ef6a8da23f75084a7685e7e0663a1e9540759dac7fc0da5c',
    'BOUNDARY_API.py': 'f128becb34d95b6875e4283baa49b3504e2c6c589e67b93e858e07c98f593e60',
    'RECOVERY.py': '4864af9e8e21aa3fa5fc0b141bddbb09900908aabf52d8141a730375b3c7553a',
    'RECOVERY_ADAPTER.py': '1a9b78c6044014ad1b69929e9a65cd34bbdc79130c77861a4152491f072f0dd4',
    'POLICY.py': POLICY_SHA,
    'BUILDER_SCOPE.json': '85441db890036947f6bc242e66ef15db750a683d73fe02d06778ebe996d4fb54',
    'SEED.json': SEED_SHA,
}
NATIVE = 'gpu/orch_r125_continual_native.py'
POLICY = 'gpu/orch_r179_context_survival.py'
OLD_OPERATOR = Path('/localhome/local-rohing/orch_r144_node3_target_handoff_operator_20260916t1541z_5/OPERATOR.py')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path == path.resolve()
            and not any(part.is_symlink() for part in (path, *path.parents)), 'canonical_pin_path')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    sha(path)
    return json.loads(Path(path).read_text())


def load(name):
    require(sha(HERE / name) == DEPENDENCIES[name], 'pinned_dependency:' + name)
    spec = importlib.util.spec_from_file_location('r179_' + name.replace('.', '_'), HERE / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lane_for(physical):
    require(sha(HERE / 'SEED.json') == SEED_SHA, 'exact_six_inventory')
    require(type(physical) is int and physical in (0, 1, 2, 3, 4, 7), 'node3_six_only')
    return next(row for row in read(HERE / 'SEED.json')['lanes'] if row['physical'] == physical)


def scope(plan):
    lane = lane_for(plan['physical'])
    require(sha(lane['plan_ref']['path']) == lane['plan_ref']['sha256'], 'original_plan_pin')
    require(plan == read(lane['plan_ref']['path']), 'exact_whole_current_plan')
    require(plan['root'] == lane['life_root'] and plan['source_root'] == lane['source_root']
            and plan['gpu_uuid'] == lane['gpu_uuid'], 'current_life_source_device')
    require(not plan.get('preupdate_recovery') and not plan.get('authorized_wall_extension'), 'no_recovery_or_wall_change')
    return plan['physical']


def current_direct_processes(helper, pid, config_path, config, plan):
    lane = lane_for(scope(plan))
    require(plan['physical'] in (0, 2), 'current_direct_contained_only')
    actor = helper.process_record(pid)
    timer = helper.process_record(actor['parent'])
    supervisor = helper.process_record(timer['parent'])
    expected = [str(helper.PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(config_path)]
    require(actor['argv'] == expected, 'exact_native_argv')
    require(timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
            and len(timer['argv']) == 11 and re.fullmatch(r'[1-9][0-9]*s', timer['argv'][3])
            and timer['argv'][4:] == expected, 'exact_timer_argv')
    require(sha(OLD_OPERATOR) == DEPENDENCIES['FAMILY.py'], 'actual_contained_supervisor_source')
    require(supervisor['argv'] == [str(helper.PYTHON), '-B', str(OLD_OPERATOR), '--action', 'contained',
            '--output', str(Path(config_path).parent)], 'exact_existing_contained_supervisor')
    require(actor['pid'] == lane['identity']['pid'] and actor['start_ticks'] == lane['identity']['start_ticks'],
            'exact_current_actor_identity')
    policy = config['device_containment']
    for process in (actor, timer, supervisor):
        require(process['uid'] == os.getuid() == policy['uid'] and process['cwd'] == plan['source_root']
                and process['cvd'] == [plan['gpu_uuid']] and process['cgroup'] ==
                '0::/system.slice/' + policy['unit'] + '.service', 'exact_owned_contained_topology')
    require(actor['group'] == timer['group'] == timer['pid'] and supervisor['group'] == supervisor['pid']
            and supervisor['parent'] == 1, 'exact_groups_no_foreign_supervisor')
    launch = helper.read(Path(config['attempt_dir']) / 'LAUNCH.json')
    require(launch['pid'] == timer['pid'] and launch['parent_start_ticks'] == timer['start_ticks']
            and launch['guard_sha256'] == helper.sha(config_path) and launch['plan_sha256'] == config['plan_sha256'],
            'original_launch_binding')
    return dict(actor=actor, timer=timer, supervisor=supervisor)


def source_pins(source):
    return {str(path.relative_to(source)): sha(path) for path in sorted(source.rglob('*.py'))}


def verify_source(family, binding, old_config, old_plan, new_config, new_plan):
    physical = scope(old_plan)
    lane = lane_for(physical)
    require(sha(lane['guard_ref']['path']) == lane['guard_ref']['sha256']
            and old_config == read(lane['guard_ref']['path']), 'exact_current_guard')
    target = ROOT / ('physical' + str(physical))
    destination = target / 'source'
    require(new_plan['source_root'] == str(destination) and Path(binding) == target / 'PROPOSED_GUARD.json',
            'single_staged_destination')
    family['plan_delta'](old_plan, new_plan)
    family['guard_delta'](old_config, new_config)
    original = Path(old_plan['source_root'])
    require(source_pins(original) == old_config['source_pins'], 'entire_original_source')
    require(POLICY not in old_config['source_pins'] and old_config['source_pins'][NATIVE] ==
            lane['source_census']['native']['sha256'], 'actual_unpatched_native_cohort')
    policy = load('POLICY.py')
    require((destination / NATIVE).read_text() == policy.patch_native((original / NATIVE).read_text()),
            'only_compaction_decision_patch')
    expected = dict(old_config['source_pins'], **{NATIVE: sha(destination / NATIVE), POLICY: POLICY_SHA})
    require(source_pins(destination) == expected == new_config['source_pins'], 'full_source_plus_one_policy')
    if old_plan.get('startup_context'):
        require(sha(new_plan['startup_context']['path']) == old_plan['startup_context']['sha256'], 'unchanged_startup')
    require(read(new_config['allocation_path']) == dict(read(old_config['allocation_path']),
            plan_sha256=new_config['plan_sha256']), 'allocation_rebind_only')
    stage = read(target / 'STAGED_SOURCE.json')
    require(sha(binding) == stage['guard_sha256'] and stage['old_guard_ref'] == lane['guard_ref']
            and stage['old_plan_ref'] == lane['plan_ref'] and stage['policy_sha256'] == POLICY_SHA, 'stage_inputs_bound')
    cpu = read(target / 'CPU_POLICY.json')
    require(cpu['status'] == 'PASS' and cpu['returncode'] == 0 and cpu['immutable_after_cpu'] is True
            and cpu['policy_sha256'] == POLICY_SHA and cpu['source_manifest_sha256'] ==
            hashlib.sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest()
            and sha(target / 'CPU_POLICY.log') == cpu['log_sha256']
            and sha(HERE / 'receiving_policy.py') == cpu['test_sha256'], 'actual_receiving_source_CPU')


def saved_function(family, source):
    tree = ast.parse(source)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'saved_evidence')
    matches = [node for node in ast.walk(function) if isinstance(node, ast.Constant)
               and node.value == '7626d13974a78c713b9e966093e285e1e8a4f194301dd8b69ec68cfcae656526']
    require(len(matches) == 1, 'one_legacy_native_reference')
    matches[0].value = '106be5bd8bde805c092bbbf49233391b799c2b0641d3c41fdd75cb66d75ebc45'
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])), family['__file__'], 'exec'), family)


def monitor_loaded(family, output, saved, unlock):
    helper = family['api']()
    config = helper.read(output / 'GUARD.json')
    plan = helper.read(config['plan_path'])
    old_head = Path(saved['record_path']).name
    deadline = min(time.monotonic() + 600, time.monotonic() + plan['hard_end_unix'] - time.time())
    while time.monotonic() < deadline:
        require(not any((output / name).exists() for name in ('SUPERVISOR_FAILED.json', 'EXIT.json', 'SERVICE_EXIT.json')),
                'successor_failed_preserve_no_retry')
        for path in sorted((Path(plan['root']) / 'stream/records').glob('*.json')):
            if not re.fullmatch(r'\d{20}\.json', path.name) or path.name <= old_head:
                continue
            record = helper.read(path)
            require(record['sha256'] == helper.digest({key: value for key, value in record.items() if key != 'sha256'}),
                    'new_journal_hash')
            if record['kind'] != 'LOADED':
                continue
            document = record['document']
            require(document['resume'] is True and document['optimizer_steps'] == saved['optimizer_steps']
                    and document['adapter_sha256'] == saved['adapter_state_sha256'], 'exact_saved_loaded')
            actor = helper.identity(document['pid'])
            require(actor['argv'][-1] == str(output / 'GUARD.json') and helper.ALLOCATOR in actor['environment']
                    and actor['cwd'] == plan['source_root'], 'new_source_actual_native_allocator')
            proof = helper.read(output / 'CONTAINMENT_VERIFIED.json')
            denied = proof.get('denied_foreign_minors')
            if denied is None:
                denied = [int(name.removeprefix('nvidia')) for name in proof['denied_devices']]
            require(sorted(denied) == [minor for minor in range(8) if minor != config['device_containment']['minor']]
                    and proof['policy'] == config['device_containment'], 'all_seven_foreign_denials')
            launch = helper.read(output / 'LAUNCH.json')
            require(actor['parent'] == launch['pid'] and launch['guard_sha256'] == helper.sha(output / 'GUARD.json'),
                    'new_native_launch_binding')
            receipt = dict(status='SUCCESSOR_EXACT_STATE_LOADED', physical=plan['physical'],
                record_path=str(path), record_sha256=helper.sha(path), actor=actor,
                optimizer_steps=document['optimizer_steps'], adapter_state_sha256=document['adapter_sha256'],
                policy_sha256=POLICY_SHA, source_root=plan['source_root'], boundary_sha256=helper.sha(output / 'BOUNDARY.json'),
                effective_next_cycle=saved['cycle']+1, observed_unix=time.time(),
                context_retention_observed=False, completed_sleep_observed=False, no_scientific_claim=True)
            helper.write(output / 'LOADED_RECEIPT.json', receipt)
            unlock()
            return receipt
        time.sleep(1)
    helper.write(output / 'MONITOR_TIMEOUT.json', dict(loaded=False, observed_unix=time.time(), no_retry=True))
    return dict(status='LOAD_NOT_OBSERVED_NO_RETRY')


def family_namespace():
    for name, checksum in DEPENDENCIES.items():
        require(sha(HERE / name) == checksum, 'dependency_pin:' + name)
    source = (HERE / 'FAMILY.py').read_bytes()
    family = dict(__name__='r179_private_original_family', __file__=str(Path(__file__).resolve()))
    exec(compile(source, family['__file__'], 'exec'), family)
    helper = family['api']()
    helper.family_scope = scope
    original_processes = family['old_processes']
    def processes(pid, config_path, config, plan):
        lane = lane_for(scope(plan))
        require(str(config_path) == lane['guard_ref']['path'] and sha(config_path) == lane['guard_ref']['sha256'],
                'inventoried_guard_path_hash')
        result = current_direct_processes(helper, pid, config_path, config, plan) if plan['physical'] in (0, 2) else (
            original_processes(pid, config_path, config, plan))
        require(result['actor']['pid'] == lane['identity']['pid']
                and result['actor']['start_ticks'] == lane['identity']['start_ticks'], 'inventoried_native_pid_ticks')
        return result
    family.update(api=lambda: helper, lane_scope=scope, old_processes=processes,
        STAGED_SOURCE_ROOT=ROOT, PATCH_SHA=POLICY_SHA, HELPER_SHA=POLICY_SHA,
        POLICY='R179_CONTEXT_SURVIVES_SLEEP_V1')
    family['verify_source'] = lambda *args: verify_source(family, *args)
    family['monitor'] = lambda *args: monitor_loaded(family, *args)
    family['pause_recovery'] = load('RECOVERY.py').Recovery()
    load('RECOVERY_ADAPTER.py').repaired_handoff(family, source)
    saved_function(family, source)
    return family


def prepare(physical, output, local_cpu):
    family = family_namespace()
    helper = family['api']()
    require(socket.gethostname() == helper.HOST and ROOT == Path('/localhome/local-rohing/orch_r179_node3_context_20260917t1715z_1'),
            'actual_node3_attempt_root')
    require(sha(local_cpu) == read(HERE / 'CPU_LOCAL_REF.json')['sha256'], 'bound_local_CPU')
    cpu = read(local_cpu)
    require(cpu['status'] == 'PASS' and cpu['operator_sha256'] == sha(__file__)
            and cpu['dependencies'] == DEPENDENCIES and cpu['failed'] == 0, 'operator_actual_CPU')
    lane = lane_for(physical)
    config, plan, original = family['old_modules'](lane['guard_ref']['path'])
    processes = family['old_processes'](lane['identity']['pid'], lane['guard_ref']['path'], config, plan)
    inventory_path = ROOT / 'INVENTORY.json'
    require(inventory_path.exists(), 'create_once_inventory_required')
    require(helper.read(inventory_path)['lanes'][[row['physical'] for row in helper.read(inventory_path)['lanes']].index(physical)]
            ['processes'] == processes, 'prepared_inventory_exact_topology')
    receipt = ROOT / ('physical' + str(physical)) / 'CPU_LIFECYCLE.json'
    helper.write(receipt, dict(status='PASS', operator_sha256=sha(__file__), api_sha256=DEPENDENCIES['BOUNDARY_API.py'],
        patch_sha256=POLICY_SHA, helper_sha256=POLICY_SHA, local_cpu_path=str(local_cpu), local_cpu_sha256=sha(local_cpu),
        receiving_cpu_sha256=sha(ROOT / ('physical' + str(physical)) / 'CPU_POLICY.json'),
        dependencies=DEPENDENCIES, policy_label_semantics='Exact_R179_policy_not_historical_R144_patch', signals_sent=0))
    return family['stage'](physical, output, receipt)


def inventory():
    family = family_namespace()
    helper = family['api']()
    require(socket.gethostname() == helper.HOST, 'actual_node3_inventory')
    rows = []
    for physical in (0, 1, 2, 3, 4, 7):
        lane = lane_for(physical)
        config, plan, original = family['old_modules'](lane['guard_ref']['path'])
        processes = family['old_processes'](lane['identity']['pid'], lane['guard_ref']['path'], config, plan)
        require(processes == family['old_processes'](lane['identity']['pid'], lane['guard_ref']['path'], config, plan),
                'twice_exact_topology')
        rows.append(dict(physical=physical, live=True, guard_path=lane['guard_ref']['path'],
            guard_sha256=lane['guard_ref']['sha256'], processes=processes))
        for name in tuple(sys.modules):
            if name == 'gpu' or name.startswith('gpu.') or name == 'organism_v6' or name.startswith('organism_v6.'):
                del sys.modules[name]
    helper.write(ROOT / 'INVENTORY.json', dict(lanes=rows, observed_unix=time.time(), signals_sent=0))
    return dict(status='INVENTORY_BOUND', physicals=[row['physical'] for row in rows], signals_sent=0)


def device_preflight(family, output):
    helper = family['api']()
    request = helper.read(output / 'STAGED.json')
    require(request['operator_sha256'] == sha(__file__) and request['new_config_sha256'] == sha(output / 'GUARD.json'),
            'bound_device_preflight')
    config, plan, original = family['new_modules'](output / 'GUARD.json')
    proof = read(request['cpu_path'])
    local_cpu = read(proof['local_cpu_path'])
    require(sha(HERE / 'device_probe.py') == local_cpu['device_probe_sha256'], 'CPU_bound_device_probe')
    (output / 'DEVICE_PREFLIGHT_ONCE').mkdir()
    policy = deepcopy(config['device_containment'])
    prefix = policy['unit'].rsplit('-', 1)[0]
    policy['unit'] = prefix + '-' + uuid.uuid4().hex
    payload = [str(helper.PYTHON), '-I', '-B', str(HERE / 'device_probe.py'), '--policy',
               json.dumps(policy, sort_keys=True), '--uuid', plan['gpu_uuid']]
    if plan['physical'] in (0, 2):
        command = family['direct_command'](plan, policy, payload, 60)
    elif plan['physical'] == 1:
        command = original.programmes.device_containment_command(1, policy['minor'], policy['uid'], policy['gid'],
            policy['unit'], plan['source_root'], payload, 60)
    else:
        command = original.programmes.containment_command(plan, policy, payload, 60)
    command = helper.allocator_command(command)
    result = subprocess.run(command, text=True, capture_output=True, timeout=90, cwd=plan['source_root'])
    helper.write(output / 'DEVICE_PREFLIGHT_PROCESS.json', dict(returncode=result.returncode, stdout=result.stdout,
        stderr=result.stderr, command=command, operator_sha256=sha(__file__), observed_unix=time.time()))
    require(result.returncode == 0, 'device_probe_refused_before_stop')
    observed = json.loads(result.stdout)
    require(observed['status'] == 'PASS' and observed['policy'] == policy and observed['gpu_uuid'] == plan['gpu_uuid']
            and observed['denied_foreign_minors'] == [minor for minor in range(8) if minor != policy['minor']],
            'receiving_device_exact_proof')
    receipt = dict(status='PASS', result=observed, guard_sha256=sha(output / 'GUARD.json'),
        operator_sha256=sha(__file__), device_probe_sha256=sha(HERE / 'device_probe.py'),
        original_guard_unchanged=sha(request['old_config']) == request['old_config_sha256'],
        no_models_or_learner_signals=True, observed_unix=time.time())
    helper.write(output / 'DEVICE_PREFLIGHT.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', choices=('inventory', 'stage', 'validate', 'device', 'handoff', 'supervise', 'contained'), required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--physical', type=int, choices=(0, 1, 2, 3, 4, 7))
    parser.add_argument('--cpu', type=Path)
    parser.add_argument('--seconds', type=int, default=1200)
    args = parser.parse_args()
    family = family_namespace()
    if args.action == 'inventory':
        result = inventory()
    elif args.action == 'stage':
        result = prepare(args.physical, args.output, args.cpu)
    elif args.action == 'validate':
        result = family['validate_new'](args.output)
    elif args.action == 'device':
        result = device_preflight(family, args.output)
    elif args.action == 'handoff':
        device = read(args.output / 'DEVICE_PREFLIGHT.json')
        require(device['status'] == 'PASS' and device['guard_sha256'] == sha(args.output / 'GUARD.json')
                and device['operator_sha256'] == sha(__file__) and device['device_probe_sha256'] == sha(HERE / 'device_probe.py')
                and device['original_guard_unchanged'] is True, 'receiving_device_before_any_STOP')
        result = family['handoff'](args.output, args.seconds)
    else:
        try:
            result = family[args.action](args.output)
        except BaseException as error:
            family['api']().write(args.output / 'SUPERVISOR_FAILED.json', dict(error_type=type(error).__name__,
                error=str(error), observed_unix=time.time(), no_retry=True))
            raise
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
