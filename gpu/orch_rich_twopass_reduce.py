"""Fixed-denominator readout of two-pass generator artifacts; never launches."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from organism_v6 import orch_rich_twopass as policy


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reduce(root, reviews=None, gold=None):
    root = Path(root)
    reviews, gold = reviews or {}, gold or {}
    assert sha(root / 'TASKS.json') == policy.TASKS_SHA
    document = read(root / 'TASKS.json')
    policy.validate_roster(document)
    tasks = {task['id']: task for task in document['tasks']}
    for task_id, decision in gold.items():
        assert task_id in tasks
        assert decision['question_sha256'] == tasks[task_id]['question_sha256']
        assert decision['status'] in ('VALID', 'INVALID', 'AMBIGUOUS') and decision['reason']
        if decision['status'] == 'VALID':
            assert policy.original.number(decision['independent_answer']) == policy.original.number(tasks[task_id]['gold'])
    rows, inventory, pending = [], {}, []
    ledger = [json.loads(line) for line in (root / 'CALLS.jsonl').read_text().splitlines()]
    assert len(ledger) <= policy.MAX_CALLS
    assert [entry['index'] for entry in ledger] == list(range(len(ledger)))
    for path in sorted(root.glob('shard[0-3]/CALL_*.json')):
        row = read(path)
        assert row['index'] < len(ledger)
        reservation = ledger[row['index']]
        assert all(row[field] == reservation[field] for field in ('position', 'stage', 'condition'))
        assert row['task_id'] == document['tasks'][row['position']]['id']
        assert row['task_id'] in tasks and row['family'] == tasks[row['task_id']]['family']
        key = row['task_id'] + ':' + row['condition'] + ':' + row['stage']
        assert key not in inventory
        inventory[key] = dict(path=str(path.relative_to(root)), sha256=sha(path))
        if row['status'] == 'RESERVED':
            pending.append(key)
        if row['status'] == 'OK':
            assert policy.text_sha(row['target']) == row['target_sha256']
            if key in reviews:
                assert row['stage'] != 'draft'
                decision = reviews[key]
                assert decision['raw_call_sha256'] == inventory[key]['sha256']
                row = policy.admit(row, decision, gold.get(row['task_id'], {}))
        rows.append(row)
    assert set(reviews) <= set(inventory)
    assert len(rows) <= policy.MAX_CALLS
    completed = all((root / f'shard{index}/RESULT.json').exists()
                    and read(root / f'shard{index}/RESULT.json')['status'] == 'COMPLETE' for index in range(4))
    terminal = read(root / 'TERMINAL.json') if (root / 'TERMINAL.json').exists() else dict(status='RUNNING')
    marks = [read(path) for path in root.glob('shard[0-3]/TASK_*.json')]
    complete = completed and terminal['status'] == 'COMPLETE' and len(marks) == 512 and not pending
    successful = [row for row in rows if row['status'] == 'OK']
    source = [row for row in rows if row['stage'] == 'draft']
    complete = complete and len(rows) == len(ledger)
    output = dict(tasks_sha256=policy.TASKS_SHA, fixed_denominator=256, complete=complete,
        terminal=terminal, fits=0, fit_ready=False, pending_calls=pending,
        attempts_recorded=len(ledger), raw_call_files=len(rows),
        reserved_without_call_file=len(ledger) - len(rows), successful_generations=len(successful),
        errors=sum(row['status'] == 'ERROR' for row in rows),
        shared_draft_attempts=sum(entry['stage'] == 'draft' for entry in ledger),
        shared_draft_raw_call_files=len(source),
        shared_draft_outcome_pass=sum(row.get('outcome_pass', False) for row in source),
        known_prompt_tokens=sum(row['call']['prompt_tokens'] for row in successful),
        known_generated_tokens=sum(row['generated_tokens'] for row in successful),
        known_generated_token_ids_including_eos=sum(len(row['call']['token_ids']) for row in successful),
        failed_call_token_usage_unknown=len(successful) != len(ledger),
        reviewed_targets=len(reviews), gold_reviewed_tasks=len(gold),
        claim='GENERATOR_SELECTION_NOT_LEARNING_TRANSFER_OR_REFLECTION_CAUSAL',
        conditions={}, source_token_distribution=sorted(row['generated_tokens'] for row in source if row['status'] == 'OK'),
        raw_inventory=inventory, paired_outcomes=[], gold_counts=dict(Counter(value['status'] for value in gold.values())))
    for condition in policy.CONDITIONS:
        selected = [row for row in rows if row['condition'] == condition]
        by_kind = {}
        for stage in ('final', 'record'):
            group = [row for row in selected if row['stage'] == stage]
            good = [row for row in group if row['status'] == 'OK']
            attempts = sum(entry['condition'] == condition and entry['stage'] == stage for entry in ledger)
            eligible = 256 if stage == 'final' else sum(
                row['stage'] == 'final' and policy.record_allowed(row) for row in selected)
            by_kind[stage] = dict(fixed_denominator=256, attempts=attempts,
                eligible_opportunities=eligible, not_attempted_eligible=eligible - attempts,
                raw_call_files=len(group), reserved_without_call_file=attempts - len(group),
                successful_generations=len(good), errors=sum(row['status'] == 'ERROR' for row in group),
                pending_raw_calls=sum(row['status'] == 'RESERVED' for row in group),
                reviewed_targets=sum(row['task_id'] + ':' + condition + ':' + stage in reviews for row in good),
                unreviewed_targets=sum(row['task_id'] + ':' + condition + ':' + stage not in reviews for row in good),
                outcome_pass=sum(row.get('outcome_pass', False) for row in group),
                token_contract_pass=sum(row.get('token_contract_pass', False) for row in group),
                unreviewed_candidates=sum(row.get('candidate', False) and row.get('semantic_status') == 'UNREVIEWED' for row in group),
                qualified_rows=sum(row.get('admitted', False) for row in group),
                candidate_rows=sum(row.get('candidate', False) for row in group),
                overlong_sources=sum(row.get('generated_tokens', 0) > 400 for row in group),
                generation_cap_hits=sum(row.get('call', {}).get('truncated', False) for row in group),
                semantic_statuses=dict(Counter(row.get('semantic_status', row['status']) for row in group)),
                axes={axis: dict(Counter(str(row.get('review', {}).get(axis)) for row in good)) for axis in policy.admission.AXES},
                generated_tokens=sorted(row['generated_tokens'] for row in good),
                prompt_tokens=sorted(row['call']['prompt_tokens'] for row in good))
        by_family = {}
        for family in policy.original.MINING:
            group = [row for row in selected if row['family'] == family]
            by_family[family] = dict(fixed_denominator=64,
                final_attempts=sum(entry['condition'] == condition and entry['stage'] == 'final'
                    and document['tasks'][entry['position']]['family'] == family for entry in ledger),
                final_successful_generations=sum(row['stage'] == 'final' and row['status'] == 'OK' for row in group),
                final_outcome_pass=sum(row['stage'] == 'final' and row.get('outcome_pass', False) for row in group),
                qualified_rows=sum(row.get('admitted', False) for row in group),
                qualified_distinct_tasks=sorted({row['task_id'] for row in group if row.get('admitted', False)}))
        output['conditions'][condition] = dict(stages=by_kind, families=by_family,
            qualified_rows=sum(row.get('admitted', False) for row in selected), maximum_targets=512,
            known_prompt_tokens=sum(row['call']['prompt_tokens'] for row in selected if row['status'] == 'OK'),
            known_generated_tokens=sum(row['generated_tokens'] for row in selected if row['status'] == 'OK'))
    indexed = {(row['task_id'], row['condition'], row['stage']): row for row in rows}
    if complete:
        assert len({row['index'] for row in rows}) == len(ledger) == terminal['attempted_calls']
        assert terminal['finished_unix'] - terminal['started_unix'] <= 7200
        for task in document['tasks']:
            draft = indexed[(task['id'], 'SHARED', 'draft')]
            if draft['status'] != 'OK':
                assert not any((task['id'], condition, 'final') in indexed for condition in policy.CONDITIONS)
                continue
            for condition in policy.CONDITIONS:
                final = indexed[(task['id'], condition, 'final')]
                record = indexed.get((task['id'], condition, 'record'))
                assert bool(record) == policy.record_allowed(final)
                for row in (final, record):
                    if row is None:
                        continue
                    actual, neutral = policy.prompt(task, row['stage'], condition, draft['target'],
                                                   final.get('target') if row['stage'] == 'record' else None)
                    assert row['messages'] == actual and row['student_prefix'] == neutral
                    assert row['actor_state'] == draft['actor_state']
                    assert row['max_new_tokens'] == policy.CAPS[row['stage']]
                    if row['status'] == 'OK':
                        assert row['common_draft_sha256'] == draft['target_sha256']
                        assert row['call']['messages'] == actual
                        assert len(row['call']['token_ids']) <= policy.CAPS[row['stage']]
                        assert row['call']['prompt_tokens'] <= policy.CONTEXT
        output['complete_paired_history_and_budget_checks'] = True
    for task in document['tasks']:
        pair = dict(task_id=task['id'], family=task['family'])
        for condition in policy.CONDITIONS:
            row = indexed.get((task['id'], condition, 'final'), {})
            pair[condition] = dict(outcome_pass=row.get('outcome_pass', False), status=row.get('status', 'NOT_ATTEMPTED'),
                                   generated_tokens=row.get('generated_tokens'))
        output['paired_outcomes'].append(pair)
    output['paired_final_counts'] = dict(Counter(
        ('BOTH_CORRECT' if pair['BRANCH']['outcome_pass'] and pair['CONTINUE']['outcome_pass'] else
         'BRANCH_ONLY' if pair['BRANCH']['outcome_pass'] else
         'CONTINUE_ONLY' if pair['CONTINUE']['outcome_pass'] else 'NEITHER_CORRECT')
        if pair['BRANCH']['status'] == pair['CONTINUE']['status'] == 'OK' else 'INCOMPLETE_OR_ERROR'
        for pair in output['paired_outcomes']))
    output['shared_draft_known_prompt_tokens'] = sum(row['call']['prompt_tokens'] for row in source if row['status'] == 'OK')
    output['shared_draft_known_generated_tokens'] = sum(row['generated_tokens'] for row in source if row['status'] == 'OK')
    return output, [row for row in rows if row.get('admitted', False)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--review', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    decisions = read(options.review) if options.review else {}
    result, admitted = reduce(options.root, decisions.get('reviews'), decisions.get('gold'))
    options.output.mkdir(parents=True, exist_ok=True)
    (options.output / 'SUMMARY.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    (options.output / 'ADMITTED_ROWS.json').write_text(json.dumps(admitted, sort_keys=True, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('complete', 'terminal', 'attempts_recorded',
          'successful_generations', 'errors', 'reviewed_targets', 'gold_reviewed_tasks', 'conditions')}, indent=2))


if __name__ == '__main__':
    main()
