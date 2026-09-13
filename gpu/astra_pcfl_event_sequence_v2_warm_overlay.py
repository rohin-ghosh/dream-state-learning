"""Build a fresh validation-only overlay without modifying acquisition sources."""

import argparse
import ast
import hashlib
import json
from pathlib import Path


SOURCE = Path('/tmp/astra_pcfl_sequence_v2_source_20260913_attempt2')
DESTINATION = Path('/tmp/astra_pcfl_sequence_v2_source_20260913_warmfix4')
RELATIVE = Path('gpu/astra_pcfl_event_sequence_v2_fit.py')
OUTER = Path('gpu/astra_pcfl_event_sequence_v2_outer.py')
ORIGINAL_SHA = '4112899215ded5191b697cad9bf912bb72a65b026779f3d6dbbd548b36d0aa19'
OUTER_ORIGINAL_SHA = '88eb6775f481c02b9888ebdc17e3db49d6fc388a50ff35f94231d76693828360'
SCOPE = 'warm_receipt_and_readonly_predecessor_split'


def pin(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def validate_repair(original, replacement, *, outer=False):
    texts = [Path(path).read_text() for path in (original, replacement)]
    trees = [ast.parse(text) for text in texts]
    functions = [{node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)} for tree in trees]
    allowed = ('_inputs', 'controller') if outer else ('validate_warm_tensors', 'validate_predecessor', 'run_phase')
    for tree, mapping in zip(trees, functions):
        for name in allowed:
            if sum(isinstance(node, ast.FunctionDef) and node.name == name for node in tree.body) != 1:
                raise ValueError('exact scoped functions required')
    if outer:
        if ast.get_source_segment(texts[0], functions[0]['_inputs']) != ast.get_source_segment(texts[1], functions[1]['_inputs']):
            raise ValueError('read-only _inputs bytes changed')
        wrappers = [node for node in trees[1].body if isinstance(node, ast.FunctionDef) and node.name == '_inputs_for_write']
        if len(wrappers) != 1 or '_inputs_for_write' in functions[0]:
            raise ValueError('exact new outer write wrapper required')
        expected = ast.parse('''def _inputs_for_write(inputs_path, inputs_sha256, allocation_path, allocation_sha256, outer_sha256, phase, deadline, *, stage="fit", state=None, output=None):
    inputs, allocation, material = _inputs(inputs_path, inputs_sha256, allocation_path, allocation_sha256,
                                         outer_sha256, phase, deadline, stage=stage, state=state, output=output)
    if stage == "fit":
        config = fit.sequence.training_config(phase, inputs["model_path"], learner_seed=inputs["learner_seed"], device="cuda")
        fit.validate_predecessor_for_write(inputs, material, phase, output, config, "NATIVE")
    return inputs, allocation, material
''').body[0]
        if ast.dump(wrappers[0]) != ast.dump(expected):
            raise ValueError('outer write wrapper differs from exact boundary')
        trees[1].body.remove(wrappers[0])
        calls = sorted((node for node in ast.walk(functions[1]['controller']) if isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name) and node.func.id in ('_inputs', '_inputs_for_write')),
                       key=lambda node: (node.lineno, node.col_offset))
        if [node.func.id for node in calls] != ['_inputs_for_write', '_inputs_for_write', '_inputs']:
            raise ValueError('only first two controller prefit calls may change; postflight must stay read-only')
        for node in calls[:2]:
            node.func.id = '_inputs'
        if ast.dump(trees[0]) != ast.dump(trees[1]):
            raise ValueError('non-validator change outside explicit AST boundaries')
        return
    if not outer:
        wrappers = [node for node in trees[1].body if isinstance(node, ast.FunctionDef)
                    and node.name == 'validate_predecessor_for_write']
        if len(wrappers) != 1 or 'validate_predecessor_for_write' in functions[0]:
            raise ValueError('exact new write wrapper required')
        wrapper = wrappers[0]
        if isinstance(wrapper.body[0], ast.Expr) and isinstance(wrapper.body[0].value, ast.Constant) and isinstance(wrapper.body[0].value.value, str):
            wrapper.body.pop(0)
        expected = ast.parse('''def validate_predecessor_for_write(inputs, material, phase, root, config, kind):
    parent, prior, before = validate_predecessor(inputs, material, phase, root, config, kind)
    if parent is not None:
        v3._warm_parent(parent, root / "checkpoint", config)
    return parent, prior, before
''').body[0]
        if ast.dump(wrapper) != ast.dump(expected):
            raise ValueError('write wrapper differs from exact boundary')
        trees[1].body.remove(wrapper)
        if any(isinstance(node, ast.Attribute) and node.attr == '_warm_parent'
               or isinstance(node, ast.Name) and node.id == '_warm_parent'
               for node in ast.walk(functions[1]['validate_predecessor'])):
            raise ValueError('read-only predecessor must not call warm preparation')
        for mapping in functions:
            for name in ('validate_warm_tensors', 'validate_predecessor'):
                mapping[name].body = [ast.Pass()]
    caller = functions[1]['run_phase']
    calls = [node.func for node in ast.walk(caller) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == 'validate_predecessor_for_write']
    if len(calls) != 1:
        raise ValueError('exact single prefit call rename required')
    calls[0].id = 'validate_predecessor'
    if ast.dump(trees[0]) != ast.dump(trees[1]):
        raise ValueError('non-validator change outside explicit AST boundaries')


def build(replacement, commit, outer_replacement):
    if len(commit) != 40 or any(character not in '0123456789abcdef' for character in commit):
        raise ValueError('full committed repair revision required')
    if not SOURCE.is_dir() or SOURCE.resolve() != SOURCE or DESTINATION.exists() or DESTINATION.is_symlink():
        raise ValueError('immutable original and fresh overlay required')
    original = pin(SOURCE / RELATIVE)
    if original['sha256'] != ORIGINAL_SHA:
        raise ValueError('original frozen fit drift')
    outer_original = pin(SOURCE / OUTER)
    if outer_original['sha256'] != OUTER_ORIGINAL_SHA:
        raise ValueError('original frozen outer drift')
    replacement = Path(replacement).resolve()
    outer_replacement = Path(outer_replacement).resolve()
    replacements = {str(RELATIVE): pin(replacement), str(OUTER): pin(outer_replacement)}
    validate_repair(SOURCE / RELATIVE, replacement)
    validate_repair(SOURCE / OUTER, outer_replacement, outer=True)
    original_inventory = {str(path.relative_to(SOURCE)): pin(path) for path in SOURCE.rglob('*')
                          if path.is_file() and '__pycache__' not in path.parts}
    DESTINATION.mkdir()
    for relative, binding in original_inventory.items():
        target = DESTINATION / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative in replacements:
            with target.open('xb') as stream:
                stream.write(Path(replacements[relative]['path']).read_bytes())
        else:
            target.symlink_to(binding['path'])
    if any(pin(binding['path']) != binding for binding in original_inventory.values()):
        raise ValueError('original source changed during preparation')
    if any(pin(DESTINATION / relative)['sha256'] != binding['sha256'] for relative, binding in replacements.items()):
        raise ValueError('replacement source changed during preparation')
    receipt = dict(schema='pcfl.event_sequence.v2.warm_repair.v1', original_root=str(SOURCE),
                   source_root=str(DESTINATION), original=original, replacement=pin(DESTINATION / RELATIVE),
                   outer_original=outer_original, outer_replacement=pin(DESTINATION / OUTER),
                   scope=SCOPE, repair_commit=commit,
                   original_inventory=original_inventory, material_reexported=False, original_modified=False)
    with (DESTINATION / 'warm_repair.json').open('x') as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
        stream.write('\n')
    return pin(DESTINATION / 'warm_repair.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replacement', required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--outer-replacement', required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.replacement, args.commit, args.outer_replacement), sort_keys=True))


if __name__ == '__main__':
    main()
