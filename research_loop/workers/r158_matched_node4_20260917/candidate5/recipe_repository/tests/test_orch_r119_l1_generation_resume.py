import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r119_l1_generation_resume as runtime


class CheckpointViewTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.checkpoint = self.root / 'original_checkpoint'
        self.checkpoint.mkdir()
        names = ['optimizer.pt', 'rank0.pt', 'rank1.pt',
                 'adapter/adapter_config.json', 'adapter/adapter_model.safetensors']
        for name in names:
            path = self.checkpoint / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(('CPU_FIXTURE_' + name).encode())
        manifest = dict(schema='COMBINED_CONTINUAL_CHECKPOINT_V1',
                        metadata=dict(update=15460, adapter=dict(state_sha256='fixture_state')),
                        files={name: runtime.trainer.sha(self.checkpoint / name) for name in names})
        (self.checkpoint / 'COMMIT.json').write_text(json.dumps(manifest))
        self.view = self.root / 'view'
        (self.view / 'input').mkdir(parents=True)
        (self.view / 'TASKS.json').write_text('{}')
        self.document = dict(wrapper_sha256=runtime.trainer.sha(runtime.__file__),
                             generator_sha256=runtime.trainer.sha(runtime.generation.__file__),
                             policy_sha256=runtime.trainer.sha(runtime.generation.policy.__file__),
                             lease_end_unix=100000, hard_deadline_unix=78400,
                             node='ovx', lanes=list(range(8)), checkpoint=str(self.checkpoint),
                             checkpoint_commit_sha256=runtime.trainer.sha(self.checkpoint / 'COMMIT.json'),
                             checkpoint_state_sha256='fixture_state', origin_view=str(self.view),
                             tasks_sha256=runtime.trainer.sha(self.view / 'TASKS.json'))

    def check(self):
        (self.root / 'FORKS.json').write_text(json.dumps(self.document))
        with patch.object(runtime.time, 'time', return_value=1000):
            return runtime.config(self.root)

    def copy_view(self):
        shutil.copytree(self.checkpoint, self.view / 'input' / 'checkpoint')

    def test_real_physical_bundle_verifies_with_unchanged_verifier(self):
        self.copy_view()
        self.assertEqual(self.check(), self.document)

    def test_checkpoint_symlink_rejected_before_model_launch(self):
        (self.view / 'input' / 'checkpoint').symlink_to(self.checkpoint)
        with self.assertRaisesRegex(AssertionError, 'checkpoint_view_must_be_physical'):
            self.check()

    def test_corrupt_physical_copy_is_not_accepted_by_commit_only(self):
        self.copy_view()
        (self.view / 'input' / 'checkpoint' / 'optimizer.pt').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'checkpoint_hash_drift'):
            self.check()

    def test_wrong_seed_rejected(self):
        self.copy_view()
        self.document['checkpoint_state_sha256'] = 'wrong_state'
        with self.assertRaises(AssertionError):
            self.check()

    def test_lane_expansion_and_clock_extension_rejected(self):
        self.copy_view()
        self.document['node'] = 'a100'
        with self.assertRaises(AssertionError):
            self.check()
        self.document['node'] = 'ovx'
        self.document['hard_deadline_unix'] += 1
        with self.assertRaises(AssertionError):
            self.check()


if __name__ == '__main__':
    unittest.main()
