"""Local R170 staging only; Main owns saved-state, source-review and admission gates.

Call scaffold_immutable_files before handoff, then finalize_selection_bundle at
the actual completed readout boundary. build_selection_bundle combines these
steps. No GO is written unless bind_main_go receives Main's exact scope dict
(the selection bundle exposes expected_main_go_scope). None of these functions
imports staged source, loads checkpoint payloads, or starts a process/model.
"""

from copy import deepcopy
import hashlib
import math
import os
from pathlib import Path
import stat
from types import SimpleNamespace

from gpu import orch_r168_targeted_replay_driver as driver


integration = driver.integration
replay = driver.replay
REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_ROOT = REPO_ROOT / 'research_loop/workers/r168_replay_candidates_20260917'
CPU_SHA256 = 'fbf830c6fc398a863296fe79aed9d587bc7393c2b9f76675604ba52177e5225c'
DRIVER_SHA256 = '43295e6b98ebb10c7e99247e8b26720948b25556d5da13e34759c1f2d0088351'
GPU_UUID = 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821'
HELPER_PINS = {
    'gpu/orch_r168_targeted_replay.py': integration.ARM_SHA256,
    'gpu/orch_r168_targeted_replay_native.py': driver.INTEGRATION_SHA256,
    'gpu/orch_r168_targeted_replay_driver.py': DRIVER_SHA256,
}
NATIVE_PATH = 'gpu/orch_r125_continual_native.py'
GUARD_PATH = 'gpu/orch_r125_continual_guard.py'
DISCLAIMERS = dict(saved_state_ownership_verified=False, boundary_admitted=False,
    full_source_approved=False, receiving_cpu_gate_passed=False,
    gpu_used=False, model_called=False, human_ratification_created=False)


def file_ref(path):
    """Hash bounded regular local metadata without following symlinks or loading state."""
    path = replay.canonical(path)
    parent = replay.directory_fd(path.parent)
    try:
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                             dir_fd=parent)
        with os.fdopen(descriptor, 'rb') as stream:
            before = os.fstat(stream.fileno())
            replay.require(stat.S_ISREG(before.st_mode) and before.st_size <= replay.MAX_METADATA_BYTES,
                           'bounded_regular_reference')
            raw = stream.read(replay.MAX_METADATA_BYTES + 1)
            after = os.fstat(stream.fileno())
            replay.require(len(raw) == before.st_size and all(getattr(before, field) == getattr(after, field)
                for field in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')),
                'reference_changed_during_read')
    finally:
        os.close(parent)
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())


def _bytes(reference):
    path = replay.reference_fields(reference)
    return integration._source_bytes(SimpleNamespace(__file__=str(path)), reference['sha256'])


def _write(path, document):
    replay.write_once(path, document)
    return file_ref(path)


def _write_bytes(path, raw):
    path = replay.canonical(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    parent = replay.directory_fd(path.parent)
    try:
        descriptor = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=parent)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(parent)
    finally:
        os.close(parent)


def _time(now, hard_end):
    replay.require(all(type(value) in (int, float) and math.isfinite(value)
                       for value in (now, hard_end)) and 0 <= now < hard_end,
                   'finite_time_inside_existing_hardwall')


def _relative(name):
    replay.require(type(name) is str and name and '\\' not in name, 'relative_python_pin')
    path = Path(name)
    replay.require(not path.is_absolute() and '..' not in path.parts
        and str(path) == name and path.suffix == '.py', 'relative_python_pin')
    return path


def _inputs(old_guard_ref, old_plan_ref, approved_intake_sha256, now):
    replay.require(replay.valid_hash(approved_intake_sha256), 'predeclared_intake_hash')
    guard = replay.read_bound(old_guard_ref)
    plan = replay.read_bound(old_plan_ref)
    replay.require(guard['schema'] == 'R125_CONTINUAL_GUARD_V1'
        and dict(path=guard['plan_path'], sha256=guard['plan_sha256']) == old_plan_ref,
        'old_guard_exact_plan_reference')
    replay.require(plan['root'] == driver.LIFE_ROOT and type(plan['physical']) is int
        and plan['physical'] == 1 and plan['gpu_uuid'] == GPU_UUID
        and plan['presleep_variant'] == 'reread_select'
        and plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 1
        and plan['anchor_lambda'] == 0.25 and plan.get('preupdate_recovery') is None
        and not plan.get('authorized_wall_extension'),
        'exact_creative_reread_physical1_baseline')
    replay.require(guard['hard_end_unix'] == plan['hard_end_unix'], 'unchanged_existing_hardwall')
    _time(now, plan['hard_end_unix'])
    old_source = replay.canonical(plan['source_root'])
    startup = plan['startup_context']
    replay.require(replay.canonical(startup['path']) == old_source / 'STARTUP.md',
                   'only_pinned_STARTUP_md')
    pins = guard['source_pins']
    replay.require(type(pins) is dict and pins and not set(pins).intersection(HELPER_PINS),
                   'old_source_without_replay_helpers')
    for name, checksum in pins.items():
        _relative(name)
        replay.require(replay.valid_hash(checksum), 'known_source_pin_hash')
    replay.require(pins.get(NATIVE_PATH) == integration.NATIVE_SHA256
        and pins.get(GUARD_PATH) == driver.GUARD_SHA256, 'frozen_native_and_original_guard')
    allocation_ref = dict(path=guard['allocation_path'], sha256=guard['allocation_sha256'])
    allocation = replay.read_bound(allocation_ref)
    replay.require(allocation['plan_sha256'] == old_plan_ref['sha256']
        and allocation['physical'] == plan['physical'] and allocation['gpu_uuid'] == plan['gpu_uuid'],
        'old_allocation_exact_plan_and_device')
    return guard, plan, allocation


def _cpu(reference):
    replay.require(reference['sha256'] == CPU_SHA256, 'approved_local_CPU_evidence_hash')
    evidence = replay.read_bound(reference)
    replay.require(evidence['schema'] == 'R168_ISOLATED_NATIVE_CPU_V1'
        and evidence['failures'] == 0 and evidence['errors'] == 0
        and evidence['native_fixture_byte_verified'] is True, 'bound_native_CPU_evidence')
    return evidence


def _runtime(source, evidence):
    pins = evidence['source_sha256']
    replay.require(pins['research_loop/workers/r168_replay_candidates_20260917/NATIVE_cdb542.py']
                   == integration.NATIVE_SHA256, 'CPU_native_contract')
    _bytes(dict(path=str(source / NATIVE_PATH), sha256=integration.NATIVE_SHA256))
    for name, checksum in HELPER_PINS.items():
        if name != 'gpu/orch_r168_targeted_replay_driver.py':
            replay.require(pins.get(name) == checksum, 'CPU_replay_helper_contract')
        _bytes(dict(path=str(source / name), sha256=checksum))
    for name, checksum in pins.items():
        if name.startswith(('gpu/', 'organism_v6/')):
            _bytes(dict(path=str(source / _relative(name)), sha256=checksum))
    dependencies = {}
    for name in integration.DEPENDENCIES:
        relative = name.replace('.', '/') + '.py'
        actual = file_ref(source / relative)['sha256']
        replay.require(actual == pins[relative], 'runtime_dependency_matches_CPU_evidence')
        dependencies[name] = actual
    return dict(schema='R168_NATIVE_SLEEP_RUNTIME_V1', native_sha256=integration.NATIVE_SHA256,
        arm_sha256=integration.ARM_SHA256, integration_sha256=driver.INTEGRATION_SHA256,
        dependencies=dependencies)


def _inventory(source, expected, startup_hash):
    allowed = set(expected) | {'STARTUP.md'}
    directories = {str(parent) for name in allowed for parent in Path(name).parents
                   if str(parent) != '.'}
    observed = set()
    for path in source.rglob('*'):
        relative = str(path.relative_to(source))
        replay.require(not path.is_symlink(), 'no_source_symlinks')
        if path.is_dir():
            replay.require(relative in directories, 'no_unvetted_source_directories')
        else:
            replay.require(path.is_file() and relative in allowed, 'source_whitelist_only')
            observed.add(relative)
    replay.require(observed == allowed, 'complete_source_whitelist')
    actual = {name: file_ref(source / name)['sha256'] for name in sorted(expected)}
    replay.require(actual == expected, 'source_pin_delta_or_unknown_hash')
    _bytes(dict(path=str(source / 'STARTUP.md'), sha256=startup_hash))
    return actual


def scaffold_immutable_files(*, old_guard_ref, old_plan_ref, new_source_root, output_root,
                            approved_intake_sha256, now, helper_source_root=REPO_ROOT,
                            cpu_evidence_ref=None):
    """Copy only bound Python/STARTUP bytes and the exact three reviewed helpers.

    PLAN changes only source_root/startup path; ALLOCATION changes only its
    plan hash. The original guard is copied now and patched only by bind_main_go.
    Outputs are create-only; a failed/partial stage is not reusable authority.
    """
    guard, old_plan, allocation = _inputs(old_guard_ref, old_plan_ref, approved_intake_sha256, now)
    source, output, helpers = map(replay.canonical, (new_source_root, output_root, helper_source_root))
    old_source = replay.canonical(old_plan['source_root'])
    life = replay.canonical(old_plan['root'])
    for destination in (source, output):
        replay.require(not destination.exists(), 'fresh_staging_destination')
        replay.require(not any(destination.is_relative_to(protected)
            or protected.is_relative_to(destination) for protected in (old_source, life, helpers)),
            'staging_outside_existing_source_and_life')
    replay.require(not output.is_relative_to(source),
                   'external_binding_metadata_outside_source')
    cpu_evidence_ref = cpu_evidence_ref or dict(path=str(EVIDENCE_ROOT / 'NATIVE_CPU_FINAL.json'),
                                               sha256=CPU_SHA256)
    evidence = _cpu(cpu_evidence_ref)
    for module, checksum in ((driver, DRIVER_SHA256), (integration, driver.INTEGRATION_SHA256),
                             (replay, integration.ARM_SHA256)):
        integration._source_bytes(module, checksum)
    files = {name: _bytes(dict(path=str(old_source / name), sha256=checksum))
             for name, checksum in guard['source_pins'].items()}
    files['STARTUP.md'] = _bytes({key: old_plan['startup_context'][key] for key in ('path', 'sha256')})
    files.update({name: _bytes(dict(path=str(helpers / name), sha256=checksum))
                  for name, checksum in HELPER_PINS.items()})
    for name, checksum in evidence['source_sha256'].items():
        if name.startswith(('gpu/', 'organism_v6/')):
            replay.require(name in files and hashlib.sha256(files[name]).hexdigest() == checksum,
                           'source_candidate_matches_native_CPU_evidence')
    output.mkdir(parents=True, exist_ok=False)
    source.mkdir(parents=True, exist_ok=False)
    for name, raw in files.items():
        _write_bytes(source / name, raw)
    expected = dict(guard['source_pins'], **HELPER_PINS)
    pins = _inventory(source, expected, old_plan['startup_context']['sha256'])
    runtime = _runtime(source, evidence)
    plan = deepcopy(old_plan)
    plan['source_root'] = str(source)
    plan['startup_context']['path'] = str(source / 'STARTUP.md')
    plan_ref = _write(output / 'PROPOSED_PLAN.json', plan)
    allocation['plan_sha256'] = plan_ref['sha256']
    scaffold = dict(schema='R170_REPLAY_SOURCE_SCAFFOLD_V1', created_unix=now,
        old_guard_ref=deepcopy(old_guard_ref), old_plan_ref=deepcopy(old_plan_ref),
        source_root=str(source), output_root=str(output), source_pins=pins,
        approved_intake_sha256=approved_intake_sha256, cpu_evidence_ref=deepcopy(cpu_evidence_ref),
        plan_ref=plan_ref, allocation_ref=_write(output / 'ALLOCATION.json', allocation),
        runtime_ref=_write(output / 'RUNTIME.json', runtime), main_go_created=False, **DISCLAIMERS)
    return dict(scaffold, scaffold_ref=_write(output / 'SCAFFOLD.json', scaffold))


def _check_scaffold(scaffold_ref, approved_intake_sha256, now):
    scaffold = replay.read_bound(scaffold_ref)
    replay.require(scaffold['schema'] == 'R170_REPLAY_SOURCE_SCAFFOLD_V1'
        and scaffold['approved_intake_sha256'] == approved_intake_sha256,
        'exact_predeclared_scaffold_intake')
    guard, old_plan, allocation = _inputs(scaffold['old_guard_ref'], scaffold['old_plan_ref'],
                                         approved_intake_sha256, now)
    source, output = map(replay.canonical, (scaffold['source_root'], scaffold['output_root']))
    replay.require(replay.reference_fields(scaffold_ref) == output / 'SCAFFOLD.json'
        and not output.is_relative_to(source), 'external_scaffold_reference')
    for field, filename in (('plan_ref', 'PROPOSED_PLAN.json'), ('allocation_ref', 'ALLOCATION.json'),
                            ('runtime_ref', 'RUNTIME.json')):
        replay.require(replay.reference_fields(scaffold[field]) == output / filename,
                       'exact_external_scaffold_paths')
    plan = deepcopy(old_plan)
    plan['source_root'] = str(source)
    plan['startup_context']['path'] = str(source / 'STARTUP.md')
    replay.require(replay.encoded(replay.read_bound(scaffold['plan_ref'])) == replay.encoded(plan),
                   'plan_paths_only_delta')
    allocation['plan_sha256'] = scaffold['plan_ref']['sha256']
    replay.require(replay.encoded(replay.read_bound(scaffold['allocation_ref'])) == replay.encoded(allocation),
                   'allocation_plan_hash_only')
    expected = dict(guard['source_pins'], **HELPER_PINS)
    replay.require(scaffold['source_pins'] == expected, 'scaffold_exact_source_pins')
    _inventory(source, expected, old_plan['startup_context']['sha256'])
    runtime = _runtime(source, _cpu(scaffold['cpu_evidence_ref']))
    replay.require(replay.read_bound(scaffold['runtime_ref']) == runtime, 'actual_source_runtime_binding')
    return scaffold, guard, plan


def finalize_selection_bundle(*, scaffold_ref, boundary_ref, checkpoint_ref,
                              approved_intake_sha256, now, main_go_scope=None):
    """Freeze the actual SLEEP_COMPLETE/COMMIT's next cycle, never a predicted one."""
    scaffold, guard, plan = _check_scaffold(scaffold_ref, approved_intake_sha256, now)
    replay.require(now >= scaffold['created_unix'], 'boundary_finalization_after_scaffold')
    selection = replay.freeze_selection(own_root=plan['root'], boundary_ref=boundary_ref,
        checkpoint_ref=checkpoint_ref, dose=4, plan_sha256=scaffold['plan_ref']['sha256'],
        runtime_sha256=scaffold['runtime_ref']['sha256'], frozen_unix=now,
        row_objects=[dict(segment=118, object_id='chrysanthemum-petal', selection_kind='OBJECT_REPLAY',
                          support_event_ids=['child:segment:118'])])
    selected = selection['selected'][0]
    replay.require(selected['source_sha256'] == integration.SOURCE_SHA256
        and selected['row_sha256'] == integration.ROW_SHA256, 'whole_untouched_exact_row118')
    output = replay.canonical(scaffold['output_root'])
    selection_ref = _write(output / 'SELECTION.json', selection)
    scope = {key: selection[key] for key in ('life_root', 'life_role', 'target_cycle',
                                            'plan_sha256', 'runtime_sha256')}
    scope.update(approved_intake_sha256=approved_intake_sha256, not_before=now,
                 expires=plan['hard_end_unix'])
    bundle = dict(schema='R170_REPLAY_SELECTION_BUNDLE_V1', scaffold_ref=deepcopy(scaffold_ref),
        plan_ref=scaffold['plan_ref'], runtime_ref=scaffold['runtime_ref'], selection_ref=selection_ref,
        source_pins=scaffold['source_pins'], source_cycle=selection['source_cycle'],
        target_cycle=selection['target_cycle'], expected_main_go_scope=scope,
        main_go_created=False, **DISCLAIMERS)
    bundle_ref = _write(output / 'SELECTION_BUNDLE.json', bundle)
    result = dict(bundle, selection_bundle_ref=bundle_ref)
    if main_go_scope is not None:
        result.update(bind_main_go(selection_bundle_ref=bundle_ref, main_go_scope=main_go_scope, now=now))
    return result


def bind_main_go(*, selection_bundle_ref, main_go_scope, now):
    """Only serialize explicit Main scope; this does not ratify or admit anything.

    main_go_scope must exactly equal expected_main_go_scope from the selection
    bundle: life_root, life_role, target_cycle, plan_sha256, runtime_sha256,
    approved_intake_sha256, not_before and expires (the unchanged hardwall).
    Main must supply that dict explicitly; do not treat its presence in metadata
    as authorization to call this function.
    """
    bundle = replay.read_bound(selection_bundle_ref)
    replay.require(bundle['schema'] == 'R170_REPLAY_SELECTION_BUNDLE_V1'
        and type(main_go_scope) is dict
        and replay.encoded(main_go_scope) == replay.encoded(bundle['expected_main_go_scope']),
        'explicit_Main_exact_scope_required')
    scaffold, guard, plan = _check_scaffold(bundle['scaffold_ref'],
                                           main_go_scope['approved_intake_sha256'], now)
    output, source = map(replay.canonical, (scaffold['output_root'], scaffold['source_root']))
    replay.require(replay.reference_fields(selection_bundle_ref) == output / 'SELECTION_BUNDLE.json'
        and replay.reference_fields(bundle['selection_ref']) == output / 'SELECTION.json',
        'exact_external_selection_paths')
    selection = replay.validate_selection(replay.read_bound(bundle['selection_ref']))
    replay.require(selection['life_root'] == driver.LIFE_ROOT
        and selection['plan_sha256'] == scaffold['plan_ref']['sha256']
        and selection['runtime_sha256'] == scaffold['runtime_ref']['sha256']
        and main_go_scope['expires'] == plan['hard_end_unix'], 'exact_selected_plan_runtime_hardwall')
    selected = selection['selected']
    replay.require(len(selected) == 1 and selected[0]['segment'] == 118
        and selected[0]['source_sha256'] == integration.SOURCE_SHA256
        and selected[0]['row_sha256'] == integration.ROW_SHA256
        and selected[0]['selection_kind'] == 'OBJECT_REPLAY'
        and selected[0]['extra_presentations'] == 4, 'one_exact_original_object_four_extras')
    go = dict(deepcopy(main_go_scope), schema=replay.GO_SCHEMA,
              action='ONE_EXPERIMENTAL_TARGETED_REPLAY_SLEEP', selection=bundle['selection_ref'])
    replay.validate_go(go, bundle['selection_ref'], selection, scaffold['approved_intake_sha256'], now)
    for name in ('MAIN_GO.json', 'DRIVER_BINDING.json', 'PROPOSED_GUARD.json', 'BOUND_BUNDLE.json',
                 'STAGED_SOURCE.json'):
        replay.require(not (output / name).exists(), 'create_only_Main_binding')
    go_ref = _write(output / 'MAIN_GO.json', go)
    binding = dict(schema=driver.BINDING_SCHEMA, life_root=driver.LIFE_ROOT, life_role=replay.ROLE,
        resume=True, plan_ref=scaffold['plan_ref'], runtime_ref=scaffold['runtime_ref'],
        selection_ref=bundle['selection_ref'], main_go_ref=go_ref,
        approved_intake_sha256=scaffold['approved_intake_sha256'], native_sha256=integration.NATIVE_SHA256,
        integration_sha256=driver.INTEGRATION_SHA256, arm_sha256=integration.ARM_SHA256,
        driver_sha256=DRIVER_SHA256)
    binding_ref = _write(output / 'DRIVER_BINDING.json', binding)
    guard_path = source / GUARD_PATH
    original = _bytes(dict(path=str(guard_path), sha256=driver.GUARD_SHA256))
    patched = driver.patch_guard(original, binding_ref)
    temporary = guard_path.with_name(guard_path.name + '.r170-staged')
    _write_bytes(temporary, patched)
    os.replace(temporary, guard_path)
    expected = dict(scaffold['source_pins'])
    expected[GUARD_PATH] = hashlib.sha256(patched).hexdigest()
    pins = _inventory(source, expected, plan['startup_context']['sha256'])
    config = dict(guard, plan_path=scaffold['plan_ref']['path'], plan_sha256=scaffold['plan_ref']['sha256'],
        allocation_path=scaffold['allocation_ref']['path'], allocation_sha256=scaffold['allocation_ref']['sha256'],
        attempt_dir=str(output), resume=True, source_pins=pins)
    result = dict(schema='R170_REPLAY_BOUND_BUNDLE_V1', selection_bundle_ref=deepcopy(selection_bundle_ref),
        plan_ref=scaffold['plan_ref'], allocation_ref=scaffold['allocation_ref'],
        runtime_ref=scaffold['runtime_ref'], selection_ref=bundle['selection_ref'],
        main_go_ref=go_ref, driver_binding_ref=binding_ref,
        guard_ref=_write(output / 'PROPOSED_GUARD.json', config),
        source_pins=pins, main_go_created=True, **DISCLAIMERS)
    result['config_ref'] = result['guard_ref']
    result['driver_binding'] = result['driver_binding_ref']
    result['staged_source_ref'] = _write(output / 'STAGED_SOURCE.json',
        dict(schema='R170_REPLAY_STAGED_SOURCE_V1', guard_sha256=result['guard_ref']['sha256'],
             driver_binding=binding_ref, source_pins=pins, **DISCLAIMERS))
    return dict(result, bound_bundle_ref=_write(output / 'BOUND_BUNDLE.json', result))


def build_selection_bundle(*, old_guard_ref, old_plan_ref, new_source_root, output_root,
                           boundary_ref, checkpoint_ref, approved_intake_sha256, now,
                           helper_source_root=REPO_ROOT, cpu_evidence_ref=None, main_go_scope=None):
    """Convenience for a fresh local stage when the real boundary is already available."""
    scaffold = scaffold_immutable_files(old_guard_ref=old_guard_ref, old_plan_ref=old_plan_ref,
        new_source_root=new_source_root, output_root=output_root,
        approved_intake_sha256=approved_intake_sha256, now=now,
        helper_source_root=helper_source_root, cpu_evidence_ref=cpu_evidence_ref)
    return finalize_selection_bundle(scaffold_ref=scaffold['scaffold_ref'], boundary_ref=boundary_ref,
        checkpoint_ref=checkpoint_ref, approved_intake_sha256=approved_intake_sha256,
        now=now, main_go_scope=main_go_scope)
