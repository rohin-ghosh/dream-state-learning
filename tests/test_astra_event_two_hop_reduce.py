"""Independent reduction checks over fake-native terminal evidence."""

from contextlib import ExitStack
from pathlib import Path
import json
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools import astra_event_two_hop_reduce as reducer
from tests.test_astra_event_two_hop import fixture, arguments, runner
from tests.test_experienced_event_two_hop import generation
from tests.test_astra_selected_reader_repair import write


def terminal_fixture(root, stack, readout=True):
    state = fixture(root, stack)
    runner.main(arguments(root, 'collect'))
    if readout:
        runner.main(arguments(root, 'readout'))
    return state


class TwoHopReductionTests(unittest.TestCase):
    def test_complete_replays_all_conditions_and_reads_no_weight_files(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            terminal_fixture(root, stack)
            original = {str(path.relative_to(root)): reducer.digest(path) for path in root.rglob('*') if path.is_file()}
            digest = reducer.digest

            def checked_digest(path):
                self.assertNotIn('adapter', Path(path).parts)
                self.assertNotEqual(Path(path).suffix, '.safetensors')
                return digest(path)

            with patch.object(reducer, 'digest', side_effect=checked_digest):
                report = reducer.reduce_root(root)
            self.assertEqual(report['status'], 'COMPLETE', report)
            self.assertEqual(report['total_native_calls'], 120)
            self.assertFalse(report['tensor_loading'])
            collect = report['stages']['collect']
            self.assertEqual((collect['accepted_events'], collect['event_denominator']), (4, 4))
            readout = report['stages']['readout']
            self.assertEqual(readout['native_calls_by_role'], {'actor': 96, 'memory': 16})
            self.assertTrue(readout['readonly']['matched'])
            self.assertTrue(readout['matched_collection_source'])
            self.assertEqual(readout['unmatched_native_calls'], 0)
            for condition, correct in zip(runner.CONDITIONS, (4, 4, 2, 4)):
                panel = readout['panels'][condition]
                self.assertEqual((panel['correct'], panel['denominator'], panel['observed_episodes']), (correct, 4, 4))
                for episode in panel['episodes']:
                    self.assertEqual(len(episode['read_addresses']), 4)
                    self.assertEqual(episode['routes'], 2)
                    self.assertIsNotNone(episode['first_route'])
                    self.assertEqual(episode['strict_arrival'], episode['current'] == episode['goal'])
            self.assertEqual(original, {str(path.relative_to(root)): reducer.digest(path) for path in root.rglob('*') if path.is_file()})

    def test_native_call_role_condition_prompt_response_and_scope_tampering(self):
        for field, value in (('role', 'memory'), ('condition', 'OFF_OWN_TEXT'), ('adapter_off', True),
                             ('messages', []), ('response', generation('NONE')), ('call_index', 7)):
            with self.subTest(field=field), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                terminal_fixture(root, stack)
                path = root / 'readout/CALL_000.json'
                capture = reducer.read(path)
                capture[field] = value
                write(path, capture)
                report = reducer.reduce_root(root)
                self.assertEqual(report['status'], 'INVALID')
                self.assertIn('native_', report['verification_error'])

    def test_summary_episode_and_actual_text_substitution_are_rejected(self):
        for mutation in ('summary', 'transition', 'own_text', 'collection_call'):
            with self.subTest(mutation=mutation), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                terminal_fixture(root, stack)
                if mutation == 'summary':
                    path = root / 'readout/RESULT.json'
                    result = reducer.read(path)
                    result['panels']['ON_UNAVAILABLE']['correct'] = 4
                    write(path, result)
                elif mutation == 'collection_call':
                    path = root / 'collect/CALL_001.json'
                    capture = reducer.read(path)
                    capture['response']['raw'] += 'repair'
                    write(path, capture)
                else:
                    path = root / 'readout/ON_OWN_TEXT_EPISODE_00.json'
                    entry = reducer.read(path)
                    if mutation == 'transition':
                        entry['episode']['routes'][0]['destination'] = entry['task']['goal']
                    else:
                        collection = reducer.read(root / 'collect/COLLECTION.json')
                        world = collection['world']
                        store = runner.task.exact_text_store(collection)
                        commands = iter(['READ EVENT ' + entry['task']['events'][0],
                            'ROUTE ' + world['edges'][0]['port'], 'ROUTE ' + world['edges'][2]['port']])
                        entry['episode'] = runner.task.run_episode(world, entry['task'],
                            lambda messages: generation(next(commands)),
                            lambda address: store[address].rstrip('\n') + '\n')
                        entry['score'] = runner.task.score_episode(world, entry['task'], entry['episode'])
                    write(path, entry)
                report = reducer.reduce_root(root)
                self.assertEqual(report['status'], 'INVALID')
                if mutation == 'own_text':
                    self.assertEqual(report['verification_error'], 'nonparametric_memory_text_drift')

    def test_failed_collection_remains_failed_with_fixed_denominators(self):
        for early in (False, True):
            with self.subTest(early=early), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                state = fixture(root, stack)
                if early:
                    stack.enter_context(patch.object(runner, 'load_parent', side_effect=ValueError('parent unavailable')))
                else:
                    original_factory = state.factory.side_effect

                    def factory(*args, **kwargs):
                        engine = original_factory(*args, **kwargs)
                        engine.generate = lambda messages, **kwargs: generation('INVALID', messages)
                        return engine

                    state.factory.side_effect = factory
                with self.assertRaises(ValueError):
                    runner.main(arguments(root, 'collect'))
                report = reducer.reduce_root(root)
                self.assertEqual(report['status'], 'FAILED', report)
                self.assertEqual(report['failure_stage'], 'collect')
                self.assertEqual(report['stages']['collect']['event_denominator'], 4)
                self.assertEqual(report['stages']['collect']['native_calls'], 0 if early else 4)
                self.assertEqual(report['expected_task_denominators'], {condition: 4 for condition in runner.CONDITIONS})
                self.assertEqual(report['stages']['readout']['status'], 'NOT_ADMISSIBLE_AFTER_FAILED_COLLECTION')
                if not early:
                    self.assertEqual(report['stages']['collect']['accepted_events'], 0)
                    self.assertTrue(report['stages']['collect']['replay_verified'])

    def test_readonly_source_and_code_joins_and_missing_readout(self):
        for field, value in (('adapter_state_after', 'changed'), ('frozen_base_unchanged', False),
                             ('collection_result_sha256', 'unrelated'), ('helper_sha256', 'changed-helper')):
            with self.subTest(field=field), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                terminal_fixture(root, stack)
                path = root / 'readout/RESULT.json'
                receipt = reducer.read(path)
                receipt[field] = value
                write(path, receipt)
                self.assertEqual(reducer.reduce_root(root)['status'], 'INVALID')
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            terminal_fixture(root, stack, readout=False)
            report = reducer.reduce_root(root)
            self.assertEqual(report['status'], 'INCOMPLETE')
            self.assertEqual(report['stages']['readout']['task_denominators'], {condition: 4 for condition in runner.CONDITIONS})

    def test_cli_reduces_without_ml_imports_and_creates_exclusive_output(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            terminal_fixture(root, stack)
            script = """
import builtins, sys
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from tools import astra_event_two_hop_reduce
raise SystemExit(astra_event_two_hop_reduce.main(['--root', sys.argv[1]]))
"""
            completed = subprocess.run([sys.executable, '-c', script, str(root)], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)['status'], 'COMPLETE')
            output = root / 'reduction.json'
            self.assertEqual(reducer.main(['--root', str(root), '--output', str(output)]), 0)
            with self.assertRaises(FileExistsError):
                reducer.main(['--root', str(root), '--output', str(output)])

    def test_multicommand_node_as_port_and_truncation_are_distinct(self):
        world = runner.task.build_world()
        public = runner.task.build_tasks(world)[0]
        multiline = 'READ EVENT ' + public['events'][0] + '\nROUTE ' + public['ports'][0] + '\n'
        cases = ((generation(multiline), 'MULTI_COMMAND_OUTPUT'),
                 (generation('ROUTE ' + public['node']), 'NODE_AS_PORT'),
                 (dict(raw=multiline, terminal=False, truncated=True), 'NONTERMINAL_OR_TRUNCATED'))
        for response, category in cases:
            with self.subTest(category=category):
                episode = runner.task.run_episode(world, public, lambda messages: response, lambda address: self.fail('unexpected read'))
                diagnostic = reducer.output_diagnostic(episode)
                self.assertEqual(diagnostic['classification'], category)
                self.assertEqual(diagnostic['raw'], response['raw'])
                self.assertEqual((episode['memory_calls'], episode['route_calls']), (0, 0))

    def test_turnbound_reuses_explicit_collection_without_new_collection_directory(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            prior, current = root / 'prior', root / 'current'
            terminal_fixture(prior, stack, readout=False)
            runner.main(arguments(prior, 'readout', current / 'readout') + ['--protocol', 'turnbound'])
            self.assertFalse((current / 'collect').exists())
            report = reducer.reduce_root(current, collection_path=prior / 'collect')
            self.assertEqual(report['status'], 'COMPLETE', report)
            self.assertEqual(report['stages']['readout']['protocol'], 'turnbound')
            self.assertTrue(report['reused_collection'])
            self.assertEqual((report['reused_collection_native_calls'], report['new_native_calls']), (8, 112))
            output = root / 'reused.json'
            self.assertEqual(reducer.main(['--root', str(current), '--collection', str(prior / 'collect'),
                                          '--output', str(output)]), 0)
            self.assertEqual(reducer.read(output)['status'], 'COMPLETE')

    def test_readout_and_episode_protocol_must_agree(self):
        for mutation in ('arguments', 'episode', 'unknown'):
            with self.subTest(mutation=mutation), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                prior, current = root / 'prior', root / 'current'
                terminal_fixture(prior, stack, readout=False)
                runner.main(arguments(prior, 'readout', current / 'readout') + ['--protocol', 'turnbound'])
                if mutation == 'episode':
                    path = current / 'readout/ON_PARAMETRIC_EPISODE_00.json'
                    document = reducer.read(path)
                    del document['episode']['protocol']
                else:
                    path = current / 'readout/RESULT.json'
                    document = reducer.read(path)
                    document['arguments']['protocol'] = 'original' if mutation == 'arguments' else 'unregistered'
                write(path, document)
                report = reducer.reduce_root(current, collection_path=prior / 'collect')
                self.assertEqual(report['status'], 'INVALID')
                self.assertIn('protocol', report['verification_error'])


if __name__ == '__main__':
    unittest.main()
