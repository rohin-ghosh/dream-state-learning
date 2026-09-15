"""Freeze the common intensity/two-pass roster from the existing cached source."""

from collections import Counter
import hashlib
import json
from pathlib import Path

from organism_v6 import orch_math_rich as original

SOURCE_SHA = '17f347dc51477c50d4efb83959dbb7c56297aba886e5544ee2aaed3024813465'
DESTINATION = Path('research_notes/analysis/orch_rich_intensity_20260915_attempt1')
SEED = 'RICH_INTENSITY_COMMON_V1_20260915'


def freeze():
    source = Path('gpu_artifacts_local/orch_math_rich_20260914_attempt1/gsm8k_train.jsonl')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA
    paths = [Path('gpu_artifacts_local/orch_math_rich_20260914_attempt1/TASKS.json'),
             Path('research_notes/analysis/orch_math_record_20260914_attempt1/TASKS.json'),
             Path('research_notes/analysis/orch_math_replication_20260914_attempt1/TASKS.json'),
             Path('research_notes/analysis/orch_math_scale_20260914_attempt1/TASKS.json')]
    excluded = []
    for path in paths:
        document = json.loads(path.read_text())
        excluded.extend(document['tasks'])
        excluded.extend(document.get('held_tasks', []))
    ids = {task['id'] for task in excluded}
    hashes = {original.digest(' '.join(task['question'].lower().split())) for task in excluded}
    assert len(ids) == len(hashes) == 1216
    pools = {family: [] for family in original.MINING}
    seen = set(hashes)
    for index, line in enumerate(source.read_text().splitlines()):
        record = json.loads(line)
        question = record['question'].strip()
        identity = original.digest(' '.join(question.lower().split()))
        task_id = f'gsm8k-train-{index}'
        family = original.family(question)
        if task_id in ids or identity in seen or family not in pools:
            continue
        seen.add(identity)
        pools[family].append(dict(id=task_id, question=question,
            question_sha256=identity, family=family,
            gold=str(original.number(record['answer'].rsplit('####', 1)[1]))))
    tasks = []
    for family, pool in pools.items():
        assert len(pool) >= 64, (family, len(pool))
        tasks.extend(sorted(pool, key=lambda task: original.digest(SEED + ':' + task['id']))[:64])
    assert Counter(task['family'] for task in tasks) == dict.fromkeys(original.MINING, 64)
    document = dict(tasks=tasks, denominator=256, per_family=64, seed=SEED,
        excluded_ids=sorted(ids), excluded_question_hashes=sorted(hashes),
        pool_counts={family: len(pool) for family, pool in pools.items()},
        maximum_calls=1536, no_l2_l3_access=True, fit_ready=False)
    DESTINATION.mkdir(parents=True, exist_ok=False)
    wire = DESTINATION / 'TASKS.json'
    wire.write_text(json.dumps(document, indent=2, ensure_ascii=False) + '\n')
    provenance = dict(source_path=str(source), source_sha256=SOURCE_SHA,
        tasks_path=str(wire), tasks_sha256=hashlib.sha256(wire.read_bytes()).hexdigest(),
        prior_manifests={str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
        excluded_distinct_ids=len(ids), excluded_distinct_question_hashes=len(hashes),
        normalized_question_hash='orch_math_rich.digest(lowercase whitespace-normalized question)',
        scope='Shared 256 fresh L1 tasks; TWO-PASS consumes exact bytes; no reference reasoning')
    (DESTINATION / 'DATA_PROVENANCE.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps(provenance, indent=2))


if __name__ == '__main__':
    freeze()
