import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location('fleet_source_pipeline', Path(__file__).with_name('fleet_source_pipeline.py'))
pipeline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pipeline)
protocol = pipeline.protocol


class PipelineTests(unittest.TestCase):
    def test_allocation_carries_reads_and_two_hops(self):
        result = pipeline.allocation(dict(journal_stat_bytes=600, initial_adapter_stat_bytes=10),
            dict(metadata=50, adapter=20))
        self.assertEqual(result['metadata_read_cap'], 650 + pipeline.OBSERVATION_RESERVATION + pipeline.HEADROOM)
        self.assertEqual(result['adapter_read_cap'], 100 + 16 * pipeline.MIB)
        self.assertEqual(result['adapter_hops_reserved'], 2)

    def test_allocation_refuses_per_life_overflow(self):
        with self.assertRaisesRegex(ValueError, 'per_life_2GiB_cap'):
            pipeline.allocation(dict(journal_stat_bytes=2*pipeline.GIB, initial_adapter_stat_bytes=1),
                dict(metadata=0, adapter=0))

    def test_stat_does_not_open_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records = root / 'stream/records'
            records.mkdir(parents=True)
            (records / '00000000000000000000.json').write_bytes(b'private TRAIN')
            adapter = root / 'checkpoints/initial/adapter'
            adapter.mkdir(parents=True)
            (adapter.parent / 'COMMIT.json').write_bytes(b'{}')
            (adapter / 'adapter_model.safetensors').write_bytes(b'private tensor')
            with patch.object(Path, 'read_bytes', side_effect=AssertionError('no content')):
                result = pipeline.stat_life(dict(storage_root=str(root), life_id='life'))
            self.assertEqual(result['source_content_bytes_read'], 0)
            self.assertEqual(result['journal_stat_bytes'], len(b'private TRAIN'))

    def test_stat_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / 'stream/records'
            directory.mkdir(parents=True)
            (directory / '00000000000000000000.json').symlink_to('/etc/passwd')
            with self.assertRaisesRegex(ValueError, 'no_source_symlink'):
                pipeline.stat_life(dict(storage_root=str(root), life_id='life'))

    def record(self):
        context = dict(system_prompt='Original system', birth_prompt='Original birth')
        state = dict(history=dict(context, events=[dict(actor='child', split='TRAIN', origin='TRAIN_COLLECTION',
            text='菊花与教室'), dict(actor='parent', split='TRAIN', origin='TRAIN_COLLECTION', text='Not child')]))
        return context, dict(document=dict(resume_state=dict(state=state, sha256=protocol.digest(state))))

    def test_original_language_survives_without_negative_proxy(self):
        context, record = self.record()
        result = pipeline.original_language_witnesses(record, context)
        self.assertEqual([entry['text'] for entry in result['witnesses']], ['菊花与教室'])
        self.assertEqual(result['lexical_instrument'], 'NOT_APPLIED_NONCOVERAGE_NOT_NEGATIVE')
        self.assertFalse(result['parent_access'])

    def test_held_origin_refused(self):
        context, record = self.record()
        wrapped = record['document']['resume_state']
        wrapped['state']['history']['events'][0]['split'] = 'HELD'
        wrapped['sha256'] = protocol.digest(wrapped['state'])
        with self.assertRaisesRegex(ValueError, 'no_evaluation_or_parent_history'):
            pipeline.original_language_witnesses(record, context)

    def test_birth_change_refused(self):
        context, record = self.record()
        context['birth_prompt'] = 'Different'
        with self.assertRaisesRegex(ValueError, 'unchanged_original_birth'):
            pipeline.original_language_witnesses(record, context)

    def test_identity_includes_boot_and_ticks(self):
        expected = dict(pid=1, start_ticks='20', boot_id='boot')
        for field in expected:
            actual = copy.deepcopy(expected)
            actual[field] = 'changed'
            self.assertFalse(pipeline.exact_identity(expected, actual))
        self.assertTrue(pipeline.exact_identity(expected, expected))


if __name__ == '__main__':
    unittest.main()
