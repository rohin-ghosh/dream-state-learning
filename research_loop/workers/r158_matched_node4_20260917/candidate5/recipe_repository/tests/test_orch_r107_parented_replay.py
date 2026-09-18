from copy import deepcopy

import pytest

from organism_v6 import orch_math_feedback_uptake as history_policy
from organism_v6 import orch_r107_parented_replay as replay
from tests.orch_math_feedback_uptake_test import Tokenizer as OriginalTokenizer, tasks


class Tokenizer(OriginalTokenizer):
    def decode(self, token_ids, **unused):
        return ''.join(chr(token) for token in token_ids)


def records(terminal=True):
    tokenizer = Tokenizer()
    task = tasks()[0]
    history = []
    for purpose, raw in zip(history_policy.PURPOSES,
            ('My mistaken result.\nFINAL: 684', 'My recomputation differs.\nFINAL: 651',
             'I retain the recomputed product.\nFINAL: 651')):
        messages = [dict(role='system', content='Use observed evidence.'),
            dict(role='user', content=task['question'] + (' Parent: inspect the product.' if purpose != 'experience' else ''))]
        response = dict(raw=raw, messages=messages, token_ids=tokenizer.encode(raw)
            + ([tokenizer.eos_token_id] if terminal else []), terminal=terminal,
            truncated=not terminal, input_truncated=False,
            prompt_tokens=len(tokenizer.apply_chat_template(messages, tokenize=True,
                add_generation_prompt=True, return_dict=False)))
        history.append(history_policy.record(task, purpose, response))
    return task, history, [['inspect the product.'], ['Do not retain unsupported conclusions.']]


def test_replays_actual_prompts_and_keeps_wrong_records():
    task, history, teachers = records()
    rows = replay.sleep_rows(task, history, teachers)
    assert len(rows) == 3
    assert rows[0]['outcome'] == 'INCORRECT'
    assert rows[1]['outcome'] == rows[2]['outcome'] == 'CORRECT'
    for row, record in zip(rows, history):
        assert row['student_prefix'] == record['response']['messages']
        assert row['target'] == record['response']['raw']
        assert row['objective'].endswith('not_unlikelihood')
        replay.verify_source(row, dict(response=record['response']))
    assert not rows[0]['teacher_in_prefix']
    assert rows[1]['teacher_in_prefix']
    rows[0]['student_prefix'][0]['content'] = 'mutated'
    assert history[0]['response']['messages'][0]['content'] == 'Use observed evidence.'


@pytest.mark.parametrize('terminal', [True, False])
def test_exact_masks_and_no_invented_eos(terminal):
    task, history, teachers = records(terminal)
    tokenizer = Tokenizer()
    row = replay.sleep_rows(task, history, teachers)[0]
    encoded = replay.encode_row(row, tokenizer, 16384)
    generated = tuple(history[0]['response']['token_ids'])
    assert encoded.labels[-len(generated):] == generated
    assert all(label == -100 for label in encoded.labels[:-len(generated)])
    assert (encoded.labels[-1] == tokenizer.eos_token_id) == terminal
    with pytest.raises(ValueError, match='full_source_no_truncation'):
        replay.encode_row(row, tokenizer, 10)


@pytest.mark.parametrize('field,value', [
    ('messages', []), ('messages', [dict(role='assistant', content='not a source turn')]),
    ('terminal', 'true'), ('token_ids', []), ('token_ids', [True]),
])
def test_missing_native_provenance_rejected(field, value):
    task, history, teachers = records()
    response = deepcopy(history[0]['response'])
    response[field] = value
    history[0] = history_policy.record(task, 'experience', response)
    with pytest.raises(ValueError):
        replay.sleep_rows(task, history, teachers)


@pytest.mark.parametrize('field,value', [
    ('target', 'invented'), ('student_prefix', [dict(role='user', content='invented')]),
    ('source_generated_token_ids', [99]), ('append_eos', False),
])
def test_source_changes_rejected(field, value):
    task, history, teachers = records()
    row = replay.sleep_rows(task, history, teachers)[0]
    row[field] = value
    with pytest.raises(ValueError):
        replay.verify_source(row, dict(response=history[0]['response']))


def test_teacher_target_substitution_still_rejected():
    task, history, teachers = records()
    copied = 'Always recompute every arithmetic operation carefully using external tools before answering.'
    teachers[1] = [copied]
    response = dict(history[2]['response'], raw=copied)
    history[2] = history_policy.record(task, 'revision', response)
    with pytest.raises(ValueError, match='teacher_text_in_target'):
        replay.sleep_rows(task, history, teachers)


def test_token_substitution_rejected_by_encoder():
    task, history, teachers = records()
    row = replay.sleep_rows(task, history, teachers)[0]
    row['source_generated_token_ids'][0] += 1
    with pytest.raises(ValueError, match='native_generated_text_must_match'):
        replay.encode_row(row, Tokenizer(), 16384)


def test_noncanonical_generation_tokenization_is_preserved():
    task, history, teachers = records()
    row = replay.sleep_rows(task, history, teachers)[0]
    row['source_generated_token_ids'] = [9001, 1]

    class AlternateTokenizer(Tokenizer):
        def decode(self, token_ids, **unused):
            assert tuple(token_ids) == (9001,)
            return row['target']

    encoded = replay.encode_row(row, AlternateTokenizer(), 16384)
    assert encoded.labels[-2:] == (9001, 1)


def test_prompt_token_count_must_match_actual_source():
    task, history, teachers = records()
    row = replay.sleep_rows(task, history, teachers)[0]
    row['source_prompt_tokens'] += 1
    with pytest.raises(ValueError, match='native_prompt_token_count'):
        replay.encode_row(row, Tokenizer(), 16384)
