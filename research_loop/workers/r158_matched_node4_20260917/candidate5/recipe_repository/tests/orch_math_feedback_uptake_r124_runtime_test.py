import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_r124_runtime as repair


class RuntimeTests(unittest.TestCase):
    def test_old_mounted_receipt_preserved_new_era_written(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);service=root/'service';service.mkdir()
            (root/'MOUNTED_BEFORE.json').write_text('{"old":true}')
            with patch.object(repair,'SERVICE',service):
                repair.successor_write(root,root/'MOUNTED_BEFORE.json',{'new':True})
                repair.successor_write(root,root/'LOADED.json',{'loaded':True})
            self.assertEqual(json.loads((root/'MOUNTED_BEFORE.json').read_text()),{'old':True})
            self.assertEqual(json.loads((service/'MOUNTED_BEFORE.json').read_text()),{'new':True})
            self.assertTrue((root/'LOADED.json').exists())

    def setup_root(self,root):
        (root/'COUNTERS.json').write_text('{"native":200}')
        for role in ('before','after'):
            output=root/'paired_DEV'/role
            output.mkdir(parents=True)
            (output/'PROCESS_RESULT.json').write_text(json.dumps(dict(status='FAILED_NO_RETRY',returncode=1)))
            (output/'process.log').write_text("ModuleNotFoundError: No module named 'tokenizers'\n")
            for name in ('LAUNCH.json','BINDING.json'):
                (output/name).write_text('{}')

    def test_exact_premodel_failure_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.setup_root(root)
            result=repair.failed_before_input(root,{'contract':{'inherited_counters':{'native':200}}})
            self.assertEqual(set(result),{'before','after'})

    def test_no_loaded_model_input_or_charge(self):
        for name in ('paired_DEV/before/LOADED.json','paired_DEV/after/BATCH.request.json','reservations/0001.json','LOADED.json'):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);self.setup_root(root)
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.touch()
                with self.assertRaises(ValueError):
                    repair.failed_before_input(root,{'contract':{'inherited_counters':{'native':200}}})

    def test_live_actor_rejected(self):
        with patch.object(repair.os,'pidfd_open',return_value=7),patch.object(repair.os,'close'),self.assertRaises(ValueError):
            repair.require_absent({'pid':42})

    def test_wrong_interpreter_rejected_before_import(self):
        with patch.object(repair.sys,'executable','/usr/bin/python3'),patch.object(repair.importlib,'import_module') as load,self.assertRaises(ValueError):
            repair.preflight()
        load.assert_not_called()
