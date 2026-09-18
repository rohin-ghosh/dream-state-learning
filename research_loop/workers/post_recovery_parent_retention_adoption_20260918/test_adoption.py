"""CPU-only adoption refusals and exact source preservation regressions."""

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import adoption


class AdoptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provenance = adoption.verify_phase2()
        cls.captured = adoption.read(adoption.PHASE2 / 'private/capture.json')
        cls.observation = adoption.read(adoption.OWN / 'SOURCE_OBSERVATION.json')
        cls.outputs = adoption.candidate_bytes(cls.provenance)

    def validate(self, observation):
        adoption.validate_observation(observation, self.provenance, self.captured)

    def test_exact_running_pair_baselines(self):
        self.validate(self.observation)

    def test_three_exact_postimages(self):
        self.assertEqual(set(self.outputs), set(adoption.CHANGED))
        for label in ('learner', 'frozen'):
            for relative, content in self.outputs.items():
                self.assertEqual(adoption.sha(content),
                    self.provenance['sources'][label]['files'][relative]['proposed_fork_sha256'])

    def test_every_other_guard_pin_preserved(self):
        receipt = adoption.build_receipt(self.observation, self.provenance, self.outputs)
        for label in ('learner', 'frozen'):
            original = self.observation['targets'][label]['source_pins']
            proposed = receipt['proposed_source_pins'][label]
            self.assertEqual(set(original), set(proposed))
            self.assertEqual({key for key in original if original[key] != proposed[key]}, set(adoption.CHANGED))
            self.assertEqual(receipt['preserved_files_per_target'][label], 204)

    def test_no_deployment_or_checkpoint_claim(self):
        receipt = adoption.build_receipt(self.observation, self.provenance, self.outputs)
        for key in ('deployable', 'checkpoint_state_verified', 'boundary_reserved'):
            self.assertFalse(receipt[key])
        for key in ('native_signals', 'remote_writes', 'GPU_jobs'):
            self.assertEqual(receipt[key], 0)

    def test_each_protected_source_drift_refused(self):
        protected = ('gpu/r232_recovery.py', 'gpu/r232_runtime.py', 'gpu/r205_runtime.py',
            'gpu/orch_r125_stream_journal.py', 'organism_v6/orch_r227_learning_policy.py', *adoption.CHANGED)
        for label in ('learner', 'frozen'):
            for relative in protected:
                with self.subTest(label=label, path=relative):
                    observation = deepcopy(self.observation)
                    observation['targets'][label]['disk_hashes'][relative] = '0' * 64
                    with self.assertRaisesRegex(ValueError, 'disk_guard_mismatch'):
                        self.validate(observation)

    def test_repinning_a_changed_closure_is_not_authorization(self):
        observation = deepcopy(self.observation)
        for key in ('source_pins', 'disk_hashes'):
            observation['targets']['learner'][key]['gpu/r232_runtime.py'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'whole_source_closure_changed'):
            self.validate(observation)

    def test_pid_reuse_wrong_cwd_or_argv_refused(self):
        for key, value in (('pid', 1), ('start_ticks', '1'), ('cwd', '/tmp'), ('argv', ['python'])):
            with self.subTest(key=key):
                observation = deepcopy(self.observation)
                observation['targets']['frozen']['native'][key] = value
                with self.assertRaises(ValueError):
                    self.validate(observation)

    def test_dead_native_refused(self):
        observation = deepcopy(self.observation)
        observation['targets']['learner']['native']['process_state'] = 'Z'
        with self.assertRaisesRegex(ValueError, 'native_not_live'):
            self.validate(observation)

    def test_guard_plan_and_lease_drift_refused(self):
        for key in ('guard_sha256', 'plan_sha256', 'lease_sha256'):
            with self.subTest(key=key):
                observation = deepcopy(self.observation)
                observation['targets']['learner'][key] = '0' * 64
                with self.assertRaises(ValueError):
                    self.validate(observation)

    def test_root_guard_path_and_deadline_drift_refused(self):
        for key, value in (('guard_path', '/tmp/GUARD.json'), ('root', '/tmp/raw'), ('hard_end_unix', 9999999999)):
            with self.subTest(key=key):
                observation = deepcopy(self.observation)
                observation['targets']['learner'][key] = value
                with self.assertRaises(ValueError):
                    self.validate(observation)

    def test_expired_capture_refused(self):
        observation = deepcopy(self.observation)
        observation['finished_unix'] = observation['targets']['learner']['hard_end_unix']
        with self.assertRaisesRegex(ValueError, 'observation_outside_current_guard_window'):
            self.validate(observation)

    def test_incomplete_pair_refused(self):
        observation = deepcopy(self.observation)
        del observation['targets']['frozen']
        with self.assertRaisesRegex(ValueError, 'both_pair_members_required'):
            self.validate(observation)

    def test_unpinned_extra_file_refused(self):
        observation = deepcopy(self.observation)
        observation['targets']['learner']['disk_hashes']['gpu/extra.py'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'disk_guard_mismatch'):
            self.validate(observation)

    def test_wrong_patch_postimage_refused(self):
        provenance = deepcopy(self.provenance)
        provenance['sources']['learner']['files'][adoption.CHANGED[0]]['proposed_fork_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'exact_patch_postimage'):
            adoption.candidate_bytes(provenance)

    def test_phase2_artifact_drift_refused(self):
        with tempfile.TemporaryDirectory(dir=adoption.OWN) as temporary:
            fake = Path(temporary)
            (fake / 'MANIFEST.json').write_text('{}')
            with patch.object(adoption, 'PHASE2', fake):
                with self.assertRaisesRegex(ValueError, 'phase2_binding'):
                    adoption.verify_phase2()

    def test_worker_path_traversal_refused(self):
        for name in ('', '.', '..', '../outside', '/tmp/outside', 'nested/path'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                adoption.confined_new_directory(name)

    def test_existing_output_and_symlink_refused(self):
        with tempfile.TemporaryDirectory(dir=adoption.OWN) as temporary:
            existing = Path(temporary)
            with self.assertRaises(ValueError):
                adoption.confined_new_directory(existing.name)
            link = existing / 'link'
            link.symlink_to('/tmp')
            with patch.object(adoption, 'OWN', existing), self.assertRaises(ValueError):
                adoption.confined_new_directory('link')

    def test_extra_output_file_refused(self):
        outputs = dict(self.outputs, **{'gpu/extra.py': b'no'})
        with self.assertRaisesRegex(ValueError, 'three_file_overlay_only'):
            adoption.build_receipt(self.observation, self.provenance, outputs)

    def test_receipt_rejects_nonfork_bytes(self):
        outputs = dict(self.outputs)
        outputs[adoption.CHANGED[0]] += b'\n'
        with self.assertRaisesRegex(ValueError, 'receipt_postimage_binding'):
            adoption.build_receipt(self.observation, self.provenance, outputs)


if __name__ == '__main__':
    unittest.main(verbosity=2)
