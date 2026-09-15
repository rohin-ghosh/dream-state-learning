"""Snapshot local dependency bytes once; no edits to borrowed shared sources."""

import ast
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import tarfile


REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / 'research_notes/analysis/orch_rich_hot_a100_20260915_attempt1'


def main():
    pending = [Path('gpu/orch_rich_hot_a100_run.py'), Path('gpu/orch_rich_hot_a100_scan.py'),
               Path('tests/test_orch_rich_hot_a100.py')]
    selected = set()
    while pending:
        relative = pending.pop()
        if relative in selected or not (REPO / relative).is_file():
            continue
        selected.add(relative)
        for parent in relative.parents:
            if str(parent) != '.':
                pending.append(parent / '__init__.py')
        if relative.suffix != '.py':
            continue
        tree = ast.parse((REPO / relative).read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names = [node.module] + [node.module + '.' + alias.name for alias in node.names]
            for name in names:
                candidate = Path(*name.split('.'))
                pending.extend([candidate.with_suffix('.py'), candidate / '__init__.py'])
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.endswith('.sh'):
                pending.append(relative.parent / node.value)
    snapshot = ROOT / 'source'
    snapshot.mkdir(exist_ok=False)
    inventory = {}
    for relative in sorted(selected):
        data = (REPO / relative).read_bytes()
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        inventory[str(relative)] = hashlib.sha256(data).hexdigest()
    with (ROOT / 'source.tar').open('xb') as output:
        with tarfile.open(fileobj=output, mode='w') as archive:
            for relative in sorted(selected):
                archive.add(snapshot / relative, arcname=str(relative), recursive=False)
    (ROOT / 'SOURCE_INVENTORY.json').write_text(json.dumps(inventory, sort_keys=True, indent=2) + '\n')
    prior = REPO / 'research_notes/analysis/orch_rich_intensity_20260915_attempt1'
    for name in ('TASKS.json', 'DATA_PROVENANCE.json'):
        shutil.copyfile(prior / name, ROOT / name)
    shutil.copyfile(REPO / 'gpu_artifacts_local/orch_math_rich_20260914_attempt1/gsm8k_train.jsonl',
                    ROOT / 'gsm8k_train.jsonl')
    print(json.dumps(dict(source_files=len(selected), source_sha256=hashlib.sha256((ROOT / 'source.tar').read_bytes()).hexdigest())))


if __name__ == '__main__':
    main()
