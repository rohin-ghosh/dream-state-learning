"""CPU-only continuation fixtures; the embedded historical REQUEST is TRAIN only."""

import base64
from copy import deepcopy
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from gpu import orch_r162_train_continuation as continuation
from gpu import orch_r159_train_service as old
from test_orch_r159_train_service import life, start, generate, drain, checks, write, real_dependencies


def archive():
    report = Path(__file__).resolve().parents[1]/'research_loop/workers/R162_TRAIN_CONTINUATION.md'
    encoded = report.read_text().split('<!-- R162_DIAGNOSIS_GZIP_BASE64 -->')[1].split('```text\n')[1].split('```')[0]
    raw = gzip.decompress(base64.b64decode(encoded))
    assert len(raw) == 206564
    assert hashlib.sha256(raw).hexdigest() == '92346dd073f422e405166a207018f79824270775ad33d00beaad14198e22a9ad'
    return json.loads(raw)


def event_evidence(event):
    return dict(publication=dict(id=event['event_id'].split(':')[-1], path=event['source_id'],
        sha256=event['source_sha256']), text=event['text'][len('Tool: '):])


def archived_request():
    return next(row['record'] for row in archive()['rows'] if row['index'] == 280)


def compact(life):
    history = life.stream.history
    history.compact(old.TrainEvent(event_id='synthetic-summary:'+str(len(history.operations)),
        actor='child', text='My tentative summary, not a verified result.', split='TRAIN', phase='compaction',
        episode_id='continual_stream', source_id='synthetic-summary', source_sha256='a'*64,
        origin='TRAIN_COLLECTION'), through=history.frontier())


def inject_environment(life, evidence):
    publication = evidence['publication']
    life.stream.history.append(old.TrainEvent(event_id='environment:inbox:'+publication['id'],
        actor='environment', text='Tool: '+evidence['text'], split='TRAIN', phase='feedback',
        episode_id='continual_stream', source_id=publication['path'], source_sha256=publication['sha256'],
        origin='TRAIN_COLLECTION'))


def identities(life):
    config_ref = write(life.base/'R159.CONFIG.json', life.config)
    owner = dict(schema=continuation.OWNER_SCHEMA, process=dict(pid=2147483647, start_ticks=1234,
        boot_id=continuation.boot_id(), argv=[sys.executable, '-B', str(Path(old.__file__).resolve()),
            'run', '--config', config_ref['path'], '--fresh-owner'], executable=old.reference(life.config['python'])),
        script=old.reference(Path(old.__file__).resolve()), config=config_ref, captured_unix=time.time())
    identity_ref = write(life.base/'SYNTHETIC_OWNER.json', owner)
    return config_ref, identity_ref


def handoff(life, predecessor):
    predecessor.close()
    config_ref, identity_ref = identities(life)
    authority = continuation.prepare(config_ref, identity_ref)
    authority_ref = write(life.base/'R162.AUTHORITY.json', authority)
    return authority_ref


def resume(life, authority_ref, *, api=None):
    watcher = continuation.Continuation(authority_ref, main_go=True, api=life.api if api is None else api)
    life.services.append(watcher)
    return watcher


def snapshot(directory):
    return {path.name: path.read_bytes() for path in directory.iterdir()}


def test_archived_actual_request280_proves_task_and_feedback_loss():
    record = archived_request()
    assert hashlib.sha256(old.gym.encoded(record)+b'\n').hexdigest() == 'adc272f7d86dba47b88f793e2852e5ca18cbb151d8463afd823fce36bc7ca860'
    assert record['document']['split'] == 'TRAIN'
    history = record['document']['resume_state']['state']['history']
    for position in (9, 16):
        evidence = event_evidence(history['events'][position])
        proof = continuation.context_loss(record, evidence)
        assert proof['request_index'] == 280 and proof['event_position'] == position
        assert proof['visible_frontier'] == 39
        assert proof['compaction']['through']['event_count'] == 18
        assert proof['compaction']['receipt_sha256'] == '452c69df28e69273d90af73f1bfcadb80a6b2aaab9dc710b159660225421cff8'
        assert old.Service.exposed(None, record, evidence) is False


@pytest.mark.parametrize('change', ['record', 'resume', 'history', 'messages', 'compaction'])
def test_archived_request_tampering_fails_closed(change):
    record = archived_request()
    evidence = event_evidence(record['document']['resume_state']['state']['history']['events'][9])
    if change == 'record':
        record['sha256'] = '0'*64
    elif change == 'resume':
        record['document']['resume_state']['sha256'] = '0'*64
    elif change == 'history':
        record['document']['history_sha256'] = '0'*64
    elif change == 'messages':
        record['document']['messages'][0]['content'] += 'tampered'
    else:
        resume_state = record['document']['resume_state']
        history = resume_state['state']['history']
        history['operations'][1]['through']['event_count'] = 19
        history['state_sha256'] = old._digest({key: value for key, value in history.items() if key != 'state_sha256'})
        record['document']['history_sha256'] = old._digest(history)
        resume_state['sha256'] = old._digest(resume_state['state'])
    if change != 'record':
        record['sha256'] = old._digest({key: value for key, value in record.items() if key != 'sha256'})
    with pytest.raises(ValueError):
        continuation.context_loss(record, evidence)


@pytest.mark.parametrize('change', ['actor', 'source', 'text', 'id', 'split'])
def test_missing_or_wrong_attribution_is_not_proven_loss(change):
    record = archived_request()
    event = record['document']['resume_state']['state']['history']['events'][9]
    evidence = event_evidence(event)
    if change == 'actor':
        evidence = event_evidence({**event, 'event_id': 'child:inbox:fake'})
    elif change == 'source':
        evidence['publication']['sha256'] = 'b'*64
    elif change == 'text':
        evidence['text'] = 'different task'
    elif change == 'id':
        evidence['publication']['id'] = 'not-published'
    else:
        record['document']['split'] = 'EVAL'
    assert continuation.context_loss(record, evidence) is None


def test_continuation_preserves_prefix_counters_and_excludes_both_owners(life):
    predecessor = start(life)
    predecessor.tick()
    generate(life)
    drain(predecessor)
    saved = deepcopy(predecessor.state)
    authority_ref = handoff(life, predecessor)
    directory = life.root/'train_service_r159'
    before = snapshot(directory)
    calls = list(life.calls)
    watcher = resume(life, authority_ref)
    for field in (*continuation.COUNTERS, 'floor', 'cursor', 'last_commit', 'exposures', 'task_checks'):
        if field != 'read_bytes':
            assert watcher.state[field] == saved[field]
    predecessor_bytes = old.bound(authority_ref)['predecessor']['ledger_bytes']
    assert watcher.state['read_bytes'] == saved['read_bytes']+2*predecessor_bytes
    assert watcher.state['starts'] == saved['starts']+1
    assert watcher.config == life.config and life.calls == calls
    assert watcher.ledger_bytes == predecessor_bytes+sum(path.stat().st_size for path in watcher.directory.glob('*.json'))
    with pytest.raises(BlockingIOError):
        start(life, fresh=False)
    with pytest.raises(BlockingIOError):
        resume(life, authority_ref)
    assert snapshot(directory) == before
    first = json.loads((watcher.directory/'00000000.json').read_bytes())
    assert first['kind'] == 'EPOCH_AUTHORITY' and first['state'] == saved
    assert first['previous_sha256'] == old.bound(authority_ref)['predecessor']['tip']


def test_confirmed_task_loss_advances_new_task_not_old_answer(life):
    predecessor = start(life)
    predecessor.tick()
    generate(life)
    drain(predecessor)
    compact(life)
    watcher = resume(life, handoff(life, predecessor))
    generate(life, 'Answer: 4')
    drain(watcher)
    assert watcher.state['task_index'] == 1 and watcher.state['offers'] == 2
    assert watcher.state['outcomes'][0]['reasons'] == ['TASK_CONTEXT_LOST']
    assert watcher.state['outcomes'][0]['exposed_responses'] == 1
    assert not checks(life)
    assert [call[1] for call in life.calls if call[0] == 'offer'] == [0, 1]
    generate(life, 'Answer: 4')
    drain(watcher)
    assert checks(life)[0][1] == 1 and watcher.state['accepted'] is True


@pytest.mark.parametrize('answer', ['2', '4'])
def test_feedback_loss_is_retirement_not_rendering_or_success(life, answer):
    predecessor = start(life)
    predecessor.tick()
    generate(life, 'Answer: '+answer)
    drain(predecessor)
    feedback = deepcopy(predecessor.state['feedback'])
    failed_bytes = Path(feedback['source']['path']).read_bytes()
    inject_environment(life, feedback)
    compact(life)
    watcher = resume(life, handoff(life, predecessor))
    generate(life, incoming=False)
    drain(watcher)
    outcome = watcher.state['outcomes'][0]
    assert outcome['feedback_unrendered'] is True and outcome['actual_checker_accepted'] is (answer == '4')
    assert outcome['checked'] == 1 and outcome['reasons'] == ['FEEDBACK_CONTEXT_LOST', 'TASK_CONTEXT_LOST']
    assert len(checks(life)) == 1 and watcher.state['task_index'] == 1
    events = [json.loads(path.read_bytes()) for path in watcher.directory.glob('*.json')]
    assert not any(event['kind'] == 'FEEDBACK_ACTUALLY_RENDERED' for event in events)
    retirement = next(event for event in events if event['kind'] == 'CONTEXT_LOSS_RETIREMENT')
    assert retirement['details']['pending_feedback'] == feedback
    assert Path(feedback['source']['path']).read_bytes() == failed_bytes


def test_task_loss_cannot_skip_unseen_unlocated_pending_feedback(life):
    predecessor = start(life)
    predecessor.tick()
    generate(life, 'Answer: 2')
    drain(predecessor)
    compact(life)
    watcher = resume(life, handoff(life, predecessor))
    generate(life, incoming=False)
    drain(watcher)
    assert watcher.state['feedback'] is not None and watcher.state['task_index'] == 0
    assert watcher.state['outcomes'] == [] and len(checks(life)) == 1


def test_eviction_alone_and_never_ingested_task_do_not_prove_compaction(life):
    predecessor = start(life)
    predecessor.tick()
    watcher = resume(life, handoff(life, predecessor))
    generate(life, incoming=False)
    drain(watcher)
    assert watcher.state['task_index'] == 0 and watcher.state['exposures'] == 0
    generate(life)
    drain(watcher)
    history = life.stream.history
    history.evict_oldest(history.frontier(), reason='synthetic explicit eviction')
    generate(life)
    drain(watcher)
    assert watcher.state['task_index'] == 0 and watcher.state['exposures'] == 1


def test_no_backlog_recheck_retirement_or_offer_before_future_boundary(life):
    predecessor = start(life)
    predecessor.tick()
    generate(life)
    drain(predecessor)
    compact(life)
    generate(life, 'Answer: 4')
    watcher = resume(life, handoff(life, predecessor))
    drain(watcher)
    assert not checks(life) and watcher.state['task_index'] == 0 and watcher.state['exposures'] == 1
    generate(life)
    drain(watcher)
    assert watcher.state['task_index'] == 1


def test_preserved_six_response_cadence_and_actual_feedback_barrier(life):
    predecessor = start(life)
    predecessor.tick()
    generate(life)
    drain(predecessor)
    watcher = resume(life, handoff(life, predecessor))
    for unused in range(5):
        generate(life)
        drain(watcher)
    assert watcher.state['exposures'] == 6 and watcher.state['offers'] == 1
    generate(life)
    drain(watcher)
    assert watcher.state['outcomes'][0]['observation'] == 'NO_SUBMISSION/ABANDONED'
    assert watcher.state['offers'] == 2 and not checks(life)


@pytest.mark.parametrize('problem', ['live', 'lock', 'terminal', 'pending', 'cleared_intent', 'partial', 'changed_prefix'])
def test_unsafe_handoff_rejected_without_new_epoch_or_calls(life, problem, monkeypatch):
    predecessor = start(life)
    predecessor.tick()
    config_ref, identity_ref = identities(life)
    if problem == 'terminal':
        predecessor.finish('TEST_STOP')
    elif problem in ('pending', 'cleared_intent'):
        predecessor.state['pending_action'] = dict(action='check', task_index=0, response_index=5)
        predecessor.append('INTENT')
        if problem == 'cleared_intent':
            predecessor.state['pending_action'] = None
            predecessor.append('TEST_CANNOT_CLEAR_UNCERTAINTY')
    elif problem == 'live':
        original = os.path.lexists
        monkeypatch.setattr(os.path, 'lexists', lambda path: True if str(path) == '/proc/2147483647' else original(path))
    if problem != 'lock':
        predecessor.close()
    if problem == 'partial':
        (life.root/'train_service_r159/00009999.json.partial').write_text('partial')
    calls = list(life.calls)
    with pytest.raises((ValueError, BlockingIOError)):
        authority = continuation.prepare(config_ref, identity_ref)
        assert problem == 'changed_prefix'
        reference = write(life.base/'R162.AUTHORITY.json', authority)
        resumed_old = start(life, fresh=False)
        resumed_old.close()
        resume(life, reference)
    assert life.calls == calls and not (life.root/'train_service_r162').exists()


@pytest.mark.parametrize('field', ['pid', 'start_ticks', 'boot_id', 'argv', 'executable', 'script', 'config'])
def test_owner_identity_tampering_rejected(life, field):
    config_ref, identity_ref = identities(life)
    owner = old.bound(identity_ref)
    if field in ('pid', 'start_ticks'):
        owner['process'][field] = 0
    elif field == 'boot_id':
        owner['process'][field] = 'wrong-boot'
    elif field == 'argv':
        owner['process'][field].insert(1, '-c')
    elif field == 'executable':
        owner['process'][field]['sha256'] = '0'*64
    else:
        owner[field]['sha256'] = '0'*64
    with pytest.raises(ValueError):
        continuation.validate_owner(owner, config_ref, life.config)


def test_explicit_go_and_no_epoch_restart_even_after_lock_release(life):
    predecessor = start(life)
    predecessor.tick()
    authority_ref = handoff(life, predecessor)
    with pytest.raises(ValueError, match='Main_GO'):
        continuation.Continuation(authority_ref, main_go=False, api=life.api)
    watcher = resume(life, authority_ref)
    watcher.close()
    before = snapshot(watcher.directory)
    calls = list(life.calls)
    with pytest.raises(FileExistsError):
        resume(life, authority_ref)
    assert snapshot(watcher.directory) == before and life.calls == calls


@pytest.mark.parametrize('field', ['offers', 'check_calls', 'polls', 'read_bytes', 'record_reads', 'output_reserved'])
def test_cumulative_caps_cannot_reset(life, field):
    predecessor = start(life)
    predecessor.tick()
    state = deepcopy(predecessor.state)
    name = continuation.COUNTERS[field]
    maximum = life.config['caps'].get(name, life.config['limits'].get(name))
    state[field] = maximum+1
    with pytest.raises(ValueError, match='cumulative'):
        continuation.limits(state, life.config, time.time())


@pytest.mark.parametrize('budget', ['read_bytes', 'record_reads', 'output_bytes', 'polls', 'ledger_bytes', 'deadline'])
def test_runtime_budget_stops_without_additional_external_actions(life, budget):
    predecessor = start(life)
    predecessor.tick()
    watcher = resume(life, handoff(life, predecessor))
    generate(life, 'Answer: 4')
    calls = list(life.calls)
    if budget == 'ledger_bytes':
        watcher.ledger_bytes = life.config['limits'][budget]-65536
    elif budget == 'output_bytes':
        watcher.state['output_reserved'] = life.config['limits'][budget]
    elif budget == 'deadline':
        watcher.clock = lambda: life.config['deadline_unix']
    else:
        watcher.state[budget] = life.config['limits'][budget]
    drain(watcher)
    assert watcher.state['terminal'] is not None and life.calls == calls


def test_uncertain_new_offer_is_never_retried(life):
    predecessor = start(life)
    predecessor.tick()
    generate(life)
    drain(predecessor)
    compact(life)
    authority_ref = handoff(life, predecessor)
    calls = []

    def uncertain(action, task_index=0, response_index=None):
        calls.append((action, task_index))
        raise RuntimeError('publication may have happened')

    watcher = resume(life, authority_ref, api=uncertain)
    generate(life)
    drain(watcher)
    assert calls == [('offer', 1)] and watcher.state['terminal']['status'] == 'UNCERTAIN_NO_RETRY'
    assert watcher.state['pending_action']['task_index'] == 1
    watcher.tick()
    assert calls == [('offer', 1)]


def test_actual_staged_helper_survives_epoch_without_repreflight(life):
    life.config['dependency_paths'] = real_dependencies()
    predecessor = start(life, api=old.StagedGym(life.config))
    predecessor.tick()
    assert predecessor.state['terminal'] is None
    generate(life)
    drain(predecessor)
    compact(life)
    watcher = resume(life, handoff(life, predecessor), api=old.StagedGym(life.config))
    generate(life)
    drain(watcher)
    assert watcher.state['terminal'] is None and watcher.state['offers'] == 2
    task = json.loads((life.root/'train_environment/task_000001/TASK.json').read_bytes())
    assert task['task_id'] == old.gym.task_id(1) and task['binding'] == watcher.state['generator_binding']
    events = [json.loads(path.read_bytes()) for path in watcher.directory.glob('*.json')]
    assert not any(event['kind'] == 'INTENT' and event['state']['pending_action']['action'] == 'preflight' for event in events)


def test_cli_help_never_activates():
    completed = subprocess.run([sys.executable, '-B', '-m', 'gpu.orch_r162_train_continuation', '--help'],
        capture_output=True, text=True, timeout=20)
    assert completed.returncode == 0 and '--main-go' in completed.stdout


def test_node4_style_standalone_prepare_fullpath_without_mutating_source(life):
    predecessor = start(life)
    predecessor.tick()
    predecessor.close()
    config_ref, identity_ref = identities(life)
    before = {str(path.relative_to(life.source)): path.read_bytes() for path in life.source.rglob('*') if path.is_file()}
    authority_path = life.base/'STANDALONE.AUTHORITY.json'
    environment = dict(os.environ, R162_R159_SCRIPT=str(Path(old.__file__).resolve()),
        PYTHONPATH=str(life.source), PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
    command = [sys.executable, '-B', str(Path(continuation.__file__).resolve())]
    prepared = subprocess.run(command+['prepare', '--config', config_ref['path'], '--config-sha256', config_ref['sha256'],
        '--owner-identity', identity_ref['path'], '--owner-identity-sha256', identity_ref['sha256'],
        '--output', str(authority_path)], cwd=life.base, env=environment, capture_output=True, text=True, timeout=30)
    assert prepared.returncode == 0, prepared.stderr
    authority_ref = json.loads(prepared.stdout)['output']
    refused = subprocess.run(command+['run', '--authority', authority_ref['path'], '--authority-sha256', authority_ref['sha256']],
        cwd=life.base, env=environment, capture_output=True, text=True, timeout=30)
    assert refused.returncode != 0 and 'Main_GO' in refused.stderr
    assert not (life.root/'train_service_r162').exists()
    assert before == {str(path.relative_to(life.source)): path.read_bytes() for path in life.source.rglob('*') if path.is_file()}
    assert not (life.source/'gpu/orch_r159_train_service.py').exists()


def test_standalone_wrong_predecessor_bytes_fail_before_import(tmp_path):
    fake = tmp_path/'wrong.py'
    fake.write_text("raise RuntimeError('must_not_execute')\n")
    result = subprocess.run([sys.executable, '-B', str(Path(continuation.__file__).resolve()), '--help'],
        env=dict(os.environ, R162_R159_SCRIPT=str(fake), PYTHONDONTWRITEBYTECODE='1'),
        capture_output=True, text=True, timeout=20)
    assert result.returncode != 0 and 'original_R159_script_hash' in result.stderr
    assert 'RuntimeError: must_not_execute' not in result.stderr


def test_process_identity_and_expected_ticks_binding(life, monkeypatch):
    actual = continuation.process_identity(os.getpid())
    assert actual['pid'] == os.getpid() and actual['start_ticks'] > 0
    assert actual['executable'] == old.reference(Path(sys.executable).resolve())
    config_ref, identity_ref = identities(life)
    owner = old.bound(identity_ref)
    monkeypatch.setattr(continuation, 'process_identity', lambda pid: deepcopy(owner['process']))
    captured = continuation.identify(config_ref, owner['script']['path'], 2147483647, 1234)
    assert captured['process'] == owner['process']
    with pytest.raises(ValueError, match='expected_start_ticks'):
        continuation.identify(config_ref, owner['script']['path'], 2147483647, 1235)


@pytest.mark.parametrize('target', ['authority', 'identity', 'config', 'ledger'])
def test_handoff_hash_tampering_never_creates_epoch(life, target):
    predecessor = start(life)
    predecessor.tick()
    authority_ref = handoff(life, predecessor)
    authority = old.bound(authority_ref)
    if target == 'authority':
        path = Path(authority_ref['path'])
    elif target == 'identity':
        path = Path(authority['owner_identity']['path'])
    elif target == 'config':
        path = Path(authority['config']['path'])
    else:
        path = sorted((life.root/'train_service_r159').glob('*.json'))[-1]
    path.chmod(0o600)
    path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError):
        resume(life, authority_ref)
    assert not (life.root/'train_service_r162').exists()


def test_audit_read_budget_charged_before_epoch(life):
    predecessor = start(life)
    predecessor.tick()
    predecessor.state['read_bytes'] = life.config['limits']['read_bytes']-1
    predecessor.append('TEST_EXHAUSTED_READS')
    predecessor.close()
    config_ref, identity_ref = identities(life)
    with pytest.raises(ValueError, match='audit_read_budget'):
        continuation.prepare(config_ref, identity_ref)
    assert not (life.root/'train_service_r162').exists()


def test_cumulative_wall_not_reset_at_handoff(life):
    predecessor = start(life)
    predecessor.tick()
    predecessor.state['started_unix'] = time.time()-life.config['limits']['wall_seconds']-1
    predecessor.append('TEST_OLD_WALL_EXPIRED')
    predecessor.close()
    config_ref, identity_ref = identities(life)
    with pytest.raises(ValueError, match='original_cumulative_wall'):
        continuation.prepare(config_ref, identity_ref)


def test_final_task_loss_never_offers_task24_and_keeps_48_checks(life):
    predecessor = start(life)
    predecessor.tick()
    watcher = resume(life, handoff(life, predecessor))
    watcher.state.update(task_index=23, offers=24, check_calls=48, task_checks=2, checked=2)
    calls = list(life.calls)
    watcher.retire({'TASK_CONTEXT_LOST': {'synthetic_counter_boundary': True}})
    assert watcher.state['terminal']['status'] == 'COMPLETE'
    assert watcher.state['offers'] == 24 and watcher.state['check_calls'] == 48
    assert life.calls == calls


def test_checker_48_cap_is_not_reset_in_continuation(life):
    predecessor = start(life)
    predecessor.tick()
    watcher = resume(life, handoff(life, predecessor))
    watcher.state['check_calls'] = 48
    generate(life, 'Answer: 4')
    drain(watcher)
    assert watcher.state['terminal']['status'] == 'STOPPED_NO_RETRY'
    assert not checks(life) and watcher.state['check_calls'] == 48


def test_background_records_are_neither_actions_nor_loss_proofs(life):
    predecessor = start(life)
    predecessor.tick()
    watcher = resume(life, handoff(life, predecessor))
    life.journal.record('READOUT', dict(path='/forbidden/held/data.json'))
    life.journal.record('BACKGROUND_UPDATE', dict(status='synthetic_background'))
    drain(watcher)
    assert watcher.state['offers'] == 1 and watcher.state['exposures'] == 0 and not checks(life)
