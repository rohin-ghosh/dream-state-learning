import importlib.util
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import runpy
import sys
import io
import tarfile


SPEC = importlib.util.spec_from_file_location('remote_checks', Path(__file__).with_name('remote_checks.py'))
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


class ReceivingChecksTests(unittest.TestCase):
    def fixture(self):
        overlay = {name: 'value = 1\n' for name in checks.ALLOWED}
        original = {name: checks.checksum(b'value = 0\n') for name in checks.ALLOWED
            if name not in {'gpu/checkpoint_tail_runtime.py', 'gpu/pair_retention_runtime.py'}}
        observation = dict(life='curriculum_learner', status='EXACT_GUARDED_SOURCE_VERIFIED',
            source_pins=original, guard_sha256='a' * 64, plan=dict(hard_end_unix=1790791200))
        prepared = dict(life=observation['life'], status='LOCAL_PREPARED_NOT_ADMITTED',
            old_source_pins=original, old_guard_sha256=observation['guard_sha256'],
            new_source_pins={name: checks.checksum(text.encode()) for name, text in overlay.items()},
            changed={name: dict(before=original.get(name), after=checks.checksum(text.encode()))
                for name, text in overlay.items()}, deadline_unix=1790791200)
        return observation, prepared, overlay

    def test_exact_six_file_source_only_overlay(self):
        observation, prepared, overlay = self.fixture()
        self.assertEqual(checks.validate_overlay(observation, prepared, overlay), prepared['new_source_pins'])

    def test_refuses_extra_code_or_missing_reader(self):
        for extra in (True, False):
            observation, prepared, overlay = self.fixture()
            if extra:
                overlay['gpu/unapproved.py'] = 'value = 1\n'
            else:
                overlay.pop('gpu/checkpoint_tail_runtime.py')
            with self.assertRaisesRegex(ValueError, 'six_file'):
                checks.validate_overlay(observation, prepared, overlay)

    def test_refuses_hash_mismatch_and_wall_extension(self):
        observation, prepared, overlay = self.fixture()
        prepared['deadline_unix'] += 1
        with self.assertRaisesRegex(ValueError, 'no_wall_extension'):
            checks.validate_overlay(observation, prepared, overlay)
        prepared['deadline_unix'] -= 1
        overlay['gpu/r232_recovery.py'] = 'value = 2\n'
        with self.assertRaisesRegex(ValueError, 'overlay_hashes'):
            checks.validate_overlay(observation, prepared, overlay)

    def test_no_activation_or_native_control(self):
        source = Path(checks.__file__).read_text()
        for forbidden in ('SIGTERM', 'SIGSTOP', 'pidfd_send_signal', 'systemd-run', 'dispatch_once'):
            self.assertNotIn(forbidden, source)
        self.assertIn("'historical_COMPLETE_LEARN_pair'", source)
        self.assertIn('live_boundary_reserved=False', source)

    def test_tail_observation_never_claims_handoff_or_modifies_scanner(self):
        source = Path(__file__).with_name('tail_observation.py').read_text()
        for forbidden in ('SIGTERM', 'SIGSTOP', 'pidfd_send_signal', 'flock(', 'dispatch_once'):
            self.assertNotIn(forbidden, source)
        self.assertIn('state = scan(journal, selection)', source)
        self.assertIn('authorizes_native_handoff=False', source)
        self.assertIn('persist_complete_anchors=False', source)

    def test_profile_refuses_unbound_inputs_before_importing_receiving_code(self):
        specification = importlib.util.spec_from_file_location('profile_tail',
            Path(__file__).with_name('profile_tail.py'))
        profiler = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(profiler)
        with tempfile.TemporaryDirectory() as directory:
            request = Path(directory) / 'request.json'
            helper = Path(directory) / 'observer.py'
            request.write_text('{}')
            helper.write_text('raise RuntimeError("must not import")')
            with self.assertRaisesRegex(ValueError, 'exact_probe_request_required'):
                profiler.profile(request, '0' * 64, helper, '0' * 64)
            with self.assertRaisesRegex(ValueError, 'exact_read_only_observer_required'):
                profiler.profile(request, hashlib.sha256(request.read_bytes()).hexdigest(),
                                 helper, '0' * 64)

    def test_profile_is_process_local_instrumentation_only(self):
        source = Path(__file__).with_name('profile_tail.py').read_text()
        for forbidden in ('write_text(', 'write_bytes(', 'SIGTERM', 'pidfd_send_signal',
                          'flock(', 'dispatch_once', 'os.kill('):
            self.assertNotIn(forbidden, source)
        self.assertIn('reader.hash_record = original_hash', source)
        self.assertIn('reader._decoded_record = original_decode', source)

    def test_complete_cost_is_explicitly_not_live_scan_or_handoff(self):
        source = Path(__file__).with_name('complete_cost_probe.py').read_text()
        for forbidden in ('write_text(', 'write_bytes(', 'SIGTERM', 'pidfd_send_signal',
                          'flock(', 'dispatch_once', 'os.kill('):
            self.assertNotIn(forbidden, source)
        self.assertIn('current_sidecars_verified=False', source)
        self.assertIn('full_scan_called=False', source)
        self.assertIn('authorizes_native_handoff=False', source)
        self.assertIn("hash_record(journal, index)", source)
        self.assertIn("candidate['learn_index'] + 1", source)

    def test_frontier_port_matches_main_source_and_refuses_double_application(self):
        specification = importlib.util.spec_from_file_location('frontier_port',
            Path(__file__).with_name('frontier_port.py'))
        overlay = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(overlay)
        repository = Path(__file__).resolve().parents[3]
        proposed = (repository / 'organism_v6/orch_r124_train_history.py').read_bytes()
        original = proposed
        for before, after in reversed(overlay.EDITS):
            self.assertEqual(original.count(after.encode()), 1)
            original = original.replace(after.encode(), before.encode(), 1)
        self.assertEqual(overlay.port(original), proposed)
        with self.assertRaisesRegex(ValueError, 'unmodified_target'):
            overlay.port(proposed)
        with self.assertRaisesRegex(ValueError, 'one_exact_seam'):
            overlay.port(original.replace(b'self._events = []', b'self._events = list()'))

    def test_frontier_port_cli_validates_before_creating_output(self):
        script = Path(__file__).with_name('frontier_port.py')
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / 'original.py'
            output = Path(directory) / 'output.py'
            for content in ('_frontier_hasher = None', 'not_the_expected_source = True'):
                original.write_text(content)
                with patch.object(sys, 'argv', [str(script), str(original), str(output)]):
                    with self.assertRaises(ValueError):
                        runpy.run_path(str(script), run_name='__main__')
                self.assertFalse(output.exists())

    def test_c2_bundle_rejects_unbound_paths_and_links(self):
        specification = importlib.util.spec_from_file_location('stage_c2',
            Path(__file__).with_name('stage_c2.py'))
        staging = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(staging)
        for name, kind in (('../outside', tarfile.REGTYPE),
                           ('C2/epoch3/linked', tarfile.SYMTYPE),
                           ('C2/epoch3/EPOCH3_SOURCE.json', tarfile.REGTYPE)):
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode='w:gz') as archive:
                entry = tarfile.TarInfo(name)
                entry.type = kind
                archive.addfile(entry, io.BytesIO())
            content = stream.getvalue()
            if name.endswith('EPOCH3_SOURCE.json'):
                self.assertEqual(len(staging.validated_members(content,
                    hashlib.sha256(content).hexdigest())), 1)
            else:
                with self.assertRaisesRegex(ValueError, 'only_unique_regular_epoch3_paths'):
                    staging.validated_members(content, hashlib.sha256(content).hexdigest())
            with self.assertRaisesRegex(ValueError, 'exact_prepared_archive'):
                staging.validated_members(content, '0' * 64)


if __name__ == '__main__':
    unittest.main()
