import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from gpu import orch_r118_grid_parallel_handoff as handoff
from gpu import orch_r118_grid_parallel_run as runner


def test_CLI_help_does_not_import_models_or_launch():
    result = subprocess.run([sys.executable, '-B', runner.__file__, '--help'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'pending-snapshot' in result.stdout and 'crash-release' in result.stdout


def test_reference_hash_before_decoding_and_no_python_JSON(tmp_path):
    path = tmp_path / 'source.py'
    path.write_text('raise RuntimeError("never execute on validation")\n')
    reference = dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    assert runner.verify_file(reference) == path
    with pytest.raises(json.JSONDecodeError):
        runner.read(reference)
    with pytest.raises(ValueError, match='exact_pinned'):
        runner.verify_file(dict(reference, sha256='wrong'))


@pytest.mark.parametrize('branch', ['F4', 'A4'])
def test_central_bootstrap_before_go_optimizer_None(branch, tmp_path, monkeypatch):
    monkeypatch.setenv('R118_PARALLEL_SESSION', str(tmp_path / 'Main_SESSION.json'))
    monkeypatch.setenv('R118_PARALLEL_SESSION_SHA256', 'Main session sha')
    events = []
    engine = object()
    decoder = SimpleNamespace(loaded=SimpleNamespace(optimizer=None, engine=engine),
                              verify_base=lambda:events.append('readonly_verified'))

    def bootstrap(**kwargs):
        assert kwargs == dict(root='COMMON', branch=branch, engine=engine, optimizer=None,
                              session_path=tmp_path / 'Main_SESSION.json', session_sha256='Main session sha')
        events.append('central_bootstrap')
        return dict(new_peer_rng=True, inherited_peer_rng=False)

    def wait(path, digest, actual_branch, check):
        assert handoff.shared.read(tmp_path / 'FRESH_BOOTSTRAP_RETURN.json')['new_peer_rng']
        assert actual_branch == branch
        events.append('all8_GO')

    adapter = SimpleNamespace(parallel=SimpleNamespace(bootstrap_fresh_actor=bootstrap,
        wait_fresh_collection_go=wait), shared=handoff.shared)
    runner.bootstrap_before_collection(adapter, decoder, dict(shared_root='COMMON', branch=branch),
                                       tmp_path, lambda stage:None)
    assert events == ['central_bootstrap', 'all8_GO', 'readonly_verified']


def test_no_peer_optimizer_or_missing_bootstrap_API(tmp_path, monkeypatch):
    monkeypatch.setenv('R118_PARALLEL_SESSION', str(tmp_path / 'SESSION.json'))
    monkeypatch.setenv('R118_PARALLEL_SESSION_SHA256', 'pin')
    decoder = SimpleNamespace(loaded=SimpleNamespace(optimizer=object()))
    with pytest.raises(ValueError, match='optimizer_None'):
        runner.bootstrap_before_collection(None, decoder, {}, tmp_path, None)
    decoder.loaded.optimizer = None
    with pytest.raises(ValueError, match='fresh_API'):
        runner.bootstrap_before_collection(SimpleNamespace(parallel=SimpleNamespace()), decoder, {}, tmp_path, None)


def test_FINAL_rebind_changes_only_identities_and_output(tmp_path):
    root = tmp_path / 'A4'
    root.mkdir()
    guard = root / 'CPU_LAUNCH.json'
    native = root / 'NATIVE_IDENTITY.json'
    handoff.shared.write(guard, dict(terminal_filename=runner.TERMINAL,
        identity=dict(boot_id='fixture', pid=123, start_ticks='42', uid=1000)))
    handoff.shared.write(native, dict(identity=dict(boot_id='fixture', pid=456, start_ticks=43),
                                     process=['fixture',456,43]))
    previous = dict(branch_root=str(root), output='old', predecessor_refs=[], predecessor_processes=[],
        max_native_calls=8, max_parent_calls=0, max_training_calls=0, max_optimizer_steps=0,
        start_unix=1789491600, end_unix=1789492800, final_ids=['never inspected content'],
        selection_validator={'pinned':'canonical'}, decoder={'pinned':'original'})
    result = runner.rebound_final_plan(previous, tmp_path / 'new_eval', handoff.reference(guard),
                                       handoff.reference(native), handoff)
    assert {key for key in previous if previous[key] != result[key]} == {
        'output', 'predecessor_refs', 'predecessor_processes'}
    assert result['predecessor_processes'][1]['pid'] == 456
    assert result['predecessor_processes'][1]['uid'] == 1000
    assert result['predecessor_processes'][1]['start_ticks'] == '43'


def test_wait_is_bounded_and_checks_lease(tmp_path):
    checks = []
    with pytest.raises(ValueError, match='bounded_wait'):
        runner.wait_file(tmp_path / 'missing', 1, checks.append, clock=lambda:2, pause=lambda duration:None)
    assert checks == ['grid_parallel_file_wait']


def test_fresh_dispatch_env_required_before_release_or_model(monkeypatch, tmp_path):
    monkeypatch.delenv('R118_PARALLEL_BRANCH', raising=False)
    plan = dict(schema='R118_GRID_PARALLEL_EXEC_V1', root=str(tmp_path), directory=str(tmp_path / 'new'), branch='A4')
    with pytest.raises(ValueError, match='dispatcher_injected'):
        runner.validate(plan, None)


def test_campaign_uses_central_safe_publication_and_exact_certificate():
    certificate = {'path':'/own/SAFE.json', 'sha256':'certificate pin'}
    plan = dict(campaign=dict(path='/Main/CAMPAIGN.json', sha256='Main pin'), common_root='/COMMON',
                branch='F4', bounds=dict(train_end_unix=100))
    calls = []
    def await_activation(*args, **kwargs):
        calls.append((args, kwargs))
        return {'path':'/Main/ACTIVATION.json', 'sha256':'activation pin'}
    adapter = SimpleNamespace(parallel=SimpleNamespace(
        campaign_document=lambda *args: (dict(root='/COMMON', deadline_unix=100), None),
        await_campaign_activation=await_activation))
    check = lambda stage: None
    assert runner.campaign_activation(plan, adapter, certificate, check)['sha256'] == 'activation pin'
    assert calls == [(('/Main/CAMPAIGN.json', 'Main pin', 'F4', certificate), dict(check=check))]
    plan['bounds']['train_end_unix'] = 99
    with pytest.raises(ValueError, match='original_campaign_deadline'):
        runner.campaign_activation(plan, adapter, certificate, check)
    assert len(calls) == 1
