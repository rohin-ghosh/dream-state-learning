"""Freeze deterministic task selection and byte-matched original prompt receipts."""

import datetime
import hashlib
import json
from pathlib import Path

from organism_v6 import orch_base_contract as policy


ROOT = Path('research_notes/analysis/orch_base_contract_20260914_attempt1')


def main():
    code_root = Path('research_notes/analysis/orch_code_bounded_20260914_attempt1')
    math_root = Path('research_notes/analysis/orch_math_rich_20260914_attempt1')
    origins = [('CODE', code_root / 'TASKS.json', 2), ('MATH', math_root / 'TASKS_VIEW.json', 1)]
    entries = []
    for domain, path, per_family in origins:
        selected = policy.select(json.loads(path.read_text())['tasks'], per_family)
        for task in selected:
            entries.append(dict(domain=domain, task=task, source_path=str(path),
                                source_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    code_rows = [(str(path), json.loads(path.read_text()), hashlib.sha256(path.read_bytes()).hexdigest())
                 for path in sorted((code_root / 'terminal_verified').glob('shard*/CALL_*.json'))]
    math_file = math_root / 'RAW_ROWS.json'
    math_rows = [(str(math_file), row, hashlib.sha256(math_file.read_bytes()).hexdigest())
                 for row in json.loads(math_file.read_text())]
    for entry in entries:
        domain = entry['domain']
        source = code_rows if domain == 'CODE' else math_rows
        candidates = [(path, row, digest) for path, row, digest in source if row['task_id'] == entry['task']['id']
                      and (row.get('arm') == 'rich' and row.get('turn') == 0 if domain == 'CODE' else row['kind'] == 'rich')]
        assert len(candidates) == 1
        path, row, digest = candidates[0]
        messages, student = policy.prompt(entry)
        assert messages == row['call']['messages'] and student == row['student_prefix']
        entry.update(initial_messages=messages, original_receipt_path=path, original_receipt_sha256=digest,
                     original_target_sha256=row['target_sha256'])
        records = [item for _, item, _ in source if item['task_id'] == entry['task']['id']
                   and item['kind'] == 'record' and (domain != 'CODE' or item['arm'] == 'rich')]
        if not records:
            entry['success_record_template_matches_original_receipt'] = 'NO_ORIGINAL_SUCCESS_RECORD; shared original domain prompt function'
            continue
        assert len(records) == 1
        if domain == 'CODE':
            history = sorted([item for _, item, _ in source if item['task_id'] == entry['task']['id']
                              and item['arm'] == 'rich' and item['kind'] != 'record'], key=lambda item: item['turn'])
            history = [policy.capture(entry, item['call'], item['student_prefix']) for item in history]
            assert policy.code.prompt(entry['task'], 'rich', history, True)[0] == records[0]['call']['messages']
        else:
            prior = records[0]['call']['messages'][1]['content']
            assert policy.math.prompt(entry['task'], 'record', prior)[0] == records[0]['call']['messages']
        entry['success_record_template_matches_original_receipt'] = True
    document = dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), entries=entries,
                    denominator=8, maximum_calls=32, generation_tokens=512, context_tokens=2048,
                    selection='original_order_first_two_per_CODE_family_first_one_per_MATH_family',
                    diagnostic_reuse=True, no_new_gold_targets=True)
    with (ROOT / 'FREEZE.json').open('x') as stream:
        stream.write(json.dumps(document, indent=2, ensure_ascii=False) + '\n')
    print([(entry['domain'], entry['task']['id']) for entry in entries])


if __name__ == '__main__':
    main()
