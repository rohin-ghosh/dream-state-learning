"""Copy only Main's journal cache methods onto either actual NODE4 variant."""

import ast
import hashlib
import io
from pathlib import Path
import unittest


MAIN_SHA = 'd57c318baa509c009f12328b566f391f79a3948e497b6fdbc04bd2d1d274c9fd'
ORIGINAL_SHAS = {
    'fcd9fd151d7d1f5b2f7611074cf5e70772c77e0c2b4162c8e0b1d71bc9e5a429',
    '3925a6dff44c71994d446445833207ba3b4a9c8a983b56a8f3e3de84239eb0ca',
}
REPLACED = ('__init__', 'record', 'latest_checkpoint', 'read_inbox')
ADDED = ('_file_identity', '_record_snapshot', '_reload_state', '_validated_state', 'audit')
CACHE_TESTS = (
    'test_hot_path_uses_validated_state_without_replaying_old_records',
    'test_reopen_always_revalidates_the_complete_chain',
    'test_cached_authoritative_checkpoint_is_detached_from_callers',
    'test_old_record_rewrite_with_restored_mtime_invalidates_cache',
    'test_file_change_during_full_revalidation_rejected',
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def methods(source):
    classes = [node for node in ast.parse(source).body if isinstance(node, ast.ClassDef)
               and node.name == 'StreamJournal']
    require(len(classes) == 1, 'one_actual_StreamJournal')
    return {node.name: node for node in classes[0].body if isinstance(node, ast.FunctionDef)}


def start(node):
    return min([node.lineno] + [decorator.lineno for decorator in node.decorator_list]) - 1


def patch_journal(actual, main):
    require(hashlib.sha256(actual.encode()).hexdigest() in ORIGINAL_SHAS, 'known_actual_journal_bytes')
    require(hashlib.sha256(main.encode()).hexdigest() == MAIN_SHA, 'exact_Main_journal_cache_bytes')
    original, canonical = methods(actual), methods(main)
    require(not set(ADDED).intersection(original), 'no_existing_cache_repatch')
    lines, reference = actual.splitlines(keepends=True), main.splitlines(keepends=True)
    edits = [(start(original[name]), original[name].end_lineno,
              ''.join(reference[start(canonical[name]):canonical[name].end_lineno])) for name in REPLACED]
    insertion = '\n\n'.join(''.join(reference[start(canonical[name]):canonical[name].end_lineno]).rstrip()
                            for name in ADDED) + '\n\n'
    edits.append((start(original['_validate_entry']), start(original['_validate_entry']), insertion))
    for lower, upper, text in sorted(edits, reverse=True):
        lines[lower:upper] = [text]
    patched = ''.join(lines)
    changed = methods(patched)
    require(set(changed) == set(original) | set(ADDED), 'only_Main_cache_method_set')
    for name, node in original.items():
        expected = canonical[name] if name in REPLACED else node
        require(ast.dump(changed[name]) == ast.dump(expected), 'exact_method_preservation:' + name)
    for name in ADDED:
        require(ast.dump(changed[name]) == ast.dump(canonical[name]), 'exact_Main_added_method:' + name)
    compile(patched, '<actual-journal-cache-overlay>', 'exec')
    return patched


def run_cache_tests(path):
    import importlib.util
    spec = importlib.util.spec_from_file_location('actual_receiving_Main_journal_tests', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    log = io.StringIO()
    suite = unittest.TestSuite(module.StreamJournalTests(name) for name in CACHE_TESTS)
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    require(result.wasSuccessful() and result.testsRun == 5, 'actual_Main_cache_tests:' + log.getvalue())
    return dict(passed=result.testsRun, output=log.getvalue())
