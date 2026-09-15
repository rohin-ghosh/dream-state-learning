"""Bind Main's admitted incremental packet without re-admission or target edits."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from gpu import orch_combined_l1_run as combined
from gpu.orch_l2_rich_math_bootstrap import read, sha
from organism_v6 import orch_combined_l1_continual as policy


def exclusion_inventory(repository, root):
    paths = [root / 'COHORT.json',
        repository / 'research_notes/analysis/orch_l1_bootstrap_transfer_20260915_attempt1/COHORT.json',
        repository / 'research_notes/analysis/orch_rich_breadth_bootstrap_20260915_attempt1/COHORT.json']
    tasks, sources = [], {}
    for path in paths:
        if path.exists():
            document = read(path)
            tasks.extend(document['tasks'])
            sources[str(path)] = sha(path)
    questions = set()
    for task in tasks:
        questions.add(hashlib.sha256(task['question'].encode()).hexdigest())
        questions.add(hashlib.sha256(' '.join(task['question'].split()).encode()).hexdigest())
        if task.get('question_sha256'):
            questions.add(task['question_sha256'])
    routes = []
    for probe in read(root / 'ROUTE_COHORT.json')['probes']:
        routes.extend(combined.route.goal.identifiers(probe['collection']['world']))
    return dict(held_math=sorted({task['id'] for task in tasks}), held_question_hashes=sorted(questions),
                held_route=sorted(set(routes)), sources=sources, outcomes_inspected=False)


def bind(repository, root, manifest_path):
    manifest = read(manifest_path)
    assert manifest['schema'] == 'ORCH_CONTINUAL_BATCH_V1'
    assert manifest['encoding'] == 'math'
    assert manifest['admission_mode'] == 'INDIVIDUAL_EXISTING_AUTHOR_FULLTEXT_REVIEW'
    assert manifest['individual_semantic_status'] == 'PASS'
    assert (manifest.get('origin') == 'EXTERNAL_GENERATION' or
            manifest['batch_id'] == 'math_final_review_delta76_20260915'), 'external_generation_origin_required'
    assert not manifest.get('parenting_or_l2_experience', False)
    rows_path = manifest_path.parent / manifest['rows_path']
    assert rows_path.resolve().parent == manifest_path.parent.resolve()
    assert sha(rows_path) == manifest['rows_sha256']
    rows = read(rows_path)
    assert len(rows) == manifest['row_count']
    assert [row['target_sha256'] for row in rows] == manifest['target_sha256s']
    source_pins = {}
    for field in ('expanded_packet', 'prior_packet', 'source_native_archive'):
        source = repository / manifest[field + '_path']
        assert source.is_file() and sha(source) == manifest[field + '_sha256']
        source_pins[str(source.relative_to(repository))] = sha(source)
    prior = read(repository / manifest['prior_packet_path'])
    expanded = read(repository / manifest['expanded_packet_path'])
    assert len(prior) == manifest['previous_rows_unchanged']
    prior_by_hash = {row['target_sha256']: row for row in prior}
    expanded_by_hash = {row['target_sha256']: row for row in expanded}
    assert len(prior_by_hash) == len(prior) and len(expanded_by_hash) == len(expanded)
    assert all(expanded_by_hash.get(key) == row for key, row in prior_by_hash.items())
    assert {key: row for key, row in expanded_by_hash.items() if key not in prior_by_hash} == {
        row['target_sha256']: row for row in rows}
    wrappers = [dict(corpus=manifest['batch_id'], index=index, encoding='math', row=row,
                     target_sha256=row['target_sha256']) for index, row in enumerate(rows)]
    packet = dict(schema='COMBINED_CONTINUAL_ADMITTED_BATCH_V1', batch_id=manifest['batch_id'],
        origin='EXTERNAL_GENERATION', parenting_or_l2_experience=False,
        author_qualified=True, rows=wrappers, rows_sha256=policy.digest(wrappers),
        provenance=dict(manifest_sha256=sha(manifest_path), rows_file_sha256=sha(rows_path),
                        original_manifest=manifest, verified_source_pins=source_pins))
    exclusions = exclusion_inventory(repository, root)
    state = policy.initial_state(read(root / 'PACKET/ADMITTED_ROWS.json'), combined.MANIFEST_SHA)
    checked = policy.append_batch(state, packet, **{key: exclusions[key]
        for key in ('held_math', 'held_route', 'held_question_hashes')})
    destination = root / 'INBOX' / manifest['batch_id']
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(manifest_path, destination / 'MANIFEST.json')
    shutil.copyfile(rows_path, destination / 'ROWS.json')
    policy.atomic_json(destination / 'EXCLUSIONS.json', exclusions)
    policy.atomic_json(destination / 'BOUND_PACKET.json', packet)
    policy.atomic_json(destination / 'CPU_BOUND.json', dict(status='PASS', model_loaded=False,
        native_calls=0, manifest_sha256=sha(destination / 'MANIFEST.json'),
        rows_sha256=sha(destination / 'ROWS.json'), packet_sha256=sha(destination / 'BOUND_PACKET.json'),
        exclusions_sha256=sha(destination / 'EXCLUSIONS.json'),
        accepted=checked['ingested'][-1]['added'], deduplicated=len(checked['duplicates']),
        queued_not_training=True))
    print(json.dumps(read(destination / 'CPU_BOUND.json'), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, default=Path.cwd())
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    options = parser.parse_args()
    bind(options.repository.resolve(), options.root.resolve(), options.manifest.resolve())
