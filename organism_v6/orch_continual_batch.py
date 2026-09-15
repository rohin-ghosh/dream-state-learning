"""Mechanical admission and prospective sampled-author batch semantics."""

import hashlib
import json
import re

from organism_v6 import orch_math_rich as math


SCHEMA = 'ORCH_CONTINUAL_BATCH_V1'
MODE = 'BATCH_SAMPLED_AUTHOR_REVIEW'
BATCH_SIZE = 64
SAMPLE_SIZE = 12
SAMPLE_SEED = 'ROHIN96_CONTINUAL_BATCH_SAMPLE_V1_20260915'
TRAIN_CONTEXT = 2048
AXES = ('first_person', 'grounded_operations', 'checkable_expectation',
        'reusable_content', 'no_padding', 'neutral_prefix_compatible')
QUALITY_AXES = tuple(axis for axis in AXES if axis != 'first_person')
PURPOSE = 'L1_RICHNESS_GENERATION'


def require(value, reason):
    if not value:
        raise ValueError(reason)


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def digest(value):
    return text_sha(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False))


def sample(rows):
    require(len(rows) == BATCH_SIZE, 'fixed64_batch_required')
    require(len({row['target_sha256'] for row in rows}) == BATCH_SIZE, 'dedup_required')
    return sorted(rows, key=lambda row: text_sha(SAMPLE_SEED + ':' + row['target_sha256']))[:SAMPLE_SIZE]


def mechanical(call, task, loaded, prepared, tokenizer, exclusions, provenance):
    require(provenance.get('registered_source_purpose') == PURPOSE and
            provenance.get('source_registry_sha256'), 'parenting_L2_or_unregistered_source_quarantine')
    require('error' not in call and call['task_id'] == task['id'], 'failed_or_wrong_native_call')
    require(task['id'].startswith('gsm8k-train-'), 'train_source_only')
    require(task['question_sha256'] == math.digest(' '.join(task['question'].lower().split())), 'question_hash_drift')
    require(task['id'] not in exclusions['math_ids'] and task['question_sha256'] not in exclusions['question_hashes'],
            'frozen_held_overlap')
    require(loaded['observed'] == prepared['initial'], 'native_actor_base_identity_mismatch')
    response = call['response']
    require(response['terminal'] and not response['truncated'], 'nonterminal_or_truncated')
    target = response['raw']
    require(isinstance(target, str) and target.strip(), 'empty_native_target')
    require(math.final_value(target) == math.number(task['gold']), 'original_math_oracle_failure')
    require(call['gold'] == task['gold'] and call['outcome']['outcome_pass'] is True, 'native_outcome_mismatch')
    require(call['messages'][1] == dict(role='user', content=task['question']), 'source_question_message_mismatch')
    require(call['stage'] in ('source', 'new_record', 'reconsider'), 'not_generation_source')
    require(response['token_ids'][-1] == tokenizer.eos_token_id, 'native_eos_mismatch')
    native_target_ids = response['token_ids'][:-1]
    require(tokenizer.decode(native_target_ids, skip_special_tokens=False,
                            clean_up_tokenization_spaces=False) == target, 'raw_native_token_mismatch')
    prefix = [dict(role='user', content=task['question'])]
    if call['stage'] != 'source':
        require(len(call['messages']) == 4 and call['messages'][2]['role'] == 'assistant', 'actual_source_history_required')
        prefix += [call['messages'][2], dict(role='user', content='Write your own reusable account of this solution and its checks. Finish with a separate FINAL: numeric answer.'
                   if call['stage'] == 'new_record' else 'Reconsider your solution using the given problem. Explain any useful revision or check, then finish with a separate FINAL: numeric answer.')]
    messages = prefix + [dict(role='assistant', content=target)]
    context = tokenizer.apply_chat_template(prefix, tokenize=False, add_generation_prompt=True, return_dict=False)
    full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, return_dict=False)
    require(full == context + target + tokenizer.eos_token + '\n', 'exact_training_boundary')
    prefix_ids = tokenizer.encode(context, add_special_tokens=False)
    target_ids = tokenizer.encode(target, add_special_tokens=False)
    suffix_ids = tokenizer.encode('\n', add_special_tokens=False)
    sequence = tokenizer.encode(full, add_special_tokens=False)
    require(sequence == prefix_ids + target_ids + [tokenizer.eos_token_id] + suffix_ids, 'exact_encoder_token_boundary')
    require(not set(tokenizer.all_special_ids).intersection(target_ids), 'target_special_token_injection')
    require(len(sequence) <= TRAIN_CONTEXT, 'skip_unsupported_traincontext_no_crop')
    require(tokenizer.decode(sequence, skip_special_tokens=False, clean_up_tokenization_spaces=False) == full, 'training_roundtrip')
    serialized = json.dumps(messages, ensure_ascii=False)
    require(not any(identity in serialized for identity in exclusions['route_ids']), 'frozen_route_held_overlap')
    return dict(task_id=task['id'], question=task['question'], question_sha256=task['question_sha256'],
        family=task['family'], gold=task['gold'], kind=call['stage'], condition=call['strategy'],
        student_prefix=prefix, student_prefix_sha256=math.digest(prefix), target=target, target_sha256=text_sha(target),
        generated_tokens=len(native_target_ids), call=response, generation_messages=call['messages'],
        outcome_pass=True, token_contract_pass=True, mechanical_pass=True, candidate=True,
        semantic_status='UNREVIEWED', admitted=False, trainingAllowed=False,
        provenance=provenance, actor=loaded['observed'],
        training_encoding=dict(context_limit=TRAIN_CONTEXT, sequence_length=len(sequence),
            input_ids=sequence, labels=[-100] * len(prefix_ids) + target_ids + [tokenizer.eos_token_id] + [-100] * len(suffix_ids)))


def source_lines(target):
    return [dict(line_id=index, text=line) for index, line in enumerate(target.splitlines(keepends=True), 1)]


def resolve_line_reviews(rows, result):
    expected = {row['target_sha256']: row for row in rows}
    resolved = []
    for review in result['reviews']:
        require(review['target_sha256'] in expected, 'unknown_review_target')
        row = expected[review['target_sha256']]
        require(text_sha(row['target']) == row['target_sha256'], 'immutable_target_hash_mismatch')
        lines = {line['line_id']: line['text'] for line in source_lines(row['target'])}
        identifiers = review.get('evidence_line_ids')
        require(isinstance(identifiers, list) and identifiers and
                all(type(identifier) is int and identifier in lines for identifier in identifiers), 'valid_evidence_line_ids_required')
        require(len(set(identifiers)) == len(identifiers), 'duplicate_evidence_line_ids')
        require('evidence_spans' not in review, 'provider_must_select_lines_not_retype_spans')
        answer = review['independent_answer']
        require(isinstance(answer, str) and re.fullmatch(r'-?(?:0|[1-9]\d*)(?:\.\d+|/[1-9]\d*)?', answer),
                'canonical_numeric_string_required')
        numeric = math.number(answer)
        if review.get('gold_status') == 'VALID':
            require(numeric == math.number(row['gold']), 'unverified_gold_VALID')
        if review.get('has_meaningful_branch') is True:
            require(all(isinstance(review.get(key), str) and review[key].strip() and review[key] in row['target']
                        for key in ('branching_alternative', 'branch_rejection_reason')), 'branch_measurement_requires_literal_evidence')
        resolved.append(dict(review, evidence_spans=[lines[identifier] for identifier in identifiers],
                             evidence_serialization='IMMUTABLE_TARGET_LINE_IDS_V2'))
    return dict(reviews=resolved)


def validate_review(rows, result):
    expected = {row['target_sha256']: row for row in rows}
    reviews = result['reviews']
    require(len(reviews) == len(expected) and {review['target_sha256'] for review in reviews} == set(expected), 'review_inventory_mismatch')
    for review in reviews:
        row = expected[review['target_sha256']]
        require(review['raw_call_sha256'] == row['provenance']['raw_call_sha256'] and
                review['student_prefix_sha256'] == row['student_prefix_sha256'], 'review_hash_mismatch')
        require(review['full_text_read'] is True and bool(review['reason'].strip()), 'actual_fulltext_reason_required')
        require(review['evidence_spans'] and all(span and span in row['target'] for span in review['evidence_spans']), 'literal_evidence_spans_required')
        require(review['status'] in ('PASS', 'FAIL', 'UNRESOLVED'), 'unknown_review_status')
        if review['status'] == 'PASS':
            require(all(review[axis] is True for axis in QUALITY_AXES), 'false_semantic_PASS')
            require(review['gold_status'] == 'VALID' and math.number(review['independent_answer']) == math.number(row['gold']), 'unverified_gold_PASS')
    return reviews


def adjudicate(rows, reviews):
    selected = sample(rows)
    require({review['target_sha256'] for review in reviews} == {row['target_sha256'] for row in selected}
            and len(reviews) == SAMPLE_SIZE, 'frozen_sample_required')
    passed = sum(review['status'] == 'PASS' for review in reviews)
    fatal = any(review['gold_status'] != 'VALID' or review['grounded_operations'] is not True or
                review['neutral_prefix_compatible'] is not True for review in reviews)
    accepted = passed >= 10 and not fatal
    review_map = {review['target_sha256']: review for review in reviews}
    exported = []
    for row in rows:
        review = review_map.get(row['target_sha256'])
        if review and review['status'] != 'PASS':
            continue
        exported.append(dict(row, semantic_status='PASS' if review else 'UNREVIEWED',
            admitted=False, trainingAllowed=False, batch_training_allowed=accepted,
            review=review, admission_mode=MODE, eligibility_version='ROHIN98_SOURCE_BACKED_V2',
            original_semantic_status=row['semantic_status'], first_person_is_measurement_not_gate=True))
    return dict(accepted=accepted, sample_size=SAMPLE_SIZE, sample_pass=passed,
                fatal_grounding_or_gold=fatal, population=BATCH_SIZE, exported_rows=len(exported)), exported
