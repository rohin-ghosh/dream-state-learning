import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class Astra7LaunchTests(unittest.TestCase):
    def test_only_one_supervisor_and_no_parent_process(self):
        path=Path(__file__).with_name('prepare.py')
        spec=importlib.util.spec_from_file_location('astra7_prepare',path)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'source').mkdir()
            (root/'READY.json').write_text(json.dumps(dict(status='CPU_PASS_NOT_LAUNCHED')))
            with patch.object(module.subprocess,'Popen',return_value=SimpleNamespace(pid=12345)) as spawn:
                module.launch(SimpleNamespace(root=root))
            self.assertEqual(spawn.call_count,1)
            self.assertIn('gpu.r229_astra7_runtime',spawn.call_args.args[0])
            receipt=json.loads((root/'DISPATCHED.json').read_bytes())
            self.assertEqual(receipt['processes'],dict(supervisor=12345))
            self.assertFalse((root/'parent.log').exists())


if __name__=='__main__':
    unittest.main()
