"""Build a fresh validation-only overlay without modifying acquisition sources."""

import argparse
import ast
import hashlib
import json
from pathlib import Path


SOURCE = Path('/tmp/astra_pcfl_sequence_v2_source_20260913_attempt2')
DESTINATION = Path('/tmp/astra_pcfl_sequence_v2_source_20260913_warmfix3')
RELATIVE = Path('gpu/astra_pcfl_event_sequence_v2_fit.py')
OUTER = Path('gpu/astra_pcfl_event_sequence_v2_outer.py')
ORIGINAL_SHA = '4112899215ded5191b697cad9bf912bb72a65b026779f3d6dbbd548b36d0aa19'


def pin(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def build(replacement, commit):
    if len(commit) != 40 or any(character not in '0123456789abcdef' for character in commit):
        raise ValueError('full committed repair revision required')
    if not SOURCE.is_dir() or SOURCE.resolve() != SOURCE or DESTINATION.exists() or DESTINATION.is_symlink():
        raise ValueError('immutable original and fresh overlay required')
    original = pin(SOURCE / RELATIVE)
    if original['sha256'] != ORIGINAL_SHA:
        raise ValueError('original frozen fit drift')
    replacement = Path(replacement).resolve()
    trees = [ast.parse(path.read_bytes()) for path in (SOURCE / RELATIVE, replacement)]
    for tree in trees:
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'validate_warm_tensors']
        if len(functions) != 1:
            raise ValueError('single validator required')
        functions[0].body = [ast.Pass()]
    if ast.dump(trees[0]) != ast.dump(trees[1]):
        raise ValueError('non-validator change refused')
    original_inventory = {str(path.relative_to(SOURCE)): pin(path) for path in SOURCE.rglob('*')
                          if path.is_file() and '__pycache__' not in path.parts}
    DESTINATION.mkdir()
    for relative, binding in original_inventory.items():
        target = DESTINATION / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative == str(RELATIVE):
            with target.open('xb') as stream:
                stream.write(replacement.read_bytes())
        elif relative == str(OUTER):
            with target.open('xb') as stream:
                stream.write(Path(binding['path']).read_bytes())
        else:
            target.symlink_to(binding['path'])
    if any(pin(binding['path']) != binding for binding in original_inventory.values()):
        raise ValueError('original source changed during preparation')
    receipt = dict(schema='pcfl.event_sequence.v2.warm_repair.v1', original_root=str(SOURCE),
                   source_root=str(DESTINATION), original=original, replacement=pin(DESTINATION / RELATIVE),
                   outer_original=pin(SOURCE / OUTER), outer_relocated=pin(DESTINATION / OUTER),
                   scope='validate_warm_tensors_only', repair_commit=commit,
                   original_inventory=original_inventory, material_reexported=False, original_modified=False)
    with (DESTINATION / 'warm_repair.json').open('x') as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
        stream.write('\n')
    return pin(DESTINATION / 'warm_repair.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replacement', required=True)
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.replacement, args.commit), sort_keys=True))


if __name__ == '__main__':
    main()
