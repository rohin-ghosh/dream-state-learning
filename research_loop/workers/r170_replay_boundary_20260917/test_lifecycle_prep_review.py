"""Independent local-only observer tests; every subprocess is replaced by a mock."""

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest import mock

import pytest


HERE = Path(__file__).resolve().parent
FREEZE_SHA = '34d8a82e6dd5cf15493b2a838baa66806dcf25b96cdbe91586c83ce924d489c0'
CONSUMED_REVIEW_SHA = 'af9d60e96a035b5363e3eaf7c179e010a9e44b4d58eb83b1692bf2d3b19510ce'


@pytest.fixture
def observer(tmp_path, monkeypatch):
    path = HERE / 'BOUNDARY_FREEZE.py'
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FREEZE_SHA
    assert hashlib.sha256(HERE.joinpath('REVIEW_ASSEMBLY_V2.md').read_bytes()).hexdigest() == CONSUMED_REVIEW_SHA
    specification = importlib.util.spec_from_file_location('independent_boundary_observer', path)
    module = importlib.util.module_from_spec(specification)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    stage, life = tmp_path / 'stage', tmp_path / 'life'
    bootstrap = stage / 'bootstrap'
    location = bootstrap / 'research_loop/workers/r170_replay_boundary_20260917'
    location.mkdir(parents=True)
    stage.joinpath('physical1').mkdir()
    boundary = life / 'stream/records/00000000000000000043.json'
    checkpoint = life / 'checkpoints/sleep_000043/COMMIT.json'
    for target in (boundary, checkpoint):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('{"fixture":true,"sha256":"not_the_file_digest"}\n')
    for name, value in dict(STAGE=stage, LIFE=life, BOOTSTRAP=bootstrap, HERE=location).items():
        monkeypatch.setattr(module, name, value)
    monkeypatch.setattr(sys, 'path', list(sys.path))
    monkeypatch.setattr(module.time, 'time', lambda: 1000)
    monkeypatch.setattr(module.time, 'monotonic', lambda: 100)
    saved = dict(path=str(boundary), cycle=43, state_sha256='state_fixture')
    current = mock.Mock(side_effect=[saved, saved, saved])
    readout = mock.Mock(return_value=True)
    original = SimpleNamespace(saved=SimpleNamespace(sleep_boundary=current, readout_started=readout))
    processes = dict(actor=dict(pid=1266769, start_ticks='28048014'),
                     timer=dict(pid=1266768), supervisor=dict(pid=1266757))
    writes = []

    def write(target, document):
        with target.open('x') as stream:
            json.dump(document, stream)
        writes.append((target, document))

    helper = SimpleNamespace(write=write, process_record=mock.Mock(return_value=processes['actor']))
    family = dict(api=lambda: helper, old_modules=lambda path: ({}, dict(
        root=str(life), hard_end_unix=10000, readout_revision=2), original),
        old_processes=lambda *arguments: processes)
    adapter = dict(family_namespace=lambda: family, OLD_GUARD=life / 'GUARD.json')
    ready = SimpleNamespace(load_operator=lambda: adapter, EXPECTED_PID=1266769, EXPECTED_TICKS='28048014')
    loader = mock.Mock(return_value=ready)
    monkeypatch.setattr(module, 'load', loader)
    invocation = mock.Mock(return_value=SimpleNamespace(returncode=0, stdout=b'{"fixture":true}', stderr=b''))
    monkeypatch.setattr(module.subprocess, 'run', invocation)
    return SimpleNamespace(module=module, stage=stage, life=life, bootstrap=bootstrap,
        location=location, boundary=boundary, checkpoint=checkpoint, saved=saved,
        current=current, readout=readout, invocation=invocation, loader=loader,
        writes=writes, write=write)


def test_watcher_exact_isolated_child_environment_byte_refs_and_single_invocation(observer):
    fixture = observer
    result = fixture.module.watch(60)
    assert result['same_boundary_after'] is True and result['returncode'] == 0
    command = fixture.invocation.call_args.args[0]
    assert command[:5] == [fixture.module.PYTHON, '-I', '-B', str(fixture.location / 'BOUNDARY_FREEZE.py'), '--assemble']
    arguments = json.loads(command[5])
    assert arguments == dict(boundary_ref=fixture.module.reference(fixture.boundary),
        checkpoint_ref=fixture.module.reference(fixture.checkpoint), cycle=43)
    options = fixture.invocation.call_args.kwargs
    assert options == dict(cwd=fixture.bootstrap, env=dict(PATH='/usr/bin:/bin', CUDA_VISIBLE_DEVICES='',
        PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1'),
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=False)
    fixture.readout.assert_called_once_with(str(fixture.life), 43, 2, 1266768)
    with pytest.raises(FileExistsError):
        fixture.module.watch(60)
    fixture.invocation.assert_called_once()
    assert [path.name for path, document in fixture.writes] == [
        'SELECTION_OBSERVER_STARTED.json', 'SELECTION_OBSERVER_RESULT.json']
    assert not any(result[field] for field in ('signals_sent', 'model_calls', 'main_go_created'))


@pytest.mark.xfail(strict=True, reason='moved head is recorded but successful child return still returns success')
def test_moved_head_after_finalizer_must_not_return_success(observer):
    observer.current.side_effect = [observer.saved, observer.saved, None]
    with pytest.raises(ValueError, match='boundary|expired|moved'):
        observer.module.watch(60)


def test_failed_child_result_preserved_and_not_retried(observer):
    observer.invocation.return_value = SimpleNamespace(returncode=1, stdout=b'', stderr=b'fixture_failure')
    with pytest.raises(ValueError, match='selection_failed_no_retry'):
        observer.module.watch(60)
    receipt = json.loads(observer.stage.joinpath('physical1/SELECTION_OBSERVER_RESULT.json').read_text())
    assert receipt['returncode'] == 1 and receipt['stderr'] == 'fixture_failure'
    with pytest.raises(FileExistsError):
        observer.module.watch(60)
    observer.invocation.assert_called_once()


def test_uncertain_timeout_consumes_observer_without_second_child(observer):
    observer.invocation.side_effect = subprocess.TimeoutExpired(['fixture_finalizer'], 120)
    with pytest.raises(subprocess.TimeoutExpired):
        observer.module.watch(60)
    assert observer.stage.joinpath('physical1/SELECTION_OBSERVER_STARTED.json').exists()
    assert not observer.stage.joinpath('physical1/SELECTION_OBSERVER_RESULT.json').exists()
    with pytest.raises(FileExistsError):
        observer.module.watch(60)
    observer.invocation.assert_called_once()


def test_finalizer_calls_only_selection_with_explicit_no_go_and_metadata_write(observer):
    fixture = observer
    result = dict(source_cycle=43, target_cycle=44,
        selection_bundle_ref=dict(path=str(fixture.stage / 'physical1/SELECTION_BUNDLE.json'), sha256='1' * 64),
        expected_main_go_scope=dict(target_cycle=44))
    finalize = mock.Mock(return_value=result)
    namespace = dict(finalize_selection_bundle=finalize, _write=fixture.write)
    namespace_loader = mock.Mock(return_value=namespace)
    fixture.loader.return_value = SimpleNamespace(assembly_namespace=namespace_loader)
    boundary_ref, checkpoint_ref = map(fixture.module.reference, (fixture.boundary, fixture.checkpoint))
    receipt = fixture.module.freeze(boundary_ref, checkpoint_ref, 43)
    fixture.loader.assert_called_once_with('ASSEMBLY_V2.py', fixture.module.ASSEMBLY_SHA)
    namespace_loader.assert_called_once_with(dict(path=str(fixture.location / 'APPROVED_RECEIVING_CPU.json'),
                                                sha256=fixture.module.APPROVAL_SHA))
    assert finalize.call_args.kwargs == dict(scaffold_ref=dict(path=str(fixture.stage / 'physical1/SCAFFOLD.json'),
        sha256=fixture.module.SCAFFOLD_SHA), boundary_ref=boundary_ref, checkpoint_ref=checkpoint_ref,
        approved_intake_sha256=fixture.module.SCOPE_SHA, now=1000, main_go_scope=None)
    assert [path.name for path, document in fixture.writes] == ['SELECTION_FREEZE_RECEIPT.json']
    assert receipt['awaiting_explicit_Main_scope'] is True and receipt['main_go_created'] is False
    fixture.invocation.assert_not_called()


def test_byte_drift_refuses_before_importing_assembly(observer):
    boundary_ref = observer.module.reference(observer.boundary)
    checkpoint_ref = observer.module.reference(observer.checkpoint)
    observer.boundary.write_text('{"different_fixture_bytes":true}\n')
    with pytest.raises(ValueError, match='observed_byte_refs_unchanged'):
        observer.module.freeze(boundary_ref, checkpoint_ref, 43)
    observer.loader.assert_not_called()
    assert observer.writes == []


def test_source_has_no_lifecycle_or_model_calls_and_no_go_binding():
    tree = ast.parse(HERE.joinpath('BOUNDARY_FREEZE.py').read_bytes())
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert not attributes.intersection({'pidfd_open', 'pidfd_send_signal', 'kill', 'killpg',
        'load_model', 'from_pretrained', 'handoff', 'supervise', 'bind_main_go'})
    direct_keys = {node.slice.value for node in ast.walk(tree) if isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name) and node.value.id == 'assembly'
        and isinstance(node.slice, ast.Constant)}
    assert direct_keys == {'finalize_selection_bundle', '_write'}


def test_composed_cpu_refs_and_compatibility_fields_are_bound_but_not_handoff_go():
    raw = HERE.joinpath('CPU_LIFECYCLE_AUTHORITY.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == 'ef38100cf80a6e64299fb012e348ceab80689726338332289860792273f7e8fd'
    authority = json.loads(raw)
    verified = []

    def verify(value):
        if isinstance(value, dict):
            if set(value) == {'path', 'sha256'}:
                assert hashlib.sha256(Path(value['path']).read_bytes()).hexdigest() == value['sha256']
                verified.append(value)
            else:
                for entry in value.values():
                    verify(entry)
        elif isinstance(value, list):
            for entry in value:
                verify(entry)

    verify(authority)
    assert len(verified) == 13
    repository = HERE.parents[2]
    family_path = repository / 'gpu/orch_r144_node3_target_handoff.py'
    api_path = HERE.parent / 'r144_node3_target_handoff_20260916t1541z_operator5/BOUNDARY_API.py'
    constants = {}
    for node in ast.parse(family_path.read_bytes()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in ('API_SHA', 'PATCH_SHA', 'HELPER_SHA'):
                constants[node.targets[0].id] = ast.literal_eval(node.value)
    for field, constant in [('api_sha256', 'API_SHA'), ('patch_sha256', 'PATCH_SHA'), ('helper_sha256', 'HELPER_SHA')]:
        assert authority[field] == constants[constant]
    assert authority['operator_sha256'] == hashlib.sha256(HERE.joinpath('OPERATOR_RECOVERY_V2.py').read_bytes()).hexdigest()
    for name, checksum in authority['deployed_dependency_pins'].items():
        path = {'FAMILY.py': family_path, 'BOUNDARY_API.py': api_path}.get(name, HERE / name)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == checksum
    assert set(authority['compatibility_labels_only']) == {'patch_sha256', 'helper_sha256'}
    assert authority['status'] == 'PASS'
    assert authority['learner_handoff_authorized'] is authority['main_go_created'] is False
    assert authority['signals_sent'] == authority['model_calls'] == 0
    assert authority['local_CPU']['passed'] == 203 and authority['local_CPU']['expected_xfailed'] == 4
    assert authority['source_only_review_ref']['sha256'] == CONSUMED_REVIEW_SHA
