import ast
from copy import deepcopy
import inspect
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r154_repo_reader_recover as recovery


class RepoReaderRecoveryTests(unittest.TestCase):
    def test_exact_original_scope_only(self):
        plan = dict(physical=7, gpu_uuid=recovery.GPU_UUID, root=str(recovery.ROOT),
                    source_root=str(recovery.LIFE / 'source1'), hard_end_unix=recovery.OLD_WALL,
                    lease_end_unix=recovery.LEASE_END)
        guard = dict(hard_end_unix=recovery.OLD_WALL, next_reserved_unix=recovery.LEASE_END)
        recovery.scope(plan, guard)
        for key, values in [('physical', [0, 1, 2, 3, 4, 5, 6, True]),
                            ('root', ['/foreign']), ('gpu_uuid', ['GPU-foreign']),
                            ('source_root', ['/foreign']), ('hard_end_unix', [recovery.HARD_END])]:
            for value in values:
                changed = dict(plan, **{key: value})
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    recovery.scope(changed, guard)

    def test_wall_receipt_changes_only_permitted_deadline(self):
        state = dict(deadline_unix=recovery.OLD_WALL, rows=['retained'], carry='retained',
                     pending=None, sleep_frontier=1, sleep_receipts=[dict(status='COMPLETE')])
        before = deepcopy(state)
        lease = dict(hard_end_unix=recovery.HARD_END, lease_end_unix=recovery.LEASE_END)
        result = recovery.wall_authorization(state, lease)
        self.assertEqual(result['previous_stream_sha256'], recovery.digest(state))
        self.assertEqual(result['new_deadline_unix'], 1789617240.0)
        self.assertEqual(result['safety_margin_seconds'], 600)
        self.assertEqual(state, before)
        for key in lease:
            with self.subTest(key=key), self.assertRaises(ValueError):
                recovery.wall_authorization(state, dict(lease, **{key: lease[key] + 1}))

    def test_previous_wall_must_match(self):
        with self.assertRaisesRegex(ValueError, 'prior_stream_wall'):
            recovery.wall_authorization(dict(deadline_unix=0),
                dict(hard_end_unix=recovery.HARD_END, lease_end_unix=recovery.LEASE_END))

    def test_wall_only_extension_rejects_pending_sleep(self):
        with self.assertRaisesRegex(ValueError, 'wall_extension_saved_sleep_boundary'):
            recovery.wall_authorization(dict(deadline_unix=recovery.OLD_WALL, pending='sleep:hash',
                rows=[], sleep_frontier=0, sleep_receipts=[dict(status='COMPLETE')]),
                dict(hard_end_unix=recovery.HARD_END, lease_end_unix=recovery.LEASE_END))

    def test_125_unsaved_updates_never_become_clean_resume(self):
        records = [dict(index=0, kind='SLEEP_COMPLETE', sha256='saved')]
        records.extend(dict(index=index, kind='UPDATE', sha256=str(index),
                            document=dict(optimizer_step=2745 + index, losses='not_returned'))
                       for index in range(1, 126))
        before = deepcopy(records)
        summary = recovery.suffix_summary(records, 0, 2745)
        self.assertEqual(summary['unsaved_updates'], 125)
        self.assertEqual(summary['last_optimizer_step'], 2870)
        self.assertFalse(summary['update_state_snapshots_available'])
        self.assertNotIn('losses', str(summary))
        self.assertEqual(records, before)
        with self.assertRaisesRegex(ValueError, 'separate_verified_reconciliation'):
            recovery.require_clean_recovery(summary, dict(pending=None, rows=[], sleep_frontier=0))

    def test_pending_generations_also_reject_clean_resume(self):
        for state in [dict(pending='sleep:hash', rows=[], sleep_frontier=0),
                      dict(pending=None, rows=['new'], sleep_frontier=0)]:
            with self.assertRaisesRegex(ValueError, 'saved_RNG_sleep_boundary'):
                recovery.require_clean_recovery(dict(unsaved_updates=0), state)

    def test_clean_boundary_is_only_precondition_not_launch(self):
        self.assertIsNone(recovery.require_clean_recovery(dict(unsaved_updates=0),
                          dict(pending=None, rows=['saved'], sleep_frontier=1)))

    def test_nonconsecutive_updates_rejected(self):
        records = [dict(kind='SLEEP_COMPLETE'), dict(kind='UPDATE', document=dict(optimizer_step=2747))]
        with self.assertRaisesRegex(ValueError, 'consecutive_UPDATE'):
            recovery.suffix_summary(records, 0, 2745)

    def test_entire_journal_chain_is_bound(self):
        manifest = dict(schema='journal', journal_id='own')
        record = dict(index=0, journal_id='own', previous_sha256=recovery.digest(manifest),
                      kind='SLEEP_COMPLETE', document={})
        record['sha256'] = recovery.digest(record)
        recovery.chain([record], manifest)
        for key, value in [('index', 1), ('journal_id', 'foreign'), ('previous_sha256', 'wrong'),
                           ('document', {'tampered': True})]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                recovery.chain([dict(record, **{key: value})], manifest)

    def test_inspection_has_no_launch_or_signal_or_remote_write_surface(self):
        source = inspect.getsource(recovery.inspect)
        tree = ast.parse(source)
        called = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
        self.assertFalse(called & {'os.kill', 'signal.pidfd_send_signal', 'subprocess.Popen',
                                  'shutil.copytree', 'journal.record', 'deliver'})
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                self.assertNotIn(node.func.attr, {'write_text', 'write_bytes', 'mkdir', 'unlink', 'rename'})

    def test_snapshot_exposes_only_reviewed_documents(self):
        self.assertEqual(recovery.ALLOWED_DOCUMENTS, {'access.md', 'overview.md', 'continuity.md'})
        self.assertIn('restart_from_zero_permitted=False', inspect.getsource(recovery.broker_preflight))

    def evidence(self):
        return dict(saved=dict(cycle=30, optimizer_steps=2745, index=3179, state_sha256=recovery.SAVED_SHA,
                    checkpoint=dict(sha256=recovery.CHECKPOINT_SHA)),
                    head=dict(index=3317, file=dict(sha256=recovery.HEAD_SHA)),
                    suffix=dict(unsaved_updates=125, last_optimizer_step=2870))

    def test_explicit_adjudication_allows_saved_not_interrupted_state(self):
        result = recovery.explicit_cutoff(self.evidence(), recovery.AUTHORITY)
        self.assertEqual(result['recovery_type'], 'EXACT_SAVED30_NOT_INTERRUPTED2870')
        self.assertEqual(result['unsaved_updates_not_restored'], 125)
        self.assertFalse(result['fresh_base_or_adapter'])
        self.assertFalse(result['archived_suffix_replayed'])
        self.assertFalse(result['archived_text_reinjected'])

    def test_saved_segment_requires_exact_authority(self):
        with self.assertRaisesRegex(ValueError, 'explicit_saved_checkpoint'):
            recovery.explicit_cutoff(self.evidence(), 'implicit')

    def test_changed_checkpoint_rejected(self):
        evidence = self.evidence()
        evidence['saved']['checkpoint']['sha256'] = 'foreign'
        with self.assertRaises(ValueError):
            recovery.explicit_cutoff(evidence, recovery.AUTHORITY)

    def test_changed_archival_cutoff_rejected(self):
        evidence = self.evidence()
        evidence['head']['index'] += 1
        with self.assertRaises(ValueError):
            recovery.explicit_cutoff(evidence, recovery.AUTHORITY)

    def test_archived_update_accounting_cannot_be_hidden(self):
        evidence = self.evidence()
        evidence['suffix']['unsaved_updates'] = 0
        with self.assertRaisesRegex(ValueError, '125_unsaved'):
            recovery.explicit_cutoff(evidence, recovery.AUTHORITY)

    def test_branch_plan_preserves_entire_recipe(self):
        plan = dict(root='/old/run1', source_root='/old/source', hard_end_unix=recovery.OLD_WALL,
                    startup_context=dict(path='/old/source/startup.md', sha256='same'),
                    seed=99, decoder={'temperature': .7}, context_limit=16384, arbitrary='retained')
        before = deepcopy(plan)
        branch = recovery.plan_for_segment(plan, Path('/new/run1'), Path('/new/source'), {'bound': True})
        self.assertEqual(branch['seed'], 99)
        self.assertEqual(branch['decoder'], before['decoder'])
        self.assertEqual(branch['startup_context']['sha256'], 'same')
        self.assertEqual(plan, before)
        self.assertEqual(branch['hard_end_unix'], recovery.HARD_END)
        self.assertNotIn('preupdate_recovery', branch)

    def test_segment_rejects_inherited_pending_recovery_directive(self):
        with self.assertRaises(ValueError):
            recovery.plan_for_segment(dict(preupdate_recovery={'unknown': 1}), Path('/new'), Path('/source'), {})

    def test_segment_directory_cannot_be_original_or_foreign(self):
        for path in (recovery.ROOT, recovery.LIFE / 'source1', Path('/tmp/recovery_r154_saved30_20260916_attempt1')):
            with self.subTest(path=path), self.assertRaises(ValueError):
                recovery.output_scope(path)
        self.assertEqual(recovery.output_scope(recovery.LIFE / 'recovery_r154_saved30_20260916_attempt1').parent,
                         recovery.LIFE)

    def test_prefix_copies_without_truncating_original_or_inbox_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            original = base / 'original'
            (original / 'records').mkdir(parents=True)
            (original / 'inbox').mkdir()
            (original / 'inbox/new.json').write_text('not copied')
            (original / 'JOURNAL.json').write_text('{}')
            for index in range(3):
                for suffix in ('.json', '.intent.json'):
                    (original / 'records' / (f'{index:020d}' + suffix)).write_text(str(index))
            before = {str(path.relative_to(original)): path.read_bytes() for path in original.rglob('*') if path.is_file()}
            recovery.copy_prefix(original, base / 'branch', 1)
            self.assertEqual(len(list((base / 'branch/records').iterdir())), 4)
            self.assertEqual(list((base / 'branch/inbox').iterdir()), [])
            self.assertEqual(before, {str(path.relative_to(original)): path.read_bytes() for path in original.rglob('*') if path.is_file()})
            with self.assertRaises(ValueError):
                recovery.copy_prefix(original, base / 'branch', 1)

    def test_broker_delivers_only_future_committed_TRAIN(self):
        request = dict(split='TRAIN', segment='seg', resume_state={'private': 'not part of request'})
        response = dict(request_sha256=recovery.digest(dict(split='TRAIN', segment='seg')), response=dict(raw='repo_read access.md'))
        committed = dict(source_sha256=recovery.digest(response), segment='seg')
        self.assertEqual(recovery.future_read(request, response, committed, 3179, 3183), 'repo_read access.md')
        with self.assertRaisesRegex(ValueError, 'future_segment'):
            recovery.future_read(request, response, committed, 3179, 1481)
        with self.assertRaises(ValueError):
            recovery.future_read(dict(request, split='FINAL'), response, committed, 3179, 3183)
        with self.assertRaises(ValueError):
            recovery.future_read(request, response, dict(committed, source_sha256='wrong'), 3179, 3183)

    def test_confinement_uses_only_seven_and_preserves_allocator(self):
        class Capsule:
            def device_containment_command(self, *args):
                self.args = args
                return ['sudo', 'systemd-run', '/usr/bin/env', '-i', 'CUDA_VISIBLE_DEVICES=' + recovery.GPU_UUID, 'payload']
        capsule = Capsule()
        config = dict(attempt_dir='/new/segment', device_containment=dict(minor=7, uid=2524, gid=2524, unit='own'))
        plan = dict(physical=7, source_root='/source')
        with patch.object(recovery, 'confinement', return_value=capsule):
            result = recovery.contained_command(config, plan, ['payload'], 100)
            self.assertEqual(capsule.args[:4], (7, 7, 2524, 2524))
            self.assertEqual(result[result.index('/usr/bin/env') + 2], 'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True')
            self.assertIn('--property=BindPaths=/new/segment/run1:' + str(recovery.ROOT), result)
            for physical in (0, 1, 2, 3, 4, 5, 6):
                with self.subTest(physical=physical), self.assertRaises(ValueError):
                    recovery.contained_command(config, dict(plan, physical=physical), ['payload'], 100)

    def test_stage_keeps_old_native_and_does_not_dispatch(self):
        source = inspect.getsource(recovery.stage)
        self.assertIn('entire_old_source_byte_identical_no_suffix_patch', source)
        self.assertNotIn('Popen', source)
        self.assertNotIn('pidfd_send_signal', source)
        self.assertIn('historical_readouts_already_dispatched', source)

    def test_launch_requires_posted_bound_gate(self):
        source = inspect.getsource(recovery.launch_gate)
        for binding in ('branch_cpu_sha256', 'operator_sha256', 'segment_sha256', 'posted'):
            self.assertIn(binding, source)
        self.assertIn('fresh_unchanged_privileged_admission', inspect.getsource(recovery.supervise))
        self.assertIn('verify_device_containment', inspect.getsource(recovery.contained))

    def test_broker_cannot_republish_initial_connection(self):
        source = inspect.getsource(recovery.broker)
        self.assertIn('publish_initial_connection=False', source)
        self.assertIn('historical_READs_replayed=False', source)
        self.assertIn("record['kind'] == 'COMMITTED'", source)
        self.assertIn("'BROKER_ONCE'", source)
        self.assertNotIn("'FIRST_READ.json'", source)

    def test_segment_mount_must_not_point_at_original(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            original = output / 'original'
            original.mkdir()
            branch = output / 'run1'
            branch.mkdir()
            segment = dict(original_root_device=original.stat().st_dev, original_root_inode=original.stat().st_ino)
            with patch.object(recovery, 'read', return_value=segment), patch.object(recovery, 'ROOT', original):
                with self.assertRaisesRegex(ValueError, 'private_namespace'):
                    recovery.verify_segment_mount(output)
            with patch.object(recovery, 'read', return_value=segment), patch.object(recovery, 'ROOT', branch):
                self.assertTrue(recovery.verify_segment_mount(output)['original_host_root_hidden'])

    def test_saved_inbox_copy_excludes_postcutoff_message(self):
        import json
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            old, new = base / 'old', base / 'new'
            (old / 'inbox').mkdir(parents=True)
            (old / 'records').mkdir()
            (new / 'inbox').mkdir(parents=True)
            saved, future = old / 'inbox/saved.json', old / 'inbox/future.json'
            saved.write_text('{}')
            future.write_text('{"not_reinjected":true}')
            record = dict(kind='INBOX', document=dict(source_id=str(saved), source_sha256=recovery.sha(saved)))
            (old / 'records/00000000000000000000.json').write_text(json.dumps(record))
            result = recovery.copy_saved_inbox(old, new, 0)
            self.assertEqual(set(result), {'saved.json'})
            self.assertEqual({path.name for path in (new / 'inbox').iterdir()}, {'saved.json'})
            self.assertTrue(future.exists())


if __name__ == '__main__':
    unittest.main()
