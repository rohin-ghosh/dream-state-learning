"""Freeze existing task/raw receipts after independent question arithmetic."""

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

from organism_v6 import orch_oracle_repair as policy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    analysis = root / 'research_notes/analysis'
    audit_path = options.output / 'QUESTION_ARITHMETIC.json'
    audits = json.loads(audit_path.read_text())['audits']
    candidates, exclusions, inputs = [], [], {}
    for cohort, directory, task_file in (
            ('270', 'orch_math_rich_20260914_attempt1', 'TASKS_VIEW.json'),
            ('276', 'orch_math_replication_20260914_attempt1', 'TASKS.json')):
        source = analysis / directory
        task_path = source / task_file
        inputs[str(task_path.relative_to(root))] = policy.sha256(task_path)
        tasks = json.loads(task_path.read_text())['tasks']
        if len(tasks) != 32:
            raise ValueError('old_denominator_must_remain_32')
        if cohort == '270':
            raw_path = source / 'RAW_ROWS.json'
            inputs[str(raw_path.relative_to(root))] = policy.sha256(raw_path)
            rows = [(row, raw_path) for row in json.loads(raw_path.read_text())]
        else:
            rows = [(json.loads(path.read_text()), path) for path in sorted(
                (source / 'native_terminal').glob('launch*/native/CALL_*.json'))]
        terse = {row['task_id']: (row, path) for row, path in rows if row['kind'] == 'terse'}
        if len(terse) != 32:
            raise ValueError('exactly_32_old_terse_receipts_required')
        for task in tasks:
            row, path = terse[task['id']]
            inputs[str(path.relative_to(root))] = policy.sha256(path)
            raw = row['target']
            if raw != row['call']['raw'] or policy.text_hash(raw) != row['target_sha256']:
                raise ValueError('old_raw_byte_integrity_failure')
            value = policy.prior_number(raw)
            reason = None
            if row['call'].get('error') or row['call']['truncated']:
                reason = 'OLD_CALL_ERROR_OR_TRUNCATION'
            elif value is None:
                reason = 'NOT_UNAMBIGUOUS_NUMERIC_CHILD_OUTPUT'
            elif value == policy.number(task['gold']):
                reason = ('OLD_CORRECT_NUMERIC' if row['outcome_pass'] else
                          'FORMAT_ONLY_REJECTION_NUMERIC_VALUE_ALREADY_CORRECT')
            audit = audits.get(task['id'])
            if reason is None:
                if audit is None:
                    raise ValueError('missing_independent_question_audit:' + task['id'])
                if audit.get('exclude'):
                    reason = 'QUESTION_AMBIGUITY: ' + audit['exclude']
                elif policy.number(audit['value']) != policy.number(task['gold']):
                    reason = 'GOLD_DISAGREES_WITH_INDEPENDENT_ARITHMETIC: ' + audit['reason']
            item = dict(id=task['id'], cohort=cohort, question=task['question'], gold=task['gold'],
                        question_sha256=policy.digest(' '.join(task['question'].lower().split())),
                        family=task['family'], prior_raw=raw, prior_sha256=policy.text_hash(raw),
                        old_outcome_pass=row['outcome_pass'], source_path=str(path.relative_to(root)),
                        source_sha256=policy.sha256(path), audit=audit)
            if reason:
                exclusions.append(dict(item, reason=reason))
            else:
                candidates.append(dict(item, audit_status='PASS', audited_value=audit['value']))
    ordered = sorted(candidates, key=lambda item: item['question_sha256'])
    selected = [dict(task, branch_order=list(policy.branch_order(position)), shard=policy.shard_for(position))
                for position, task in enumerate(ordered[:24])]
    exclusions.extend(dict(task, reason='ELIGIBLE_BUT_OUTSIDE_PROSPECTIVE_HASH_TOP24') for task in ordered[24:])
    document = dict(created_utc=datetime.now(timezone.utc).isoformat(), tasks=selected,
                    denominator=len(selected), old_denominators={'270': 32, '276': 32},
                    eligible_before_cap=len(ordered), exclusions=exclusions, source_inputs=inputs,
                    question_audit_sha256=policy.sha256(audit_path), new_native_calls=0,
                    no_held_task_access=True)
    policy.validate_roster(document)
    policy.write(options.output / 'ROSTER.json', document)
    print(json.dumps(dict(denominator=len(selected), eligible=len(ordered), exclusions=len(exclusions),
                          roster_sha256=policy.sha256(options.output / 'ROSTER.json'))))


if __name__ == '__main__':
    main()
