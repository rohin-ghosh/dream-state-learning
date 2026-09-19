"""R158 node4-only matched triplet staging and Main-gated contained execution."""

import argparse
import ast
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time
from types import ModuleType


HOST = 'a4u8g-0105'
HOST_SHA256 = 'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b'
BASE = Path('/localhome/local-rohing')
PYTHON = BASE / 'v2/venv/bin/python'
MODULE = 'gpu.orch_r158_matched_node4'
SCOPE = 'R158_NODE4_MATCHED_INITIALIZE_RUN_5_6_7'
WALL = 1789646400
LEASE_SHA256 = 'ca4ead20b2b772c09e4d30e271c24988f0bbcc5f625665e6b63a441fe0e112a2'
LEASE_PATH = BASE / 'orch_r132_kernel_child_20260916_attempt1/control1/LEASE_BUDGET.json'
DEVICES = {
    5: 'GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30',
    6: 'GPU-06b31c8f-7a96-d812-23f3-df3444d95397',
    7: 'GPU-6eac3b9d-551a-d786-f598-04ef6d701c98',
}
ARMS = {'parented_learning': 5, 'parented_frozen': 6, 'unparented_learning': 7}
CAPSULE_RELATIVE = 'gpu/R158_CONFINEMENT_API.py'
CAPSULE_SHA256 = '29e2d77dfe21a6c1b37861f52c00d2eeb858c67b60f054ab6e2d2238cc135c95'
OLD_DEVICES = "DEVICES = {2: 'GPU-d62ba12e-ff08-9e5e-ba35-14c723f6e05b', 6: 'GPU-67a989f7-2660-a76b-40e8-3619b9fa2987'}"
REPAIR_FILES = (
    'gpu/orch_r150_matched_native.py', 'gpu/orch_r151_memory_probe.py',
    'gpu/orch_r151_matched_containment.py', 'gpu/orch_r151_matched_stage.py',
    'tests/test_orch_r150_matched_native.py', 'tests/test_orch_r151_memory_probe.py',
    'tests/test_orch_r151_matched_containment.py',
    'gpu/orch_r158_train_gym.py', 'tests/test_orch_r158_train_gym.py',
    'organism_v6/reasoning_gym_families.json',
    'organism_v6/bootstrap_reasoning_gym.txt',
    'gpu/orch_r158_matched_node4.py', 'tests/test_orch_r158_matched_node4.py',
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def canonical(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts
            and not any(part.is_symlink() for part in (path, *path.parents)), 'canonical_unlinked_path')
    return path


def sha(path):
    value = hashlib.sha256()
    with canonical(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            value.update(block)
    return value.hexdigest()


def read(path):
    return json.loads(canonical(path).read_bytes())


def reference(path):
    return dict(path=str(canonical(path)), sha256=sha(path))


def bound(value):
    require(sha(value['path']) == value['sha256'], 'exact_bound_receipt')
    return read(value['path'])


def write(path, value):
    path = canonical(path)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), 0o444)


def inventory(root):
    root = canonical(root)
    result = {}
    for path in sorted(root.rglob('*')):
        canonical(path)
        require(path.is_file() or path.is_dir(), 'ordinary_source_files')
        if path.is_file():
            result[str(path.relative_to(root))] = sha(path)
    return result


def render_capsule(original):
    require(hashlib.sha256(original).hexdigest() == CAPSULE_SHA256, 'exact_proven_capsule')
    text = original.decode()
    require(text.count(OLD_DEVICES) == 1 and text.count("'ipp2-ovx-p1-10'") == 1,
            'exact_capsule_profile_sites')
    return text.replace(OLD_DEVICES, 'DEVICES = ' + repr(DEVICES), 1).replace(
        "'ipp2-ovx-p1-10'", repr(HOST), 1).encode()


def load_capsule(path):
    data = canonical(path).read_bytes()
    text = data.decode()
    new_devices = 'DEVICES = ' + repr(DEVICES)
    require(text.count(new_devices) == 1 and text.count(repr(HOST)) == 1, 'node4_capsule_profile')
    original = text.replace(new_devices, OLD_DEVICES, 1).replace(repr(HOST), "'ipp2-ovx-p1-10'", 1).encode()
    require(render_capsule(original) == data, 'capsule_only_host_and_devices_changed')
    module = ModuleType('r158_node4_capsule')
    exec(compile(data, str(path), 'exec'), module.__dict__)
    return module


def profile_tree(original):
    tree = ast.parse(original)
    replacements = dict(HOST=HOST, HOST_SHA256=HOST_SHA256, DEVICES=DEVICES,
                        SCOPE=SCOPE, MODULE=MODULE, EXISTING_LEASE_SHA256=LEASE_SHA256)
    changed = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in replacements:
                node.value = ast.parse(repr(replacements[name]), mode='eval').body
                changed.add(name)
    require(changed == set(replacements), 'exact_R151_profile_assignments')
    for name, before, after in (
        ('go_binding', '[0, 3, 4]', '[5, 6, 7]'),
        ('validate_go', "'R151_MAIN_GO_V1'", "'R158_MAIN_GO_V1'"),
    ):
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
        require(len(functions) == 1, 'exact_R151_profile_function')
        expected = ast.dump(ast.parse(before, mode='eval').body, include_attributes=False)
        count = 0

        class Replace(ast.NodeTransformer):
            def visit(self, node):
                nonlocal count
                if ast.dump(node, include_attributes=False) == expected:
                    count += 1
                    return ast.parse(after, mode='eval').body
                return super().visit(node)

        Replace().visit(functions[0])
        require(count == 1, 'single_R151_profile_literal')
    supervisors = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'supervise']
    require(len(supervisors) == 1, 'single_R151_supervisor')
    scan_calls = 0

    class RecheckScan(ast.NodeTransformer):
        def visit_Call(self, node):
            nonlocal scan_calls
            if (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == 'subprocess' and node.func.attr == 'run'):
                require(len(node.args) == 1 and isinstance(node.args[0], ast.Name)
                        and node.args[0].id == 'command', 'exact_privileged_scan_call')
                require({keyword.arg for keyword in node.keywords} ==
                        {'env', 'text', 'stdout', 'stderr', 'timeout'}, 'exact_scan_call_contract')
                scan_calls += 1
                node.func = ast.Name(id='scan_with_transient_rechecks', ctx=ast.Load())
                node.keywords.append(ast.keyword(arg='receipt_dir', value=ast.Name(id='attempt', ctx=ast.Load())))
            return self.generic_visit(node)

    RecheckScan().visit(supervisors[0])
    require(scan_calls == 1, 'single_privileged_scan_call_replaced')
    return ast.fix_missing_locations(tree)


def transient_scan_only(report, config, plan):
    if (not isinstance(report, dict) or report.get('scanner_euid') != 0 or report.get('clear') is not False
            or report.get('host_sha256') != HOST_SHA256
            or report.get('device_minor') != config['device_containment']['minor']):
        return False
    device = report.get('gpu', {})
    if (not isinstance(device, dict) or device.get('uuid') != plan['gpu_uuid']
            or device.get('memory_used_mib') != 0 or device.get('utilization_percent') != 0):
        return False
    reasons, processes, compute = (report.get(name) for name in ('blocking_reasons', 'processes', 'compute_processes'))
    if not all(isinstance(value, list) for value in (reasons, processes, compute)) or not reasons:
        return False
    if not all(isinstance(value, dict) for value in processes + compute):
        return False
    if any(value.get('gpu_uuid') == plan['gpu_uuid'] for value in compute):
        return False
    for reason in reasons:
        match = re.fullmatch(r'process_identity_drift:([1-9][0-9]*)', reason) if isinstance(reason, str) else None
        if match is None:
            return False
        process_id = int(match.group(1))
        matches = [value for value in processes if value.get('pid') == process_id]
        if len(matches) != 1:
            return False
        process = matches[0]
        if (process.get('target_device_open') is not False or process.get('cvd') not in (None, '', '-1')
                or any(value.get('pid') == process_id for value in compute)):
            return False
    return True


def scan_with_transient_rechecks(command, *, receipt_dir, env, text, stdout, stderr, timeout):
    require(command[-3:-1] == ['scan', '--config'], 'exact_scan_command_for_rechecks')
    require(command[command.index('-m') + 1] == 'gpu.orch_r125_continual_guard', 'unchanged_privileged_scanner')
    config = read(command[-1])
    plan = read(config['plan_path'])
    require(canonical(receipt_dir) == canonical(config['attempt_dir']), 'scan_observations_in_owned_attempt')
    require(type(timeout) in (int, float) and 0 < timeout <= 100, 'existing_scan_timeout_bound')
    output = canonical(receipt_dir) / 'ADMISSION_OBSERVATIONS'
    output.mkdir(mode=0o700)
    deadline = time.monotonic() + min(timeout, 60)
    for number in range(8):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            require(number > 0, 'time_for_first_admission_observation')
            return result
        started = time.time()
        try:
            result = subprocess.run(command, env=env, text=text, stdout=stdout, stderr=stderr, timeout=remaining)
        except BaseException as error:
            write(output / f'{number:03d}_ERROR.json', dict(error_type=type(error).__name__,
                error=str(error), started_unix=started, finished_unix=time.time(), retried=False))
            raise
        raw = result.stdout
        with (output / f'{number:03d}.stdout').open('x') as stream:
            stream.write(raw)
        write(output / f'{number:03d}_RECEIPT.json', dict(returncode=result.returncode,
            started_unix=started, finished_unix=time.time(), stdout_sha256=sha(output / f'{number:03d}.stdout'),
            command_sha256=hashlib.sha256(json.dumps(command, separators=(',', ':')).encode()).hexdigest(),
            original_reasons_removed=False, native_started=False))
        if result.returncode != 0:
            return result
        report = json.loads(raw)
        if not transient_scan_only(report, config, plan):
            return result
        if number == 7 or time.monotonic() + 0.25 >= deadline:
            return result
        time.sleep(0.25)
    raise AssertionError('bounded_scan_loop_must_return')


def engine():
    path = Path(__file__).resolve().with_name('orch_r151_matched_containment.py')
    module = ModuleType('r158_isolated_R151_supervision')
    module.__file__ = str(Path(__file__).resolve())
    exec(compile(profile_tree(path.read_bytes()), str(path), 'exec'), module.__dict__)
    module.load_capsule = load_capsule
    module.render_capsule = render_capsule
    module.verify_budget = verify_budget
    module.scan_with_transient_rechecks = scan_with_transient_rechecks
    return module


def verify_lease(path):
    require(canonical(path) == LEASE_PATH and sha(path) == LEASE_SHA256, 'exact_existing_node4_budget')
    prior = read(path)
    require(prior['lease_extended'] is False and prior['hard_end_unix'] == 1789754400
            and prior['lease_end_unix'] == 1789776000 and prior['safety_margin_seconds'] == 21600
            and WALL <= prior['hard_end_unix'] == prior['lease_end_unix'] - 21600,
            'existing_six_hour_reserve_not_relaxed')
    return prior


def verify_budget(config, plan):
    require(sha(config['lease_path']) == config['lease_sha256'], 'bound_node4_cohort_budget')
    budget = read(config['lease_path'])
    require(budget['schema'] == 'R158_EXISTING_NODE4_COHORT_BUDGET_V1'
            and budget['physical_devices'] == [5, 6, 7] and budget['host_sha256'] == HOST_SHA256
            and budget['lease_extended'] is False and budget['existing_life_wall_changed'] is False
            and budget['safety_margin_seconds'] == 21600, 'scoped_node4_existing_budget')
    require(budget['derived_from']['sha256'] == LEASE_SHA256, 'exact_prior_budget_reference')
    prior = verify_lease(budget['derived_from']['path'])
    require(plan['hard_end_unix'] == config['hard_end_unix'] == budget['hard_end_unix'] == WALL
            and plan['lease_end_unix'] == config['next_reserved_unix'] == budget['lease_end_unix']
            == prior['lease_end_unix'], 'exact_prospective_wall_not_extension')


def verify_repairs(path, repository, *, require_freeze=False):
    proof = read(path)
    require(proof['schema'] == 'R158_MATCHED_REPAIR_REVIEW_V1' and proof['status'] == 'PASS'
            and proof['issuer'] in ('Main', 'Banach', 'Builder') and type(proof['freeze_allowed']) is bool
            and proof['capacity_consumer_fixed'] is True and proof['deadline_cleanup_fixed'] is True
            and proof['failure_receipts_fixed'] is True, 'completed_reviewed_R150_R151_repairs')
    require(set(REPAIR_FILES) <= set(proof['files']), 'repair_core_and_regression_source_pins')
    for name, checksum in proof['files'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts
                and sha(Path(repository) / name) == checksum, 'actual_repaired_source_bytes')
    require(proof['tests']['exit_code'] == 0 and type(proof['tests']['passed']) is int
            and proof['tests']['passed'] > 0 and proof['tests']['logs'], 'actual_repair_tests_passed')
    for log in proof['tests']['logs']:
        require(sha(log['path']) == log['sha256'], 'bound_repair_test_log')
    if require_freeze:
        require(proof['issuer'] == 'Main' and proof['freeze_allowed'] is True
                and proof.get('review_disposition') == 'APPROVED_FOR_FREEZE'
                and proof.get('review_receipts'), 'Main_review_dispositions_before_freeze')
        for receipt in proof['review_receipts']:
            require(sha(receipt['path']) == receipt['sha256'], 'bound_Main_review_disposition')
    return proof


def stage_source(repository, destination, runtime, proof, capsule_original, repairs):
    from gpu.orch_r151_matched_stage import stage_source as original_stage
    repository, destination = canonical(repository), canonical(destination)
    verify_repairs(repairs, repository)
    capsule = render_capsule(canonical(capsule_original).read_bytes())
    result = original_stage(repository, destination, runtime, proof)
    with (destination / CAPSULE_RELATIVE).open('xb') as stream:
        stream.write(capsule)
    fixture = destination / 'research_loop/workers/r143_node5_allocator_20260916t1427z/CONFINEMENT_API.py'
    fixture.parent.mkdir(parents=True, exist_ok=True)
    with fixture.open('xb') as stream:
        stream.write(canonical(capsule_original).read_bytes())
    ledger_relative = 'organism_v6/reasoning_gym_families.json'
    for relative in (ledger_relative, 'organism_v6/bootstrap_reasoning_gym.txt'):
        (destination / relative).parent.mkdir(parents=True, exist_ok=True)
        with (destination / relative).open('xb') as stream:
            stream.write((repository / relative).read_bytes())
        require(sha(destination / relative) == sha(repository / relative), 'exact_TRAIN_constructor_asset')
    (destination / 'STAGED_SOURCE.json').rename(destination / 'R151_STAGED_SOURCE_ORIGINAL.json')
    write(destination / 'R158_REPAIRS.json', read(repairs))
    write(destination / 'R158_SOURCE_PROFILE.json', dict(schema='R158_NODE4_SOURCE_PROFILE_V1',
        original_staging_manifest=reference(destination / 'R151_STAGED_SOURCE_ORIGINAL.json'),
        repairs=reference(repairs), original_capsule=reference(capsule_original),
        supervisor_sha256=sha(destination / 'gpu/orch_r151_matched_containment.py'),
        helper_sha256=sha(destination / 'gpu/orch_r158_matched_node4.py'),
        allowed_physical=[5, 6, 7], host=HOST, requested_scope=SCOPE))
    write(destination / 'STAGED_SOURCE.json', dict(schema='R158_MATCHED_STAGED_SOURCE_V1',
        files=inventory(destination), original_staging_manifest=reference(destination / 'R151_STAGED_SOURCE_ORIGINAL.json'),
        train_split_ledger=dict(relative=ledger_relative, sha256=sha(destination / ledger_relative)),
        constructor_bootstrap=dict(relative='organism_v6/bootstrap_reasoning_gym.txt',
            sha256=sha(destination / 'organism_v6/bootstrap_reasoning_gym.txt'), child_startup_use=False)))
    verify_repairs(repairs, repository)
    return dict(status='SOURCE_STAGED_NOT_FROZEN_NOT_LAUNCHED', original_stage=result,
                files=inventory(destination))


def plans(source, output, lease, initialization_source=None):
    from gpu import orch_r125_continual_native as native
    from gpu import orch_r150_matched_native as matched
    from organism_v6.orch_r125_plain_context import VERSION
    prior = verify_lease(lease)
    startup = source / 'research_notes/R150_MATCHED_STARTUP_2026-09-16.txt'
    result = []
    for arm, physical in ARMS.items():
        plan = dict(schema=native.SCHEMA, base_sha256=native.BASE_SHA256, system_prompt=native.SYSTEM,
            birth_prompt=startup.read_text(), startup_context=dict(version='R127_STARTUP_V1',
                path=str(startup), sha256=sha(startup)), presentation_version=VERSION,
            presleep_variant='free_distillation', seed=0,
            compaction_invitation=native.PRESLEEP_INVITATIONS['free_distillation'],
            new_presentations=16, rehearsal_presentations=1, anchor_lambda=0.25, segments_per_sleep=2,
            segment_tokens=512, context_limit=16384, max_sleeps=None, readout_revision=1,
            root=str(output / arm), source_root=str(source), physical=physical, gpu_uuid=DEVICES[physical],
            model_dir=str(BASE / '.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28'),
            anchors=str(BASE / 'orch_r107_base_anchors_20260915_attempt1'),
            decoder=dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05, no_repeat_ngram_size=16),
            hard_end_unix=WALL, lease_end_unix=prior['lease_end_unix'], matched_arm=arm,
            parent_enabled=arm != 'unparented_learning',
            initialization_validation_schema='R151_MATCHED_INITIAL_CAPACITY_V1')
        if initialization_source is not None:
            plan['initialization_source'] = reference(canonical(initialization_source))
            matched.validate_initialization_source(plan)
        native.validate_plan(plan)
        result.append(plan)
    cohort = matched.cohort_document(result, output / 'common_initial')
    return result, cohort, prior


def verify_cpu(path, source):
    cpu = read(path)
    require(cpu['status'] == 'PASS' and cpu['exit_code'] == 0 and cpu['host'] == HOST
            and type(cpu['passed']) is int and cpu['passed'] > 0
            and cpu['source_inventory'] == inventory(source) and cpu['logs'], 'actual_receiving_CPU_source_gate')
    for log in cpu['logs']:
        require(sha(log['path']) == log['sha256'], 'actual_CPU_log_bytes')
    return cpu


def initializer_profile_preflight(plan):
    from gpu import orch_r151_memory_probe as probe
    profile = probe.initializer_profile(plan, HOST)
    require(profile == 'R158_NODE4', 'actual_node4_capacity_callback_profile')
    return dict(status='PASS', profile=profile, host=HOST, physical=plan['physical'],
        gpu_uuid=plan['gpu_uuid'], GPU_calls=0, numerical_capacity_proof=False,
        memory_probe_sha256=sha(Path(probe.__file__)))


def prepare(base, lease, cpu, intake, publication, repairs, initialization_source=None):
    base = canonical(base)
    require(base.parent == BASE and base.name.startswith('orch_r158_matched_node4_')
            and socket.gethostname() == HOST and os.getuid() == os.getgid() == 2524
            and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'exact_node4_CPU_preparation')
    source, control, cohort_root = base / 'source', base / 'control', base
    require(source == Path(__file__).resolve().parents[1], 'prepare_from_staged_node4_source')
    verify_repairs(repairs, source, require_freeze=True)
    verify_cpu(cpu, source)
    scope = read(intake)
    require(scope['requested_scope'] == SCOPE and scope['classification'] == 'STANDING_AUTHORIZED_NON_MATERIAL'
            and scope['changes_invariants'] is False and scope['new_human_ratification_claimed'] is False,
            'approved_intake_scope_no_new_ratification')
    posted = read(publication)
    require(posted['posted'] is True and posted['git_commit_or_push'] is False
            and sha(posted['note_path']) == posted['note_sha256'], 'actual_local_builder_publication')
    compiled = engine()
    capsule = source / CAPSULE_RELATIVE
    api = load_capsule(capsule)
    plan_list, cohort, prior = plans(source, cohort_root, lease, initialization_source)
    profile_preflight = initializer_profile_preflight(plan_list[0])
    require(time.time() + 600 < WALL, 'time_for_bounded_prospective_triplet')
    require(not (base / 'common_initial').exists() and all(not (base / arm).exists() for arm in ARMS),
            'never_reuse_initial_or_old_life_roots')
    control.mkdir(exist_ok=False)
    (base / 'attempts').mkdir(exist_ok=False)
    write(control / 'INITIALIZER_PROFILE_PREFLIGHT.json', profile_preflight)
    write(cohort_root / 'COHORT.json', cohort)
    write(cohort_root / 'LEASE_BUDGET.json', dict(schema='R158_EXISTING_NODE4_COHORT_BUDGET_V1',
        derived_from=reference(lease), hard_end_unix=WALL, lease_end_unix=prior['lease_end_unix'],
        safety_margin_seconds=21600, lease_extended=False, existing_life_wall_changed=False,
        physical_devices=[5, 6, 7], host_sha256=HOST_SHA256, purchase_performed=False))
    manifest = dict(files=inventory(source))
    write(control / 'SOURCE_MANIFEST.json', manifest)
    pins = {name: checksum for name, checksum in manifest['files'].items() if name.endswith('.py')}
    gate = dict(status='PASS', source_manifest_sha256=sha(control / 'SOURCE_MANIFEST.json'),
        initializer_profile_preflight=reference(control / 'INITIALIZER_PROFILE_PREFLIGHT.json'),
        matched_cohort_sha256=sha(cohort_root / 'COHORT.json'), actual_CPU_receipt=reference(cpu),
        repairs=reference(repairs), guard_derivation=dict(status='PASS',
            original_guard_sha256=compiled.ORIGINAL_GUARD_SHA256,
            r150_parent_guard_sha256=compiled.R150_PARENT_GUARD_SHA256,
            guard_sha256=pins[compiled.GUARD], patcher_sha256=pins[compiled.STAGING_PATCHER],
            memory_probe_sha256=pins[compiled.MEMORY_PROBE],
            initialize_callback='gpu.orch_r151_memory_probe.initial_capacity',
            original_checks_preserved=True, run_dispatch_unchanged=True))
    compiled.verify_guard_derivation(source, pins, gate)
    write(control / 'CPU_GATE.json', gate)
    configurations = []
    for plan in plan_list:
        arm = plan['matched_arm']
        plan['matched_cohort'] = reference(cohort_root / 'COHORT.json')
        plan_path = cohort_root / (arm + '.PLAN.json')
        write(plan_path, plan)
        for phase in (('initialize', 'run') if arm == 'parented_learning' else ('run',)):
            name = phase + '-' + arm
            directory, attempt = control / name, base / 'attempts' / (name + '-attempt1')
            directory.mkdir(exist_ok=False)
            write(directory / 'ALLOCATION.json', dict(plan_sha256=sha(plan_path), cpu_tests_passed=True,
                gpu_uuid=plan['gpu_uuid'], physical=plan['physical'], declared_unix=time.time(),
                builder_entry_pushed=True, builder_entry_posted=True, git_push_performed=False,
                legacy_builder_entry_pushed_semantics='LOCAL_POSTING_NOT_GIT_PUSH',
                publication=reference(publication), GPU_admitted=False, fresh_admission_required=True))
            config = dict(schema='R125_CONTINUAL_GUARD_V1', phase=phase, matched_arm=arm, resume=False,
                requested_scope=SCOPE, source_pins=pins, host_sha256=HOST_SHA256,
                boot_id=compiled.BOOT_ID.read_text().strip(), matched_cohort_sha256=plan['matched_cohort']['sha256'],
                hard_end_unix=WALL, next_reserved_unix=prior['lease_end_unix'], attempt_dir=str(attempt),
                allocator=compiled.ALLOCATOR, device_containment=dict(uid=2524, gid=2524,
                    minor=api.device_minor(plan['gpu_uuid']), unit=compiled.new_unit(attempt)),
                r158_base=str(base), r158_repairs=reference(repairs), r158_cpu=reference(cpu))
            for key, path in dict(plan=plan_path, lease=cohort_root / 'LEASE_BUDGET.json',
                allocation=directory / 'ALLOCATION.json', source_manifest=control / 'SOURCE_MANIFEST.json',
                cpu_gate=control / 'CPU_GATE.json', intake=intake, capsule=capsule).items():
                config[key + '_path'], config[key + '_sha256'] = str(path), sha(path)
            config_path = directory / 'GUARD.json'
            write(config_path, config)
            from gpu import orch_r125_continual_guard as guard
            guard.validate(config_path)
            verify_budget(config, plan)
            configurations.append(dict(phase=phase, arm=arm, physical=plan['physical'],
                config=reference(config_path), receipt_dir=str(attempt),
                required_GO_binding=compiled.go_binding(config, plan, sha(config_path))))
    require(inventory(source) == manifest['files'], 'source_unchanged_before_freeze')
    for path in sorted(source.rglob('*'), reverse=True):
        path.chmod(0o555 if path.is_dir() else 0o444)
    source.chmod(0o555)
    result = dict(status='PREPARED_FROZEN_NO_GPU_NO_MAIN_GO', configurations=configurations,
        source_manifest=reference(control / 'SOURCE_MANIFEST.json'), cohort=reference(cohort_root / 'COHORT.json'),
        prepared_unix=time.time(), GPU_calls=0, donor_signals=0)
    write(control / 'PREPARED_EXECUTION.json', result)
    return result


def validate_extra(config_path, main_go_path):
    config, go = read(config_path), read(main_go_path)
    plan = read(config['plan_path'])
    base = canonical(config['r158_base'])
    require(base.parent == BASE and base.name.startswith('orch_r158_matched_node4_')
            and canonical(plan['root']) == base / plan['matched_arm']
            and canonical(plan['source_root']) == base / 'source', 'new_R158_roots_only')
    require(plan['matched_arm'] in ARMS and plan['physical'] == ARMS[plan['matched_arm']]
            and plan['gpu_uuid'] == DEVICES[plan['physical']] and config['resume'] is False,
            'exact_node4_arm_assignment_fresh_only')
    bound(config['r158_repairs']); bound(config['r158_cpu'])
    verify_repairs(config['r158_repairs']['path'], base / 'source', require_freeze=True)
    verify_cpu(config['r158_cpu']['path'], base / 'source')
    for path in (base / 'source', *(base / 'source').rglob('*')):
        require(not path.is_symlink() and path.stat().st_mode & 0o222 == 0, 'entire_source_frozen')
    cohort = read(plan['matched_cohort']['path'])
    initial = base / 'common_initial'
    require(cohort['initial_directory'] == str(initial), 'single_common_initial_namespace')
    if config['phase'] == 'initialize':
        require(go.get('initialization') is None and not initial.exists(), 'initializer_once_no_existing_state')
    else:
        proof = go['initialization']
        expected = dict(initialized=initial / 'INITIALIZED.json', commit=initial / 'COMMIT.json',
            lifecycle=base / 'attempts/initialize-parented_learning-attempt1/LIFECYCLE.json')
        require(set(proof) == set(expected) and all(proof[name] == reference(path)
                for name, path in expected.items()), 'Main_bound_actual_common_initial_and_exit')
        lifecycle = bound(proof['lifecycle'])
        require(lifecycle['status'] == 'SERVICE_EXIT_VERIFIED' and lifecycle['cgroup_empty_verified'] is True
                and lifecycle['service_returncode'] == 0, 'initializer_exited_successfully_before_lanes')
        from gpu import orch_r150_matched_native as matched
        matched.verify_initialization_validation(plan, cohort, bound(proof['initialized']))
    return config, plan


@contextmanager
def exclusive_phase(config, plan):
    base = canonical(config['r158_base'])
    lock = os.open(BASE / ('.orch_r158_node4_device_' + str(plan['physical']) + '.lock'),
                   os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (base / 'control' / ('PHASE_ONCE_' + config['phase'] + '_' + plan['matched_arm'])).mkdir()
        yield
    finally:
        os.close(lock)


def execute(action, config_path, receipt_dir, main_go_path, main_go_sha256):
    require(action in ('supervise', 'contained', 'native'), 'explicit_execution_action')
    compiled = engine()
    compiled.validate(config_path, receipt_dir, main_go_path, main_go_sha256)
    config, plan = validate_extra(config_path, main_go_path)
    if action == 'supervise':
        require(os.getuid() == os.getgid() == 2524 and os.environ.get('CUDA_VISIBLE_DEVICES') == '',
                'unprivileged_CPU_supervisor')
        with exclusive_phase(config, plan):
            return compiled.supervise(config_path, receipt_dir=receipt_dir,
                main_go_path=main_go_path, main_go_sha256=main_go_sha256)
    return getattr(compiled, action)(config_path, receipt_dir=receipt_dir,
        main_go_path=main_go_path, main_go_sha256=main_go_sha256)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    source = commands.add_parser('source')
    for name in ('repository', 'destination', 'runtime', 'proof', 'capsule-original', 'repairs'):
        source.add_argument('--' + name, type=Path, required=True)
    preparing = commands.add_parser('prepare')
    for name in ('base', 'lease', 'cpu', 'intake', 'publication', 'repairs'):
        preparing.add_argument('--' + name, type=Path, required=True)
    preparing.add_argument('--initialization-source', type=Path)
    for action in ('supervise', 'contained', 'native'):
        command = commands.add_parser(action)
        for name in ('config', 'receipt-dir', 'main-go'):
            command.add_argument('--' + name, type=Path, required=True)
        command.add_argument('--main-go-sha256', required=True)
    args = parser.parse_args()
    if args.action == 'source':
        print(json.dumps(stage_source(args.repository, args.destination, args.runtime,
            args.proof, args.capsule_original, args.repairs)))
    elif args.action == 'prepare':
        print(json.dumps(prepare(args.base, args.lease, args.cpu, args.intake, args.publication,
                                 args.repairs, args.initialization_source)))
    else:
        execute(args.action, args.config, args.receipt_dir, args.main_go, args.main_go_sha256)


if __name__ == '__main__':
    main()
