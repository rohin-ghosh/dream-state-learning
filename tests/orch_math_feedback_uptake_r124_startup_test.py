from contextlib import ExitStack
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from gpu import orch_math_feedback_uptake_r124_runtime as runtime


class StartupPathTests(unittest.TestCase):
    def fixture(self, directory):
        base=Path(directory)
        root=base/'A2';root.mkdir()
        source=base/'source/gpu';source.mkdir(parents=True)
        script=source/'runtime.py';script.write_text('cpu fixture')
        write=runtime.run.write
        write(source.parent/'CPU_TESTS.json',dict(passed=True,source_files={'gpu/runtime.py':runtime.run.sha(script)}))
        write(root/'COUNTERS.json',{'native':200})
        write(root/'PLAN.json',{})
        write(root/'LAUNCH.json',dict(identity={'pid':100}))
        write(root/'admission_attempt2/GUARD_STARTED.json',dict(identity={'pid':101}))
        write(root/'GUARD_TERMINAL.json',dict(returncode=1))
        write(root/'MOUNTED_BEFORE.json',dict(historical=True))
        for role in ('before','after'):
            output=root/'paired_DEV'/role;output.mkdir(parents=True)
            write(output/'PROCESS_RESULT.json',dict(status='FAILED_NO_RETRY',returncode=1))
            (output/'process.log').write_text("ModuleNotFoundError: No module named 'tokenizers'\n")
            write(output/'BINDING.json',{});write(output/'LAUNCH.json',{})
        return base,root,script

    def test_full_guard_reaches_only_injected_model_boundary(self):
        for clear in (True,False):
            with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                base,root,script=self.fixture(directory)
                plan=dict(uuid='GPU-test',bounds={'hard_end_unix':10**12},contract={'inherited_counters':{'native':200}})
                stack.enter_context(patch.object(runtime.run,'ROOT',base))
                stack.enter_context(patch.object(runtime,'SERVICE',root/'new_service'))
                stack.enter_context(patch.object(runtime,'__file__',str(script)))
                stack.enter_context(patch.object(runtime.run,'configure'))
                stack.enter_context(patch.object(runtime.run,'validate',return_value=plan))
                stack.enter_context(patch.object(runtime,'preflight',return_value={'cpu_only':True}))
                stack.enter_context(patch.object(runtime,'require_absent'))
                scan=Mock(returncode=0,stdout=json.dumps(dict(clear=clear,scanner_euid=0,gpu={'uuid':'GPU-test'})),stderr='')
                scanner=stack.enter_context(patch.object(runtime.subprocess,'run',return_value=scan))
                actor=Mock(pid=os.getpid(),returncode=0)
                boundary=stack.enter_context(patch.object(runtime.subprocess,'Popen',return_value=actor))
                if clear:
                    runtime.guard()
                    self.assertEqual(boundary.call_count,1)
                    self.assertEqual(boundary.call_args.args[0],[runtime.PYTHON,'-B',str(script),'resident'])
                    self.assertEqual(boundary.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'],'GPU-test')
                    self.assertTrue((root/'new_service/LAUNCH.json').exists())
                else:
                    with self.assertRaises(ValueError):runtime.guard()
                    boundary.assert_not_called()
                self.assertIn(runtime.PYTHON,scanner.call_args.args[0])
                self.assertEqual(runtime.run.read(root/'COUNTERS.json'),{'native':200})
                self.assertEqual(runtime.run.read(root/'MOUNTED_BEFORE.json'),{'historical':True})

    def test_full_resident_prefix_reaches_new_cycle_without_old_receipt_collision(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            base,root,script=self.fixture(directory)
            service=root/'new_service';service.mkdir()
            plan=dict(branch='A2',original_root=str(root),bounds={'train_end_unix':10**12},anchors='anchors',
                contract={'next_cycle':12,'initial_checkpoint':{},'inherited_counters':{'native':200}},
                initial_history='history',initial_carry='carry',train='train')
            stack.enter_context(patch.object(runtime.run,'ROOT',base))
            stack.enter_context(patch.object(runtime,'SERVICE',service))
            stack.enter_context(patch.object(runtime,'preflight',return_value={}))
            stack.enter_context(patch.object(runtime.run,'configure'))
            stack.enter_context(patch.object(runtime.run,'validate',return_value=plan))
            stack.enter_context(patch.object(runtime.run.math,'mounted',return_value={'fresh':True}))
            stack.enter_context(patch.object(runtime.run,'restore',return_value=Mock(tokenizer=object())))
            stack.enter_context(patch.object(runtime.run.old.inventory,'build_inventory',return_value=({'family':[]},{})))
            stack.enter_context(patch.object(runtime.run.control,'checked',side_effect=lambda key: [[],[],[],[],[],[],[],[],[],[],[],[]] if key=='train' else []))
            collect=stack.enter_context(patch.object(runtime.run.old,'collect',side_effect=RuntimeError('INJECTED_FIRST_NEW_CYCLE_BOUNDARY')))
            with self.assertRaisesRegex(RuntimeError,'INJECTED_FIRST_NEW_CYCLE_BOUNDARY'):
                runtime.resident()
            self.assertEqual(collect.call_args.args[3],12)
            self.assertTrue((root/'LOADED.json').exists())
            self.assertEqual(runtime.run.read(root/'MOUNTED_BEFORE.json'),{'historical':True})
            self.assertEqual(runtime.run.read(service/'MOUNTED_BEFORE.json'),{'fresh':True})
            self.assertTrue((service/'PROBES_NOT_RETRIED.json').exists())
