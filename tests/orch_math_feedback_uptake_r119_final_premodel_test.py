from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_r119_final_premodel as repair


class PremodelTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_any_model_or_input_artifact_forbids_recovery(self):
        for name in ('LEDGER.json','BEFORE.json','AFTER.json','MOUNTED_FINAL.json','COMPLETE.json','CALL_0001.request.json','CALL_0001.raw.json'):
            folder = self.root/name.replace('.','_')
            folder.mkdir()
            (folder/name).write_text('{}')
            with self.subTest(name=name), self.assertRaises(ValueError):
                repair.no_model_evidence(folder,'F2')

    def test_nonzero_charged_calls_forbid_recovery(self):
        repair.write(self.root/'TERMINAL.json',dict(charged_native=8,completed_native=0,unattempted_native=0))
        with self.assertRaisesRegex(ValueError,'zero_model_input'):
            repair.no_model_evidence(self.root,'F2')

    def test_existing_claim_is_never_overwritten(self):
        old = self.root/'claim.json'
        repair.write(old,dict(original=True))
        before = old.read_bytes()
        (self.root/'evaluation').mkdir()
        repair.write(self.root/'evaluation/PLAN.json',dict(plan=True))
        plan = dict(quota_claim=str(old),original_claim=repair.ref(old),quota_id='same',
            root=str(self.root/'evaluation'),continuation_claim=str(self.root/'continuation.json'),
            premodel_previous=dict(path='old'),premodel_proof=dict(real=True))
        with patch.object(repair,'attempts',return_value=[]):
            repair.claim(plan)
            with self.assertRaises(FileExistsError):
                repair.claim(plan)
        self.assertEqual(old.read_bytes(),before)
        self.assertEqual(repair.read(self.root/'continuation.json')['original_claim'],plan['original_claim'])

    def test_changed_original_claim_rejected(self):
        path=self.root/'claim.json'
        repair.write(path,dict(owner='foreign'))
        plan=dict(quota_claim=str(path),original_claim=dict(path=str(path),sha256='wrong'),continuation_claim=str(self.root/'next.json'))
        with patch.object(repair,'attempts',return_value=[]), self.assertRaisesRegex(ValueError,'no_reset'):
            repair.claim(plan)

    def test_previous_model_attempt_is_not_filtered(self):
        with patch.object(repair,'attempts',return_value=['old/LEDGER.json']):
            with self.assertRaisesRegex(ValueError,'old_model_attempt'):
                repair.claim({})

    def test_original_native_and_capture_exact_code(self):
        values=repair.functions()
        self.assertIs(values['native'].__code__,repair.original.native.__code__)
        self.assertIs(values['capture'].__code__,repair.original.capture.__code__)
        self.assertIs(values['native'].__globals__['release'],repair.release)

    def test_exact_guard_bytes_match_published_originals(self):
        root=Path(__file__).resolve().parents[1]
        for name,digest in repair.GUARDS.items():
            self.assertEqual(repair.original.sha(root/name),digest)


if __name__ == '__main__':
    unittest.main()
