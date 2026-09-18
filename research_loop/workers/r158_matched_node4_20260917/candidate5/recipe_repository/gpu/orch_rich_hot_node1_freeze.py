"""Prospectively partition only cached unheld TRAIN tasks into bounded batches."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tarfile

from gpu.orch_rich_hot_node1_run import sha, write
from organism_v6 import orch_rich_hot_node1 as policy


def freeze(root):
    source_root = Path('research_notes/analysis/orch_rich_hot_node2_20260915_attempt1')
    source = source_root / 'gsm8k_train.jsonl'
    provenance = json.loads((source_root / 'DATA_PROVENANCE.json').read_text())
    old_tasks = json.loads((source_root / 'TASKS.json').read_text())
    policy.require(sha(source) == policy.SOURCE_SHA, 'source_sha256')
    excluded_ids = set(old_tasks['excluded_ids']) | {task['id'] for task in old_tasks['tasks']}
    excluded_hashes = set(old_tasks['excluded_question_hashes']) | {task['question_sha256'] for task in old_tasks['tasks']}
    policy.require(len(old_tasks['excluded_ids']) == provenance['excluded_ids'] and
        len(old_tasks['excluded_question_hashes']) == provenance['excluded_question_hashes'], 'exclusion_count_join')
    verified_manifests = {}
    for path, expected in provenance['manifests'].items():
        policy.require(sha(path) == expected, 'inherited_exclusion_manifest_drift:' + path)
        verified_manifests[path] = expected
    tasks, seen = [], set(excluded_hashes)
    for index, line in enumerate(source.read_text().splitlines()):
        record = json.loads(line)
        question = record['question'].strip()
        identity = f'gsm8k-train-{index}'
        digest = policy.source.question_hash(question)
        family = policy.source.original.family(question)
        if identity in excluded_ids or digest in seen or family not in policy.source.original.MINING:
            continue
        seen.add(digest)
        tasks.append(dict(id=identity, question=question, question_sha256=digest, family=family,
            gold=str(policy.source.original.number(record['answer'].rsplit('####', 1)[1]))))
    tasks.sort(key=lambda task: policy.source.original.digest(['RICH_HOT_NODE1_V1', task['id']]))
    available = len(tasks)
    tasks = tasks[:4096]
    policy.require(len(tasks) >= 512, 'at_least_one_full_native_batch')
    batches = []
    for offset in range(0, len(tasks), 512):
        selected = tasks[offset:offset + 512]
        batches.append(dict(batch=len(batches), tasks=selected,
            sha256=policy.source.original.digest(selected), denominator_per_condition=len(selected)))
    root.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(source, root / 'gsm8k_train.jsonl')
    write(root / 'TASKS.json', dict(batches=batches, total_distinct_tasks=len(tasks),
        excluded_ids=sorted(excluded_ids), excluded_question_hashes=sorted(excluded_hashes),
        available_training_pool=available, planned_maximum_calls=6 * len(tasks),
        no_held_family_tasks=True, fits=0, parent_calls=0))
    write(root / 'PROVENANCE.json', dict(source_sha256=sha(source),
        inherited_provenance_sha256=sha(source_root / 'DATA_PROVENANCE.json'),
        excluded_node2_cohort_sha256=sha(source_root / 'TASKS.json'),
        exclusion_manifests=verified_manifests, known_exclusions_not_full_census=True,
        no_held_families=True, no_reference_reasoning_in_prompts=True,
        selection='node1 hash order over cached TRAIN MINING families excluding inherited known rosters and node2 cohort',
        frozen_before_native_calls_utc=datetime.now(timezone.utc).isoformat()))
    write(root / 'PROTOCOL.json', policy.protocol())
    lease_line = next(line for line in Path('research_loop/COORDINATION.md').read_text().splitlines()
        if '2026-09-15T01:03Z' in line and 'ACCESS HANDOFF complete' in line)
    write(root / 'LEASE.json', dict(verbatim_reference=lease_line,
        authority='Fable access handoff plus direct Main conservative cutoff instruction',
        date_only_lease_end='2026-09-19', conservative_lease_end_utc='2026-09-19T00:00:00+00:00',
        margin_seconds=policy.LEASE_MARGIN, no_extension_or_new_onboarding=True))
    inventory = {}
    for directory in ('gpu', 'organism_v6', 'research_loop'):
        for path in sorted(Path(directory).rglob('*')):
            if path.suffix not in ('.py', '.sh') or not path.is_file():
                continue
            destination = root / 'source' / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
            inventory[str(path)] = sha(destination)
    path = Path('tests/test_orch_rich_hot_node1.py')
    destination = root / 'source' / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, destination)
    inventory[str(path)] = sha(destination)
    write(root / 'SOURCE_SHA256.json', inventory)
    with tarfile.open(root / 'source.tar', 'w') as archive:
        for path in inventory:
            archive.add(root / 'source' / path, arcname='source/' + path)
    print(json.dumps(dict(tasks=len(tasks), batches=len(batches), planned_maximum_calls=6 * len(tasks),
        source_sha256=sha(root / 'SOURCE_SHA256.json'), tasks_sha256=sha(root / 'TASKS.json'))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    freeze(parser.parse_args().root)
