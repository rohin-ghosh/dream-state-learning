from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r118_grid_final as final


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    root, common, runtime = tmp_path / 'lives', tmp_path / 'common', tmp_path / 'runtime'
    for path in (root / 'A4', common, runtime):
        path.mkdir(parents=True)
    monkeypatch.setattr(final, 'ROOT', root)
    monkeypatch.setattr(final, 'COMMON', common)
    monkeypatch.setattr(final, 'RUNTIME', runtime)
    monkeypatch.setattr(final.time, 'time', lambda: final.START - 60)
    final.write(runtime / 'SOURCE_CLOSURE.json', dict(files={}))
    monkeypatch.setattr(final, 'CLOSURE_SHA', final.sha(runtime / 'SOURCE_CLOSURE.json'))
    for name in ('CONFIG.json', 'INITIALIZED.json', 'ADOPTION.json'):
        final.write(common / name, dict(fixture=name))
    for constant, name in (('COMMON_SHA', 'CONFIG.json'), ('INITIALIZED_SHA', 'INITIALIZED.json'), ('ADOPTION_SHA', 'ADOPTION.json')):
        monkeypatch.setattr(final, constant, final.sha(common / name))
    tasks = [dict(id=identifier, split='FINAL', fixture=True) for identifier in final.IDS]
    final.write(root / 'A4' / 'FINAL.json', tasks)
    monkeypatch.setattr(final, 'FINAL_SHA', final.sha(root / 'A4' / 'FINAL.json'))
    monkeypatch.setattr(final, 'FINAL_SPLIT_SHA', final.digest(tasks))
    final.write(root / 'A4' / 'SERVICE_IDENTITY.json', dict(fixture=True))
    (root / 'A4' / 'LEDGER.jsonl').write_text('')
    config = dict(root=str(root / 'A4'), physical=7, uuid='GPU-fixture', base_sha256=final.BASE_SHA,
        model_dir=str(tmp_path / 'model'), decoder=final.DECODER, prompts=dict(held=final.HELD_PROMPT),
        inputs={'FINAL.json': final.FINAL_SHA, 'SERVICE_IDENTITY.json': final.sha(root / 'A4' / 'SERVICE_IDENTITY.json')},
        split_sha256=dict(FINAL=final.FINAL_SPLIT_SHA))
    final.write(root / 'A4' / 'CONFIG.json', config)
    monkeypatch.setattr(final, 'BRANCHES', {'A4': (7, 'GPU-fixture', final.sha(root / 'A4' / 'CONFIG.json'))})
    era = root / 'A4' / 'shared_repair_v1'
    final.write(era / 'CPU_LAUNCH.json', dict(terminal_filename='R118_SHARED_REPAIR_TERMINAL.json',
        identity=dict(pid=900001, uid=123, boot_id='fixture', start_ticks='1')))
    final.write(era / 'LOADED.json', dict(process=['fixture', 900002, 2]))
    selector = tmp_path / 'selection.py'
    selector.write_text('import json\n'
        'def validate_selection(root, *, config_sha256, initialized_sha256, adoption_sha256, clock):\n'
        '    assert clock() >= 1789491600\n'
        '    return json.loads((root / "FINAL_SELECTION.json").read_text())\n'
        'def select(*args, **kwargs):\n'
        '    raise AssertionError("never writer")\n'
        'def wait_select(*args, **kwargs):\n'
        '    raise AssertionError("never waiter")\n')
    monkeypatch.setattr(final, 'SELECTION_SHA', final.sha(selector))
    output = tmp_path / 'evaluation'
    plan_ref = final.prepare('A4', output, selector)
    plan = final.bound(plan_ref)
    return plan, tasks


def selection(plan):
    optimizer = final.COMMON / 'optimizer.pt'
    optimizer.write_bytes(b'CPU fixture only')
    checkpoint_path = final.COMMON / 'checkpoint.json'
    final.write(checkpoint_path, dict(complete=True, optimizer_rng_sha256=final.sha(optimizer),
        adapter=dict(base_sha256=final.BASE_SHA), source_process=['fixture', 900003, 3]))
    checkpoint = dict(path=str(checkpoint_path), path_sha256=final.sha(checkpoint_path),
        optimizer_path=str(optimizer), optimizer_path_sha256=final.sha(optimizer))
    value = dict(schema='R118_FINAL_SELECTION_V1', generation=3, checkpoint=checkpoint,
        evaluation_deadline_unix=final.END, scheduled_unix=final.START, shared_root=str(final.COMMON),
        branches=['F1', 'F2', 'F3', 'F4', 'A1', 'A2', 'A3', 'A4'],
        lineage_sha256={'CONFIG.json': final.COMMON_SHA, 'INITIALIZED.json': final.INITIALIZED_SHA,
                        'ADOPTION.json': final.ADOPTION_SHA})
    path = final.COMMON / 'FINAL_SELECTION.json'
    final.write(path, value)
    return final.ref(path), value


def test_metadata_prepare_and_validation_never_open_sealed_file(prepared, monkeypatch, tmp_path):
    plan, unused = prepared
    original = Path.open

    def safe_open(path, *args, **kwargs):
        assert path.name != 'FINAL.json'
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', safe_open)
    final.validate_plan(plan)
    another = final.prepare('A4', tmp_path / 'another', plan['selection_validator']['path'])
    assert final.bound(another)['final_contents_read'] is False


@pytest.mark.parametrize('now', [final.START - .001, final.END, final.END + 100])
def test_no_early_or_late_sealed_read(prepared, monkeypatch, now):
    plan, unused = prepared
    monkeypatch.setattr(final, 'read', lambda unused: pytest.fail('no content read outside window'))
    with pytest.raises(ValueError, match='FINAL_time_window'):
        final.read_final(plan, now)


def test_exact_panel_at_time_gate(prepared):
    plan, tasks = prepared
    assert final.read_final(plan, final.START) == tasks


@pytest.mark.parametrize('key,value', [('max_native_calls', 9), ('max_parent_calls', 1),
    ('max_training_calls', 1), ('max_optimizer_steps', 1), ('attached_open_calls', 1),
    ('end_unix', final.END + 1), ('parent_absent', False), ('fresh_process', False),
    ('old_ledger_unchanged', False), ('physical', 3), ('uuid', 'other'), ('held_prompt', 'new')])
def test_scope_drift_rejected(prepared, key, value):
    plan, unused = prepared
    with pytest.raises(ValueError):
        final.validate_plan(dict(plan, **{key: value}))


def test_changed_sealed_bytes_rejected(prepared):
    plan, unused = prepared
    (Path(plan['branch_root']) / 'FINAL.json').write_text('[]')
    with pytest.raises(ValueError, match='sealed_file_changed'):
        final.read_final(plan, final.START)


def test_cycle_zero_allowed_but_morning_partial_reserved_or_complete_suppresses(prepared):
    plan, unused = prepared
    root = Path(plan['branch_root'])
    (root / 'LEDGER.jsonl').write_text(json.dumps(dict(kind='NATIVE', cycle=0, split='FINAL',
        reserved_unix=final.START - 100, purpose='final0')) + '\n')
    assert final.prior_morning(root) is None
    with (root / 'LEDGER.jsonl').open('a') as stream:
        stream.write(json.dumps(dict(kind='NATIVE', cycle=4, purpose='final_morning')) + '\n')
    assert final.prior_morning(root) == 'PRIOR_RESERVATION_NO_RETRY'
    final.write(root / 'readouts/0004/final_morning/STARTED.json', {})
    assert final.prior_morning(root) == 'PRIOR_ATTEMPT_NO_RETRY'
    final.write(root / 'readouts/0004/final_morning/COMPLETE.json', {})
    assert final.prior_morning(root) == 'COMPLETE_NO_RERUN'


def test_no_selection_writer_or_latest_state_access(prepared, monkeypatch):
    plan, unused = prepared
    reference, selected = selection(plan)
    final.write(final.COMMON / 'STATE.json', {'changed_after_freeze': True})
    original = Path.open

    def protected(path, *args, **kwargs):
        assert path.name != 'STATE.json'
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', protected)
    assert final.validate_binding(plan, reference, final.START + 1)[0] == selected


def test_changed_optimizer_blocks_loading(prepared):
    plan, unused = prepared
    reference, selected = selection(plan)
    Path(selected['checkpoint']['optimizer_path']).write_bytes(b'changed')
    with pytest.raises(ValueError, match='checkpoint_optimizer_provenance'):
        final.validate_binding(plan, reference, final.START + 1)


def test_real_Main_v2_pure_consumer_api_reads_frozen_snapshot(prepared, monkeypatch):
    from gpu import orch_r118_final_selection as main_selector

    plan, unused = prepared
    reference, selected = selection(plan)
    config_path = final.COMMON / 'CONFIG.json'
    metrics = dict(optimizer_steps=30, child_token_exposures=40, anchor_token_exposures=10)
    config = dict(owner='F1', branches={branch: dict(root=str(final.COMMON)) for branch in main_selector.BRANCHES},
                  initial_checkpoint=selected['checkpoint'], pretransition_metrics=metrics)
    config_path.write_text(json.dumps(config))
    monkeypatch.setattr(final, 'COMMON_SHA', final.sha(config_path))
    plan['common_config_sha256'] = final.COMMON_SHA
    state = dict(generation=0, checkpoint=selected['checkpoint'], config_sha256=final.COMMON_SHA,
        **metrics, **{'shared_' + key: 0 for key in metrics})
    final.write(final.COMMON / 'final_selection/STATE.json', state)
    selected.update(generation=0, selected_unix=final.START + .5, committed_sleep=None,
        state_reference=final.ref(final.COMMON / 'final_selection/STATE.json'),
        lineage_sha256={'CONFIG.json': final.COMMON_SHA, 'INITIALIZED.json': plan['initialized_sha256'],
                        'ADOPTION.json': plan['adoption_sha256']},
        lifetime_metrics=metrics, shared_metrics={key: 0 for key in metrics})
    Path(reference['path']).write_text(json.dumps(selected))
    reference = final.ref(reference['path'])
    plan['selection_validator'] = final.ref(main_selector.__file__)
    monkeypatch.setattr(final, 'SELECTION_SHA', plan['selection_validator']['sha256'])
    final.write(final.COMMON / 'STATE.json', dict(unrelated_mutable_new_state=True))
    actual, unused = final.validate_binding(plan, reference, final.START + 1)
    assert actual == selected


def test_rejects_old_proposed_binding_path(prepared):
    plan, unused = prepared
    with pytest.raises(ValueError, match='Main_common_freeze_only'):
        final.validate_binding(plan, dict(path=str(final.COMMON / 'FINAL_READOUT_BINDING.json')), final.START + 1)


def test_release_must_include_dead_guard_not_just_empty_gpu(prepared, monkeypatch):
    plan, unused = prepared
    monkeypatch.setattr(final, 'alive', lambda item: item['pid'] == 900001)
    with pytest.raises(ValueError, match='old_guard_or_actor_still_live'):
        final.predecessor_release(plan)


def test_exclusive_evidence_writer_preserves_first_bytes(tmp_path):
    path = tmp_path / 'evidence.json'
    final.write(path, dict(value=1))
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        final.write(path, dict(value=2))
    assert path.read_bytes() == before


def test_scheduler_does_not_scan_or_load_before_time_gate(prepared, monkeypatch):
    plan, unused = prepared
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    monkeypatch.setattr(final, 'scan', lambda unused: pytest.fail('early GPU scan'))
    monkeypatch.setattr(final.time, 'sleep', lambda unused: (_ for unused in ()).throw(InterruptedError('fixture')))
    with pytest.raises(InterruptedError):
        final.guard(plan, final.COMMON / 'FINAL_SELECTION.json')
    assert final.read(Path(plan['output']) / 'TERMINAL.json')['status'] == 'FAILED'
    assert not (Path(plan['output']) / 'DISPATCH.json').exists()


def test_actual_readout_control_flow_eight_only_parent_free_no_optimizer(prepared, monkeypatch):
    plan, tasks = prepared
    monkeypatch.setattr(final.time, 'time', lambda: final.START + 10)
    reference, selected = selection(plan)
    output = Path(plan['output'])
    final.write(output / 'admission/0000.json', dict(clear=True, scanner_euid=0, blocking_reasons=[], gpu=dict(uuid=plan['uuid'])))
    dispatch = dict(plan=final.ref(output / 'PLAN.json'), binding=reference,
        admission=final.ref(output / 'admission/0000.json'), dispatched_unix=final.START + 1,
        deadline_unix=final.END, release=dict(status='RELEASED_OBSERVED_NO_SIGNALS', processes=plan['predecessor_processes']))
    final.write(output / 'DISPATCH.json', dispatch)
    monkeypatch.setattr(final, 'alive', lambda unused: False)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', plan['uuid'])
    original = Path.read_bytes
    monkeypatch.setattr(Path, 'read_bytes', lambda path: ('CUDA_VISIBLE_DEVICES=' + plan['uuid']).encode()
        if str(path) == '/proc/self/environ' else original(path))
    calls = []

    class Decoder:
        def __init__(self, loaded):
            assert loaded.optimizer is None

        def batch(self, messages, cap):
            assert len(messages) == 8 and cap == 2048
            assert all(len(prompt) == 2 and prompt[0]['content'] == final.HELD_PROMPT for prompt in messages)
            ledger = final.read(output / 'EVAL_LEDGER.json')
            assert len(ledger['reservations']) == 8 and ledger['parent_calls'] == ledger['optimizer_steps'] == 0
            calls.append(messages)
            return [dict(raw='MOVES: UP', token_ids=[1, 2], terminal=True)] * 8

        def verify_base(self):
            calls.append('verified')

    def load(stage, **kwargs):
        assert stage[3] == 'sealed_readout' and stage[5:7] == (False, True)
        assert not vars(kwargs['context'])
        assert kwargs['predecessor_processes']
        kwargs['check']('model_load')
        return SimpleNamespace(optimizer=None)

    bridge = SimpleNamespace(AdapterIdentity=SimpleNamespace(from_document=lambda value: value),
                             ARMS=['learned'], StageBinding=lambda *args: args)
    native = SimpleNamespace(bridge=bridge, StageContext=SimpleNamespace, load_stage=load,
                             process_identity=lambda: ['newboot', 111, 2])
    policy = SimpleNamespace(HELD_PROMPT=final.HELD_PROMPT, DECODER=final.DECODER,
        public_observation=lambda task, state: dict(fixture=task['id']), game=SimpleNamespace(initial=lambda task: {}))
    monkeypatch.setattr(final, 'runtime_imports', lambda: SimpleNamespace(native=native, SharedDecoder=Decoder,
        grid=SimpleNamespace(policy=policy)))
    old_ledger = (Path(plan['branch_root']) / 'LEDGER.jsonl').read_bytes()
    final.readout(plan, dispatch)
    complete = final.read(output / 'COMPLETE.json')
    assert complete['native_calls'] == 8 and len(complete['response_refs']) == 8
    assert calls[-1] == 'verified' and len(calls) == 2
    assert (Path(plan['branch_root']) / 'LEDGER.jsonl').read_bytes() == old_ledger
    with pytest.raises(FileExistsError):
        final.readout(plan, dispatch)
    assert len(calls) == 2
