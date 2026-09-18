import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import prep_common as common
import source_prepare


class PreparationTests(unittest.TestCase):
    def ledger(self,root):
        return common.Ledger(root,dict(metadata=100,adapter=50,per_life=80,discovery=20),['life'])

    def test_discovery_charged_inside_metadata_before_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()
            source=root/'source.json'
            source.write_text('{"safe":1}')
            ledger=self.ledger(root/'ledger')
            reader=common.Reader(ledger,'life','read',[source],True)
            document,reference=reader.document(source)
            self.assertEqual(document,dict(safe=1))
            self.assertEqual(ledger.totals()['metadata'],source.stat().st_size)
            self.assertEqual(ledger.totals()['discovery'],source.stat().st_size)

    def test_no_read_after_budget_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()
            source=root/'source.json'
            source.write_bytes(b'x'*81)
            reader=common.Reader(self.ledger(root/'ledger'),'life','read',[source])
            with self.assertRaisesRegex(ValueError,'per_life_read_budget'):
                reader.raw(source)
            self.assertEqual(reader.bytes,0)

    def test_failed_parse_charge_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()
            source=root/'source.json'
            source.write_text('not JSON')
            ledger=self.ledger(root/'ledger')
            with self.assertRaises(json.JSONDecodeError):
                common.Reader(ledger,'life','once',[source]).document(source)
            self.assertEqual(ledger.totals()['metadata'],8)
            with self.assertRaisesRegex(ValueError,'consumed'):
                common.Reader(ledger,'life','once',[source]).document(source)

    def test_discovery_subcap_and_aggregate(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=self.ledger(directory)
            with self.assertRaisesRegex(ValueError,'discovery_subcap'):
                ledger.reserve('large','life','metadata',21,True)
            ledger.reserve('first','life','metadata',80)
            with self.assertRaisesRegex(ValueError,'aggregate_read_budget'):
                ledger.reserve('second','_campaign','metadata',21)

    def test_unknown_life_and_adapter_discovery_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=self.ledger(directory)
            with self.assertRaisesRegex(ValueError,'declared_read_account'):
                ledger.reserve('unknown','extra','metadata',1)
            with self.assertRaisesRegex(ValueError,'included_in_metadata'):
                ledger.reserve('wrong','life','adapter',1,True)

    def test_source_symlink_and_outside_scope_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()
            source=root/'source'
            source.write_bytes(b'safe')
            link=root/'link'
            link.symlink_to(source)
            reader=common.Reader(self.ledger(root/'ledger'),'life','read',[link])
            with self.assertRaisesRegex(ValueError,'non_symlink'):
                reader.raw(link)
            with self.assertRaisesRegex(ValueError,'allowlist'):
                reader.raw(source)

    def test_original_birth_candidate_order_preserved(self):
        life=dict(proposed_storage_root='/original/life/run1',snapshot_plan_ref=dict(path='/current/PLAN.json'),
            old_birth_plan=dict(path='/historical/PLAN.json'))
        result=source_prepare.original_plan_candidates(life)
        self.assertEqual(result[0],Path('/historical/PLAN.json'))
        self.assertIn(Path('/original/life/control/PLAN.json'),result)

    def test_identity_includes_uid_and_boot(self):
        identity=dict(pid=3,start_ticks='7',boot_id='boot',uid=4)
        self.assertTrue(source_prepare.identity_same(identity,dict(identity)))
        self.assertFalse(source_prepare.identity_same(identity,dict(identity,uid=5)))
        self.assertFalse(source_prepare.identity_same(identity,dict(identity,boot_id='other')))

    def test_scope_is_exact_and_not_gpu_GO(self):
        root=Path(__file__).resolve().parent
        scope,proposal=common.scope(root/'PREPARATION_SCOPE.json',root/'PROPOSAL.json')
        self.assertFalse(scope['gpu_execution_authorized_now'])
        self.assertEqual(len(proposal['lives']),24)


if __name__=='__main__':
    unittest.main()
