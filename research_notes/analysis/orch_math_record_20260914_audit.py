"""CPU-only terminal provenance, pairing, diversity and token accounting."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics

from gpu.orch_math_rich_screen import write
from organism_v6 import orch_math_record as policy
from organism_v6 import orch_math_rich as original


ROOT = Path('gpu_artifacts_local/orch_math_record_20260914_attempt1/terminal')
OUTPUT = Path('research_notes/analysis/orch_math_record_20260914_attempt1')


def read(path):
    return json.loads(Path(path).read_text())


def distribution(values):
    return dict(count=len(values), minimum=min(values), maximum=max(values),
                mean=statistics.mean(values), median=statistics.median(values), total=sum(values),
                exact_sorted=sorted(values))


def main():
    document = read(ROOT / 'TASKS.json')
    tasks = {task['id']: task for task in document['tasks']}
    rows = read(OUTPUT / 'ROWS.json')
    lookup = {(row['task_id'], row['kind']): row for row in rows}
    assert len(rows) == len(lookup) == 190
    for row in rows:
        previous = None if row['kind'] == 'rich' else lookup[(row['task_id'], 'rich')]['target']
        messages, student = policy.prompt(tasks[row['task_id']], row['kind'], previous)
        assert row['call']['messages'] == messages and row['student_prefix'] == student
        assert hashlib.sha256(row['target'].encode()).hexdigest() == row['target_sha256']
        assert row['review']['target_sha256'] == row['target_sha256']
        assert all(span in row['target'] for span in row['review']['evidence_spans'])
        assert len(row['call']['token_ids']) <= 512 and row['call']['prompt_tokens'] <= 2048
        if row['admitted']:
            assert row['outcome_pass'] and row['token_contract_pass']
            assert all(row['review'][axis] is True for axis in policy.AXES)
    admitted = [row for row in rows if row['admitted']]
    assert len({row['target_sha256'] for row in admitted}) == len(admitted)
    original_tasks = read('gpu_artifacts_local/orch_math_rich_20260914_attempt1/TASKS.json')['tasks']
    assert not (set(tasks) & {task['id'] for task in original_tasks})
    assert not ({task['question_sha256'] for task in tasks.values()} &
                {task['question_sha256'] for task in original_tasks})
    states, guards = [], []
    for shard in range(4):
        actor = read(ROOT / f'shard{shard}/ACTOR_READY.json')
        result = read(ROOT / f'shard{shard}/RESULT.json')
        assert actor['adapter_state'] == result['adapter_state'] == '37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0'
        assert result['status'] == 'COMPLETE' and result['fits'] == result['updates'] == 0
        assert result['trainingAllowed'] is False and result['base_verification']['verified']
        directory = ROOT / f'shard{shard}_launch'
        started = datetime.fromisoformat((directory / 'started_utc.txt').read_text().strip().replace('Z', '+00:00'))
        finished = datetime.fromisoformat((directory / 'finished_utc.txt').read_text().strip().replace('Z', '+00:00'))
        assert finished.timestamp() <= int((directory / 'deadline_epoch.txt').read_text())
        assert (directory / 'exit_code.txt').read_text().strip() == '0'
        assert read(ROOT / f'RELEASE_GPU{shard+4}.json')['clear']
        guards.append((finished-started).total_seconds())
        states.append(dict(shard=shard, native_pid=result['pid'], ready_unix=actor['ready_unix'],
                           finished_unix=result['finished_unix'], guard_seconds=guards[-1]))
    stats = dict(reviewed=190, admitted_rows=len(admitted), distinct_admitted_tasks=len({row['task_id'] for row in admitted}),
                 distinct_admitted_target_hashes=len({row['target_sha256'] for row in admitted}),
                 conditions={}, family_counts=dict(Counter(row['family'] for row in admitted)),
                 guardian_gpu_seconds=sum(guards), guardian_gpu_hours=sum(guards)/3600,
                 native_states=states, training=False,
                 boolean_feedback_echoes=[dict(task_id=row['task_id'], kind=row['kind'], admitted=row['admitted'])
                     for row in rows if 'checker' in row['target'].lower()],
                 neutral_prefix_replay_passed=190, guidance_reference_reasoning_exposure=False)
    for kind in ('rich', 'old_record', 'new_record'):
        group = [row for row in rows if row['kind'] == kind]
        stats['conditions'][kind] = dict(generated=distribution([row['generated_tokens'] for row in group]),
            prompt=distribution([row['call']['prompt_tokens'] for row in group]),
            admitted=distribution([row['generated_tokens'] for row in group if row['admitted']]),
            under150=sum(row['generated_tokens'] < 150 for row in group),
            over400=sum(row['generated_tokens'] > 400 for row in group),
            truncated=sum(row['call']['truncated'] for row in group),
            failed_token_rows=[dict(task_id=row['task_id'], tokens=row['generated_tokens'])
                              for row in group if not row['token_contract_pass']])
    write(OUTPUT / 'DISTRIBUTION.json', stats)
    print(json.dumps({key: value for key, value in stats.items() if key not in ('conditions', 'native_states')}, indent=2))


if __name__ == '__main__':
    main()
