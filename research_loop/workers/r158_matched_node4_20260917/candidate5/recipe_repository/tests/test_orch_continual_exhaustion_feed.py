from copy import deepcopy
import hashlib
import json

import pytest

from gpu import orch_continual_exhaustion_feed as feed


class Tokenizer:
    eos_token = '§'
    eos_token_id = ord('§')
    all_special_ids = [ord('§')]

    def encode(self, text, **unused):
        return list(map(ord, text))

    def decode(self, tokens, **unused):
        return ''.join(map(chr, tokens))

    def apply_chat_template(self, messages, add_generation_prompt=False, **unused):
        text = ''.join(message['role'] + ':' + message['content'] +
                       ('§\n' if message['role'] == 'assistant' else '\n') for message in messages)
        return text + ('assistant:' if add_generation_prompt else '')


def fixture(shard=1, stage='final_0'):
    payload = dict(id='gsm8k-train-1', question='What is 2 plus 3?', gold='5', family='percentages')
    payload['question_sha256'] = feed.admission.math.digest(payload['question'].lower())
    task = dict(id='B000-P03', family='math', payload=payload)
    identity = dict(state_sha256=feed.original.INITIAL_STATE, base_sha256='base')
    prepared = dict(identity=identity, identities={str(shard): identity})
    loaded = dict(observed=identity, condition=feed.generation.CONDITIONS[shard // 2],
                  uuid=feed.original.UUIDS[shard])
    target = '2+3=5.\nFINAL: 5'
    prior = target if shard >= 4 and stage == 'final_0' else None
    messages = feed.generation.messages(task, shard, prior)
    prompt_hash = hashlib.sha256((json.dumps(messages, sort_keys=True, indent=2) + '\n').encode()).hexdigest()
    call = dict(shard=shard, task_id=task['id'], source_task_id=payload['id'], family='math', stage=stage,
        condition=loaded['condition'], steering_degree=shard // 2, generator_identity=identity,
        generator_classification='ORIGINAL37EC_CONTROL', source_checkpoint_commit_sha256=None,
        source_checkpoint_update=None, source_code_sha256=feed.SOURCE_SHA, prompt_version=feed.generation.VERSION,
        messages=messages, prompt_sha256=prompt_hash, prompt_tokens=200, max_new_tokens=16384,
        target_max_new_tokens=16384, context=32768, trainingAllowed=False,
        outcome=dict(correct=True, admitted=False, semantic_status='UNREVIEWED'),
        response=dict(raw=target, token_ids=Tokenizer().encode(target) + [Tokenizer.eos_token_id],
            terminal=True, truncated=False, messages=messages, prompt_tokens=200, max_new_tokens=16384, context=32768))
    intent = {key: deepcopy(value) for key, value in call.items() if key not in ('response', 'outcome')}
    draft = dict(task_id=task['id'], shard=shard, stage='draft_0', generator_identity=identity,
                 source_code_sha256=feed.SOURCE_SHA, response=dict(raw=target)) if prior else None
    return call, intent, task, loaded, prepared, draft


def candidate(arguments, exclusions=None):
    call, intent, task, loaded, prepared, draft = arguments
    normalized = feed.validate_call(*arguments)
    return feed.admission.mechanical(normalized, task['payload'], loaded, dict(initial=prepared['identity']),
        Tokenizer(), exclusions or dict(math_ids=[], question_hashes=[], route_ids=[]),
        dict(registered_source_purpose=feed.admission.PURPOSE, source_registry_sha256='registered'))


@pytest.mark.parametrize('shard,stage,kind', [(1, 'final_0', 'source'), (2, 'final_0', 'source'),
    (4, 'draft_0', 'source'), (4, 'final_0', 'new_record'), (6, 'final_0', 'reconsider')])
def test_exact_native_to_neutral_preserves_raw(shard, stage, kind):
    arguments = fixture(shard, stage)
    original = deepcopy(arguments)
    row = candidate(arguments)
    assert arguments == original
    assert row['kind'] == kind
    assert row['target'] == arguments[0]['response']['raw']
    assert row['student_prefix'][0]['content'] == arguments[2]['payload']['question']
    assert not row['admitted'] and not row['trainingAllowed']
    assert row['semantic_status'] == 'UNREVIEWED'
    assert row['training_encoding']['labels'][-1] == -100


@pytest.mark.parametrize('field,value,reason', [
    ('shard', 0, 'checkpoint_derived'), ('generator_classification', 'CHECKPOINT_DERIVED_NOT_IMPROVED', 'quarantine'),
    ('source_checkpoint_commit_sha256', 'teacher', 'quarantine'), ('source_checkpoint_update', 256, 'quarantine'),
    ('source_task_id', 'gsm8k-held-1', 'source_task'), ('family', 'route', 'math_completed'),
    ('trainingAllowed', True, 'unadmitted'), ('stage', 'exposure_0', 'known_math_stage'),
    ('source_code_sha256', 'drift', 'reservation_drift'), ('prompt_version', 'old', 'reservation_drift')])
def test_quarantines_wrong_sources(field, value, reason):
    arguments = fixture()
    arguments[0][field] = value
    with pytest.raises(ValueError, match=reason):
        feed.validate_call(*arguments)


def test_reservation_and_prompt_drift_rejected():
    arguments = fixture()
    arguments[1]['prompt_tokens'] = 199
    with pytest.raises(ValueError, match='reservation_drift'):
        feed.validate_call(*arguments)
    arguments = fixture()
    arguments[0]['messages'][1]['content'] = 'substituted question'
    arguments[1]['messages'] = deepcopy(arguments[0]['messages'])
    with pytest.raises(ValueError, match='native_prompt'):
        feed.validate_call(*arguments)


def test_checkpoint_identity_rejected():
    arguments = fixture()
    arguments[0]['generator_identity'] = dict(state_sha256='derived')
    with pytest.raises(ValueError, match='identity_required'):
        feed.validate_call(*arguments)


def test_actual_prior_required():
    arguments = list(fixture(4))
    arguments[-1] = None
    with pytest.raises(ValueError, match='actual_own_prior'):
        feed.validate_call(*arguments)
    arguments = fixture(4)
    arguments[-1]['response']['raw'] = 'invented history'
    with pytest.raises(ValueError, match='native_prompt'):
        feed.validate_call(*arguments)


@pytest.mark.parametrize('held_field', ['math_ids', 'question_hashes', 'route_ids'])
def test_inherits_held_exclusions(held_field):
    arguments = fixture()
    exclusions = dict(math_ids=[], question_hashes=[], route_ids=[])
    values = dict(math_ids=arguments[2]['payload']['id'],
                  question_hashes=arguments[2]['payload']['question_sha256'], route_ids='2 plus 3')
    exclusions[held_field] = [values[held_field]]
    with pytest.raises(ValueError, match='held_overlap'):
        candidate(arguments, exclusions)


@pytest.mark.parametrize('raw,truncated,reason', [('FINAL: 6', False, 'oracle_failure'),
    ('Answer is 5.', False, 'oracle_failure'), ('FINAL: 5', True, 'truncated'),
    ('a' * 2100 + '\nFINAL: 5', False, 'traincontext_no_crop')])
def test_original_oracle_and_encoder_no_salvage(raw, truncated, reason):
    arguments = fixture()
    arguments[0]['response'].update(raw=raw, truncated=truncated,
        token_ids=Tokenizer().encode(raw) + [Tokenizer.eos_token_id])
    with pytest.raises(ValueError, match=reason):
        candidate(arguments)


def test_no_native_root_or_existing_output_writes(tmp_path):
    with pytest.raises(ValueError):
        feed.owned_output(feed.SOURCE / 'orch_continual_exhaustion_feed_bad')
    with pytest.raises(ValueError):
        feed.owned_output(tmp_path)
    fresh = tmp_path / 'orch_continual_exhaustion_feed_snapshot1'
    assert feed.owned_output(fresh) == fresh
    fresh.mkdir()
    with pytest.raises(ValueError):
        feed.owned_output(fresh)
