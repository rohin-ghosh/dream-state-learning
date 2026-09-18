"""Bind separately reviewed receiving evidence without changing frozen V1 bytes."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
V1_SHA256 = '32ac4f130e58ba852f3c74f9c5000137065f335f1306df0094d49309b3d5afb1'
APPROVAL_SCHEMA = 'R170_MAIN_REVIEWED_RECEIVING_BINDING_V1'
AUTHORITY = 'BUILDER_CPU_EVIDENCE_BINDING_NOT_HUMAN_RATIFICATION'
NATIVE_PATH = 'gpu/orch_r125_continual_native.py'
NATIVE_EVIDENCE_KEY = 'research_loop/workers/r168_replay_candidates_20260917/NATIVE_cdb542.py'
SUPPORT_PINS = {
    'gpu/orch_r145_suffix_boundary.py': '632c519fd4c5a840d13b1e9503e61f512340ee9361ef95dcd43cbaf704ee0ce5',
    'gpu/orch_r145_suffix_loss.py': 'd5e69655fd30f3317d114bd4aab2025024fdfb1521664b536d54ad61069bf026',
}
REAL_TORCH_TEST = ('tests.test_orch_r168_targeted_replay.TargetedReplayTests.'
                   'test_actual_torch_CPU_applies_exact_baseline_then_four_extra_updates')


def encoded(document):
    return json.dumps(document, sort_keys=True, indent=2, allow_nan=False).encode() + b'\n'


def validate_assembly_inputs(approval, old_guard_ref, old_plan_ref, intake_hash, require):
    require(old_guard_ref == approval['old_guard_ref'] and old_plan_ref == approval['old_plan_ref']
            and intake_hash == approval['approved_intake_sha256'], 'reviewed_assembly_inputs_only')


def validate_receiving(evidence, approval, guard, plan, helpers, require):
    require(evidence.get('schema') == 'R175_ACTUAL_RECEIVING_CPU_V1'
            and evidence.get('status') == 'CPU_TESTS_PASS_NOT_ADMISSION', 'actual_receiving_status')
    for field in ('success', 'evidence_rebind_eligible', 'test_suite_success',
                  'source_unchanged_after_tests'):
        require(evidence.get(field) is True, 'positive_receiving:' + field)
    for field in ('full_source_approval', 'evaluator_admission', 'saved_state_ownership_established',
                  'saved_handoff_created', 'operational_GO_created', 'test_assertions_changed',
                  'numerical_tolerances_changed', 'startup_copied'):
        require(evidence.get(field) is False, 'no_scope_expansion:' + field)
    for field in ('failures', 'errors', 'original_test_methods_removed'):
        require(type(evidence.get(field)) is int and evidence[field] == 0, 'zero_' + field)
    require(not evidence.get('failure') and not evidence.get('failure_type')
            and not evidence.get('traceback') and evidence.get('skipped') == []
            and evidence.get('denied_runtime_operations') == [], 'no_failure_skip_or_denial')
    require(type(evidence.get('attempt_limit')) is int and evidence['attempt_limit'] == 1
            and evidence.get('retry_permitted') is False, 'one_consumed_receiving_attempt')
    require(evidence['old_guard_ref'] == approval['old_guard_ref']
            and evidence['old_plan_ref'] == approval['old_plan_ref'], 'same_receiving_guard_and_plan')
    require(evidence['old_source_root'] == plan['source_root']
            and evidence['old_life_root'] == plan['root']
            and evidence['hard_end_unix_unmodified'] == guard['hard_end_unix'], 'same_source_life_and_wall')
    require(evidence['runner_ref']['sha256'] == approval['receiving_runner_sha256'], 'reviewed_runner')
    require(evidence['train_fixture_ref']['sha256'] == approval['train_fixture_sha256'], 'reviewed_TRAIN_fixture')
    required_ids = approval['required_test_ids']
    outcomes = evidence['outcomes']
    require(len(required_ids) == len(set(required_ids)) == 85
            and type(evidence['tests_run']) is int and evidence['tests_run'] == len(required_ids)
            and sorted(entry['test'] for entry in outcomes) == sorted(required_ids)
            and all(entry == {'test': entry['test'], 'status': 'PASS'} for entry in outcomes),
            'complete_exact_test_coverage')
    require(set(evidence['tests']) == set(approval['original_test_sha256']), 'exact_test_file_set')
    for name, checksum in approval['original_test_sha256'].items():
        require(evidence['tests'][name]['original_sha256'] == checksum, 'original_test_hash:' + name)
        require(evidence['tests'][name] == approval['reviewed_test_records'][name],
                'reviewed_path_only_adaptations:' + name)
    torch = evidence['torch']
    require(torch['imported'] is True and torch['cuda_initialized'] is False
            and torch['real_torch_test'] == [{'test': REAL_TORCH_TEST, 'status': 'PASS'}],
            'actual_torch_CPU_exact_updates')
    require(evidence['environment']['CUDA_VISIBLE_DEVICES'] == ''
            and evidence['environment']['HF_HUB_OFFLINE'] == '1'
            and evidence['environment']['TRANSFORMERS_OFFLINE'] == '1', 'CPU_offline_environment')
    expected = dict(guard['source_pins'], **helpers)
    require(len(guard['source_pins']) == 1854 and len(expected) == 1857
            and not set(expected).intersection(SUPPORT_PINS), 'exact_old_source_plus_three_helpers')
    require(evidence['candidate_source_sha256'] == expected, 'complete_receiving_candidate_pins')
    manifest_hash = hashlib.sha256(encoded(expected)).hexdigest()
    require(evidence['candidate_source_manifest_sha256'] == manifest_hash
            == approval['candidate_source_manifest_sha256'], 'complete_candidate_manifest_hash')
    require(evidence['old_python_files_copied'] == 1854
            and evidence['added_python_files'] == helpers, 'only_three_added_runtime_files')
    expected_reads = {str(Path(plan['source_root']) / name): checksum
                      for name, checksum in guard['source_pins'].items()}
    expected_reads.update({approval[field]['path']: approval[field]['sha256']
                          for field in ('old_guard_ref', 'old_plan_ref')})
    bound_reads = evidence['receiving_bound_reads']
    require(len(bound_reads) == len(expected_reads)
            and len({entry['path'] for entry in bound_reads}) == len(expected_reads)
            and {entry['path']: entry['sha256'] for entry in bound_reads} == expected_reads
            and all(type(entry['bytes']) is int and 0 <= entry['bytes'] <= 2 * 1024 * 1024
                    for entry in bound_reads), 'complete_bounded_old_source_read_custody')
    require(type(evidence['operational_bytes_read']) is int
            and evidence['operational_bytes_read'] == sum(entry['bytes'] for entry in bound_reads)
            and evidence['operational_bytes_read'] <= 64 * 1024 * 1024, 'bound_source_reader_byte_accounting')
    scratch = Path(evidence['scratch'])
    source = Path(evidence['candidate_source_root'])
    require(scratch.is_absolute() and '..' not in scratch.parts and source == scratch / 'source',
            'actual_receiving_source_location')
    executed = evidence['executed_project_files']
    for name, record in executed.items():
        require(name in expected and record['path'] == str(source / name)
                and record['sha256'] == expected[name] and type(record['executions']) is int
                and record['executions'] > 0, 'executed_candidate_origin:' + name)
    for name, record in evidence['loaded_project_modules'].items():
        relative = name.replace('.', '/') + '.py'
        if relative not in expected and relative not in SUPPORT_PINS:
            relative = name.replace('.', '/') + '/__init__.py'
        if relative in SUPPORT_PINS:
            require(record == dict(path=str(scratch / 'test_support' / relative),
                                   sha256=SUPPORT_PINS[relative]), 'separate_imported_test_support')
        else:
            require(relative in expected and record == dict(path=str(source / relative),
                    sha256=expected[relative]), 'loaded_candidate_origin:' + name)
    dependencies = evidence['runtime_dependencies']
    require(set(dependencies) == {'gpu.orch_r108_guided_native', 'gpu.orch_r144_sleep_targets',
                                  'organism_v6.orch_r125_plain_context'}, 'exact_runtime_dependencies')
    for name, reference in dependencies.items():
        relative = name.replace('.', '/') + '.py'
        require(reference == dict(path=str(source / relative), sha256=expected[relative])
                and relative in executed, 'actual_executed_runtime_dependency:' + name)
    require(NATIVE_PATH in executed and set(helpers).issubset(executed), 'native_and_helpers_executed')
    require(set(evidence['negative_test_support']) == set(SUPPORT_PINS)
            and set(evidence['test_support_executed']) == set(SUPPORT_PINS), 'both_negative_test_helpers')
    for name, checksum in SUPPORT_PINS.items():
        reference = dict(path=str(scratch / 'test_support' / name), sha256=checksum)
        require(evidence['negative_test_support'][name] == dict(reference, runtime_candidate_member=False)
                and evidence['test_support_executed'][name] == dict(reference,
                    role='NEGATIVE_TEST_SUPPORT_NOT_RUNTIME'), 'negative_test_support_origin')
    require(evidence['allowed_runtime_probes'] == approval['reviewed_runtime_probes'],
            'only_reviewed_readonly_library_probes')
    return dict(source_sha256=dict(expected, **{NATIVE_EVIDENCE_KEY: expected[NATIVE_PATH]}))


def assembly_namespace(approval_ref):
    raw = (HERE / 'ASSEMBLY.py').read_bytes()
    if hashlib.sha256(raw).hexdigest() != V1_SHA256:
        raise ValueError('immutable_ASSEMBLY_V1')
    namespace = dict(__name__='r170_assembly_v1_receiving_bound', __file__=str(HERE / 'ASSEMBLY.py'))
    exec(compile(raw, namespace['__file__'], 'exec'), namespace)
    replay = namespace['replay']
    approval = replay.read_bound(approval_ref)
    replay.require(approval['schema'] == APPROVAL_SCHEMA and approval['authority'] == AUTHORITY
                   and approval['assembly_v1_sha256'] == V1_SHA256,
                   'explicit_Main_receiving_evidence_binding')
    namespace['_bytes'](approval['independent_review_ref'])
    historical_cpu = namespace['_cpu']
    original_inputs = namespace['_inputs']

    def reviewed_inputs(old_guard_ref, old_plan_ref, approved_intake_sha256, now):
        validate_assembly_inputs(approval, old_guard_ref, old_plan_ref,
                                 approved_intake_sha256, replay.require)
        return original_inputs(old_guard_ref, old_plan_ref, approved_intake_sha256, now)

    def receiving_cpu(reference):
        current_approval = replay.read_bound(approval_ref)
        replay.require(current_approval == approval and reference == approval['receiving_cpu_ref'],
                       'exact_reviewed_receiving_reference')
        namespace['_bytes'](approval['independent_review_ref'])
        historical_cpu(approval['historical_cpu_ref'])
        evidence = replay.read_bound(reference)
        guard = replay.read_bound(approval['old_guard_ref'])
        plan = replay.read_bound(approval['old_plan_ref'])
        return validate_receiving(evidence, approval, guard, plan, namespace['HELPER_PINS'], replay.require)

    namespace.update(_cpu=receiving_cpu, _inputs=reviewed_inputs)
    return namespace
