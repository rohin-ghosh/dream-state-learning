from copy import deepcopy
import json
import os
from types import SimpleNamespace

import pytest

from gpu import orch_r158_train_gym as channel
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream


@pytest.mark.parametrize('raw,terminal,truncated,expected', [
    ('I checked it.\nAnswer: 42', True, False, '42'),
    ('ANSWER： 42\nmore exploration', False, True, '42'),
    ('<answer>1 2\n3 4</answer> then more', False, True, '1 2\n3 4'),
    ('ACT: (1+2)*3\n', False, True, '(1+2)*3'),
    ('Answer: 4', False, True, None),
    ('I might answer 42', True, False, None),
    ('<answer>42', True, False, None),
    ('<answer></answer>', True, False, None),
    ('<answer>4</answer>\n<answer>5', False, True, None),
    ('<answer>4</answer>\nAnswer: 5', False, True, None),
    ('Answer: 4\nAnswer:', False, True, None),
    ('Answer: 4\nAnswer: 5', False, True, None),
    ('<answer>4</answer>\nAnswer: 5\n', False, True, '5'),
    ('Answer: 4\n<answer>5</answer>', False, True, '5'),
    ('Answer: 4\n<answer>5', True, False, None),
    ('<answer>4</answer>\nAnswer:', True, False, None),
    ('<answer>4</answer>\nAnswer: 5', True, False, '5'),
])
def test_answer_contract(raw, terminal, truncated, expected):
    assert channel.parse_answer(raw, terminal=terminal, truncated=truncated) == expected


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -1, 2, True, '1'])
def test_failed_or_invalid_verifier_is_not_a_zero_score(value):
    with pytest.raises(ValueError, match='real_finite_verifier_score'):
        channel.grade(SimpleNamespace(score_answer=lambda **unused: value), {}, 'answer')


def test_verifier_exception_is_not_synthesized_feedback():
    def broken(**unused):
        raise RuntimeError('actual verifier failure')
    with pytest.raises(RuntimeError, match='actual verifier failure'):
        channel.grade(SimpleNamespace(score_answer=broken), {}, 'answer')


@pytest.mark.parametrize('index', [-1, 24, True, '0'])
def test_task_range_cannot_request_held_splits(index):
    with pytest.raises(ValueError, match='bounded_prospective_TRAIN_task'):
        channel.task_id(index)


def test_real_repository_adapter_import_precedes_version_gate(monkeypatch):
    monkeypatch.setattr(channel, 'version', lambda unused: 'wrong-version')
    with pytest.raises(ValueError, match='pinned_reasoning_gym_version'):
        channel.dataset(0)


@pytest.fixture
def life(tmp_path, monkeypatch):
    root = tmp_path / 'orch_r158_cpu_fixture' / 'unparented_learning'
    root.mkdir(parents=True)
    binding = {'package_version': '0.1.25', 'package_source_sha256': 'a' * 64, 'split_ledger_sha256': 'b' * 64}
    source = SimpleNamespace(score_answer=lambda answer, entry: 1.0 if answer == '4' else 0.0)
    monkeypatch.setattr(channel, 'dataset', lambda index: (source, {'question': 'What is two plus two?', 'answer': 'SECRET_REFERENCE'}, binding))
    journal = StreamJournal(root / 'stream', create=True)
    stream = ContinualStream(TrainHistory(system_prompt='Observe and investigate.', birth_prompt='An actual conversation.'),
        context_limit=4096, segment_tokens=128, segments_per_sleep=2, deadline_unix=1000, model_state_sha256='f' * 64)
    journal.record('COMMITTED', {'state': stream.checkpoint()})
    yield root, journal, stream
    journal.close()


def generate(journal, stream, raw, *, truncated=False):
    def response(*args, **unused):
        return dict(raw=raw, token_ids=[10] * 128 if truncated else [10, 11, 2],
                    terminal=not truncated, truncated=truncated)
    stream.step(response, lambda messages: sum(len(message['content'].split()) + 4 for message in messages),
                journal.record, incoming=journal.read_inbox(), now=lambda: 100)


def test_real_journal_offer_check_and_masking(life):
    root, journal, stream = life
    offered = channel.offer(root, 0)
    published = json.loads(open(offered['publication']['path']).read())
    assert published['actor'] == 'environment' and published['speaker'] == 'Tool'
    assert 'SECRET_REFERENCE' not in str(published)
    assert 'sha256' not in published['text'] and 'schema' not in published['text']
    generate(journal, stream, 'I checked the addition.\nAnswer: 4')
    records = sorted((root / 'stream/records').glob('[0-9]' * 20 + '.json'))
    response_index = next(json.loads(path.read_text())['index'] for path in records if json.loads(path.read_text())['kind'] == 'RESPONSE')
    result = channel.check(root, 0, response_index)
    assert result['accepted'] is True
    feedback = json.loads(open(result['publication']['path']).read())
    assert 'real check' in feedback['text'] and feedback['actor'] == 'environment'
    assert 'SECRET_REFERENCE' not in str(result) + str(feedback)
    assert stream.rows[-1]['prefix_loss'] is False and stream.rows[-1]['target_loss'] is True
    assert 'What is two plus two?' not in stream.rows[-1]['target']
    with pytest.raises(FileExistsError):
        channel.check(root, 0, response_index)


def test_question_must_be_in_actual_child_request(life):
    root, journal, stream = life
    generate(journal, stream, 'Answer: 4')
    channel.offer(root, 0)
    with pytest.raises(ValueError, match='task_actually_rendered'):
        channel.check(root, 0, 2)


@pytest.mark.parametrize('raw', [
    '<answer>4</answer>\n<answer>5', '<answer>4</answer>\nAnswer: 5',
    'Answer: 4\nAnswer:', 'Answer: 4\n<answer>',
])
def test_unfinished_revision_publishes_no_verifier_feedback(life, raw):
    root, journal, stream = life
    channel.offer(root, 0)
    generate(journal, stream, raw, truncated=True)
    before = sorted((root / 'stream/inbox').glob('*.json'))
    records = [json.loads(path.read_text()) for path in sorted((root / 'stream/records').glob('[0-9]' * 20 + '.json'))]
    response = next(record for record in records if record['kind'] == 'RESPONSE')
    assert channel.check(root, 0, response['index'])['status'] == 'NO_COMPLETE_ANSWER'
    assert sorted((root / 'stream/inbox').glob('*.json')) == before
    assert not list(channel.directory(root, 0).glob('answer_*'))


@pytest.mark.parametrize('raw,expected', [
    ('<answer>4</answer>\nAnswer: 5\n', '5'),
    ('Answer: 5\n<answer>4</answer>', '4'),
])
def test_complete_mixed_revision_is_the_checked_answer(life, raw, expected):
    root, journal, stream = life
    channel.offer(root, 0)
    generate(journal, stream, raw, truncated=True)
    records = [json.loads(path.read_text()) for path in sorted((root / 'stream/records').glob('[0-9]' * 20 + '.json'))]
    response = next(record for record in records if record['kind'] == 'RESPONSE')
    result = channel.check(root, 0, response['index'])
    saved = json.loads(open(result['result_path']).read())
    assert saved['answer'] == expected and result['accepted'] == (expected == '4')


@pytest.mark.parametrize('task_index', [0, 1, 2])
def test_installed_actual_adapter_offer_check_cpu(tmp_path, task_index):
    pytest.importorskip('reasoning_gym')
    source, entry, binding = channel.dataset(task_index)
    assert binding['package_version'] == '0.1.25'
    assert channel.grade(source, entry, str(entry['answer']))['accepted'] is True
    root = tmp_path / f'orch_r158_installed_smoke_{task_index}' / 'unparented_learning'
    root.mkdir(parents=True)
    journal = StreamJournal(root / 'stream', create=True)
    try:
        stream = ContinualStream(TrainHistory(system_prompt='CPU fixture.', birth_prompt='Synthetic integration.'),
            context_limit=4096, segment_tokens=128, segments_per_sleep=2, deadline_unix=1000, model_state_sha256='f' * 64)
        journal.record('COMMITTED', {'state': stream.checkpoint()})
        offered = channel.offer(root, task_index)
        generate(journal, stream, '<answer>' + str(entry['answer']) + '</answer>')
        records = [json.loads(path.read_text()) for path in sorted((root / 'stream/records').glob('[0-9]' * 20 + '.json'))]
        response = next(record for record in records if record['kind'] == 'RESPONSE')
        result = channel.check(root, task_index, response['index'])
        assert result['accepted'] is True
        assert stream.rows[-1]['prefix_loss'] is False
        assert stream.rows[-1]['target_loss'] is True
        generate(journal, stream, 'I received a real checker result.')
        assert any('Training puzzle check: accepted' in message['content'] for message in stream.rows[-1]['prefix'])
        assert offered['rendered'] is False
    finally:
        journal.close()


def test_source_tamper_refused(life):
    root, journal, stream = life
    channel.offer(root, 0)
    generate(journal, stream, 'Answer: 4')
    records = [json.loads(path.read_text()) for path in sorted((root / 'stream/records').glob('[0-9]' * 20 + '.json'))]
    position = next(index for index, record in enumerate(records) if record['kind'] == 'RESPONSE')
    triple = deepcopy(records[position - 1:position + 2])
    triple[1]['document']['response']['raw'] = 'Answer: 5'
    with pytest.raises(ValueError, match='record_hash'):
        channel.verify_triple(triple, 'What is two plus two?')


def test_existing_task_is_never_republished(life):
    root, unused_journal, unused_stream = life
    channel.offer(root, 0)
    before = list((root / 'stream/inbox').glob('*.json'))
    with pytest.raises(FileExistsError):
        channel.offer(root, 0)
    assert list((root / 'stream/inbox').glob('*.json')) == before


def test_mutated_task_receipt_is_rejected_before_scoring(life):
    root, journal, stream = life
    channel.offer(root, 0)
    generate(journal, stream, 'Answer: 4')
    path = channel.directory(root, 0) / 'TASK.json'
    task = json.loads(path.read_bytes())
    task['text'] += '\nForged addition.'
    os.chmod(path, 0o600)
    path.write_bytes(channel.encoded(task))
    with pytest.raises(ValueError, match='published_task_receipt_binding'):
        channel.check(root, 0, 3)
