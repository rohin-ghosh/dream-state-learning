"""Move only observer cursor inputs to the four R184 parent successors."""

import ast
import hashlib
import json
from pathlib import Path


HOME = Path(__file__).resolve().parent


def build():
    original = (HOME / 'r181_journal_status.py').read_text()
    before = "        parent_path = HOME / f'activation_20260917T2057Z/physical{physical}/parent'\n        if physical == 1:\n            parent_path = HOME / 'activation_r178_20260917T2148Z/physical1/parent'"
    after = "        parent_path = HOME / f'activation_r184_20260917T2248Z/physical{physical}/parent'"
    if original.count(before) != 1:
        raise ValueError('one_exact_existing_cursor_input')
    source = original.replace(before, after)
    old_functions = {node.name: ast.dump(node) for node in ast.parse(original).body if isinstance(node, ast.FunctionDef)}
    new_functions = {node.name: ast.dump(node) for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}
    if set(old_functions) != set(new_functions) or any(old_functions[name] != new_functions[name]
            for name in old_functions if name != 'collect'):
        raise ValueError('unchanged_native_and_REQUEST_observation')
    output = HOME / 'r185_node4_status.py'
    with output.open('x') as stream:
        stream.write(source)
    return dict(source=str(output), sha256=hashlib.sha256(source.encode()).hexdigest(),
        old_source_unchanged=True, journal_writes=0, native_signals=0, provider_calls=0)


if __name__ == '__main__':
    print(json.dumps(build(), sort_keys=True))
