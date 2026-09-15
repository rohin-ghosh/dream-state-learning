"""Bounded CPU-only V3 math snapshots; no provider, generation or admission."""

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import tarfile
import time

from organism_v6 import orch_continual_batch as admission
from organism_v6 import orch_rich_hot_node2 as original
from organism_v6 import orch_rich_hot_node2_exhaustion_v3 as generation


SOURCE = Path('/localhome/local-rohing/orch_rich_hot_node2_exhaustion_v3_20260915_attempt1')
ORIGINAL = Path('/localhome/local-rohing/orch_rich_hot_node2_20260915_attempt1')
SOURCE_SHA = 'f71ab1fcad22792e70d79b732937bf9cc004f80cbcaec01be799f119dd4d7d13'
PREPARE_SHA = '0c7c9d351b0357bc48a492d26ac2301edda9c53f21ed0e3e356ab15dd92bfd57'
PREFIX = 'orch_continual_exhaustion_feed'


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def owned_output(path):
    path = Path(path)
    admission.require(path.name.startswith(PREFIX) and not path.exists(), 'fresh_owned_output_required')
    admission.require(path.parent.resolve() != SOURCE and SOURCE not in path.resolve().parents,
                      'never_write_generator_source')
    return path


def verify_source():
    admission.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only')
    admission.require(sha(SOURCE / 'PREPARE.json') == PREPARE_SHA, 'frozen_prepare_drift')
    prepared = read(SOURCE / 'PREPARE.json')
    admission.require(prepared['source_sha256'] == SOURCE_SHA == sha(SOURCE / 'source.tar'), 'source_archive_drift')
    from gpu.orch_math_rich_source import verify_archive
    admission.require(verify_archive(SOURCE / 'source.tar', SOURCE / 'source') == prepared['source_files'],
                      'source_files_drift')
    for module in (generation, original):
        relative = Path('organism_v6') / Path(module.__file__).name
        admission.require(sha(module.__file__) == sha(SOURCE / 'source' / relative), 'loaded_generation_policy_drift')
    admission.require(sha(admission.__file__) == '1c2349d27cb4ab7eacd4e9d62519aacf45579be764fd65b1bd030eaccdc038be',
                      'unchanged_encoder_policy_required')
    for name in ('TASKS.json', 'LIFETIME.json', 'PROTOCOL.md'):
        admission.require(sha(SOURCE / name) == prepared['files'][str(SOURCE / name)], 'source_input_drift')
    admission.require(prepared['identity']['state_sha256'] == original.INITIAL_STATE, 'original37ec_only')
    admission.require(sha(ORIGINAL / 'gsm8k_train.jsonl') == original.SOURCE_SHA, 'cached_train_source_drift')
    manifest_path = Path(prepared['bundle']) / 'MANIFEST.json'
    admission.require(sha(manifest_path) == '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469',
                      'portable_manifest_drift')
    manifest = read(manifest_path)
    admission.require(manifest['parent_state'] == original.INITIAL_STATE and
        all(sha(Path(prepared['model_dir']) / name) == digest for name, digest in manifest['tokenizer_files'].items()),
        'native_tokenizer_drift')
    return prepared


def register(output, exclusions_path):
    prepared = verify_source()
    output = owned_output(output)
    output.mkdir()
    registry = dict(schema='ORCH_CONTINUAL_EXHAUSTION_FEED_REGISTRY_V1', external_generation_required=True,
        exclusions_sha256=sha(exclusions_path), policy_sha256=sha(admission.__file__),
        adapter_sha256=sha(__file__), source_generation_policy_sha256=sha(generation.__file__),
        sources={str(SOURCE): dict(purpose=admission.PURPOSE, source_purpose='L1_EXTERNAL_GENERATION',
            parenting_experience=False, family='math', allowed_shards=list(range(1, 8)),
            generator_state_sha256=original.INITIAL_STATE, generator_base_sha256=prepared['identity']['base_sha256'],
            source_archive_sha256=SOURCE_SHA, source_prepare_sha256=PREPARE_SHA,
            protocol_sha256=sha(SOURCE / 'PROTOCOL.md'), source_tasks_sha256=sha(SOURCE / 'TASKS.json'),
            source_data_sha256=original.SOURCE_SHA, prompt_version=generation.VERSION,
            authority='Main 2026-09-15 06:00: bounded source sidecar only; new publisher segment separately allocated',
            instruction_regime='PER_ROW_EXHAUSTION_ONLY_OR_STEERED',
            checkpoint_derived_allowed=False, teacher_targets_allowed=False, L2_allowed=False)},
        generation_lifetime=read(SOURCE / 'LIFETIME.json'), provider_calls=0, gpu_reservations=0,
        provider_budget_allocated=False, publisher_segment_authorized=False,
        created_unix=time.time())
    write(output / 'SOURCE_REGISTRY.json', registry)
    return dict(native_registry_path=str(output / 'SOURCE_REGISTRY.json'),
                registry_sha256=sha(output / 'SOURCE_REGISTRY.json'), provider_calls=0, gpu_reservations=0)


def validate_call(call, intent, task, loaded, prepared, draft=None):
    shard = call['shard']
    admission.require(type(shard) is int and shard in range(1, 8), 'checkpoint_derived_or_wrong_shard')
    identity = prepared['identities'][str(shard)]
    admission.require(identity == prepared['identity'] == call['generator_identity'] == loaded['observed'] and
        identity['state_sha256'] == original.INITIAL_STATE, 'original37ec_identity_required')
    admission.require(call['generator_classification'] == 'ORIGINAL37EC_CONTROL' and
        call['source_checkpoint_commit_sha256'] is None and call['source_checkpoint_update'] is None,
        'checkpoint_or_L2_quarantine')
    admission.require('error' not in call and call['family'] == task['family'] == 'math', 'math_completed_only')
    admission.require(call['task_id'] == task['id'] and call['source_task_id'] == task['payload']['id'], 'source_task_binding')
    admission.require(call['stage'] in ('draft_0', 'final_0'), 'known_math_stage_only')
    admission.require(call['outcome']['correct'] is True and call['outcome']['admitted'] is False and
        call['trainingAllowed'] is False, 'original_oracle_unadmitted_required')
    admission.require(intent and all(call.get(key) == value for key, value in intent.items()), 'native_reservation_drift')
    admission.require(call['source_code_sha256'] == SOURCE_SHA and call['prompt_version'] == generation.VERSION,
                      'source_prompt_version_drift')
    admission.require(call['condition'] == loaded['condition'] == generation.CONDITIONS[shard // 2] and
        loaded['uuid'] == original.UUIDS[shard] and call['steering_degree'] == shard // 2, 'shard_condition_binding')
    prior = None
    if call['stage'] == 'final_0' and shard >= 4:
        admission.require(draft is not None and draft['task_id'] == call['task_id'] and
            draft['shard'] == shard and draft['stage'] == 'draft_0' and 'error' not in draft and
            draft['generator_identity'] == identity and draft['source_code_sha256'] == SOURCE_SHA,
            'actual_own_prior_required')
        prior = draft['response']['raw']
    else:
        admission.require(call['stage'] == ('final_0' if shard < 4 else 'draft_0'), 'stage_condition_binding')
    response = call['response']
    admission.require(call['messages'] == generation.messages(task, shard, prior) == response['messages'],
                      'exact_native_prompt_binding')
    prompt_wire = (json.dumps(call['messages'], sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    admission.require(hashlib.sha256(prompt_wire).hexdigest() == call['prompt_sha256'], 'prompt_hash_drift')
    admission.require(call['prompt_tokens'] == response['prompt_tokens'] and
        call['max_new_tokens'] == response['max_new_tokens'] == generation.effective_budget(call['prompt_tokens']) and
        call['context'] == response['context'] == generation.CONTEXT and
        call['target_max_new_tokens'] == generation.TARGET, 'native_budget_binding')
    normalized = deepcopy(call)
    normalized.update(task_id=task['payload']['id'], gold=task['payload']['gold'],
        stage='source' if prior is None else ('new_record' if shard // 2 == 2 else 'reconsider'),
        strategy=call['condition'], outcome=dict(call['outcome'], outcome_pass=True))
    normalized['messages'][1] = dict(role='user', content=task['payload']['question'])
    return normalized


def snapshot(output, exclusions_path, seen_path, registry_path):
    prepared = verify_source()
    registry = read(registry_path)
    entry = registry['sources'].get(str(SOURCE), {})
    admission.require(entry.get('purpose') == admission.PURPOSE and
        entry.get('source_purpose') == 'L1_EXTERNAL_GENERATION' and entry.get('parenting_experience') is False and
        entry.get('allowed_shards') == list(range(1, 8)) and entry.get('source_archive_sha256') == SOURCE_SHA and
        entry.get('source_prepare_sha256') == PREPARE_SHA and
        entry.get('protocol_sha256') == sha(SOURCE / 'PROTOCOL.md') and
        entry.get('generator_state_sha256') == original.INITIAL_STATE, 'registered_source_binding')
    admission.require(registry['exclusions_sha256'] == sha(exclusions_path) and
        registry['policy_sha256'] == sha(admission.__file__) and registry['adapter_sha256'] == sha(__file__) and
        registry['source_generation_policy_sha256'] == sha(generation.__file__), 'registry_policy_or_exclusion_drift')
    output = owned_output(output)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(prepared['model_dir'], local_files_only=True)
    document = read(SOURCE / 'TASKS.json')
    records = [json.loads(line) for line in (ORIGINAL / 'gsm8k_train.jsonl').read_text().splitlines()]
    exclusions_bytes, seen_bytes = Path(exclusions_path).read_bytes(), Path(seen_path).read_bytes()
    admission.require(hashlib.sha256(exclusions_bytes).hexdigest() == registry['exclusions_sha256'], 'exclusions_changed')
    exclusions, seen = json.loads(exclusions_bytes), set(json.loads(seen_bytes))
    captured = []
    for shard in range(1, 8):
        for path in sorted((SOURCE / f'shard{shard}').glob('B*.json')):
            if not re.fullmatch(r'B\d{3}-P\d{2}_(draft|final)_0\.json', path.name):
                continue
            data = path.read_bytes()
            call = json.loads(data)
            if call.get('family') == 'math':
                captured.append((path, data, call))
    admission.require(len(captured) <= 65536, 'bounded_source_scan')
    output.mkdir()
    raw = output / 'raw'
    raw.mkdir()
    inventory, selected, skipped, eligible = {}, [], Counter(), 0

    def preserve(path, data=None):
        relative = path.relative_to(SOURCE)
        data = path.read_bytes() if data is None else data
        destination = raw / relative
        digest = hashlib.sha256(data).hexdigest()
        if str(relative) in inventory:
            admission.require(inventory[str(relative)] == digest, 'captured_artifact_changed')
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as stream:
                stream.write(data)
            inventory[str(relative)] = digest
        return 'raw/' + str(relative), digest

    for path, data, call in sorted(captured, key=lambda item: (
            item[2]['stage'] != 'final_0', item[2]['finished_unix'], str(item[0]))):
        try:
            match = re.fullmatch(r'B(\d{3})-P(\d{2})', call['task_id'])
            admission.require(match is not None, 'task_cursor_shape')
            shard = call['shard']
            admission.require(path.parent.name == f'shard{shard}', 'path_shard_binding')
            task = generation.task_at(document, int(match[1]), int(match[2]), shard)
            record = records[int(task['payload']['id'].rsplit('-', 1)[1])]
            admission.require(record['question'].strip() == task['payload']['question'] and
                admission.math.number(record['answer'].rsplit('####', 1)[1]) == admission.math.number(task['payload']['gold']),
                'exact_cached_source_gold')
            intent_path = SOURCE / 'reservations' / f'{shard}_{call["task_id"]}_{call["stage"]}.json'
            intent = read(intent_path)
            loaded_path = SOURCE / f'shard{shard}/LOADED.json'
            loaded = read(loaded_path)
            draft_path = path.with_name(f'{call["task_id"]}_draft_0.json')
            draft = read(draft_path) if shard >= 4 and call['stage'] == 'final_0' else None
            if draft is not None:
                draft_intent = read(SOURCE / 'reservations' / f'{shard}_{call["task_id"]}_draft_0.json')
                admission.require(all(draft.get(key) == value for key, value in draft_intent.items()) and
                    draft['messages'] == draft['response']['messages'] == generation.messages(task, shard),
                    'own_prior_reservation_or_prompt_drift')
            normalized = validate_call(call, intent, task, loaded, prepared, draft)
            target_sha = admission.text_sha(call['response']['raw'])
            admission.require(target_sha not in seen, 'duplicate_target')
            provenance = dict(raw_call_path='raw/' + str(path.relative_to(SOURCE)),
                raw_call_sha256=hashlib.sha256(data).hexdigest(), source_native_path=str(path),
                intent_path='raw/' + str(intent_path.relative_to(SOURCE)), intent_sha256=sha(intent_path),
                loaded_path=f'raw/shard{shard}/LOADED.json', loaded_sha256=sha(loaded_path),
                source_archive_sha256=SOURCE_SHA, source_prepare_sha256=PREPARE_SHA,
                tasks_sha256=sha(SOURCE / 'TASKS.json'), source_data_sha256=original.SOURCE_SHA,
                source_registry_sha256=sha(registry_path), registered_source_purpose=admission.PURPOSE,
                source_purpose='L1_EXTERNAL_GENERATION', parenting_experience=False, no_parent_teacher_target=True,
                generation_family='math', physical_gpu=shard, gpu_uuid=loaded['uuid'],
                native_finished_unix=call['finished_unix'], original_native_stage=call['stage'],
                source_task_id=call['source_task_id'], source_capture_id=call['task_id'],
                generator_classification=call['generator_classification'], high_budget=call['max_new_tokens'],
                prompt_version=call['prompt_version'], native_prompt_sha256=call['prompt_sha256'],
                instruction_regime='EXHAUSTION_ONLY' if shard == 1 else 'STEERED', steering_degree=shard // 2,
                instruction_amount_tokens=sum(len(tokenizer.encode(message['content'], add_special_tokens=False))
                    for index, message in enumerate(call['messages']) if message['role'] == 'system' or
                    (index > 1 and message['role'] == 'user')),
                mechanical_branch_counts=call['outcome'].get('claimed_approach_count'),
                self_reported_branch_counts=None, semantic_branching_status='UNREVIEWED',
                serialization_adapter='V3_NATIVE_VALIDATED_TO_UNCHANGED_NEUTRAL_ENCODER_V1',
                host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest())
            row = admission.mechanical(normalized, task['payload'], loaded, dict(initial=prepared['identity']),
                                       tokenizer, exclusions, provenance)
            row['generation_messages'] = call['messages']
            row['original_semantic_status'] = call['outcome']['semantic_status']
            eligible += 1
            seen.add(target_sha)
            if len(selected) < admission.BATCH_SIZE:
                preserve(path, data)
                preserve(intent_path)
                preserve(loaded_path)
                if draft is not None:
                    preserve(draft_path)
                selected.append(row)
        except (ValueError, KeyError, IndexError, TypeError, FileNotFoundError) as error:
            skipped[str(error)] += 1
    for name, data in (('EXCLUSIONS.json', exclusions_bytes), ('SEEN_INPUT.json', seen_bytes),
                       ('SOURCE_REGISTRY.json', Path(registry_path).read_bytes())):
        with (output / name).open('xb') as stream:
            stream.write(data)
    write(output / 'CANDIDATES.json', selected)
    write(output / 'RAW_INVENTORY.json', inventory)
    checks = dict(status='PASS', source=str(SOURCE), source_archive_sha256=SOURCE_SHA,
        source_prepare_sha256=PREPARE_SHA, snapshot_unix=time.time(), captured_calls=len(captured),
        eligible_unique_after_seen=eligible, selected=len(selected),
        pending_eligible=eligible - len(selected), skipped=dict(skipped),
        candidates_sha256=sha(output / 'CANDIDATES.json'), inventory_sha256=sha(output / 'RAW_INVENTORY.json'),
        source_registry_sha256=sha(registry_path), exclusions_sha256=sha(output / 'EXCLUSIONS.json'),
        seen_sha256=sha(output / 'SEEN_INPUT.json'), all_selected_exact_encoder_pass=True,
        train_context=admission.TRAIN_CONTEXT, native_actor=prepared['identity'],
        first_native_capture_unix=min((item[2]['finished_unix'] for item in captured), default=None),
        last_native_capture_unix=max((item[2]['finished_unix'] for item in captured), default=None),
        captured_generated_tokens=sum(len(item[2].get('response', {}).get('token_ids', [])) for item in captured),
        native_calls=0, provider_calls=0, gpu_reservations=0, admitted_rows=0,
        semantic_status='UNREVIEWED', raw_stays_native=True, old_source_and_seen_unchanged=True)
    write(output / 'SOURCE_CHECKS.json', checks)
    with tarfile.open(str(output) + '.tar.gz', 'x:gz') as archive:
        for path in sorted(output.rglob('*')):
            if path.is_file():
                archive.add(path, arcname=str(path.relative_to(output)), recursive=False)
    return dict(checks, native_snapshot_path=str(output), source_checks_sha256=sha(output / 'SOURCE_CHECKS.json'),
                native_archive_path=str(output) + '.tar.gz', native_archive_sha256=sha(str(output) + '.tar.gz'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('register', 'snapshot'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--exclusions', type=Path, required=True)
    parser.add_argument('--seen', type=Path)
    parser.add_argument('--registry', type=Path)
    options = parser.parse_args()
    if options.action == 'register':
        result = register(options.output, options.exclusions)
    else:
        if not options.seen or not options.registry:
            parser.error('--seen and --registry required')
        result = snapshot(options.output, options.exclusions, options.seen, options.registry)
    print(json.dumps(result, sort_keys=True))
