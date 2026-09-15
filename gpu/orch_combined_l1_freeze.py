"""Immutable combined L1 inputs from existing qualified corpus snapshots."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil

from gpu.orch_l2_rich_math_bootstrap import read, sha, write
from organism_v6 import orch_math_rich as math


SEQ_SHA = '8606ffeb9c8b935f8003bba03bbe0a26abef2b8eb7e5c0e834a6bea8b914d53a'
CAPSULE_SHA = 'cbe638aa1377a98ada6c60a3fc1b264c685a2e31c95b5121f2dd3f860bda1a1e'
MATH_SHA = '257272aeead68cd690b984895e09fad9493d3d1d0e5b7e76b6c27872da2e3d2e'


def text_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def freeze(repository, output):
    assert not (output / 'CORPUS_MANIFEST.json').exists()
    assert sha(output / 'SEQ266/TRAINING_ROWS.json') == SEQ_SHA
    assert sha(output / 'SEQ266/CAPSULE.json') == CAPSULE_SHA
    old_material = read(output / 'SEQ266/TRAINING_ROWS.json')
    capsule = read(output / 'SEQ266/CAPSULE.json')['capsule']
    assert old_material['new_trajectory_rows'] == capsule['rows'] and len(capsule['rows']) == 1452
    source = repository / 'research_notes/analysis'
    scale_root = source / 'orch_rich_breadth_bootstrap_20260915_attempt1/scale764'
    scale_packet = scale_root / 'PACKET/ADMITTED_ROWS.json'
    assert sha(scale_packet) == MATH_SHA
    (output / 'SOURCES').mkdir(exist_ok=False)
    (output / 'PACKET').mkdir(exist_ok=False)
    rows = [dict(corpus='SEQ266', index=index, encoding='terse_route', row=row,
                 target_sha256=text_hash(row['assistant'])) for index, row in enumerate(capsule['rows'])]
    for index, row in enumerate(read(scale_packet)):
        rows.append(dict(corpus='MATH764', index=index, encoding='math', row=row,
            target_sha256=row['target_sha256']))
    assert len(rows) == 2216
    seen = {row['target_sha256'] for row in rows}
    counts, duplicates, sources = {'SEQ266': 1452, 'MATH764': 764}, [], {}
    additions = [
        ('MATH_RICH19', source / 'orch_math_rich_20260914_attempt1', 'RAW_ROWS.json', 'math'),
        ('MATH_RECORD92', source / 'orch_math_record_20260914_attempt1', 'ROWS.json', 'math'),
        ('INTENSITY56', source / 'orch_rich_supply_review_20260915', 'ADMITTED_COMBINED.json', 'math'),
        ('TWO_PASS9', source / 'orch_rich_twopass_20260914_attempt1/readout_first_reviewed', 'ADMITTED_ROWS.json', 'math'),
        ('FULL_RICH3', source / 'orch_full_rich_20260914_attempt1', 'ADMITTED_ROWS.json', 'rich_route')]
    for label, directory, filename, encoding in additions:
        path = directory / filename
        payload = read(path)
        admitted = [(index, row) for index, row in enumerate(payload) if row.get('admitted') is True]
        expected = {'MATH_RICH19': 19, 'MATH_RECORD92': 92, 'INTENSITY56': 56, 'TWO_PASS9': 9, 'FULL_RICH3': 3}[label]
        assert len(admitted) == expected
        counts[label] = 0
        copied = output / 'SOURCES' / label
        copied.mkdir()
        shutil.copyfile(path, copied / filename)
        sources[str(path.relative_to(repository))] = sha(path)
        for sidecar in ('ADMITTED_ROWS.json', 'SEMANTIC_REVIEW.json', 'GOLD_REVIEW.json', 'TASKS.json',
                        'TASKS_VIEW.json', 'MANIFEST.json', 'QUALIFICATION_GOLD.json', 'QUALIFICATION_REVIEWS.json',
                        'COMBINED_GOLD.json', 'COMBINED_REVIEWS.json', 'REVIEW_BINDINGS.json', 'PACKET_BINDINGS.json'):
            candidate = directory / sidecar
            if candidate.exists() and candidate != path:
                shutil.copyfile(candidate, copied / sidecar)
                sources[str(candidate.relative_to(repository))] = sha(candidate)
        for index, row in admitted:
            assert row['semantic_status'] == 'PASS'
            target = row['student']['target'] if encoding == 'rich_route' else row['target']
            digest = text_hash(target)
            if encoding == 'math':
                assert row['outcome_pass'] and row['token_contract_pass']
                assert row['target_sha256'] == digest and row['call']['raw'] == target
            else:
                assert row['student']['messages'][-1] == dict(role='assistant', content=target)
                assert row['student']['parent_guidance_removed']
            if digest in seen:
                duplicates.append(dict(corpus=label, index=index, target_sha256=digest))
                continue
            seen.add(digest)
            rows.append(dict(corpus=label, index=index, encoding=encoding, row=row, target_sha256=digest))
            counts[label] += 1
    for name in ('LEGACY_MATERIAL.json', 'OLD_MASKS.json', 'LEGACY_READOUT.json', 'COHORT.json',
                 'TASKS_SOURCE.json', 'QUALIFICATION_GOLD.json', 'DATA_PROVENANCE.json'):
        destination = output / (name if name != 'DATA_PROVENANCE.json' else 'MATH764_PROVENANCE.json')
        shutil.copyfile(scale_root / name, destination)
    shutil.copyfile(scale_packet, output / 'SOURCES/MATH764.json')
    legacy = read(output / 'LEGACY_MATERIAL.json')
    assert all(legacy[key] == old_material[key] for key in legacy)
    held_math = read(output / 'COHORT.json')['tasks']
    training_math = {entry['row']['task_id'] for entry in rows if entry['encoding'] == 'math'}
    assert not training_math & {task['id'] for task in held_math}
    assert len(held_math) == 64
    probes = []
    serialized = json.dumps(rows, ensure_ascii=False)
    from gpu import astra_goal_quality_train as route
    for probe in capsule['source_plan']['probes']:
        identifiers = route.goal.identifiers(probe['world'])
        assert not any(identity in serialized for identity in identifiers), 'route_held_identifier_in_training'
        collections = capsule['original_exposures'][probe['shard']]['collections']
        collection = next(entry for entry in collections if entry['master'] == probe['master'])
        assert collection['world'] == probe['world']
        probes.append(dict(shard=probe['shard'], master=probe['master'], collection=collection))
    assert len(probes) == 16
    write(output / 'ROUTE_COHORT.json', dict(probes=probes, conditions=['OWN_TEXT', 'UNAVAILABLE'],
        tasks_per_world=4, max_calls=768, no_outcomes_read=True,
        origin='Exact SEQ266 reserved PROBE worlds and actual child text stores; new process/readout, not novel worlds.'))
    write(output / 'PACKET/ADMITTED_ROWS.json', rows)
    write(output / 'CORPUS_MANIFEST.json', dict(schema='COMBINED_L1_FROZEN_EXISTING_CORPORA_V1',
        counts=counts, rows=len(rows), duplicates=duplicates, other_sources=sources,
        seq266_sha256=SEQ_SHA, capsule_sha256=CAPSULE_SHA, entire_math764_sha256=MATH_SHA,
        packet_sha256=sha(output / 'PACKET/ADMITTED_ROWS.json'),
        math_cohort_sha256=sha(output / 'COHORT.json'), route_cohort_sha256=sha(output / 'ROUTE_COHORT.json'),
        math_tasks=len(training_math), row_presentations=16, updates=(12 + len(rows)) * 8,
        qualification='Already admitted only; no new review or filtering beyond exact-target duplicate exclusion for additions.',
        order='Preserve all1452 SEQ266 rows including repeated commands in distinct contexts; then entire764; then named canonical admitted sources in listed order.',
        new_generation=0, outcomes_used_for_selection=False, semantic_selection=False,
        other_source_lineages='Mixed previously qualified child lineages; all new fits independently reset37ec.',
        files={str(path.relative_to(output)): sha(path) for path in output.rglob('*.json')
            if path.name != 'CORPUS_MANIFEST.json'}))
    print(json.dumps(dict(counts=counts, rows=len(rows), updates=(12 + len(rows)) * 8,
        duplicates=len(duplicates), manifest_sha256=sha(output / 'CORPUS_MANIFEST.json'),
        packet_sha256=sha(output / 'PACKET/ADMITTED_ROWS.json')), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--repository', type=Path, default=Path.cwd())
    options = parser.parse_args()
    freeze(options.repository.resolve(), options.root.resolve())
