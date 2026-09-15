"""Append sampled-author batches without upgrading unsampled review labels."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tarfile

from gpu import orch_combined_l1_continual_ingest as initial
from gpu import orch_combined_l1_sampled_wrapper_v1 as handoff
from organism_v6 import orch_combined_l1_continual as state_policy
from organism_v6 import orch_combined_l1_sampled_policy_v1 as admission


POLICY_SHA = 'c4bea936768dd171731965d7724761aec8c93225991140fbc06db1116a681b5f'
WRAPPER_SHA = 'ce5c35f7386b72530fa703d2d17a21a4324d045fed8f039420571fae543826e2'
NODE2_SHA = '9eaa28bdba338873134cd0e1dbbadfae24c86722735978b3f3b0b77082957415'
SCHEMA = 'COMBINED_CONTINUAL_SAMPLED_BATCH_V1'
read, sha, write = initial.read, initial.sha, state_policy.atomic_json
handoff.policy = admission


def validate_entry(entry, exclusions):
    row, eligibility = entry['row'], entry['eligibility']
    assert entry['encoding'] == 'math_content_v2'
    expected = handoff.wrap_row(row, eligibility['batch_manifest_sha256'])
    assert {key: entry[key] for key in expected} == expected, 'sampled_wrapper_drift'
    assert eligibility['policy'] == 'ROHIN98_BATCH_SAMPLED_AUTHOR_REVIEW_V2'
    assert row['admission_mode'] == admission.MODE and row['batch_training_allowed'] is True
    assert row['admitted'] is False and row['trainingAllowed'] is False, 'historical_label_upgrade'
    assert row['semantic_status'] == ('PASS' if row['review'] else 'UNREVIEWED')
    assert row['original_semantic_status'] == 'UNREVIEWED'
    assert entry['target_sha256'] == row['target_sha256'] == admission.text_sha(row['target'])
    assert admission.math.digest(row['student_prefix']) == row['student_prefix_sha256']
    assert row['question_sha256'] == admission.math.digest(' '.join(row['question'].lower().split()))
    assert row['student_prefix'][0] == dict(role='user', content=row['question'])
    assert all(message['role'] != 'system' for message in row['student_prefix'])
    assert row['task_id'] not in exclusions['held_math'], 'held_math_id'
    assert row['question_sha256'] not in exclusions['held_question_hashes'], 'held_question_hash'
    assert not any(identifier in json.dumps(row['student_prefix'] + [dict(role='assistant', content=row['target'])],
        ensure_ascii=False) for identifier in exclusions['held_route']), 'held_route_id'
    for message in row['student_prefix']:
        text = message['content']
        hashes = {admission.text_sha(text), admission.text_sha(' '.join(text.split())),
                  admission.math.digest(' '.join(text.lower().split()))}
        assert not hashes.intersection(exclusions['held_question_hashes']), 'held_prefix_question'
    assert row['provenance']['registered_source_purpose'] == admission.PURPOSE
    assert row['provenance']['no_parent_teacher_target'] is True, 'teacher_parenting_quarantine'
    assert row['call']['terminal'] and not row['call']['truncated']
    assert row['call']['raw'] == row['target'] and row['outcome_pass']
    assert admission.math.final_value(row['target']) == admission.math.number(row['gold'])
    assert row['training_encoding']['context_limit'] == admission.TRAIN_CONTEXT
    assert row['training_encoding']['sequence_length'] <= admission.TRAIN_CONTEXT


def validate_packet(packet, exclusions):
    assert packet['schema'] == SCHEMA
    assert sha(admission.__file__) == packet['policy_sha256'] == POLICY_SHA
    assert sha(handoff.__file__) == packet['wrapper_sha256'] == WRAPPER_SHA
    assert packet['origin'] == 'L1_EXTERNAL_GENERATION' and packet['parenting_experience'] is False
    assert packet['strong_teacher_source'] is False, 'teacher_quarantine'
    assert packet['rows_sha256'] == state_policy.digest(packet['rows'])
    proof = packet['proof']
    candidates, reviews = proof['candidates'], proof['reviews']
    selected = admission.sample(candidates)
    assert proof['sample_registration']['semantic_results_seen'] is False
    assert proof['sample_registration']['sample_target_sha256s'] == [row['target_sha256'] for row in selected]
    admission.validate_review(selected, dict(reviews=reviews))
    decision, exported = admission.adjudicate(candidates, reviews)
    assert decision['accepted'] and decision == proof['decision'], 'sampled_batch_not_accepted'
    expected = {row['target_sha256']: row for row in exported}
    assert len({entry['target_sha256'] for entry in packet['rows']}) == len(packet['rows'])
    assert set(expected) == {entry['target_sha256'] for entry in packet['rows']} | set(proof['wrapper_excluded_hashes'])
    for entry in packet['rows']:
        assert entry['row'] == expected[entry['target_sha256']], 'original_sampled_row_drift'
        validate_entry(entry, exclusions)


def append(state, packet, exclusions):
    binding = state_policy.digest(packet)
    for previous in state['ingested']:
        if previous['batch_id'] == packet['batch_id']:
            assert previous['sha256'] == binding, 'batch_id_rebound'
            return state
    validate_packet(packet, exclusions)
    rows, duplicates = list(state['rows']), list(state['duplicates'])
    seen = {row['target_sha256'] for row in rows}
    for entry in packet['rows']:
        if entry['target_sha256'] in seen:
            duplicates.append(dict(batch_id=packet['batch_id'], index=entry['index'], target_sha256=entry['target_sha256']))
        else:
            rows.append(entry)
            seen.add(entry['target_sha256'])
    return dict(state, version=state['version'] + 1, rows=rows, duplicates=duplicates,
        ingested=state['ingested'] + [dict(batch_id=packet['batch_id'], sha256=binding,
            added=len(rows) - len(state['rows']), provenance=packet['provenance'],
            admission_mode=admission.MODE, historical_labels_unchanged=True,
            unsampled_individual_status='UNREVIEWED', semantic_branching_certified=False)])


def native_check(packet, exclusions, tokenizer):
    from gpu.orch_combined_l1_continual_content import encode_rows
    validate_packet(packet, exclusions)
    for candidate in packet['proof']['candidates']:
        native = packet['proof']['native'][candidate['target_sha256']]
        call, prepared = native['call'], native['prepared']
        if candidate['provenance'].get('serialization_adapter'):
            from gpu import orch_continual_batch_snapshot_node2 as node2
            assert sha(node2.__file__) == NODE2_SHA
            assert candidate['provenance']['serialization_adapter'] == 'NODE2_MATH_NATIVE_TO_NEUTRAL_V1_ORIGINAL_RAW_PRESERVED'
            call, prepared = node2.normalized_call(call), dict(initial=prepared['identity'])
        recomputed = admission.mechanical(call, native['task'], native['loaded'], prepared,
            tokenizer, dict(math_ids=exclusions['held_math'], question_hashes=exclusions['held_question_hashes'],
                            route_ids=exclusions['held_route']), candidate['provenance'])
        assert recomputed == candidate, 'native_mechanical_replay_drift'
    encoded = encode_rows([entry['row'] for entry in packet['rows']], tokenizer)
    for entry, value in zip(packet['rows'], encoded):
        supplied = entry['row']['training_encoding']
        assert list(value.input_ids) == supplied['input_ids'], 'exact_sampled_native_inputs'
        assert list(value.labels) == supplied['labels'], 'exact_sampled_native_labels'
        assert len(value.input_ids) == supplied['sequence_length'] <= admission.TRAIN_CONTEXT
    return encoded


def bind(repository, root, manifest_path, stdout=False):
    manifest = read(manifest_path)
    assert manifest['schema'] == 'ORCH_CONTINUAL_BATCH_V1' and manifest['encoding'] == 'math_content_v2'
    assert manifest['batch_author_accepted'] is True and manifest['admission_mode'] == admission.MODE
    assert manifest['source_purpose'] == 'L1_EXTERNAL_GENERATION'
    assert manifest['generation_not_parenting'] and not manifest['parenting_experience']
    paths = {}
    for prefix in ('source_batch_manifest', 'source_native_archive', 'sample_registration',
                   'sampled_review', 'source_registry', 'exclusions'):
        path = repository / manifest[prefix + '_path']
        assert path.resolve().is_relative_to(repository.resolve())
        assert sha(path) == manifest[prefix + '_sha256'], prefix + '_binding'
        paths[prefix] = path
    rows_path = manifest_path.parent / manifest['rows_path']
    assert rows_path.resolve().parent == manifest_path.parent.resolve()
    assert sha(rows_path) == manifest['rows_sha256']
    wrapped = read(rows_path)
    assert len(wrapped) == manifest['row_count']
    source_root = paths['source_batch_manifest'].parent
    registration = read(paths['sample_registration'])
    assert sha(source_root / 'CANDIDATES.json') == registration['candidates_sha256']
    assert sha(source_root / 'REGISTRATION.json') == registration['registration_sha256']
    candidates, reviews = read(source_root / 'CANDIDATES.json'), read(paths['sampled_review'])
    decision, exported = admission.adjudicate(candidates, reviews)
    assert exported == read(source_root / 'ROWS.json')
    source_manifest = read(paths['source_batch_manifest'])
    assert sha(source_root / source_manifest['rows_path']) == source_manifest['rows_sha256']
    registry = read(paths['source_registry'])
    native = {}
    with tarfile.open(paths['source_native_archive']) as archive:
        members = {member.name.removeprefix('./'): member for member in archive.getmembers()}

        def source(name, expected=None):
            member = members[name]
            assert member.isfile()
            raw = archive.extractfile(member).read()
            if expected is not None:
                assert hashlib.sha256(raw).hexdigest() == expected, 'native_source_hash'
            return json.loads(raw)

        for candidate in candidates:
            provenance = candidate['provenance']
            matches = [name for name in registry['sources'] if provenance['source_native_path'].startswith(name + '/')]
            assert len(matches) == 1, 'single_registered_source_required'
            source_name = matches[0]
            registered = registry['sources'][source_name]
            assert registered['purpose'] == admission.PURPOSE and registered['family'] == 'math'
            assert provenance['source_archive_sha256'] == registered['source_archive_sha256']
            assert provenance['source_registry_sha256'] == manifest['source_registry_sha256']
            prepared = source('raw/PREPARE.json', provenance['source_prepare_sha256'])
            tasks = source('raw/TASKS.json', provenance['tasks_sha256'])
            task = next(task for task in tasks['tasks'] if task['id'] == candidate['task_id'])
            call = source(provenance['raw_call_path'], provenance['raw_call_sha256'])
            intent = source(provenance['intent_path'], provenance['intent_sha256'])
            assert all(call[key] == value for key, value in intent.items()), 'native_intent_binding'
            native[candidate['target_sha256']] = dict(prepared=prepared, task=task, call=call,
                loaded=source(provenance['loaded_path'], provenance['loaded_sha256']))
    packet = dict(schema=SCHEMA, batch_id=manifest['batch_id'], origin='L1_EXTERNAL_GENERATION',
        parenting_experience=False, strong_teacher_source=False, policy_sha256=POLICY_SHA,
        wrapper_sha256=WRAPPER_SHA, rows=[dict(entry, corpus=manifest['batch_id'], index=index,
            encoding='math_content_v2', target_sha256=entry['row']['target_sha256']) for index, entry in enumerate(wrapped)],
        proof=dict(candidates=candidates, reviews=reviews, decision=decision,
            sample_registration=registration, native=native,
            wrapper_excluded_hashes=sorted({row['target_sha256'] for row in exported} -
                                           {entry['row']['target_sha256'] for entry in wrapped})),
        provenance=dict(original_manifest=manifest, manifest_sha256=sha(manifest_path),
            rows_file_sha256=sha(rows_path), verified_source_pins={str(path): sha(path) for path in paths.values()}))
    packet['rows_sha256'] = state_policy.digest(packet['rows'])
    exclusions = initial.exclusion_inventory(repository, root)
    if stdout:
        validate_packet(packet, exclusions)
        json.dump(dict(packet=packet, exclusions=exclusions,
            manifest_bytes=base64.b64encode(manifest_path.read_bytes()).decode(),
            rows_bytes=base64.b64encode(rows_path.read_bytes()).decode()), sys.stdout)
        return
    from gpu.orch_combined_l1_continual_guard import take_batch
    state = state_policy.initial_state(read(root / 'PACKET/ADMITTED_ROWS.json'), initial.combined.MANIFEST_SHA)
    state = take_batch(root, state)
    checked = append(state, packet, exclusions)
    destination = root / 'SAMPLED_QUEUE_PENDING' / manifest['batch_id']
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(manifest_path, destination / 'MANIFEST.json')
    shutil.copyfile(rows_path, destination / 'ROWS.json')
    write(destination / 'BOUND_PACKET.json', packet)
    write(destination / 'EXCLUSIONS.json', exclusions)
    write(destination / 'CPU_BOUND.json', dict(status='PASS', packet_sha256=sha(destination / 'BOUND_PACKET.json'),
        manifest_sha256=sha(destination / 'MANIFEST.json'), rows_sha256=sha(destination / 'ROWS.json'),
        exclusions_sha256=sha(destination / 'EXCLUSIONS.json'), added=checked['ingested'][-1]['added'],
        rows_after=len(checked['rows']), native_calls=0, queued_not_training=True,
        admission_mode=admission.MODE, unsampled_individual_status='UNREVIEWED'))
    print(json.dumps(read(destination / 'CPU_BOUND.json'), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, default=Path.cwd())
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--stdout', action='store_true')
    options = parser.parse_args()
    bind(options.repository.resolve(), options.root.resolve(), options.manifest.resolve(), options.stdout)
