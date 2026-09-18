"""Main cache-method delta only; preserve each cohort's transition validators."""

import ast

from takeover import HERE, REPO, require, write, reference

METHODS = ('_file_identity', '_record_snapshot', '_reload_state', '_validated_state', 'audit')
REPLACED = ('record', 'latest_checkpoint', 'read_inbox')


def methods(source):
    journal = next(node for node in ast.parse(source).body if isinstance(node, ast.ClassDef) and node.name == 'StreamJournal')
    return {node.name: node for node in journal.body if isinstance(node, ast.FunctionDef)}


def text(source, node):
    start = min([node.lineno] + [decorator.lineno for decorator in node.decorator_list])
    return '\n'.join(source.splitlines()[start - 1:node.end_lineno])


def patch_journal(original, canonical):
    prior, current = methods(original), methods(canonical)
    require(not set(METHODS) & set(prior), 'cache_not_already_present')
    result = original
    for name in REPLACED:
        before = text(original, prior[name])
        require(result.count(before) == 1, 'one_original_method:' + name)
        result = result.replace(before, text(canonical, current[name]))
    init_before = text(original, prior['__init__'])
    require(init_before.count('            self._scan()') == 1, 'one_initial_full_scan')
    result = result.replace(init_before, init_before.replace('            self._scan()', '            self._state = self._reload_state()'))
    anchor = text(original, prior['_validate_entry'])
    added = '\n\n'.join(text(canonical, current[name]) for name in METHODS)
    require(result.count(anchor) == 1, 'one_cache_insertion_boundary')
    result = result.replace(anchor, added + '\n\n' + anchor)
    compile(result, '<node3-journal-cache>', 'exec')
    return result


def build():
    canonical_path = REPO / 'gpu/orch_r125_stream_journal.py'
    canonical = canonical_path.read_text()
    rows = []
    for physical in (0, 1, 2, 3, 4, 7):
        folder = HERE / 'r181' / ('physical' + str(physical))
        write(folder / 'new_journal.py', patch_journal((folder / 'original_journal.py').read_text(), canonical))
        rows.append(dict(physical=physical, original=reference(folder / 'original_journal.py'), patched=reference(folder / 'new_journal.py')))
    write(HERE / 'r181/JOURNAL_CACHE_DELTA.json', dict(canonical=reference(canonical_path), patch=reference(__file__),
        rows=rows, validators_fsync_hash_lock_unchanged=True, no_inflight_native_changes=True))


if __name__ == '__main__':
    build()
