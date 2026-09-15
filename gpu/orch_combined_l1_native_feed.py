"""Node-only publisher proof export with lossless additive-metadata projection."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import sys
import tarfile


POLICY_SHA = 'c4bea936768dd171731965d7724761aec8c93225991140fbc06db1116a681b5f'
WRAPPER_SHA = 'ce5c35f7386b72530fa703d2d17a21a4324d045fed8f039420571fae543826e2'
REPORTING_FIELDS = frozenset(('instruction_regime', 'instruction_amount_tokens', 'branch_metrics',
    'mechanical_branch_counts', 'self_reported_branch_counts'))
ROOT = Path('/localhome/local-rohing/orch_continual_batch_20260915_segment2_disk_native1')
REGISTRY_PURPOSE = 'L1_RICHNESS_GENERATION'


def validate_registry_source(registered):
    assert registered['purpose'] == REGISTRY_PURPOSE and registered['family'] == 'math'


def allowed_number(number):
    return type(number) is int and (number in (27, 33, 34, 36, 38, 40) or 41 <= number <= 999)


def discover(root=ROOT):
    found = []
    for path in sorted(root.glob('orch_continual_batch_snapshot_*/MANIFEST.json')):
        match = re.fullmatch(r'orch_continual_batch_snapshot_(\d{3})', path.parent.name)
        if match is None or not 41 <= int(match[1]) <= 999:
            continue
        try:
            manifest = read(path)
        except (OSError, json.JSONDecodeError):
            continue
        if manifest.get('batch_author_accepted') is not True:
            continue
        found.append(dict(number=int(match[1]), manifest_sha256=sha(path),
            batch_id=manifest.get('batch_id'), row_count=manifest.get('row_count')))
    return found


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text())


def project(wrapped, batch_id, index):
    original = wrapped['eligibility']
    assert REPORTING_FIELDS <= original.keys(), 'native_reporting_metadata_missing'
    eligibility = {key: value for key, value in original.items() if key not in REPORTING_FIELDS}
    return dict(wrapped, eligibility=eligibility, encoding='math_content_v2', corpus=batch_id, index=index,
        target_sha256=wrapped['row']['target_sha256'],
        publisher_reporting_metadata={key: original[key] for key in REPORTING_FIELDS},
        publisher_original_eligibility=original,
        projection='REMOVE_ONLY_ADDITIVE_REPORTING_FIELDS_FROM_V2_CORE_KEEP_ORIGINAL_ROW_AND_METADATA')


def export(number, expected_manifest_sha, exclusions):
    assert allowed_number(number), 'bounded_native_publisher_sequence_only'
    batch = ROOT / f'orch_continual_batch_snapshot_{number:03d}'
    manifest_path = batch / 'MANIFEST.json'
    assert sha(manifest_path) == expected_manifest_sha
    manifest = read(manifest_path)
    assert manifest['schema'] == 'ORCH_CONTINUAL_BATCH_V1'
    assert manifest['source_purpose'] == 'L1_EXTERNAL_GENERATION' and manifest['parenting_experience'] is False
    assert manifest['batch_author_accepted'] is True and manifest['encoding'] == 'math_content_v2'
    paths = {}
    for key in ('source_native_archive', 'source_batch_manifest', 'sampled_review', 'sample_registration', 'exclusions', 'source_registry'):
        path = Path(manifest[key + '_path'])
        assert path.resolve().is_relative_to(ROOT.resolve())
        assert sha(path) == manifest[key + '_sha256'], key + '_source_pin'
        paths[key] = path
    rows_path = batch / manifest['rows_path']
    assert rows_path.parent == batch and sha(rows_path) == manifest['rows_sha256']
    wrapped = read(rows_path)
    assert len(wrapped) == manifest['row_count']
    binding = read(paths['source_batch_manifest'])
    assert binding['candidates_sha256'] == sha(batch / 'CANDIDATES.json')
    assert binding['reviews_sha256'] == sha(paths['sampled_review'])
    assert binding['sample_sha256'] == sha(paths['sample_registration'])
    candidates = read(batch / 'CANDIDATES.json')
    reviews = read(paths['sampled_review'])
    decision = read(batch / 'BATCH_DECISION.json')
    assert decision['accepted'] and decision['exported_rows'] == len(wrapped)
    registry, native = read(paths['source_registry']), {}
    with tarfile.open(paths['source_native_archive']) as archive:
        members = {member.name.removeprefix('./'): member for member in archive.getmembers()}

        def source(name, expected):
            member = members[name]
            assert member.isfile() and '..' not in Path(name).parts and not Path(name).is_absolute()
            raw = archive.extractfile(member).read()
            assert hashlib.sha256(raw).hexdigest() == expected, 'native_archive_member_binding'
            return json.loads(raw)

        for candidate in candidates:
            provenance = candidate['provenance']
            matches = [name for name in registry['sources'] if provenance['source_native_path'].startswith(name + '/')]
            assert len(matches) == 1
            registered = registry['sources'][matches[0]]
            validate_registry_source(registered)
            assert registered['source_archive_sha256'] == provenance['source_archive_sha256']
            assert provenance['source_registry_sha256'] == manifest['source_registry_sha256']
            prepared = source('raw/PREPARE.json', provenance['source_prepare_sha256'])
            tasks = source('raw/TASKS.json', provenance['tasks_sha256'])
            task = next(task for task in tasks['tasks'] if task['id'] == candidate['task_id'])
            call = source(provenance['raw_call_path'], provenance['raw_call_sha256'])
            intent = source(provenance['intent_path'], provenance['intent_sha256'])
            assert all(call[key] == value for key, value in intent.items())
            native[candidate['target_sha256']] = dict(prepared=prepared, task=task, call=call,
                loaded=source(provenance['loaded_path'], provenance['loaded_sha256']))
    entries = [project(row, manifest['batch_id'], index) for index, row in enumerate(wrapped)]
    packet = dict(schema='COMBINED_CONTINUAL_SAMPLED_BATCH_V1', batch_id=manifest['batch_id'],
        origin='L1_EXTERNAL_GENERATION', parenting_experience=False, strong_teacher_source=False,
        policy_sha256=POLICY_SHA, wrapper_sha256=WRAPPER_SHA, rows=entries,
        proof=dict(candidates=candidates, reviews=reviews, decision=decision,
            sample_registration=read(paths['sample_registration']), native=native, wrapper_excluded_hashes=[]),
        provenance=dict(original_manifest=manifest, manifest_sha256=sha(manifest_path), rows_file_sha256=sha(rows_path),
            verified_source_pins={str(path): sha(path) for path in paths.values()},
            publisher_policy_sha256=sha(ROOT / 'source/organism_v6/orch_continual_batch.py'),
            publisher_wrapper_sha256=sha(ROOT / 'source/gpu/orch_continual_batch_handoff.py'),
            consumer_core_revalidation='existing fixedV2 source/admission/native encoder; additive reporting metadata retained without recertification',
            original_training_rows_unchanged=True, native_storage_only=True))
    packet['rows_sha256'] = digest(entries)
    return dict(packet=packet, exclusions=exclusions,
        manifest_bytes=base64.b64encode(manifest_path.read_bytes()).decode(),
        rows_bytes=base64.b64encode(rows_path.read_bytes()).decode())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--number', type=int)
    parser.add_argument('--manifest-sha')
    parser.add_argument('--exclusions', type=Path)
    parser.add_argument('--discover', action='store_true')
    args = parser.parse_args()
    if args.discover:
        json.dump(discover(), sys.stdout)
    else:
        assert args.number is not None and args.manifest_sha and args.exclusions
        json.dump(export(args.number, args.manifest_sha, read(args.exclusions)), sys.stdout)
