"""CPU-only native-driver joins and bounded child-selection callback tests."""

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

from gpu import astra_experienced_event_adult_cycle as runner
from organism_v6 import experienced_event_corrective_replay as corrective
from tests.test_experienced_event_corrective_replay import fixture as public_fixture


ACTOR_SHA = 'a' * 64
BASE_SHA = 'b' * 64


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(runner.source.native._json_bytes(value))


def fixture(root):
    collection, records, unused = public_fixture()
    directory = root / 'before'
    current = dict(initial_training_result_sha256='c' * 64, adult_source={'collection': 'A2'},
        memory_source={'memory': 'original'}, cue_source={'cue': 'original'}, prior_adult_source={'prior': 'A1'},
        prior_adult_training_result_sha256='c' * 64, cycle=2, master=runner.adult.SECOND_MASTER,
        development_arm='CUE_REPLAY', arguments=dict(expected_base_sha256=BASE_SHA,
                                                   expected_initial_adapter_sha256='d' * 64))
    arguments = dict(current['arguments'], phase='readout', state='BEFORE', cycle=2,
                     development_arm='CUE_REPLAY', reader_wrapper=0)
    before = dict(deepcopy(current), schema=runner.SCHEMA, status='COMPLETE', phase='readout', state='BEFORE',
        frozen_base_unchanged=True, fits=0, loaded_adapter_state_sha256=ACTOR_SHA, arguments=arguments,
        reader_wrapper=0, runner_sha256='e' * 64, material_sha256='f' * 64,
        panels=dict(OWN_PARAMETRIC=dict(denominator=4, episodes=deepcopy(records))))
    request = {key: deepcopy(before[key]) for key in ('schema', 'phase', 'state', 'cycle', 'master',
               'development_arm', 'runner_sha256', 'material_sha256', 'arguments')}
    write(directory / 'RESULT.json', before)
    write(directory / 'REQUEST.json', request)
    write(directory / 'new_task/PANELS.json', before['panels'])
    for index, record in enumerate(records, 1):
        write(directory / ('new_task/OWN_PARAMETRIC_EPISODE_%02d.json' % index), record)
    return directory, collection, current


class DriverTests(unittest.TestCase):
    def load(self, directory, collection, current):
        return runner.load_correction_before(directory, collection, current, expected_adapter_state_sha256=ACTOR_SHA)

    def test_load_all_four_records_source_hashes_and_two_cases(self):
        with TemporaryDirectory() as temporary:
            directory, collection, current = fixture(Path(temporary))
            originals = {str(path): path.read_bytes() for path in directory.rglob('*.json')}
            cases, provenance = self.load(directory, collection, current)
            self.assertEqual(cases['expected_calls'], 2)
            self.assertEqual(len(provenance['source_files']), 7)
            for name, digest in provenance['source_files'].items():
                self.assertEqual(digest, runner.source.file_hash(directory / name))
            self.assertEqual(provenance['result_sha256'], runner.source.file_hash(directory / 'RESULT.json'))
            self.assertEqual(provenance['loaded_adapter_state_sha256'], ACTOR_SHA)
            self.assertEqual(originals, {path: Path(path).read_bytes() for path in originals})

    def test_before_receipt_lineage_actor_and_flags_drift_rejected(self):
        faults = dict(status='FAILED', phase='train', state='AFTER', cycle=1, fits=1,
            development_arm='CUE_LOSS_OFF', frozen_base_unchanged=False,
            initial_training_result_sha256='wrong', adult_source={}, memory_source={}, cue_source={},
            prior_adult_source={}, prior_adult_training_result_sha256='wrong',
            loaded_adapter_state_sha256='wrong', reader_wrapper=8)
        for key, value in faults.items():
            with self.subTest(key=key), TemporaryDirectory() as temporary:
                directory, collection, current = fixture(Path(temporary))
                before = runner.source.read(directory / 'RESULT.json')
                before[key] = value
                write(directory / 'RESULT.json', before)
                with self.assertRaises(ValueError):
                    self.load(directory, collection, current)
        for key in ('expected_base_sha256', 'expected_initial_adapter_sha256'):
            with self.subTest(key=key), TemporaryDirectory() as temporary:
                directory, collection, current = fixture(Path(temporary))
                current['arguments'][key] = 'wrong'
                with self.assertRaisesRegex(ValueError, 'identity_mismatch'):
                    self.load(directory, collection, current)

    def test_files_request_panel_and_actual_public_trace_drift_rejected(self):
        for fault in ('request', 'panel', 'episode', 'extra', 'failed', 'consistent_trace_drift'):
            with self.subTest(fault=fault), TemporaryDirectory() as temporary:
                directory, collection, current = fixture(Path(temporary))
                if fault == 'request':
                    request = runner.source.read(directory / 'REQUEST.json')
                    request['arguments']['expected_base_sha256'] = 'wrong'
                    write(directory / 'REQUEST.json', request)
                elif fault == 'panel':
                    write(directory / 'new_task/PANELS.json', {})
                elif fault == 'extra':
                    write(directory / 'new_task/OWN_PARAMETRIC_EPISODE_05.json', {})
                elif fault == 'failed':
                    write(directory / 'FAILED.json', {})
                else:
                    path = directory / 'new_task/OWN_PARAMETRIC_EPISODE_01.json'
                    record = runner.source.read(path)
                    record['episode']['messages'][1]['content'] += '\nInjected source change'
                    write(path, record)
                    if fault == 'consistent_trace_drift':
                        before = runner.source.read(directory / 'RESULT.json')
                        before['panels']['OWN_PARAMETRIC']['episodes'][0] = record
                        write(directory / 'RESULT.json', before)
                        write(directory / 'new_task/PANELS.json', before['panels'])
                with self.assertRaises(ValueError):
                    self.load(directory, collection, current)

    def test_two_actual_choices_wrong_but_sourced_remain_admitted_no_fit(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory, collection, current = fixture(root)
            cases, provenance = self.load(directory, collection, current)
            output = root / 'select_corrective'
            output.mkdir()
            raw = collection['episodes'][0]['event']['raw']
            engine = MagicMock()
            engine.generate.side_effect = lambda messages, **kwargs: dict(messages=deepcopy(messages), raw=raw,
                                                                          terminal=True, truncated=False)
            result = runner.select_corrective(engine, cases, output, provenance)
            self.assertEqual(engine.generate.call_count, 2)
            for call, case in zip(engine.generate.call_args_list, cases['cases']):
                self.assertEqual(call.args[0], case['messages'])
                self.assertEqual(call.kwargs, dict(max_new_tokens=160))
            selection = runner.source.read(output / 'SELECTION.json')
            self.assertEqual(selection['chosen_source_indexes'], [0, 0])
            self.assertEqual(selection['admitted_selections'], 2)
            self.assertEqual(len(selection['row_source_indexes']), 16)
            self.assertEqual((result['fits'], result['model_calls'], result['parent_present']), (0, 2, False))
            self.assertEqual(result['selection_sha256'], runner.source.file_hash(output / 'SELECTION.json'))
            self.assertEqual(len(list(output.glob('CALL_*.json'))), 2)
            self.assertFalse((output / 'adapter').exists())
            records = runner.source.read(directory / 'RESULT.json')['panels']['OWN_PARAMETRIC']['episodes']
            corrective.replay_selection(selection, collection, records)
            with self.assertRaises(FileExistsError):
                runner.select_corrective(engine, cases, output, provenance)
            self.assertEqual(engine.generate.call_count, 2)

    def test_invalid_abstained_and_callback_failure_retained_without_retry(self):
        for response in ('garbage', 'NONE', None):
            with self.subTest(response=response), TemporaryDirectory() as temporary:
                root = Path(temporary)
                directory, collection, current = fixture(root)
                cases, provenance = self.load(directory, collection, current)
                output = root / 'selection'
                output.mkdir()
                engine = MagicMock()
                if response is None:
                    engine.generate.side_effect = RuntimeError('synthetic callback error')
                else:
                    engine.generate.return_value = dict(raw=response, terminal=True, truncated=False)
                result = runner.select_corrective(engine, cases, output, provenance)
                self.assertEqual((engine.generate.call_count, result['admitted_selections']), (2, 0))
                selection = runner.source.read(output / 'SELECTION.json')
                self.assertEqual(selection['status'], 'SELECTION_CAPTURED_NO_FIT')
                for capture in selection['captures']:
                    if response is None:
                        self.assertIsNotNone(capture['error'])
                    else:
                        self.assertEqual(capture['response']['raw'], response)

    def test_callback_cap_and_preparation_hash_reject_before_extra_generation(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory, collection, current = fixture(root)
            cases, provenance = self.load(directory, collection, current)
            engine = MagicMock()
            engine.generate.return_value = dict(raw='NONE', terminal=True, truncated=False)

            def extra_callback(plan, generate):
                for case in plan['cases']:
                    generate(case['messages'])
                generate(plan['cases'][0]['messages'])

            output = root / 'extra'
            output.mkdir()
            with patch.object(corrective, 'collect_selection', side_effect=extra_callback):
                with self.assertRaisesRegex(ValueError, 'corrective_callback_cap'):
                    runner.select_corrective(engine, cases, output, provenance)
            self.assertEqual(engine.generate.call_count, 2)
            output = root / 'corrupt'
            output.mkdir()
            cases['preparation_sha256'] = 'wrong'
            engine.generate.reset_mock()
            with self.assertRaisesRegex(ValueError, 'prepared_cases_source_drift'):
                runner.select_corrective(engine, cases, output, provenance)
            engine.generate.assert_not_called()

    def test_cli_only_selected_cycle2_before_actor_and_phase(self):
        common = []
        for name in ('model-dir', 'expected-base-sha256', 'initial-adapter-dir', 'expected-initial-adapter-sha256',
                     'collection', 'cue-collection', 'output', 'gpu-uuid'):
            common.extend(['--' + name, 'unused'])
        cases = [dict(phase='train', arm='CUE_REPLAY', cycle='2', state='BEFORE', correction=True),
                 dict(phase='select_corrective', arm='CUE_REPLAY', cycle='2', state='BEFORE', correction=False),
                 dict(phase='select_corrective', arm='CUE_LOSS_OFF', cycle='2', state='BEFORE', correction=True),
                 dict(phase='select_corrective', arm='CUE_REPLAY', cycle='1', state='BEFORE', correction=True),
                 dict(phase='select_corrective', arm='CUE_REPLAY', cycle='2', state='AFTER', correction=True)]
        for case in cases:
            arguments = common + ['--phase', case['phase'], '--development-arm', case['arm'],
                                  '--cycle', case['cycle'], '--state', case['state']]
            if case['correction']:
                arguments += ['--correction-before', 'before']
            with self.subTest(case=case), patch.object(runner.source, 'Engine') as engine:
                with self.assertRaises(ValueError):
                    runner.main(arguments)
                engine.assert_not_called()


if __name__ == '__main__':
    unittest.main()
