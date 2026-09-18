import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import preparation_io as common


HERE = Path(__file__).resolve().parent
component = HERE/'reviewed_prep_common.py'
if not component.exists():
    component = HERE.parent/'r172_forward_probes_20260917/prep_common.py'
spec = importlib.util.spec_from_file_location('reviewed_prep_common',component)
reviewed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reviewed)
sys.modules['reviewed_prep_common'] = reviewed
import r176_transfer as transfer


class TransferTests(unittest.TestCase):
    def test_stage_and_export_receipts_have_distinct_paths(self):
        import inspect
        source = inspect.getsource(transfer.export)
        self.assertIn("operation/'EXPORT_PUBLIC_METADATA.json'",source)
        self.assertNotIn("operation/'PUBLIC_METADATA.json'",source)

    def test_reviewed_source_unchanged(self):
        self.assertEqual(common.sha(component.read_bytes()),transfer.REVIEWED_SHA)

    def test_exact_stream_charges_before_short_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            reader = common.Reader(Path(temporary),{'metadata':dict(document=dict(bytes=100),reference={})},[])
            stream = reviewed.ChargedStream(io.BytesIO(b'ab'),transfer.AllowanceLedger(reader),'C2','wire')
            with self.assertRaisesRegex(ValueError,'truncated_or_invalid_transfer_read'):
                stream.exact(3)
            self.assertEqual(reader.charged['metadata'],3)

    def test_disk_cap_is_stricter_than_reviewed_component(self):
        self.assertEqual(transfer.DiskLedger.CAPS,dict(receiving=2*common.GIB))
        self.assertEqual(reviewed.DiskLedger.CAPS['receiving'],16*common.GIB)

    def test_fixed_complete_hash_refuses_substitution(self):
        with self.assertRaisesRegex(ValueError,'source_complete_exact_bytes'):
            transfer.validate_complete(b'{}')

    def test_complete_header_requires_all_private_custody_members(self):
        document = dict(status='FIXED_C2_SLEEP33_SOURCE_CAPTURE_VERIFIED',scope_sha256=common.SCOPE_SHA,
            proposal_sha256=common.PINS['PROPOSAL.json'],slots_sha256=common.PINS['SLOTS.json'],
            life_id='C2',sleep=33,model_calls=0,provider_calls=0,files={})
        raw = common.canonical(document)
        with patch.object(transfer,'FIXED_COMPLETE_SHA',common.sha(raw)):
            with self.assertRaisesRegex(ValueError,'complete_private_source_closure'):
                transfer.validate_complete(raw)

    def test_global_allowance_integrity_and_pass_identity(self):
        authorities = {}
        for kind in ('metadata','adapter'):
            document = dict(status='PRECHARGED_NO_REFUND',scope_sha256=common.SCOPE_SHA,
                life_id='C2',kind=kind,read_pass='source_export',sleep=33)
            authorities[kind] = dict(document=document,reference=dict(sha256=common.digest(document)))
        transfer.verify_authorities(authorities,'source_export')
        with self.assertRaisesRegex(ValueError,'distinct_named_transfer_pass'):
            transfer.verify_authorities(authorities,'receiver_stream')
        authorities['adapter']['document']['sleep'] = 34
        with self.assertRaisesRegex(ValueError,'explicit_global_precharge'):
            transfer.verify_authorities(authorities,'source_export')


if __name__=='__main__':
    unittest.main()
