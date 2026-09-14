from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from gpu import astra_experienced_event_cue_collect as runner
from tests.test_experienced_event_cue_collection import PublicReadingActor, generation


class SyntheticEngine:
    def __init__(self, *, bad_first_bank=False, actor_error=False):
        self.banks = runner.training_banks()
        self.facts = sum(self.banks, [])
        self.actor = PublicReadingActor()
        self.bad_events = {fact["event"] for fact in self.banks[0]} if bad_first_bank else set()
        self.actor_error = actor_error

    def generate(self, messages):
        if messages[0]["content"] == runner.source.material.FORMATION_SYSTEM:
            fact = next(fact for fact in self.facts if fact["port"] in messages[1]["content"])
            if len(messages) == 2:
                return generation("EXPLORE " + fact["node"] + " " + fact["port"])
            raw = "invalid event" if fact["event"] in self.bad_events else runner.source.material._event(fact) + "\n"
            return generation(raw)
        if self.actor_error:
            raise RuntimeError("synthetic generation infrastructure fault")
        return self.actor(messages)


class CueNativeTests(unittest.TestCase):
    def test_training_banks_exclude_previous_bank_and_each_other(self):
        banks = runner.training_banks()
        self.assertEqual(len(banks), 2)
        identities = [{value for fact in bank for value in fact.values() if type(value) is str}
                      for bank in banks + [runner.source.material.build_bank(runner.source.MASTER)]]
        self.assertTrue(all(not identities[first] & identities[second]
                            for first in range(3) for second in range(first + 1, 3)))

    def test_source_then_external_text_collection_no_fit(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = runner.collect(SyntheticEngine(), root)
            self.assertEqual(result["admitted_events"], 8)
            self.assertEqual(result["selected_successes"], 8)
            self.assertEqual(result["student_rows"], 20)
            self.assertEqual(result["physical_model_calls"], 36)
            self.assertEqual(result["fits"], 0)
            self.assertEqual(len(list(root.glob("CALL_*.json"))), 36)
            bank = runner.source.read(root / "BANK_00/CUE_COLLECTION.json")
            self.assertTrue(all(raw.endswith("\n\n") for raw in bank["raw_memory_by_address"].values()))

    def test_wrong_source_events_are_not_repaired_or_used_for_cues(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = runner.collect(SyntheticEngine(bad_first_bank=True), root)
            self.assertEqual(result["admitted_events"], 4)
            self.assertEqual(result["selected_successes"], 4)
            self.assertEqual(result["cue_task_denominator"], 8)
            bank = runner.source.read(root / "BANK_00/CUE_COLLECTION.json")
            self.assertEqual(bank["status"], "SOURCE_INCOMPLETE_NO_CUE_EPISODES")
            self.assertEqual(bank["student_rows"], [])

    def test_infrastructure_fault_cannot_finish_as_complete_collection(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, "native_callback_failure"):
                runner.collect(SyntheticEngine(actor_error=True), root)
            calls = [runner.source.read(path) for path in root.glob("CALL_*.json")]
            self.assertTrue(any(call["error"] for call in calls))
            self.assertTrue((root / "BANK_RESULTS.json").exists())


def original_fixture(root):
    root.mkdir()
    result = runner.collect(SyntheticEngine(), root)
    arguments = dict(expected_base_sha256='a' * 64, phase='collect', adapter_dir=None)
    metadata = dict(schema='DEV_GUIDED_EXTERNAL_EVENT_CUE_COLLECTION_V1', master=runner.MASTER,
                    arguments=arguments)
    runner.source.write(root / 'REQUEST.json', metadata)
    runner.source.write(root / 'RESULT.json', dict(result, **metadata,
                        status='COLLECTION_COMPLETE_NO_FIT', frozen_base_unchanged=True))
    return root


def rewrite(path, value):
    path.write_text(json.dumps(value))


class ReuseExperienceTests(unittest.TestCase):
    def test_exact_source_validation_reads_no_original_cue_rows_or_scores(self):
        with TemporaryDirectory() as temporary:
            root = original_fixture(Path(temporary) / 'original')
            for path in list(root.glob('CALL_*.json')) + list(root.glob('BANK_*/CUE_COLLECTION.json')) + [root / 'BANK_RESULTS.json']:
                path.unlink()
            result = runner.source.read(root / 'RESULT.json')
            result['selected_successes'] = 'not consumed'
            result['student_rows'] = {'deliberately': 'not a training source'}
            rewrite(root / 'RESULT.json', result)
            loaded = runner.load_reused_experiences(root, expected_base_sha256='a' * 64)
            self.assertEqual(len(loaded['banks']), 2)
            self.assertEqual(len(loaded['input_file_sha256']), 14)
            self.assertFalse(loaded['source_cue_rows_used'])
            self.assertFalse(loaded['source_cue_scores_used'])
            for name, digest in loaded['input_file_sha256'].items():
                self.assertEqual(runner.source.file_hash(root / name), digest)
                self.assertNotIn('CUE_COLLECTION', name)
            self.assertTrue(all(raw.endswith('\n\n') for bank in loaded['banks']
                                for raw in bank['raw_memory_by_address'].values()))

    def test_altered_missing_unterminated_and_wrong_bank_fail(self):
        faults = ('missing', 'aggregate_drift', 'wrong_field', 'unterminated', 'truncated',
                  'wrong_bank', 'bad_explore', 'wrong_messages', 'wrong_token', 'failed_marker')
        for fault in faults:
            with self.subTest(fault=fault), TemporaryDirectory() as temporary:
                root = original_fixture(Path(temporary) / 'original')
                directory = root / 'BANK_00'
                individual = directory / 'EXPERIENCE_01.json'
                records = runner.source.read(directory / 'EXPERIENCES.json')
                if fault == 'missing':
                    individual.unlink()
                elif fault == 'aggregate_drift':
                    changed = deepcopy(records[0])
                    changed['event']['raw'] += '\n'
                    rewrite(individual, changed)
                elif fault == 'wrong_bank':
                    rewrite(directory / 'BANK.json', runner.training_banks()[1])
                elif fault == 'failed_marker':
                    rewrite(root / 'FAILED.json', {'error': 'original failed'})
                else:
                    if fault == 'wrong_field':
                        fact = records[0]['fact']
                        records[0]['event']['raw'] = records[0]['event']['raw'].replace(fact['outcome'], records[1]['fact']['outcome'])
                    elif fault == 'unterminated':
                        records[0]['event']['terminal'] = False
                    elif fault == 'truncated':
                        records[0]['exploration']['truncated'] = True
                    elif fault == 'bad_explore':
                        records[0]['exploration']['raw'] += '\n'
                    elif fault == 'wrong_messages':
                        records[0]['event']['messages'] = []
                    elif fault == 'wrong_token':
                        records[0]['event']['token_ids'] = [1, 2]
                    rewrite(individual, records[0])
                    rewrite(directory / 'EXPERIENCES.json', records)
                with self.assertRaises((ValueError, OSError)):
                    runner.load_reused_experiences(root, expected_base_sha256='a' * 64)

    def test_original_metadata_and_base_are_required(self):
        for key, value in (('schema', 'other'), ('master', 'other'), ('status', 'INCOMPLETE'),
                           ('admitted_events', 7), ('frozen_base_unchanged', False), ('fits', 1)):
            with self.subTest(key=key), TemporaryDirectory() as temporary:
                root = original_fixture(Path(temporary) / 'original')
                result = runner.source.read(root / 'RESULT.json')
                result[key] = value
                rewrite(root / 'RESULT.json', result)
                with self.assertRaises(ValueError):
                    runner.load_reused_experiences(root, expected_base_sha256='a' * 64)
        with TemporaryDirectory() as temporary:
            root = original_fixture(Path(temporary) / 'original')
            with self.assertRaisesRegex(ValueError, 'base_binding'):
                runner.load_reused_experiences(root, expected_base_sha256='b' * 64)

    def test_reuse_calls_actor_only_preserves_source_bytes_and_strips_explicit_guide(self):
        with TemporaryDirectory() as temporary:
            root = original_fixture(Path(temporary) / 'original')
            before = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file()}
            loaded = runner.load_reused_experiences(root, expected_base_sha256='a' * 64)
            output = Path(temporary) / 'successor'
            output.mkdir()
            actor = PublicReadingActor()
            engine = Mock(generate=actor)
            with patch.object(runner.cue, 'GUIDANCE', runner.EXPLICIT_GUIDANCE):
                result = runner.collect(engine, output, reused_experiences=loaded)
            self.assertEqual(result['physical_model_calls'], 20)
            self.assertEqual(result['physical_actor_calls'], 20)
            self.assertEqual(result['new_exploration_event_calls'], 0)
            self.assertEqual(result['experiences_reused'], 8)
            self.assertEqual(result['cue_task_denominator'], 8)
            self.assertEqual(result['selected_successes'], 8)
            self.assertEqual(result['fits'], 0)
            self.assertTrue(all(message[0]['content'] == runner.cue.controller.PUBLIC_SYSTEM + runner.EXPLICIT_GUIDANCE
                                for message in actor.messages))
            for index, bank in enumerate(loaded['banks']):
                collection = runner.source.read(output / ('BANK_%02d/CUE_COLLECTION.json' % index))
                self.assertEqual(collection['raw_memory_by_address'], bank['raw_memory_by_address'])
                self.assertEqual(len(collection['episodes']), 4)
                for row in collection['student_rows']:
                    self.assertNotIn(runner.EXPLICIT_GUIDANCE, json.dumps(row['prefix']))
                for fact in bank['bank']:
                    for value in fact.values():
                        if type(value) is str:
                            self.assertNotIn(value, runner.EXPLICIT_GUIDANCE)
            self.assertEqual(before, {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file()})

    def test_reused_cue_errors_cannot_complete(self):
        with TemporaryDirectory() as temporary:
            root = original_fixture(Path(temporary) / 'original')
            loaded = runner.load_reused_experiences(root, expected_base_sha256='a' * 64)
            output = Path(temporary) / 'successor'
            output.mkdir()
            engine = Mock(generate=Mock(side_effect=RuntimeError('native error')))
            with patch.object(runner.cue, 'GUIDANCE', runner.EXPLICIT_GUIDANCE), \
                    self.assertRaisesRegex(ValueError, 'native_callback_failure'):
                runner.collect(engine, output, reused_experiences=loaded)
            self.assertEqual(engine.generate.call_count, 8)

    def test_reuse_reaches_but_never_exceeds_twenty_four_actor_calls(self):
        with TemporaryDirectory() as temporary:
            root = original_fixture(Path(temporary) / 'original')
            loaded = runner.load_reused_experiences(root, expected_base_sha256='a' * 64)
            output = Path(temporary) / 'successor'
            output.mkdir()
            matching_actor = PublicReadingActor()

            def two_reads_then_route(messages):
                task = dict(line.split(' ', 1) for line in messages[1]['content'].splitlines()[1:])
                reads = sum(message['role'] == 'assistant' and message['content'].startswith('READ EVENT ')
                            for message in messages)
                if reads < 2:
                    return generation('READ EVENT ' + task['EVENTS'].split(',')[reads])
                return matching_actor(messages)

            engine = Mock(generate=Mock(side_effect=two_reads_then_route))
            with patch.object(runner.cue, 'GUIDANCE', runner.EXPLICIT_GUIDANCE):
                result = runner.collect(engine, output, reused_experiences=loaded)
            self.assertEqual(result['physical_actor_calls'], 24)
            self.assertEqual(engine.generate.call_count, 24)
            self.assertEqual(result['new_exploration_event_calls'], 0)
            self.assertEqual(result['selected_successes'], 8)

    def test_both_cli_flags_required_before_native_loading(self):
        common = ['--model-dir', 'unused', '--expected-base-sha256', 'a' * 64,
                  '--output', 'unused-output', '--gpu-uuid', 'GPU-test']
        for extra in (['--reuse-experiences', 'unused'], ['--explicit-cue-strategy']):
            with self.subTest(extra=extra), patch.object(runner.source.native, 'load_local_tokenizer') as load, \
                    self.assertRaises(SystemExit):
                runner.main(common + extra)
            load.assert_not_called()

    def test_cli_records_guidance_and_validates_before_native_imports(self):
        with TemporaryDirectory() as temporary:
            root = original_fixture(Path(temporary) / 'original')
            output = Path(temporary) / 'successor'
            arguments = ['--model-dir', 'unused', '--expected-base-sha256', 'a' * 64,
                '--output', str(output), '--gpu-uuid', 'GPU-test', '--reuse-experiences', str(root), '--explicit-cue-strategy']
            actor = PublicReadingActor()
            engine = Mock(generate=actor, runtime={'test': 'scripted CPU only'})
            original_guidance = runner.cue.GUIDANCE
            with patch.dict(os.environ, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES='GPU-test'), \
                    patch.object(runner.source.native, 'load_local_tokenizer', return_value=object()), \
                    patch.object(runner.source.native, 'tokenizer_signature', return_value={}), \
                    patch.object(runner.source, 'Engine', return_value=engine):
                runner.main(arguments)
            request = runner.source.read(output / 'REQUEST.json')
            self.assertEqual(request['schema'], 'DEV_GUIDED_EXTERNAL_EVENT_CUE_REUSE_V1')
            self.assertEqual(request['guidance'], runner.EXPLICIT_GUIDANCE)
            self.assertEqual(request['guidance_sha256'], sha256(runner.EXPLICIT_GUIDANCE.encode()).hexdigest())
            self.assertEqual(runner.cue.GUIDANCE, original_guidance)
            self.assertEqual(runner.source.read(output / 'RESULT.json')['status'], 'COLLECTION_COMPLETE_NO_FIT')
            engine.verify_base.assert_called_once()
            (root / 'BANK_00/EXPERIENCE_01.json').unlink()
            arguments[arguments.index('--output') + 1] = str(Path(temporary) / 'invalid-successor')
            with patch.dict(os.environ, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES='GPU-test'), \
                    patch.object(runner.source.native, 'load_local_tokenizer') as load, \
                    self.assertRaises(ValueError):
                runner.main(arguments)
            load.assert_not_called()
            self.assertEqual(runner.cue.GUIDANCE, original_guidance)


if __name__ == "__main__":
    unittest.main()
