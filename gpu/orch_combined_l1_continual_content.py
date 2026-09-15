"""Versioned content-only ingress; historical row labels remain untouched."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

from gpu import orch_combined_l1_continual_ingest as initial
from organism_v6 import orch_combined_l1_continual as state_policy
from organism_v6 import orch_math_readmission as eligibility_policy


POLICY_SHA = 'a3d1b626c0317d47f9324e54e86752eded9ec52f3e94596d979bf57ea660f307'
read, sha, write = initial.read, initial.sha, state_policy.atomic_json


def encode_rows(rows, tokenizer):
    from gpu import orch_guided_native as native
    from organism_v6.orch_l2_rich_math import CONTEXT
    encoded = []
    for row in rows:
        prefix, target = row['student_prefix'], row['target']
        messages = prefix + [dict(role='assistant', content=target)]
        context = tokenizer.apply_chat_template(prefix, tokenize=False, add_generation_prompt=True, return_dict=False)
        full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, return_dict=False)
        assert full == context + target + tokenizer.eos_token + '\n'
        prefix_ids = native.source.native._encode(tokenizer, context)
        target_ids = native.source.native._encode(tokenizer, target)
        suffix_ids = native.source.native._encode(tokenizer, '\n')
        supervised = target_ids + (tokenizer.eos_token_id,)
        sequence = native.source.native._encode(tokenizer, full)
        assert len(target_ids) > 0 and len(sequence) <= CONTEXT
        assert not set(tokenizer.all_special_ids).intersection(target_ids)
        assert native.source.native._decode(tokenizer, sequence) == full
        assert sequence == prefix_ids + supervised + suffix_ids
        item = native.source.native.EncodedRow(sequence,
            (-100,) * len(prefix_ids) + supervised + (-100,) * len(suffix_ids), supervised)
        native.bridge.validate_encoding_boundary(item, prefix_ids=prefix_ids, target_ids=target_ids,
            suffix_ids=suffix_ids, eos_token_id=tokenizer.eos_token_id, validate_masks=native.masks.validate_masks)
        encoded.append(item)
    return tuple(encoded)


def validate_entry(entry, exclusions):
    assert sha(eligibility_policy.__file__) == POLICY_SHA
    row, eligibility = entry['row'], entry['eligibility']
    assert entry['encoding'] == 'math_content_v2'
    assert entry['target_sha256'] == row['target_sha256'] == eligibility['target_sha256']
    reassessed = eligibility_policy.reassess(row, row['review'], entry['gold_review'],
        eligibility['source_capture_sha256'], exclusions['held_math'])
    assert reassessed == eligibility and reassessed['eligible'], 'v2_eligibility_binding_failed'
    assert entry['question_sha256'] == entry['gold_review']['question_sha256']
    assert entry['question_sha256'] not in exclusions['held_question_hashes'], 'held_question_hash'
    assert row['student_prefix'] and row['student_prefix'][-1]['role'] == 'user'
    assert not any(message['role'] == 'system' for message in row['student_prefix'])
    question_hashes = set()
    for message in row['student_prefix']:
        text = message['content']
        question_hashes.update((hashlib.sha256(text.encode()).hexdigest(),
                               hashlib.sha256(' '.join(text.split()).encode()).hexdigest()))
    assert not question_hashes & set(exclusions['held_question_hashes']), 'held_question_text'
    assert not any(identifier in json.dumps(entry, ensure_ascii=False) for identifier in exclusions['held_route'])


def append(state, packet, exclusions):
    assert packet['schema'] == 'COMBINED_CONTINUAL_CONTENT_BATCH_V2'
    assert packet['origin'] == 'L1_EXTERNAL_GENERATION' and packet['parenting_experience'] is False
    assert packet['policy_sha256'] == POLICY_SHA and packet['rows_sha256'] == state_policy.digest(packet['rows'])
    batch_id, binding = packet['batch_id'], state_policy.digest(packet)
    for previous in state['ingested']:
        if previous['batch_id'] == batch_id:
            assert previous['sha256'] == binding, 'batch_id_rebound'
            return state
    rows, duplicates = list(state['rows']), list(state['duplicates'])
    seen = {entry['target_sha256'] for entry in rows}
    for index, entry in enumerate(packet['rows']):
        validate_entry(entry, exclusions)
        if entry['target_sha256'] in seen:
            duplicates.append(dict(batch_id=batch_id, index=index, target_sha256=entry['target_sha256']))
        else:
            rows.append(entry)
            seen.add(entry['target_sha256'])
    return dict(state, version=state['version'] + 1, rows=rows, duplicates=duplicates,
        ingested=state['ingested'] + [dict(batch_id=batch_id, sha256=binding,
            added=len(rows) - len(state['rows']), provenance=packet['provenance'],
            policy_sha256=POLICY_SHA, historical_labels_unchanged=True)])


def bind(repository, root, manifest_path):
    manifest = read(manifest_path)
    assert manifest['schema'] == 'ORCH_CONTINUAL_BATCH_V1' and manifest['encoding'] == 'math_content_v2'
    assert manifest['source_purpose'] == 'L1_EXTERNAL_GENERATION'
    assert manifest['generation_not_parenting'] and not manifest['parenting_experience']
    assert manifest['policy_sha256'] == POLICY_SHA == sha(repository / manifest['policy_path'])
    path = manifest_path.parent / manifest['rows_path']
    assert path.resolve().parent == manifest_path.parent.resolve() and sha(path) == manifest['rows_sha256']
    source = repository / manifest['source_archive_path']
    assert sha(source) == manifest['source_archive_sha256']
    originals_path = repository / manifest['original_rows_path']
    assert sha(originals_path) == manifest['original_rows_sha256']
    originals = {row['target_sha256']: row for row in read(originals_path)}
    assert all(sha(repository / name) == expected for name, expected in manifest['review_file_sha256'].items())
    material = read(path)
    assert len(material) == manifest['row_count']
    rows = []
    with tarfile.open(source) as archive:
        members = {member.name.removeprefix('./'): member for member in archive.getmembers()}
        for index, wrapped in enumerate(material):
            row = wrapped['row']
            assert originals[row['target_sha256']] == row
            member = members[wrapped['source_archive_member'].removeprefix('./')]
            assert member.isfile()
            raw = archive.extractfile(member).read()
            assert hashlib.sha256(raw).hexdigest() == wrapped['eligibility']['source_capture_sha256']
            rows.append(dict(wrapped, corpus=manifest['batch_id'], index=index,
                encoding='math_content_v2', target_sha256=row['target_sha256']))
    packet = dict(schema='COMBINED_CONTINUAL_CONTENT_BATCH_V2', batch_id=manifest['batch_id'],
        origin='L1_EXTERNAL_GENERATION', parenting_experience=False, policy_sha256=POLICY_SHA,
        rows=rows, rows_sha256=state_policy.digest(rows), provenance=dict(
            original_manifest=manifest, manifest_sha256=sha(manifest_path), rows_file_sha256=sha(path)))
    exclusions = initial.exclusion_inventory(repository, root)
    state = state_policy.initial_state(read(root / 'PACKET/ADMITTED_ROWS.json'), initial.combined.MANIFEST_SHA)
    for previous in sorted((root / 'INBOX').glob('*/BOUND_PACKET.json')):
        state = state_policy.append_batch(state, read(previous), **{key: exclusions[key]
            for key in ('held_math', 'held_route', 'held_question_hashes')})
    checked = append(state, packet, exclusions)
    destination = root / 'CONTENT_QUEUE' / manifest['batch_id']
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(manifest_path, destination / 'MANIFEST.json')
    shutil.copyfile(path, destination / 'ROWS.json')
    shutil.copyfile(repository / manifest['policy_path'], destination / 'PINNED_POLICY.py')
    write(destination / 'EXCLUSIONS.json', exclusions)
    write(destination / 'BOUND_PACKET.json', packet)
    write(destination / 'CPU_BOUND.json', dict(status='PASS', manifest_sha256=sha(destination / 'MANIFEST.json'),
        rows_sha256=sha(destination / 'ROWS.json'), packet_sha256=sha(destination / 'BOUND_PACKET.json'),
        exclusions_sha256=sha(destination / 'EXCLUSIONS.json'), policy_sha256=POLICY_SHA,
        added=checked['ingested'][-1]['added'], duplicate_count=len(checked['duplicates']) - len(state['duplicates']),
        rows_after=len(checked['rows']), native_calls=0, historical_labels_unchanged=True,
        queued_not_training=True))
    print(json.dumps(read(destination / 'CPU_BOUND.json'), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, default=Path.cwd())
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    options = parser.parse_args()
    bind(options.repository.resolve(), options.root.resolve(), options.manifest.resolve())
