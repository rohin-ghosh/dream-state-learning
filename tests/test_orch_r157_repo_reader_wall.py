import ast
from copy import deepcopy
import importlib.util
import inspect
import json
from pathlib import Path
import signal
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from gpu import orch_r157_repo_reader_wall as wall


class WallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def saved(self):
        state = dict(pending=None, rows=['own history'], sleep_frontier=1,
            sleep_receipts=[dict(status='COMPLETE')], deadline_unix=wall.OLD_WALL,
            arbitrary_carry={'saved': True})
        return dict(state=state, state_sha256=wall.digest(state), cycle=33)

    def plan(self):
        return dict(physical=7, gpu_uuid=wall.GPU, root=str(wall.ROOT), source_root=str(wall.SOURCE),
            hard_end_unix=wall.OLD_WALL, lease_end_unix=1789617840,
            decoder={'unchanged': True}, authorized_wall_extension={'old_consumed': True})

    def config(self):
        return dict(resume=True, device_containment=dict(uid=2524, gid=2524, minor=7))

    def put(self, path, document):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document))
        return path

    def test_wall_epoch(self):
        from datetime import datetime, timezone
        self.assertEqual(datetime.fromtimestamp(wall.NEW_WALL, timezone.utc).isoformat(), '2026-09-19T00:00:00+00:00')

    def test_reader_parent_resume_preserves_original_loop(self):
        original = Path(wall.__file__).with_name('orch_r133_programme_parent.py').read_bytes()
        generated = wall.reader_parent_resume_source(original, {'path': '/tmp/spec', 'sha256': 'a' * 64})
        original_tree, generated_tree = ast.parse(original), ast.parse(generated)
        loops = []
        for tree in (original_tree, generated_tree):
            serve = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'serve')
            loops.append(ast.dump(next(node for node in ast.walk(serve) if isinstance(node, ast.While))))
        self.assertEqual(*loops)
        guard = next(node for node in generated_tree.body if isinstance(node, ast.FunctionDef) and node.name == '_r157_guard')
        root_checks = [node for node in ast.walk(guard) if isinstance(node, ast.Compare)
                       and ast.unparse(node.left) == "config['root']" and isinstance(node.ops[0], ast.In)]
        self.assertEqual(ast.literal_eval(root_checks[0].comparators[0]), (str(wall.HOST_ROOT),))
        self.assertIn('exact_reader_parent_only', generated)

    def test_reader_parent_rejects_changed_original(self):
        with self.assertRaisesRegex(ValueError, 'reviewed_programme_source_only'):
            wall.reader_parent_resume_source(b'def serve(): pass', {})

    def test_ceiling_is_ten_minute_compatibility_bound(self):
        self.assertEqual(wall.CEILING - wall.NEW_WALL, 600)

    def test_shared_authorization_exact_file(self):
        path = Path(__file__).resolve().parents[1] / 'research_loop/workers/r157_keepalive_20260917/AUTHORIZATION.json'
        if not path.exists():
            self.skipTest('shared artifact is tested separately on receiving host')
        self.assertFalse(wall.authority(path)['purchase_or_lease_transaction_authorized'])

    def test_changed_authority_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exact_Main'):
            wall.authority(self.put(self.root / 'AUTH.json', {'approved': True}))

    def test_correct_scope(self):
        wall.scope(self.plan(), self.config())

    def test_all_seven_foreign_slots_rejected(self):
        for physical in range(7):
            with self.subTest(physical=physical), self.assertRaises(ValueError):
                wall.scope(dict(self.plan(), physical=physical), self.config())

    def test_bool_slot_rejected(self):
        with self.assertRaises(ValueError):
            wall.scope(dict(self.plan(), physical=True), self.config())

    def test_foreign_uuid_rejected(self):
        with self.assertRaises(ValueError):
            wall.scope(dict(self.plan(), gpu_uuid='GPU-foreign'), self.config())

    def test_wrong_source_rejected(self):
        with self.assertRaises(ValueError):
            wall.scope(dict(self.plan(), source_root=str(wall.LIFE / 'source1')), self.config())

    def test_new_life_rejected(self):
        with self.assertRaises(ValueError):
            wall.scope(self.plan(), dict(self.config(), resume=False))

    def test_foreign_device_policy_rejected(self):
        for field, value in [('uid', 0), ('gid', 0), ('minor', 6)]:
            config = self.config()
            config['device_containment'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                wall.scope(self.plan(), config)

    def test_wall_only_plan_preserves_recipe_and_paths(self):
        old, saved = self.plan(), self.saved()
        before = deepcopy((old, saved))
        plan = wall.boundary_plan(old, saved)
        self.assertEqual({key for key in plan if plan[key] != old[key]},
                         {'hard_end_unix', 'lease_end_unix', 'authorized_wall_extension'})
        self.assertEqual((old, saved), before)
        self.assertEqual(plan['authorized_wall_extension']['previous_stream_sha256'], saved['state_sha256'])

    def test_pending_generation_rejected(self):
        saved = self.saved()
        saved['state']['pending'] = 'generation:pending'
        with self.assertRaisesRegex(ValueError, 'completed_saved'):
            wall.boundary_plan(self.plan(), saved)

    def test_pending_sleep_rejected(self):
        saved = self.saved()
        saved['state']['pending'] = 'sleep:pending'
        with self.assertRaises(ValueError):
            wall.boundary_plan(self.plan(), saved)

    def test_unsaved_training_rows_rejected(self):
        saved = self.saved()
        saved['state']['rows'].append('unsaved')
        with self.assertRaises(ValueError):
            wall.boundary_plan(self.plan(), saved)

    def test_empty_saved_checkpoint_rejected(self):
        saved = self.saved()
        saved['state']['sleep_receipts'] = []
        with self.assertRaises(ValueError):
            wall.boundary_plan(self.plan(), saved)

    def test_tampered_context_rejected(self):
        saved = self.saved()
        saved['state']['arbitrary_carry'] = {}
        with self.assertRaises(ValueError):
            wall.boundary_plan(self.plan(), saved)

    def test_old_saved30_deadline_rejected(self):
        saved = self.saved()
        saved['state']['deadline_unix'] = 1789596240
        saved['state_sha256'] = wall.digest(saved['state'])
        with self.assertRaises(ValueError):
            wall.boundary_plan(self.plan(), saved)

    def test_wrong_ceiling_rejected(self):
        with self.assertRaises(ValueError):
            wall.boundary_plan(self.plan(), self.saved(), wall.CEILING + 1)

    def test_preupdate_replay_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no_replay'):
            wall.boundary_plan(dict(self.plan(), preupdate_recovery={}), self.saved())

    def conflict(self):
        return dict(schema='R157_NODE5_TARGETED_RESERVATION_AUDIT_V1', host=wall.HOST,
            authorization_sha256=wall.AUTH_SHA, observed_utc='1970-01-01T00:16:40+00:00',
            conflicting_real_reservation_found=False, numeric_cutoff_is_not_booking=True,
            purchase_performed=False, actual_reservation_receipts=[])

    def test_actual_conflict_blocks(self):
        document = self.conflict()
        document['conflicting_real_reservation_found'] = True
        with self.assertRaises(ValueError):
            wall.conflict_check(self.put(self.root / 'conflict.json', document), 1001)

    def test_fresh_conflict_review(self):
        wall.conflict_check(self.put(self.root / 'conflict.json', self.conflict()), 1001)

    def test_stale_conflict_review_rejected(self):
        with self.assertRaises(ValueError):
            wall.conflict_check(self.put(self.root / 'conflict.json', self.conflict()), 12000)

    def test_unreviewed_availability_not_fabricated(self):
        document = dict(self.conflict(), numeric_cutoff_is_not_booking=False)
        with self.assertRaises(ValueError):
            wall.conflict_check(self.put(self.root / 'conflict.json', document), 1001)

    def test_no_signal_to_parents_or_foreign_roles(self):
        with patch.object(wall.signal, 'pidfd_send_signal') as send:
            for role in ('timer', 'supervisor', 'pilot', 'run1', 'other'):
                with self.subTest(role=role), self.assertRaises(ValueError):
                    wall.send(role, 999, signal.SIGTERM)
            send.assert_not_called()

    def test_no_SIGKILL(self):
        with patch.object(wall.signal, 'pidfd_send_signal') as send:
            with self.assertRaises(ValueError):
                wall.send('actor', 999, signal.SIGKILL)
            send.assert_not_called()

    def test_exact_allowed_pidfd_signal(self):
        with patch.object(wall.signal, 'pidfd_send_signal') as send:
            wall.send('actor', 100, signal.SIGCONT)
            send.assert_called_once_with(100, signal.SIGCONT)

    def test_no_destructive_process_group_api(self):
        tree = ast.parse(inspect.getsource(wall))
        calls = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
        self.assertFalse(calls & {'os.kill', 'os.killpg', 'shutil.rmtree'})

    def test_broker_command_no_foreign_GPU_access(self):
        command = wall.broker_command(self.root)
        self.assertIn('--property=DevicePolicy=strict', command)
        self.assertFalse(any('DeviceAllow=/dev/nvidia' in item for item in command))
        self.assertIn('--property=SendSIGKILL=no', command)
        self.assertIn('--property=KillMode=process', command)
        self.assertIn('--property=PrivateNetwork=yes', command)

    def test_every_capsule_load_binds_only_reader(self):
        capsule = SimpleNamespace(DEVICES={2:'foreign', 6:'foreign'})
        with patch.object(wall, 'load_api', return_value=capsule):
            self.assertEqual(wall.confinement().DEVICES, {7:wall.GPU})
            capsule.DEVICES = {0:'foreign'}
            self.assertEqual(wall.confinement().DEVICES, {7:wall.GPU})

    def test_contained_process_initializes_its_own_capsule(self):
        source = inspect.getsource(wall.contained)
        self.assertIn('capsule = confinement()', source)
        self.assertIn("'--foreground'", source)
        self.assertNotIn('--kill-after', source)

    def test_readmit_never_signals_or_initializes_new_life(self):
        source = inspect.getsource(wall.readmit)
        tree = ast.parse(source)
        calls = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
        self.assertFalse(calls & {'send', 'handoff', 'prepare', 'signal.pidfd_send_signal'})
        self.assertIn('readmit_only_failed_before_native_launch', source)
        self.assertIn('unchanged_stopped_saved_boundary', source)

    def test_broker_uses_existing_recovered_namespace(self):
        command = wall.broker_command(self.root)
        self.assertIn('--property=BindPaths=' + str(wall.HOST_ROOT) + ':' + str(wall.ROOT), command)
        self.assertIn('--property=ReadOnlyPaths=' + str(wall.ROOT), command)

    def test_publication_future_cursor_without_replay(self):
        directory, journal = self.root / 'broker', self.root / 'stream'
        directory.mkdir()
        result = wall.broker_reconciliation(directory, dict(index=10, next_index=11, record_sha256='head'), 10, 'head', journal)
        self.assertEqual(result['start_index'], 11)
        self.assertFalse(result['replay_past_reads'])
        self.assertFalse(result['publish_initial_connection'])

    def test_lagging_broker_rejected(self):
        with self.assertRaisesRegex(ValueError, 'caught_up'):
            wall.broker_reconciliation(self.root, dict(index=9, next_index=10, record_sha256='head'), 10, 'head', self.root)

    def test_unresolved_intent_rejected(self):
        self.put(self.root / 'INTENT_0001.json', {})
        with self.assertRaisesRegex(ValueError, 'unresolved'):
            wall.broker_reconciliation(self.root, dict(index=10, next_index=11, record_sha256='head'), 10, 'head', self.root)

    def publication(self):
        directory, journal = self.root / 'broker', self.root / 'stream'
        directory.mkdir()
        inbox = self.put(journal / 'inbox/published.json', {'saved': 'opaque'})
        publication = dict(id='published', sha256=wall.sha(inbox))
        self.put(directory / 'READ_0001.json', dict(manifest_sha256=wall.SNAPSHOT_SHA, publication=publication))
        self.put(directory / 'INTENT_0001.json', {})
        return directory, journal, publication

    def test_published_unconsumed_message_inherited_not_resent(self):
        directory, journal, publication = self.publication()
        result = wall.broker_reconciliation(directory, dict(index=10, next_index=11, record_sha256='head'), 10, 'head', journal)
        self.assertEqual(result['inherited_pending'], {'published': '0001'})
        self.assertEqual(len(result['reconciled_reads']), 1)

    def test_missing_published_bytes_rejected(self):
        directory, journal, publication = self.publication()
        (journal / 'inbox/published.json').unlink()
        with self.assertRaises(FileNotFoundError):
            wall.broker_reconciliation(directory, dict(index=10, next_index=11, record_sha256='head'), 10, 'head', journal)

    def test_consumed_publication_join(self):
        directory, journal, publication = self.publication()
        self.put(journal / 'records/00000000000000000008.json', dict(kind='INBOX', sha256='record8',
            document=dict(message={'id':publication['id']}, source_sha256=publication['sha256'])))
        self.put(directory / 'CONSUMED_0001.json', dict(record_index=8, inbox_id='published', record_sha256='record8'))
        result = wall.broker_reconciliation(directory, dict(index=10, next_index=11, record_sha256='head'), 10, 'head', journal)
        self.assertEqual(result['inherited_pending'], {})

    def generation(self):
        request = dict(split='TRAIN', segment='own', resume_state={'private': 'not hashed in request'})
        response = dict(request_sha256=wall.digest({'split':'TRAIN', 'segment':'own'}), response={'raw':'repo_read access.md'})
        committed = dict(source_sha256=wall.digest(response), segment='own')
        return request, response, committed

    def test_future_original_schema_request_response_join(self):
        self.assertEqual(wall.future_request(*self.generation()), 'repo_read access.md')

    def test_held_request_never_delivered(self):
        request, response, committed = self.generation()
        request['split'] = 'HELD'
        with self.assertRaises(ValueError):
            wall.future_request(request, response, committed)

    def test_uncommitted_response_rejected(self):
        request, response, committed = self.generation()
        committed['source_sha256'] = 'wrong'
        with self.assertRaises(ValueError):
            wall.future_request(request, response, committed)

    def test_cross_segment_response_rejected(self):
        request, response, committed = self.generation()
        committed['segment'] = 'foreign'
        with self.assertRaises(ValueError):
            wall.future_request(request, response, committed)

    def test_old_R154_output_rejected(self):
        with self.assertRaises(ValueError):
            wall.output_scope(wall.OLD)

    def test_exclusive_receipts(self):
        path = self.root / 'receipt.json'
        wall.write(path, {'first': True})
        with self.assertRaises(FileExistsError):
            wall.write(path, {'overwritten': True})

    def test_symlink_receipt_rejected(self):
        real = self.put(self.root / 'real.json', {})
        link = self.root / 'link.json'
        link.symlink_to(real)
        with self.assertRaises(ValueError):
            wall.read(link)


if __name__ == '__main__':
    unittest.main()
