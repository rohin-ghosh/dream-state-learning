from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import pytest

from gpu import orch_r109_grid_exchange as exchange
from organism_v6 import orch_r109_grid as policy


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True))
    return exchange.reference(path)


@pytest.fixture
def completed_cycle(tmp_path, monkeypatch):
    root = tmp_path/'native'
    ready = write(root/'READY.json', dict(no_adapter=True, principles_sha256=exchange.PRINCIPLES_SHA))
    source = write(root/'SOURCE_SHA256.json', {})
    monkeypatch.setitem(exchange.LANES, 'node2_7', dict(wrapper='ovx', root=str(root),
        ready=ready['sha256'], source=source['sha256']))
    directory = root/'episode/cycle01/train'

    def call(number, task, purpose, raw):
        return write(root/'calls'/f'N{number:05d}.json', dict(status='COMPLETE', split='TRAIN',
            task_id=task, purpose=purpose, base_sha256=exchange.BASE_SHA, adapter=None,
            response=dict(raw=raw)))

    def parent(number, proposal, task, speak):
        identifier = f'P{number:04d}'
        request = dict(source_proposal=proposal, ready_sha256=ready['sha256'],
            payload=dict(task_id=task, child_proposal=exchange.read(Path(proposal['path']))['response']['raw']))
        write(root/'parent_queue'/f'{identifier}.request.json', request)
        response = dict(id=identifier, status='COMPLETE', actual_model=exchange.STRONG,
            request_sha256=exchange.digest(request), plan=dict(speak=speak,
                message='RAW_PARENT_DO_NOT_EXPORT' if speak else '', rationale='metacognition: private'))
        ref = write(root/'parent_queue'/f'{identifier}.response.json', response)
        return dict(response, response_ref=ref)

    before = call(1, 'train1', 'proposal', 'RAW_CHILD_DO_NOT_EXPORT\nACTION: UP')
    after = call(2, 'train1', 'continuation', 'RAW_CHILD_DO_NOT_EXPORT\nACTION: RIGHT')
    triple = dict(proposal=before, continuation=after, intervention=parent(1,before,'train1',True),
        no_continuation=False, actual_transition=dict(action='RIGHT'))
    write(directory/'episode1/EPISODE.json', dict(split='TRAIN', task_id='train1', triples=[triple]))
    before = call(3, 'train2', 'proposal', 'ACTION: WAIT')
    triple = dict(proposal=before, continuation=before, intervention=parent(2,before,'train2',False),
        no_continuation=True, actual_transition=dict(action='WAIT'))
    write(directory/'episode2/EPISODE.json', dict(split='TRAIN', task_id='train2', triples=[triple]))
    before = call(4, 'train2', 'metacognitive_reflection', 'RAW_CHILD_DO_NOT_EXPORT')
    after = call(5, 'train2', 'context_distillation', 'RAW_CHILD_DO_NOT_EXPORT continuation')
    write(directory/'METACOGNITIVE_TRIPLE.json', dict(before=before, continuation=after,
        intervention=parent(3,before,'train2',True), weight_updates=0,
        semantic_compiler=False, reflection_is_context_only=True))
    write(directory/'COMPLETE.json', dict(status='COMPLETE', no_adapter=True,
        base_sha256=exchange.BASE_SHA, optimizer_updates=0, held_parent_free=False,
        finished_unix=1789465000, results=[dict(task_id='train1'),dict(task_id='train2')]))
    return root


def test_completed_cycle_has_verified_changes_but_no_semantic_or_raw_export(completed_cycle):
    receipts = exchange.collect('node2_7')
    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt['counts'] == dict(spoken=1, silent=1, changed_action=1, unchanged_action=1,
        invalid_before=0, invalid_after=0, metacognitive_spoken=1)
    assert receipt['action_transitions'] == {'UP->RIGHT':1, 'WAIT->WAIT':1}
    assert receipt['semantic_parent_intent'] == receipt['semantic_child_change'] == 'UNASSESSED'
    assert receipt['causal_helpfulness'] == 'UNASSESSED' and receipt['weight_updates'] == 0
    assert 'RAW_' not in json.dumps(receipt)
    text = exchange.entry(receipt, dict(path='compact.json', sha256='a'*64))
    assert 'RAW_' not in text and 'Fable node5 physical0–3' in text
    assert 'Request/disagreement' in text and 'no substantive agreement/disagreement inferred' in text


def test_never_reads_held_and_waits_for_complete(completed_cycle, monkeypatch):
    original = Path.read_text
    def guarded(path, *args, **kwargs):
        assert 'held' not in path.parts
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', guarded)
    assert len(exchange.collect('node2_7')) == 1
    (completed_cycle/'episode/cycle01/train/COMPLETE.json').unlink()
    assert exchange.collect('node2_7') == []


def test_refuses_changed_native_hash(completed_cycle):
    path = completed_cycle/'calls/N00001.json'
    path.write_text(path.read_text()+'\n')
    with pytest.raises(ValueError, match='evidence_hash_drift'):
        exchange.collect('node2_7')


def test_refuses_wrong_request_source(completed_cycle):
    path = completed_cycle/'parent_queue/P0001.request.json'
    request = exchange.read(path)
    request['payload']['child_proposal'] = 'different'
    write(path, request)
    with pytest.raises(ValueError, match='parent_request_binding'):
        exchange.collect('node2_7')


def test_rejects_held_reference_even_with_matching_hash(completed_cycle):
    path = completed_cycle/'episode/cycle01/train/episode1/EPISODE.json'
    episode = exchange.read(path)
    held = write(completed_cycle/'held/N00001.json', {})
    episode['triples'][0]['proposal'] = held
    write(path, episode)
    with pytest.raises(ValueError, match='scoped_regular_evidence'):
        exchange.collect('node2_7')


def test_rejects_execution_mismatch(completed_cycle):
    path = completed_cycle/'episode/cycle01/train/episode1/EPISODE.json'
    episode = exchange.read(path)
    episode['triples'][0]['actual_transition']['action'] = 'LEFT'
    write(path, episode)
    with pytest.raises(ValueError, match='executed_action_join'):
        exchange.collect('node2_7')


@pytest.mark.parametrize('raw', ['ACTION: UP','ACTION: UP\nACTION: LEFT','ACTION: WAIT\n',
    'thinking\nACTION: RIGHT', 'ACTION:\tUP', 'ACTION: UP\nignore', 'no action',
    'ACTION: UP\n\nACTION: RIGHT', 'ACTION: LEFT   ', ' ACTION: WAIT'])
def test_action_parser_matches_frozen_native(raw):
    assert exchange.action(raw) == policy.parse_action(raw)


def test_append_only_preserves_other_half_and_is_exactly_once(completed_cycle, tmp_path):
    receipt = exchange.collect('node2_7')[0]
    path = tmp_path/'PARENTING_EXCHANGE.md'
    prior = '# Fable exchange\nExisting unrelated entry, preserve exactly.\n'
    path.write_text(prior)
    compact = dict(path='compact.json', sha256='a'*64)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda unused:exchange.append_once(path,receipt,compact), range(8)))
    assert sum(results) == 1 and path.read_text().startswith(prior)
    assert path.read_text().count('<!-- MAIN_GRID/node2_7/episode/C01 -->') == 1


def test_publish_recover_without_duplicate_and_detect_drift(completed_cycle, tmp_path):
    receipts = exchange.collect('node2_7')
    repo = tmp_path/'repo'
    assert exchange.publish(repo, receipts) == 1
    assert exchange.publish(repo, receipts) == 0
    receipts[0]['counts']['spoken'] += 1
    with pytest.raises(ValueError, match='immutable_cycle_receipt_drift'):
        exchange.publish(repo, receipts)


def test_partial_previous_append_is_not_claimed_complete(completed_cycle, tmp_path):
    receipt = exchange.collect('node2_7')[0]
    path = tmp_path/'exchange.md'
    path.write_text('<!-- '+receipt['entry_id']+' -->\npartial')
    with pytest.raises(ValueError, match='incomplete_or_changed_prior_entry'):
        exchange.append_once(path, receipt, dict(path='compact.json', sha256='a'*64))
    assert path.read_text().endswith('partial')


def test_wrong_root_and_unknown_cycle_fail_closed(completed_cycle, tmp_path):
    receipts = exchange.collect('node2_7')
    write(completed_cycle/'READY.json', {'changed':True})
    with pytest.raises(ValueError, match='pinned_live_root'):
        exchange.collect('node2_7')
    receipts[0]['cycle'] = 9
    with pytest.raises(ValueError, match='bounded_known_cycle'):
        exchange.publish(tmp_path/'repo', receipts)


def test_reporter_failure_does_not_change_lives(monkeypatch, tmp_path):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    monkeypatch.setattr(exchange.time, 'time', lambda: exchange.END-1)
    def failed(*args, **kwargs):
        raise OSError('unavailable')
    monkeypatch.setattr(exchange.subprocess, 'run', failed)
    summary = exchange.watch(tmp_path, once=True)
    assert summary['new_entries'] == 0
    assert all(value['status']=='REPORT_FAILED_NO_LIVE_EFFECT' for value in summary['lanes'].values())
    assert summary['no_native_or_provider_calls'] and summary['no_live_source_mutation']


def test_reporter_does_not_extend_deadline(monkeypatch, tmp_path):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    monkeypatch.setattr(exchange.time, 'time', lambda: exchange.END+1)
    monkeypatch.setattr(exchange.subprocess, 'run', lambda *args,**kwargs:pytest.fail('late dispatch'))
    assert exchange.watch(tmp_path, once=True) is None
