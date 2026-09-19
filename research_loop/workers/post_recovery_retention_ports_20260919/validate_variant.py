"""Run the unchanged 17+5 contracts and preservation checks in one isolated process."""

import argparse
import ast
import hashlib
import importlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import sys
import unittest

from port import port_text, reference_edits
from prepare import FILES, HERE, PHASE2, VARIANTS


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def mentions_retention(node):
    return any(isinstance(child, ast.Name) and child.id == 'retained_parent_event_id'
        or isinstance(child, ast.Attribute) and child.attr in
            ('_active_parent_event_id', '_retain_stage_parent', '_remember_rendered_parent')
        or isinstance(child, ast.Constant) and child.value in
            ('retained_parent_event_id', 'retention_messages') for child in ast.walk(node))


class RemoveRetention(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        if node.name in ('_retain_stage_parent', '_remember_rendered_parent'):
            return None
        return self.generic_visit(node)

    def visit_arguments(self, node):
        kept = [(argument, default) for argument, default in zip(node.kwonlyargs, node.kw_defaults, strict=True)
            if argument.arg != 'retained_parent_event_id']
        node.kwonlyargs = [argument for argument, unused in kept]
        node.kw_defaults = [default for unused, default in kept]
        return self.generic_visit(node)

    def visit_Call(self, node):
        node.keywords = [keyword for keyword in node.keywords if keyword.arg != 'retained_parent_event_id']
        return self.generic_visit(node)

    def visit_Assign(self, node):
        node = self.generic_visit(node)
        if mentions_retention(node):
            return None
        return node

    def visit_Expr(self, node):
        node = self.generic_visit(node)
        if mentions_retention(node):
            return None
        return node

    def visit_If(self, node):
        if mentions_retention(node.test):
            return None
        node = self.generic_visit(node)
        return node if node.body else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('variant', choices=VARIANTS)
    life = parser.parse_args().variant
    root = HERE / life
    pins = json.loads((root / 'SOURCE_PINS.before.json').read_bytes())
    sys.path.insert(0, str(HERE.parents[2]))
    support_path = root / 'TEST_SUPPORT.json'
    if support_path.exists():
        for relative, evidence in json.loads(support_path.read_bytes()).items():
            path = root / 'test_support' / relative
            if sha(path) != evidence['sha256'] or sha(path) != pins[relative]:
                raise ValueError('exact_pinned_test_support')
            name = relative.removesuffix('.py').replace('/', '.')
            package, attribute = name.rsplit('.', 1)
            parent = importlib.import_module(package)
            setattr(parent, attribute, load(name, path))
    tests = load('retention_tests_' + life, root / 'test_retention.py')
    targeted = unittest.defaultTestLoader.loadTestsFromModule(tests)
    if targeted.countTestCases() != 17:
        raise ValueError('exact_17_phase2_tests')
    choices = {
        'test_orch_r125_continual_stream.py': (
            'test_threshold_compaction_precedes_generation_and_preserves_raw_input',
            'test_threshold_reuses_prior_child_distillation_not_later_failed_code',
            'test_threshold_never_silently_drops_oversized_fresh_input'),
        'test_orch_r124_train_history.py': (
            'test_pinned_parent_is_verbatim_masked_once_across_compaction_eviction_and_restore',
            'test_child_cannot_be_pinned_and_pins_cannot_be_silently_truncated'),
    }
    legacy = unittest.TestSuite()
    for name, methods in choices.items():
        module = load('legacy_' + name.removesuffix('.py'), HERE / 'legacy_tests' / name)
        for candidate in vars(module).values():
            if isinstance(candidate, type) and issubclass(candidate, unittest.TestCase):
                for method in methods:
                    if hasattr(candidate, method):
                        legacy.addTest(candidate(method))
    if legacy.countTestCases() != 5:
        raise ValueError('exact_five_existing_contracts')

    class PreservationTests(unittest.TestCase):
        def test_exact_three_variant_modules_and_unchanged_tests(self):
            for relative in FILES:
                name = relative.removesuffix('.py').replace('/', '.')
                self.assertEqual(Path(sys.modules[name].__file__).resolve(), root / 'fork' / relative)
            self.assertEqual(sha(root / 'test_retention.py'), sha(PHASE2 / 'test_retention.py'))
            self.assertEqual(sha(root / 'run_checks.py'), sha(PHASE2 / 'run_checks.py'))
            for name, expected in json.loads((HERE / 'TEST_INPUTS.json').read_bytes()).items():
                self.assertEqual(sha(HERE / 'legacy_tests' / name), expected)

        def test_preimages_and_exact_phase2_delta_preserve_every_other_byte(self):
            edits = reference_edits()
            pins = json.loads((root / 'SOURCE_PINS.before.json').read_bytes())
            for relative in FILES:
                before, after = root / 'preimage' / relative, root / 'fork' / relative
                self.assertEqual(sha(before), pins[relative])
                self.assertEqual(after.read_text(), port_text(before.read_text(), edits[relative]))
                self.assertEqual(ast.dump(ast.parse(before.read_text())),
                    ast.dump(RemoveRetention().visit(ast.parse(after.read_text()))))

        def test_existing_interrupt_interface_and_abort_semantics(self):
            signature = inspect.signature(tests.stream_module.ContinualStream.step)
            expected_interrupt = life in ('C0', 'Astra7', 'C2')
            self.assertEqual('interrupt' in signature.parameters, expected_interrupt)
            if not expected_interrupt:
                return
            fixture = tests.RetentionTests()
            fixture.setUp()
            seen = []
            def interrupted(messages, *, interrupt, **unused):
                seen.append(interrupt)
                return dict(raw='partial', token_ids=[1], interruption={'source': 'synthetic'})
            interrupt = lambda: True
            result = fixture.stream.step(interrupted, tests.token_count, fixture.journal.record,
                incoming=[fixture.current], interrupt=interrupt, retained_parent_event_id=fixture.current.event_id)
            self.assertEqual(seen, [interrupt])
            self.assertEqual(result['status'], 'ABORTED_NOT_TRAINED')
            self.assertIsNone(fixture.stream.pending)
            self.assertEqual(fixture.stream.rows, [])
            kinds = [kind for kind, unused in fixture.journal.records]
            self.assertIn('GENERATION_ABORTED', kinds)
            self.assertNotIn('COMMITTED', kinds)

        def test_nontraining_response_and_checkpoint_roundtrip_unchanged(self):
            fixture = tests.RetentionTests()
            fixture.setUp()
            before_model = fixture.stream.model_state_sha256
            result = fixture.stream.step(fixture.child.generate, tests.token_count, fixture.journal.record,
                incoming=[fixture.current], train_response=False, retained_parent_event_id=fixture.current.event_id)
            self.assertFalse(result['training_eligible'])
            self.assertEqual(fixture.stream.rows, [])
            self.assertEqual(fixture.stream.model_state_sha256, before_model)
            checkpoint = fixture.stream.checkpoint()
            restored = tests.stream_module.ContinualStream.restore(checkpoint, expected_sha256=checkpoint['sha256'])
            self.assertEqual(checkpoint, restored.checkpoint())
            self.assertNotIn('_active_parent_event_id', str(checkpoint))

        def test_r227_language_and_native_hooks_remain_variant_specific(self):
            before = (root / 'preimage' / FILES[0]).read_text()
            after = (root / 'fork' / FILES[0]).read_text()
            for marker in ('all_child_rows', 'effective_config', 'language_scope', 'annotate_language_policy',
                    'reading_reply_policy', 'console_preemption_policy', 'r184_cpu_bridge', 'finish_sleep',
                    'fresh_readout', 'new_presentations', 'train_response=False'):
                self.assertEqual(after.count(marker), before.count(marker), marker)

    results = {}
    for label, suite in (('TESTS', targeted), ('LEGACY_TESTS', legacy),
            ('PRESERVATION_TESTS', unittest.defaultTestLoader.loadTestsFromTestCase(PreservationTests))):
        with (root / (label + '.log')).open('w') as stream:
            outcome = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        results[label] = dict(tests=outcome.testsRun, passed=outcome.wasSuccessful(),
            failures=len(outcome.failures), errors=len(outcome.errors), skipped=len(outcome.skipped),
            log_sha256=sha(root / (label + '.log')))
    imported = {}
    repository = HERE.parents[2]
    for name, module in list(sys.modules.items()):
        path = getattr(module, '__file__', None)
        if not path or not Path(path).is_file() or not path.endswith('.py'):
            continue
        path = Path(path).resolve()
        if path.is_relative_to(root / 'fork'):
            imported[name] = dict(path=str(path.relative_to(HERE)), sha256=sha(path), role='variant_overlay')
        elif path.is_relative_to(root / 'test_support'):
            relative = str(path.relative_to(root / 'test_support'))
            imported[name] = dict(path=str(path.relative_to(HERE)), sha256=sha(path), role='pinned_test_support',
                source_pin_sha256=pins[relative], matches_source_pin=sha(path) == pins[relative])
        elif path.is_relative_to(repository) and not path.is_relative_to(HERE):
            relative = str(path.relative_to(repository))
            imported[name] = dict(path=relative, sha256=sha(path), role='local_test_support',
                source_pin_sha256=pins.get(relative), matches_source_pin=sha(path) == pins.get(relative))
    matched_support = all(item.get('matches_source_pin', True) for item in imported.values())
    receipt = dict(variant=life, process_id=os.getpid(), isolated_process=True,
        tests=results, imported_modules=imported, no_generation=True, no_remote_access=True,
        imported_support_matches_source_pins=matched_support,
        status='PASS' if matched_support and all(item['passed'] for item in results.values()) else 'FAIL')
    (root / 'TEST_RECEIPT.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(life + ': ' + ', '.join(f'{label}={result["tests"]}:{result["passed"]}' for label, result in results.items()))
    if receipt['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
