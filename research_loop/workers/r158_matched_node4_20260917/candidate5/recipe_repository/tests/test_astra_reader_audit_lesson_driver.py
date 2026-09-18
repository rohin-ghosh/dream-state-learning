"""Native-dispatch plumbing with a fake engine and real exclusive captures."""

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from gpu import astra_reader_audit_lesson as runner
from tests.test_experienced_event_reader_audit_lesson import events


class DriverTests(unittest.TestCase):
    def inputs(self):
        return dict(after=dict(arguments=dict(model_dir='model', adapter_dir='adapter'),
                               loaded_adapter_state_sha256='actor'),
                    provenance=dict(source='fixture'),
                    dev=runner.lesson.build_cases(events('DEV'), split='DEV'),
                    held=runner.lesson.build_cases(events('HELD'), split='HELD'))

    def test_collect_and_full_child_row_replay_without_duplicate_writes(self):
        inputs = self.inputs()
        cases = inputs['held']['cases'] + inputs['dev']['cases']
        answers = iter(case['expected'] for case in cases)
        engine = MagicMock()
        engine.runtime = {}
        engine.model.named_parameters.return_value = [('layer.lora_A.weight', object())]
        engine.generate.side_effect = lambda messages, **kwargs: dict(raw=next(answers), terminal=True,
            truncated=False, messages=deepcopy(messages))
        with TemporaryDirectory() as temporary:
            root = Path(temporary) / 'collect'
            with patch.dict('os.environ', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES='gpu'), \
                    patch.object(runner, 'load_inputs', return_value=inputs), \
                    patch.object(runner.source.native, 'load_local_tokenizer', return_value=object()), \
                    patch.object(runner.source, 'Engine', return_value=engine), \
                    patch.dict('sys.modules', {'organism_v6.pcfl_vertical_train':
                        SimpleNamespace(_state_hash=lambda parameters: 'actor')}):
                runner.main(['--phase', 'collect', '--after-source', 'source', '--output', str(root),
                             '--gpu-uuid', 'gpu'])
            result = runner.source.read(root / 'RESULT.json')
            self.assertEqual(result['status'], 'LESSON_READY')
            self.assertEqual(result['model_calls'], 80)
            self.assertEqual(len(list(root.glob('CALL_*.json'))), 80)
            rows, receipt = runner.replay_lesson(root, inputs)
            self.assertEqual(len(rows), 64)
            self.assertEqual(receipt, runner.source.file_hash(root / 'RESULT.json'))
            for row in rows:
                self.assertNotIn(runner.lesson.PARENT_GUIDANCE, str(row['prefix']))

    def test_prepare_never_loads_tokenizer_or_model(self):
        with TemporaryDirectory() as temporary, \
                patch.dict('os.environ', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1'), \
                patch.object(runner, 'load_inputs', return_value=self.inputs()), \
                patch.object(runner.source.native, 'load_local_tokenizer') as tokenizer, \
                patch.object(runner.source, 'Engine') as engine:
            root = Path(temporary) / 'prepare'
            runner.main(['--phase', 'prepare', '--after-source', 'source', '--output', str(root),
                         '--gpu-uuid', 'gpu'])
            engine.assert_not_called()
            tokenizer.assert_not_called()
            self.assertEqual(runner.source.read(root / 'RESULT.json')['status'], 'PREPARED_NO_MODEL')

    def test_unbound_training_is_rejected_before_source_or_native(self):
        with patch.object(runner, 'load_inputs') as load:
            with self.assertRaises(ValueError):
                runner.main(['--phase', 'train', '--after-source', 'source', '--output', 'unused',
                             '--gpu-uuid', 'gpu'])
            load.assert_not_called()

    def test_memory_views_do_not_create_independent_events(self):
        rows = [dict(event='event', messages=[dict(content='raw')])] * 8
        self.assertEqual(runner.events_from_rows(rows), [dict(event='event', raw='raw')])


if __name__ == '__main__':
    unittest.main()
