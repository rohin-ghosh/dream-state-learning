"""Freeze local public questions without exporting reference reasoning."""

import hashlib
import json
from pathlib import Path

from gpu.orch_math_rich_screen import write
from organism_v6 import orch_math_scale as policy


def main():
    source = Path('gpu_artifacts_local/orch_math_rich_20260914_attempt1/gsm8k_train.jsonl')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == '17f347dc51477c50d4efb83959dbb7c56297aba886e5544ee2aaed3024813465'
    paths = [Path('gpu_artifacts_local/orch_math_rich_20260914_attempt1/TASKS.json'),
             Path('research_notes/analysis/orch_math_record_20260914_attempt1/TASKS.json'),
             Path('research_notes/analysis/orch_math_replication_20260914_attempt1/TASKS.json')]
    document = policy.build_tasks([json.loads(line) for line in source.read_text().splitlines()],
                                 [json.loads(path.read_text()) for path in paths])
    directory = Path('research_notes/analysis/orch_math_scale_20260914_attempt1')
    directory.mkdir(parents=True, exist_ok=False)
    write(directory / 'TASKS.json', document)
    write(directory / 'DATA_PROVENANCE.json', dict(source_path=str(source),
          source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
          prior_manifests={str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
          excluded_distinct_ids=len(document['excluded_ids']),
          excluded_distinct_question_hashes=len(document['excluded_question_hashes']),
          tasks_sha256=hashlib.sha256((directory / 'TASKS.json').read_bytes()).hexdigest(),
          scope='1024 mining +64 never-mined held L1; no L2/L3; no reference reasoning'))


if __name__ == '__main__':
    main()
