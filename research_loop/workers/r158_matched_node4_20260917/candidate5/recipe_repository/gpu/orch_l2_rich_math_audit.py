"""Offline, immutable-evidence reconciliation for the completed rich L2 pilot."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

from gpu.orch_l2_rich_math_parent import validate
from organism_v6 import orch_l2_rich_math as policy


NATIVE_ROOT = Path('/localhome/local-rohing/orch_l2_rich_math_20260915_attempt1')


def read(path):
    return json.loads(path.read_text())


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def provider_evidence(outer):
    turns = outer.get('num_turns')
    usage = outer.get('modelUsage') or {}
    utilities = [name for name in usage if name.startswith('claude-haiku-')]
    main_models = [name for name in usage if name.startswith('claude-sonnet-')]
    known = set(utilities + main_models) == set(usage)
    complete = type(turns) is int and turns >= 1 and len(main_models) == 1 and bool(utilities) and known
    return dict(reported_main_turns=turns,
                utility_model_occurrences=len(utilities),
                accounted_call_lower_bound=turns + len(utilities) if complete else None,
                accounting_evidence_complete=complete,
                actual_provider_calls=None,
                exact_call_count_known=False,
                usage_iteration_entries=len((outer.get('usage') or {}).get('iterations', [])),
                model_names=sorted(usage),
                is_error=outer.get('is_error'),
                subtype=outer.get('subtype'))


def verify_manifest(root, manifest):
    files = set()
    for line in manifest.read_text().splitlines():
        expected, relative = line.split('  ', 1)
        path = (root / relative).resolve()
        require(path.is_relative_to(root.resolve()), 'manifest_path_escape')
        require(path not in files, 'duplicate_manifest_path')
        require(sha(path) == expected, 'native_file_digest_mismatch:' + relative)
        files.add(path)
    actual = {path.resolve() for path in root.rglob('*') if path.is_file()}
    require(files == actual, 'native_manifest_file_set_mismatch')
    return len(files)


def verify_adapter(root, identity):
    directory = root / Path(identity['path']).relative_to(NATIVE_ROOT)
    require(directory.resolve().is_relative_to(root.resolve()), 'adapter_path_escape')
    for filename, expected in identity['files']:
        require(Path(filename).name == filename, 'adapter_filename_escape')
        require(sha(directory / filename) == expected, 'adapter_file_digest_mismatch')


def verify_sleep(directory, receipt, previous, frozen):
    require(receipt['input_adapter'] == previous, 'sleep_predecessor_mismatch')
    updates, fits = receipt['updates'], receipt['fits']
    require(type(updates) is int and updates >= 0, 'invalid_update_count')
    losses_path = directory / 'LOSSES.jsonl'
    losses = lines(losses_path) if losses_path.exists() else []
    require(len(losses) == updates, 'sleep_loss_count_mismatch')
    require([row['update'] for row in losses] == list(range(1, updates + 1)), 'sleep_update_sequence_mismatch')
    require(all(math.isfinite(row['loss']) for row in losses), 'nonfinite_sleep_loss')
    if frozen or updates == 0:
        require(updates == fits == 0 and receipt['output_adapter'] == previous,
                'zero_or_frozen_sleep_changed_state')
    else:
        require(fits == 1, 'sleep_fit_count_mismatch')
    return len(losses)


def candidate_dispositions(rows, no_review_reasons):
    eligible = [row for row in rows if row['candidate']]
    admitted = [row for row in eligible if row['admitted']]
    failed = [row for row in eligible if row['semantic_status'] == 'FAIL']
    unreviewed = [row for row in eligible if row['semantic_status'] == 'UNREVIEWED']
    require(len(admitted) + len(failed) + len(unreviewed) == len(eligible), 'unclassified_candidate_disposition')
    require(all(row['semantic_status'] == 'PASS' for row in admitted), 'admitted_without_pass')
    return dict(captures=len(rows), eligible_candidates=len(eligible), prefiltered=len(rows) - len(eligible),
                admitted=len(admitted), semantic_fail=len(failed), no_valid_review=len(unreviewed),
                no_valid_review_reasons=dict(Counter(no_review_reasons.get(row['index'], 'UNCLASSIFIED') for row in unreviewed)))


def held_failure_category(held, response):
    if held['correct']:
        require(response['terminal'] and not response['truncated'] and held.get('answer') is not None,
                'registered_correct_with_invalid_completion')
        return 'registered_correct'
    if response['truncated']:
        return 'truncation'
    if not response['terminal']:
        return 'nonterminal_other'
    if held.get('answer') is None:
        return 'missing_exact_FINAL'
    return 'parsed_wrong'


def audit(recovery):
    root, parent = recovery / 'native', recovery / 'parent_service'
    native_files = verify_manifest(root, recovery / 'NATIVE_SHA256SUMS')
    terminal, cohort, lifetime = (read(root / name) for name in ('PILOT_TERMINAL.json', 'COHORT.json', 'LIFETIME.json'))
    require(terminal['status'] == 'COMPLETE', 'pilot_not_complete')
    require(terminal['lifetime'] == lifetime, 'lifetime_changed')
    require(cohort == policy.cohort(), 'cohort_changed')
    require(not list(root.glob('**/FAILED.json')), 'native_failed_stage')
    learner = lines(root / 'CALLS_LEARNER.jsonl')
    require([row['index'] for row in learner] == list(range(len(learner))), 'learner_ledger_sequence')
    no_review_reasons = {}
    for path in sorted((root / 'parent_queue').glob('*.request.json')):
        request = read(path)
        response = read(path.with_name(path.name.replace('.request.', '.response.')))
        if request['payload']['kind'] == 'semantic' and response['result'].get('error'):
            for candidate in request['payload']['candidates']:
                no_review_reasons[candidate['index']] = 'PARENT_RESPONSE_REJECTED'
    for path in sorted(root.glob('**/REVIEW_*_ERROR.json')):
        response = read(path.with_name(path.name.replace('_ERROR', '')))
        for review in response['reviews']:
            no_review_reasons[review['index']] = read(path)['error']
    processes, loaded_processes, captures, arms = set(), set(), {}, {}
    for arm in policy.ARMS:
        previous = read(root / ('OFF' if arm == 'BOOTSTRAP_OFF' else 'FULL') / 'COMPLETE.json')['output_adapter']
        verify_adapter(root, previous)
        cycles = []
        guardian = read(root / (arm + '_GUARD') / 'TERMINAL.json')
        require(guardian['status'] == 'COMPLETE', 'guardian_not_complete')
        for cycle in range(4):
            phases = ('readout',) if cycle == 0 or arm == 'BOOTSTRAP_OFF' else ('experience', 'sleep', 'readout')
            result = dict(cycle=cycle)
            for phase in phases:
                directory = root / arm / f'cycle{cycle}' / phase
                receipt = read(directory / 'COMPLETE.json')
                require(receipt['status'] == 'COMPLETE', 'stage_not_complete')
                require(receipt['input_adapter'] == previous, 'stage_predecessor_mismatch')
                require(receipt['finished_unix'] < lifetime['deadline_unix'], 'stage_exceeds_deadline')
                process = tuple(receipt['process'])
                require(process not in processes, 'reused_stage_process')
                processes.add(process)
                launch = read(root / (arm + '_GUARD') / f'{cycle}_{phase}_LAUNCH.json')
                require(launch['pid'] == process[1] and int(launch['start_ticks']) == process[2], 'guardian_process_mismatch')
                require(launch['uuid'] == receipt['uuid'] and launch['deadline_unix'] == lifetime['deadline_unix'], 'guardian_binding_mismatch')
                if (directory / 'LOADED.json').exists():
                    loaded = read(directory / 'LOADED.json')
                    require(loaded['observed'] == previous and tuple(loaded['process']) == process, 'loaded_adapter_mismatch')
                    loaded_processes.add(process)
                for path in directory.glob('CALL_*.json'):
                    capture = read(path)
                    require(capture['index'] not in captures, 'duplicate_learner_capture')
                    require('response' in capture and 'error' not in capture, 'failed_learner_capture')
                    captures[capture['index']] = capture
                if phase == 'experience':
                    episodes = [read(path) for path in sorted(directory.glob('EPISODE_*.json'))]
                    require(len(episodes) == receipt['denominator'] == 8, 'experience_denominator')
                    require(sum(episode['final_correct'] for episode in episodes) == receipt['successes'], 'experience_score_mismatch')
                    require(len(receipt['admitted']) == receipt['admitted_rows'], 'admission_count_mismatch')
                    result.update(experience_correct=receipt['successes'], admitted_rows=receipt['admitted_rows'])
                    dispositions = candidate_dispositions(read(directory / 'REVIEWED_ROWS.json'), no_review_reasons)
                    require(dispositions['admitted'] == receipt['admitted_rows'], 'reviewed_admission_count_mismatch')
                    require('UNCLASSIFIED' not in dispositions['no_valid_review_reasons'], 'unclassified_missing_review')
                    result['candidate_dispositions'] = dispositions
                elif phase == 'sleep':
                    verify_sleep(directory, receipt, previous, arm == 'GUIDED_FROZEN')
                    previous = receipt['output_adapter']
                    verify_adapter(root, previous)
                    result.update(updates=receipt['updates'], fits=receipt['fits'], sleep_reason=receipt.get('reason'),
                                  adapter_state_sha256=previous['state_sha256'])
                else:
                    held = [read(path) for path in sorted(directory.glob('HELD_*.json'))]
                    require(len(held) == receipt['denominator'] == 8, 'held_denominator')
                    require([row['task_id'] for row in held] == [task['id'] for task in cohort['held'][cycle]], 'held_task_identity_mismatch')
                    failure_counts = Counter()
                    for task, row in zip(cohort['held'][cycle], held):
                        capture = captures[row['index']]
                        require(capture['messages'] == [dict(role='user', content=task['question'])], 'held_prompt_not_neutral')
                        response = capture['response']
                        correct = policy.judge(task, response['raw'])['correct'] and response['terminal'] and not response['truncated']
                        require(row['correct'] == correct, 'held_score_mismatch')
                        failure_counts[held_failure_category(row, response)] += 1
                    require(sum(row['correct'] for row in held) == receipt['successes'], 'held_total_mismatch')
                    result.update(held_correct=receipt['successes'], held_denominator=8,
                                  retention=receipt['retention'], audit=receipt['audit'],
                                  held_outcome_partition=dict(failure_counts),
                                  readout_state_sha256=previous['state_sha256'])
            cycles.append(result)
        arms[arm] = dict(cycles=cycles, guardian=guardian)
    require(set(captures) == set(range(len(learner))), 'learner_capture_ledger_mismatch')
    require(len(learner) <= lifetime['learner_call_cap'], 'learner_cap_exceeded')
    provider_rows = []
    requests = sorted((root / 'parent_queue').glob('*.request.json'))
    for path in requests:
        request = read(path)
        validate(request['payload'])
        require(request == read(parent / path.name), 'parent_request_copy_mismatch')
        response_name = path.name.replace('.request.', '.response.')
        response = read(parent / response_name)
        require(response == read(root / 'parent_queue' / response_name), 'parent_response_copy_mismatch')
        require(response['id'] == request['id'] and response['request_sha256'] == policy.digest(request), 'parent_response_binding_mismatch')
        outer = read(parent / request['id'] / 'stdout.json')
        evidence = provider_evidence(outer)
        provider_rows.append(dict(id=request['id'], kind=request['payload']['kind'],
                                  candidate_count=len(request['payload'].get('candidates', [])),
                                  returned_error=response['result'].get('error'),
                                  output_tokens=(outer.get('usage') or {}).get('output_tokens'),
                                  stop_reason=outer.get('stop_reason'), terminal_reason=outer.get('terminal_reason'),
                                  result_characters=len(outer.get('result', '')), **evidence))
    reservations = lines(parent / 'CALLS_PROVIDER.jsonl')
    require(len(requests) == len(lines(root / 'CALLS_PARENT_REQUESTS.jsonl')), 'parent_request_count_mismatch')
    require({row['request_id'] for row in reservations} == {row['id'] for row in provider_rows}, 'provider_reservation_request_mismatch')
    review_errors = [dict(path=str(path.relative_to(root)), **read(path)) for path in sorted(root.glob('**/REVIEW_*_ERROR.json'))]
    lower_bound = sum(row['accounted_call_lower_bound'] or 0 for row in provider_rows)
    held_partition = Counter()
    for arm in arms.values():
        for cycle in arm['cycles']:
            held_partition.update(cycle['held_outcome_partition'])
    return dict(created_utc=datetime.now(timezone.utc).isoformat(),
                scope='Offline audit only; no original broker edits, calls, replay, or GPU action',
                native_files_sha256_verified=native_files,
                native_archive_sha256=sha(recovery / 'native.tar.gz'),
                native_manifest_sha256=sha(recovery / 'NATIVE_SHA256SUMS'),
                terminal=terminal, fresh_stage_processes=len(processes), native_loaded_processes=len(loaded_processes),
                learner_calls=len(learner), learner_phases=dict(Counter(row['phase'] for row in learner)),
                held_outcome_partition=dict(held_partition),
                held_partition_method='Original registered correct/answer and response flags only; failure precedence truncation, nonterminal_other, null registered answer (missing_exact_FINAL), parsed_wrong; no prose inference or score changes',
                arms=arms, review_errors=review_errors,
                parent=dict(invocations=len(provider_rows), reservation_slots=len(reservations),
                            reported_main_turns=sum(row['reported_main_turns'] or 0 for row in provider_rows),
                            utility_model_occurrences=sum(row['utility_model_occurrences'] for row in provider_rows),
                            missing_accounting_invocations=sum(not row['accounting_evidence_complete'] for row in provider_rows),
                            accounted_call_lower_bound=lower_bound,
                            reservation_undercount_at_least=max(0, lower_bound - len(reservations)),
                            exact_actual_calls=None, exact_cap_compliance='UNVERIFIED: aggregate usage does not expose utility-call multiplicity',
                            returned_errors=sum(bool(row['returned_error']) for row in provider_rows), rows=provider_rows))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--recovery', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    recovery, output = options.recovery.resolve(), options.output.resolve()
    require(output.parent == recovery, 'output_must_be_in_recovery_root')
    result = audit(recovery)
    with output.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')


if __name__ == '__main__':
    main()
