"""Experimental replay of actual child continuations, not retold histories.

This is a separately labelled L2 treatment. Incorrect outputs remain attributed
records and receive ordinary likelihood training, not an unlikelihood loss.
Parent text may remain in the source prompt but is never substituted as a target.
Incomplete generated prefixes do not acquire an invented terminal EOS.
"""

from copy import deepcopy

from organism_v6 import orch_math_feedback_uptake as history_policy


MODE = 'R107_ACTUAL_CAUSAL_PREFIX_REPLAY_V1'


def sleep_rows(task, history, teacher_rounds):
    rows = history_policy.sleep_rows(task, history, teacher_rounds)
    records = {history_policy.digest(record): record for record in history}
    for row in rows:
        response = records[row['source_record_sha256']]['response']
        messages = response.get('messages')
        history_policy.require(isinstance(messages, list) and messages,
            'actual_source_messages_required')
        history_policy.require(all(isinstance(message, dict)
            and set(message) == {'role', 'content'}
            and message['role'] in ('system', 'user', 'assistant')
            and isinstance(message['content'], str) for message in messages),
            'source_message_schema')
        history_policy.require(messages[-1]['role'] == 'user', 'source_user_turn_required')
        history_policy.require(type(response.get('terminal')) is bool
            and type(response.get('truncated')) is bool, 'native_completion_flags_required')
        history_policy.require(not (response['terminal'] and response['truncated']),
            'contradictory_completion')
        token_ids = response.get('token_ids')
        history_policy.require(isinstance(token_ids, list) and token_ids
            and all(type(token) is int and token >= 0 for token in token_ids),
            'actual_generated_token_ids_required')
        row.update(student_prefix=deepcopy(messages), source_prompt_sha256=history_policy.digest(messages),
            source_generated_token_ids=list(token_ids), append_eos=response['terminal'],
            continuation_only=not response['terminal'], replay_mode=MODE,
            teacher_in_prefix=any(text and text in message['content']
                for teachers in teacher_rounds for text in teachers for message in messages),
            objective='actual_child_continuation_SFT_not_unlikelihood',
            observed_fact_endorsement=False, source_outcome_is_metadata_only=True)
    return rows


def verify_source(row, call):
    response = call['response']
    history_policy.require(row['replay_mode'] == MODE, 'replay_mode_required')
    history_policy.require(row['student_prefix'] == response['messages']
        and row['source_prompt_sha256'] == history_policy.digest(response['messages']),
        'actual_prompt_binding')
    history_policy.require(row['target'] == response['raw']
        and row['target_sha256'] == history_policy.text_sha(response['raw']), 'actual_target_binding')
    history_policy.require(row['source_generated_token_ids'] == response['token_ids']
        and row['append_eos'] is response['terminal']
        and row['continuation_only'] is (not response['terminal']), 'actual_token_completion_binding')
    return row


def encode_row(row, tokenizer, context_limit):
    from gpu import orch_guided_native as native

    history_policy.require(row['replay_mode'] == MODE, 'replay_mode_required')
    history_policy.require(type(row['append_eos']) is bool, 'explicit_eos_policy')
    prompt = tokenizer.apply_chat_template(row['student_prefix'], tokenize=False,
        add_generation_prompt=True, return_dict=False)
    prefix_ids = tuple(tokenizer.encode(prompt, add_special_tokens=False))
    target_ids = tuple(tokenizer.encode(row['target'], add_special_tokens=False))
    history_policy.require(target_ids and not set(tokenizer.all_special_ids).intersection(target_ids),
        'nonempty_special_free_child_target')
    history_policy.require(tuple(tokenizer.encode(prompt + row['target'], add_special_tokens=False))
        == prefix_ids + target_ids, 'actual_prompt_target_boundary')
    generated = target_ids + ((tokenizer.eos_token_id,) if row['append_eos'] else ())
    history_policy.require(generated == tuple(row['source_generated_token_ids']),
        'native_generated_tokens_must_match')
    sequence = prefix_ids + generated
    history_policy.require(0 < len(sequence) <= context_limit, 'full_source_no_truncation')
    labels = (-100,) * len(prefix_ids) + generated
    return native.source.native.EncodedRow(sequence, labels, generated)
