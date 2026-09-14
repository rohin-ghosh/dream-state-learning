"""CPU-only fresh cohort and source provenance; reads original IDs only."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from gpu import astra_portable_actor_bundle as portable
from organism_v6 import orch_math_replication as policy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--original-tasks', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    if policy.sha256(options.dataset) != policy.DATA_SHA256:
        raise ValueError('public_dataset_bytes_changed')
    original = json.loads(options.original_tasks.read_text())
    original_ids = [task['id'] for task in original['tasks']]
    del original
    records = [json.loads(line) for line in options.dataset.read_text().splitlines()]
    cohort = policy.build_cohort(records, original_ids)
    options.output.mkdir(parents=True, exist_ok=False)
    policy.write(options.output / 'TASKS.json', cohort)
    contract = portable.contract()
    root = Path(__file__).resolve().parents[1]
    imported = set()
    for module in tuple(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename:
            path = Path(filename).resolve()
            if path.is_file() and path.is_relative_to(root):
                imported.add(path.relative_to(root).as_posix())
    imported.update(('organism_v6/pcfl_vertical_train.py',
                     'gpu/astra_goal_breadth_collection_guard.sh', 'gpu/astra_goal_pair_collection_guard.sh',
                     'gpu/astra_event_two_hop_memory_guard.sh'))
    missing = [name for name in imported if not (root / name).is_file()]
    if missing:
        raise ValueError('missing_helper_paths:' + repr(missing))
    policy.write(options.output / 'CPU_PROVENANCE.json', dict(
        created_utc=datetime.now(timezone.utc).isoformat(), public_dataset_sha256=policy.DATA_SHA256,
        original_tasks_sha256=policy.sha256(options.original_tasks),
        original_access='ONLY_TASK_IDS_EXTRACTED_NO_RESPONSES',
        cohort_sha256=policy.sha256(options.output / 'TASKS.json'),
        portable_source_contract=contract, portable_manifest_sha256=policy.MANIFEST_SHA256,
        imported_sources={name: policy.sha256(root / name) for name in sorted(imported)},
        model_calls=0, prior_outcomes_read=False, native_verified=False))
    print(json.dumps(dict(status='COHORT_FROZEN_CPU_ONLY', denominator=32,
                         tasks_sha256=policy.sha256(options.output / 'TASKS.json'))))


if __name__ == '__main__':
    main()
