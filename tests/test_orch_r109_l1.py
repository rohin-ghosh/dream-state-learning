import hashlib
from pathlib import Path
import tempfile
import unittest

from organism_v6 import orch_r109_l1_policy as policy
from gpu.orch_r109_l1_ops import source_binding


class R109ContractTests(unittest.TestCase):
    def test_owned_allocation(self):
        for node in ('node1','node2'):
            for index in range(7):
                with self.subTest(node=node,index=index):
                    self.assertTrue(0<=policy.allocation(node,index)<14)

    def test_generation7_never_allowed(self):
        for node in ('node1','node2'):
            for index in (-1,7,8,True):
                with self.subTest(node=node,index=index),self.assertRaises(ValueError):
                    policy.allocation(node,index)

    def test_fixed_clock_no_restart(self):
        first=policy.lifetime(policy.START+10,policy.END+21600)
        later=policy.lifetime(policy.START+7200,policy.END+21600)
        self.assertEqual(first,later)
        self.assertEqual(first['hard_deadline_unix']-first['started_unix'],28800)
        with self.assertRaises(ValueError):
            policy.lifetime(policy.CUTOFF,policy.END+21600)

    def test_lease_margin(self):
        with self.assertRaises(ValueError):
            policy.lifetime(policy.START+1,policy.END+21599)

    def test_global_training_cursor_not_reset(self):
        rows=policy.batch_positions(8933,3635,42)
        self.assertEqual(rows[0],('legacy',8932%210))
        self.assertEqual(rows[2],('anchor',8932%42))
        with self.assertRaises(ValueError):
            policy.batch_positions(1,3635,42)

    def test_node1_manifest_source_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source=root/'SOURCE_SHA256.json'
            source.write_text('{}')
            self.assertEqual(source_binding(root),dict(path=str(source),sha256=hashlib.sha256(b'{}').hexdigest()))

    def test_functional_prompts_not_count_gates(self):
        self.assertEqual(set(policy.GUIDANCE),set(policy.CONDITIONS))
        self.assertIn('announcements',policy.GUIDANCE['FUNCTIONAL_METACOGNITION'])
        self.assertIn('Never change the problem',policy.GUIDANCE['PERCEPTION'])

    def test_fail_closed_ingestion(self):
        row=dict(source_label=policy.LABELS[3],split='TRAIN',task_id='train1',contamination_family='train_world',
            functional_verdict='PASS',grounding_verdict='PASS',source_archive_sha256='a',source_call_sha256='b',
            annotation_sha256='c',target_actor='CHILD',parent_text_masked=True,target='child',
            target_sha256=hashlib.sha256(b'child').hexdigest(),native_token_ids=[1],student_prefix=[],prefix_sha256=policy.digest([]))
        changes=[dict(split='HELD'),dict(target_actor='PARENT'),dict(parent_text_masked=False),
            dict(functional_verdict='UNKNOWN'),dict(grounding_verdict='FAIL'),dict(source_archive_sha256=''),dict(target='rewritten')]
        for change in changes:
            with self.subTest(change=change),self.assertRaises(ValueError):
                policy.validate_eligible(dict(row,**change),set(),set())
        with self.assertRaises(ValueError):
            policy.validate_eligible(row,set(),{'train_world'})


if __name__=='__main__':
    unittest.main()
