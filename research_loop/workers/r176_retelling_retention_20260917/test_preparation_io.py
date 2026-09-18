import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import preparation_io as common
import c2_capture


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.ledger = common.Ledger(self.root/'ledger')
        self.clock = patch.object(common.time,'time',return_value=1789660000)
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def test_distinct_per_life_kind_limits(self):
        self.ledger.reserve('meta1','C2','metadata',common.GIB)
        with self.assertRaisesRegex(ValueError,'per_life_kind_cap'):
            self.ledger.reserve('meta2','C2','metadata',1)
        self.ledger.reserve('adapter1','C2','adapter',128*common.MIB,sleep=33,read_pass='original_capture')

    def test_adapter_pass_cannot_be_repeated_under_new_attempt_name(self):
        self.ledger.reserve('capture1','C2','adapter',12,sleep=33,read_pass='original_capture')
        with self.assertRaisesRegex(ValueError,'named_adapter_pass_already_consumed'):
            self.ledger.reserve('capture2','C2','adapter',12,sleep=33,read_pass='original_capture')

    def test_no_out_of_scope_checkpoint(self):
        for life,sleep in [('C2',32),('C5',35),('C3',33)]:
            with self.assertRaises(ValueError):
                self.ledger.reserve('wrong','C2' if life=='C3' else life,'adapter',129*common.MIB,
                    sleep=sleep,read_pass='original_capture')

    def test_discovery_included_not_additional(self):
        self.ledger.reserve('discovery','_campaign','metadata',32*common.MIB,discovery=True)
        with self.assertRaisesRegex(ValueError,'discovery_included_subcap'):
            self.ledger.reserve('extra','C2','metadata',1,discovery=True)

    def test_failed_exact_read_keeps_advance_charge(self):
        source = self.root/'source.json'
        source.write_bytes(b'{}')
        allowance = self.ledger.reserve('read','C2','metadata',100)
        reader = common.Reader(self.root/'reads1',{'metadata':allowance},[source])
        with self.assertRaisesRegex(ValueError,'exact_source_bytes'):
            reader.document(source,'0'*64)
        rows = list((self.root/'reads1/reads').glob('*.json'))
        self.assertEqual(len(rows),1)
        self.assertEqual(json.loads(rows[0].read_bytes())['bytes'],2)

    def test_refusal_before_content_when_over_allowance(self):
        source = self.root/'source.json'
        source.write_bytes(b'{}')
        allowance = self.ledger.reserve('read','C2','metadata',1)
        reader = common.Reader(self.root/'reads1',{'metadata':allowance},[source])
        with self.assertRaisesRegex(ValueError,'delegated_read_cap'):
            reader.raw(source)
        self.assertEqual(reader.actual['metadata'],0)

    def test_symlink_refused(self):
        source = self.root/'source.json'
        source.write_bytes(b'{}')
        alias = self.root/'alias.json'
        alias.symlink_to(source)
        reader = common.Reader(self.root/'reads1',{},[alias])
        with self.assertRaisesRegex(ValueError,'exact_source_allowlist'):
            reader.raw(alias)

    def test_scope_pins_are_still_exact(self):
        self.assertEqual(len(common.validate_controls(Path(__file__).parent)),4)

    def test_prior_exact_custody_plan_need_not_share_storage_generation_prefix(self):
        path = '/localhome/local-rohing/orch_r157_community_C2_20260917_attempt1/control/PLAN.json'
        custody = dict(registry_birth_plan=dict(path=path,sha256='a'*64))
        self.assertEqual(c2_capture.custody_plan_path(custody),Path(path))

    def test_custody_original_plan_reference_must_be_confined(self):
        for path in ('/etc/PLAN.json','../../PLAN.json','/localhome/local-rohing/../PLAN.json',
                '/localhome/local-rohing/PLAN.other'):
            with self.assertRaisesRegex(ValueError,'custody_bound_original_plan_reference'):
                c2_capture.custody_plan_path(dict(registry_birth_plan=dict(path=path,sha256='a'*64)))

    def test_distinct_explicit_pre_model_repair_retains_failed_charge(self):
        self.ledger.reserve('capture1','C2','adapter',128*common.MIB,sleep=33,read_pass='original_capture')
        failed = common.write(self.root/'failed.json',dict(status='FAILED_CAPTURE_PRESERVED_NO_RETRY',
            actual_bytes=dict(adapter=0),model_calls=0,provider_calls=0))
        repair = common.write(self.root/'repair.json',dict(failed_receipt=failed,scope_sha256=common.SCOPE_SHA,
            new_operation='repair1',failed_operation='capture1'))
        self.ledger.reserve('repair1','C2','adapter',128*common.MIB,sleep=33,read_pass='original_capture',
            repair_authority=repair)
        rows = [json.loads(path.read_bytes()) for path in (self.root/'ledger/reservations').glob('*.json')]
        self.assertEqual(sum(row['bytes'] for row in rows),256*common.MIB)
        with self.assertRaises(ValueError):
            self.ledger.reserve('repair2','C2','adapter',128*common.MIB,sleep=33,read_pass='original_capture',
                repair_authority=repair)


if __name__=='__main__':
    unittest.main()
