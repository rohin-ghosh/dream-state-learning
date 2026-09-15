"""Freeze the complete qualified difference, without fitting or new reviews."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from gpu.orch_rich_intensity_reduce import read, reduce
from organism_v6 import orch_math_rich as original


FIRST_SHA = '52197d8d0f73528af69b61e6f244e5b1570f2bcfafd5ebb79d4058c959946837'
FIRST = Path('research_notes/analysis/orch_rich_intensity_20260915_first_qualified')
QUALIFIED = Path('research_notes/analysis/orch_rich_intensity_20260915_terminal')
PANEL = Path('research_notes/analysis/orch_rich_intensity_20260915_paired8')
ROOT = Path('gpu_artifacts_local/orch_rich_intensity_20260915_attempt3/terminal')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def wire(document):
    return (json.dumps(document, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode()


def key(row):
    return ':'.join(row[field] for field in ('condition', 'task_id', 'kind'))


def select(first, rows):
    assert len(first) == 16 and all(row['admitted'] for row in first)
    qualified = [row for row in rows if row['admitted']]
    assert len(qualified) == 26
    by_key = {key(row): row for row in qualified}
    assert len(by_key) == len(qualified)
    assert len({key(row) for row in first}) == 16
    assert all(row == by_key[key(row)] for row in first)
    first_keys = {key(row) for row in first}
    extra = [row for row in qualified if key(row) not in first_keys]
    assert len(extra) == 10
    assert len({row['target_sha256'] for row in qualified}) == 26
    assert not {row['target_sha256'] for row in extra} & {row['target_sha256'] for row in first}
    combined = first + extra
    assert {key(row) for row in combined} == set(by_key)
    for row in combined:
        assert row['semantic_status'] == 'PASS' and row['review']['full_text_read'] is True
        assert row['candidate'] and row['outcome_pass'] and row['token_contract_pass']
        assert row['target'] == row['call']['raw']
        assert sha(row['target'].encode()) == row['target_sha256']
        assert original.digest(row['student_prefix']) == row['student_prefix_sha256']
    return extra, combined


def membership(rows):
    return dict(rows=len(rows), unique_targets=len({row['target_sha256'] for row in rows}),
        distinct_tasks=len({row['task_id'] for row in rows}),
        distinct_task_kind=len({(row['task_id'], row['kind']) for row in rows}),
        tasks=sorted({row['task_id'] for row in rows}),
        families=dict(Counter(row['family'] for row in rows)),
        conditions=dict(Counter(row['condition'] for row in rows)))


def export(output):
    assert not output.exists(), 'immutable_destination_already_exists'
    source_paths = [FIRST / 'ADMITTED.json', FIRST / 'REVIEWS.json', FIRST / 'GOLD.json',
        QUALIFIED / 'SUMMARY.json', QUALIFIED / 'REVIEWS.json', QUALIFIED / 'GOLD.json',
        PANEL / 'ADMITTED.json', PANEL / 'REVIEWS.json', PANEL / 'GOLD.json', ROOT / 'TASKS.json']
    source_bytes = {path: path.read_bytes() for path in source_paths}
    assert sha(source_bytes[FIRST / 'ADMITTED.json']) == FIRST_SHA
    first = json.loads(source_bytes[FIRST / 'ADMITTED.json'])
    reviews = json.loads(source_bytes[QUALIFIED / 'REVIEWS.json'])
    gold = json.loads(source_bytes[QUALIFIED / 'GOLD.json'])
    summary, rows = reduce(ROOT, reviews, gold)
    published = json.loads(source_bytes[QUALIFIED / 'SUMMARY.json'])
    assert summary['complete'] and all(published[name] == value for name, value in summary.items())
    extra, combined = select(first, rows)
    tasks = {task['id']: task for task in json.loads(source_bytes[ROOT / 'TASKS.json'])['tasks']}
    first_keys = {key(row) for row in first}
    panel_admitted = json.loads(source_bytes[PANEL / 'ADMITTED.json'])
    assert all(row in panel_admitted for row in extra)
    payloads = dict(FIRST16=source_bytes[FIRST / 'ADMITTED.json'],
        ADDITIONAL10=wire(extra), COMBINED26=wire(combined))
    files = {name + '.json': raw for name, raw in payloads.items()}
    row_manifest = []
    for position, row in enumerate(combined):
        identity = key(row)
        captured = summary['inventory'][identity]
        raw_path = ROOT / captured['path']
        raw = raw_path.read_bytes()
        assert sha(raw) == captured['sha256'] == reviews[identity]['raw_call_sha256']
        assert json.loads(raw)['call'] == row['call']
        assert reviews[identity] == row['review']
        assert gold[row['task_id']]['status'] == 'VALID'
        qualification = FIRST if identity in first_keys else PANEL
        reference_reviews = json.loads(source_bytes[qualification / 'REVIEWS.json'])
        reference_gold = json.loads(source_bytes[qualification / 'GOLD.json'])
        assert reference_reviews[identity] == row['review']
        assert reference_gold[row['task_id']] == gold[row['task_id']]
        frozen_path = 'RAW/' + captured['path']
        files[frozen_path] = raw
        task = tasks[row['task_id']]
        assert task['family'] == row['family'] and task['gold'] == row['gold']
        row_manifest.append(dict(combined_index=position,
            additional_index=position - 16 if position >= 16 else None,
            first16_index=position if position < 16 else None, key=identity,
            task_id=row['task_id'], family=row['family'], condition=row['condition'], kind=row['kind'],
            question_sha256=task['question_sha256'], target_sha256=row['target_sha256'],
            student_prefix_sha256=row['student_prefix_sha256'],
            row_canonical_sha256=original.digest(row),
            raw_capture=dict(source=str(raw_path), frozen=frozen_path, sha256=sha(raw)),
            qualification=dict(review_path=str(qualification / 'REVIEWS.json'), review_key=identity,
                review_canonical_sha256=original.digest(row['review']),
                gold_path=str(qualification / 'GOLD.json'), gold_key=row['task_id'],
                gold_canonical_sha256=original.digest(gold[row['task_id']]),
                admitted_path=str(qualification / 'ADMITTED.json'),
                admitted_index=(first if position < 16 else panel_admitted).index(row))))
    files['TASK_MEMBERSHIP.json'] = wire([tasks[identity] for identity in sorted({row['task_id'] for row in combined})])
    files['QUALIFICATION_REVIEWS.json'] = wire({key(row): reviews[key(row)] for row in combined})
    files['QUALIFICATION_GOLD.json'] = wire({identity: gold[identity] for identity in sorted({row['task_id'] for row in combined})})
    manifest = dict(schema='RICH_INTENSITY_EXISTING_QUALIFIED_BOOTSTRAP_INPUT_V1',
        selection='ALL terminal admitted rows minus exact first16 keys; assert no target-hash overlap. No ranking or additional filtering.',
        order='ADDITIONAL10 uses terminal reducer shard/call order; COMBINED26 is original first16 order followed by ADDITIONAL10.',
        immutability='Exclusive-create destination and files; read-only file modes; verify SHA256 before use.',
        hash_conventions=dict(files_and_targets='SHA256 of exact bytes; targets UTF-8',
            student_prefix_and_canonical_objects='Existing orch_math_rich.digest; no new normalization'),
        membership={name: membership(selected) for name, selected in
            (('FIRST16', first), ('ADDITIONAL10', extra), ('COMBINED26', combined))},
        source_files={str(path): dict(sha256=sha(raw), bytes=len(raw)) for path, raw in source_bytes.items()},
        files={name: dict(sha256=sha(raw), bytes=len(raw)) for name, raw in files.items()},
        rows=row_manifest, semantic_reviews_added=0, independent_verification=False,
        generated_calls=0, fits=0, gate_changes=False, new_l1_outcomes_read=False,
        fixed16_bootstrap_entrypoint_compatible=False,
        encoder_check='Separate ENCODER_COMPATIBILITY.json; packet assembly alone does not verify encoding.',
        training_authorized=False, dose_matching_designed=False)
    assert all(path.read_bytes() == raw for path, raw in source_bytes.items())
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in dict(files, **{'MANIFEST.json': wire(manifest)}).items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
        path.chmod(0o444)
    assert all(sha((output / name).read_bytes()) == entry['sha256'] for name, entry in manifest['files'].items())
    return dict(output=str(output), manifest_sha256=sha((output / 'MANIFEST.json').read_bytes()),
        packets={name: manifest['files'][name + '.json']['sha256'] for name in payloads},
        membership=manifest['membership'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    options = parser.parse_args()
    print(json.dumps(export(options.output), indent=2))
