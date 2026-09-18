import unittest
from unittest.mock import patch

from gpu.orch_r132_kernel_bridge import result_summary
from gpu import orch_r132_kernel_bridge as bridge


class ResultSummaryTests(unittest.TestCase):
    def test_explicit_nfkc_kernel_request_preserves_policy_for_origin_verification(self):
        raw = '```python\nvalue = ９８\n```'
        record = dict(kind='RESPONSE', sha256='a' * 64, document=dict(response=dict(raw=raw)))
        with patch.object(bridge, 'read_regular', return_value=b'fixture'), \
                patch.object(bridge, 'read_document', return_value=record), \
                patch.object(bridge, 'verify_source_origin') as origin:
            request = bridge.child_request('/not_dispatched', 1, code_policy=bridge.code_blocks.NFKC_POLICY)
        self.assertEqual(request['source'], 'value = 98\n')
        self.assertEqual(origin.call_args.args[-1], bridge.code_blocks.NFKC_POLICY)

    def result(self, status='CORRECT'):
        return dict(schema='R132_KERNEL_RESULT_V1', origin={'child_generated': True},
                    status=status, launch_attempted=True, cgroup_removed=True,
                    capture={'returncode': 0}, measurement={'status': status, 'cases': {
                        str(size): dict(correct=True, reference_ms=1.0, candidate_ms=0.5,
                                        reported_speedup=2.0)
                        for size in (1, 1024, 65537, 1048576)}})

    def test_measurement_summary_has_qualified_actual_times(self):
        text = result_summary(self.result())
        self.assertIn('Length 65537: correctness=True', text)
        self.assertIn('reported_speedup=2.0', text)
        self.assertIn('not proof of general speedup', text)

    def test_builder_fixture_never_delivered_as_child_result(self):
        result = self.result()
        result['origin']['child_generated'] = False
        with self.assertRaisesRegex(ValueError, 'actual_child_origin'):
            result_summary(result)

    def test_unexecuted_or_unreaped_success_rejected(self):
        for key in ('launch_attempted', 'cgroup_removed'):
            result = self.result()
            result[key] = False
            with self.assertRaisesRegex(ValueError, 'executed_and_reaped_kernel'):
                result_summary(result)

    def test_all_shapes_required(self):
        result = self.result()
        del result['measurement']['cases']['1']
        with self.assertRaisesRegex(ValueError, 'all_task_shapes'):
            result_summary(result)

    def test_failure_cannot_claim_correctness(self):
        result = self.result('KERNEL_ERROR')
        result['measurement'] = {'reported_error': {'error': 'compile failed'}}
        text = result_summary(result)
        self.assertIn('compile failed', text)
        self.assertIn('does not establish a correct, faster kernel', text)
        self.assertNotIn('reported_speedup=', text)

    def test_unfinished_status_rejected(self):
        with self.assertRaisesRegex(ValueError, 'finished_kernel_result_status'):
            result_summary(self.result('DISPATCH_INCOMPLETE'))

    def test_invalid_candidate_feedback_does_not_claim_execution(self):
        result = self.result('REQUEST_REJECTED')
        result.update(launch_attempted=False, error='imports_not_allowed')
        text = result_summary(result)
        self.assertIn('REQUEST_REJECTED', text)
        self.assertIn('imports_not_allowed', text)
        self.assertNotIn('reported_speedup=', text)


if __name__ == '__main__':
    unittest.main()
