from pathlib import Path
import unittest
from unittest.mock import patch

from gpu import orch_r167_object_probe_queue as queue
from tests.test_orch_r167_object_probe_queue import QueueTests

import capture_worker
import prep_common as common
import transfer
from test_transfer_accounting import TransferFixture


class CaptureTests(unittest.TestCase):
    def fixture(self):
        fixture=QueueTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.ready()
        return fixture

    def test_new_capture_uses_existing_frozen_boundary_checks(self):
        fixture=self.fixture()
        capture_worker.capture_once(queue,fixture.plan_path,1)
        captured=Path(fixture.plan['queue_root'])/'captures/000001'
        self.assertEqual((captured/'adapter/adapter_model.safetensors').read_bytes(),b'adapter')
        receipt=common.read(captured/'COMPLETE.json')
        self.assertFalse(receipt['adapter_write_hash_reread'])
        self.assertEqual(queue.read_totals(Path(fixture.plan['queue_root']))['adapter'],len(b'adapter{}'))

    def test_original_birth_required_and_no_capture_retry(self):
        fixture=self.fixture()
        capture_worker.capture_once(queue,fixture.plan_path,1)
        with self.assertRaises(FileExistsError):
            capture_worker.capture_once(queue,fixture.plan_path,1)

    def test_no_adapter_reread_for_write_receipt(self):
        fixture=self.fixture()
        original=queue.protocol.ref
        def guarded(path):
            if '/captures/' in str(path) and '/adapter/' in str(path):
                raise AssertionError('unbudgeted adapter reread')
            return original(path)
        with patch.object(queue.protocol,'ref',side_effect=guarded):
            capture_worker.capture_once(queue,fixture.plan_path,1)


class TransferTests(TransferFixture):
    def test_forward_copy_does_not_require_initial_copy(self):
        result=self.receive()
        self.assertEqual(result['sleep'],3)
        self.assertFalse((self.receiving/'lives/life/captures/000000').exists())
        self.assertEqual(result['model_calls'],0)

    def test_next_capture_may_repeat_identical_custody_without_overwrite(self):
        self.receive()
        original=(self.receiving/'lives/life/REGISTERED.json').stat().st_mtime_ns
        self.capture(4)
        self.receive(sleep=4)
        self.assertEqual((self.receiving/'lives/life/REGISTERED.json').stat().st_mtime_ns,original)

    def test_unknown_life_and_unsafe_member_rejected(self):
        with self.assertRaisesRegex(ValueError,'exact_requested_transfer'):
            self.receive(self.archive(header_change=lambda header: header.update(life_id='other')))
        with self.assertRaisesRegex(ValueError,'relative_transfer'):
            transfer.member_path('../parent/inbox.json','life',3)
        with self.assertRaisesRegex(ValueError,'adapter_only'):
            transfer.member_path('lives/life/captures/000003/adapter/optimizer_rng.pt','life',3)

    def test_consumed_transfer_not_retried(self):
        self.receive()
        with self.assertRaises(FileExistsError):
            self.receive()


if __name__=='__main__':
    unittest.main()
