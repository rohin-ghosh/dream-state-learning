import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from gpu import orch_r118_grid_parallel_handoff as handoff


shared = handoff.shared


def write(path, document):
    shared.write(path, document)
    return handoff.reference(path)


def test_original_guard_decimal_ticks_normalize_without_identity_waiver():
    original = dict(boot_id='exact-boot', pid=1107627, start_ticks='1139572', uid=2524)
    assert handoff.central_identity(original) == dict(boot_id='exact-boot', pid=1107627, start_ticks=1139572)
    assert original['start_ticks'] == '1139572'
    for invalid in (True, -1, '1.0', '1e4', None, ''):
        with pytest.raises(ValueError):
            handoff.central_identity(dict(original, start_ticks=invalid))


@pytest.fixture
def settled(tmp_path):
    root, common, bundle = [tmp_path / name for name in ('A4', 'common', 'bundle')]
    identity = dict(boot_id='fixture', pid=12345, start_ticks=42)

    def write(path, document):
        shared.write(path, document)
        return handoff.reference(path)

    source = write(bundle / 'orch_r118_grid_shared_repair.py', {'source': 'CPU fixture'})
    frozen = write(tmp_path / 'frozen/source.py', {'source': 'frozen fixture'})
    manifest = write(bundle / 'MANIFEST.json', dict(files={'orch_r118_grid_shared_repair.py':source['sha256']},
        frozen_source=str(tmp_path / 'frozen'), frozen_files={'source.py':frozen['sha256']}))
    ready = write(root / 'shared_repair_v1/READY.json', dict(root=str(root), terminal_filename=handoff.TERMINAL,
        bundle=str(bundle), manifest_sha256=manifest['sha256'], source_sha256=source['sha256'], bounds={}))
    write(root / 'shared_repair_v1/LOADED.json', dict(process=['fixture', 12345, 42]))
    write(root / 'CONFIG.json', {})
    write(root / 'SHARED_ACTIVATION.json', {})
    write(root / 'SHARED_TERMINAL.json', dict(status='FAILED', historical=True))
    config = write(common / 'CONFIG.json', {})
    optimizer = write(common / 'optimizer.json', {'state': 'existing'})
    checkpoint = write(common / 'checkpoint.json', dict(complete=True, adapter={'fixture':'adapter'},
        optimizer_rng_sha256=optimizer['sha256']))
    checkpoint_ref = dict(path=checkpoint['path'], path_sha256=checkpoint['sha256'],
        optimizer_path=optimizer['path'], optimizer_path_sha256=optimizer['sha256'])
    state = dict(generation=1, checkpoint=checkpoint_ref, config_sha256=config['sha256'])
    write(common / 'STATE.json', state)
    write(common / 'generation_000000/sleep/COMPLETE.json', dict(state=state))
    session = dict(branch='A4', branch_root=str(root), shared_root=str(common), generation=1,
        checkpoint=checkpoint_ref, checkpoint_sha256=checkpoint['sha256'],
        config_sha256=config['sha256'], adapter={'fixture':'adapter'})
    carry = [{'split':'TRAIN', 'purpose':'reflection', 'attached_readout':False}]
    write(root / 'CARRY.json', carry)
    rows = []
    for number in (1, 2):
        row = dict(kind='NATIVE', number=number, cycle=5, reserved_unix=1, task_id=f'TRAIN{number}',
                   split='TRAIN', purpose='episode', attached_readout=False)
        rows.append(row)
        write(root / f'calls/N{number:05d}.json', dict(row, status='COMPLETE'))
    rows.append(dict(kind='PARENT', number=1, cycle=5, reserved_unix=1))
    write(root / 'parent_received/P0001.json', dict(disposition={'status':'MISSING'}))
    (root / 'LEDGER.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
    write(root / 'cycles/0005/TRAIN_COMPLETE.json', dict(carry=carry,
        outcomes=[dict(task_id=f'TRAIN{number}', split='TRAIN') for number in (1, 2)]))
    write(root / 'cycles/0005/CYCLE_COMPLETE.json', dict(cycle=5, finished_unix=10,
        shared_generation=1, shared_checkpoint_sha256=checkpoint['sha256']))
    write(root / 'shared_cycles/0005/RELOADED.json', dict(generation=1,
        checkpoint_sha256=checkpoint['sha256'], resident_reload=True))
    packet = dict(cycle=5, session=dict(generation=0), rows=[{'causal':'TRAIN-only'}],
                  episode_ids=['TRAIN1', 'TRAIN2'])
    packet_ref = write(root / 'shared_cycles/0005/PACKET.json', packet)
    submission_ref = write(common / 'generation_000000/A4.json', dict(generation=0, branch='A4',
        rows=packet['rows'], episode_ids=packet['episode_ids']))
    write(root / 'shared_cycles/0005/SUBMITTED.json', dict(packet=packet_ref, submission=submission_ref))
    binding = handoff.run.client.call_binding(session)
    write(root / 'readouts/0005/dev/STARTED.json', dict(pid=67890, parent=False,
        carry_access=False, shared_child=binding, started_unix=2))
    write(root / 'readouts/0005/dev/COMPLETE.json', dict(status='COMPLETE', scope='dev', cycle=5,
        fresh_process=True, parent_calls=0, optimizer_steps=0, carry_access=False,
        readout_open_excluded=True, shared_child=binding, finished_unix=9))
    return root, session, dict(session=session, cycle=5, ready_reference=ready, native_identity=identity)


def change(path, **fields):
    shared.write(path, dict(shared.read(path), **fields), replace=True)


def test_real_files_snapshot_is_readonly_and_not_release(settled):
    root, session, args = settled
    before = {str(path):shared.sha(path) for path in root.rglob('*') if path.is_file()}
    document = handoff.snapshot(root, **args)
    assert document['next_cycle'] == 6
    assert (document['native_used'], document['parent_used']) == (2, 1)
    assert document['activation_authorized'] is False
    assert document['terminal_filename'] == handoff.TERMINAL
    assert document['rng_provenance'].startswith('PREDECESSOR_RANK_RNG_NOT_SAVED')
    assert before == {str(path):shared.sha(path) for path in root.rglob('*') if path.is_file()}
    assert not (root / handoff.TERMINAL).exists()


@pytest.fixture
def crashed(settled, monkeypatch):
    root, session, args = settled
    guard = dict(boot_id='fixture', pid=12346, start_ticks='43')
    write(root / 'shared_repair_v1/CPU_LAUNCH.json', dict(identity=guard))
    write(root / handoff.TERMINAL, dict(status='FAILED', exit_code=1))
    (root / 'readouts/0005/dev/COMPLETE.json').unlink()
    (root / 'cycles/0005/CYCLE_COMPLETE.json').unlink()
    common = Path(session['shared_root'])
    config_path = common / 'CONFIG.json'
    change(config_path, branches={'A4':dict(train_ids=['TRAIN1', 'TRAIN2'])})
    state = shared.read(common / 'STATE.json')
    state['config_sha256'] = shared.sha(config_path)
    shared.write(common / 'STATE.json', state, replace=True)
    session['config_sha256'] = state['config_sha256']
    change(common / 'generation_000000/sleep/COMPLETE.json', state=state, same_optimizer=True,
           source_checkpoint=dict(path_sha256='original_child'))
    previous = common / 'generation_000000/A4.json'
    change(previous, checkpoint_sha256='original_child')
    submitted = root / 'shared_cycles/0005/SUBMITTED.json'
    change(submitted, submission=handoff.reference(previous))
    monkeypatch.setattr(handoff.parallel, 'predecessor_released', lambda identity:None)
    return root, session, dict(args, guard_identity=guard, output=root / 'prospective_failed_eval')


def test_crashed_DEV_is_explicit_no_fake_completion_or_replay(crashed):
    root, session, args = crashed
    before = {str(path):shared.sha(path) for path in root.rglob('*') if path.is_file()}
    result = handoff.recovery_snapshot(root, **args)
    assert result['next_cycle'] == 6
    assert result['owner_boundary']['canonical_reload_required'] is True
    assert 'fresh_dev' not in result['owner_boundary']
    disposition = handoff.checked(result['owner_boundary']['postcommit_eval_disposition'])
    assert disposition['evaluations'] == dict(DEV='FAILED', OPEN='NOT_ATTEMPTED')
    assert disposition['replay_train'] is False
    cursor = handoff.checked(result['owner_boundary']['settled_cursor'])
    assert cursor['pending_train_calls'] == cursor['pending_train_submissions'] == []
    assert cursor['native_used'] == 2 and cursor['parent_used'] == 1
    assert all(shared.sha(Path(path)) == digest for path, digest in before.items())
    assert not (root / 'cycles/0005/CYCLE_COMPLETE.json').exists()
    assert not (root / 'RELEASE.json').exists()
    handoff.validate_snapshot(result)


@pytest.mark.parametrize('failure', ['live_native', 'new_submission', 'unsettled_train', 'changed_carry',
                                   'new_collection', 'wrong_packet', 'missing_parent'])
def test_crash_recovery_never_discards_or_replays_TRAIN(crashed, monkeypatch, failure):
    root, session, args = crashed
    if failure == 'live_native':
        def alive(identity):
            raise ValueError('predecessor_still_alive')
        monkeypatch.setattr(handoff.parallel, 'predecessor_released', alive)
    elif failure == 'new_submission':
        write(Path(session['shared_root']) / 'generation_000001/A4.json', dict(rows=['new TRAIN']))
    elif failure == 'unsettled_train':
        change(root / 'calls/N00002.json', status='STARTED')
    elif failure == 'changed_carry':
        shared.write(root / 'CARRY.json', [], replace=True)
    elif failure == 'new_collection':
        write(root / 'shared_cycles/0006/COLLECTION.json', dict(status='begun'))
    elif failure == 'wrong_packet':
        change(root / 'shared_cycles/0005/PACKET.json', rows=['different'])
    else:
        change(root / 'parent_received/P0001.json', disposition=None)
    with pytest.raises(ValueError):
        handoff.recovery_snapshot(root, **args)
    assert not args['output'].exists()


def test_crashed_snapshot_revalidates_evidence_and_no_release_without_all8(crashed):
    root, session, args = crashed
    result = handoff.recovery_snapshot(root, **args)
    reference = write(root / 'BOUNDARY.json', result)
    authorization = write(root / 'NO_GO.json', dict(schema='R118_GRID_PARALLEL_DRAIN_V1',
                                                  status='NOT_AUTHORIZED', branches={}))
    with pytest.raises(ValueError, match='Main_all8'):
        handoff.release_crashed(authorization=authorization, boundary_reference=reference,
                               output=root / 'not_released')
    change(root / handoff.TERMINAL, status='COMPLETE')
    with pytest.raises(ValueError):
        handoff.validate_snapshot(result)


@pytest.fixture
def pending(settled):
    root, session, args = settled
    rows = handoff.run.read_ledger(root)
    for number in (3, 4):
        row = dict(kind='NATIVE', number=number, cycle=6, reserved_unix=11, task_id=f'TRAIN{number}',
                   split='TRAIN', purpose='episode', attached_readout=False)
        rows.append(row)
        write(root / f'calls/N{number:05d}.json', dict(row, status='COMPLETE'))
    rows.append(dict(kind='PARENT', number=2, cycle=6, reserved_unix=11))
    write(root / 'parent_received/P0002.json', dict(disposition={'status':'SILENT'}))
    (root / 'LEDGER.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
    write(root / 'cycles/0006/TRAIN_COMPLETE.json', dict(carry=shared.read(root / 'CARRY.json'),
        outcomes=[dict(task_id=f'TRAIN{number}', split='TRAIN') for number in (3, 4)]))
    write(root / 'shared_cycles/0006/COLLECTION.json', session)
    packet = dict(cycle=6, session=session, rows=[{'canonical_causal':'new train'}],
                  episode_ids=['TRAIN3', 'TRAIN4'])
    packet_ref = write(root / 'shared_cycles/0006/PACKET.json', packet)
    accepted = write(Path(session['shared_root']) / 'generation_000001/A4.json', dict(branch='A4',
        generation=1, checkpoint_sha256=session['checkpoint_sha256'], rows=packet['rows'],
        episode_ids=packet['episode_ids']))
    write(root / 'shared_cycles/0006/SUBMITTED.json', dict(packet=packet_ref, submission=accepted))
    return root, session, dict(args, cycle=6, output=root / 'prospective/PENDING_CURSOR.json')


def test_pending_two_episodes_adopted_without_calls_or_duplicate_submission(pending, monkeypatch):
    from gpu import orch_r118_grid_parallel_loop as loop
    root, session, args = pending
    boundary = handoff.pending_snapshot(root, **args)
    assert boundary['next_cycle'] == 7 and boundary['completed_cycle'] == 6
    assert handoff.checked(boundary['owner_boundary']['settled_cursor'])['next_cycle'] == 7
    before = {str(path):shared.sha(path) for path in root.rglob('*') if path.is_file()}
    monkeypatch.setattr(loop.run, 'life_class', lambda *args:pytest.fail('no new calls'))
    monkeypatch.setattr(loop.run.client, 'run_cycle_and_submit', lambda *args:pytest.fail('no duplicate submit'))
    accepted = handoff.checked(boundary['pending_submission'])
    monkeypatch.setattr(loop, 'resume_pending', lambda *args, **kwargs:dict(cycle=6, submission=accepted['submission']))
    submitted = loop.collect_or_adopt(root, None, None, session, boundary, 6, None, True)
    assert submitted == handoff.checked(boundary['pending_submission'])
    assert all(shared.sha(Path(path)) == digest for path, digest in before.items())
    assert not (root / 'cycles/0006/CYCLE_COMPLETE.json').exists()


@pytest.mark.parametrize('failure', ['partial', 'parent_pending', 'sleep_started', 'later_cycle',
                                   'wrong_common', 'prior_DEV_missing'])
def test_pending_requires_exact_settled_TRAIN_not_arbitrary_partial(pending, failure):
    root, session, args = pending
    if failure == 'partial':
        change(root / 'calls/N00004.json', status='STARTED')
    elif failure == 'parent_pending':
        change(root / 'parent_received/P0002.json', disposition=None)
    elif failure == 'sleep_started':
        write(Path(session['shared_root']) / 'generation_000001/sleep/START.json', {})
    elif failure == 'later_cycle':
        write(root / 'shared_cycles/0007/COLLECTION.json', {})
    elif failure == 'wrong_common':
        change(Path(session['shared_root']) / 'generation_000001/A4.json', rows=[])
    else:
        (root / 'readouts/0005/dev/COMPLETE.json').unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        handoff.pending_snapshot(root, **args)
    assert not args['output'].exists()


@pytest.mark.parametrize('relative,fields', [
    ('readouts/0005/dev/COMPLETE.json', {'parent_calls':1}),
    ('readouts/0005/dev/COMPLETE.json', {'fresh_process':False}),
    ('readouts/0005/dev/COMPLETE.json', {'carry_access':True}),
    ('readouts/0005/dev/COMPLETE.json', {'finished_unix':11}),
    ('readouts/0005/dev/STARTED.json', {'pid':12345}),
    ('shared_cycles/0005/RELOADED.json', {'resident_reload':False}),
    ('cycles/0005/CYCLE_COMPLETE.json', {'shared_generation':0}),
    ('calls/N00001.json', {'status':'RESERVED'}),
    ('shared_repair_v1/LOADED.json', {'process':['fixture', 999, 1]}),
])
def test_rejects_nonsettled_or_false_provenance(settled, relative, fields):
    root, session, args = settled
    change(root / relative, **fields)
    with pytest.raises(ValueError):
        handoff.snapshot(root, **args)


@pytest.mark.parametrize('relative', ['generation_000001/A4.json',
                                    'generation_000001/sleep/START.json'])
def test_current_generation_busy_rejected(settled, relative):
    root, session, args = settled
    shared.write(Path(session['shared_root']) / relative, {})
    with pytest.raises(ValueError, match='already'):
        handoff.snapshot(root, **args)


def test_zero_generation_and_uncommitted_rejected(settled):
    root, session, args = settled
    change(Path(session['shared_root']) / 'generation_000000/sleep/COMPLETE.json', state={})
    with pytest.raises(ValueError, match='complete_binds'):
        handoff.snapshot(root, **args)


@pytest.mark.parametrize('relative', ['LEDGER.jsonl', 'CARRY.json', 'parent_received/P0001.json',
                                    'SHARED_TERMINAL.json'])
def test_preserved_state_tamper_rejected(settled, relative):
    root, session, args = settled
    document = handoff.snapshot(root, **args)
    with (root / relative).open('a') as stream:
        stream.write(' ')
    with pytest.raises(ValueError):
        handoff.validate_snapshot(document)


@pytest.mark.parametrize('relative', ['parent_queue/P0002.response.json',
                                    'shared_cycles/0006/COLLECTION.json'])
def test_snapshot_race_detected(settled, relative):
    root, session, args = settled
    document = handoff.snapshot(root, **args)
    shared.write(root / relative, {})
    with pytest.raises(ValueError):
        handoff.validate_snapshot(document)


def test_candidate_only_creates_explicit_output(tmp_path):
    source = tmp_path / 'source.py'
    source.write_text('pass\n')
    reference = handoff.candidate(tmp_path / 'READY.json', sources=[str(source)])
    document = handoff.checked(reference)
    assert document['status'] == 'CPU_ONLY_NOT_ARMED'
    assert document['activation_authorized'] is False
    assert document['parent_wait_seconds'] == {'F4':600, 'A4':120}
    assert not document['serial_adamw_equivalent']


def test_inside_rejects_traversal_and_symlink_escape(tmp_path):
    root = tmp_path / 'root'
    root.mkdir()
    outside = tmp_path / 'outside'
    outside.write_text('unchanged')
    (root / 'link').symlink_to(outside)
    for relative in ('../outside', str(outside), 'link'):
        with pytest.raises(ValueError):
            handoff.inside(root, relative)


def test_drain_not_go_never_inspects_or_signals(tmp_path, monkeypatch):
    from gpu import orch_r118_grid_final_drain as process

    path = tmp_path / 'AUTH.json'
    shared.write(path, dict(schema='R118_GRID_PARALLEL_DRAIN_V1', status='CPU_ONLY_NOT_ARMED',
                            branches=list(shared.BRANCHES)))
    monkeypatch.setattr(process, 'inspect_owned', lambda *args:pytest.fail('no actor access'))
    monkeypatch.setattr(handoff.os, 'pidfd_open', lambda *args:pytest.fail('no signals'))
    with pytest.raises(ValueError, match='Main_all8'):
        handoff.drain_at_settled_boundary(authorization=handoff.reference(path), root=tmp_path,
            session={}, cycle=1, ready_reference={}, output=tmp_path / 'output')


@pytest.fixture
def supervised(tmp_path):
    native = dict(boot_id='fixture', pid=101, start_ticks=1)
    guard = dict(boot_id='fixture', pid=102, start_ticks=2)
    timer = dict(boot_id='fixture', pid=103, start_ticks=3)
    guard_path = tmp_path / 'GUARD.json'
    final_path = tmp_path / 'FINAL.json'
    shared.write(guard_path, dict(native_identity=native, guard_identity=guard, root=str(tmp_path),
                                 terminal_filename='R118_GRID_PARALLEL_TERMINAL.json'))
    shared.write(final_path, dict(native_identity=native, timer_identity=timer, root=str(tmp_path),
        old_timer_retired=True, canonical_selection_schema='R118_FINAL_SELECTION_V1', evaluation_only=True))
    certificate = dict(branch='A4', root=str(tmp_path), identity=native,
        retained_supervision=dict(native_identity=native, guard_identity=guard,
            owner_verified_safe_for_parallel=True, guard_binding=handoff.reference(guard_path),
            final_identity_bindings=[dict(identity=timer, evidence=handoff.reference(final_path))]))
    return certificate, guard_path, final_path


def test_actual_successor_guard_and_FINAL_bindings(supervised):
    certificate, guard_path, final_path = supervised
    seen = []
    handoff.supervision(certificate, verify_identity=seen.append)
    assert [item['pid'] for item in seen] == [101, 102, 103]


@pytest.mark.parametrize('field,value', [('native_identity', {'pid':999}), ('old_timer_retired', False),
    ('canonical_selection_schema', 'R118_FINAL_SHARED_CHECKPOINT_V1'), ('evaluation_only', False)])
def test_stale_or_incorrect_FINAL_rebind_rejected(supervised, field, value):
    certificate, guard_path, final_path = supervised
    change(final_path, **{field:value})
    certificate['retained_supervision']['final_identity_bindings'][0]['evidence'] = handoff.reference(final_path)
    with pytest.raises(ValueError, match='FINAL_rebind'):
        handoff.supervision(certificate, verify_identity=lambda identity:None)


@pytest.mark.parametrize('busy', [True, False])
def test_real_pidfd_release_or_busy_resume_preserves_foreign_sentinel(settled, monkeypatch, busy):
    from gpu import orch_r118_grid_final_drain as process
    import hashlib

    root, session, args = settled
    actor = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)', 'resident'])
    sentinel = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)', 'guard'])
    try:
        native = process.identity(actor.pid)
        guard = process.identity(sentinel.pid)
        for record in (native, guard):
            record['command_sha256'] = hashlib.sha256(
                (Path('/proc') / str(record['pid']) / 'cmdline').read_bytes()).hexdigest()
        monkeypatch.setattr(process, 'inspect_owned', lambda pid, plan:native if pid == actor.pid else guard)
        change(root / 'CONFIG.json', uuid='GPU-test')
        bounds = handoff.checked(args['ready_reference'])['bounds']
        auth = root / 'AUTH.json'
        shared.write(auth, dict(schema='R118_GRID_PARALLEL_DRAIN_V1', status='MAIN_ALL8_COORDINATED_GO',
            issued_unix=0, expires_unix=handoff.run.grid.TRAIN_END,
            branches={branch:dict(root=str(root), ready=args['ready_reference'], generation=1,
                checkpoint_sha256=session['checkpoint_sha256'], bounds=bounds,
                native_identity=native, guard_identity=guard) for branch in shared.BRANCHES}))

        def capture(*unused, **kwargs):
            assert process.identity(actor.pid)['state'] in ('T', 't')
            if busy:
                raise ValueError('next cursor busy')
            return dict(next_cycle=6, native_used=2, parent_used=1, preserved_files={},
                bounds=dict(train_end_unix=handoff.run.grid.TRAIN_END, hard_end_unix=handoff.run.grid.END,
                            max_native_calls=1858, max_parent_calls=298))

        monkeypatch.setattr(handoff, 'snapshot', capture)
        monkeypatch.setattr(handoff, 'validate_snapshot', lambda value:value)
        actual_exited = process.exited

        def exited(descriptor):
            result = actual_exited(descriptor)
            if result and not (root / handoff.TERMINAL).exists():
                shared.write(root / handoff.TERMINAL, {'status':'FAILED', 'fixture_guard':True})
            return result

        monkeypatch.setattr(process, 'exited', exited)
        result = handoff.drain_at_settled_boundary(authorization=handoff.reference(auth), root=root,
            session=session, cycle=5, ready_reference=args['ready_reference'], output=root / 'output',
            clock=lambda:1)
        assert sentinel.poll() is None
        if busy:
            assert result['released'] is False and actor.poll() is None
            for unused in range(100):
                if process.identity(actor.pid)['state'] not in ('T', 't'):
                    break
                time.sleep(.01)
            assert process.identity(actor.pid)['state'] not in ('T', 't')
        else:
            assert result['status'] == 'RELEASED' and result['terminal_status'] == 'FAILED'
            assert actor.wait(timeout=2) < 0
        assert shared.read(root / 'SHARED_TERMINAL.json')['status'] == 'FAILED'
    finally:
        for child in (actor, sentinel):
            if child.poll() is None:
                child.terminate()
            child.wait(timeout=3)
