import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    import orch_r119_l1_gen7_post_r127 as candidate
except ImportError:
    from gpu import orch_r119_l1_gen7_post_r127 as candidate


class CustodyTests(unittest.TestCase):
    def test_exact_cursor_and_original_allowance(self):
        release = dict(status='RELEASED',no_replay=True,boundary=dict(progress=dict(calls=21259,inherited_calls=15842,batch=302,position=17),next_call=21260,next_cursor=dict(batch=302,position=19)))
        self.assertEqual(candidate.cursor(release)['calls'],21259)
        release['boundary']['progress']['inherited_calls']=21259
        with self.assertRaises(AssertionError):candidate.cursor(release)

    def fixture(self, root):
        plan = root/'PLAN.json'
        candidate.write(root/'START.json',dict(pid=999991,plan=dict(path=str(plan),sha256=candidate.PLAN_SHA)))
        candidate.write(root/'SOURCE_LAUNCH.json',dict(pid=999992,condition='SOURCE',started_unix=1))
        outcome=dict(condition='SOURCE',returncode=1,complete=False,finished_unix=2,no_retry=True)
        candidate.write(root/'SOURCE_EXIT.json',outcome)
        candidate.write(root/'TERMINAL.json',dict(status='INCOMPLETE',parent_calls=0,training_rows=0,optimizer_steps=0,finished_unix=3,results=[outcome]))
        return plan

    def test_failure_terminal_does_not_require_success_or_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);plan=self.fixture(root)
            result=candidate.metadata(root,plan)
            self.assertEqual(result['status'],'INCOMPLETE')
            self.assertEqual(result['pids'],[999991,999992])

    def test_terminal_without_exit_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);plan=self.fixture(root)
            (root/'SOURCE_EXIT.json').unlink()
            with self.assertRaises(AssertionError):candidate.metadata(root,plan)

    def test_unrecorded_terminal_outcome_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);plan=self.fixture(root)
            path=root/'TERMINAL.json';document=json.loads(path.read_text());document['results']=[]
            path.write_text(json.dumps(document))
            with self.assertRaises(AssertionError):candidate.metadata(root,plan)

    def test_no_terminal_waits(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(candidate.metadata(Path(directory),Path(directory)/'PLAN.json'))

    def test_any_existing_pid_blocks_even_reused_or_zombie(self):
        with patch.object(Path,'exists',return_value=True):self.assertFalse(candidate.absent([42]))
        with patch.object(Path,'exists',return_value=False):self.assertTrue(candidate.absent([42]))

    def test_receipts_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'receipt.json';candidate.write(path,dict(first=True))
            with self.assertRaises(AssertionError):candidate.write(path,dict(first=False))
            self.assertEqual(json.loads(path.read_text()),dict(first=True))


if __name__=='__main__':unittest.main()
