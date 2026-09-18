"""Freeze readout tasks, existing qualification and legacy inputs; no model."""

import argparse
import json
from pathlib import Path
import shutil

from gpu.orch_l2_rich_math_bootstrap import read, sha, write
from organism_v6 import orch_l1_bootstrap_transfer as transfer
from organism_v6 import orch_rich_breadth_bootstrap as policy


def freeze(repository, output):
    assert not output.exists(), 'preserve_existing_attempt'
    packet = repository / 'research_notes/analysis/orch_rich_intensity_20260915_bootstrap26_v1'
    source = repository / 'gpu_artifacts_local/orch_math_rich_20260914_attempt1/gsm8k_train.jsonl'
    assert sha(source) == transfer.SOURCE_SHA
    expected = {'FIRST16.json': policy.FIRST_SHA, 'ADDITIONAL10.json': policy.ADDITIONAL_SHA,
        'COMBINED26.json': policy.COMBINED_SHA, 'MANIFEST.json': policy.MANIFEST_SHA}
    assert all(sha(packet / name) == digest for name, digest in expected.items())
    manifest = read(packet / 'MANIFEST.json')
    assert all(sha(packet / name) == entry['sha256'] for name, entry in manifest['files'].items())
    policy.validate_packets(*(read(packet / name) for name in ('FIRST16.json', 'ADDITIONAL10.json', 'COMBINED26.json')))
    names = {'TASKS.json', 'TASKS_VIEW.json', 'COHORT.json', 'ROSTER.json', 'PANEL_TASKS.json', 'TASK_MEMBERSHIP.json'}
    paths = sorted({path for directory in ('research_notes/analysis', 'gpu_artifacts_local')
        for path in (repository / directory).rglob('*.json')
        if path.name in names and not any(part.startswith('source') for part in path.parts)})
    anscombe = repository / 'research_notes/analysis/orch_l1_bootstrap_transfer_20260915_attempt1/COHORT.json'
    assert anscombe in paths and sha(anscombe) == '3530b667828373408ec6de97f9080c9c1e7a692ee617a90930ce8a9aa1adcbe4'
    hashes = {str(path.relative_to(repository)): sha(path) for path in paths}
    documents = [read(path) for path in paths] + [read(packet / 'COMBINED26.json')]
    document = policy.cohort((json.loads(line) for line in source.read_text().splitlines()), documents)
    assert not {task['id'] for task in document['tasks']} & {task['id'] for task in read(anscombe)['tasks']}
    assert all(sha(repository / name) == digest for name, digest in hashes.items()), 'roster_changed_during_freeze'
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(packet, output / 'PACKET')
    prior = repository / 'research_notes/analysis/orch_l2_rich_math_20260915_attempt1'
    prior_prepared = read(prior / 'PREPARE.json')
    for name in ('LEGACY_MATERIAL.json', 'OLD_MASKS.json', 'LEGACY_READOUT.json'):
        assert sha(prior / name) == prior_prepared['files'][name]
        shutil.copyfile(prior / name, output / name)
    write(output / 'COHORT.json', document)
    write(output / 'DATA_PROVENANCE.json', dict(source_path=str(source.relative_to(repository)),
        source_sha256=sha(source), roster_files=hashes, roster_count=len(paths),
        anscombe_roster_sha256=sha(anscombe), anscombe_outcomes_read=False,
        packet_files=expected, cohort_sha256=sha(output / 'COHORT.json'),
        legacy_files={name: sha(output / name) for name in ('LEGACY_MATERIAL.json', 'OLD_MASKS.json', 'LEGACY_READOUT.json')},
        source_reasoning_exported=False, native_calls=0, pretraining_contamination_unknown=True,
        qualification='Existing author-only PASS, not independent certification; no new admission.',
        freshness='Public cached GSM8K; excludes prior registered rosters by ID and normalized question.'))
    print(json.dumps(dict(cohort_sha256=sha(output / 'COHORT.json'),
        provenance_sha256=sha(output / 'DATA_PROVENANCE.json'), roster_count=len(paths),
        pools=document['pool_counts'], excluded_ids=len(document['excluded_ids'])), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    freeze(options.repository.resolve(), options.output.resolve())
