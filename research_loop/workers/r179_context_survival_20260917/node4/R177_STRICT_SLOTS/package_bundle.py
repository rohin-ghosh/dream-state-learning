"""Copy exact existing scanner imports and wrapper bytes into a new receiving bundle."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def closure(repository, initial):
    pending = list(initial)
    found = set()
    while pending:
        relative = pending.pop()
        if relative in found or not (repository / relative).is_file():
            continue
        found.add(relative)
        tree = ast.parse((repository / relative).read_text())
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module, *[node.module + '.' + item.name for item in node.names]]
            for module in modules:
                pieces = module.split('.')
                pending.append(Path(*pieces).with_suffix('.py'))
                for length in range(1, len(pieces) + 1):
                    pending.append(Path(*pieces[:length]) / '__init__.py')
    return sorted(found)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--remote-root', required=True)
    options = parser.parse_args()
    destination = options.destination
    destination.mkdir()
    wrapper = Path(__file__).resolve().parent
    for name in ('slot_policy.py', 'test_slot_policy.py'):
        shutil.copyfile(wrapper / name, destination / name)
    originals = {}
    initial = [Path('gpu/orch_r111_route_admission.py')]
    for relative in closure(options.repository, initial):
        target = destination / 'scanner' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(options.repository / relative, target)
        originals[str(relative)] = sha(target)
    manifest = dict(schema='R177_NODE4_STRICT_SLOTS_BUNDLE_V1', remote_root=options.remote_root,
        python_files={str(path.relative_to(destination)): sha(path) for path in sorted(destination.rglob('*.py'))},
        unchanged_scanner_sources=originals, physical_allowlist=[2, 5], model_calls=0,
        author_scope='Rohin167 explicit Ampere2/Bacon5 allocation; non-material outer confinement')
    with (destination / 'BUNDLE.json').open('x') as stream:
        json.dump(manifest, stream, sort_keys=True, indent=2)
    print(json.dumps(dict(bundle_sha256=sha(destination / 'BUNDLE.json'), files=len(manifest['python_files']))))


if __name__ == '__main__':
    main()
