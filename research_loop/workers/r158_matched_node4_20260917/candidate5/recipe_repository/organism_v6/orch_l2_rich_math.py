"""Small finite congruence-join pilot and exact bootstrap row boundary."""

from collections import Counter
from copy import deepcopy
import hashlib
import json
from math import gcd

from organism_v6 import orch_math_rich as original
from organism_v6 import orch_math_record as record
from organism_v6 import orch_math_scale as admission


FAMILY = 'PM_CONGRUENCE_JOIN_V1'
PACKET_SHA = '52197d8d0f73528af69b61e6f244e5b1570f2bcfafd5ebb79d4058c959946837'
CONTEXT = 4096
MAX_GENERATED = 512
HOURS = 4
GPU_HOURS = 16
LEARNER_CALLS = 1536
PARENT_CALLS = 192
PAIRS = ((7, 11), (11, 13), (13, 17), (17, 19))
ARMS = ('GUIDED_SLEEP', 'GUIDED_FROZEN', 'UNPARENTED_SLEEP', 'BOOTSTRAP_OFF')
BOOTSTRAP_PRESENTATIONS = 16
GUIDANCE = original.RICH_GUIDANCE
RECONSIDER = 'Reconsider your solution using the given constraints. Explain any useful revision or check, then finish with a separate FINAL: numeric answer.'
NEUTRAL_RECORD = 'Write your own reusable account of this solution and its checks. Finish with a separate FINAL: numeric answer.'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_packet(rows):
    assert len(rows) == 16
    for row in rows:
        assert row['admitted'] and row['semantic_status'] == 'PASS' and row['candidate']
        assert row['outcome_pass'] and row['token_contract_pass']
        assert 150 <= row['generated_tokens'] <= 400
        assert hashlib.sha256(row['target'].encode()).hexdigest() == row['target_sha256']
        assert original.digest(row['student_prefix']) == row['student_prefix_sha256']
        assert row['target'] == row['call']['raw']
        assert row['student_prefix'] and row['student_prefix'][-1]['role'] == 'user'
        assert not any(message['role'] == 'system' for message in row['student_prefix'])
    assert len({row['target_sha256'] for row in rows}) == 16
    return dict(rows=16, tasks=len({row['task_id'] for row in rows}),
                conditions=dict(Counter(row['condition'] for row in rows)))


def reference(task):
    left, right = task['left_modulus'], task['right_modulus']
    assert gcd(left, right) == 1
    answers = [value for value in range(left * right)
               if value % left == task['left_residue'] and value % right == task['right_residue']]
    assert len(answers) == 1
    return answers[0]


def question(task):
    return (f"Find the least nonnegative integer x such that x leaves remainder {task['left_residue']} "
            f"when divided by {task['left_modulus']}, and remainder {task['right_residue']} "
            f"when divided by {task['right_modulus']}. Explain your reasoning and any check you make. "
            'Finish with a separate line FINAL: followed by just the integer answer.')


def cohort():
    used = set()

    def task(label, position):
        left, right = PAIRS[position % len(PAIRS)]
        counter = 0
        while True:
            seed = int(digest(['ORCH_L2_RICH_MATH_V1', label, position, counter]), 16)
            residues = (left, right, seed % left, (seed // left) % right)
            if residues not in used:
                break
            counter += 1
        used.add(residues)
        result = dict(id=f'{FAMILY}_{label}_{position}', family=FAMILY,
                      left_modulus=left, right_modulus=right,
                      left_residue=residues[2], right_residue=residues[3])
        result['question'] = question(result)
        result['reference_answer'] = reference(result)
        return result

    train = [[task(f'TRAIN_C{cycle}', position) for position in range(8)] for cycle in range(1, 4)]
    held = [[task(f'HELD_S{stage}', position) for position in range(8)] for stage in range(4)]
    return dict(family=FAMILY, train=train, held=held, same_stage_common_to_all_arms=True,
                reference='exhaustive enumeration of all residues below the product',
                mining_or_reserved_l1_l3_used=False)


def judge(task, raw):
    answer = original.final_value(raw)
    return dict(answer=str(answer) if answer is not None else None,
                correct=answer is not None and answer == original.number(str(reference(task))))


def encode_packet(rows, tokenizer):
    validate_packet(rows)
    return encode_rows(rows, tokenizer)


def encode_rows(rows, tokenizer):
    from gpu import orch_guided_native as native

    encoded = []
    for row in rows:
        prefix, target = row['student_prefix'], row['target']
        full_messages = prefix + [dict(role='assistant', content=target)]
        context = tokenizer.apply_chat_template(prefix, tokenize=False, add_generation_prompt=True, return_dict=False)
        full = tokenizer.apply_chat_template(full_messages, tokenize=False, add_generation_prompt=False, return_dict=False)
        assert full == context + target + tokenizer.eos_token + '\n'
        prefix_ids = native.source.native._encode(tokenizer, context)
        target_ids = native.source.native._encode(tokenizer, target)
        suffix_ids = native.source.native._encode(tokenizer, '\n')
        supervised = target_ids + (tokenizer.eos_token_id,)
        sequence = native.source.native._encode(tokenizer, full)
        assert 150 <= len(target_ids) <= 400 and len(sequence) <= CONTEXT
        assert not set(tokenizer.all_special_ids).intersection(target_ids)
        assert native.source.native._decode(tokenizer, sequence) == full
        assert sequence == prefix_ids + supervised + suffix_ids
        item = native.source.native.EncodedRow(sequence,
                    (-100,) * len(prefix_ids) + supervised + (-100,) * len(suffix_ids), supervised)
        native.bridge.validate_encoding_boundary(item, prefix_ids=prefix_ids, target_ids=target_ids,
            suffix_ids=suffix_ids, eos_token_id=tokenizer.eos_token_id, validate_masks=native.masks.validate_masks)
        encoded.append(item)
    return tuple(encoded)


def capture(task, response, prefix, kind, index):
    evaluation_task = dict(task, gold=str(reference(task)))
    row = original.capture(evaluation_task, kind, response, prefix)
    bounded = 150 <= row['generated_tokens'] <= 400 and not response['truncated'] and response['prompt_tokens'] <= CONTEXT
    row.update(index=index, context_contract=CONTEXT, student_prefix_sha256=original.digest(prefix),
               candidate=row['outcome_pass'] and bounded, token_contract_pass=bounded,
               actual_child=True, trainingAllowed=False)
    return row


def experience(task, generate, coach=None, telemetry=None):
    public = [dict(role='user', content=task['question'])]
    captures, interventions = [], []
    last_correct = False
    for attempt in range(3):
        actual = [dict(role='system', content=GUIDANCE)] + deepcopy(public)
        if interventions and interventions[-1].get('speak'):
            actual[-1]['content'] += '\n\nPARENT LEARNING COACH:\n' + interventions[-1]['message']
        response, index = generate(actual, purpose='experience', task_id=task['id'], attempt=attempt)
        row = capture(task, response, deepcopy(public), 'rich', index)
        captures.append(row)
        public.append(dict(role='assistant', content=response['raw']))
        last_correct = row['outcome_pass']
        if attempt == 0 and coach is not None:
            intervention = coach(dict(kind='coach', task_id=task['id'], question=task['question'],
                messages=deepcopy(public), outcome_correct=last_correct, learner=deepcopy(telemetry or {})))
            interventions.append(intervention)
        if attempt < 2:
            public.append(dict(role='user', content=RECONSIDER))
    if last_correct:
        prefix = deepcopy(public) + [dict(role='user', content=NEUTRAL_RECORD)]
        actual = deepcopy(public) + [dict(role='user', content=record.NEW_RECORD)]
        response, index = generate(actual, purpose='record', task_id=task['id'])
        captures.append(capture(task, response, prefix, 'new_record', index))
    return dict(task_id=task['id'], final_correct=last_correct, captures=captures,
                parent_interventions=interventions, actual_calls=len(captures))


def review_payload(rows):
    return dict(kind='semantic', candidates=[dict(index=row['index'], target=row['target'],
        target_sha256=row['target_sha256'], student_prefix=row['student_prefix'],
        student_prefix_sha256=row['student_prefix_sha256']) for row in rows if row['candidate']])


def admit_reviews(rows, response):
    decisions = {decision['index']: decision for decision in response.get('reviews', [])}
    output = []
    for row in rows:
        if row['index'] not in decisions:
            output.append(row)
            continue
        decision = decisions[row['index']]
        assert row['candidate']
        output.append(admission.admit(row, decision, dict(status='VALID')))
    assert set(decisions) <= {row['index'] for row in rows}
    return output
