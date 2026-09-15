import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r133_code_feedback_guard as guard


class GuardTests(unittest.TestCase):
    def config(self):
        return dict(schema='R133_MAIN_GUARD_V1', wrapper='ovx3', physical=7,
            gpu_uuid=guard.GPU_UUID, created_unix=1000, hard_end_unix=6000,
            next_reserved_unix=8000, lease_end_unix=30000, max_native_calls=96)

    def test_scope(self):
        guard.validate_scope(self.config(), 2000)

    def test_other_slot_or_quota_rejected(self):
        for key, value in (('wrapper', 'ovx'), ('physical', 6), ('gpu_uuid', 'GPU-other'),
                           ('max_native_calls', 97), ('schema', 'OTHER')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                guard.validate_scope(dict(self.config(), **{key: value}), 2000)

    def test_time_boundaries(self):
        for now in (999, 6000, 6001):
            with self.subTest(now=now), self.assertRaises(ValueError):
                guard.validate_scope(self.config(), now)
        for change in (dict(hard_end_unix=8300), dict(next_reserved_unix=6600),
                       dict(lease_end_unix=27600)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                guard.validate_scope(dict(self.config(), **change), 2000)

    def test_reference_requires_exact_bytes_and_absolute_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt.json'
            path.write_text(json.dumps({'status': 'COMPLETE'}))
            ref = dict(path=str(path), sha256=guard.sha(path))
            self.assertEqual(guard.reference(ref), path)
            for changed in (dict(ref, sha256='0' * 64), dict(ref, path='relative.json'),
                            dict(ref, extra=True)):
                with self.subTest(changed=changed), self.assertRaises(ValueError):
                    guard.reference(changed)

    def test_checkpoint_identity_and_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'adapter.bin'
            path.write_bytes(b'frozen fixture')
            adapter = dict(path=directory, base_sha256='b' * 64, state_sha256='s' * 64,
                           files=[['adapter.bin', guard.sha(path)]])
            checkpoint = dict(metadata=dict(update=18404, arm='FULL', adapter=adapter),
                              files={'adapter/adapter.bin': guard.sha(path)})
            guard.validate_checkpoint(dict(adapter=adapter), checkpoint)
            for metadata in (dict(checkpoint['metadata'], update=18405),
                             dict(checkpoint['metadata'], arm='CONTROL')):
                with self.assertRaises(ValueError):
                    guard.validate_checkpoint(dict(adapter=adapter), dict(checkpoint, metadata=metadata))
            with self.assertRaises(ValueError):
                guard.validate_checkpoint(dict(adapter=dict(adapter, state_sha256='other')), checkpoint)
            path.write_bytes(b'changed fixture')
            with self.assertRaises(ValueError):
                guard.validate_checkpoint(dict(adapter=adapter), checkpoint)

    def test_inventory_union_and_projection_identity(self):
        projection = dict(ref='LEGACY', spec_sha256=['a' * 64], task_id_sha256=['b' * 64],
                          used_seed_sha256=[])
        inventory = dict(schema='R133_HASH_ONLY_EXCLUSIONS_V1',
            normalization=guard.collection.public.NORMALIZATION, attested_by='Main',
            coverage='R119_LINEAGE_DECLARED_CODE_INVENTORIES',
            inventory_refs=[dict(ref='LEGACY', sha256='c' * 64)],
            spec_sha256=['a' * 64], task_id_sha256=['b' * 64], used_seed_sha256=[])
        guard.validate_inventory(inventory, [(projection, 'c' * 64)])
        for changed in (dict(inventory, task_id_sha256=[]),
                        dict(inventory, spec_sha256=['d' * 64])):
            with self.assertRaises(ValueError):
                guard.validate_inventory(changed, [(projection, 'c' * 64)])
        with self.assertRaises(ValueError):
            guard.validate_inventory(inventory, [(projection, 'd' * 64)])

    def test_native_without_dispatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'supervisor_dispatch_required'):
                guard.validate_native_entry(Path(directory) / 'config.json', dict(output_root=directory))

    def test_cleanup_targets_only_owned_session(self):
        process = Mock(pid=12345)
        process.poll.return_value = None
        with patch.object(guard.os, 'killpg') as kill:
            guard.reap_owned_child(process)
        kill.assert_called_once_with(12345, guard.signal.SIGTERM)
        process.wait.assert_called_once_with(timeout=10)
        process.reset_mock()
        process.poll.return_value = 0
        with patch.object(guard.os, 'killpg') as kill:
            guard.reap_owned_child(process)
        kill.assert_not_called()

    def test_cleanup_escalates_only_own_child_on_timeout(self):
        process = Mock(pid=12345)
        process.poll.return_value = None
        process.wait.side_effect = [guard.subprocess.TimeoutExpired('owned', 10), 0]
        with patch.object(guard.os, 'killpg') as kill:
            guard.reap_owned_child(process)
        self.assertEqual([entry.args for entry in kill.call_args_list],
                         [(12345, guard.signal.SIGTERM), (12345, guard.signal.SIGKILL)])

    def test_allocation_scope_and_dated_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / 'entry.md'
            declared = '1970-01-01T00:16:40Z'
            entry.write_text('[Builder / Main] ' + declared + '\n' + 'a' * 64)
            allocation = dict(self.config(), schema='R133_DATED_ALLOCATION_V1',
                purpose='PUBLIC_TRAIN_READONLY_COLLECTION', plan_sha256='a' * 64,
                checkpoint=18404, optimizer_steps=0, parent_calls=0, declared_utc=declared,
                builder_entry=dict(path=str(entry), sha256=guard.sha(entry)))
            guard.validate_allocation(allocation, self.config(), dict(plan_sha256='a' * 64))
            for changed in (dict(allocation, physical=6), dict(allocation, optimizer_steps=1),
                            dict(allocation, declared_utc='not a date')):
                with self.assertRaises(ValueError):
                    guard.validate_allocation(changed, self.config(), dict(plan_sha256='a' * 64))


if __name__ == '__main__':
    unittest.main()
