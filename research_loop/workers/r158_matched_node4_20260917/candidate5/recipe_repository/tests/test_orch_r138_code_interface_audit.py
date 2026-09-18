from copy import deepcopy
import importlib.util
import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


specification = importlib.util.spec_from_file_location('interface_audit',
    Path(__file__).resolve().parents[1] / 'gpu/orch_r138_code_interface_audit.py')
subject = importlib.util.module_from_spec(specification)
specification.loader.exec_module(subject)


def extract(raw, **kwargs):
    return subject.extract(raw, terminal=kwargs.get('terminal', True), truncated=kwargs.get('truncated', False))


def task():
    return dict(kind=0, threshold=0, factor=2, offset=1, public_input=[-1, 0, 1],
                verification_inputs=[[-1, 0, 1]] * 20)


class ExtractionTests(unittest.TestCase):
    def test_unquoted_value_extracted_without_rewriting_code(self):
        result = extract('{"expression":sum(affine(ge(values,0),2,1))}')
        self.assertEqual(result['expression'], 'sum(affine(ge(values,0),2,1))')
        self.assertEqual(result['format'], 'UNQUOTED_EXPRESSION')
        self.assertEqual(result['selection'], 'SELECTED')

    def test_wrappers_share_exact_expression_AST(self):
        sources = ['{"expression":"sum(values)"}', '{"expr":"sum(values)"}',
            '{"expression":sum(values)}', '```json\n{"expression":"sum(values)"}\n```',
            '```python\nreturn sum(values)\n```', 'def solve(values):\n    return sum(values)']
        selected = [extract(source) for source in sources]
        self.assertTrue(all(item['selection'] == 'SELECTED' for item in selected))
        self.assertEqual(len({item['ast_sha256'] for item in selected}), 1)

    def test_ambiguity_never_selects_first_or_last_candidate(self):
        sources = ['{"expression":"0","expression":"sum(values)"}',
            '{"expr":"0","expression":"sum(values)"}',
            '{"expression":"0","comment":"sum(values)"}',
            '{"expression":"0"}\n{"expression":"sum(values)"}',
            '```json\n{"expression":"0"}\n```\n```json\n{"expression":"sum(values)"}\n```',
            'Reasoning or instruction text\n{"expression":"sum(values)"}',
            'return 0\nreturn sum(values)']
        for source in sources:
            with self.subTest(source=source):
                self.assertEqual(extract(source)['selection'], 'UNSUPPORTED')

    def test_malicious_AST_cannot_execute(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'must_not_exist'
            sources = [f'{{"expression":__import__("pathlib").Path({str(marker)!r}).touch()}}',
                '{"expression":values.__class__}', '{"expression":eval("sum(values)")}',
                '{"expression":sum(values, **{})}', '{"expression":(lambda: sum(values))()}',
                '{"expression":[sum(values) for item in values]}',
                'import os\nreturn sum(values)', '@decorator\ndef solve(values):\n return sum(values)']
            with patch('builtins.eval', side_effect=AssertionError('no_eval')):
                for source in sources:
                    with self.subTest(source=source):
                        self.assertNotEqual(extract(source)['selection'], 'SELECTED')
            self.assertFalse(marker.exists())

    def test_invented_code_is_never_added(self):
        for source in ['def solve(xs):\n return sum(xs)',
                       'def solve(values):\n result = sum(values)\n return result',
                       'def solve(values):\n "docstring"\n return sum(values)',
                       'def solve(values=side_effect()):\n return sum(values)',
                       'def solve(values: side_effect()):\n return sum(values)',
                       'def sum(values):\n return sum(values)']:
            with self.subTest(source=source):
                self.assertEqual(extract(source)['selection'], 'UNSUPPORTED')

    def test_arity_and_None_preserved_not_repaired(self):
        self.assertEqual(extract('{"expression":sum(values,values)}')['reason'], 'HELPER_ARITY')
        self.assertEqual(extract('{"expression":clip(values,0,None)}')['reason'], 'NON_BOUNDED_INTEGER_CONSTANT')

    def test_truncation_excluded_even_with_valid_prefix(self):
        with patch.object(subject.ast, 'parse', side_effect=AssertionError('no_salvage')):
            for terminal, truncated in [(False, True), (False, False), (True, True)]:
                result = extract('{"expression":"sum(values)"}', terminal=terminal, truncated=truncated)
                self.assertEqual(result['selection'], 'EXCLUDED')
                self.assertIsNone(result['expression'])

    def test_bounded_inputs_and_unclosed_fences(self):
        for source in ['x' * 4097, '```json\n{"expression":"sum(values)"}',
                       '{"expression":"' + '1' * 501 + '"}',
                       '{"expression":' + 'sum(' * 300 + 'values' + ')' * 300 + '}']:
            with self.subTest(length=len(source)):
                self.assertEqual(extract(source)['selection'], 'UNSUPPORTED')

    def test_extract_never_reads_oracle_or_invokes_sandbox_execution(self):
        self.assertEqual(list(inspect.signature(subject.extract).parameters), ['raw', 'terminal', 'truncated'])
        with patch.object(subject.frozen.public, 'expected', side_effect=AssertionError('no_gold')):
            with patch.object(subject.frozen, 'evaluate', side_effect=AssertionError('no_candidate_execution')):
                self.assertEqual(extract('{"expression":sum(values)}')['selection'], 'SELECTED')

    def test_sanitized_shapes_do_not_leak_constants_or_names(self):
        result = extract('{"expression":sum(affine(values,17,91))}')
        self.assertEqual(result['shape'], 'sum(affine(values,N,N))')
        self.assertNotIn('privateSecret', subject.safe_shape('privateSecret(values)'))
        self.assertNotIn('privateSecret', subject.safe_shape('"privateSecret"'))


class DiagnosticTests(unittest.TestCase):
    def test_fixed_checks_and_inputs_immutable(self):
        original_task = task()
        selection = extract('{"expression":sum(affine(ge(values,0),2,1))}')
        before = deepcopy((original_task, selection))
        with patch('builtins.eval', side_effect=AssertionError('must_use_R133_interpreter')):
            result = subject.evaluate_selected(selection, original_task)
        self.assertEqual(result['status'], 'DIAGNOSTIC_CHECK_PASS')
        self.assertEqual(result['matched'], 20)
        self.assertEqual(before, (original_task, selection))

    def test_list_return_is_not_wrapped_in_sum(self):
        selection = extract('{"expression":affine(values,2,1)}')
        result = subject.evaluate_selected(selection, task())
        self.assertEqual(result['reason'], 'NON_INTEGER_RETURN')
        self.assertEqual(result['status'], 'INTERPRETER_REJECTED')
        self.assertEqual(selection['expression'], 'affine(values,2,1)')

    def test_changing_expected_values_cannot_change_selected_candidate(self):
        raw = '{"expression":sum(values)}'
        selection = extract(raw)
        with patch.object(subject.frozen.public, 'expected', return_value=1):
            subject.evaluate_selected(selection, task())
        self.assertEqual(selection, extract(raw))
        with patch.object(subject.frozen.public, 'expected', return_value=-999):
            subject.evaluate_selected(selection, task())
        self.assertEqual(selection, extract(raw))

    def test_all_selections_frozen_before_first_oracle_comparison(self):
        records = [dict(response=dict(raw='{"expression":sum(values)}', terminal=True, truncated=False),
                        planned_call=position + 1, task_index=0, model='BASE_NO_LORA', stage='draft',
                        canonical=dict(category='PARSER_ERROR', success=False)) for position in range(2)]
        original = subject.extract
        calls = []
        def tracked(*args, **kwargs):
            calls.append(True)
            return original(*args, **kwargs)
        def expected(*args):
            self.assertEqual(len(calls), 2)
            return 0
        before = deepcopy(records)
        with patch.object(subject, 'extract', side_effect=tracked), patch.object(subject.frozen.public, 'expected', side_effect=expected):
            rows, manifest = subject.diagnose(records, [task()])
        self.assertEqual(len(manifest), 64)
        self.assertEqual(records, before)
        self.assertTrue(all(row['canonical']['category'] == 'PARSER_ERROR' for row in rows))

    def test_unsupported_never_reaches_oracle(self):
        with patch.object(subject.frozen.public, 'expected', side_effect=AssertionError('no_gold')):
            result = subject.evaluate_selected(extract('{"expression":clip(values,0,None)}'), task())
        self.assertEqual(result['status'], 'SANDBOX_REJECTED')

    def test_revision_classification_distinguishes_surface_and_expression(self):
        def row(raw):
            selection = extract(raw)
            return dict(complete=True, selection=selection, canonical=dict(category='PARSER_ERROR'),
                        diagnostic=subject.evaluate_selected(selection, task()))
        before = row('{"expression":sum(values)}')
        self.assertEqual(subject.revision(before, before)['classification'], 'EXACT_OUTPUT_UNCHANGED')
        surface = row('{"expression":"sum( values )"}')
        self.assertEqual(subject.revision(before, surface)['classification'], 'SURFACE_ONLY_SAME_EXPRESSION_AST')
        changed = row('{"expression":len(values)}')
        self.assertEqual(subject.revision(before, changed)['classification'], 'EXPRESSION_AST_CHANGED')
        changed['complete'] = False
        self.assertEqual(subject.revision(before, changed), dict(classification='EXCLUDED_INCOMPLETE_PAIR'))


class SnapshotTests(unittest.TestCase):
    def test_exact_author_status_not_generic_complete(self):
        author = dict(schema='R136_AUTHOR_RESULTS_V1', status='COMPLETE_AUTHOR_REDERIVED',
                      integrity=dict(evidence_sha256='a' * 64))
        reduced = dict(status='COMPLETE', expected_plan_sha256=subject.PINS['PLAN.json'],
                       evidence_sha256='a' * 64)
        subject.validate_headers(author, reduced)
        for status in ('COMPLETE', 'NOT_READY', 'FAILED_NO_RETRY'):
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, 'completed_R136_only'):
                subject.validate_headers(dict(author, status=status), reduced)

    def test_read_only_hashes_and_change_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixture.json'
            path.write_text('{"unchanged":true}')
            before = path.read_bytes()
            snapshot = subject.Snapshot(directory)
            snapshot.read('fixture.json')
            snapshot.stable()
            self.assertEqual(before, path.read_bytes())
            path.write_text('{"unchanged":false}')
            with self.assertRaisesRegex(ValueError, 'changed_artifact'):
                snapshot.stable()

    def test_symlinks_traversal_duplicate_keys_and_wrong_pins_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'fixture.json').write_text('{"value":1,"value":2}')
            (root / 'link.json').symlink_to(root / 'fixture.json')
            snapshot = subject.Snapshot(root)
            for name in ['fixture.json', 'link.json', '../foreign.json', str(root / 'fixture.json')]:
                with self.subTest(name=name), self.assertRaises(ValueError):
                    snapshot.read(name)
            (root / 'PLAN.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'R136_pin_mismatch'):
                snapshot.read('PLAN.json')


if __name__ == '__main__':
    unittest.main()
