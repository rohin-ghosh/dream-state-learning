import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SOURCE = Path(__file__).with_name('parent_recovery.py')
SPEC = importlib.util.spec_from_file_location('parent_recovery', SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ParentRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(saved_counts={'REQUEST': 129, 'RESPONSE': 129},
            terminal_counts={'REQUEST': 132, 'RESPONSE': 132}, saved_record_index=5453,
            active_host_root='/localhome/local-rohing/orch_recovery/control0/run1',
            logical_root='/localhome/local-rohing/orch_original/run1')
        self.state = dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', record_count=5456,
            request_count=129, response_count=129, head_sha256='a' * 64,
            events=[dict(actor='child', text='real saved text', record_index=5450)],
            boundaries=[dict(response_count=129, record_index=5450, next_request_index=None)],
            consumed_inbox={})

    def test_saved_prefix_does_not_create_novel_parent_slot(self):
        result = MODULE.recover_clock(self.state, self.row)
        self.assertEqual(result['request_count'], 132)
        self.assertEqual(result['response_count'], 132)
        self.assertEqual(result['journal_request_count'], 129)
        self.assertLess(result['request_count'], 132 + 1)

    def test_first_novel_boundary_has_novel_lifetime_clock(self):
        self.state['request_count'] = 130
        result = MODULE.recover_clock(self.state, self.row)
        self.assertEqual(result['request_count'], 133)
        self.assertEqual(result['response_count'], 132)

    def test_source_text_and_saved_boundary_are_not_rewritten(self):
        original = copy.deepcopy(self.state)
        result = MODULE.recover_clock(self.state, self.row)
        self.assertEqual(self.state, original)
        for field in ('events', 'head_sha256', 'record_count', 'consumed_inbox', 'boundaries'):
            self.assertEqual(result[field], original[field])

    def test_only_post_recovery_boundaries_receive_offsets(self):
        self.state['response_count'] = 130
        self.state['boundaries'].append(dict(response_count=130, record_index=5456, next_request_index=5457))
        result = MODULE.recover_clock(self.state, self.row)
        self.assertEqual(result['boundaries'][0]['response_count'], 129)
        self.assertEqual(result['boundaries'][1]['response_count'], 133)
        self.assertEqual(result['boundaries'][1]['journal_response_count'], 130)

    def test_zero_offset_preserves_count(self):
        self.row['terminal_counts'] = dict(self.row['saved_counts'])
        result = MODULE.recover_clock(self.state, self.row)
        self.assertEqual(result['response_count'], 129)

    def test_rejects_bad_counts_and_wrong_schema(self):
        for field, value in (('request_count', 128), ('response_count', -1),
                             ('request_count', True), ('schema', 'SEALED_SNAPSHOT')):
            with self.subTest(field=field, value=value):
                state = dict(self.state, **{field: value})
                with self.assertRaises(ValueError):
                    MODULE.recover_clock(state, self.row)
        self.row['terminal_counts']['REQUEST'] = 128
        with self.assertRaises(ValueError):
            MODULE.recover_clock(self.state, self.row)

    def test_config_preserves_parent_policy_and_counts_reserved_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            predecessor = Path(directory)
            (predecessor / 'STARTED.json').write_text(json.dumps({'branch': 'support'}))
            config = dict(node='ovx2', root=self.row['logical_root'], hard_end_unix=1789668000,
                programme='emotional_support', parent_style='unchanged', cadence_responses=1,
                principles_path='/frozen/PRINCIPLES.md', principles_sha256='b' * 64,
                programme_path='/frozen/PROGRAMME.json', programme_sha256='c' * 64,
                parent_reasoning_effort='low', schedule_on='request')
            result = MODULE.recovered_config(config, self.row,
                dict(clock='request_count', cursor=135), predecessor, '/new/source')
            for field in ('programme', 'parent_style', 'cadence_responses', 'principles_path',
                          'principles_sha256', 'programme_path', 'programme_sha256',
                          'parent_reasoning_effort', 'schedule_on'):
                self.assertEqual(result[field], config[field])
            self.assertEqual(result['start_after_request_count'], 135)
            self.assertEqual(result['start_after_response_count'], 132)
            self.assertEqual(result['root'], self.row['active_host_root'])
            self.assertEqual(result['hard_end_unix'], 1789689000)
            self.assertEqual(config['hard_end_unix'], 1789668000)

    def test_bound_evidence_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt.json'
            path.write_text('{}')
            reference = MODULE.reference(path)
            MODULE.verify(reference)
            path.write_text('{"changed": true}')
            with self.assertRaises(ValueError):
                MODULE.verify(reference)


if __name__ == '__main__':
    unittest.main()
