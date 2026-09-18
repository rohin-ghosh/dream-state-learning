"""Independent normalization/wiring probes; no actual approval, scaffold, selection or GO."""

import ast
from copy import deepcopy
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ASSEMBLY_SHA = '3e9da0d121cb53b76ad1411f9c6e942923892363cb5dcde591674c7ac881347e'
V1_SHA = '32ac4f130e58ba852f3c74f9c5000137065f335f1306df0094d49309b3d5afb1'
FAILED = HERE.parent / 'r174_receiving_cpu_repair_20260917/ACTUAL_RECEIVING_CPU.json'
FAILED_SHA = 'd14cda179688a3d145ea1ae5e8039c4e5c4dd3f530ded4d28ac523051a2e28dd'
ACTUAL = HERE.parent / 'r175_receiving_ldconfig_20260917/ACTUAL_RECEIVING_CPU.json'
ACTUAL_SHA = '8f60e4ae3d9e21766b46f816822852285b2f757a0cb952089184d38f1df9b1b3'


def load(path, checksum=None):
    raw = path.read_bytes()
    if checksum is not None:
        assert hashlib.sha256(raw).hexdigest() == checksum
    specification = importlib.util.spec_from_file_location('independent_' + path.stem, path)
    module = importlib.util.module_from_spec(specification)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


@pytest.fixture
def proposal():
    assembly = load(HERE / 'ASSEMBLY_V2.py', ASSEMBLY_SHA)
    raw = ACTUAL.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ACTUAL_SHA
    assert hashlib.sha256(FAILED.read_bytes()).hexdigest() == FAILED_SHA
    evidence = json.loads(raw)
    helpers = deepcopy(evidence['added_python_files'])
    guard = dict(source_pins={name: checksum for name, checksum in evidence['candidate_source_sha256'].items()
        if name not in helpers}, hard_end_unix=evidence['hard_end_unix_unmodified'])
    plan = dict(source_root=evidence['old_source_root'], root=evidence['old_life_root'])
    approval = dict(old_guard_ref=deepcopy(evidence['old_guard_ref']), old_plan_ref=deepcopy(evidence['old_plan_ref']),
        receiving_runner_sha256=evidence['runner_ref']['sha256'],
        train_fixture_sha256=evidence['train_fixture_ref']['sha256'],
        required_test_ids=sorted(entry['test'] for entry in evidence['outcomes']),
        original_test_sha256={name: record['original_sha256'] for name, record in evidence['tests'].items()},
        reviewed_test_records=deepcopy(evidence['tests']),
        candidate_source_manifest_sha256=evidence['candidate_source_manifest_sha256'],
        reviewed_runtime_probes=deepcopy(evidence['allowed_runtime_probes']), approved_intake_sha256='1' * 64)
    yield SimpleNamespace(module=assembly, evidence=evidence, approval=approval, guard=guard, plan=plan, helpers=helpers)
    assert ACTUAL.read_bytes() == raw
    assert hashlib.sha256(FAILED.read_bytes()).hexdigest() == FAILED_SHA


def validate(fixture, evidence=None):
    return fixture.module.validate_receiving(fixture.evidence if evidence is None else evidence,
        fixture.approval, fixture.guard, fixture.plan, fixture.helpers, require)


def test_failed_R174_refuses_and_actual_R175_normalizes_without_source_drift(proposal):
    with pytest.raises(ValueError, match='actual_receiving_status'):
        validate(proposal, json.loads(FAILED.read_bytes()))
    normalized = validate(proposal)['source_sha256']
    assert normalized['organism_v6/orch_r125_plain_context.py'].startswith('b3859e')
    assert not set(proposal.module.SUPPORT_PINS).intersection(normalized)
    assert normalized == dict(proposal.evidence['candidate_source_sha256'],
        **{proposal.module.NATIVE_EVIDENCE_KEY: proposal.evidence['candidate_source_sha256'][proposal.module.NATIVE_PATH]})


def test_positive_R175_schema_is_compatible_without_weakening_other_gates(proposal):
    changed = dict(proposal.evidence, schema='R175_ACTUAL_RECEIVING_CPU_V1')
    assert validate(proposal, changed) == validate(proposal)


def test_historical_schema_cannot_replace_actual_R175_schema(proposal):
    with pytest.raises(ValueError, match='actual_receiving_status'):
        validate(proposal, dict(proposal.evidence, schema='R173_ACTUAL_RECEIVING_CPU_V1'))


@pytest.mark.parametrize('field,value', [('retry_permitted', True), ('attempt_limit', 2)])
def test_inconsistent_attempt_scope_refuses(proposal, field, value):
    with pytest.raises(ValueError):
        validate(proposal, dict(proposal.evidence, **{field: value}))


def test_contradictory_added_helper_hash_refuses(proposal):
    evidence = deepcopy(proposal.evidence)
    evidence['added_python_files']['gpu/orch_r168_targeted_replay_driver.py'] = '0' * 64
    with pytest.raises(ValueError):
        validate(proposal, evidence)


def test_missing_read_custody_with_over_limit_counter_refuses(proposal):
    evidence = dict(proposal.evidence, receiving_bound_reads=[], operational_bytes_read=65 * 1024 * 1024)
    with pytest.raises(ValueError):
        validate(proposal, evidence)


@pytest.mark.parametrize('mutation', ['duplicate', 'wrong_hash', 'oversize_file', 'negative_bytes',
                                    'boolean_bytes', 'wrong_sum', 'over_total'])
def test_full_read_census_and_each_byte_bound_refuses_independently(proposal, mutation):
    evidence = deepcopy(proposal.evidence)
    reads = evidence['receiving_bound_reads']
    if mutation == 'duplicate':
        reads[-1] = deepcopy(reads[0])
    elif mutation == 'wrong_hash':
        reads[0]['sha256'] = '0' * 64
    elif mutation == 'oversize_file':
        reads[0]['bytes'] = 2 * 1024 * 1024 + 1
    elif mutation == 'negative_bytes':
        reads[0]['bytes'] = -1
    elif mutation == 'boolean_bytes':
        reads[0]['bytes'] = True
    elif mutation == 'wrong_sum':
        evidence['operational_bytes_read'] += 1
    elif mutation == 'over_total':
        for record in reads[:33]:
            record['bytes'] = 2 * 1024 * 1024
    if mutation != 'wrong_sum':
        evidence['operational_bytes_read'] = sum(record['bytes'] for record in reads)
    with pytest.raises(ValueError):
        validate(proposal, evidence)


@pytest.fixture
def bound_namespace(proposal, tmp_path):
    module = proposal.module
    historical_path = REPO / 'research_loop/workers/r168_replay_candidates_20260917/NATIVE_CPU_FINAL.json'
    historical = dict(path=str(historical_path), sha256=hashlib.sha256(historical_path.read_bytes()).hexdigest())
    report = tmp_path / 'SYNTHETIC_REVIEW_NOT_FOR_STAGING.txt'
    report.write_text('Synthetic unit-test review bytes only; not operational approval.\n')
    review_ref = dict(path=str(report), sha256=hashlib.sha256(report.read_bytes()).hexdigest())
    receiving_ref = dict(path=str(tmp_path / 'IN_MEMORY_ONLY_RECEIVING.json'), sha256='2' * 64)
    approval_ref = dict(path=str(tmp_path / 'IN_MEMORY_ONLY_APPROVAL.json'), sha256='3' * 64)
    approval = dict(deepcopy(proposal.approval), schema=module.APPROVAL_SCHEMA, authority=module.AUTHORITY,
        assembly_v1_sha256=V1_SHA, independent_review_ref=review_ref,
        historical_cpu_ref=historical, receiving_cpu_ref=receiving_ref)
    baseline = dict(__name__='independent_original_assembly', __file__=str(HERE / 'ASSEMBLY.py'))
    raw = HERE.joinpath('ASSEMBLY.py').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == V1_SHA
    exec(compile(raw, baseline['__file__'], 'exec'), baseline)
    real_read = baseline['replay'].read_bound
    events = []

    def read(reference):
        events.append(deepcopy(reference))
        if reference == approval_ref:
            return deepcopy(approval)
        if reference == receiving_ref:
            return deepcopy(proposal.evidence)
        if reference == historical:
            return real_read(reference)
        if reference == approval['old_guard_ref']:
            return deepcopy(proposal.guard)
        if reference == approval['old_plan_ref']:
            return deepcopy(proposal.plan)
        raise ValueError('not_a_test_fixture_reference')

    with mock.patch.object(baseline['replay'], 'read_bound', side_effect=read):
        namespace = module.assembly_namespace(approval_ref)
        yield SimpleNamespace(proposal=proposal, namespace=namespace, baseline=baseline, events=events,
            approval=approval, approval_ref=approval_ref, receiving_ref=receiving_ref,
            historical=historical, report=report, tmp_path=tmp_path)
    assert not Path(approval_ref['path']).exists() and not Path(receiving_ref['path']).exists()


def test_namespace_changes_only_cpu_and_stricter_inputs_with_original_globals(bound_namespace):
    fixture = bound_namespace
    namespace, baseline = fixture.namespace, fixture.baseline
    functions = [node.name for node in ast.parse(HERE.joinpath('ASSEMBLY.py').read_bytes()).body
                 if isinstance(node, ast.FunctionDef)]
    changed = {name for name in functions if namespace[name].__code__ != baseline[name].__code__}
    assert changed == {'_cpu', '_inputs'}
    for name in set(functions) - changed:
        assert namespace[name].__globals__ is namespace
        assert namespace[name].__defaults__ == baseline[name].__defaults__
        assert namespace[name].__kwdefaults__ == baseline[name].__kwdefaults__
    for name, captured in (('_cpu', 'historical_cpu'), ('_inputs', 'original_inputs')):
        original = inspect.getclosurevars(namespace[name]).nonlocals[captured]
        assert original.__code__ == baseline[name].__code__ and original.__globals__ is namespace
    assert namespace['scaffold_immutable_files'].__kwdefaults__['cpu_evidence_ref'] is None


def test_both_receiving_and_frozen_historical_evidence_are_rechecked(bound_namespace):
    fixture = bound_namespace
    fixture.events.clear()
    normalized = fixture.namespace['_cpu'](fixture.receiving_ref)
    assert normalized == validate(fixture.proposal)
    assert fixture.events == [fixture.approval_ref, fixture.historical, fixture.receiving_ref,
                              fixture.approval['old_guard_ref'], fixture.approval['old_plan_ref']]
    with pytest.raises(ValueError, match='exact_reviewed_receiving_reference'):
        fixture.namespace['_cpu'](fixture.historical)
    fixture.approval['historical_cpu_ref'] = dict(fixture.historical, sha256='0' * 64)
    with pytest.raises(ValueError, match='exact_reviewed_receiving_reference'):
        fixture.namespace['_cpu'](fixture.receiving_ref)


def test_changed_independent_review_refuses_before_reading_receiving_or_historical(bound_namespace):
    fixture = bound_namespace
    fixture.report.write_text('Changed synthetic review bytes, still not approval.\n')
    fixture.events.clear()
    with pytest.raises(ValueError):
        fixture.namespace['_cpu'](fixture.receiving_ref)
    assert fixture.events == [fixture.approval_ref]


@pytest.mark.parametrize('position', [0, 1, 2])
def test_wrong_guard_plan_or_intake_refuses_before_original_input_reads(bound_namespace, position):
    fixture = bound_namespace
    arguments = [fixture.approval['old_guard_ref'], fixture.approval['old_plan_ref'], '1' * 64, 0]
    arguments[position] = 'not_approved'
    fixture.events.clear()
    with pytest.raises(ValueError, match='reviewed_assembly_inputs_only'):
        fixture.namespace['_inputs'](*arguments)
    assert fixture.events == []


def test_current_scaffold_wiring_supplies_receiving_reference_and_metadata_only():
    tree = ast.parse(HERE.joinpath('SCAFFOLD_V2_OPERATOR.py').read_bytes())
    execute = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'execute')
    calls = [node for node in ast.walk(execute) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Subscript) and isinstance(node.func.value, ast.Name)
             and node.func.value.id == 'assembly']
    assert [node.func.slice.value for node in calls] == ['scaffold_immutable_files', '_write']
    source_call = calls[0]
    keywords = {keyword.arg: keyword.value for keyword in source_call.keywords}
    assert ast.dump(keywords['cpu_evidence_ref']) == ast.dump(ast.parse("approval['receiving_cpu_ref']", mode='eval').body)
    assert ast.dump(keywords['old_guard_ref']) == ast.dump(ast.Name(id='GUARD_REF', ctx=ast.Load()))
    assert 'RECEIVING_GATE_BINDING.json' in ast.unparse(calls[1].args[0])
    assert not any(isinstance(node, ast.Attribute) and node.attr in ('Popen', 'run', 'pidfd_send_signal', 'kill')
                   for node in ast.walk(tree))


def test_latest_historical_stage_cycle_does_not_fall_back_to_older_selected_cycle():
    family_path = REPO / 'gpu/orch_r144_node3_target_handoff.py'
    tree = ast.parse(family_path.read_bytes())
    stage = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'stage')
    historical_loop = next(node for node in stage.body if isinstance(node, ast.For)
                           and isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name)
                           and node.iter.func.id == 'reversed')
    checked = []
    records = {cycle: dict(kind='SLEEP_COMPLETE', sha256='bound', document=dict(cycle=cycle,
        resume_state=dict(state={'fixture': True}, sha256='state'))) for cycle in (40, 41)}

    def saved_evidence(plan, saved, original):
        checked.append(saved['cycle'])
        require(saved['cycle'] == 40, 'selected_exact_boundary_no_missed_cycle')

    namespace = dict(candidates=[40, 41], helper=SimpleNamespace(read=lambda cycle: records[cycle],
        digest=lambda document: 'bound', write=mock.Mock(side_effect=AssertionError('no_stage_receipt'))),
        saved_evidence=saved_evidence, require=require, old_plan={}, original=None, output=Path('/unused'))
    with pytest.raises(ValueError, match='selected_exact_boundary_no_missed_cycle'):
        exec(compile(ast.fix_missing_locations(ast.Module(body=[historical_loop], type_ignores=[])),
                     '<original_stage_history_loop_only>', 'exec'), namespace)
    assert checked == [41]
