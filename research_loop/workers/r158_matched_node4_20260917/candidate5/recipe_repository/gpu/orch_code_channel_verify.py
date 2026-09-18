"""CPU-only native-token replay and descriptive payload audit; never changes admission."""

import argparse
import json
from pathlib import Path

from gpu.orch_code_channel_freeze import digest, write
from organism_v6 import orch_code_channel as policy


def payload_audit(task, row):
    last = row['target'].strip().splitlines()[-1] if row['target'].strip() else ''
    if last.startswith('ACTION: '):
        payload = last[len('ACTION: '):]
        projection = 'EXACT_INLINE_ACTION_PREFIX_REMOVAL_DIAGNOSTIC_ONLY'
    else:
        payload = last
        projection = 'UNCHANGED_FINAL_LINE'
    try:
        expression, unused = policy.code.parse_action(payload)
        outcome = policy.code.check(task, expression)
    except Exception as error:
        outcome = dict(success=False, error=str(error))
    return dict(arm=row['arm'], position=row['position'], task_id=row['task_id'],
                target_sha256=row['target_sha256'], projection=projection, outcome=outcome,
                registered_outcome_unchanged=row['outcome_pass'], admission_allowed=False)


def main():
    parser = argparse.ArgumentParser()
    for name in ('root', 'model-dir', 'output'):
        parser.add_argument('--' + name, required=True)
    options = parser.parse_args()
    root = Path(options.root)
    source = root / 'source'
    freeze = json.loads((source / 'research_notes/analysis/orch_code_channel_20260915_attempt1/FREEZE.json').read_text())
    from gpu import astra_portable_actor_bundle as portable

    tokenizer = portable.source.native.load_local_tokenizer(options.model_dir)
    count = 0
    payloads = []
    joins = []
    for arm in policy.ARMS:
        before = json.loads((root / arm / 'PRECALL_PROOF.json').read_text())
        result = json.loads((root / arm / 'RESULT.json').read_text())
        assert result['status'] == 'COMPLETE' and result['completed_tasks'] == 64
        for proof in (before, result['final_proof']):
            assert proof['actual_native_base_sha256'] == policy.BASE
            assert proof['actual_mounted_sha256'] == policy.MOUNTED
        histories = {}
        for path in sorted((root / arm).glob('CALL_*.json')):
            row = json.loads(path.read_text())
            task = freeze['tasks'][row['position']]
            previous = histories.get(row['position']) if row['kind'] == 'NEW' else None
            messages, student = policy.prompt(task, arm, previous)
            assert row['call']['messages'] == messages and row['student_prefix'] == student
            tokens = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                                     return_dict=False)
            assert tokens == row['call']['input_token_ids']
            assert len(tokens) + row['call']['generation_ceiling'] <= 4096
            tail = row['call']['token_ids']
            terminal = bool(tail) and tail[-1] == tokenizer.eos_token_id
            assert terminal == row['call']['terminal']
            decoded = tokenizer.decode(tail[:-1] if terminal else tail, skip_special_tokens=False,
                                         clean_up_tokenization_spaces=False)
            assert decoded == row['target'] == row['call']['raw'] and policy.sha(decoded) == row['target_sha256']
            replay = policy.capture(task, arm, row['call'], previous)
            for field in ('feedback', 'outcome_pass', 'token_contract', 'generated_tokens', 'source_target_sha256'):
                actual = json.loads(json.dumps(replay[field])) if field == 'feedback' else replay[field]
                assert actual == row[field]
            assert row['semantic_status'] == 'UNREVIEWED' and not row['admitted']
            if row['kind'] == 'SOURCE':
                payloads.append(payload_audit(task, row))
            histories[row['position']] = row
            count += 1
            joins.append(dict(path=str(path.relative_to(root)), sha256=digest(path)))
    write(options.output, dict(status='PASS', verified_calls=count, model_calls=0, fits=0,
        actual_pre_post_base_and_mount=True, prompt_and_token_and_neutral_prefix_replay=True,
        raw_files=joins, payload_audit=payloads,
        warning='Payload audit is posthoc descriptive projection only. No changes to registered outcomes, targets, grammar, or admission. No reference tests changed.'))


if __name__ == '__main__':
    main()
