"""Exercise the copied runtime with exact observed plans and synthetic CPU state."""

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import interrupted_sleep as candidate
from receiving_fixture import EVIDENCE, SOURCE_PINS, build_fixture, load_receiving_sources, make_native


HERE = Path(__file__).resolve().parent


class AppliedWallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {life: load_receiving_sources(life) for life in ('C0', 'Astra7')}

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=HERE, prefix='.wall-fixture-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.use_life('C0')
        path_patch = patch.object(candidate, 'Path', side_effect=self.receiving_path)
        path_patch.start()
        self.addCleanup(path_patch.stop)

    def use_life(self, life):
        self.life = life
        self.fixture = build_fixture(self.root / life, life, self.sources[life])
        self.native = make_native(self.fixture)
        self.native.prepare_wall_extension = Mock(side_effect=AssertionError('wall_reapplication_forbidden'))
        self.plan_path = self.fixture.root / 'observed-plan.json'
        self.plan_path.write_bytes(self.fixture.plan_bytes)
        self.envelope = self.prepare()

    def receiving_path(self, value):
        if str(value) == self.fixture.plan['root']:
            return self.fixture.root
        return Path(value)

    def prepare(self, plan_bytes=None, life=None):
        return candidate.prepare_candidate(self.fixture.complete, self.fixture.pending,
            self.fixture.updates, recipe=self.fixture.recipe, eligibility=self.fixture.eligibility,
            life=self.life if life is None else life,
            plan_bytes=self.fixture.plan_bytes if plan_bytes is None else plan_bytes)

    def finish(self, envelope=None, plan_bytes=None, clock=lambda: 1789900000):
        envelope = self.envelope if envelope is None else envelope
        return candidate.finish_interrupted_sleep(envelope, expected_sha256=envelope['sha256'],
            native=self.native, journal=self.fixture.journal,
            plan_bytes=self.fixture.plan_bytes if plan_bytes is None else plan_bytes,
            anchors={'fixture': 'CPU-only wall compatibility'}, clock=clock)

    @staticmethod
    def encode(plan):
        return json.dumps(plan, sort_keys=True, separators=(',', ':')).encode()

    @staticmethod
    def resign(envelope):
        prepared = envelope['candidate']['contract']
        prepared['sha256'] = candidate.digest(prepared['contract'])
        envelope['sha256'] = candidate.digest(envelope['candidate'])
        return envelope

    def rebound_envelope(self, plan_bytes):
        envelope = deepcopy(self.envelope)
        envelope['candidate']['original_plan_sha256'] = hashlib.sha256(plan_bytes).hexdigest()
        compatibility = envelope['candidate']['applied_wall_compatibility']
        compatibility['original_plan_sha256'] = hashlib.sha256(plan_bytes).hexdigest()
        compatibility['authorization_sha256'] = candidate.digest(
            json.loads(plan_bytes).get('authorized_wall_extension'))
        return self.resign(envelope)

    def files(self):
        return {str(path.relative_to(self.root)): (path.stat().st_ino,
            hashlib.sha256(path.read_bytes()).hexdigest())
            for path in self.root.rglob('*') if path.is_file()}

    def assert_rejected(self, operation, reason):
        before = self.files()
        with self.assertRaisesRegex(ValueError, reason):
            operation()
        self.assertEqual(self.files(), before)
        self.assertEqual(self.native.instances, [])
        self.assertEqual(self.fixture.journal.records, [])
        self.assertFalse((self.fixture.root / 'interrupted_sleep_restarts').exists())
        self.native.prepare_wall_extension.assert_not_called()

    def assert_success_preserves_wall_and_history(self, expected_steps):
        old_plan = self.fixture.plan_bytes
        old_authorization = deepcopy(self.fixture.plan['authorized_wall_extension'])
        old_records = deepcopy((self.fixture.complete, self.fixture.pending,
            self.fixture.recipe, self.fixture.eligibility, self.fixture.updates))
        old_state = deepcopy(self.fixture.pending['document']['resume_state']['state'])
        old_envelope = deepcopy(self.envelope)
        old_files = self.files()
        with patch.object(candidate, 'validate_wall_extension', wraps=candidate.validate_wall_extension) as validator:
            self.assertEqual(self.prepare(), self.envelope)
            result = self.finish()
            self.assertEqual(validator.call_count, 2)
            for call in validator.call_args_list:
                self.assertEqual(call.args, (old_authorization,))
        self.assertEqual(self.envelope, old_envelope)
        self.assertEqual(self.fixture.plan_bytes, old_plan)
        self.assertEqual(self.plan_path.read_bytes(), old_plan)
        self.assertEqual(self.fixture.plan['authorized_wall_extension'], old_authorization)
        self.assertEqual(self.native.instances[0].plan, json.loads(old_plan))
        self.assertEqual(old_records, (self.fixture.complete, self.fixture.pending,
            self.fixture.recipe, self.fixture.eligibility, self.fixture.updates))
        for name, identity in old_files.items():
            self.assertEqual(self.files()[name], identity)
        state = result['stream_state']['state']
        for field in old_state:
            if field not in ('pending', 'sleep_frontier', 'sleep_receipts', 'model_state_sha256'):
                self.assertEqual(state[field], old_state[field], field)
        self.assertEqual(state['sleep_receipts'][:-1], old_state['sleep_receipts'])
        self.assertEqual(state['deadline_unix'], candidate.FINAL_BOUND)
        accounting = result['accounting']
        self.assertEqual(accounting['recovery_optimizer_steps'], 48)
        self.assertEqual(result['checkpoint']['optimizer_steps'], expected_steps)
        self.assertEqual(accounting['hard_end_unix'], candidate.FINAL_BOUND)
        plan_hash, authorization_hash = candidate.OBSERVED_WALL_BINDINGS[self.life]
        self.assertEqual(accounting['applied_wall_compatibility'], dict(
            schema='NODE2_OBSERVED_APPLIED_WALL_COMPATIBILITY_V1', life=self.life,
            original_plan_sha256=plan_hash, authorization_sha256=authorization_hash,
            final_bound_unix=candidate.FINAL_BOUND, authorization_reapplied=False,
            new_extension_event=False))
        self.assertEqual(accounting['rng_origin'], 'DURABLE_COMPLETE_NOT_UNSAVED_POST_GENERATION_STATE')
        self.assertFalse(accounting['exact_resident_continuity_claimed'])
        self.assertFalse(result['paired_LEARN_published'])
        kinds = [entry['kind'] for entry in self.fixture.journal.records]
        self.assertEqual(kinds.count('UPDATE'), 48)
        self.assertEqual(kinds.count('SLEEP_COMPLETE'), 1)
        self.assertNotIn('WALL_EXTENDED', kinds)
        self.assertNotIn('R184_LEARN_COMPLETE', kinds)
        self.native.prepare_wall_extension.assert_not_called()

    def test_C0_exact_observed_applied_wall_preserves_plan_and_history(self):
        self.assert_success_preserves_wall_and_history(8460)

    def test_Astra7_exact_observed_applied_wall_preserves_plan_and_history(self):
        self.use_life('Astra7')
        self.assert_success_preserves_wall_and_history(9692)

    def test_prepare_rejects_removed_null_or_nonobject_authorization(self):
        for value in ('removed', None, {}, [], True):
            with self.subTest(value=value):
                changed = deepcopy(self.fixture.plan)
                if value == 'removed':
                    del changed['authorized_wall_extension']
                else:
                    changed['authorized_wall_extension'] = value
                self.assert_rejected(lambda: self.prepare(self.encode(changed)),
                    'exact_observed_wall_authorization')

    def test_prepare_rejects_changed_authorization_even_with_same_final_bound(self):
        original = self.fixture.plan['authorized_wall_extension']
        mutations = {
            'schema': 'another_schema',
            'previous_stream_sha256': '0' * 64,
            'previous_deadline_unix': original['previous_deadline_unix'] - 1,
            'new_deadline_unix': candidate.FINAL_BOUND + 1,
            'lease_end_unix': candidate.OBSERVED_LEASE_END + 1,
            'safety_margin_seconds': 119,
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                changed = deepcopy(self.fixture.plan)
                changed['authorized_wall_extension'][field] = value
                self.assert_rejected(lambda: self.prepare(self.encode(changed)),
                    'exact_observed_wall_authorization')

    def test_prepare_rejects_malformed_authorization_fields(self):
        for field, value in (('new_deadline_unix', True), ('new_deadline_unix', float('inf')),
                ('lease_end_unix', float('nan')), ('previous_stream_sha256', 'not-a-digest')):
            with self.subTest(field=field, value=value):
                changed = deepcopy(self.fixture.plan)
                changed['authorized_wall_extension'][field] = value
                self.assert_rejected(lambda: self.prepare(self.encode(changed)),
                    'exact_observed_wall_authorization|Out of range float values')
        changed = deepcopy(self.fixture.plan)
        del changed['authorized_wall_extension']['schema']
        self.assert_rejected(lambda: self.prepare(self.encode(changed)),
            'exact_observed_wall_authorization')

    def test_prepare_rejects_a_new_consistent_extension(self):
        changed = deepcopy(self.fixture.plan)
        changed['hard_end_unix'] += 60
        changed['authorized_wall_extension']['new_deadline_unix'] += 60
        self.assert_rejected(lambda: self.prepare(self.encode(changed)),
            'exact_observed_wall_authorization')

    def test_prepare_rejects_plan_reserialization_or_whitespace(self):
        variants = (self.fixture.plan_bytes + b' ', b'\n' + self.fixture.plan_bytes,
            self.encode(self.fixture.plan))
        for raw in variants:
            with self.subTest(sha256=hashlib.sha256(raw).hexdigest()):
                self.assertNotEqual(raw, self.fixture.plan_bytes)
                self.assert_rejected(lambda: self.prepare(raw), 'exact_observed_plan_bytes')

    def test_prepare_rejects_other_plan_changes_and_preupdate_spoofs(self):
        for changes in (dict(hard_end_unix=candidate.FINAL_BOUND + 1),
                dict(lease_end_unix=candidate.OBSERVED_LEASE_END + 1),
                dict(root='/tmp/unbound-root'), dict(new_presentations=15),
                dict(preupdate_recovery={}), dict(preupdate_recovery={'fake': True})):
            with self.subTest(changes=changes):
                changed = dict(self.fixture.plan, **changes)
                self.assert_rejected(lambda: self.prepare(self.encode(changed)),
                    'exact_observed_plan_bytes')

    def test_prepare_rejects_wrong_life_and_nonbytes_input(self):
        for life, reason in (('Astra7', 'exact_observed_wall_authorization'),
                ('MathB', 'exact_observed_life_and_plan_bytes_required')):
            with self.subTest(life=life):
                self.assert_rejected(lambda: self.prepare(life=life), reason)
        for raw in (self.fixture.plan_bytes.decode(), bytearray(self.fixture.plan_bytes)):
            with self.subTest(input_type=type(raw).__name__):
                self.assert_rejected(lambda: self.prepare(raw),
                    'exact_observed_life_and_plan_bytes_required')

    def test_prepare_rejects_authenticated_complete_or_pending_with_different_wall(self):
        original = deepcopy((self.fixture.complete, self.fixture.pending,
            self.fixture.recipe, self.fixture.eligibility, self.fixture.updates))
        for field in ('complete', 'pending'):
            for deadline in (candidate.FINAL_BOUND - 1, candidate.FINAL_BOUND + 1):
                with self.subTest(field=field, deadline=deadline):
                    changed = getattr(self.fixture, field)
                    saved = changed['document']['resume_state']
                    saved['state']['deadline_unix'] = deadline
                    saved['sha256'] = candidate.digest(saved['state'])
                    changed['sha256'] = candidate.digest({key: value for key, value in changed.items()
                        if key != 'sha256'})
                    previous = self.fixture.pending
                    for record in (self.fixture.recipe, self.fixture.eligibility, *self.fixture.updates):
                        record['previous_sha256'] = previous['sha256']
                        record['sha256'] = candidate.digest({key: value for key, value in record.items()
                            if key != 'sha256'})
                        previous = record
                    self.assert_rejected(self.prepare, 'deadline_unchanged')
                    (self.fixture.complete, self.fixture.pending, self.fixture.recipe,
                        self.fixture.eligibility, self.fixture.updates) = deepcopy(original)

    def test_runtime_rejects_new_wall_even_after_envelope_and_contract_rehash(self):
        changed = deepcopy(self.fixture.plan)
        changed['hard_end_unix'] += 60
        changed['authorized_wall_extension']['new_deadline_unix'] += 60
        raw = self.encode(changed)
        envelope = self.rebound_envelope(raw)
        contract = envelope['candidate']['contract']['contract']
        contract['hard_end_unix'] = changed['hard_end_unix']
        saved = contract['preserved_state']
        saved['state']['deadline_unix'] = changed['hard_end_unix']
        saved['sha256'] = candidate.digest(saved['state'])
        self.resign(envelope)
        self.assert_rejected(lambda: self.finish(envelope, raw), 'exact_observed_wall_authorization')

    def test_runtime_rejects_new_authorization_with_same_final_bound_after_rehash(self):
        changed = deepcopy(self.fixture.plan)
        changed['authorized_wall_extension']['previous_stream_sha256'] = 'e' * 64
        raw = self.encode(changed)
        self.assert_rejected(lambda: self.finish(self.rebound_envelope(raw), raw),
            'exact_observed_wall_authorization')

    def test_runtime_rejects_field_removal_after_rehash(self):
        for value in ('removed', None, {}):
            with self.subTest(value=value):
                changed = deepcopy(self.fixture.plan)
                if value == 'removed':
                    del changed['authorized_wall_extension']
                else:
                    changed['authorized_wall_extension'] = value
                raw = self.encode(changed)
                self.assert_rejected(lambda: self.finish(self.rebound_envelope(raw), raw),
                    'exact_observed_wall_authorization')

    def test_runtime_rejects_changed_raw_bytes_after_rehash(self):
        raw = self.fixture.plan_bytes + b' '
        self.assert_rejected(lambda: self.finish(self.rebound_envelope(raw), raw),
            'exact_observed_plan_bytes')

    def test_runtime_rejects_other_lifes_observed_plan_after_rehash(self):
        other = build_fixture(self.root / 'other-plan', 'Astra7', self.sources['Astra7'])
        raw = other.plan_bytes
        self.assert_rejected(lambda: self.finish(self.rebound_envelope(raw), raw),
            'exact_observed_wall_authorization')

    def test_runtime_rejects_changed_compatibility_receipt_after_rehash(self):
        for field, value in (('final_bound_unix', candidate.FINAL_BOUND + 1),
                ('authorization_reapplied', True), ('new_extension_event', True),
                ('authorization_sha256', 'f' * 64)):
            with self.subTest(field=field):
                envelope = deepcopy(self.envelope)
                envelope['candidate']['applied_wall_compatibility'][field] = value
                self.resign(envelope)
                self.assert_rejected(lambda: self.finish(envelope), 'same_observed_wall_compatibility')

    def test_runtime_rejects_pending_wall_change_after_state_contract_and_envelope_rehash(self):
        for deadline in (candidate.FINAL_BOUND - 1, candidate.FINAL_BOUND + 1):
            with self.subTest(deadline=deadline):
                envelope = deepcopy(self.envelope)
                saved = envelope['candidate']['contract']['contract']['preserved_state']
                saved['state']['deadline_unix'] = deadline
                saved['sha256'] = candidate.digest(saved['state'])
                self.resign(envelope)
                self.assert_rejected(lambda: self.finish(envelope), 'wall_already_applied_to_pending_state')

    def test_runtime_does_not_extend_expired_observed_deadline(self):
        self.assert_rejected(lambda: self.finish(clock=lambda: candidate.FINAL_BOUND),
            'original_hard_end_expired')

    def test_wall_validator_is_exact_pinned_original_function_copy(self):
        copied = (HERE / 'applied_wall_validation.py').read_text()
        copied_function = next(node for node in ast.parse(copied).body
            if isinstance(node, ast.FunctionDef) and node.name == 'validate_wall_extension')
        relative = 'gpu/orch_r125_stream_journal.py'
        for life in ('C0', 'Astra7'):
            with self.subTest(life=life):
                raw = (EVIDENCE / life / relative).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), SOURCE_PINS[relative])
                original = raw.decode()
                original_function = next(node for node in ast.parse(original).body
                    if isinstance(node, ast.FunctionDef) and node.name == 'validate_wall_extension')
                self.assertEqual(ast.get_source_segment(copied, copied_function),
                    ast.get_source_segment(original, original_function))
                self.assertEqual(self.sources[life].journal.WALL_EXTENSION_SCHEMA,
                    'R131_SAVED_STATE_WALL_EXTENSION_V1')

    def test_Astra7_partial_intent_still_blocks_actual_runtime_without_mutation(self):
        self.use_life('Astra7')
        journal_root = self.fixture.root / 'physical-journal'
        with self.sources['Astra7'].journal.StreamJournal(journal_root, create=True) as physical:
            partial = journal_root / 'records/00000000000000007808.intent.json.partial'
            partial.write_bytes(b'')
            identity = (partial.stat().st_ino, partial.stat().st_size,
                hashlib.sha256(partial.read_bytes()).hexdigest())
            with patch.object(self.fixture.journal, 'audit', side_effect=physical.audit):
                self.assert_rejected(self.finish, 'incomplete_or_unexpected_journal_tail')
            self.assertEqual(identity, (partial.stat().st_ino, partial.stat().st_size,
                hashlib.sha256(partial.read_bytes()).hexdigest()))
            self.assertEqual(partial.read_bytes(), b'')


if __name__ == '__main__':
    unittest.main()
