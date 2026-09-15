from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_r118_final_custody as final


class FinalCustodyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.plan = dict(start_unix=final.original.START, end_unix=final.original.END,
            lease_end_unix=final.original.END+21600, original_root=str(self.root/'original'),
            root=str(self.root/'evaluation'), quota_claim=str(self.root/'claim.json'), quota_id='quota',
            evaluation_chain=[dict(root=str(self.root/'oldest')), dict(root=str(self.root/'newer'))])
        Path(self.plan['root']).mkdir()
        final.write(Path(self.plan['root'])/'PLAN.json', dict(test=True))

    def test_no_early_attempt_or_sealed_inspection(self):
        with patch.object(final.original, 'prior_attempts') as inspect:
            with self.assertRaisesRegex(ValueError, 'FINAL_clock_gate'):
                final.attempts(self.plan, final.original.START-1)
            inspect.assert_not_called()

    def test_recursive_oldest_partial_blocks_claim(self):
        oldest = self.root/'oldest'
        oldest.mkdir()
        (oldest/'CALL_0001.request.json').write_text('{}')
        with patch.object(final.time, 'time', return_value=final.original.START+1):
            with self.assertRaisesRegex(ValueError, 'prior_FINAL_attempt'):
                final.claim(self.plan)
        self.assertFalse(Path(self.plan['quota_claim']).exists())

    def test_claim_one_original_quota_no_reset(self):
        with patch.object(final.time, 'time', return_value=final.original.START+1):
            reference = final.claim(self.plan)
            with self.assertRaises(FileExistsError):
                final.claim(self.plan)
        self.assertEqual(final.original.bound(reference)['native_cap'], 8)

    def test_claim_after_window_rejected(self):
        with patch.object(final.time, 'time', return_value=final.original.END):
            with self.assertRaisesRegex(ValueError, 'FINAL_clock_gate'):
                final.claim(self.plan)

    def test_other_namespace_claim_rejected(self):
        final.write(self.plan['quota_claim'], dict(quota_id='quota', root='other', plan={}))
        with patch.object(final, 'custody', return_value={}), \
                patch.object(final.time, 'time', return_value=final.original.START+1):
            with self.assertRaisesRegex(ValueError, 'no_other_quota_owner'):
                final.release(self.plan)

    def test_recursive_lineage_preserves_original_quota(self):
        oldest = self.root/'old.json'
        final.write(oldest, dict(native_cap=8, parent_cap=0, root='old'))
        newer = self.root/'new.json'
        final.write(newer, dict(native_cap=8, parent_cap=0, root='new', previous_evaluation_plan=final.ref(oldest)))
        self.assertEqual([entry['root'] for entry in final.evaluation_chain(final.ref(newer))], ['new', 'old'])

    def test_more_calls_or_parent_lineage_rejected(self):
        for number, values in enumerate(((9, 0), (8, 1))):
            path = self.root/f'bad{number}.json'
            final.write(path, dict(native_cap=values[0], parent_cap=values[1], root='bad'))
            with self.assertRaisesRegex(ValueError, 'same_eight'):
                final.evaluation_chain(final.ref(path))

    def custody_fixture(self):
        service = self.root/'services/lane1'
        service.mkdir(parents=True)
        original = self.root/'original'
        original.mkdir()
        final.write(original/'COUNTERS.json', dict(native=274, parent=60))
        docs = {}
        def record(name, document):
            path = self.root/(name+'.json')
            final.write(path, document)
            docs[name] = final.ref(path)
            return docs[name]
        child = dict(pid=11)
        terminal = record('terminal', dict(status='FAILED', identity=child, native_alive=False, no_retry=True))
        failure = record('failure', dict(session_sha256=final.recovery.FAILED_SESSION, retry_allowed=False))
        failed = record('failed', dict(status='CPU_CHILD_EXITED_BEFORE_MODEL_BOOTSTRAP', native_calls=0,
            signals=0, native=child, guard_terminal=terminal, failed_dispatch=failure))
        boundary = record('boundary', dict(preserved_files={}, counters=dict(native=274, parent=60)))
        released = record('released', dict(status='RELEASED', root=str(original), predecessors=[child], boundary=boundary))
        runtime = record('runtime', dict(release=released))
        timer = record('timer', dict(identity=dict(pid=12)))
        retired = record('retired', dict(release=released, timers=[dict(record=timer, identity=dict(pid=12), actual_eval_calls=0)]))
        evidence = record('evidence', dict(service=str(service), runtime=runtime, release=released,
            second_failure=failed, timer_retirement=retired))
        plan = dict(physical=1, original_root=str(original), failed_startup_custody=evidence)
        return service, plan, docs

    def run_custody(self, plan, alive=False):
        with patch.object(final, 'SERVICES', self.root/'services'), \
                patch.object(final.life, 'alive', return_value=alive), \
                patch.object(final.life.boundary, 'unchanged'), \
                patch.object(final.life.drain, 'live_readout_identities', return_value=[]):
            return final.custody(plan)

    def test_real_failed_release_without_fake_clean_or_expiry_extension(self):
        service, plan, docs = self.custody_fixture()
        result = self.run_custody(plan)
        self.assertTrue(result['no_fabricated_clean_release'])
        self.assertFalse((service/'CLEAN_RELEASE.json').exists())

    def test_new_guard_or_launch_forbids_never_started_disposition(self):
        service, plan, docs = self.custody_fixture()
        (service/'LAUNCH.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'never_dispatched'):
            self.run_custody(plan)

    def test_live_predecessor_rejected(self):
        service, plan, docs = self.custody_fixture()
        with self.assertRaisesRegex(ValueError, 'still_live'):
            self.run_custody(plan, alive=True)

    def test_charges_cannot_change(self):
        service, plan, docs = self.custody_fixture()
        (Path(plan['original_root'])/'COUNTERS.json').write_text('{"native":275,"parent":60}')
        with self.assertRaisesRegex(ValueError, 'no_charge_reset'):
            self.run_custody(plan)

    def test_original_capture_and_native_implementation_reused(self):
        functions = final.functions()
        self.assertIs(functions['capture'].__code__, final.original.capture.__code__)
        self.assertIs(functions['native'].__code__, final.original.native.__code__)
        self.assertIs(functions['native'].__globals__['release'], final.release)
        self.assertEqual(functions['native'].__globals__['MODULE'], final.MODULE)


if __name__ == '__main__':
    unittest.main()
