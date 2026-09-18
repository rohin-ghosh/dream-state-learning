"""Separately pinned segment1 export and native CPU replay; no model calls."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import sys
import tarfile

from gpu import orch_combined_l1_native_feed as common


ROOT = Path('/localhome/local-rohing/orch_continual_exhaustion_publish_20260915_segment1')
REGISTRY_SHA = '9c290dddda5c4958f3dde8d1b0c09289dcf410a3b3abafdb78d57e84560a6431'
SOURCE_REGISTRY_SHA = 'd3441e8f2edd9e9eab653f6b6d34554a76bccec9e2c2134805050e0ca0445ec6'
ADAPTER_SHA = '14afaf648ddc594f6b4cb491bd89a62f8bcefa46f0d042c6b948b9613c1abf38'
GENERATION_SHA = 'da0fcbebecefcc53ca79833edad1717cc616d0d4cba9b6e6f2e28f17cda77a82'
SOURCE = '/localhome/local-rohing/orch_rich_hot_node2_exhaustion_v3_20260915_attempt1'
INITIAL = '37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0'
BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
BATCH_PATTERN = r'orch_continual_exhaustion_segment1_\d{3}'
read, sha = common.read, common.sha


def unpack(blob, expected):
    raw = base64.b64decode(blob, validate=True)
    assert hashlib.sha256(raw).hexdigest() == expected, 'source_blob_hash'
    return json.loads(raw)


def registries(proof):
    publisher = unpack(proof['publisher_registry'], REGISTRY_SHA)
    registry = unpack(proof['source_registry'], SOURCE_REGISTRY_SHA)
    assert publisher['source_registry_sha256'] == SOURCE_REGISTRY_SHA
    assert publisher['batching_rule'] == 'MIXED_STEERING_SAME_37EC'
    assert publisher['causal_prompt_comparison'] is False
    assert publisher['BASE_stream_registered'] is False
    assert all(publisher[key] is True for key in ('no_L2', 'no_checkpoint', 'no_teacher'))
    assert registry['adapter_sha256'] == ADAPTER_SHA
    assert registry['source_generation_policy_sha256'] == GENERATION_SHA
    assert set(registry['sources']) == {SOURCE}
    entry = registry['sources'][SOURCE]
    common.validate_registry_source(entry)
    assert entry['allowed_shards'] == list(range(1, 8))
    assert entry['generator_state_sha256'] == INITIAL and entry['generator_base_sha256'] == BASE
    assert entry['source_purpose'] == 'L1_EXTERNAL_GENERATION'
    assert all(entry[key] is False for key in ('parenting_experience', 'checkpoint_derived_allowed',
                                               'teacher_targets_allowed', 'L2_allowed'))
    return entry


def discover(root=ROOT):
    assert sha(root / 'PUBLISHER_REGISTRY.json') == REGISTRY_SHA
    assert sha(root / 'SOURCE_REGISTRY.json') == SOURCE_REGISTRY_SHA
    result = []
    for path in sorted(root.glob('orch_continual_exhaustion_feed_batch_*/MANIFEST.json')):
        match = re.fullmatch(r'orch_continual_exhaustion_feed_batch_(\d{3})', path.parent.name)
        if not match or not 0 <= int(match[1]) < 64:
            continue
        manifest = read(path)
        if manifest.get('batch_author_accepted') is not True:
            continue
        assert manifest['batch_id'] == f'orch_continual_exhaustion_segment1_{int(match[1]):03d}'
        result.append(dict(number=int(match[1]), batch_id=manifest['batch_id'],
                           manifest_sha256=sha(path), row_count=manifest['row_count']))
    return result


def export(number, expected, exclusions, root=ROOT):
    assert type(number) is int and 0 <= number < 64
    batch = root / f'orch_continual_exhaustion_feed_batch_{number:03d}'
    manifest_path = batch / 'MANIFEST.json'
    assert sha(manifest_path) == expected
    manifest = read(manifest_path)
    assert manifest['batch_id'] == f'orch_continual_exhaustion_segment1_{number:03d}'
    assert manifest['schema'] == 'ORCH_CONTINUAL_BATCH_V1' and manifest['encoding'] == 'math_content_v2'
    assert manifest['batch_author_accepted'] is True and manifest['parenting_experience'] is False
    assert manifest['source_purpose'] == 'L1_EXTERNAL_GENERATION'
    assert manifest['source_mix'] == 'MIXED_STEERING_SAME_37EC' and manifest['causal_prompt_comparison'] is False
    proof = dict(publisher_registry=base64.b64encode((root / 'PUBLISHER_REGISTRY.json').read_bytes()).decode(),
                 source_registry=base64.b64encode((root / 'SOURCE_REGISTRY.json').read_bytes()).decode())
    registered = registries(proof)
    paths = {}
    for key in ('source_native_archive', 'source_batch_manifest', 'sampled_review',
                'sample_registration', 'exclusions', 'source_registry'):
        path = Path(manifest[key + '_path'])
        assert path.resolve().is_relative_to(root.resolve())
        assert sha(path) == manifest[key + '_sha256'], key + '_source_pin'
        paths[key] = path
    assert manifest['source_registry_sha256'] == SOURCE_REGISTRY_SHA
    assert manifest['rows_path'] == 'ROWS.json'
    assert sha(batch / 'ROWS.json') == manifest['rows_sha256']
    wrapped = read(batch / 'ROWS.json')
    assert len(wrapped) == manifest['row_count']
    binding = read(paths['source_batch_manifest'])
    assert binding['candidates_sha256'] == sha(batch / 'CANDIDATES.json')
    assert binding['reviews_sha256'] == sha(paths['sampled_review'])
    assert binding['sample_sha256'] == sha(paths['sample_registration'])
    candidates = read(batch / 'CANDIDATES.json')
    proof['files'] = {}
    with tarfile.open(paths['source_native_archive']) as archive:
        members = {member.name.removeprefix('./'): member for member in archive.getmembers()}
        inventory_raw = archive.extractfile(members['RAW_INVENTORY.json']).read()
        inventory = json.loads(inventory_raw)
        proof['inventory'] = base64.b64encode(inventory_raw).decode()
        proof['inventory_sha256'] = hashlib.sha256(inventory_raw).hexdigest()

        def capture(name, expected_sha=None):
            if name in ('raw/PREPARE.json', 'raw/TASKS.json'):
                raw = (Path(SOURCE) / name.removeprefix('raw/')).read_bytes()
                assert expected_sha and hashlib.sha256(raw).hexdigest() == expected_sha
                proof['files'][name] = base64.b64encode(raw).decode()
                return json.loads(raw)
            member = members[name]
            assert member.isfile() and '..' not in Path(name).parts and not Path(name).is_absolute()
            raw = archive.extractfile(member).read()
            if expected_sha is not None:
                assert hashlib.sha256(raw).hexdigest() == expected_sha
            proof['files'][name] = base64.b64encode(raw).decode()
            return json.loads(raw)

        capture('raw/PREPARE.json', registered['source_prepare_sha256'])
        capture('raw/TASKS.json', registered['source_tasks_sha256'])
        for candidate in candidates:
            provenance = candidate['provenance']
            assert provenance['source_registry_sha256'] == SOURCE_REGISTRY_SHA
            assert provenance['source_archive_sha256'] == registered['source_archive_sha256']
            assert provenance['source_native_path'].startswith(SOURCE + '/')
            for key in ('raw_call', 'intent', 'loaded'):
                capture(provenance[key + '_path'], provenance[key + '_sha256'])
            call = json.loads(base64.b64decode(proof['files'][provenance['raw_call_path']]))
            if call['shard'] >= 4 and call['stage'] == 'final_0':
                name = f'raw/shard{call["shard"]}/{call["task_id"]}_draft_0.json'
                capture(name, inventory[name.removeprefix('raw/')])
    entries = [common.project(row, manifest['batch_id'], index) for index, row in enumerate(wrapped)]
    packet = dict(schema='COMBINED_CONTINUAL_SAMPLED_BATCH_V1', batch_id=manifest['batch_id'],
        origin='L1_EXTERNAL_GENERATION', parenting_experience=False, strong_teacher_source=False,
        policy_sha256=common.POLICY_SHA, wrapper_sha256=common.WRAPPER_SHA, rows=entries,
        proof=dict(candidates=candidates, reviews=read(paths['sampled_review']),
            decision=read(batch / 'BATCH_DECISION.json'), sample_registration=read(paths['sample_registration']),
            wrapper_excluded_hashes=[], exhaustion_segment1=proof),
        provenance=dict(original_manifest=manifest, manifest_sha256=expected,
            rows_file_sha256=manifest['rows_sha256'], verified_source_pins={str(path): sha(path) for path in paths.values()},
            publisher_registry_sha256=REGISTRY_SHA, source_adapter_sha256=ADAPTER_SHA,
            source_mix='MIXED_STEERING_SAME_37EC', causal_prompt_comparison=False,
            original_training_rows_unchanged=True, native_storage_only=True))
    packet['rows_sha256'] = common.digest(entries)
    return dict(packet=packet, exclusions=exclusions,
        manifest_bytes=base64.b64encode(manifest_path.read_bytes()).decode(),
        rows_bytes=base64.b64encode((batch / 'ROWS.json').read_bytes()).decode())


def replay(candidates, proof, exclusions, tokenizer):
    from gpu import orch_continual_exhaustion_feed as adapter
    from gpu import orch_combined_l1_continual_sampled as sampled
    assert sha(Path(adapter.__file__)) == ADAPTER_SHA
    assert sha(Path(adapter.generation.__file__)) == GENERATION_SHA
    registered = registries(proof)
    prepared = unpack(proof['files']['raw/PREPARE.json'], registered['source_prepare_sha256'])
    tasks = unpack(proof['files']['raw/TASKS.json'], registered['source_tasks_sha256'])
    inventory = unpack(proof['inventory'], proof['inventory_sha256'])
    for candidate in candidates:
        provenance = candidate['provenance']
        assert provenance['source_registry_sha256'] == SOURCE_REGISTRY_SHA
        assert provenance['source_archive_sha256'] == registered['source_archive_sha256']
        assert provenance['source_native_path'] == SOURCE + '/' + provenance['raw_call_path'].removeprefix('raw/')
        assert provenance['serialization_adapter'] == 'V3_NATIVE_VALIDATED_TO_UNCHANGED_NEUTRAL_ENCODER_V1'
        call, intent, loaded = [unpack(proof['files'][provenance[key + '_path']], provenance[key + '_sha256'])
                                for key in ('raw_call', 'intent', 'loaded')]
        match = re.fullmatch(r'B(\d{3})-P(\d{2})', call['task_id'])
        assert match
        task = adapter.generation.task_at(tasks, int(match[1]), int(match[2]), call['shard'])
        draft = None
        if call['shard'] >= 4 and call['stage'] == 'final_0':
            name = f'raw/shard{call["shard"]}/{call["task_id"]}_draft_0.json'
            draft = unpack(proof['files'][name], inventory[name.removeprefix('raw/')])
        normalized = adapter.validate_call(call, intent, task, loaded, prepared, draft)
        assert provenance['instruction_regime'] == ('EXHAUSTION_ONLY' if call['shard'] == 1 else 'STEERED')
        assert provenance['steering_degree'] == call['shard'] // 2
        recomputed = sampled.admission.mechanical(normalized, task['payload'], loaded,
            dict(initial=prepared['identity']), tokenizer,
            dict(math_ids=exclusions['held_math'], question_hashes=exclusions['held_question_hashes'],
                 route_ids=exclusions['held_route']), provenance)
        recomputed['generation_messages'] = call['messages']
        recomputed['original_semantic_status'] = call['outcome']['semantic_status']
        assert recomputed == candidate, 'native_mechanical_replay_drift'


def native_check(packet, exclusions, tokenizer):
    from gpu import orch_combined_l1_continual_sampled as sampled
    from gpu.orch_combined_l1_continual_content import encode_rows
    assert re.fullmatch(BATCH_PATTERN, packet['batch_id'])
    sampled.validate_packet(packet, exclusions)
    replay(packet['proof']['candidates'], packet['proof']['exhaustion_segment1'], exclusions, tokenizer)
    encoded = encode_rows([entry['row'] for entry in packet['rows']], tokenizer)
    for entry, value in zip(packet['rows'], encoded):
        supplied = entry['row']['training_encoding']
        assert list(value.input_ids) == supplied['input_ids']
        assert list(value.labels) == supplied['labels']
        assert len(value.input_ids) == supplied['sequence_length'] <= sampled.admission.TRAIN_CONTEXT
    return encoded


def probe_envelope(number, exclusions):
    assert type(number) is int and 0 <= number < 64
    batch = ROOT / f'orch_continual_exhaustion_feed_batch_{number:03d}'
    proof = dict(publisher_registry=base64.b64encode((ROOT / 'PUBLISHER_REGISTRY.json').read_bytes()).decode(),
                 source_registry=base64.b64encode((ROOT / 'SOURCE_REGISTRY.json').read_bytes()).decode(), files={})
    with tarfile.open(str(batch) + '.tar.gz') as archive:
        for member in archive.getmembers():
            name = member.name.removeprefix('./')
            if member.isfile() and (name.startswith('raw/') or name == 'RAW_INVENTORY.json'):
                assert '..' not in Path(name).parts and not Path(name).is_absolute()
                raw = archive.extractfile(member).read()
                if name == 'RAW_INVENTORY.json':
                    proof['inventory'] = base64.b64encode(raw).decode()
                    proof['inventory_sha256'] = hashlib.sha256(raw).hexdigest()
                else:
                    proof['files'][name] = base64.b64encode(raw).decode()
    registered = registries(proof)
    for name, key in [('PREPARE.json', 'source_prepare_sha256'), ('TASKS.json', 'source_tasks_sha256')]:
        raw = (Path(SOURCE) / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == registered[key]
        proof['files']['raw/' + name] = base64.b64encode(raw).decode()
    candidates = read(batch / 'CANDIDATES.json')
    return dict(candidates=candidates, proof=proof, exclusions=exclusions,
                candidates_sha256=sha(batch / 'CANDIDATES.json'), batch_number=number)


def probe_check(envelope, model_dir=None):
    from transformers import AutoTokenizer
    registered = registries(envelope['proof'])
    prepared = unpack(envelope['proof']['files']['raw/PREPARE.json'], registered['source_prepare_sha256'])
    tokenizer = AutoTokenizer.from_pretrained(model_dir or prepared['model_dir'], local_files_only=True)
    replay(envelope['candidates'], envelope['proof'], envelope['exclusions'], tokenizer)
    return dict(status='PASS', candidate_count=len(envelope['candidates']), batch_number=envelope['batch_number'],
        candidates_sha256=envelope['candidates_sha256'], publisher_registry_sha256=REGISTRY_SHA,
        native_model_calls=0, accepted=False, queued=False,
        scope='MECHANICAL_ENCODER_REPLAY_ONLY_NOT_AUTHOR_ADMISSION',
        supervised_tokens=sum(sum(label != -100 for label in row['training_encoding']['labels']) for row in envelope['candidates']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--discover', action='store_true')
    parser.add_argument('--number', type=int)
    parser.add_argument('--manifest-sha')
    parser.add_argument('--exclusions', type=Path)
    parser.add_argument('--probe-batch', type=int)
    parser.add_argument('--probe-export', action='store_true')
    parser.add_argument('--probe-receive', action='store_true')
    parser.add_argument('--model-dir')
    args = parser.parse_args()
    if args.probe_receive:
        json.dump(probe_check(json.load(sys.stdin), args.model_dir), sys.stdout)
    elif args.probe_batch is not None:
        envelope = probe_envelope(args.probe_batch, read(args.exclusions))
        json.dump(envelope if args.probe_export else probe_check(envelope), sys.stdout)
    else:
        json.dump(discover() if args.discover else export(args.number, args.manifest_sha, read(args.exclusions)), sys.stdout)
