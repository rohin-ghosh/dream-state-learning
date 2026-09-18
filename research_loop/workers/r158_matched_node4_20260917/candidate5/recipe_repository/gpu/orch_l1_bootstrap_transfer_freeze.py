"""Freeze existing corpus manifests and task/prompt bytes without reading outcomes."""

import argparse
import json
from pathlib import Path

from gpu.orch_l2_rich_math_bootstrap import read, sha, write
from organism_v6 import orch_l1_bootstrap_transfer as policy


def freeze(repository, output):
    output.mkdir(parents=True, exist_ok=True)
    assert not any(output.iterdir()), 'preserve_existing_freeze'
    source = repository / 'gpu_artifacts_local/orch_math_rich_20260914_attempt1/gsm8k_train.jsonl'
    assert sha(source) == policy.SOURCE_SHA
    names = {'TASKS.json', 'TASKS_VIEW.json', 'COHORT.json', 'ROSTER.json'}
    paths = []
    for directory in ('research_notes/analysis', 'gpu_artifacts_local'):
        for path in (repository / directory).rglob('*.json'):
            if path.name in names and output not in path.parents and 'source' not in path.parts:
                paths.append(path)
    paths = sorted(set(paths))
    documents = [read(path) for path in paths]
    source_pilot = repository / 'research_notes/analysis/orch_l2_rich_math_20260915_attempt1'
    assert sha(source_pilot / 'ADMITTED.json') == policy.PACKET_SHA
    packet = read(source_pilot / 'ADMITTED.json')
    documents.append(packet)
    assert {row['family'] for row in packet} == set(policy.IN_FAMILIES)
    document = policy.cohort((json.loads(line) for line in source.read_text().splitlines()), documents)
    assert len([identity for identity in document['excluded_ids'] if identity.startswith('gsm8k-train-')]) >= 1472
    write(output / 'COHORT.json', document)
    write(output / 'DATA_PROVENANCE.json', dict(source_path=str(source.relative_to(repository)),
        source_sha256=sha(source), manifests={str(path.relative_to(repository)): sha(path) for path in paths},
        packet_sha256=policy.PACKET_SHA, cohort_sha256=sha(output / 'COHORT.json'),
        prospective=True, native_calls=0, results_read=False,
        pretraining_contamination_unknown=True,
        freshness='Excludes registered prior TRAIN/eval/collection IDs and normalized questions; not a pretraining-novelty claim.'))
    print(json.dumps(dict(cohort_sha256=sha(output / 'COHORT.json'), manifests=len(paths),
        excluded_ids=len(document['excluded_ids']), pools=document['pool_counts'],
        tasks=[task['id'] for task in document['tasks']]), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    freeze(options.repository.resolve(), options.output.resolve())
