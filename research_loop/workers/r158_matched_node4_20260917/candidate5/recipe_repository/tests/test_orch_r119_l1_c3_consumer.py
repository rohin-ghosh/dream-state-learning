import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r119_l1_c3_consumer as candidate
from gpu import orch_r109_l1_experience as experience


class BoundaryTests(unittest.TestCase):
    def test_common_future_boundary_not_arm_local_segment(self):
        for update in range(15460,18533,128):
            self.assertEqual(candidate.cohort_for(update,18020),'C3' if update>=18020 else 'C2')
        for invalid in (18021,0,15461):
            with self.assertRaises(AssertionError):candidate.cohort_for(invalid,18020)
        with self.assertRaises(AssertionError):candidate.cohort_for(18020,18021)

    def test_original_schedule_and_control_mask_unchanged(self):
        for update in range(18021,18149):
            positions=experience.positions(update,9444,7,22)
            self.assertEqual(len(positions),4)
            self.assertEqual(positions[-1][0]=='eligible',(update-9444-1)%8==0)
        self.assertEqual(experience.labels_for('CONTROL','eligible',[1,2]),[-100,-100])
        self.assertEqual(experience.labels_for('FULL','eligible',[1,2]),[1,2])

    def test_real_CPU_exit_zero_only_not_failed_or_running(self):
        for code in (0,7):
            child=subprocess.Popen([sys.executable,'-c','raise SystemExit(%d)'%code])
            try:
                for unused in range(200):
                    text=Path('/proc',str(child.pid),'stat').read_text()
                    if text.rsplit(')',1)[1].split()[0]=='Z':break
                    time.sleep(.01)
                if code==0:self.assertTrue(candidate.completed_exit(text))
                else:
                    with self.assertRaises(AssertionError):candidate.completed_exit(text)
            finally:child.wait()
        self.assertFalse(candidate.completed_exit(Path('/proc/self/stat').read_text()))

    def test_no_false_readout_complete(self):
        document=dict(status='COMPLETE',condition='ON',capability_calls=32,base_and_adapter_unchanged=True,
                      checkpoint_state_sha256='state',parent_access=False,training_ingestion=False)
        def read(path):
            return dict(document,condition=path.parent.name)
        trainer=SimpleNamespace(read=read,sha=lambda path:'hash',storage=SimpleNamespace(
            verify_checkpoint=lambda path:dict(metadata=dict(adapter=dict(state_sha256='state')))))
        proofs=candidate.readout_proof(trainer,Path('/owned'),'FULL',1,Path('/checkpoint'))
        self.assertEqual(set(proofs),{'ON','OFF'})
        for change in (dict(status='FAILED'),dict(capability_calls=31),dict(training_ingestion=True),
                       dict(parent_access=True),dict(checkpoint_state_sha256='other')):
            saved=dict(document)
            document.update(change)
            with self.assertRaises(AssertionError):candidate.readout_proof(trainer,Path('/owned'),'FULL',1,Path('/checkpoint'))
            document.clear();document.update(saved)

    def test_same_original_training_readout_bytecode_bound_per_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            sha=lambda path:'hash'
            def write(path,document):path.write_text(json.dumps(document))
            trainer=SimpleNamespace(read=lambda path:json.loads(path.read_text()),sha=sha,write=write,
                storage=SimpleNamespace(verify_checkpoint=lambda path:dict(metadata=dict(update=18020))))
            frozen=SimpleNamespace(trainer=trainer,experience=experience)
            config=dict(slots={'FULL':0,'CONTROL':1},activation_update=18020,
                cohorts={'C3':dict(path=str(root/'cohort'))},held_path=str(root/'held'),
                uuid_by_index=['zero','one'],model_dir='/base',lease_end_unix=9999999999,hard_deadline_unix=9999978399)
            plan=dict(lifetime=dict(started_unix=1))
            with patch.object(candidate,'configuration',return_value=(frozen,config)),patch.object(
                    candidate,'verify_cohort',return_value=(root/'cohort',plan,{})):
                result=candidate.stage_namespace(root,'FULL',9,root/'checkpoint',True)
                context=result[-1]
                self.assertIs(context['train'].__code__,experience.train.__code__)
                self.assertIs(context['readout'].__code__,experience.readout.__code__)
                self.assertEqual(result[-2]['cohort'],'C3')
                self.assertEqual(result[-2]['start_update'],18020)
                self.assertEqual(result[-2]['end_update'],18148)


if __name__=='__main__':unittest.main()
