"""CPU-only immutable source snapshots and exact encoding for live A100 math."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile
import time

from organism_v6 import orch_continual_batch as policy


SOURCE = Path('/localhome/local-rohing/orch_rich_hot_a100_20260915_attempt1')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def snapshot(output, exclusions_path, seen_path, registry_path):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only_no_gpu_reservation')
    policy.require(output.name.startswith('orch_continual_batch_') and not output.exists(), 'fresh_owned_snapshot_root')
    from gpu import astra_portable_actor_bundle as portable
    from gpu.orch_math_rich_source import verify_archive

    registry = read(registry_path)
    registration = registry['sources'].get(str(SOURCE))
    policy.require(registration and registration['purpose'] == policy.PURPOSE, 'quarantine_unregistered_or_parenting_root')
    if registry.get('external_generation_required'):
        policy.require(registration.get('source_purpose') == 'L1_EXTERNAL_GENERATION' and
                       registration.get('parenting_experience') is False, 'quarantine_parenting_or_unknown_purpose')
    prepared = read(SOURCE / 'PREPARE.json')
    policy.require(prepared['source_sha256'] == registration['source_archive_sha256'] and
                   sha(SOURCE / 'PROTOCOL.md') == registration['protocol_sha256'], 'registered_source_purpose_binding_drift')
    policy.require(sha(SOURCE / 'source.tar') == prepared['source_sha256'], 'generator_source_archive_drift')
    policy.require(verify_archive(SOURCE / 'source.tar', SOURCE / 'source') == prepared['source_files'], 'generator_source_bytes_drift')
    policy.require(all(sha(SOURCE / name) == digest for name, digest in prepared['files'].items()), 'generator_input_drift')
    manifest = portable.read_manifest(prepared['bundle'], expected_manifest_sha256='5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469')
    policy.require(manifest['parent_state'] == prepared['initial']['state_sha256'], 'original_actor_required')
    tokenizer = portable.source.native.load_local_tokenizer(prepared['model_dir'])
    output.mkdir()
    raw = output / 'raw'
    raw.mkdir()
    inventory = {}

    def copy(relative):
        source = SOURCE / relative
        data = source.read_bytes()
        policy.require(hashlib.sha256(data).hexdigest() == sha(source), 'source_snapshot_race')
        destination = raw / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(data)
        inventory[str(relative)] = hashlib.sha256(data).hexdigest()
        return read(destination) if relative.suffix == '.json' else None

    for name in ('PREPARE.json', 'READY.json', 'TASKS.json', 'DATA_PROVENANCE.json', 'SOURCE_INVENTORY.json',
                 'source.tar', 'gsm8k_train.jsonl', 'PROTOCOL.md', 'DIRECTIVE.txt', 'LIFETIME.json'):
        copy(Path(name))
    loaded = {}
    captured = []
    for index in (2, 3, 4, 5, 6, 7):
        folder = Path(f'gpu{index}')
        if not (SOURCE / folder / 'LOADED.json').exists():
            continue
        loaded[index] = copy(folder / 'LOADED.json')
        copy(Path(f'LAUNCH_{index}.json'))
        for path in sorted((SOURCE / folder).glob('CALL_*.json')):
            relative = path.relative_to(SOURCE)
            call = copy(relative)
            intent = relative.with_name(relative.name.replace('CALL_', 'INTENT_'))
            copy(intent)
            captured.append((relative, index, call))
    exclusions = read(exclusions_path)
    seen = set(read(seen_path))
    tasks = {task['id']: task for task in read(raw / 'TASKS.json')['tasks']}
    records = [json.loads(line) for line in (raw / 'gsm8k_train.jsonl').read_text().splitlines()]
    selected, skipped = [], []
    order = {'new_record': 0, 'source': 1, 'reconsider': 2}
    for relative, index, call in sorted(captured, key=lambda entry: (order.get(entry[2].get('stage'), 99),
                                        entry[2].get('finished_unix', 0), str(entry[0]))):
        try:
            task = tasks[call['task_id']]
            record = records[int(task['id'].rsplit('-', 1)[1])]
            policy.require(record['question'].strip() == task['question'] and
                           policy.math.number(record['answer'].rsplit('####', 1)[1]) == policy.math.number(task['gold']), 'exact_source_question_gold')
            target_sha = policy.text_sha(call.get('response', {}).get('raw', ''))
            policy.require(target_sha not in seen, 'duplicate_target')
            intent_path = relative.with_name(relative.name.replace('CALL_', 'INTENT_'))
            intent = read(raw / intent_path)
            policy.require(all(call[key] == intent[key] for key in intent), 'intent_response_binding_drift')
            if call['stage'] != 'source':
                number = int(relative.stem.split('_')[1])
                previous = read(raw / relative.with_name(f'CALL_{number - 1:04d}.json'))
                policy.require(previous['task_id'] == task['id'] and previous['stage'] == 'source' and
                    previous['response']['raw'] == call['messages'][2]['content'], 'actual_prior_native_response_required')
            provenance = dict(raw_call_path=str(Path('raw') / relative), raw_call_sha256=inventory[str(relative)],
                source_native_path=str(SOURCE / relative), intent_path=str(Path('raw') / intent_path),
                intent_sha256=inventory[str(intent_path)], loaded_path=f'raw/gpu{index}/LOADED.json',
                loaded_sha256=inventory[f'gpu{index}/LOADED.json'], source_archive_sha256=prepared['source_sha256'],
                tasks_sha256=inventory['TASKS.json'], source_data_sha256=inventory['gsm8k_train.jsonl'],
                source_prepare_sha256=inventory['PREPARE.json'], host_sha256=prepared['host_sha256'],
                physical_gpu=index, gpu_uuid=loaded[index]['uuid'], native_finished_unix=call['finished_unix'],
                no_parent_teacher_target=True, generation_family='math', high_budget=8192,
                source_purpose=registration.get('source_purpose'), parenting_experience=registration.get('parenting_experience'),
                registered_source_purpose=registration['purpose'], source_registry_sha256=sha(registry_path))
            row = policy.mechanical(call, task, loaded[index], prepared, tokenizer, exclusions, provenance)
            selected.append(row)
            seen.add(target_sha)
            if len(selected) == policy.BATCH_SIZE:
                break
        except (ValueError, KeyError, IndexError, FileNotFoundError) as error:
            skipped.append(dict(raw_call_path=str(relative), raw_call_sha256=inventory[str(relative)], reason=str(error)))
    write(output / 'CANDIDATES.json', selected)
    write(output / 'SKIPPED.json', skipped)
    write(output / 'RAW_INVENTORY.json', inventory)
    write(output / 'SOURCE_CHECKS.json', dict(status='PASS', source=str(SOURCE), native_calls=0, gpu_reservations=0,
        captured_calls=len(captured), selected=len(selected), skipped=len(skipped), source_archive_sha256=prepared['source_sha256'],
        inventory_sha256=sha(output / 'RAW_INVENTORY.json'), candidates_sha256=sha(output / 'CANDIDATES.json'),
        exclusions_sha256=sha(exclusions_path), seen_sha256=sha(seen_path), tokenizer_files=manifest['tokenizer_files'],
        snapshot_unix=time.time(), all_selected_exact_encoder_pass=True, native_actor=prepared['initial'], train_context=policy.TRAIN_CONTEXT,
        source_registry_sha256=sha(registry_path), source_started_unix=read(raw / 'LIFETIME.json')['started_unix'],
        captured_generated_tokens=sum(len(call.get('response', {}).get('token_ids', [])) for _, _, call in captured),
        first_native_capture_unix=min((call['finished_unix'] for _, _, call in captured), default=None),
        last_native_capture_unix=max((call['finished_unix'] for _, _, call in captured), default=None),
        captured_unique_targets=len({policy.text_sha(call.get('response', {}).get('raw', '')) for _, _, call in captured}),
        selected_first_native_capture_unix=min((row['provenance']['native_finished_unix'] for row in selected), default=None),
        selected_last_native_capture_unix=max((row['provenance']['native_finished_unix'] for row in selected), default=None)))
    with tarfile.open(str(output) + '.tar.gz', 'x:gz') as archive:
        for path in sorted(output.rglob('*')):
            if path.is_file():
                archive.add(path, arcname=str(path.relative_to(output)), recursive=False)
    print(json.dumps(dict(selected=len(selected), captured=len(captured), archive_sha256=sha(str(output) + '.tar.gz'))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--exclusions', type=Path, required=True)
    parser.add_argument('--seen', type=Path, required=True)
    parser.add_argument('--registry', type=Path, required=True)
    options = parser.parse_args()
    snapshot(options.output, options.exclusions, options.seen, options.registry)
