"""Synthetic CPU failures and original receiving-source transition regressions."""

import ast
from copy import copy, deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import interrupted_sleep as candidate
from receiving_fixture import EVIDENCE, SOURCE_PINS, build_fixture, load_receiving_sources, make_native


HERE = Path(__file__).resolve().parent


class InterruptedSleepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = load_receiving_sources()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=HERE, prefix='.cpu-fixture-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.fixture = build_fixture(self.root, 'C0', self.sources)
        self.native = make_native(self.fixture)
        path_patch = patch.object(candidate, 'Path', side_effect=self.receiving_path)
        path_patch.start()
        self.addCleanup(path_patch.stop)
        self.envelope = self.prepare(self.fixture, 'C0')
        self.pin = self.envelope['sha256']
        self.clock = lambda: 1789900000

    def receiving_path(self, value):
        if str(value) == self.fixture.plan['root']:
            return self.fixture.root
        return Path(value)

    @staticmethod
    def prepare(fixture, life):
        return candidate.prepare_candidate(fixture.complete, fixture.pending, fixture.updates,
            recipe=fixture.recipe, eligibility=fixture.eligibility, life=life, plan_bytes=fixture.plan_bytes)

    def run_candidate(self):
        return candidate.finish_interrupted_sleep(self.envelope, expected_sha256=self.pin,
            native=self.native, journal=self.fixture.journal, plan_bytes=self.fixture.plan_bytes,
            anchors={'fixture': 'CPU only; no training claims'}, clock=self.clock)

    def restart_directory(self):
        return self.root / 'interrupted_sleep_restarts' / self.envelope['candidate']['attempt_key']

    def destination(self):
        return self.root / 'checkpoints' / self.envelope['candidate']['checkpoint_name']

    def assert_no_completion(self):
        self.assertFalse(any(item['kind'] == 'SLEEP_COMPLETE' for item in self.fixture.journal.records))
        self.assertEqual(self.fixture.journal.latest_checkpoint()['document'],
            self.fixture.pending['document']['resume_state'])

    def assert_consumed(self):
        self.assertTrue(self.restart_directory().exists())
        before = len(self.native.instances)
        with self.assertRaisesRegex(ValueError, 'never_overwrite_or_adopt_checkpoint|restart_attempt_consumed'):
            self.run_candidate()
        self.assertEqual(len(self.native.instances), before)

    def test_C0_full_48_new_updates_not_remaining_zero(self):
        before = deepcopy(self.envelope)
        result = self.run_candidate()
        state = result['stream_state']['state']
        pending_state = self.fixture.pending['document']['resume_state']['state']
        for field in pending_state:
            if field not in ('pending', 'sleep_frontier', 'sleep_receipts', 'model_state_sha256'):
                self.assertEqual(state[field], pending_state[field], field)
        self.assertEqual((len(state['rows']), state['sleep_frontier']), (444, 444))
        self.assertEqual(len(state['sleep_receipts']), len(pending_state['sleep_receipts']) + 1)
        self.assertEqual(state['sleep_receipts'][:-1], pending_state['sleep_receipts'])
        self.assertIsNone(state['pending'])
        self.assertEqual(result['checkpoint']['optimizer_steps'], 8460)
        self.assertEqual(result['accounting']['recovery_optimizer_steps'], 48)
        self.assertEqual(result['accounting']['recorded_uncheckpointed_updates'], 48)
        self.assertEqual(result['accounting']['rng_origin'], 'DURABLE_COMPLETE_NOT_UNSAVED_POST_GENERATION_STATE')
        self.assertFalse(result['paired_LEARN_published'])
        self.assertEqual(self.envelope, before)
        self.assertEqual(self.native.instances[0].input_checkpoint, self.fixture.checkpoint)
        self.assertIn(b'synthetic_optimizer_python_CPU_CUDA_RNG_8412', self.native.instances[0].rng_source_bytes)
        self.assertEqual(len(self.native.instances[0].calls[0]['old_rows']), 441)
        self.assertEqual(len(self.native.instances[0].calls[0]['new_rows']), 3)
        self.assert_consumed()

    def test_Astra7_full_48_new_updates_not_remaining_19(self):
        self.root = self.root / 'Astra7'
        self.fixture = build_fixture(self.root, 'Astra7', self.sources)
        self.native = make_native(self.fixture)
        self.envelope = self.prepare(self.fixture, 'Astra7')
        self.pin = self.envelope['sha256']
        result = self.run_candidate()
        self.assertEqual(result['checkpoint']['optimizer_steps'], 9692)
        self.assertEqual(result['accounting']['recorded_uncheckpointed_updates'], 29)
        self.assertEqual(result['accounting']['recovery_optimizer_steps'], 48)
        self.assertTrue(result['accounting']['actual_lost_compute_not_fully_known'])
        self.assertEqual(result['stream_state']['state']['sleep_frontier'], 453)

    def test_failed_checkpoint_files_remain_byte_identical(self):
        failed = self.root / 'checkpoints/sleep_000146'
        failed.mkdir()
        artifact = failed / 'optimizer_rng.pt'
        artifact.write_bytes(b'old truncated forensic checkpoint; never promote')
        partial = failed / 'adapter.partial'
        partial.write_bytes(b'forensic partial')
        before = {path: (path.stat().st_ino, path.read_bytes()) for path in failed.iterdir()}
        self.run_candidate()
        self.assertEqual(before, {path: (path.stat().st_ino, path.read_bytes()) for path in failed.iterdir()})
        self.assertFalse((failed / 'COMMIT.json').exists())
        self.assertNotEqual(self.destination(), failed)

    def test_recovery_updates_have_distinct_epoch_and_new_counter_origin(self):
        result = self.run_candidate()
        updates = [entry for entry in self.fixture.journal.records if entry['kind'] == 'UPDATE']
        self.assertEqual([entry['document']['optimizer_step'] for entry in updates], list(range(8413, 8461)))
        for entry in updates:
            self.assertEqual(entry['document']['interrupted_sleep_restart']['compute_origin'], 'NEW_RECOVERY_COMPUTE')
            self.assertEqual(entry['document']['interrupted_sleep_restart']['epoch_sha256'],
                self.envelope['candidate']['contract']['sha256'])
        self.assertEqual(result['accounting']['recovery_first_update']['index'], 6714)
        self.assertTrue(all(entry['index'] > 6710 for entry in self.fixture.journal.records))

    def test_candidate_is_not_launch_authorization(self):
        self.assertFalse(candidate.EXECUTION_AUTHORIZED)
        self.assertFalse(self.envelope['candidate']['execution_authorized'])
        self.assertFalse(self.envelope['candidate']['contract']['contract']['execution_authorized'])
        self.run_candidate()
        kinds = {entry['kind'] for entry in self.fixture.journal.records}
        self.assertEqual(kinds, {'INTERRUPTED_SLEEP_RESTART', 'SLEEP_RECIPE', 'TARGET_ELIGIBILITY', 'UPDATE', 'SLEEP_COMPLETE'})

    def test_changed_candidate_pin_rejected_before_any_mutation(self):
        self.envelope['candidate']['contract']['contract']['preserved_state']['state']['rows'].pop()
        with self.assertRaisesRegex(ValueError, 'pinned_candidate'):
            self.run_candidate()
        self.assertFalse(self.native.instances)
        self.assertFalse(self.restart_directory().exists())

    def test_changed_original_plan_rejected(self):
        self.fixture.plan_bytes += b' '
        with self.assertRaisesRegex(ValueError, 'unchanged_original_plan_bytes'):
            self.run_candidate()
        self.assertFalse(self.native.instances)

    def test_prepare_rejects_deadline_extension_and_preupdate_spoof(self):
        for change in (dict(hard_end_unix=1789927201), dict(authorized_wall_extension={'fake': True}),
                dict(preupdate_recovery={'fake': True}), dict(preupdate_recovery={}),
                dict(authorized_wall_extension={}), dict(new_presentations=15), dict(rehearsal_presentations=1)):
            with self.subTest(change=change):
                changed = copy(self.fixture)
                changed.plan_bytes = json.dumps(dict(self.fixture.plan, **change)).encode()
                with self.assertRaises(ValueError):
                    self.prepare(changed, 'C0')

    def test_extended_or_changed_old_head_rejected(self):
        for field, value in (('index', 6712), ('previous', 'e' * 64)):
            with self.subTest(field=field):
                old = self.fixture.journal.state[field]
                self.fixture.journal.state[field] = value
                with self.assertRaisesRegex(ValueError, 'fresh_fully_verified_exact_old_head'):
                    self.run_candidate()
                self.fixture.journal.state[field] = old
        self.assertFalse(self.native.instances)

    def test_fresh_pending_state_must_match_without_reset_to_COMPLETE(self):
        self.fixture.journal.state['latest']['document'] = self.fixture.complete['document']['resume_state']
        with self.assertRaisesRegex(ValueError, 'exact_current_pending_stream'):
            self.run_candidate()
        self.assertFalse(self.native.instances)

    def test_saved_binary_mutation_rejected_before_model_load(self):
        Path(self.fixture.checkpoint['optimizer_rng_path']).write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'binary_file_binding'):
            self.run_candidate()
        self.assertFalse(self.native.instances)

    def test_saved_checkpoint_requires_COMMIT_not_loose_files(self):
        (Path(self.fixture.checkpoint['adapter_path']).parent / 'COMMIT.json').unlink()
        with self.assertRaises(FileNotFoundError):
            self.run_candidate()
        self.assertFalse(self.native.instances)

    def test_lossy_current_state_restore_is_rejected(self):
        original_restore = self.native.ContinualStream.restore
        def lossy_restore(document, *, expected_sha256):
            stream = original_restore(document, expected_sha256=expected_sha256)
            stream.history._working_entries.clear()
            return stream
        with patch.object(self.native.ContinualStream, 'restore', side_effect=lossy_restore):
            with self.assertRaisesRegex(ValueError, 'lossless_rows_history_working_state_restore'):
                self.run_candidate()
        self.assertFalse(self.native.instances)

    def test_full_journal_audit_failure_is_terminal_before_new_claim(self):
        with patch.object(self.fixture.journal, 'audit', side_effect=ValueError('unresolved_partial')):
            with self.assertRaisesRegex(ValueError, 'unresolved_partial'):
                self.run_candidate()
        self.assertFalse(self.native.instances)
        self.assertFalse(self.restart_directory().exists())

    def test_training_failure_before_first_update_stays_pending_no_retry(self):
        self.native.behavior.fail_at_step = 0
        with self.assertRaisesRegex(RuntimeError, 'synthetic_training_failure'):
            self.run_candidate()
        self.assert_no_completion()
        self.assert_consumed()

    def test_claim_is_not_freed_by_candidate_rebind(self):
        self.native.behavior.fail_at_step = 0
        with self.assertRaises(RuntimeError):
            self.run_candidate()
        original_bytes = self.fixture.plan_bytes
        self.fixture.plan_bytes += b' '
        with self.assertRaisesRegex(ValueError, 'exact_observed_plan_bytes'):
            self.prepare(self.fixture, 'C0')
        self.fixture.plan_bytes = original_bytes
        self.assert_consumed()

    def test_existing_or_dangling_recovery_checkpoint_refused(self):
        self.destination().symlink_to(self.root / 'missing-target')
        with self.assertRaisesRegex(ValueError, 'never_overwrite_or_adopt_checkpoint'):
            self.run_candidate()
        self.assertFalse(self.native.instances)

    def test_loaded_unsaved_counter_is_not_accepted(self):
        self.native.behavior.init_step_delta = 48
        with self.assertRaisesRegex(ValueError, 'restored_durable_child'):
            self.run_candidate()
        self.assert_no_completion()
        self.assert_consumed()

    def test_recipe_change_rejected(self):
        self.native.behavior.recipe_change = dict(new_presentations=15)
        with self.assertRaisesRegex(ValueError, 'unchanged_original_sleep_recipe'):
            self.run_candidate()
        self.assert_no_completion()

    def test_row_exclusions_rejected_before_update(self):
        self.native.behavior.eligibility_change = dict(excluded=[{'reason': 'arbitrary'}])
        with self.assertRaisesRegex(ValueError, 'unchanged_all_rows_target_eligibility'):
            self.run_candidate()
        self.assertEqual(self.native.instances[0].optimizer_steps, 8412)
        self.assert_no_completion()

    def test_partial_training_does_not_commit_even_with_returned_receipt(self):
        self.native.behavior.steps = 47
        with self.assertRaisesRegex(ValueError, 'full_pending_sleep_without_exclusions'):
            self.run_candidate()
        self.assert_no_completion()
        self.assertFalse(self.destination().exists())

    def test_full_counts_with_late_exclusions_do_not_commit(self):
        self.native.behavior.receipt_change = dict(excluded_rows=['no'])
        with self.assertRaisesRegex(ValueError, 'full_pending_sleep_without_exclusions'):
            self.run_candidate()
        self.assert_no_completion()

    def test_uncheckpointed_scalars_are_not_an_optimizer_continuation(self):
        self.native.behavior.wrong_counter = True
        with self.assertRaisesRegex(ValueError, 'new_recovery_updates_not_unsaved_counter_continuation'):
            self.run_candidate()
        self.assert_no_completion()

    def test_deadline_expired_before_start_creates_nothing(self):
        self.clock = lambda: 1789927200
        with self.assertRaisesRegex(ValueError, 'original_hard_end_expired'):
            self.run_candidate()
        self.assertFalse(self.restart_directory().exists())
        self.assertFalse(self.native.instances)

    def test_deadline_expires_during_training_no_completion(self):
        def clock():
            count = sum(entry['kind'] == 'UPDATE' for entry in self.fixture.journal.records)
            return 1789927200 if count >= 2 else 1789900000
        self.clock = clock
        with self.assertRaisesRegex(ValueError, 'original_hard_end_expired'):
            self.run_candidate()
        self.assert_no_completion()
        self.clock = lambda: 1789900000
        self.assert_consumed()

    def test_optimizer_mutation_before_publication_is_unknown_not_zero(self):
        self.native.behavior.raise_after_step = 1
        with self.assertRaisesRegex(RuntimeError, 'mutation_before_publication'):
            self.run_candidate()
        failure = json.loads((self.restart_directory() / 'FAILED_OR_UNKNOWN.json').read_bytes())
        self.assertEqual(failure['recovery_recorded_updates'], 1)
        self.assertEqual(self.native.instances[0].optimizer_steps, 8414)
        self.assertTrue(failure['actual_recovery_compute_not_fully_known'])
        self.assert_no_completion()
        self.assert_consumed()

    def test_recovery_ENOSPC_preserves_new_partial_and_no_retry(self):
        self.native.behavior.fail_save = True
        with self.assertRaisesRegex(OSError, 'synthetic_ENOSPC'):
            self.run_candidate()
        self.assertEqual((self.destination() / 'optimizer_rng.pt').read_bytes(), b'incomplete-new-recovery')
        self.assertFalse((self.destination() / 'COMMIT.json').exists())
        self.assert_no_completion()
        self.assert_consumed()

    def test_checkpoint_return_without_COMMIT_is_not_success(self):
        self.native.behavior.missing_commit = True
        with self.assertRaises(FileNotFoundError):
            self.run_candidate()
        self.assert_no_completion()
        self.assert_consumed()

    def test_checkpoint_return_with_different_COMMIT_is_not_success(self):
        self.native.behavior.corrupt_commit = True
        with self.assertRaisesRegex(ValueError, 'checkpoint_must_have_exact_COMMIT'):
            self.run_candidate()
        self.assert_no_completion()

    def test_COMPLETE_publication_failure_never_promotes_checkpoint(self):
        self.fixture.journal.fail_kind = 'SLEEP_COMPLETE'
        with self.assertRaisesRegex(OSError, 'publication_failure'):
            self.run_candidate()
        self.assertTrue((self.destination() / 'COMMIT.json').exists())
        self.assert_no_completion()
        self.assert_consumed()

    def test_sidecar_failure_after_durable_COMPLETE_is_unknown_not_retried(self):
        writer = candidate._write_once
        def fail_completion_receipt(path, document):
            if path.name == 'COMPLETED.json':
                raise OSError('sidecar_ENOSPC')
            return writer(path, document)
        with patch.object(candidate, '_write_once', side_effect=fail_completion_receipt):
            with self.assertRaisesRegex(OSError, 'sidecar_ENOSPC'):
                self.run_candidate()
        failure = json.loads((self.restart_directory() / 'FAILED_OR_UNKNOWN.json').read_bytes())
        self.assertIsNotNone(failure['complete_reference_if_returned'])
        self.assertEqual(len([entry for entry in self.fixture.journal.records if entry['kind'] == 'SLEEP_COMPLETE']), 1)
        self.assert_consumed()

    def test_original_transition_rejects_other_state_changes(self):
        self.run_candidate()
        document = next(entry['document'] for entry in self.fixture.journal.records if entry['kind'] == 'SLEEP_COMPLETE')
        for field, value in (('deadline_unix', 1789927201), ('rows', []), ('history', {})):
            with self.subTest(field=field):
                altered = deepcopy(document)
                altered['resume_state']['state'][field] = value
                altered['resume_state']['sha256'] = candidate.digest(altered['resume_state']['state'])
                state = dict(index=6711, previous=self.fixture.updates[-1]['sha256'],
                    latest=self.sources.journal.StreamJournal._checkpoint(self.fixture.pending['document']['resume_state']),
                    request=None, response=None, sleep_request={'cycle': 146}, inbox={})
                with self.assertRaises((ValueError, KeyError)):
                    self.fixture.journal.original._advance(state, 'SLEEP_COMPLETE', altered)

    def test_original_recovery_metadata_cannot_clear_pending(self):
        before = self.fixture.journal.latest_checkpoint()
        self.fixture.journal.record('INTERRUPTED_SLEEP_RESTART', {'pending': None, 'status': 'COMPLETE'})
        self.assertEqual(before, self.fixture.journal.latest_checkpoint())
        self.assertEqual(self.fixture.journal.state['sleep_request']['cycle'], 146)

    def test_original_transition_rejects_wrong_cycle_or_checkpoint_binding(self):
        self.run_candidate()
        document = next(entry['document'] for entry in self.fixture.journal.records if entry['kind'] == 'SLEEP_COMPLETE')
        for name in ('cycle', 'checkpoint_sha256'):
            with self.subTest(name=name):
                altered = deepcopy(document)
                altered[name] = 147 if name == 'cycle' else dict(adapter='b' * 64)
                state = dict(index=6711, previous=self.fixture.updates[-1]['sha256'],
                    latest=self.sources.journal.StreamJournal._checkpoint(self.fixture.pending['document']['resume_state']),
                    request=None, response=None, sleep_request={'cycle': 146}, inbox={})
                with self.assertRaises(ValueError):
                    self.fixture.journal.original._advance(state, 'SLEEP_COMPLETE', altered)

    def test_completion_agrees_with_original_finish_sleep_transition(self):
        other = build_fixture(self.root / 'reference', 'C0', self.sources)
        native = make_native(other)
        stream = self.sources.stream.ContinualStream.restore(other.pending['document']['resume_state'],
            expected_sha256=other.pending['document']['resume_state']['sha256'])
        child = native.NativeChild(other.plan, other.checkpoint)
        self.sources.original_finish(child, stream, other.journal, {}, other.root, 146)
        result = self.run_candidate()
        received = result['stream_state']['state']
        original = stream.checkpoint()['state']
        for field in ('rows', 'history', 'pending', 'sleep_frontier', 'deadline_unix', 'experiment'):
            self.assertEqual(received[field], original[field], field)
        new_receipt, original_receipt = received['sleep_receipts'][-1], original['sleep_receipts'][-1]
        for field in ('status', 'optimizer_steps', 'total_optimizer_steps', 'presentations',
                'new_row_sha256', 'cycle', 'excluded_rows', 'frozen_base_verified'):
            self.assertEqual(new_receipt[field], original_receipt[field], field)

    def test_original_journal_still_refuses_zero_byte_intent_partial(self):
        journal_root = self.root / 'physical-journal'
        with self.sources.journal.StreamJournal(journal_root, create=True):
            pass
        partial = journal_root / 'records/00000000000000007808.intent.json.partial'
        partial.write_bytes(b'')
        before = partial.stat()
        with self.assertRaisesRegex(ValueError, 'incomplete_or_unexpected_journal_tail'):
            self.sources.journal.StreamJournal(journal_root)
        self.assertEqual(partial.read_bytes(), b'')
        self.assertEqual(partial.stat().st_ino, before.st_ino)

    def test_original_publication_failure_poisoning_not_hidden_by_metadata(self):
        root = self.root / 'failure-journal'
        with self.sources.journal.StreamJournal(root, create=True) as journal:
            publisher = journal._publish
            def fail_record(directory, name, document):
                if name == '00000000000000000000.json':
                    raise OSError('after_intent')
                return publisher(directory, name, document)
            with patch.object(journal, '_publish', side_effect=fail_record):
                with self.assertRaisesRegex(OSError, 'after_intent'):
                    journal.record('INTERRUPTED_SLEEP_RESTART', {'fixture': True})
            with self.assertRaises(ValueError):
                journal.latest_checkpoint()
        self.assertTrue((root / 'records/00000000000000000000.intent.json').exists())
        with self.assertRaisesRegex(ValueError, 'incomplete_journal_tail'):
            self.sources.journal.StreamJournal(root)

    def test_both_receiving_source_copies_are_identically_pinned(self):
        for life in ('C0', 'Astra7'):
            for relative, expected in SOURCE_PINS.items():
                with self.subTest(life=life, source=relative):
                    self.assertEqual(hashlib.sha256((EVIDENCE / life / relative).read_bytes()).hexdigest(), expected)

    def test_original_constructor_contains_exact_saved_RNG_and_optimizer_restore(self):
        tree = ast.parse((EVIDENCE / 'C0/gpu/orch_r125_continual_native.py').read_bytes())
        native = next(item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == 'NativeChild')
        constructor = next(item for item in native.body if isinstance(item, ast.FunctionDef) and item.name == '__init__')
        source = ast.unparse(constructor)
        for expected in ("self.optimizer.load_state_dict(payload['optimizer'])", "self.torch.set_rng_state(payload['cpu_rng'])",
                "self.torch.cuda.set_rng_state_all(payload['cuda_rng'])", "random.setstate(payload['python_rng'])",
                "payload['parameter_names'] == list(self.parameters)"):
            self.assertIn(expected, source)


if __name__ == '__main__':
    unittest.main()
