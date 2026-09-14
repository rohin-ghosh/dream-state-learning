"""CPU native-interface fixtures, not actual model or GPU evidence."""

from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from gpu import astra_rich_action_first_collection as runner
from tests.test_astra_rich_trajectory_collection import fixture, cli


def successor_cli(root, state, phase, output=None):
    return ['--bundle',str(root/'bundle'),'--bundle-sha',state.bundle_sha,
            '--model-dir',str(root/'model'),'--exposure',str(root/'shard-0/expose'),
            '--shard','0','--gpu-uuid','fake-gpu','--phase',phase,
            '--output',str(output or root/('successor_'+phase))]


class ActionFirstNativeTests(unittest.TestCase):
    def test_bound_protocol_and_guard(self):
        protocol = Path(runner.__file__).resolve().parents[1]/runner.PROTOCOL_PATH
        self.assertEqual(runner.source.file_hash(protocol),runner.PROTOCOL_SHA)
        self.assertEqual(runner.V1_RICH_SHA,'ed0e59ed9719908f616bfd57d5b27c68ae58ec9cf45a8765687569bed1b3fb0d')
        guard = Path(runner.__file__).with_name('astra_rich_action_first_collection_guard.sh').read_text()
        self.assertIn('scanner.py',guard)
        self.assertIn('3960',guard)
        self.assertIn('--phase teach',guard)
        self.assertNotIn('--phase expose',guard)

    def test_reuses_exposure_and_retains_unreviewed_paired_candidates(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root,stack)
            runner.original.main(cli(root,state,'expose'))
            stack.enter_context(patch.object(runner,'V1_RICH_SHA',runner.source.file_hash(runner.rich.__file__)))
            with patch.object(runner.source,'Engine',side_effect=AssertionError('prepare cannot load model')):
                result = runner.main(successor_cli(root,state,'prepare'))
            self.assertEqual(result['model_calls'],0)
            result = runner.main(successor_cli(root,state,'teach'))
            self.assertEqual(result['status'],'COMPLETE')
            self.assertEqual(result['model_calls'],96)
            self.assertEqual(result['complete_episodes'],16)
            self.assertEqual(result['row_counts'],dict(TERSE=96,RICH=96,RICH_ACTION_ONLY=96))
            self.assertFalse(result['fit_ready'])
            self.assertFalse(result['trainingAllowed'])
            self.assertEqual(result['fits'],0)
            self.assertEqual(result['adapter_state_after'],runner.original.PARENT_STATE)
            with self.assertRaises(FileExistsError):
                runner.main(successor_cli(root,state,'teach'))

    def test_source_drift_fails_before_native_call(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root,stack)
            runner.original.main(cli(root,state,'expose'))
            stack.enter_context(patch.object(runner,'V1_RICH_SHA',runner.source.file_hash(runner.rich.__file__)))
            capture = root/'shard-0/expose/CALL_000.json'
            capture.write_text(capture.read_text()+' ')
            with patch.object(runner.source,'Engine',side_effect=AssertionError('unverified source cannot load')):
                with self.assertRaises(ValueError):
                    runner.main(successor_cli(root,state,'prepare'))
            self.assertTrue((root/'successor_prepare/FAILED.json').exists())


if __name__ == '__main__':
    unittest.main()
