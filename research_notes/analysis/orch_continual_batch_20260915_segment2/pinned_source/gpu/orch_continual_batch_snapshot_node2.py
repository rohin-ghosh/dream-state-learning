"""Read-only registered node2 L1 math capture; original native rows stay intact."""

import argparse
import hashlib
import json
import os
import socket
from pathlib import Path
import tarfile
import time

from gpu.orch_continual_batch_snapshot import read, write, sha
from organism_v6 import orch_continual_batch as policy


SOURCE = Path('/localhome/local-rohing/orch_rich_hot_node2_20260915_attempt1')


def normalized_call(call):
    policy.require(call['stage'] in ('draft', 'final') and call['outcome']['correct'] is True,
                   'node2_observed_original_oracle_required')
    policy.require(call.get('trainingAllowed') is False and call['outcome']['admitted'] is False,
                   'native_raw_unadmitted_required')
    stage = 'source'
    if len(call['messages']) == 4:
        policy.require(call['stage'] == 'final' and call['condition'] in ('TWO_PASS', 'META_EVALUATE'),
                       'registered_own_second_pass_only')
        stage = 'new_record' if call['condition'] == 'TWO_PASS' else 'reconsider'
    else:
        policy.require(len(call['messages']) == 2, 'native_message_shape')
    return dict(call, stage=stage, strategy=call['condition'],
                outcome=dict(call['outcome'], outcome_pass=call['outcome']['correct']))


def snapshot(output, exclusions_path, seen_path, registry_path):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only')
    policy.require(output.name.startswith('orch_continual_batch_') and not output.exists(), 'fresh_owned_root')
    from gpu import astra_portable_actor_bundle as portable
    from gpu.orch_math_rich_source import verify_archive
    from organism_v6 import orch_rich_hot_node2 as original
    registry = read(registry_path)
    registered = registry['sources'].get(str(SOURCE))
    policy.require(registered and registered['purpose'] == policy.PURPOSE and
        registered.get('source_purpose') == 'L1_EXTERNAL_GENERATION' and registered.get('parenting_experience') is False,
        'quarantine_unregistered_parenting_or_L2')
    prepared = read(SOURCE / 'PREPARE.json')
    policy.require(prepared['source_sha256'] == registered['source_archive_sha256'] and
        sha(SOURCE / 'PROTOCOL.md') == registered['protocol_sha256'], 'registered_source_drift')
    policy.require(sha(SOURCE / 'source.tar') == prepared['source_sha256'] and
        verify_archive(SOURCE / 'source.tar', SOURCE / 'source') == prepared['source_files'], 'source_bytes_drift')
    policy.require(all(sha(SOURCE / name) == digest for name, digest in prepared['files'].items()), 'input_drift')
    policy.require(prepared['identity']['state_sha256'] == original.INITIAL_STATE, 'original37ec_only')
    manifest = portable.read_manifest(prepared['bundle'], expected_manifest_sha256='5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469')
    policy.require(manifest['parent_state'] == prepared['identity']['state_sha256'], 'portable_actor_binding')
    tokenizer = portable.source.native.load_local_tokenizer(prepared['model_dir'])
    output.mkdir()
    raw = output / 'raw'
    raw.mkdir()
    inventory = {}

    def copy(relative):
        relative = Path(relative)
        data = (SOURCE / relative).read_bytes()
        destination = raw / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        inventory[str(relative)] = hashlib.sha256(data).hexdigest()
        return json.loads(data) if relative.suffix == '.json' else None

    for name in ('PREPARE.json', 'TASKS.json', 'INITIAL.json', 'DATA_PROVENANCE.json', 'PROTOCOL.md',
                 'LIFETIME.json', 'READY.json', 'gsm8k_train.jsonl', 'source.tar'):
        copy(name)
    tasks = {task['id']: task for task in read(raw / 'TASKS.json')['tasks']}
    records = [json.loads(line) for line in (raw / 'gsm8k_train.jsonl').read_text().splitlines()]
    captured, loaded = [], {}
    for shard in range(8):
        folder = f'shard{shard}'
        if not (SOURCE / folder / 'LOADED.json').exists():
            continue
        loaded[shard] = copy(f'{folder}/LOADED.json')
        copy(f'LAUNCH_{shard}.json')
        for path in sorted((SOURCE / folder).glob('gsm8k-train-*.json')):
            relative = path.relative_to(SOURCE)
            captured.append((relative, copy(relative)))
    exclusions, seen = read(exclusions_path), set(read(seen_path))
    selected, skipped = [], []
    for relative, call in sorted(captured, key=lambda entry: (entry[1]['stage'] != 'final', entry[1]['finished_unix'], str(entry[0]))):
        try:
            policy.require('error' not in call, 'failed_native_call')
            task, shard = tasks[call['task_id']], call['shard']
            policy.require(loaded[shard]['uuid'] == original.UUIDS[shard] and
                loaded[shard]['condition'] == call['condition'] == original.CONDITIONS[shard // 2], 'exact_native_shard_binding')
            target_sha = policy.text_sha(call['response']['raw'])
            policy.require(target_sha not in seen, 'duplicate_target')
            record = records[int(task['id'].rsplit('-', 1)[1])]
            policy.require(record['question'].strip() == task['question'] and
                policy.math.number(record['answer'].rsplit('####', 1)[1]) == policy.math.number(task['gold']), 'exact_source_gold')
            reservation = Path(f'reservations/{shard}_{task["id"]}_{call["stage"]}.json')
            intent = copy(reservation)
            policy.require(all(call[key] == value for key, value in intent.items()), 'native_intent_binding')
            prior = None
            if len(call['messages']) == 4:
                draft = read(raw / f'shard{shard}/{task["id"]}_draft.json')
                policy.require(draft['task_id'] == task['id'] and draft['shard'] == shard, 'actual_own_draft_required')
                prior = draft['response']['raw']
            policy.require(call['messages'] == original.messages(task, call['condition'], prior) and
                call['response']['messages'] == call['messages'], 'native_message_protocol_binding')
            policy.require(call['response']['max_new_tokens'] == 8192 and call['response']['context'] == 16384,
                           'native_high_budget_required')
            provenance = dict(raw_call_path='raw/' + str(relative), raw_call_sha256=inventory[str(relative)],
                source_native_path=str(SOURCE / relative), intent_path='raw/' + str(reservation), intent_sha256=inventory[str(reservation)],
                loaded_path=f'raw/shard{shard}/LOADED.json', loaded_sha256=inventory[f'shard{shard}/LOADED.json'],
                source_archive_sha256=prepared['source_sha256'], source_prepare_sha256=inventory['PREPARE.json'],
                tasks_sha256=inventory['TASKS.json'], source_data_sha256=inventory['gsm8k_train.jsonl'],
                gpu_uuid=loaded[shard]['uuid'], physical_gpu=shard, native_finished_unix=call['finished_unix'],
                host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),
                high_budget=8192, generation_family='math', registered_source_purpose=policy.PURPOSE,
                source_registry_sha256=sha(registry_path), source_purpose='L1_EXTERNAL_GENERATION',
                parenting_experience=False, no_parent_teacher_target=True, original_native_stage=call['stage'],
                serialization_adapter='NODE2_MATH_NATIVE_TO_NEUTRAL_V1_ORIGINAL_RAW_PRESERVED')
            row = policy.mechanical(normalized_call(call), task, loaded[shard], dict(initial=prepared['identity']),
                                    tokenizer, exclusions, provenance)
            selected.append(row)
            seen.add(target_sha)
            if len(selected) == 64:
                break
        except (ValueError, KeyError, IndexError, FileNotFoundError) as error:
            skipped.append(dict(raw_call_path=str(relative), raw_call_sha256=inventory[str(relative)], reason=str(error)))
    write(output / 'CANDIDATES.json', selected)
    write(output / 'SKIPPED.json', skipped)
    write(output / 'RAW_INVENTORY.json', inventory)
    write(output / 'SOURCE_CHECKS.json', dict(status='PASS', source=str(SOURCE), native_calls=0, gpu_reservations=0,
        captured_calls=len(captured), selected=len(selected), skipped=len(skipped), source_archive_sha256=prepared['source_sha256'],
        candidates_sha256=sha(output / 'CANDIDATES.json'), exclusions_sha256=sha(exclusions_path),
        source_registry_sha256=sha(registry_path), seen_sha256=sha(seen_path), snapshot_unix=time.time(),
        all_selected_exact_encoder_pass=True, tokenizer_files=manifest['tokenizer_files'],
        native_actor=prepared['identity'], train_context=2048, source_started_unix=read(raw / 'LIFETIME.json')['started_unix'],
        captured_generated_tokens=sum(len(call.get('response', {}).get('token_ids', [])) for _, call in captured),
        first_native_capture_unix=min((call['finished_unix'] for _, call in captured), default=None),
        last_native_capture_unix=max((call['finished_unix'] for _, call in captured), default=None),
        captured_unique_targets=len({policy.text_sha(call.get('response', {}).get('raw', '')) for _, call in captured}),
        selected_first_native_capture_unix=min((row['provenance']['native_finished_unix'] for row in selected), default=None),
        selected_last_native_capture_unix=max((row['provenance']['native_finished_unix'] for row in selected), default=None)))
    with tarfile.open(str(output) + '.tar.gz', 'w:gz') as archive:
        for path in sorted(output.rglob('*')):
            if path.is_file():
                archive.add(path, arcname=str(path.relative_to(output)), recursive=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('output', 'exclusions', 'seen', 'registry'):
        parser.add_argument('--' + name, type=Path, required=True)
    options = parser.parse_args()
    snapshot(options.output, options.exclusions, options.seen, options.registry)
