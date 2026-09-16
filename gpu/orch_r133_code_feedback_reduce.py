"""Read-only, terminal-gated R133/R136 public TRAIN reduction; zero model calls."""

import argparse
from collections import Counter
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from gpu import orch_r133_code_feedback_collection as collection


SCHEMA = 'R133_CODE_FEEDBACK_REDUCTION_V1'
TERMINALS = ('NATIVE_TERMINAL.json', 'EPISODES_TERMINAL.json', 'EXIT.json',
             'SUPERVISOR_COMPLETE.json', 'SUPERVISOR_FAILED.json')
RESPONSE_KEYS = {'messages', 'prompt_tokens', 'token_ids', 'raw', 'terminal',
                 'truncated', 'max_new_tokens', 'context'}
INTENT_KEYS = {'schema', 'task_id', 'model', 'stage', 'reserved_call', 'messages',
               'messages_sha256', 'shared_draft_call_sha256', 'shared_draft_text_sha256',
               'max_new_tokens', 'started_unix'}
RECOVERIES = ('failed_to_passed', 'formatting_only_recovery', 'task_semantic_correction',
              'interface_execution_recovery', 'unclassified_recovery')
CAVEATS = (
    'Exploratory immediate PUBLIC TRAIN revision only; no retained-learning, persistence or metacognition claim.',
    'Sixteen task clusters, two model states and shared drafts; 96 calls are not 96 independent samples.',
    'Success means passing the fresh task finite CPU checks, not universal program correctness.',
    'Incomplete responses stay in the planned denominator and are excluded explicitly from complete-pair contrasts.',
    'Interface execution recovery overlaps formatting-only recovery; do not add those counts as disjoint classes.',
    'Native token bounds and recorded prefixes are checked; tokenization/decoding and weight hashes are not rerun.',
    'Custody and exclusion-projection coverage remain Main-verified; this reducer does not read source panels.',
)


class EvidenceError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise EvidenceError(code)


def same(actual, expected):
    return collection.digest(actual) == collection.digest(expected)


class Snapshot:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.hashes = {}

    def read(self, relative):
        path = self.root / relative
        require(path.resolve() == path and path.is_file(), 'missing_or_symlink_artifact')
        require(path.stat().st_size <= 8 * 1024 * 1024, 'artifact_size_limit')
        try:
            content = path.read_bytes()
            def unique_keys(pairs):
                document = {}
                for key, value in pairs:
                    require(key not in document, 'duplicate_artifact_JSON_key')
                    document[key] = value
                return document
            document = json.loads(content, object_pairs_hook=unique_keys)
        except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
            raise EvidenceError('unreadable_or_inflight_artifact') from error
        observed_hash = hashlib.sha256(content).hexdigest()
        require(relative not in self.hashes or self.hashes[relative] == observed_hash,
                'artifact_changed_during_reduction')
        self.hashes[relative] = observed_hash
        return document

    def stable(self):
        for relative, expected in self.hashes.items():
            path = self.root / relative
            require(path.resolve() == path and path.is_file()
                    and collection.sha(path) == expected, 'artifact_changed_during_reduction')


def schedule(tasks=None):
    cells = []
    for position in range(collection.TASK_COUNT):
        states = collection.MODELS if position % 2 == 0 else tuple(reversed(collection.MODELS))
        forks = collection.STAGES[1:] if position % 2 == 0 else tuple(reversed(collection.STAGES[1:]))
        for model in states:
            for stage in ('draft', *forks):
                cells.append(dict(planned_call=len(cells) + 1, task_index=position,
                                  task_id_sha256=collection.digest(tasks[position]['id']) if tasks else None,
                                  model=model, stage=stage, state='NOT_INSPECTED', outcome=None))
    return cells


def cell_directory(cell, tasks):
    return 'episodes/' + tasks[cell['task_index']]['id'] + '/' + cell['model']


def artifact_presence(root, cells, tasks):
    for cell in cells:
        prefix = Path(root) / cell_directory(cell, tasks) / cell['stage']
        present = {kind: Path(str(prefix) + '.' + kind + '.json').is_file()
                   for kind in ('INTENT', 'CALL', 'FAILURE')}
        cell['artifacts_present'] = present
        if present['FAILURE']:
            cell['state'] = 'FAILURE_RECORDED'
        elif present['CALL']:
            cell['state'] = 'CALL_PRESENT_UNREDUCED'
        elif present['INTENT']:
            cell['state'] = 'RESERVED_NO_CALL'
        else:
            cell['state'] = 'NOT_STARTED'


def completion_gate(snapshot):
    documents = {name: snapshot.read(name) for name in TERMINALS if (snapshot.root / name).exists()}
    native = documents.get('NATIVE_TERMINAL.json', {})
    episodes = documents.get('EPISODES_TERMINAL.json', {})
    supervisor = documents.get('SUPERVISOR_COMPLETE.json', {})
    exit_record = documents.get('EXIT.json', {})
    require(all(type(document) is dict for document in documents.values()), 'terminal_document_type')
    require(all(type(document.get('status', '')) is str for document in documents.values()), 'terminal_status_type')
    failed = ('SUPERVISOR_FAILED.json' in documents
              or native.get('status', '').startswith('FAILED')
              or episodes.get('status', '').startswith('FAILED')
              or ('EXIT.json' in documents and exit_record.get('exit_code') != 0))
    if failed:
        return 'FAILED_NO_RETRY'
    if not all(name in documents for name in TERMINALS[:-1]):
        return 'NOT_READY'
    require(native.get('status') == episodes.get('status') == supervisor.get('status') == 'COMPLETE'
            and native.get('weights_verified_unchanged') is True
            and type(exit_record.get('exit_code')) is int and exit_record['exit_code'] == 0,
            'successful_native_weight_and_supervisor_barriers_required')
    require(type(native.get('completed_calls')) is int and native['completed_calls'] == collection.CALL_CAP
            and type(episodes.get('reserved_calls')) is int and episodes['reserved_calls'] == collection.CALL_CAP
            and type(episodes.get('completed_calls')) is int and episodes['completed_calls'] == collection.CALL_CAP,
            'terminal_fixed_96_counts')
    require(supervisor.get('native_terminal_sha256') == snapshot.hashes['NATIVE_TERMINAL.json'],
            'supervisor_native_terminal_hash')
    require(same({key: episodes.get(key) for key in ('rows_admitted', 'fit_updates', 'external_calls', 'retry_allowed')},
                 dict(rows_admitted=0, fit_updates=0, external_calls=0, retry_allowed=False)), 'collection_only_terminal')
    return 'COMPLETE'


def category(task, response):
    receipt = collection.execute_public(task, response['raw'])
    success = collection.verify(task, response['raw'])
    if 'observed' in receipt:
        name = 'TASK_PASS' if success else 'TASK_CHECK_FAILURE'
    elif 'expression' not in receipt:
        name = 'PARSER_ERROR'
    elif not receipt['interpreter_started']:
        name = 'SANDBOX_ERROR'
    else:
        name = 'INTERPRETER_ERROR'
    return dict(category=name, success=success,
                complete_response=response['terminal'] and not response['truncated'],
                truncated=response['truncated'])


def verify_response(response, prefix):
    require(type(response) is dict and set(response) == RESPONSE_KEYS, 'native_response_exact_shape')
    require(type(response['raw']) is str and len(response['raw']) <= 131072
            and type(response['terminal']) is bool and type(response['truncated']) is bool,
            'native_response_text_and_flags')
    require(same(response['messages'], prefix), 'actual_native_prefix_differs_from_intent')
    tokens = response['token_ids']
    require(type(tokens) is list and len(tokens) <= collection.MAX_NEW_TOKENS
            and all(type(token) is int and token >= 0 for token in tokens), 'native_token_bounds')
    require(not response['terminal'] or bool(tokens), 'empty_terminal_response')
    require(response['truncated'] is (not response['terminal'] and len(tokens) == collection.MAX_NEW_TOKENS),
            'native_terminal_truncation_consistency')
    require(type(response['prompt_tokens']) is int and 0 < response['prompt_tokens']
            <= collection.CONTEXT_LIMIT - collection.MAX_NEW_TOKENS
            and type(response['max_new_tokens']) is int and response['max_new_tokens'] == collection.MAX_NEW_TOKENS
            and type(response['context']) is int and response['context'] == collection.CONTEXT_LIMIT,
            'native_context_and_budget')


def verify_loaded(snapshot, expected_plan_sha256):
    started = snapshot.read('NATIVE_START.json')
    loaded = snapshot.read('LOADED.json')
    require(type(started) is dict and type(loaded) is dict, 'native_start_and_loaded_document_type')
    authorization = started.get('authorization', {})
    require(type(authorization) is dict, 'native_authorization_document_type')
    require(authorization.get('plan_sha256') == expected_plan_sha256
            and authorization.get('checkpoint') == 18404
            and authorization.get('approved_by') == 'Main'
            and collection.is_hash(authorization.get('host_sha256')) and 'hostname' not in authorization,
            'loaded_authorization_binding')
    require(type(loaded.get('optimizer_count')) is int and loaded['optimizer_count'] == 0
            and same(loaded.get('model_states'), list(collection.MODELS))
            and same(loaded.get('adapter'), authorization.get('adapter'))
            and loaded['adapter']['base_sha256'] == collection.public.BASE_SHA,
            'loaded_frozen_adapter_identity')


def episode_files(root):
    directory = Path(root) / 'episodes'
    require(not directory.is_symlink(), 'episode_directory_symlink')
    paths = list(directory.rglob('*'))
    require(not any(path.is_symlink() for path in paths), 'episode_artifact_symlink')
    return {str(path.relative_to(root)) for path in paths if path.is_file()}


def reduce_complete(snapshot, cells, tasks, expected_plan_sha256):
    verify_loaded(snapshot, expected_plan_sha256)
    expected_files = set()
    for cell in cells:
        directory = cell_directory(cell, tasks)
        expected_files.add(directory + '/COMPLETE.json')
        expected_files.update(directory + '/' + cell['stage'] + '.' + kind + '.json'
                              for kind in ('INTENT', 'CALL', 'PUBLIC', 'VERIFY'))
    require(episode_files(snapshot.root) == expected_files, 'missing_extra_or_failure_episode_artifacts')
    responses, results = {}, []
    cell_index = {(cell['task_index'], cell['model'], cell['stage']): cell for cell in cells}
    for cell in cells:
        task = tasks[cell['task_index']]
        directory = cell_directory(cell, tasks)
        prefix_path = directory + '/' + cell['stage']
        intent = snapshot.read(prefix_path + '.INTENT.json')
        call = snapshot.read(prefix_path + '.CALL.json')
        require(type(intent) is dict and set(intent) == INTENT_KEYS
                and type(call) is dict and set(call) == INTENT_KEYS | {'response', 'finished_unix'},
                'intent_and_call_exact_shape')
        require(same({key: call[key] for key in INTENT_KEYS}, intent), 'call_intent_binding')
        require(type(intent['reserved_call']) is int and intent['reserved_call'] == cell['planned_call']
                and intent['schema'] == collection.SCHEMA and intent['task_id'] == task['id']
                and intent['model'] == cell['model'] and intent['stage'] == cell['stage']
                and type(intent['max_new_tokens']) is int and intent['max_new_tokens'] == collection.MAX_NEW_TOKENS,
                'planned_call_identity_quota_or_budget')
        require(type(intent['started_unix']) in (int, float) and type(call['finished_unix']) in (int, float)
                and 0 < intent['started_unix'] <= call['finished_unix'], 'call_time_order')
        key = (cell['task_index'], cell['model'])
        previous = responses.get((*key, 'draft')) if cell['stage'] != 'draft' else None
        draft = previous['raw'] if previous is not None else None
        receipt = collection.execute_public(task, draft) if cell['stage'] == 'interpreter_feedback' else None
        prefix = collection.messages(task, cell['stage'], draft, receipt)
        require(same(intent['messages'], prefix) and intent['messages_sha256'] == collection.digest(prefix),
                'fork_prefix_or_actual_feedback_no_gold_binding')
        require(intent['shared_draft_call_sha256'] == (snapshot.hashes[directory + '/draft.CALL.json'] if previous else None)
                and intent['shared_draft_text_sha256'] == (collection.digest(draft) if previous else None),
                'shared_draft_hash_binding')
        verify_response(call['response'], prefix)
        response = call['response']
        observed = snapshot.read(prefix_path + '.PUBLIC.json')
        verification = snapshot.read(prefix_path + '.VERIFY.json')
        require(same(observed, collection.execute_public(task, response['raw'])), 'public_receipt_not_actual_execution')
        require(same(verification, dict(success=collection.verify(task, response['raw']))), 'scorer_receipt_mismatch')
        responses[(*key, cell['stage'])] = response
        cell.update(state='RESPONSE_REDERIVED', outcome=category(task, response),
                    intent_sha256=snapshot.hashes[prefix_path + '.INTENT.json'],
                    call_sha256=snapshot.hashes[prefix_path + '.CALL.json'],
                    shared_draft_call_sha256=intent['shared_draft_call_sha256'])
    for position, task in enumerate(tasks):
        states = collection.MODELS if position % 2 == 0 else tuple(reversed(collection.MODELS))
        for model in states:
            directory = 'episodes/' + task['id'] + '/' + model
            before = responses[(position, model, 'draft')]
            result = dict(task_id=task['id'], model=model,
                          shared_draft_call_sha256=snapshot.hashes[directory + '/draft.CALL.json'],
                          forks={stage: collection.correction(task, before, responses[(position, model, stage)])
                                 for stage in collection.STAGES[1:]})
            require(same(snapshot.read(directory + '/COMPLETE.json'), result), 'episode_correction_receipt_mismatch')
            for stage, comparison in result['forks'].items():
                cell_index[(position, model, stage)]['comparison_to_shared_draft'] = {
                    name: comparison[name] for name in ('complete_pair', 'before_success', 'after_success', *RECOVERIES)}
            results.append(result)
    terminal = snapshot.read('EPISODES_TERMINAL.json')
    require(same(terminal['results'], results), 'terminal_results_not_rederived')
    require(episode_files(snapshot.root) == expected_files, 'episode_set_changed_during_reduction')
    return summarize(cells, results)


def fraction(numerator, denominator):
    return dict(numerator=numerator, denominator=denominator,
                value=numerator / denominator if denominator else None)


def summarize(cells, results):
    models = {}
    for model in collection.MODELS:
        selected = [cell for cell in cells if cell['model'] == model]
        episodes = [result for result in results if result['model'] == model]
        stages = {}
        for stage in collection.STAGES:
            outcomes = [cell['outcome'] for cell in selected if cell['stage'] == stage]
            complete = [outcome for outcome in outcomes if outcome['complete_response']]
            passes = sum(outcome['success'] for outcome in complete)
            stages[stage] = dict(planned=16, recorded_calls=len(outcomes), complete=len(complete),
                                incomplete=16 - len(complete), passed_complete=passes,
                                failed_complete=len(complete) - passes,
                                complete_pass_rate=fraction(passes, len(complete)),
                                complete_passes_over_planned=fraction(passes, 16),
                                recorded_categories=dict(Counter(outcome['category'] for outcome in outcomes)))
        forks = {}
        for stage in collection.STAGES[1:]:
            pairs = [result['forks'][stage] for result in episodes if result['forks'][stage]['complete_pair']]
            failed_drafts = sum(not pair['before_success'] for pair in pairs)
            recoveries = {name: sum(pair[name] for pair in pairs) for name in RECOVERIES}
            forks[stage] = dict(planned_pairs=16, complete_pairs=len(pairs),
                                excluded_incomplete_pairs=16 - len(pairs), failed_draft_pairs=failed_drafts,
                                recoveries=recoveries,
                                failed_to_passed_rate=fraction(recoveries['failed_to_passed'], failed_drafts),
                                regressions=sum(pair['before_success'] and not pair['after_success'] for pair in pairs),
                                both_failed=sum(not pair['before_success'] and not pair['after_success'] for pair in pairs),
                                retained_passes=sum(pair['before_success'] and pair['after_success'] for pair in pairs))
        common = [result['forks'] for result in episodes
                  if all(result['forks'][stage]['complete_pair'] for stage in collection.STAGES[1:])]
        table = dict(both_pass=0, feedback_only_pass=0, neutral_only_pass=0, both_fail=0)
        failed_common = []
        for pair in common:
            feedback, neutral = (pair[stage] for stage in collection.STAGES[1:])
            key = ('both_pass' if neutral['after_success'] else 'feedback_only_pass') if feedback['after_success'] else (
                'neutral_only_pass' if neutral['after_success'] else 'both_fail')
            table[key] += 1
            if not feedback['before_success']:
                failed_common.append(pair)
        recovery_contrasts = {}
        for name in RECOVERIES:
            feedback = sum(pair['interpreter_feedback'][name] for pair in failed_common)
            neutral = sum(pair['neutral_review'][name] for pair in failed_common)
            recovery_contrasts[name] = dict(feedback=feedback, neutral=neutral,
                                            difference=fraction(feedback - neutral, len(failed_common)))
        contrast = dict(planned_task_triplets=16, common_complete_triplets=len(common),
                        excluded_incomplete_triplets=16 - len(common), pass_table=table,
                        feedback_minus_neutral_pass_rate=fraction(table['feedback_only_pass'] - table['neutral_only_pass'], len(common)),
                        common_complete_failed_drafts=len(failed_common), recovery_contrasts=recovery_contrasts)
        models[model] = dict(planned_calls=48, planned_tasks=16, stages=stages, forks=forks, paired_contrast=contrast)
    return models


def reduce(root, *, expected_plan_sha256):
    report = dict(schema=SCHEMA, generated_utc=datetime.now(timezone.utc).isoformat(),
                  status='INVALID_EVIDENCE', planned_cells=96, cells=schedule(), model_results=None,
                  outcomes_withheld=True, error_codes=[], exploratory=True, retained_learning_claim=False,
                  persistence_claim=False, metacognition_claim=False, rows_admitted=0, fit_updates=0,
                  model_calls=0, provider_calls=0, retry_allowed=False, caveats=list(CAVEATS),
                  expected_plan_sha256=expected_plan_sha256,
                  reducer_sha256=collection.sha(Path(__file__).resolve()))
    snapshot = Snapshot(root)
    try:
        require(collection.is_hash(expected_plan_sha256), 'explicit_plan_hash_required')
        snapshot.read('PLAN.json')
        require(snapshot.hashes['PLAN.json'] == expected_plan_sha256, 'Main_plan_pin_mismatch')
        snapshot.read('TASKS.json')
        snapshot.read('EXCLUSIONS.json')
        try:
            plan, tasks = collection.verified(snapshot.root, require_launchable=True)
        except (ValueError, KeyError, TypeError, OSError, RecursionError) as error:
            raise EvidenceError('prepared_source_tasks_or_exclusions_mismatch') from error
        report['cells'] = schedule(tasks)
        artifact_presence(snapshot.root, report['cells'], tasks)
        status = completion_gate(snapshot)
        if status == 'NOT_READY' and any(cell['state'] == 'FAILURE_RECORDED' for cell in report['cells']):
            status = 'FAILED_NO_RETRY'
        if status == 'COMPLETE':
            complete_cells = copy.deepcopy(report['cells'])
            models = reduce_complete(snapshot, complete_cells, tasks, expected_plan_sha256)
            snapshot.stable()
            require(not (snapshot.root / 'SUPERVISOR_FAILED.json').exists(), 'supervisor_failure_during_reduction')
            require(plan['source_sha256'] == collection.source_hashes(), 'source_changed_during_reduction')
            report.update(status='COMPLETE', cells=complete_cells, model_results=models, outcomes_withheld=False,
                          verified_artifacts=len(snapshot.hashes), evidence_sha256=collection.digest(snapshot.hashes),
                          producer_source_sha256=plan['source_sha256'])
        else:
            snapshot.stable()
            report['status'] = status
    except (EvidenceError, KeyError, TypeError, ValueError, OSError, RecursionError) as error:
        report['error_codes'] = [str(error) if isinstance(error, EvidenceError) else 'invalid_evidence_structure']
        report['status'] = 'INVALID_EVIDENCE'
    report['artifact_cell_counts'] = dict(Counter(cell['state'] for cell in report['cells']))
    report['terminal_artifact_sha256'] = {name: snapshot.hashes[name] for name in TERMINALS if name in snapshot.hashes}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--expected-plan-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(args.output.name.startswith('REDUCTION') and args.output.suffix == '.json', 'REDUCTION_JSON_output_only')
    result = reduce(args.root, expected_plan_sha256=args.expected_plan_sha256)
    collection.write(args.output, result)
    print(json.dumps({key: result[key] for key in ('status', 'planned_cells', 'outcomes_withheld', 'error_codes')}, sort_keys=True))
    return {'COMPLETE': 0, 'NOT_READY': 2, 'FAILED_NO_RETRY': 3, 'INVALID_EVIDENCE': 4}[result['status']]


if __name__ == '__main__':
    raise SystemExit(main())
