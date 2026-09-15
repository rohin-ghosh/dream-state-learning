"""Read-only, bounded CODE L2 candidate audit; never trains or calls a model."""

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import time

from organism_v6 import orch_code_bounded as gym
from organism_v6 import orch_r108_code_parent_r113_f3 as policy


ARM = 'PARENTED_DERIVED_CORRECTED_CHILD_CONTINUATION_L2_CANDIDATE'
MAX_PAIRS = 16


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def reference(path):
    return dict(path=str(Path(path).resolve(strict=True)), sha256=sha(path))


def checked(reference):
    require(sha(reference['path']) == reference['sha256'], 'source_changed')
    return read(reference['path'])


def freeze(selection, output):
    output = Path(output)
    require(not output.exists(), 'new_audit_root_required')
    entries = selection['pairs']
    require(0 < len(entries) <= MAX_PAIRS, 'bounded_pair_count')
    require(len({(row['branch'], row['prefix']) for row in entries}) == len(entries), 'unique_pairs')
    rows = []
    for entry in entries:
        branch, prefix = entry['branch'], entry['prefix']
        require(branch in ('F3', 'A3') and re.fullmatch(r'C\d{3}_E[01]', prefix), 'TRAIN_episode_only')
        root = Path(selection['roots'][branch]).resolve(strict=True)
        files = {name: root / 'reservations' / (prefix + suffix + '.json')
            for name, suffix in (('before', '_ORIGINAL'), ('parent', '_PARENT'), ('child', '_REFLECTION'))}
        files.update(triple=root / 'triples' / (prefix + '.json'),
            request=root / 'parent_queue' / (prefix + '_PARENT.request.json'),
            response=root / 'parent_queue' / (prefix + '_PARENT.response.json'), plan=root / 'PLAN.json',
            source_manifest=root / 'SOURCE_SHA256.json')
        for name in ('before', 'parent', 'child'):
            record = read(files[name])
            require(record['split'] == 'TRAIN' and record['status'] == 'COMPLETE'
                and record.get('evaluation_origin') is None, 'completed_TRAIN_only')
        extras = {name: reference(root / name) for name in ('SHARED_ACTIVATION.json',
            'CONT_SOURCE_SHA256.json', 'CONTINUATION_BINDING.json', 'LAUNCH.json',
            'R118_SHARED_NATIVE_LAUNCH.json') if (root / name).is_file()}
        rows.append(dict(branch=branch, prefix=prefix, root=str(root),
            files={name: reference(path) for name, path in files.items()}, lineage_references=extras))
    require(len({row['files']['child']['sha256'] for row in rows}) == len(rows), 'unique_native_children')
    snapshot = dict(schema='R118_CODE_L2_FROZEN_PAIRS_V1', arm=ARM, observed_unix=time.time(),
        selection=selection, pairs=rows, automatic_ingestion=False, inference_calls=0,
        sealed_contents_read=False)
    write_new(output / 'SNAPSHOT.json', snapshot)
    return snapshot


def verify_pair(entry, tasks):
    data = {name: checked(value) for name, value in entry['files'].items()}
    for value in entry['lineage_references'].values():
        require(sha(value['path']) == value['sha256'], 'lineage_changed')
    before, parent, child = (data[name] for name in ('before', 'parent', 'child'))
    triple, request, response, plan = (data[name] for name in ('triple', 'request', 'response', 'plan'))
    require(triple['task_id'] in tasks, 'registered_TRAIN_task')
    task = tasks[triple['task_id']]
    require(task['split'] == 'TRAIN' and triple['parent_present'] is True, 'parented_TRAIN_triple')
    for record, kind, phase in ((before, 'NATIVE', 'episode'), (parent, 'PARENT', 'experience'),
            (child, 'NATIVE', 'reflection')):
        require(record['kind'] == kind and record['phase'] == phase and record['status'] == 'COMPLETE'
            and record['split'] == 'TRAIN' and record.get('evaluation_origin') is None
            and record['routes'].get('evaluation_origin') is None
            and record['cycle'] == triple['cycle'], 'same_completed_TRAIN_episode')
        require(record.get('task_id', task['task_id']) == task['task_id'], 'call_task_identity')
    require(before['finished_unix'] <= parent['started_unix'] <= parent['finished_unix']
        <= child['started_unix'] <= child['finished_unix'], 'actual_causal_order')
    events = triple['events']
    require([event['actor'] for event in events] == ['environment', 'child', 'checker', 'parent', 'child'],
        'exact_experience_triple_not_open_or_readout')
    for event in events:
        require(event['split'] == 'TRAIN' and event['task_id'] == task['task_id']
            and event['task_sha256'] == task['content_sha256'] and event['visibility'] == 'CHILD_VISIBLE'
            and event['child_received'] is True and event['source_sha256'] == text_sha(event['text']),
            'native_visible_event_binding')
    require(events[0]['text'].startswith(task['prompt'])
        and events[1]['text'] == before['response']['raw']
        and events[3]['text'] == parent['guidance'] and bool(parent['guidance'])
        and events[4]['text'] == child['response']['raw'], 'exact_native_parent_child_text')
    causal = [dict(role='assistant' if event['actor'] == 'child' else 'user', content=event['text'])
        for event in events[:-1]]
    messages = child['response']['messages']
    require(len(messages) == len(causal) + 1 and messages[0]['role'] == 'system'
        and messages[1:] == causal, 'actual_feedback_and_parent_in_causal_prefix')
    require(parent['response_sha256'] == entry['files']['response']['sha256']
        and response['status'] == 'COMPLETE' and response['id'] == parent['id']
        and response['actual_model'] == parent['actual_model'] == plan['parent_model'], 'received_not_published_only')
    wire_sha = hashlib.sha256(json.dumps(request, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()
    require(response['request_sha256'] == wire_sha
        and response['payload_sha256'] == request['payload_sha256'], 'original_wire_binding')
    require(request['payload']['task_id'] == task['task_id']
        and request['payload']['task_provenance']['split'] == 'TRAIN'
        and request['payload']['task_provenance']['task_sha256'] == task['content_sha256'], 'parent_TRAIN_task_binding')
    wire = request['payload']['events']
    require(any(event['text'] == events[2]['text'] for event in wire), 'parent_visible_feedback')
    generation = child.get('shared_generation')
    if generation is not None:
        require(type(generation) is int and generation >= 0
            and generation == before.get('shared_generation')
            and child['shared_checkpoint_sha256'] == before['shared_checkpoint_sha256']
            and child['shared_learner']['checkpoint_sha256'] == child['shared_checkpoint_sha256'],
            'actual_same_shared_checkpoint')
    lineage = dict(kind='SHARED_CHILD' if generation is not None else 'PRE_SHARED_RECORDED_BASE_SOURCE',
        shared_generation=generation, checkpoint_sha256=child.get('shared_checkpoint_sha256'),
        parent_model=parent['actual_model'], live_weights_rehashed=False,
        source_manifest=entry['files']['source_manifest'], extra_references=entry['lineage_references'])
    return data, task, lineage


def masked_tokens(response, tokenizer):
    require(response['input_truncated'] is False and type(response['terminal']) is bool
        and type(response['truncated']) is bool and not (response['terminal'] and response['truncated']),
        'native_completion_metadata')
    prefix = tokenizer.apply_chat_template(response['messages'], tokenize=True,
        add_generation_prompt=True, return_dict=False)
    target = response['token_ids']
    require(type(response['prompt_tokens']) is int and len(prefix) == response['prompt_tokens']
        and prefix and target and all(type(token) is int and token >= 0 for token in prefix + target),
        'native_token_count_identity')
    require((target[-1] == tokenizer.eos_token_id) == response['terminal'], 'no_invented_EOS')
    content = target[:-1] if response['terminal'] else target
    require(tokenizer.decode(content, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        == response['raw'], 'native_decode_exact')
    labels = [-100] * len(prefix) + list(target)
    require(labels[:len(prefix)] == [-100] * len(prefix) and labels[len(prefix):] == target,
        'all_prefix_masked_exact_child_labels')
    encoded = dict(input_ids=prefix + target, labels=labels, target_ids=list(target))
    compact = dict(status='PASS', prompt_tokens=len(prefix), child_tokens=len(target),
        target_sha256=text_sha(response['raw']), prompt_ids_sha256=digest(prefix),
        target_ids_sha256=digest(target), labels_sha256=digest(labels),
        parent_prompt_labels_unmasked=0, terminal=response['terminal'], truncated=response['truncated'])
    return encoded, compact


def check_span(span, texts):
    text = texts[span['source']]
    start, end = span['start'], span['end']
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(text), 'evidence_span_bounds')
    require(text_sha(text[start:end]) == span['sha256'], 'evidence_span_identity')
    return text[start:end]


def functional_witness(witness, texts, task):
    if witness is None:
        return dict(status='UNKNOWN', reason='NO_BOUNDED_EXECUTABLE_CORRECTION_WITNESS')
    require(witness['before']['source'] == 'before' and witness['after']['source'] == 'child',
        'actual_before_after_expressions')
    expressions = {name: check_span(witness[name], texts) for name in ('before', 'after')}
    results = []
    for case in task['tests']:
        values = {}
        for name, expression in expressions.items():
            try:
                values[name] = dict(value=gym.evaluate(expression, case['arguments']))
            except (ValueError, TypeError, SyntaxError, KeyError, ZeroDivisionError, OverflowError, IndexError):
                values[name] = dict(unsupported=True)
        results.append(values)
    if any('unsupported' in row[name] for row in results for name in expressions):
        return dict(status='UNKNOWN', reason='BOUNDED_INTERPRETER_UNSUPPORTED', cases=len(results))
    same = lambda left, right: type(left) is type(right) and left == right
    changed = sum(not same(row['before']['value'], row['after']['value']) for row in results)
    before_correct = sum(same(row['before']['value'], case['expected']) for row, case in zip(results, task['tests']))
    after_correct = sum(same(row['after']['value'], case['expected']) for row, case in zip(results, task['tests']))
    status = 'PASS' if changed and after_correct == len(results) and before_correct < after_correct else 'FAIL'
    return dict(status=status, changed_cases=changed, before_correct=before_correct,
        after_correct=after_correct, cases=len(results), outcomes_sha256=digest(results),
        not_a_historical_rescore=True, gate_alone_insufficient=True)


def review_annotation(annotation, data, task, entry):
    texts = dict(child=data['child']['response']['raw'], before=data['before']['response']['raw'],
        parent=data['parent']['guidance'], environment=data['triple']['events'][0]['text'],
        feedback=data['triple']['events'][2]['text'])
    require(annotation['child_call_sha256'] == entry['files']['child']['sha256']
        and annotation['reviewed_whole_target'] == dict(sha256=text_sha(texts['child']), characters=len(texts['child']))
        and annotation['method'] == 'AUTHOR_READ_ONLY_SEMANTIC_REVIEW_NO_MODEL_CALL', 'whole_native_target_review')
    require(annotation['grounding'] in ('PASS', 'FAIL', 'UNKNOWN') and bool(annotation['rationale']), 'grounding_disposition')
    require(annotation['findings'], 'concrete_grounding_findings')
    for finding in annotation['findings']:
        require(finding['claim_role'] in ('ENDORSED_ASSERTION', 'SUPPORTED_OBSERVATION', 'UNCERTAIN')
            and finding['status'] in ('SUPPORTED', 'CONTRADICTED', 'UNKNOWN') and finding['explanation'],
            'claim_not_rejected_path_heuristic')
        require(finding['target']['source'] == 'child'
            and finding['evidence']['source'] in ('environment', 'before', 'parent', 'feedback'),
            'child_claim_vs_actual_visible_evidence')
        check_span(finding['target'], texts)
        check_span(finding['evidence'], texts)
    contradicted = any(item['status'] == 'CONTRADICTED' and item['claim_role'] == 'ENDORSED_ASSERTION'
        for item in annotation['findings'])
    require(annotation['grounding'] != 'FAIL' or contradicted, 'FAIL_requires_endorsed_contradiction')
    require(annotation['grounding'] != 'PASS' or (not contradicted
        and annotation.get('all_endorsed_claims_supported') is True
        and all(item['status'] == 'SUPPORTED' for item in annotation['findings'])), 'no_partial_support_promotion')
    return functional_witness(annotation.get('functional_witness'), texts, task)


def audit(snapshot, annotations, tokenizer):
    require(snapshot['arm'] == ARM and 0 < len(snapshot['pairs']) <= MAX_PAIRS, 'bounded_labelled_snapshot')
    keys = [(row['branch'], row['prefix']) for row in snapshot['pairs']]
    require(len(set(keys)) == len(keys), 'no_duplicate_pairs')
    tasks = {task['task_id']: task for task in policy.tasks('TRAIN')}
    results, corpus = [], []
    for entry in snapshot['pairs']:
        key = entry['branch'] + ':' + entry['prefix']
        result = dict(id=key, arm=ARM, source_child=entry['files']['child'], split='TRAIN',
            verdict='UNKNOWN', automatic_ingestion=False)
        try:
            data, task, lineage = verify_pair(entry, tasks)
            encoded, masking = masked_tokens(data['child']['response'], tokenizer)
            result.update(task_id=task['task_id'], lineage=lineage, masking=masking,
                parent_and_feedback_received=True, response_completion='TERMINAL' if masking['terminal'] else 'INCOMPLETE')
            annotation = annotations.get(key)
            if annotation is None:
                result['reason'] = 'WHOLE_TARGET_REVIEW_MISSING'
            else:
                functional = review_annotation(annotation, data, task, entry)
                result.update(grounding=annotation['grounding'], functional=functional,
                    semantic_review=annotation, reason=annotation['rationale'])
                if annotation['grounding'] == 'FAIL' or functional['status'] == 'FAIL':
                    result['verdict'] = 'REJECTED'
                elif annotation['grounding'] == 'PASS' and functional['status'] == 'PASS':
                    result['verdict'] = 'ELIGIBLE'
                    corpus.append(dict(arm=ARM, split='TRAIN', task_id=task['task_id'],
                        source_call=entry['files']['child'], causal_messages=data['child']['response']['messages'],
                        raw=data['child']['response']['raw'], encoded=encoded, lineage=lineage,
                        automatic_ingestion=False, target_origin='ACTUAL_NATIVE_CHILD_NOT_PARENT'))
        except (ValueError, KeyError, TypeError, OSError) as error:
            result.update(reason='UNVERIFIED_EVIDENCE', error_type=type(error).__name__)
            if isinstance(error, ValueError) and str(error).replace('_', '').isalnum():
                result['failed_check'] = str(error)
        results.append(result)
    return dict(schema='R118_CODE_L2_CANDIDATE_AUDIT_V1', arm=ARM, audited_pairs=len(results),
        counts=dict(Counter(row['verdict'] for row in results)), eligible_rows=len(corpus),
        results=results, model_calls=0, provider_calls=0, ingestion_rows=0,
        historical_replays=0, sealed_contents_read=False), corpus


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('entry', choices=('freeze', 'audit'))
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--selection', type=Path)
    parser.add_argument('--annotations', type=Path)
    parser.add_argument('--tokenizer', type=Path)
    args = parser.parse_args()
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only')
    if args.entry == 'freeze':
        freeze(read(args.selection), args.root)
    else:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(str(args.tokenizer), local_files_only=True, trust_remote_code=False)
        report, corpus = audit(read(args.root / 'SNAPSHOT.json'), read(args.annotations), tokenizer)
        write_new(args.root / 'AUDIT.json', report)
        write_new(args.root / 'ELIGIBLE_CORPUS_NODE_ONLY.json', dict(arm=ARM, rows=corpus, automatic_ingestion=False))
