"""Read-only coverage and paired DEV summaries of the bounded CPU judge."""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics
import time

from gpu import orch_r118_cpu_readout_judge as original


require = original.require


def average(values):
    values = list(values)
    return statistics.mean(values) if values else None


def summarize(rows):
    require(rows and len(rows) <= 64, 'bounded_DEV_rows')
    identities = [(row['cycle'], row['task_id']) for row in rows]
    require(len(set(identities)) == len(identities), 'unique_cycle_task')
    cycles = sorted({row['cycle'] for row in rows})
    baseline_cycle = cycles[0]
    baseline = {row['task_id']: row for row in rows if row['cycle'] == baseline_cycle}
    require(len(baseline) == 8, 'eight_baseline_DEV_tasks')
    groups = defaultdict(list)
    for row in rows:
        require(row['status'] in ('COMPLETE', 'UNRESOLVED', 'UNATTEMPTED'), 'known_disposition')
        if row['status'] == 'COMPLETE':
            require(all(type(row[key]) is int and row[key] >= 0
                        for key in ('departures_and_returns', 'shifts')), 'completed_metrics')
        else:
            require(row['departures_and_returns'] is None and row['shifts'] is None,
                    'unknown_not_zero')
        groups[row['input_sha256']].append(row)
    disagreements = []
    for input_sha, members in groups.items():
        signatures = {member['annotation_sha256'] for member in members if member['status'] == 'COMPLETE'}
        if len(signatures) > 1:
            disagreements.append(dict(input_sha256=input_sha, completed_annotation_hashes=sorted(signatures)))
    reports = []
    for cycle in cycles:
        current = [row for row in rows if row['cycle'] == cycle]
        require({row['task_id'] for row in current} == set(baseline), 'same_eight_DEV_tasks')
        completed = [row for row in current if row['status'] == 'COMPLETE']
        paired = [(baseline[row['task_id']], row) for row in completed
                  if baseline[row['task_id']]['status'] == 'COMPLETE']
        coverage = dict(Counter(row['status'] for row in current))
        reports.append(dict(cycle=cycle, expected=8,
            coverage={status: coverage.get(status, 0) for status in ('COMPLETE', 'UNRESOLVED', 'UNATTEMPTED')},
            native_calls=sum(row['native_calls'] for row in current),
            child_token_ids=sum(row['child_token_ids'] for row in current),
            median_child_token_ids_per_task=statistics.median(row['child_token_ids'] for row in current),
            child_output_truncated=sum(row['child_output_truncated'] for row in current),
            complete_only_mean_departures_and_returns=average(row['departures_and_returns'] for row in completed),
            complete_only_mean_shifts=average(row['shifts'] for row in completed),
            paired_completed_tasks=len(paired), baseline_cycle=baseline_cycle,
            paired_mean_departure_delta=average(after['departures_and_returns']-before['departures_and_returns']
                                               for before, after in paired),
            paired_mean_shift_delta=average(after['shifts']-before['shifts'] for before, after in paired),
            paired_mean_token_delta=average(after['child_token_ids']-before['child_token_ids']
                                           for before, after in paired),
            complete_eight_task_comparison=len(paired) == 8))
    return dict(cycles=reports, exact_unique_inputs=len(groups),
        duplicate_input_annotation_disagreements=disagreements,
        disagreements_silently_resolved=False, cached_or_imputed_annotations=0,
        semantic_labels_are_model_judgments=True, sample_order='input_hash_sorted_not_random',
        incomplete_coverage_can_bias_completed_only_means=True,
        control_dependence='NOT_ESTABLISHED_BY_THIS_SINGLE_BRANCH_DEV_SUMMARY',
        retained_learning_established=False, FINAL_read=False)


def reduce_root(root):
    root = Path(root).resolve(strict=True)
    plan = original.read(root / 'PLAN.json')
    publication = original.read(root / 'PUBLICATION.json')
    require(plan['schema'] == 'R118_CPU_DEV_JUDGE_V1' and plan['exploratory_DEV_not_FINAL'] is True,
            'original_DEV_scope')
    require(original.sha(root / 'PLAN.json') == publication['plan_sha256'], 'published_plan')
    require(original.sha(root / 'DOCUMENTS.json') == plan['documents_sha256'], 'document_inventory_hash')
    require(original.sha(root / 'MODEL_SHA256.json') == plan['model_manifest_sha256'], 'model_manifest_hash')
    require(original.sha(plan['source_manifest']) == plan['source_manifest_sha256'], 'source_manifest_hash')
    require(original.sha(original.judge.PROMPT_PATH) == plan['prompt_sha256'], 'fixed_judge_prompt')
    for relative, expected in original.read(plan['source_manifest']).items():
        require(original.sha(Path(plan['source_root']) / relative) == expected, 'frozen_judge_source')
    loaded = original.read(root / 'LOADED.json')
    require(loaded['device'] == 'cpu' and loaded['cuda_initialized'] is False
            and loaded['trainable_parameters'] == 0, 'frozen_CPU_judge_loaded')
    config_path = Path(plan['model_dir']) / 'generation_config.json'
    require(original.sha(config_path) == original.read(root / 'MODEL_SHA256.json')['generation_config.json'],
            'bound_EOS_config')
    eos = original.read(config_path)['eos_token_id']
    eos = eos if isinstance(eos, list) else [eos]
    documents = original.read(root / 'DOCUMENTS.json')
    require(len(documents) == plan['documents'] <= 64, 'exact_document_count')
    observed = time.time()
    progress_paths = sorted((root / 'progress').glob('*.json'))
    progress = {}
    for path in progress_paths:
        receipt = original.read(path)
        index = receipt['index']
        require(type(index) is int and 0 <= index < len(documents) and index not in progress,
                'unique_progress_index')
        require(path.name == f'{index:04d}.json', 'progress_name_binding')
        progress[index] = (receipt, original.sha(path))
    rows = []
    for index, item in enumerate(documents):
        document, provenance = item['document'], item['private_provenance']
        require(document['kind'] == 'held' and provenance['parent_free'] is True
                and provenance['training_buffer'] is False, 'parent_free_DEV_only')
        request = original.judge.request(document)
        require(request == item['request'], 'blind_request_preserved')
        for source in provenance['sources']:
            require(original.sha(source['path']) == source['sha256'], 'source_capture_unchanged')
        require(original.sha(provenance['held_path']) == provenance['held_sha256'], 'held_cache_unchanged')
        row = {key: provenance[key] for key in ('cycle', 'task_id', 'checkpoint_sha256',
            'native_calls', 'child_token_ids', 'child_output_truncated')}
        row.update(index=index, input_sha256=request['input_sha256'], status='UNATTEMPTED',
            departures_and_returns=None, shifts=None, annotation_sha256=None)
        if index in progress:
            receipt, receipt_sha = progress[index]
            response_path = root / f'call_{index:04d}' / 'RESPONSE.json'
            require(Path(receipt['response_path']).resolve(strict=True) == response_path
                    and original.sha(response_path) == receipt['response_sha256'], 'response_binding')
            require(original.read(response_path.parent / 'REQUEST.json') == request
                    and receipt['input_sha256'] == request['input_sha256'], 'response_request_binding')
            response = original.read(response_path)
            tokens = response['token_ids']
            if response['result'].get('reason') == 'input_context_bound':
                require(not tokens and not response['raw'] and response['input_tokens'] + plan['max_new_tokens']
                        > plan['context_limit'], 'context_bound_evidence')
                result = dict(status='UNRESOLVED', reason='input_context_bound', departures_and_returns=None, shifts=None)
            else:
                result = original.interpret(document, response['raw'], bool(tokens) and tokens[-1] in eos)
            require(result == response['result'] and receipt['status'] == result['status'], 'recomputed_annotation')
            row.update(status=result['status'], departures_and_returns=result['departures_and_returns'],
                shifts=result['shifts'], reason=result.get('reason'),
                annotation_sha256=original.judge.previous.digest(result['annotation'])
                    if result['status'] == 'COMPLETE' else None,
                progress_sha256=receipt_sha, response_path=str(response_path), response_sha256=receipt['response_sha256'],
                judge_output_tokens=len(tokens), judge_seconds=response['finished_unix']-response['started_unix'])
        rows.append(row)
    terminal_path = root / 'TERMINAL.json'
    terminal = original.read(terminal_path) if terminal_path.exists() else None
    result = summarize(rows)
    result.update(schema='R118_DEV_JUDGE_REDUCTION_V1', observed_unix=observed, root=str(root),
        plan_sha256=original.sha(root / 'PLAN.json'), documents_sha256=plan['documents_sha256'],
        model_manifest_sha256=plan['model_manifest_sha256'], prompt_sha256=plan['prompt_sha256'],
        source_sha256=original.sha(__file__), attempted_snapshot=len(progress),
        terminal=terminal, terminal_sha256=original.sha(terminal_path) if terminal else None,
        raw_transcripts_exported=False, rows=rows)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = reduce_root(args.root)
    original.write(args.output, result)
    print(json.dumps({key: value for key, value in result.items() if key != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
