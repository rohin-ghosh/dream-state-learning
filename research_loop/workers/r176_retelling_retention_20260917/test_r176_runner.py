import json
from pathlib import Path
import tempfile
import unittest

import preparation_io as common
import r176_runner as runner


class RunnerTests(unittest.TestCase):
    def config(self,condition='LORA_ON'):
        return dict(life_id='C2',sleep=33,condition=condition,physical=0,capture={'sha256':'capture'},
            source={'sha256':'source'},execution={'sha256':condition})

    def test_no_GO_refuses_before_config_or_admission(self):
        with self.assertRaisesRegex(ValueError,'separate_Main_execution_GO_required'):
            runner.enter('/not/a/config',None)

    def test_preparation_authority_is_not_execution_GO(self):
        with tempfile.TemporaryDirectory() as temporary:
            scope = Path(temporary)/'scope.json'
            scope.write_text(json.dumps(dict(status='AUTHORIZED_PREPARATION_ONLY_WITH_NEW_PRE_IO_LEDGER')))
            with self.assertRaisesRegex(ValueError,'preparation_is_not_execution_GO'):
                runner.enter('/not/a/config',scope)

    def test_pair_is_once_only_and_identical_checkpoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            now = common.END-10000
            runner.reserve(root,self.config(),{},now,common.END+21600)
            with self.assertRaisesRegex(ValueError,'finite_fixed_once_only_calls'):
                runner.reserve(root,self.config(),{},now,common.END+21600)
            changed = dict(self.config('LORA_OFF'),capture={'sha256':'different'})
            with self.assertRaisesRegex(ValueError,'same_capture_source_for_both_conditions'):
                runner.reserve(root,changed,{},now,common.END+21600)
            runner.reserve(root,self.config('LORA_OFF'),{},now,common.END+21600)
            rows = [json.loads(path.read_bytes()) for path in (root/'ledger').glob('*.RESERVED.json')]
            self.assertEqual(sum(row['calls_charged'] for row in rows),6)

    def test_wall_is_fixed_from_first_admission(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            start = common.END-10000
            runner.reserve(root,self.config(),{},start,common.END+21600)
            with self.assertRaisesRegex(ValueError,'full_job_inside_original_non_sliding_wall'):
                runner.reserve(root,self.config('LORA_OFF'),{},start+5400-915,common.END+21600)
            self.assertEqual(json.loads((root/'FIRST_ADMISSION.json').read_bytes())['first_admission_unix'],start)

    def test_no_initial_or_other_checkpoint_or_life(self):
        for values in (dict(sleep=0),dict(sleep=34),dict(life_id='C5'),dict(condition='OTHER')):
            with self.assertRaisesRegex(ValueError,'narrow_fixed_C2_sleep33_only'):
                runner.key(dict(self.config(),**values))

    def test_model_load_uses_separate_pass_and_preserves_repeated_open_charges(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            adapter = root/'adapter.safetensors'
            adapter.write_bytes(b'1234')
            allowance = dict(document=dict(bytes=8),reference={})
            account = runner.ModelLoadAccounting(root/'reads',allowance,[adapter])
            self.assertEqual(account.reader.charged['adapter'],4)
            account.observe_open(adapter)
            self.assertEqual(account.reader.charged['adapter'],4)
            account.observe_open(adapter)
            self.assertEqual(account.reader.charged['adapter'],8)
            with self.assertRaisesRegex(ValueError,'delegated_read_cap'):
                account.observe_open(adapter)

    def test_model_load_precharge_refuses_before_load_if_too_small(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            adapter = root/'adapter.safetensors'
            adapter.write_bytes(b'1234')
            with self.assertRaisesRegex(ValueError,'delegated_read_cap'):
                runner.ModelLoadAccounting(root/'reads',dict(document=dict(bytes=3),reference={}),[adapter])


if __name__=='__main__':
    unittest.main()
