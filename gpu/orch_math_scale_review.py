"""Bounded author-side full-text readers using the existing read-only agent API."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import time

from gpu.orch_math_rich_screen import write
from gpu.orch_math_scale_reduce import load_raw, reduce
from organism_v6 import orch_math_rich as original
from organism_v6 import orch_math_scale as policy
from research_loop.agents import run_agent


def schema():
    string = dict(type='string')
    boolean = dict(type=['boolean', 'null'])
    review = dict(key=string, raw_call_sha256=string, target_sha256=string,
        student_prefix_sha256=string, status=dict(type='string', enum=['PASS', 'FAIL', 'UNRESOLVED']),
        reason=string, prefix_reason=string, full_text_read=dict(type='boolean'),
        evidence_spans=dict(type='array', items=string), **{axis: boolean for axis in policy.AXES})
    gold = dict(task_id=string, question_sha256=string,
        status=dict(type='string', enum=['VALID', 'INVALID', 'AMBIGUOUS']),
        independent_answer=string, reason=string)

    def obj(properties):
        return dict(type='object', properties=properties, required=list(properties), additionalProperties=False)

    return obj(dict(reviews=dict(type='array', items=obj(review)), gold=dict(type='array', items=obj(gold))))


def make_packets(root, directory):
    document, rows, binding = load_raw(root)
    by_task = {}
    for row in rows:
        by_task.setdefault(row['task_id'], []).append(row)
    prepared = []
    for start in range(0, 1024, 8):
        tasks = document['tasks'][start:start+8]
        if any(task['id'] not in by_task for task in tasks):
            continue
        if any(any(row['kind'] == 'rich' and row['outcome_pass'] for row in by_task[task['id']])
               and not any(row['kind'] == 'new_record' for row in by_task[task['id']]) for task in tasks):
            continue
        batch = directory / f'batch_{start//8:03d}'
        if batch.exists():
            continue
        batch.mkdir(parents=True)
        packet = []
        for task in tasks:
            contents = []
            for row in by_task[task['id']]:
                key = row['task_id'] + ':' + row['kind']
                contents.append(dict(key=key, target=row['target'], student_prefix=row['student_prefix'],
                    target_sha256=row['target_sha256'], student_prefix_sha256=original.digest(row['student_prefix']),
                    raw_call_sha256=binding['inventory'][key]['sha256']))
            packet.append(dict(task_id=task['id'], question=task['question'],
                question_sha256=task['question_sha256'], gold=task['gold'], responses=contents))
        write(batch / 'PACKET.json', packet)
        write(batch / 'SCHEMA.json', schema())
        write(batch / 'REQUEST_BINDING.json', dict(tasks_sha256=binding['task_sha256'],
            packet_sha256=hashlib.sha256((batch / 'PACKET.json').read_bytes()).hexdigest(),
            reviewer='AUTHOR_SIDE_DELEGATED_CODEX_READ_ONLY_NOT_INDEPENDENT_BLIND_AUDIT',
            review_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            instruction_sha256=hashlib.sha256(Path('research_notes/analysis/orch_math_scale_20260914_review_instructions.md').read_bytes()).hexdigest(),
            max_provider_attempts=1, timeout_seconds=600))
        prepared.append(batch)
    return prepared


def run_batch(batch, workspace, root):
    started = time.time()
    node = dict(provider='codex', allow_write=False, provider_attempts=1,
        prompt_file='research_notes/analysis/orch_math_scale_20260914_review_instructions.md',
        schema_file=str((batch / 'SCHEMA.json').relative_to(workspace)),
        context_files=[str((batch / 'PACKET.json').relative_to(workspace))],
        max_context_chars_per_file=250000, reasoning_effort='high')
    try:
        status, result = run_agent(node, workspace, batch / 'reader', timeout_sec=600)
        if status or result is None:
            raise RuntimeError('reader_exit:' + str(status))
        reviews = {row['key']: {key: value for key, value in row.items() if key != 'key'} for row in result['reviews']}
        gold = {row['task_id']: {key: value for key, value in row.items() if key != 'task_id'} for row in result['gold']}
        packet = json.loads((batch / 'PACKET.json').read_text())
        assert len(reviews) == len(result['reviews'])
        assert len(gold) == len(result['gold']) == len(packet)
        assert set(reviews) == {row['key'] for task in packet for row in task['responses']}
        assert set(gold) == {task['task_id'] for task in packet}
        reduce(root, reviews, gold)
        write(batch / 'ACCEPTED_REVIEW.json', dict(reviews=reviews, gold=gold))
        write(batch / 'STATUS.json', dict(status='STRUCTURALLY_VALID_FULLTEXT_REVIEW', started=started,
              finished=time.time(), rows=len(reviews), tasks=len(gold), independent_blind_audit=False))
    except BaseException as error:
        write(batch / 'FAILED_REVIEW.json', dict(status='REVIEW_FAILURE_NO_ADMISSION',
            error_type=type(error).__name__, error=str(error), started=started, finished=time.time()))
    return str(batch)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--directory', required=True)
    parser.add_argument('--maximum-batches', type=int, default=128)
    parser.add_argument('--workers', type=int, default=4, choices=range(1, 5))
    options = parser.parse_args()
    workspace = Path.cwd()
    root = Path(options.root).resolve()
    directory = Path(options.directory).resolve()
    assert directory.is_relative_to(workspace)
    assert 1 <= options.maximum_batches <= 128
    directory.mkdir(parents=True, exist_ok=True)
    make_packets(root, directory)
    pending = [path for path in sorted(directory.glob('batch_*'))
               if not (path / 'reader').exists() and not (path / 'FAILED_REVIEW.json').exists()]
    with ThreadPoolExecutor(max_workers=options.workers) as pool:
        jobs = [pool.submit(run_batch, batch, workspace, root) for batch in pending[:options.maximum_batches]]
        for job in as_completed(jobs):
            print(job.result(), flush=True)


if __name__ == '__main__':
    main()
