"""Read-only, native-token inventory for genuine BASE TRAIN anchors; no fitting."""

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path

from organism_v6 import orch_r107_base_anchors as policy


MANIFEST_SHA = '2ad09dbe9673f95cbe92cd41e70d83635702b615fb7295b8b3f850e9ee674753'
SCHEMA = 'R107_BASE_ANCHOR_NATIVE_TOKEN_INVENTORY_V1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def checked(root, relative, expected):
    path = root / relative
    policy.require(path.resolve().is_relative_to(root.resolve()) and sha(path) == expected,
        'bound_native_file_required')
    return read(path)


def encode_anchor(task, row, call, prepared, tokenizer, context_limit):
    from gpu.astra_pchain2_native import EncodedRow

    policy.require(type(context_limit) is int and context_limit > 0, 'positive_context_limit')
    messages = policy.messages(task)
    response = call['response']
    policy.require(call['messages'] == response['messages'] == messages, 'original_prompt_required')
    policy.require(row['messages'] == messages + [dict(role='assistant', content=response['raw'])]
        and row['target'] == response['raw']
        and row['target_sha256'] == hashlib.sha256(response['raw'].encode()).hexdigest(), 'exact_native_target')
    policy.require(call['outcome'] == policy.outcome(task, response, tokenizer.eos_token_id)
        and call['outcome']['verified_anchor'] is True
        and row['machine_outcome'] == call['outcome']['machine'], 'verified_competence_required')
    prefix = tuple(tokenizer.apply_chat_template(messages, tokenize=True,
        add_generation_prompt=True, return_dict=False))
    policy.require(prepared['task_id'] == task['id'] and prepared['encoded_sha256'] == policy.digest(prefix)
        and prepared['prompt_tokens'] == response['prompt_tokens'] == len(prefix), 'frozen_native_prompt_ids')
    target = tuple(response['token_ids'])
    policy.require(1 < len(target) <= 512 and all(type(token) is int and token >= 0 for token in target)
        and target[-1] == tokenizer.eos_token_id and response['terminal'] is True
        and response['truncated'] is False, 'complete_native_target_ids')
    policy.require(not set(tokenizer.all_special_ids).intersection(target[:-1]), 'special_free_target')
    policy.require(tokenizer.decode(target[:-1], skip_special_tokens=False,
        clean_up_tokenization_spaces=False) == row['target'], 'native_token_text_roundtrip')
    policy.require(0 < len(prefix) + len(target) <= context_limit, 'no_context_truncation')
    return EncodedRow(prefix + target, (-100,) * len(prefix) + target, target)


def build_inventory(root, tokenizer, context_limit, *, expected_manifest_sha256=MANIFEST_SHA):
    root = Path(root)
    manifest = checked(root, 'ANCHOR_MANIFEST.json', expected_manifest_sha256)
    complete = read(root / 'readout/COMPLETE.json')
    policy.require(complete['status'] == 'COMPLETE' and complete['calls'] == 64
        and complete['manifest_sha256'] == expected_manifest_sha256, 'complete64_manifest_required')
    policy.require(manifest['status'] == 'VERIFIED_ANCHOR_MANIFEST_READY'
        and manifest['before_after_verified'] is True and manifest['base_sha256'] == policy.BASE_SHA
        and manifest['adapter'] is None and manifest['completed_calls'] == manifest['reserved_calls'] == 64,
        'verified_pure_base_manifest')
    for field in ('automatic_fit', 'trainingAllowed', 'fit_ready', 'teacher_targets', 'l2', 'held'):
        policy.require(manifest[field] is False, 'source_boundary_' + field)
    for stage in ('BEFORE', 'AFTER'):
        evidence = read(root / 'readout' / (stage + '.json'))
        policy.require(evidence['base_sha256'] == policy.BASE_SHA
            and evidence['frozen_base_verified'] is True and evidence['no_adapter_verified'] is True
            and evidence['parent_calls'] == evidence['training_updates'] == 0, 'frozen_base_' + stage)
    policy.require(read(root / 'readout/AFTER.json')['status'] == 'PASS', 'after_pass_required')
    plan = checked(root, 'PLAN.json', manifest['plan_sha256'])
    ready = read(root / 'READY.json')
    publication = read(root / 'PUBLICATION.json')
    policy.require(publication['ready_sha256'] == sha(root / 'READY.json')
        and publication['own_cpu_tests_passed'] is True and ready['status'] == 'PASS'
        and ready['plan_sha256'] == manifest['plan_sha256'], 'bound_ready_publication')
    suite = checked(root, 'TASKS_PRIVATE.json', ready['task_file_sha256'])
    checked(root, 'RESERVATIONS.json', ready['reservations_sha256'])
    policy.require(suite == policy.tasks() and policy.exclusions(suite) == plan['exclusions']
        and policy.digest(suite) == plan['suite_sha256'] == manifest['suite_sha256'] == ready['suite_sha256'],
        'exact_predetermined_train_suite')
    policy.require(plan['base_sha256'] == policy.BASE_SHA and plan['adapter'] is None
        and plan['parent_calls'] == plan['training_updates'] == 0 and plan['call_cap'] == 64
        and plan['max_new_tokens'] == 512, 'original_base_call_caps')
    policy.require(sha(policy.__file__) == plan['sources']['organism_v6/orch_r107_base_anchors.py'],
        'frozen_validator_source')
    policy.require(manifest['anchors_path'] == str(root / 'ANCHOR_ROWS.json')
        and manifest['runtime_prefix'] == str(root), 'exact_native_root')
    rows = checked(root, 'ANCHOR_ROWS.json', manifest['anchors_sha256'])
    policy.require(len(manifest['rows']) == 64 and len(ready['tokenization']) == 64, 'complete_task_denominators')
    calls = {}
    for position, task in enumerate(suite):
        summary = manifest['rows'][position]
        relative = 'readout/CALL_' + f'{position:03d}' + '.json'
        policy.require(summary['position'] == position and summary['task_id'] == task['id']
            and summary['family'] == task['family'] and summary['call_path'] == str(root / relative),
            'ordered_original_call_join')
        call = checked(root, relative, summary['call_sha256'])
        policy.require(call['position'] == position and call['task_id'] == task['id']
            and call['family'] == task['family'] and call['status'] == 'COMPLETE'
            and call['base_sha256'] == policy.BASE_SHA and call['adapter'] is None
            and call['max_new_tokens'] == 512
            and call['outcome']['verified_anchor'] is summary['verified_anchor'], 'original_base_call')
        calls[task['id']] = (task, call, summary, ready['tokenization'][position])
    expected_ids = {task_id for task_id, (_, _, summary, _) in calls.items() if summary['verified_anchor']}
    policy.require(len(rows) == len(expected_ids) == manifest['verified_anchors']
        and {row['task_id'] for row in rows} == expected_ids, 'all_verified_anchors_exactly_once')
    inventory = {family: [] for family in policy.FAMILIES}
    for row in rows:
        task, call, summary, prepared = calls[row['task_id']]
        actor = row['source_actor']
        policy.require(row['family'] == task['family'] and row['cohort'] == policy.COHORT
            and row['split'] == 'TRAIN' and row['admitted_as_anchor'] is True
            and row['runtime_prefix'] == str(root) and row['trainingAllowed'] is False
            and row['automatic_fit'] is False and row['fit_ready'] is False, 'ordinary_train_anchor_only')
        policy.require(actor['base_sha256'] == policy.BASE_SHA and actor['adapter'] is None
            and actor['policy_sha256'] == plan['sources']['organism_v6/orch_r107_base_anchors.py']
            and actor['generator_sha256'] == plan['sources']['gpu/orch_r107_base_anchors_run.py']
            and row['call_sha256'] == summary['call_sha256'] and row['call_path'] == summary['call_path']
            and row['task_content_sha256'] == task['content_sha256']
            and row['prompt_sha256'] == task['prompt_sha256'], 'exact_source_actor_join')
        encoded = encode_anchor(task, row, call, prepared, tokenizer, context_limit)
        inventory[task['family']].append(dict(task_id=task['id'], family=task['family'],
            source_condition='PURE_BASE', split='TRAIN', verified_competent=True,
            source_call_sha256=summary['call_sha256'], source_call_path=summary['call_path'],
            target_sha256=row['target_sha256'], encoded=encoded, automatic_fit=False,
            source_manifest_sha256=expected_manifest_sha256, source_base_sha256=policy.BASE_SHA))
    counts = {family: len(records) for family, records in inventory.items()}
    policy.require(all(counts[family] == manifest['families'][family]['verified_anchors']
        for family in policy.FAMILIES), 'family_counts_match')
    receipt = dict(schema=SCHEMA, status='ENCODED_INVENTORY_READY', runtime_prefix=str(root),
        source_manifest_sha256=expected_manifest_sha256, source_rows_sha256=manifest['anchors_sha256'],
        source_plan_sha256=manifest['plan_sha256'], suite_sha256=manifest['suite_sha256'],
        base_sha256=policy.BASE_SHA, adapter=None, source_condition='PURE_BASE', split='TRAIN',
        completed_calls=64, encoded_anchors=sum(counts.values()), families=counts,
        shortfalls={family: max(0, 4-count) for family, count in counts.items()},
        new_model_calls=0, parent_calls=0, training_updates=0, automatic_fit=False,
        source_training_allowed=False, source_fit_ready=False, native_target_ids_preserved=True,
        prompt_labels_masked=True, semantic_richness='NOT_CLAIMED', context_limit=context_limit,
        source_finished_unix=complete['finished_unix'],
        completion_categories=dict(Counter(summary['category'] for summary in manifest['rows'])),
        artifact_hashes={name: sha(root / name) for name in ('PLAN.json', 'READY.json', 'PUBLICATION.json',
            'readout/COMPLETE.json', 'readout/BEFORE.json', 'readout/AFTER.json', 'LAUNCH.json', 'ADMISSION.json')})
    return inventory, receipt


def load_inventory(root, tokenizer, context_limit=16384, *, expected_manifest_sha256=MANIFEST_SHA):
    return build_inventory(root, tokenizer, context_limit,
        expected_manifest_sha256=expected_manifest_sha256)[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--context-limit', type=int, default=16384)
    args = parser.parse_args()
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only_inventory')
    plan, ready = read(args.root / 'PLAN.json'), read(args.root / 'READY.json')
    for relative, expected in ready['model_metadata'].items():
        policy.require(sha(Path(plan['model_dir']) / relative) == expected, 'frozen_tokenizer_metadata')
    from gpu.astra_pchain2_native import load_local_tokenizer
    tokenizer = load_local_tokenizer(plan['model_dir'])
    inventory, receipt = build_inventory(args.root, tokenizer, args.context_limit)
    args.output.mkdir(parents=True, exist_ok=False)
    destination = args.output / 'ENCODED_INVENTORY.json'
    serialized = {family: [dict(row, encoded=asdict(row['encoded'])) for row in rows]
        for family, rows in inventory.items()}
    destination.write_text(json.dumps(serialized, sort_keys=True) + '\n')
    receipt.update(inventory_path=str(destination), inventory_sha256=sha(destination),
        helper_sha256=sha(__file__), loader_api='load_inventory(root, tokenizer, context_limit=16384)')
    (args.output / 'INVENTORY_RECEIPT.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
