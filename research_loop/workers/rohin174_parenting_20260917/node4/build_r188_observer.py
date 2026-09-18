"""Forward the read-only NODE4 observer to actual R188 recovery receipts."""

import ast
import hashlib
import json
from pathlib import Path


HOME = Path(__file__).resolve().parent
ORIGINAL_SHA = 'a8a87ccd82c8030b5e30b4bdaab5a124f397116300dc8ba6cd1539127ea9f838'


def patch(original):
    if hashlib.sha256(original.encode()).hexdigest() != ORIGINAL_SHA:
        raise ValueError('exact_existing_readonly_observer')
    replacements = (
        ("        loaded = None\n", "        if physical in (0, 1):\n"
         "            successor = Path('/localhome/local-rohing/orch_r188_node4_20260917t2315z') / ('recovery0_attempt2' if physical == 0 else 'recovery1')\n"
         "        loaded = None\n"),
        ("loaded['status'] == 'EXACT_SAVED_SUCCESSOR_LOADED'",
         "loaded['status'] == ('R188_SAVED_MODEL_LOADED' if physical in (0, 1) else 'EXACT_SAVED_SUCCESSOR_LOADED')"),
        ("        require(polled['snapshot']['caught_up'], 'bounded_cursor_caught_up')\n",
         "        for cursor_step in range(7):\n"
         "            if polled['snapshot']['caught_up']:\n"
         "                break\n"
         "            cursor = polled['cursor']\n"
         "            polled = snapshots.poll(root, cursor, cursor_sha256=snapshots._digest(cursor))\n"
         "        require(polled['snapshot']['caught_up'], 'bounded_cursor_caught_up')\n"),
        ("schema='NODE4_R178_READ_ONLY_ACTUAL_STATUS_V1'", "schema='NODE4_R188_READ_ONLY_ACTUAL_STATUS_V1'"),
    )
    source = original
    for before, after in replacements:
        if source.count(before) != 1:
            raise ValueError('one_exact_readonly_observer_seam')
        source = source.replace(before, after)
    previous = {node.name: ast.dump(node) for node in ast.parse(original).body if isinstance(node, ast.FunctionDef)}
    current = {node.name: ast.dump(node) for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}
    if previous.keys() != current.keys() or any(previous[name] != current[name]
            for name in previous if name != 'collect_remote'):
        raise ValueError('unchanged_observer_identity_cursor_and_read_contract')
    return source


def build():
    source = patch((HOME / 'r185_node4_status.py').read_text())
    output = HOME / 'r188_node4_status_v2.py'
    with output.open('x') as stream:
        stream.write(source)
    return dict(source=str(output), sha256=hashlib.sha256(source.encode()).hexdigest(),
        old_source_unchanged=True, journal_writes=0, native_signals=0, provider_calls=0)


if __name__ == '__main__':
    print(json.dumps(build(), sort_keys=True))
