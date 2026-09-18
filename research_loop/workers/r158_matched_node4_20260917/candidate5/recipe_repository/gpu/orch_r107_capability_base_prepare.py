"""Prepare the separately allocated, genuine BASE synthetic32 diagnostic."""

import argparse
import json
import os
from pathlib import Path
import time

from gpu import orch_r107_capability_base as runner
from gpu import orch_rich_intensity_guard as ownership
from gpu import astra_portable_actor_bundle as portable
from gpu.orch_l2_rich_math_bootstrap import BUNDLE_SHA


def prepare(root):
    runner.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only')
    root = Path(root)
    runner.require(not (root / 'PLAN.json').exists(), 'fresh_plan_required')
    verified = portable.verify_base_files(ownership.existing.BUNDLE,
        ownership.existing.MODEL, expected_manifest_sha256=BUNDLE_SHA)
    runner.require(verified['expected_base_sha256'] == runner.BASE_SHA, 'base_identity')
    source = Path(__file__).resolve().parents[1]
    started = time.time()
    plan = dict(schema=runner.SCHEMA, base_sha256=runner.BASE_SHA, adapter=None,
        training_updates=0, parent_calls=0, parent_access=False, train_ingestion=False,
        max_new_tokens=512, task_count=32, call_cap=32, conditions=['PUREBASE'],
        native_deadline_unix=started + 1770, hard_deadline_unix=started + 1800,
        lease_end_unix=1789776000, physical_index=3, device_minor=3,
        gpu_uuid=ownership.DEVICES[3], model_dir=str(ownership.existing.MODEL),
        suite_sha256=runner.SUITE_SHA,
        sources={str(path.relative_to(source)): runner.sha(path)
                 for folder in ('gpu', 'organism_v6', 'tests')
                 for path in sorted((source / folder).rglob('*.py'))})
    runner.validate_plan(plan, source, started)
    runner.storage.atomic_json(root / 'PLAN.json', plan)
    return runner.prepare(root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    options = parser.parse_args()
    result = prepare(options.root)
    print(json.dumps({key: value for key, value in result.items() if key != 'tokenization'}))
