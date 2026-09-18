"""Update only read-only cursor inputs after the three parent restarts."""

import ast
import hashlib
import json
from pathlib import Path


HOME = Path(__file__).resolve().parent


def build():
    original = (HOME / 'r188_node4_status_v2.py').read_text()
    if hashlib.sha256(original.encode()).hexdigest() != '7023471ca35b4ce0930b5722cac6d3efa9e778e66bacbe312097b3b17efdfa8f':
        raise ValueError('exact_previous_observer')
    before = "        parent_path = HOME / f'activation_r184_20260917T2248Z/physical{physical}/parent'"
    after = "        parent_path = HOME / ('activation_r184_20260917T2248Z' if physical == 1 else 'activation_r188_20260917T2339Z') / f'physical{physical}/parent'"
    if original.count(before) != 1:
        raise ValueError('one_exact_parent_cursor_input')
    source = original.replace(before, after)
    old_functions = {node.name: ast.dump(node) for node in ast.parse(original).body if isinstance(node, ast.FunctionDef)}
    new_functions = {node.name: ast.dump(node) for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}
    if old_functions.keys() != new_functions.keys() or any(old_functions[name] != new_functions[name]
            for name in old_functions if name != 'collect'):
        raise ValueError('unchanged_native_and_actual_render_checks')
    output = HOME / 'r188_node4_status_v3.py'
    with output.open('x') as stream:
        stream.write(source)
    return dict(path=str(output), sha256=hashlib.sha256(source.encode()).hexdigest(),
        child_signals=0, journal_writes=0, inbox_writes=0)


if __name__ == '__main__':
    print(json.dumps(build(), sort_keys=True))
