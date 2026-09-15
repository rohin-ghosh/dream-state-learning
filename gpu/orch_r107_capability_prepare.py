"""CPU provenance and tokenization for the separately allocated R107 diagnostic."""

import argparse
import os
from pathlib import Path
import time

from gpu import orch_r107_capability_run as run
from gpu import orch_rich_intensity_guard as ownership
from organism_v6 import orch_r107_capability as policy


def prepare(root):
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    assert not (root / 'PLAN.json').exists()
    source = Path(__file__).resolve().parents[1]
    checkpoint = run.read(root / 'checkpoint/COMPLETE.json')
    assert checkpoint['status'] == 'COMPLETE' and checkpoint['updates'] == 6208
    adapter = dict(checkpoint['output_adapter'], path=str(root / 'checkpoint/adapter'))
    run.bridge.AdapterIdentity.from_document(adapter).verify()
    assert adapter['state_sha256'] == 'a970d311de6a3a77881f95fa1b042069d708c6bf814306980f8fe36467c8e792'
    bundle = ownership.existing.BUNDLE
    model_dir = ownership.existing.MODEL
    from gpu import astra_portable_actor_bundle as portable
    from gpu.orch_l2_rich_math_bootstrap import BUNDLE_SHA

    base = portable.verify_base_files(bundle, model_dir, expected_manifest_sha256=BUNDLE_SHA)
    assert base['expected_base_sha256'] == run.BASE_SHA
    tokenizer = run.native.source.native.load_local_tokenizer(model_dir)
    tasks = policy.tasks()
    lengths = [len(tokenizer.apply_chat_template(policy.messages(task), tokenize=True,
        add_generation_prompt=True, return_dict=False)) for task in tasks]
    assert len(tasks) == 32 and all(0 < length <= 4096 for length in lengths)
    started = time.time()
    plan = dict(schema='R107_CAPABILITY_PAIRED_V1', base_sha256=run.BASE_SHA,
        training_updates=0, parent_calls=0, parent_access=False, train_ingestion=False,
        max_new_tokens=512, task_count=32, call_cap=64,
        native_deadline_unix=started + 2670, hard_deadline_unix=started + 2700,
        lease_end_unix=1789776000, conditions=['LORA_ON', 'LORA_OFF'],
        sources={str(path.relative_to(source)): run.sha(path)
                 for folder in ('gpu', 'organism_v6')
                 for path in sorted((source / folder).rglob('*.py'))},
        suite_sha256=policy.digest(tasks), gpu_uuid='GPU-e1277146-04f2-c38f-d1ae-1a98132f907e',
        physical_index=3, device_minor=3, adapter=adapter, model_dir=str(model_dir))
    run.validate_plan(plan, source, started)
    run.storage.atomic_json(root / 'PLAN.json', plan)
    run.storage.atomic_json(root / 'SUITE_SEALED.json', dict(tasks=tasks, parent_access=False, train_ingestion=False))
    ready = dict(status='PASS', plan_sha256=run.sha(root / 'PLAN.json'),
        suite_sha256=plan['suite_sha256'], checkpoint_receipt_sha256=run.sha(root / 'checkpoint/COMPLETE.json'),
        source_files=len(plan['sources']), encoded_prompts=len(lengths),
        max_prompt_tokens=max(lengths), parent_calls=0, native_calls=0,
        base_sha256=run.BASE_SHA, prepared_unix=started)
    run.storage.atomic_json(root / 'READY.json', ready)
    return ready


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    import json
    print(json.dumps(prepare(parser.parse_args().root), sort_keys=True))
