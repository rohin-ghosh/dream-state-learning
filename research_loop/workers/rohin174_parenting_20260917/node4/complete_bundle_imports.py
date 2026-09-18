"""Pin unchanged repository-local transitive imports omitted by the arm builder."""

import argparse
import ast
import hashlib
import json
from pathlib import Path


def local_imports(raw, repository):
    names = set()
    for node in ast.walk(ast.parse(raw)):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module)
            names.update(node.module + '.' + alias.name for alias in node.names if alias.name != '*')
    result = set()
    for name in names:
        if name.split('.')[0] not in ('gpu', 'organism_v6'):
            continue
        path = Path(*name.split('.')).with_suffix('.py')
        if (repository / path).is_file():
            result.add(str(path))
    return result


def complete(repository, source):
    repository, source = Path(repository).resolve(), Path(source).resolve()
    manifest = json.loads((source / 'ARM_BUNDLE.json').read_text())
    pending = list(manifest['files'])
    visited = set()
    additions = {}
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        if len(visited) > 400:
            raise ValueError('bounded_transitive_dependency_closure')
        target = source / name
        if not target.exists():
            original = repository / name
            if original.is_symlink() or original.stat().st_size > 16 * 1024 * 1024:
                raise ValueError('bounded_regular_dependency')
            raw = original.read_bytes()
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as output:
                output.write(raw)
            target.chmod(0o444)
            additions[name] = hashlib.sha256(raw).hexdigest()
        pending.extend(local_imports(target.read_bytes(), repository) - visited)
    receipt = dict(schema='R175_NODE4_UNCHANGED_IMPORT_CLOSURE_V1', files=additions,
        original_arm_bundle_sha256=hashlib.sha256((source/'ARM_BUNDLE.json').read_bytes()).hexdigest(),
        changed_existing_files=0, provider_or_model_calls=0)
    with (source/'SUPPORT_SOURCE_MANIFEST.json').open('x') as output:
        json.dump(receipt, output, indent=2, sort_keys=True)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    options = parser.parse_args()
    print(json.dumps(complete(options.repository, options.source), sort_keys=True))
