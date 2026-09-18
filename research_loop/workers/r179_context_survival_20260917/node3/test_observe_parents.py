import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SOURCE = Path(__file__).with_name('observe_parents.py')
SPEC = importlib.util.spec_from_file_location('observe_parents', SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ParentObservationTests(unittest.TestCase):
    def test_only_metadata_is_exported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            control = root / 'parents/physical0'
            attempt = control / 'parent/parent_000000'
            attempt.mkdir(parents=True)
            (control / 'BINDING.json').write_text(json.dumps(dict(physical=0,
                row=dict(active_host_root='/recovery/run1'))))
            (attempt / 'RESULT.json').write_text(json.dumps(dict(status='PUBLISHED',
                response={'message': 'DO_NOT_EXPORT_THIS_TEXT'}, source_response_count=133)))
            (attempt / 'DELIVERED.json').write_text(json.dumps(dict(
                consumption={'record_index': 5459, 'record_sha256': 'a' * 64})))
            result = MODULE.observe(root)
            self.assertNotIn('DO_NOT_EXPORT', json.dumps(result))
            self.assertEqual(result['rows'][0]['statuses'], {'PUBLISHED': 1})
            self.assertEqual(result['rows'][0]['registered_deliveries'], 1)
            self.assertTrue(result['registration_not_verified_rendered_exposure'])

    def test_pending_call_not_counted_as_delivered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            control = root / 'parents/physical0'
            (control / 'parent/parent_000000').mkdir(parents=True)
            (control / 'BINDING.json').write_text(json.dumps(dict(physical=0,
                row=dict(active_host_root='/recovery/run1'))))
            result = MODULE.observe(root)['rows'][0]
            self.assertEqual(result['registered_deliveries'], 0)
            self.assertEqual(result['statuses'], {})
            self.assertEqual(result['calls'][0]['status'], 'PENDING')


if __name__ == '__main__':
    unittest.main()
