"""Build the next read-only observer without mutating the running collector."""

import ast
import hashlib
from pathlib import Path


HOME = Path(__file__).resolve().parent


def build():
    original = (HOME / 'r178_node4_status.py').read_text()
    source = original.replace('PENDING_MAIN_R178_PRESERVATION', 'R178_B_AFTER_ORIGINAL_BASELINE')
    source = source.replace('orch_r179_node4_r181_20260917t2150z',
        'orch_r179_node4_r181journal_20260917t2220z')
    source = source.replace("        if (successor / 'LOADED_RECEIPT.json').exists():",
        "        loaded = None\n        if (successor / 'LOADED_RECEIPT.json').exists():")
    source = source.replace('        head = update = last_sleep = last_retained = None',
        '        head = update = last_sleep = last_retained = last_recipe = None')
    source = source.replace("            elif kind == 'CONTEXT_RETAINED':",
        "            elif kind == 'SLEEP_RECIPE':\n"
        "                last_recipe = dict(evidence, metadata={key: document[key] for key in\n"
        "                    ('policy', 'new_presentations', 'new_rows', 'available_old_rows',\n"
        "                     'selected_old_rows', 'anchor_lambda') if key in document})\n"
        "            elif kind == 'CONTEXT_RETAINED':")
    source = source.replace('            latest_sleep_complete=last_sleep, latest_context_retained=last_retained, messages=messages,',
        "            latest_sleep_complete=last_sleep, latest_context_retained=last_retained, messages=messages,\n"
        "            actual_R181_loaded=loaded, latest_sleep_recipe=last_recipe,\n"
        "            current_journal_sha256=sha(stage / 'source/gpu/orch_r125_stream_journal.py'),\n")
    tree = ast.parse(source)
    before = {node.name: ast.dump(node) for node in ast.parse(original).body if isinstance(node, ast.FunctionDef)}
    after = {node.name: ast.dump(node) for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert set(before) == set(after)
    assert all(before[name] == after[name] for name in before if name != 'collect_remote')
    output = HOME / 'r181_journal_status.py'
    with output.open('x') as stream:
        stream.write(source)
    return dict(path=str(output), sha256=hashlib.sha256(source.encode()).hexdigest(),
        direct_native_signals=0, provider_calls=0, predecessor_changed=False)


if __name__ == '__main__':
    import json
    print(json.dumps(build(), sort_keys=True))
