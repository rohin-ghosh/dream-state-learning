"""Package exact model-loader dependencies and owned source without old results."""

import argparse
import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import tarfile

from organism_v6 import orch_math_replication as policy


def source_closure(root, initial):
    discovered = set(initial)
    pending = list(initial)
    while pending:
        relative = pending.pop()
        if not relative.endswith('.py'):
            continue
        tree = ast.parse((root / relative).read_text(), filename=relative)
        modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
                modules.extend(node.module + '.' + alias.name for alias in node.names)
        for module in modules:
            if not module.startswith(('gpu.', 'organism_v6.')) and module not in ('gpu', 'organism_v6'):
                continue
            path = Path(*module.split('.')).with_suffix('.py')
            if not (root / path).is_file():
                path = Path(*module.split('.')) / '__init__.py'
            name = path.as_posix()
            if (root / path).is_file() and name not in discovered:
                discovered.add(name)
                pending.append(name)
    return sorted(discovered)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    options = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    provenance = json.loads((options.evidence / 'CPU_PROVENANCE.json').read_text())
    initial = set(provenance['imported_sources'])
    for pattern in ('gpu/orch_math_replication*.py', 'organism_v6/orch_math_replication*.py',
                    'tests/test_orch_math_replication*.py'):
        initial.update(path.relative_to(root).as_posix() for path in root.glob(pattern))
    source_files = source_closure(root, initial)
    inventory = {name: policy.sha256(root / name) for name in source_files}
    for name, expected in provenance['imported_sources'].items():
        if inventory[name] != expected:
            raise ValueError('source_changed_since_cpu_preparation:' + name)
    policy.write(options.evidence / 'SOURCE_SHA256.json', inventory)
    with tarfile.open(options.archive, 'x') as archive:
        for name in source_files:
            archive.add(root / name, arcname=name, recursive=False)
    with tarfile.open(options.archive) as archive:
        for member in archive:
            if not member.isfile():
                raise ValueError('non_source_archive_member')
            import hashlib
            if hashlib.sha256(archive.extractfile(member).read()).hexdigest() != inventory[member.name]:
                raise ValueError('archive_source_mismatch')
    policy.write(options.evidence / 'SOURCE_ARCHIVE.json', dict(
        created_utc=datetime.now(timezone.utc).isoformat(), files=len(source_files),
        archive_sha256=policy.sha256(options.archive),
        inventory_sha256=policy.sha256(options.evidence / 'SOURCE_SHA256.json'),
        public_dataset_sha256=policy.DATA_SHA256,
        cohort_sha256=policy.sha256(options.evidence / 'TASKS.json'),
        protocol_sha256=policy.sha256(root / 'research_notes/analysis/orch_math_replication_20260914_protocol.md'),
        cpu_tests_sha256=policy.sha256(options.evidence / 'CPU_TESTS.txt'),
        outcome_exposure=False, native_calls=0, pre_gpu_gate_complete=False))
    print(json.dumps(dict(source_files=len(source_files), archive_sha256=policy.sha256(options.archive))))


if __name__ == '__main__':
    main()
