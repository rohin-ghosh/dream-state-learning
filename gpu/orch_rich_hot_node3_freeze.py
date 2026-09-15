"""Freeze a new isolated treatment of the cached original TRAIN cohort."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tarfile

from gpu.orch_math_rich_screen import write
from gpu.orch_rich_hot_node3_run import sha
from organism_v6 import orch_math_rich as original
from organism_v6 import orch_rich_hot_node3 as policy
from organism_v6 import orch_rich_intensity as prior


def freeze(root):
    roster = Path('research_notes/analysis/orch_rich_intensity_20260915_attempt1/TASKS.json')
    provenance_path = roster.with_name('DATA_PROVENANCE.json')
    provenance = json.loads(provenance_path.read_text())
    assert sha(roster) == policy.TASKS_SHA == provenance['tasks_sha256']
    source = Path(provenance['source_path'])
    assert sha(source) == provenance['source_sha256']
    document = json.loads(roster.read_text())
    prior.validate(document)
    records = [json.loads(line) for line in source.read_text().splitlines()]
    for task in document['tasks']:
        source_row = records[int(task['id'].rsplit('-', 1)[1])]
        assert source_row['question'].strip() == task['question']
        assert original.number(source_row['answer'].rsplit('####', 1)[1]) == original.number(task['gold'])
    for path, expected in provenance['prior_manifests'].items():
        assert sha(path) == expected
    root.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(roster, root / 'TASKS.json')
    write(root / 'PROTOCOL.json', policy.protocol())
    write(root / 'PROVENANCE.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sha(source), source_path=str(source), source_rows=len(records),
        reused_train_tasks=256, all_question_and_numeric_gold_joins_verified=True,
        prior_provenance_sha256=sha(provenance_path), prior_provenance=provenance,
        old_roots_readonly=True, cached_only=True, external_answers_in_prompts=False,
        original_outcomes_preserved=True, no_held_tasks=True))
    inventory = {}
    for directory in ('gpu', 'organism_v6', 'research_loop'):
        for path in sorted(Path(directory).rglob('*')):
            if path.suffix not in ('.py', '.sh') or not path.is_file():
                continue
            target = root / 'source' / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            inventory[str(path)] = sha(target)
    test_path = Path('tests/test_orch_rich_hot_node3.py')
    target = root / 'source' / test_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(test_path, target)
    inventory[str(test_path)] = sha(target)
    write(root / 'SOURCE_SHA256.json', inventory)
    with tarfile.open(root / 'source.tar', 'w') as archive:
        for relative in inventory:
            archive.add(root / 'source' / relative, arcname='source/' + relative)
    write(root / 'FREEZE.json', dict(protocol_sha256=sha(root / 'PROTOCOL.json'),
        provenance_sha256=sha(root / 'PROVENANCE.json'), tasks_sha256=sha(root / 'TASKS.json'),
        source_sha256=sha(root / 'SOURCE_SHA256.json'), source_archive_sha256=sha(root / 'source.tar'),
        source_files=len(inventory), native_calls=0, fits=0, updates=0))
    print(json.dumps(json.loads((root / 'FREEZE.json').read_text()), sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    freeze(parser.parse_args().root)
