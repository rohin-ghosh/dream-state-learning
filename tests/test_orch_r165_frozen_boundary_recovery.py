"""R165 CPU-only serialization, checkpoint custody, and transition regressions."""

from contextlib import contextmanager
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random
import socket
import tempfile
import threading
import types
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r165_frozen_boundary_recovery as recovery


REPO = Path(recovery.__file__).resolve().parents[1]
FROZEN = REPO / 'research_loop/workers/r158_matched_node4_20260917/candidate5/source'
TORCH_AVAILABLE = importlib.util.find_spec('torch') is not None and importlib.util.find_spec('safetensors') is not None


def original_stream():
    path = FROZEN / recovery.STREAM
    if not path.is_file():
        path = REPO / recovery.STREAM
    content = path.read_bytes()
    if recovery.IMPORT.encode() in content:
        content = content.replace(recovery.IMPORT.encode(), b'', 1).replace(
            recovery.NEW_PREDICATE.encode(), recovery.OLD_PREDICATE.encode(), 1)
    return content


@contextmanager
def repaired_stream():
    from organism_v6 import orch_r150_matched_stream as stream_module
    from gpu import orch_r150_matched_journal as journal_module

    module = types.ModuleType('r165_cpu_repaired_stream')
    exec(compile(recovery.repair_stream(original_stream()), recovery.STREAM, 'exec'), module.__dict__)
    with patch.object(stream_module, 'MatchedStream', module.MatchedStream), \
            patch.object(journal_module, 'MatchedStream', module.MatchedStream):
        yield module.MatchedStream


class SerializationTests(unittest.TestCase):
    def test_only_target_order_is_normalized(self):
        before = dict(r=8, lora_alpha=16, target_modules=['q_proj', 'v_proj'], other=['a', 'b'])
        after = dict(before, target_modules=['v_proj', 'q_proj'])
        self.assertEqual(recovery.semantic_config(before), recovery.semantic_config(after))
        self.assertEqual(before['target_modules'], ['q_proj', 'v_proj'])

    def test_all_other_config_changes_rejected(self):
        before = dict(r=8, lora_alpha=16, lora_dropout=0.05, target_modules=['q_proj', 'v_proj'],
            other=['a', 'b'], nested={'keys': [1, 2]}, enabled=False)
        changes = dict(r=16, lora_alpha=32, lora_dropout=0.1, target_modules=['q_proj', 'k_proj'],
            other=['b', 'a'], nested={'keys': [2, 1]}, enabled=True, unknown='new')
        for key, value in changes.items():
            with self.subTest(key=key):
                self.assertNotEqual(recovery.semantic_config(before), recovery.semantic_config(dict(before, **{key: value})))
        self.assertNotEqual(recovery.semantic_config(before), recovery.semantic_config(dict(before, r=8.0)))

    def test_invalid_target_sets_rejected(self):
        for targets in (None, 'q_proj', [], ['q_proj', 'q_proj'], ['q_proj', 1], ['']):
            with self.subTest(targets=targets), self.assertRaisesRegex(ValueError, 'unique_string'):
                recovery.semantic_config(dict(target_modules=targets))

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            path.write_text('{"r":8,"r":16}')
            with self.assertRaisesRegex(ValueError, 'duplicate_JSON'):
                recovery.read(path)

    def test_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            path.write_text('{"r":NaN}')
            with self.assertRaisesRegex(ValueError, 'nonfinite'):
                recovery.read(path)

    def test_symlink_reference_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / 'original'
            original.write_text('{}')
            link = Path(directory) / 'link'
            link.symlink_to(original)
            with self.assertRaises((ValueError, OSError)):
                recovery.reference(link)

    def test_reference_drift_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt'
            path.write_text('{}')
            ref = recovery.reference(path)
            path.write_text('{"changed":true}')
            with self.assertRaisesRegex(ValueError, 'immutable_reference'):
                recovery.bound(ref)

    def test_bound_decodes_only_admitted_bytes_after_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'GO.json'
            path.write_text('{"authority":"original"}')
            ref = recovery.reference(path)
            admitted = recovery.safe_bytes

            def replace_after_read(*args, **kwargs):
                raw = admitted(*args, **kwargs)
                path.write_text('{"authority":"replacement"}')
                return raw

            with patch.object(recovery, 'safe_bytes', side_effect=replace_after_read):
                self.assertEqual(recovery.bound(ref), {'authority': 'original'})
            with self.assertRaisesRegex(ValueError, 'immutable_reference_bytes'):
                recovery.bound(ref)

    def test_parent_symlink_and_fifo_not_admitted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'real').mkdir()
            (root / 'real/file').write_text('{}')
            (root / 'link').symlink_to(root / 'real', target_is_directory=True)
            with self.assertRaises(OSError):
                recovery.safe_bytes(root / 'link/file')
            recovery.os.mkfifo(root / 'fifo')
            with self.assertRaisesRegex(ValueError, 'admitted_regular_file'):
                recovery.safe_bytes(root / 'fifo')

    def test_receipt_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt'
            recovery.write_once(path, {'first': True})
            with self.assertRaises(FileExistsError):
                recovery.write_once(path, {'second': True})
            self.assertEqual(recovery.read(path), {'first': True})

    def test_patch_exactly_reversible_and_all_other_checks_retained(self):
        original = original_stream()
        repaired = recovery.repair_stream(original)
        reverted = repaired.replace(recovery.IMPORT.encode(), b'', 1).replace(
            recovery.NEW_PREDICATE.encode(), recovery.OLD_PREDICATE.encode(), 1)
        self.assertEqual(reverted, original)
        self.assertIn(b'frozen_optimizer_must_be_unchanged', repaired)
        self.assertIn(b'frozen_boundary_no_training', repaired)
        self.assertIn(b'learning_cannot_use_frozen_boundary', repaired)

    def test_patch_rejects_drift_and_second_application(self):
        original = original_stream()
        for content in (original + b'\n', recovery.repair_stream(original)):
            with self.subTest(content_hash=recovery.hashlib.sha256(content).hexdigest()), \
                    self.assertRaisesRegex(ValueError, 'exact_candidate5'):
                recovery.repair_stream(content)

    def test_stage_only_declared_files_with_readonly_original(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'old'
            (source / 'gpu').mkdir(parents=True)
            (source / 'organism_v6').mkdir()
            native = FROZEN / recovery.NATIVE
            if not native.is_file():
                native = REPO / recovery.NATIVE
            (source / recovery.NATIVE).write_bytes(native.read_bytes())
            (source / recovery.STREAM).write_bytes(original_stream())
            before = recovery.inventory(source)
            for item in source.rglob('*'):
                item.chmod(0o555 if item.is_dir() else 0o444)
            try:
                result = recovery.stage_source(source, root / 'new', before)
                self.assertEqual(recovery.inventory(source), before)
                self.assertEqual(result['changed_files'], [recovery.STREAM])
                self.assertEqual(result['added_files'], [recovery.HELPER])
                self.assertFalse(result['GPU_launched'])
                with self.assertRaisesRegex(ValueError, 'new_inactive'):
                    recovery.stage_source(source, root / 'new', before)
            finally:
                for item in source.rglob('*'):
                    item.chmod(0o755 if item.is_dir() else 0o644)

    def test_complete_requires_new_exact_GO(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepared = root / 'prepared.json'
            go = root / 'go.json'
            recovery.write_once(prepared, {})
            recovery.write_once(go, {'action': 'reuse_old_R160_GO'})
            with self.assertRaisesRegex(ValueError, 'exact_boundary_completion_GO'):
                recovery.complete_boundary(recovery.reference(prepared), recovery.reference(go), root / 'attempt')
            self.assertFalse((root / 'attempt').exists())

    def test_exact_prefix_rejects_appended_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = root / 'stream/records'
            records.mkdir(parents=True)
            (root / 'stream/JOURNAL.json').write_text('{}')
            for index in range(14):
                for suffix in ('', '.intent'):
                    (records / f'{index:020d}{suffix}.json').write_text('{}')
            self.assertEqual(len(recovery.journal_prefix(root)), 29)
            (records / '00000000000000000014.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'no_duplicate_boundary'):
                recovery.journal_prefix(root)

    def test_readout_unstarted_is_not_completed(self):
        from gpu import orch_r150_readout_custody as readouts
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            locations = {key: root / key for key in ('opened', 'closed', 'dispatch', 'output', 'log', 'failure')}
            with patch.object(readouts, 'paths', return_value=locations):
                self.assertEqual(readouts.disposition(None, {}, {}, 1), 'NOT_STARTED')
                locations['opened'].write_text('{}')
                with self.assertRaisesRegex(ValueError, 'unresolved_before_model_load'):
                    readouts.disposition(None, {}, {}, 1)


class CompletionAdmissionTests(unittest.TestCase):
    def setUp(self):
        from gpu import orch_r150_matched_journal as journal_module
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        manifest_path = self.root / 'manifest.json'
        recovery.write_once(manifest_path, dict(repaired_source=str(self.root / 'source')))
        orphan_path = self.root / 'orphan.json'
        recovery.write_once(orphan_path, {})
        self.proposed = dict(kind='SLEEP_COMPLETE', document=dict(resume_state={'CPU': 'fixture'}))
        self.prepared = dict(plan=dict(path=str(self.root / 'plan.json')), repair_manifest=recovery.reference(manifest_path),
            cohort=dict(sha256='b' * 64), prefix={}, evidence=dict(orphan=recovery.reference(orphan_path)),
            proposed_transition_sha256=recovery.digest(self.proposed), resume_checkpoint=recovery.reference(orphan_path),
            readout=dict(status='NOT_STARTED', completed=False))
        prepared_path = self.root / 'prepared.json'
        recovery.write_once(prepared_path, self.prepared)
        self.prepared_ref = recovery.reference(prepared_path)
        self.go_path = self.root / 'GO.json'
        recovery.write_once(self.go_path, dict(schema='R165_BOUNDARY_COMPLETION_MAIN_GO_V1', prepared=self.prepared_ref,
            action='COMPLETE_MISSING_SLEEP1_ONLY_NO_GPU', host=socket.gethostname(), not_before=100, expires=200))
        self.go_ref = recovery.reference(self.go_path)
        self.marker = self.root / 'FIXED_OPERATION'
        self.clock = 150
        self.journal = Mock()
        self.journal.latest_checkpoint.return_value = {'document': {'CPU': 'fixture'}}
        self.journal.record.return_value = dict(index=14, path=str(self.root / 'record14'), sha256='c' * 64)
        self.context = Mock()
        self.context.__enter__ = Mock(return_value=self.journal)
        self.context.__exit__ = Mock(return_value=False)
        patches = [patch.object(recovery, 'OPERATION_ONCE', self.marker), patch.object(recovery, 'HOST', socket.gethostname()),
            patch.object(recovery.time, 'time', side_effect=lambda: self.clock),
            patch.object(recovery, 'prepare', return_value=self.prepared),
            patch.object(recovery, 'journal_prefix', return_value={}),
            patch.object(recovery, 'transition', return_value=self.proposed),
            patch.object(journal_module, 'MatchedJournal', return_value=self.context)]
        self.patched = [value.start() for value in patches]
        for value in reversed(patches):
            self.addCleanup(value.stop)
        self.prepare = self.patched[3]
        self.transition = self.patched[5]
        self.constructor = self.patched[6]

    def call(self, destination='attempt1'):
        return recovery.complete_boundary(self.prepared_ref, self.go_ref, self.root / destination)

    def test_failed_constructor_cannot_retry_in_another_directory(self):
        self.constructor.side_effect = ValueError('injected_before_journal_ownership')
        with self.assertRaisesRegex(ValueError, 'injected_before'):
            self.call()
        self.assertTrue(recovery.read(self.marker / 'FAILED.json')['no_retry'])
        self.constructor.side_effect = None
        with self.assertRaises(FileExistsError):
            self.call('attempt2')
        self.assertEqual(self.constructor.call_count, 1)
        self.journal.record.assert_not_called()

    def test_crash_after_directory_consumption_cannot_retry(self):
        write_once = recovery.write_once

        def fail_consumed(path, value):
            if Path(path) == self.marker / 'CONSUMED.json':
                raise SystemExit('crash_after_mkdir')
            return write_once(path, value)

        with patch.object(recovery, 'write_once', side_effect=fail_consumed), self.assertRaises(SystemExit):
            self.call()
        self.assertTrue(self.marker.is_dir())
        with self.assertRaises(FileExistsError):
            self.call('other_receipts')
        self.constructor.assert_not_called()

    def test_two_concurrent_callers_only_one_can_reach_journal(self):
        started, release = threading.Event(), threading.Event()

        def fail_after_wait(*args, **kwargs):
            started.set()
            self.assertTrue(release.wait(5))
            raise ValueError('one_admitted_attempt_failed')

        self.constructor.side_effect = fail_after_wait
        outcome = []

        def first():
            try:
                self.call('first')
            except BaseException as error:
                outcome.append(type(error))

        thread = threading.Thread(target=first)
        thread.start()
        try:
            self.assertTrue(started.wait(5))
            with self.assertRaises(FileExistsError):
                self.call('concurrent')
        finally:
            release.set()
            thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(outcome, [ValueError])
        self.assertEqual(self.constructor.call_count, 1)

    def test_expiry_during_preparation_consumes_without_record(self):
        def expire(*args, **kwargs):
            self.clock = 250
            return self.prepared

        self.prepare.side_effect = expire
        with self.assertRaisesRegex(ValueError, 'current_bound_Main_GO'):
            self.call()
        self.journal.record.assert_not_called()
        self.assertTrue(self.marker.is_dir())
        with self.assertRaises(FileExistsError):
            self.clock = 150
            self.call('new_receipts')

    def test_expiry_during_transition_consumes_without_record(self):
        def expire(*args, **kwargs):
            self.clock = 201
            return self.proposed

        self.transition.side_effect = expire
        with self.assertRaisesRegex(ValueError, 'current_bound_Main_GO'):
            self.call()
        self.journal.record.assert_not_called()
        self.assertTrue(recovery.read(self.marker / 'FAILED.json')['no_retry'])

    def test_GO_replacement_under_lock_is_rejected_before_record(self):
        def replace(*args, **kwargs):
            self.go_path.write_text('{"replacement":true}')
            return self.proposed

        self.transition.side_effect = replace
        with self.assertRaisesRegex(ValueError, 'immutable_reference_bytes'):
            self.call()
        self.journal.record.assert_not_called()

    def test_completed_receipt_failure_cannot_retry(self):
        write_once = recovery.write_once

        def fail_completed(path, value):
            if Path(path).name == 'COMPLETED.json':
                raise OSError('injected_completion_receipt_failure')
            return write_once(path, value)

        with patch.object(recovery, 'write_once', side_effect=fail_completed), self.assertRaises(OSError):
            self.call()
        self.journal.record.assert_called_once()
        with self.assertRaises(FileExistsError):
            self.call('retry')
        self.assertEqual(self.journal.record.call_count, 1)


@unittest.skipUnless(TORCH_AVAILABLE, 'actual Torch+safetensors CPU dependencies required')
class CheckpointAndTransitionTests(unittest.TestCase):
    def setUp(self):
        import torch
        from organism_v6.orch_r125_continual_stream import experiment_binding, PRESLEEP_INVITATIONS
        self.torch = torch
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.experiment = experiment_binding(dict(seed=0, system_prompt='Standing purpose.',
            birth_prompt='Continue your inquiry.', presleep_variant='free_distillation',
            compaction_invitation=PRESLEEP_INVITATIONS['free_distillation']))
        self.initial = self.checkpoint('initial', targets=['q_proj', 'v_proj'])
        self.orphan = self.checkpoint('sleep_000001', targets=['v_proj', 'q_proj'], cuda_rng=7)

    def checkpoint(self, name, *, targets, cuda_rng=1):
        from safetensors.torch import save_file
        from gpu.orch_r125_continual_native import BASE_SHA256
        directory = self.root / 'checkpoints' / name
        adapter = directory / 'adapter'
        adapter.mkdir(parents=True)
        save_file({'layer.lora_A.weight': self.torch.arange(8, dtype=self.torch.float32).reshape(2, 4)},
            str(adapter / 'adapter_model.safetensors'))
        (adapter / 'adapter_config.json').write_text(json.dumps(dict(r=8, lora_alpha=16, lora_dropout=0.05,
            target_modules=targets, bias='none', modules_to_save=None)))
        (adapter / 'README.md').write_text('CPU fixture, not an actual model.')
        payload = dict(optimizer=dict(state={}, param_groups=[dict(params=[0], lr=0.001, betas=(0.9, 0.999))]),
            parameter_names=['layer.lora_A.default.weight'], optimizer_steps=0,
            experiment=self.experiment, cpu_rng=self.torch.get_rng_state(), python_rng=random.getstate(),
            cuda_rng=[self.torch.tensor([cuda_rng, 2, 3], dtype=self.torch.uint8)])
        self.torch.save(payload, directory / 'optimizer_rng.pt')
        files = {path.name: recovery.sha(path) for path in adapter.iterdir()}
        optimizer_sha = recovery.sha(directory / 'optimizer_rng.pt')
        result = dict(schema='CPU_FIXTURE', base_sha256=BASE_SHA256, adapter_path=str(adapter),
            adapter_files=files, adapter_state_sha256='a' * 64, optimizer_rng_path=str(directory / 'optimizer_rng.pt'),
            checkpoint_sha256=dict(adapter=recovery.digest(files), optimizer=optimizer_sha, rng=optimizer_sha),
            optimizer_steps=0, experiment=self.experiment)
        (directory / 'COMMIT.json').write_text(json.dumps(result))
        return result

    def repin(self, checkpoint):
        adapter = Path(checkpoint['adapter_path'])
        checkpoint['adapter_files'] = {path.name: recovery.sha(path) for path in adapter.iterdir()}
        checkpoint['checkpoint_sha256']['adapter'] = recovery.digest(checkpoint['adapter_files'])
        optimizer_sha = recovery.sha(checkpoint['optimizer_rng_path'])
        checkpoint['checkpoint_sha256'].update(optimizer=optimizer_sha, rng=optimizer_sha)
        (adapter.parent / 'COMMIT.json').write_text(json.dumps(checkpoint))

    def test_real_tensor_and_payload_identity_order_only(self):
        before = recovery.inventory(self.root)
        self.assertTrue(recovery.frozen_checkpoint_identity(self.initial, self.orphan))
        self.assertNotEqual(self.initial['checkpoint_sha256']['rng'], self.orphan['checkpoint_sha256']['rng'])
        self.assertEqual(recovery.inventory(self.root), before)
        self.assertFalse(self.torch.cuda.is_initialized())

    def test_optimizer_load_uses_hashed_BytesIO_after_path_replacement(self):
        import io
        original_load = self.torch.load
        optimizer_path = Path(self.orphan['optimizer_rng_path'])
        replacement = original_load(optimizer_path, weights_only=True)
        replacement['optimizer_steps'] = 1

        def replace_before_load(source, **kwargs):
            self.assertIsInstance(source, io.BytesIO)
            self.assertEqual(kwargs, dict(map_location='cpu', weights_only=True))
            self.torch.save(replacement, optimizer_path)
            return original_load(source, **kwargs)

        with patch.object(self.torch, 'load', side_effect=replace_before_load):
            payload, adapter_bytes = recovery.checkpoint_payload(self.orphan)
        self.assertEqual(payload['optimizer_steps'], 0)
        self.assertIn('adapter_config.json', adapter_bytes)
        with self.assertRaisesRegex(ValueError, 'optimizer_RNG_file_binding'):
            recovery.checkpoint_payload(self.orphan)

    def test_safetensors_load_uses_hashed_bytes_after_path_replacement(self):
        from safetensors import torch as tensor_module
        original_load = tensor_module.load
        model_path = Path(self.orphan['adapter_path']) / 'adapter_model.safetensors'

        def replace_before_load(raw):
            self.assertIsInstance(raw, bytes)
            model_path.write_bytes(b'replaced_after_admission')
            return original_load(raw)

        with patch.object(tensor_module, 'load', side_effect=replace_before_load), \
                patch.object(tensor_module, 'load_file', side_effect=AssertionError('no_path_reopen')):
            self.assertTrue(recovery.frozen_checkpoint_identity(self.initial, self.orphan))
        with self.assertRaisesRegex(ValueError, 'adapter_file_binding'):
            recovery.frozen_checkpoint_identity(self.initial, self.orphan)

    def test_config_decode_uses_hashed_bytes_after_path_replacement(self):
        admitted = recovery.safe_bytes
        config_path = Path(self.orphan['adapter_path']) / 'adapter_config.json'

        def replace_after_admission(path, *args, **kwargs):
            raw = admitted(path, *args, **kwargs)
            if Path(path) == config_path:
                config_path.write_text('{"target_modules":["wrong"],"r":64}')
            return raw

        with patch.object(recovery, 'safe_bytes', side_effect=replace_after_admission):
            self.assertTrue(recovery.frozen_checkpoint_identity(self.initial, self.orphan))
        with self.assertRaisesRegex(ValueError, 'adapter_file_binding'):
            recovery.frozen_checkpoint_identity(self.initial, self.orphan)

    def test_real_tensor_change_even_with_rehashed_COMMIT_rejected(self):
        from safetensors.torch import save_file
        save_file({'layer.lora_A.weight': self.torch.zeros((2, 4))},
            str(Path(self.orphan['adapter_path']) / 'adapter_model.safetensors'))
        self.repin(self.orphan)
        with self.assertRaisesRegex(ValueError, 'frozen_model_and_other_file_bytes'):
            recovery.frozen_checkpoint_identity(self.initial, self.orphan)

    def test_real_config_changes_even_with_rehashed_COMMIT_rejected(self):
        path = Path(self.orphan['adapter_path']) / 'adapter_config.json'
        original = recovery.read(path)
        for key, value in (('r', 16), ('target_modules', ['q_proj', 'k_proj']), ('lora_alpha', 32),
                ('lora_dropout', 0.0), ('modules_to_save', ['head']), ('bias', 'all'), ('extra', False)):
            with self.subTest(key=key):
                path.write_text(json.dumps(dict(original, **{key: value})))
                self.repin(self.orphan)
                with self.assertRaisesRegex(ValueError, 'full_frozen_config_semantics'):
                    recovery.frozen_checkpoint_identity(self.initial, self.orphan)

    def test_optimizer_payload_mutations_rejected(self):
        path = Path(self.orphan['optimizer_rng_path'])
        original = self.torch.load(path, weights_only=True)
        changes = [('optimizer_steps', 1), ('optimizer_steps', False), ('parameter_names', ['other']),
            ('optimizer', dict(state={0: {'step': self.torch.tensor(1.)}}, param_groups=original['optimizer']['param_groups'])),
            ('optimizer', dict(state={}, param_groups=[dict(params=[0], lr=0.002, betas=(0.9, 0.999))])),
            ('experiment', dict(self.experiment, seed=2))]
        for key, value in changes:
            with self.subTest(key=key, value_type=type(value).__name__):
                self.torch.save(dict(original, **{key: value}), path)
                self.repin(self.orphan)
                with self.assertRaises(ValueError):
                    recovery.frozen_checkpoint_identity(self.initial, self.orphan)

    def test_metadata_zero_not_enough_without_payload_zero(self):
        self.orphan['optimizer_steps'] = 1
        self.repin(self.orphan)
        with self.assertRaisesRegex(ValueError, 'frozen_checkpoint_zero_steps'):
            recovery.frozen_checkpoint_identity(self.initial, self.orphan)

    def test_raw_file_drift_rejected(self):
        (Path(self.orphan['adapter_path']) / 'README.md').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'adapter_file_binding'):
            recovery.frozen_checkpoint_identity(self.initial, self.orphan)

    def test_COMMIT_drift_rejected(self):
        self.orphan['created_unix'] = 1
        with self.assertRaisesRegex(ValueError, 'checkpoint_exact_COMMIT'):
            recovery.frozen_checkpoint_identity(self.initial, self.orphan)

    def test_unknown_adapter_file_rejected(self):
        (Path(self.orphan['adapter_path']) / 'unbound').write_text('new')
        with self.assertRaisesRegex(ValueError, 'no_unbound_adapter_entries'):
            recovery.frozen_checkpoint_identity(self.initial, self.orphan)

    def test_nonconfig_readme_drift_rejected_even_rehashed(self):
        (Path(self.orphan['adapter_path']) / 'README.md').write_text('changed')
        self.repin(self.orphan)
        with self.assertRaisesRegex(ValueError, 'frozen_model_and_other_file_bytes'):
            recovery.frozen_checkpoint_identity(self.initial, self.orphan)

    def make_pending(self, stream_class, journal):
        from organism_v6.orch_r124_train_history import TrainHistory
        from organism_v6.orch_r125_plain_context import VERSION
        stream = stream_class(TrainHistory(system_prompt=self.experiment['system_prompt'],
            birth_prompt=self.experiment['birth_prompt']), arm='parented_frozen', cohort_sha256='b' * 64,
            initial_checkpoint=self.initial, experiment=self.experiment, allow_eviction=True,
            context_limit=16384, segment_tokens=16, segments_per_sleep=2, deadline_unix=1000,
            model_state_sha256=recovery.digest(self.initial['checkpoint_sha256']))
        stream.set_presentation(dict(version=VERSION, system_prompt=self.experiment['system_prompt'],
            birth_prompt=self.experiment['birth_prompt']), 16384)
        journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
        for segment in range(2):
            stream.step(lambda *args, **kwargs: dict(raw='CPU fixture continuation.', token_ids=[4, 2],
                terminal=True, truncated=False), lambda messages: 20, journal.record, now=lambda: 100)
        pending = stream.checkpoint()
        pending['state']['pending'] = 'sleep:' + recovery.digest([row['source_sha256'] for row in stream.pending_rows()])
        pending['sha256'] = recovery.digest(pending['state'])
        journal.record('SLEEP_REQUEST', dict(cycle=1, resume_state=pending))
        return pending

    def test_actual_journal_transition_and_resume_select_orphan_without_replay(self):
        from gpu.orch_r150_matched_journal import MatchedJournal
        from gpu.orch_r150_matched_native import boundary_checkpoint
        from gpu.orch_r125_continual_native import NativeChild
        with repaired_stream() as stream_class:
            with MatchedJournal(self.root / 'stream', create=True, arm='parented_frozen', cohort_sha256='b' * 64) as journal:
                pending = self.make_pending(stream_class, journal)
                before_files = recovery.inventory(self.root / 'checkpoints')
                before_records = recovery.inventory(self.root / 'stream/records')
                with patch.object(NativeChild, '__init__', side_effect=AssertionError('no_model_construction')), \
                        patch.object(NativeChild, 'generate', side_effect=AssertionError('no_generation_replay')), \
                        patch.object(NativeChild, 'sleep', side_effect=AssertionError('no_sleep_replay')):
                    proposed = recovery.transition(pending, self.orphan)
                    journal.record(proposed['kind'], proposed['document'])
                latest = journal.latest_checkpoint()
                resumed = stream_class.restore(latest['document'], expected_sha256=latest['expected_sha256'],
                    expected_arm='parented_frozen', expected_cohort_sha256='b' * 64)
                self.assertIsNone(resumed.pending)
                self.assertEqual(resumed.sleep_frontier, len(resumed.rows))
                self.assertEqual(boundary_checkpoint(resumed, self.root), self.orphan)
                self.assertEqual(before_files, recovery.inventory(self.root / 'checkpoints'))
                after_records = recovery.inventory(self.root / 'stream/records')
                self.assertEqual({name: after_records[name] for name in before_records}, before_records)
                self.assertEqual(len(after_records), len(before_records) + 2)
                with self.assertRaisesRegex(ValueError, 'first_frozen_boundary_only'):
                    recovery.transition(latest['document'], self.orphan)
                with self.assertRaises(ValueError):
                    journal.record(proposed['kind'], proposed['document'])

    def test_future_boundary_retains_strong_frozen_invariants(self):
        from gpu.orch_r150_matched_journal import MatchedJournal
        with repaired_stream() as stream_class:
            with MatchedJournal(self.root / 'stream', create=True, arm='parented_frozen', cohort_sha256='b' * 64) as journal:
                pending = self.make_pending(stream_class, journal)
                proposed = recovery.transition(pending, self.orphan)
                journal.record(proposed['kind'], proposed['document'])
                latest = journal.latest_checkpoint()
                stream = stream_class.restore(latest['document'], expected_sha256=latest['expected_sha256'],
                    expected_arm='parented_frozen', expected_cohort_sha256='b' * 64)
                stream.step(lambda *args, **kwargs: dict(raw='Later CPU continuation.', token_ids=[5], terminal=True,
                    truncated=False), lambda messages: 20, journal.record, now=lambda: 100)
                next_checkpoint = self.checkpoint('sleep_000002', targets=['q_proj', 'v_proj'], cuda_rng=9)
                receipt = stream.frozen_boundary_receipt(next_checkpoint, frozen_base_verified=True, cycle=2)
                self.assertEqual(receipt['optimizer_steps'], 0)
                for key, value in (('optimizer_steps', 1), ('cumulative_optimizer_steps', 1),
                        ('presentations', [1]), ('child_token_exposures', 1), ('anchor_token_exposures', 1),
                        ('frozen_base_verified', False), ('before_adapter_sha256', 'c' * 64)):
                    with self.subTest(key=key), self.assertRaises(ValueError):
                        stream._validate_frozen_receipt(dict(receipt, **{key: value}))

    def test_authorized_completion_appends_once_and_preserves_prefix(self):
        from gpu.orch_r150_matched_journal import MatchedJournal
        import socket

        with repaired_stream() as stream_class:
            with MatchedJournal(self.root / 'stream', create=True, arm='parented_frozen', cohort_sha256='b' * 64) as journal:
                pending = self.make_pending(stream_class, journal)
            proposed = recovery.transition(pending, self.orphan)
            prefix = {path.name: recovery.reference(path) for path in (self.root / 'stream/records').iterdir()}
            manifest = self.root / 'manifest.json'
            recovery.write_once(manifest, dict(repaired_source=str(self.root / 'inactive_source')))
            plan = self.root / 'plan.json'
            recovery.write_once(plan, {})
            prepared = dict(plan=recovery.reference(plan), repair_manifest=recovery.reference(manifest),
                cohort=dict(sha256='b' * 64), prefix=prefix,
                evidence=dict(orphan=recovery.reference(Path(self.orphan['adapter_path']).parent / 'COMMIT.json')),
                proposed_transition_sha256=recovery.digest(proposed),
                resume_checkpoint=recovery.reference(Path(self.orphan['adapter_path']).parent / 'COMMIT.json'),
                readout=dict(status='NOT_STARTED', completed=False))
            prepared_path = self.root / 'prepared.json'
            recovery.write_once(prepared_path, prepared)
            go_path = self.root / 'go.json'
            recovery.write_once(go_path, dict(schema='R165_BOUNDARY_COMPLETION_MAIN_GO_V1',
                prepared=recovery.reference(prepared_path), action='COMPLETE_MISSING_SLEEP1_ONLY_NO_GPU',
                host=socket.gethostname(), not_before=1789640000, expires=1789646400))
            checkpoint_files = recovery.inventory(self.root / 'checkpoints')
            with patch.object(recovery, 'ROOT', self.root), patch.object(recovery, 'HOST', socket.gethostname()), \
                    patch.object(recovery, 'OPERATION_ONCE', self.root / 'fixed_operation'), \
                    patch.object(recovery, 'prepare', return_value=prepared), \
                    patch.object(recovery, 'journal_prefix', return_value=prefix), \
                    patch.object(recovery.time, 'time', return_value=1789640001):
                result = recovery.complete_boundary(recovery.reference(prepared_path), recovery.reference(go_path),
                    self.root / 'completion_attempt')
                self.assertEqual(result['status'], 'SLEEP_COMPLETE_APPENDED')
                self.assertFalse(result['GPU_launched'])
                self.assertFalse(result['readout']['completed'])
                self.assertEqual(recovery.inventory(self.root / 'checkpoints'), checkpoint_files)
                for ref in prefix.values():
                    recovery.bound(ref)
                with self.assertRaises(FileExistsError):
                    recovery.complete_boundary(recovery.reference(prepared_path), recovery.reference(go_path),
                        self.root / 'duplicate_attempt')
                self.assertFalse((self.root / 'duplicate_attempt').exists())
                self.assertTrue(recovery.read(self.root / 'fixed_operation/CONSUMED.json')['no_retry'])

    def test_real_journal_faults_preserve_records_and_forbid_replay(self):
        from gpu.orch_r150_matched_journal import MatchedJournal
        original_publish = MatchedJournal._publish
        original_write = recovery.write_once
        checkpoint_files = recovery.inventory(self.root / 'checkpoints')
        with repaired_stream() as stream_class:
            for phase, added_count in (('before_intent', 0), ('after_intent', 1),
                                       ('after_record', 2), ('completion_receipt', 2)):
                with self.subTest(phase=phase):
                    root = self.root / phase
                    root.mkdir()
                    with MatchedJournal(root / 'stream', create=True, arm='parented_frozen', cohort_sha256='b' * 64) as journal:
                        pending = self.make_pending(stream_class, journal)
                    proposed = recovery.transition(pending, self.orphan)
                    prefix = {path.name: recovery.reference(path) for path in (root / 'stream/records').iterdir()}
                    manifest = root / 'manifest.json'
                    recovery.write_once(manifest, dict(repaired_source=str(root / 'inactive_source')))
                    prepared = dict(plan=dict(path=str(root / 'plan.json')), repair_manifest=recovery.reference(manifest),
                        cohort=dict(sha256='b' * 64), prefix=prefix,
                        evidence=dict(orphan=recovery.reference(Path(self.orphan['adapter_path']).parent / 'COMMIT.json')),
                        proposed_transition_sha256=recovery.digest(proposed),
                        resume_checkpoint=recovery.reference(Path(self.orphan['adapter_path']).parent / 'COMMIT.json'),
                        readout=dict(status='NOT_STARTED', completed=False))
                    prepared_path = root / 'prepared.json'
                    recovery.write_once(prepared_path, prepared)
                    go_path = root / 'GO.json'
                    recovery.write_once(go_path, dict(schema='R165_BOUNDARY_COMPLETION_MAIN_GO_V1',
                        prepared=recovery.reference(prepared_path), action='COMPLETE_MISSING_SLEEP1_ONLY_NO_GPU',
                        host=socket.gethostname(), not_before=1789640000, expires=1789646400))

                    def fail_publish(directory, name, document):
                        if phase == 'before_intent' and '.intent.' in name:
                            raise OSError('injected_before_intent')
                        result = original_publish(directory, name, document)
                        if phase == 'after_intent' and '.intent.' in name:
                            raise OSError('injected_after_intent')
                        if phase == 'after_record' and '.intent.' not in name:
                            raise OSError('injected_after_record')
                        return result

                    def fail_receipt(path, value):
                        if phase == 'completion_receipt' and Path(path).name == 'COMPLETED.json':
                            raise OSError('injected_completion_receipt')
                        return original_write(path, value)

                    with patch.object(recovery, 'ROOT', root), patch.object(recovery, 'HOST', socket.gethostname()), \
                            patch.object(recovery, 'OPERATION_ONCE', root / 'FIXED_OPERATION'), \
                            patch.object(recovery, 'prepare', return_value=prepared), \
                            patch.object(recovery, 'journal_prefix', return_value=prefix), \
                            patch.object(recovery.time, 'time', return_value=1789640001), \
                            patch.object(MatchedJournal, '_publish', side_effect=fail_publish), \
                            patch.object(recovery, 'write_once', side_effect=fail_receipt):
                        with self.assertRaisesRegex(OSError, 'injected_'):
                            recovery.complete_boundary(recovery.reference(prepared_path), recovery.reference(go_path), root / 'attempt1')
                        with self.assertRaises(FileExistsError):
                            recovery.complete_boundary(recovery.reference(prepared_path), recovery.reference(go_path), root / 'attempt2')
                    self.assertEqual(len(list((root / 'stream/records').iterdir())), len(prefix) + added_count)
                    for ref in prefix.values():
                        recovery.bound(ref)
                    failure = recovery.read(root / 'FIXED_OPERATION/FAILED.json')
                    self.assertTrue(failure['no_retry'])
                    self.assertFalse(failure['automatic_replay'])
                    self.assertEqual(recovery.inventory(self.root / 'checkpoints'), checkpoint_files)

    def test_pending_identity_drift_and_nonfrozen_arm_rejected(self):
        from gpu.orch_r150_matched_journal import MatchedJournal
        with repaired_stream() as stream_class:
            with MatchedJournal(self.root / 'stream', create=True, arm='parented_frozen', cohort_sha256='b' * 64) as journal:
                pending = self.make_pending(stream_class, journal)
            for pending_value in (None, 'sleep:' + 'c' * 64, 'generation:unresolved'):
                changed = deepcopy(pending)
                changed['state']['pending'] = pending_value
                changed['sha256'] = recovery.digest(changed['state'])
                with self.subTest(pending=pending_value), self.assertRaises(ValueError):
                    recovery.transition(changed, self.orphan)
            changed = deepcopy(pending)
            changed['state']['matched']['arm'] = 'parented_learning'
            changed['sha256'] = recovery.digest(changed['state'])
            with self.assertRaisesRegex(ValueError, 'first_frozen_boundary_only'):
                recovery.transition(changed, self.orphan)


if __name__ == '__main__':
    unittest.main(verbosity=2)
