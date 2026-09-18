"""CPU fixtures for an opt-in V3 parser, not model or content evidence."""

from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from gpu import astra_rich_action_first_v3_collection as runner
from tests.test_astra_rich_trajectory_collection import fixture, cli, RichEngine
from tests.test_astra_rich_action_first_collection import successor_cli
from tests import test_experienced_event_rich_trajectory as fixtures


class V3NativeTests(unittest.TestCase):
    def test_bound_protocol_guard_and_v2_defaults(self):
        protocol = Path(runner.__file__).resolve().parents[1]/runner.PROTOCOL_PATH
        self.assertEqual(runner.source.file_hash(protocol), runner.PROTOCOL_SHA)
        self.assertEqual(runner.CONFIG.execution_policy, runner.rich.ACTION_FIRST_V3)
        self.assertEqual(runner.v2.SCHEMA, 'DEV_RICH_ACTION_FIRST_NATIVE_V2')
        self.assertEqual(runner.v2.PROTOCOL_SHA, '509f85c17d4be373eb1e917ee11e5134dcb447257a376163fe6a995d533eece9')
        guard = Path(runner.__file__).with_name('astra_rich_action_first_v3_collection_guard.sh').read_text()
        self.assertIn('3960', guard)
        self.assertIn('astra_rich_action_first_v3_collection', guard)
        self.assertIn('--phase teach', guard)
        self.assertIn('1790380800 - 21600', guard)
        self.assertNotIn('--phase expose', guard)
        self.assertNotIn('--phase train', guard)

    def test_prepare_no_model_native_colon_rows_and_actual_joins(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            runner.original.main(cli(root, state, 'expose'))
            stack.enter_context(patch.object(runner.v2, 'V1_RICH_SHA', runner.source.file_hash(runner.rich.__file__)))
            with patch.object(runner.source, 'Engine', side_effect=AssertionError('no model in prepare')):
                prepared = runner.main(successor_cli(root, state, 'prepare'))
            self.assertEqual(prepared['model_calls'], 0)
            self.assertEqual(prepared['binding']['execution_policy'], runner.rich.ACTION_FIRST_V3)
            self.assertEqual(prepared['binding']['v2_loader_binding']['execution_policy'], runner.rich.ACTION_FIRST_V2)

            def generate(engine, messages, *, max_new_tokens):
                self.assertEqual(max_new_tokens, 512)
                engine.native_calls += 1
                return fixtures.ActionFirstV3Tests.colon_child(messages)

            with patch.object(RichEngine, 'generate', generate):
                result = runner.main(successor_cli(root, state, 'teach'))
            self.assertEqual((result['status'], result['model_calls'], result['complete_episodes']), ('COMPLETE', 96, 16))
            self.assertEqual(result['row_counts'], dict.fromkeys(runner.rich.FORMS, 96))
            self.assertEqual(result['adapter_state_after'], runner.original.PARENT_STATE)
            self.assertFalse(result['fit_ready'] or result['trainingAllowed'])
            self.assertEqual((result['fits'], result['updates']), (0, 0))
            document = runner.source.json.loads((root/'successor_teach/LESSONS.json').read_text())
            for capture in document['captures']:
                actual = runner.source.json.loads((root/f"successor_teach/CALL_{capture['call_index']:03d}.json").read_text())
                for key in ('messages', 'response', 'error'):
                    self.assertEqual(capture[key], actual[key])
            self.assertEqual(runner.rich.replay_teaching(document), document['rows'])
            with self.assertRaises(FileExistsError):
                runner.main(successor_cli(root, state, 'teach'))

    def test_invalid_raw_retained_and_no_replacement_or_content_promotion(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            runner.original.main(cli(root, state, 'expose'))
            stack.enter_context(patch.object(runner.v2, 'V1_RICH_SHA', runner.source.file_hash(runner.rich.__file__)))

            def generate(engine, messages, *, max_new_tokens):
                response = fixtures.ActionFirstV3Tests.colon_child(messages)
                response['raw'] = response['raw'].replace('RATIONALE: ', 'Rationale: ', 1)
                return response

            with patch.object(RichEngine, 'generate', generate):
                result = runner.main(successor_cli(root, state, 'teach'))
            self.assertEqual((result['status'], result['model_calls'], result['complete_episodes']), ('COMPLETE', 16, 0))
            self.assertEqual(result['row_counts'], dict.fromkeys(runner.rich.FORMS, 0))
            self.assertEqual(sum(result['execution_rejections'].values()), 16)
            self.assertFalse(result['fit_ready'])

    def test_source_drift_rejected_before_model(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            runner.original.main(cli(root, state, 'expose'))
            stack.enter_context(patch.object(runner.v2, 'V1_RICH_SHA', runner.source.file_hash(runner.rich.__file__)))
            capture = root/'shard-0/expose/CALL_000.json'
            capture.write_text(capture.read_text()+' ')
            with patch.object(runner.source, 'Engine', side_effect=AssertionError('no model before source validation')):
                with self.assertRaises(ValueError):
                    runner.main(successor_cli(root, state, 'prepare'))


if __name__ == '__main__':
    unittest.main()
