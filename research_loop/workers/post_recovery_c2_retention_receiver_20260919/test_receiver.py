"""Synthetic hook tests only; no remote process or real source is opened for writing."""

import ast
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from research_loop.workers.post_recovery_retention_boundary_20260918.boundary import (
    Refusal, SCHEMA, digest, read, read_boundary, sha)
from research_loop.workers.post_recovery_retention_boundary_20260918.coordinator import (
    validate_prepared, verify_receiver_plan)
from research_loop.workers.post_recovery_retention_boundary_20260918.operations import ReceivingHooks
from research_loop.workers.post_recovery_c2_retention_receiver_20260919.receiver import (
    C2Receiver, MainRoute, CHANGED_FILES, CONFINEMENT, DEADLINE, GPU_UUID, LEASE_END,
    ROUTE_GATES, TRIAL, plan_template, write_once)
from research_loop.workers.post_recovery_c2_retention_receiver_20260919.ports import proposed_ports, NATIVE, RUNTIME


OWN = Path(__file__).resolve().parent
WORKERS = OWN.parent


class ReceiverFixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='c2-hooks-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        old_source, new_source = self.root / 'old/source', self.root / 'new/source'
        pins = []
        r188 = WORKERS / 'post_recovery_matched_cohort_runtime_20260918/receiving/source/gpu/r188_node5_confinement.py'
        for source, version in ((old_source, 'old'), (new_source, 'new')):
            for name in CHANGED_FILES:
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(repr(version) + '\n')
            path = source / 'gpu/r188_node5_confinement.py'
            path.write_bytes(r188.read_bytes())
            native = WORKERS / 'rohin233_recovery_node4_20260918/private/port_C2' / NATIVE
            (source / NATIVE).write_bytes(native.read_bytes())
            if version == 'new':
                for name, data in proposed_ports(old_source).items():
                    (source / name).write_bytes(data)
            (source / 'STARTUP.md').write_text('unchanged startup')
            pins.append({str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')})
        life = self.root / 'life'
        journal = life / 'stream'
        (journal / 'records').mkdir(parents=True)
        (journal / 'inbox').mkdir()
        (journal / 'WRITER.lock').touch()
        self.binding = dict(pid=1139778, uid=2524, start_ticks='30025875',
            boot_id='2c05ffec-1b4c-472f-9688-2a37543a6f4a',
            guard_path=str(self.root / 'old/control/GUARD.json'), source_pins=pins[0],
            journal_root=str(journal), journal_id='260be8b8710a42559b291797c6e14983', hard_end_unix=DEADLINE)
        self.binding['command'] = ['python3', '-B', '-m', 'gpu.orch_r125_continual_guard',
            'native', '--config', self.binding['guard_path']]
        write_once(journal / 'JOURNAL.json', dict(schema=SCHEMA, journal_id=self.binding['journal_id']))
        directory = life / 'checkpoints/sleep_000004'
        adapter = directory / 'adapter'
        adapter.mkdir(parents=True)
        (adapter / 'adapter.json').write_text('{}')
        (directory / 'optimizer_rng.pt').write_bytes(b'synthetic-not-a-torch-payload')
        checkpoint = dict(adapter_path=str(adapter), optimizer_rng_path=str(directory / 'optimizer_rng.pt'),
            optimizer_steps=8, checkpoint_sha256=dict(adapter=digest('adapter'), optimizer=digest('optimizer'), rng=digest('rng')))
        write_once(directory / 'COMMIT.json', checkpoint)
        state = dict(pending=None, rows=[dict(source_sha256=digest('row'))], sleep_frontier=1,
            deadline_unix=DEADLINE, model_state_sha256=digest(checkpoint['checkpoint_sha256']),
            sleep_receipts=[dict(status='COMPLETE', cycle=4, checkpoint=checkpoint,
                checkpoint_sha256=checkpoint['checkpoint_sha256'])])
        previous = deepcopy(state)
        previous['deadline_unix'] = 1789776000
        authorization = dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1', previous_deadline_unix=1789776000,
            previous_stream_sha256=digest(previous), new_deadline_unix=DEADLINE,
            lease_end_unix=LEASE_END, safety_margin_seconds=21600)
        self.records = []
        self.append('SLEEP_COMPLETE', dict(status='COMPLETE', cycle=4, checkpoint=checkpoint,
            resume_state=dict(state=previous, sha256=digest(previous))))
        consumed = self.append('WALL_EXTENDED', dict(schema='R131_WALL_EXTENDED_V1', authorization=authorization,
            plan_sha256=digest('actual-historical-plan-in-this-synthetic-fixture'),
            state=dict(state=state, sha256=digest(state))))
        self.append('SLEEP_COMPLETE', dict(status='COMPLETE', cycle=4, checkpoint=checkpoint,
            resume_state=dict(state=state, sha256=digest(state))))
        self.append('R184_LEARN_COMPLETE', dict(cycle=4, checkpoint=checkpoint))
        write_once(journal / 'correction_ledger.json', dict(synthetic_fixture_only=True))
        selection = dict(policy='R233_PINNED_COMPLETE_TAIL_V1', root=str(journal),
            journal_id=self.binding['journal_id'], complete_index=0, complete_sha256=self.records[0]['sha256'],
            life_id=TRIAL, max_tail_records=2048, max_tail_bytes=1073741824, persist_complete_anchors=True,
            sidecars=[dict(name='correction_ledger.json', kind='R197_CORRECTION_CYCLE', required=True)])
        old_plan = dict(source_root=str(old_source), root=str(life), hard_end_unix=DEADLINE,
            lease_end_unix=LEASE_END, physical=1, gpu_uuid=GPU_UUID,
            startup_context=dict(path=str(old_source / 'STARTUP.md'), sha256=sha(old_source / 'STARTUP.md')),
            learn_row_policy='R227_ALL_AUTHENTIC_CHILD_ROWS_V1',
            system_prompt='unchanged', birth_prompt='unchanged', decoder=dict(temperature=0.7),
            think_act_learn=dict(trial_id=TRIAL, controls='learned-C2', cpu_gate_root='/unchanged/cpu',
                console_preemption_policy='R205_CONSOLE_PREEMPTION_V1'),
            checkpoint_tail_recovery=selection, authorized_wall_extension=authorization)
        control = self.root / 'old/control'
        write_once(control / 'PLAN.json', old_plan)
        write_once(control / 'LEASE.json', dict(lease_end_unix=LEASE_END, hard_end_unix=DEADLINE))
        write_once(control / 'ALLOCATION.json', dict(builder_entry_logged=True, declared_unix=1,
            gpu_uuid=GPU_UUID, physical=1))
        guard = dict(schema='R125_CONTINUAL_GUARD_V1', source_pins=pins[0], copy_raw=str(life), resume=True,
            hard_end_unix=DEADLINE, next_reserved_unix=LEASE_END, host_sha256=digest('same-host'),
            attempt_dir=str(control), plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
            lease_path=str(control / 'LEASE.json'), lease_sha256=sha(control / 'LEASE.json'),
            allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'))
        write_once(control / 'GUARD.json', guard)
        self.binding['guard_sha256'] = sha(control / 'GUARD.json')
        self.prepared = dict(old_guard_sha256=self.binding['guard_sha256'], old_source_pins=pins[0],
            new_source_pins=pins[1], old_plan=old_plan, new_plan=plan_template(old_plan, new_source),
            cpu_passed=True, same_journal=True, same_checkpoint_payloads=True, same_confinement=True,
            epoch_id='synthetic-C2-epoch1')
        changes = {name: dict(before=pins[0].get(name), after=pins[1][name])
            for name in CHANGED_FILES | {NATIVE, RUNTIME}}
        self.staged = dict(life='C2', status='IMMUTABLE_SOURCE_STAGED_NOT_DISPATCHABLE',
            old_source=str(old_source), new_source=str(new_source), old_source_pins=pins[0], new_source_pins=pins[1],
            journal_root=str(journal), journal_id=self.binding['journal_id'], changed=changes,
            old_guard_sha256=self.binding['guard_sha256'], native=dict(
                {key: self.binding[key] for key in ('pid', 'uid', 'boot_id', 'start_ticks')}, argv=self.binding['command']))
        self.authority = dict(schema='RETENTION_SOURCE_CHANGE_AUTHORITY_V1', life_binding_sha256=digest(self.binding),
            epoch_id=self.prepared['epoch_id'], wall_extension_authorized=False, approved_source_changes=changes)
        self.cpu_path = self.root / 'SYNTHETIC_CPU.json'
        write_once(self.cpu_path, dict(passed=True, source_pins=pins[1], scope='ACTUAL_RECEIVING_SOURCE_CPU',
            synthetic_fixture_only=True))
        evidence = self.root / 'SYNTHETIC_OWNER_EVIDENCE.json'
        ledger = self.root / 'SYNTHETIC_LEDGER.json'
        write_once(evidence, dict(synthetic=True))
        write_once(ledger, dict(delivered=['already-delivered'], synthetic=True))
        self.route_receipt = dict(schema='C2_RETENTION_MAIN_ROUTE_V1', owner='synthetic-test-owner', durable=True,
            life_binding_sha256=digest(self.binding), prepared_sha256=digest(self.prepared),
            source_pins_sha256=digest(pins[1]), dispatcher_module=CONFINEMENT, deadline_unix=DEADLINE,
            automatic_parent_adoption=False, inflight_deliveries=0,
            evidence_pins={str(evidence): sha(evidence)}, ledger_pins={str(ledger): sha(ledger)},
            **{key: True for key in ROUTE_GATES})
        self.dispatch = Mock(return_value=dict(synthetic=True, launched=False))
        self.route = MainRoute(lambda binding, prepared: deepcopy(self.route_receipt), lambda handle: True, self.dispatch)
        self.receiver = C2Receiver(self.binding, self.staged, cpu_receipt_path=self.cpu_path,
            consumed_wall_receipt=dict(record=consumed,
                intent=read(journal / 'records' / f"{consumed['index']:020d}.intent.json")),
            python_executable='/test-only/python', route=self.route)
        self.candidate = read_boundary(self.binding, durable=True)
        self.probe = patch.object(self.receiver, '_probe', side_effect=self.synthetic_probe).start()
        self.addCleanup(patch.stopall)
        self.process_run = patch('subprocess.run', side_effect=AssertionError('no_process_execution_in_hook_tests')).start()
        self.process_popen = patch('subprocess.Popen', side_effect=AssertionError('no_process_execution_in_hook_tests')).start()
        self.kill = patch('os.kill', side_effect=AssertionError('no_signals_in_hook_tests')).start()

    def append(self, kind, document):
        record = dict(schema=SCHEMA, journal_id=self.binding['journal_id'], index=len(self.records), kind=kind,
            previous_sha256=self.records[-1]['sha256'] if self.records else digest(dict(schema=SCHEMA,
                journal_id=self.binding['journal_id'])), document=deepcopy(document))
        record['sha256'] = digest(record)
        intent = dict(schema=SCHEMA, journal_id=record['journal_id'], index=record['index'],
            previous_sha256=record['previous_sha256'], record_sha256=record['sha256'])
        root = Path(self.binding['journal_root']) / 'records'
        write_once(root / f"{record['index']:020d}.json", record)
        write_once(root / f"{record['index']:020d}.intent.json", intent)
        self.records.append(record)
        return record

    def synthetic_probe(self, mode, candidate, plan, selection=None):
        if mode == 'checkpoint':
            return dict(adapter_verified=True, optimizer_verified=True, python_cpu_cuda_rng_verified=True,
                working_state_verified=True, no_GPU_calls=True, synthetic_fixture_only=True)
        if mode == 'guard':
            return dict(validated=True, admission_bypassed=False, guard_sha256=sha(selection['guard_path']))
        return dict(complete_index=candidate['complete_index'], complete_sha256=candidate['complete_sha256'],
            restored_state_sha256=candidate['resume_state']['sha256'], record_count=candidate['head_index'] + 1,
            head_sha256=candidate['head_sha256'], prefix_work='ALL_RETAINED_BYTES_HASHED_NO_HISTORICAL_BODY_JSON_REPLAY',
            read_only=True, writer_lock_acquired=False, journal_writes=0, pending=None,
            sidecars_verified=True, inbox_preserved=True, synthetic_fixture_only=True,
            sidecar_pins={'correction_ledger.json': sha(Path(self.binding['journal_root']) / 'correction_ledger.json')})

    def prepare(self):
        self.receiver.verify_prepared(self.prepared)
        proof = self.receiver.verify_checkpoint(self.candidate)
        result = self.receiver.prepare_receiver(self.candidate, self.prepared, proof)
        return proof, result

    def token(self, result):
        token = dict(schema='RETENTION_HANDOFF_TOKEN_V1', epoch_id=self.prepared['epoch_id'],
            life_binding_sha256=digest(self.binding), prepared_sha256=digest(self.prepared),
            authority_sha256=digest(self.authority), old_pid=self.binding['pid'],
            old_start_ticks=self.binding['start_ticks'], old_native_exited=True, exact_complete=self.candidate,
            receiver=result, new_source_pins=self.prepared['new_source_pins'], deadline_unix=DEADLINE,
            no_cold_start=True, no_unresolved_work_replayed=True, epoch_record_required_before_first_THINK=True)
        token['sha256'] = digest(token)
        return token


class ReceivingTests(ReceiverFixture):
    def test_seven_boundary_hooks_and_prepared_authority(self):
        hooks = self.receiver.hooks()
        self.assertIsInstance(hooks, ReceivingHooks)
        self.assertEqual(len(hooks.__dataclass_fields__), 7)
        validate_prepared(self.binding, self.prepared, self.authority)
        hooks.verify_prepared(self.prepared)
        self.assertTrue(hooks.dependents_clear(object()))

    def test_missing_route_refuses_before_checkpoint_reservation_or_signals(self):
        self.receiver.route = None
        with self.assertRaisesRegex(Refusal, 'route_required_before_stop'):
            self.receiver.verify_prepared(self.prepared)
        self.probe.assert_not_called()
        self.kill.assert_not_called()

    def test_original_epoch1_without_adoption_seam_refuses_before_stop(self):
        for mapping in (self.prepared['new_source_pins'], self.receiver.staged['new_source_pins']):
            mapping.pop(RUNTIME)
        with self.assertRaisesRegex(Refusal, 'epoch1_missing_C2_adoption_seam'):
            self.receiver.verify_prepared(self.prepared)
        self.probe.assert_not_called()

    def test_each_main_route_gate_fails_closed(self):
        for key in ROUTE_GATES:
            with self.subTest(gate=key):
                self.route_receipt[key] = False
                with self.assertRaisesRegex(Refusal, 'preflight_incomplete_before_stop'):
                    self.receiver.verify_prepared(self.prepared)
                self.route_receipt[key] = True

    def test_direct_guard_dispatcher_is_rejected(self):
        self.route_receipt['dispatcher_module'] = 'gpu.orch_r125_continual_guard'
        with self.assertRaisesRegex(Refusal, 'exact_Main_owned_route'):
            self.receiver.verify_prepared(self.prepared)

    def test_real_receiving_CPU_required_not_this_hook_receipt(self):
        document = read(self.cpu_path)
        document['scope'] = 'SYNTHETIC_HOOK_TESTS_ONLY'
        self.cpu_path.write_text(json.dumps(document))
        with self.assertRaisesRegex(Refusal, 'real_receiving_CPU_not_synthetic'):
            self.receiver.verify_prepared(self.prepared)

    def test_missing_wall_record_or_intent_rejected(self):
        original = deepcopy(self.receiver.consumed)
        for value in (None, {}, {'record': original['record']}, {'intent': original['intent']}):
            self.receiver.consumed = value
            with self.subTest(value=value), self.assertRaisesRegex(Refusal, 'historical_wall_record_and_intent'):
                self.receiver.verify_prepared(self.prepared)

    def test_wrong_wall_intent_rejected(self):
        self.receiver.consumed['intent']['record_sha256'] = '0' * 64
        with self.assertRaisesRegex(Refusal, 'durable_record_intent_pair'):
            self.receiver.verify_prepared(self.prepared)

    def test_original_wall_record_bytes_rechecked(self):
        path = Path(self.binding['journal_root']) / 'records/00000000000000000001.json'
        path.write_text('{}')
        with self.assertRaisesRegex(Refusal, 'original_historical_wall_bytes'):
            self.receiver.verify_prepared(self.prepared)

    def test_same_deadline_root_controls_and_only_anchor_changes(self):
        before = deepcopy(self.prepared)
        proof, result = self.prepare()
        verify_receiver_plan(self.binding, self.prepared, result, self.candidate)
        self.receiver.verify_receiver(result, self.candidate)
        self.assertEqual(self.prepared, before)
        plan = deepcopy(result['plan'])
        self.assertEqual(plan['hard_end_unix'], DEADLINE)
        self.assertNotIn('authorized_wall_extension', plan)
        self.assertEqual(plan['checkpoint_tail_recovery']['complete_index'], self.candidate['complete_index'])
        plan['checkpoint_tail_recovery'] = deepcopy(before['new_plan']['checkpoint_tail_recovery'])
        self.assertEqual(plan, before['new_plan'])
        self.assertTrue(proof['durable_files_and_directories'])
        self.dispatch.assert_not_called()
        self.process_run.assert_not_called()
        self.kill.assert_not_called()

    def test_plan_deadline_prompt_root_control_and_tail_policy_changes_rejected(self):
        for key, value in (('hard_end_unix', DEADLINE + 1), ('root', '/other'), ('system_prompt', 'changed'),
                ('learn_row_policy', 'changed'), ('think_act_learn', {'trial_id': 'frozen-pair'}),
                ('checkpoint_tail_recovery', {'persist_complete_anchors': False})):
            changed = deepcopy(self.prepared)
            changed['new_plan'][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(Refusal, 'source_relocation_consumed_wall_only'):
                self.receiver.verify_prepared(changed)

    def test_keeping_old_wall_authorization_rejected(self):
        self.prepared['new_plan']['authorized_wall_extension'] = self.prepared['old_plan']['authorized_wall_extension']
        with self.assertRaisesRegex(Refusal, 'source_relocation_consumed_wall_only'):
            self.receiver.verify_prepared(self.prepared)

    def test_source_tampering_or_extra_source_rejected(self):
        path = Path(self.staged['new_source']) / 'unexpected.py'
        path.write_text('unexpected')
        with self.assertRaisesRegex(Refusal, 'entire_immutable_python_source_closure'):
            self.receiver.verify_prepared(self.prepared)

    def test_startup_bytes_rechecked(self):
        Path(self.prepared['new_plan']['startup_context']['path']).write_text('changed')
        with self.assertRaisesRegex(Refusal, 'unchanged_startup_context_bytes'):
            self.receiver.verify_prepared(self.prepared)

    def test_wrong_checkpoint_directory_rejected_before_probe(self):
        self.receiver.verify_prepared(self.prepared)
        candidate = deepcopy(self.candidate)
        candidate['checkpoint']['adapter_path'] = '/other/checkpoint/adapter'
        with self.assertRaisesRegex(Refusal, 'exact_original_saved_checkpoint'):
            self.receiver.verify_checkpoint(candidate)
        self.probe.assert_not_called()

    def test_checkpoint_tamper_rejected_after_CPU_proof(self):
        self.receiver.verify_prepared(self.prepared)
        proof = self.receiver.verify_checkpoint(self.candidate)
        Path(self.candidate['checkpoint']['optimizer_rng_path']).write_bytes(b'changed')
        with self.assertRaisesRegex(Refusal, 'same_saved_checkpoint_files'):
            self.receiver.recheck_checkpoint(proof, self.candidate)

    def test_correction_ledger_tamper_rechecked_after_preparation(self):
        _, result = self.prepare()
        (Path(self.binding['journal_root']) / 'correction_ledger.json').write_text('{}')
        with self.assertRaisesRegex(Refusal, 'same_original_tail_sidecars'):
            self.receiver.verify_receiver(result, self.candidate)

    def test_false_tail_scan_or_prefix_replay_cannot_be_certified(self):
        self.receiver.verify_prepared(self.prepared)
        proof = self.receiver.verify_checkpoint(self.candidate)
        for key, value in (('head_sha256', '0' * 64), ('complete_index', 0), ('pending', 'REQUEST'),
                ('read_only', False), ('inbox_preserved', False), ('sidecars_verified', False),
                ('prefix_work', 'FULL_HISTORICAL_REPLAY'), ('writer_lock_acquired', True)):
            def changed_probe(mode, candidate, plan, selection=None):
                result = self.synthetic_probe(mode, candidate, plan, selection)
                result[key] = value
                return result
            self.probe.side_effect = changed_probe
            with self.subTest(key=key), self.assertRaisesRegex(Refusal, 'actual_readonly_tail_scan'):
                self.receiver.prepare_receiver(self.candidate, self.prepared, proof)

    def test_wrong_or_pending_complete_candidate_rejected(self):
        self.receiver.verify_prepared(self.prepared)
        proof = self.receiver.verify_checkpoint(self.candidate)
        candidate = deepcopy(self.candidate)
        candidate['resume_state']['state']['pending'] = 'REQUEST'
        with self.assertRaises(Refusal):
            self.receiver.prepare_receiver(candidate, self.prepared, proof)

    def test_wrong_or_stale_tail_anchor_rejected_by_shared_contract(self):
        _, result = self.prepare()
        result['plan']['checkpoint_tail_recovery']['complete_index'] = 0
        with self.assertRaises(Refusal):
            verify_receiver_plan(self.binding, self.prepared, result, self.candidate)

    def test_unrelated_saved_state_edit_in_wall_record_rejected(self):
        receipt = self.receiver.consumed
        saved = receipt['record']['document']['state']
        saved['state']['rows'][0]['source_sha256'] = digest('different-row')
        saved['sha256'] = digest(saved['state'])
        record = receipt['record']
        record['sha256'] = digest({key: value for key, value in record.items() if key != 'sha256'})
        receipt['intent']['record_sha256'] = record['sha256']
        root = Path(self.binding['journal_root']) / 'records'
        (root / '00000000000000000001.json').write_text(json.dumps(record))
        (root / '00000000000000000001.intent.json').write_text(json.dumps(receipt['intent']))
        with self.assertRaisesRegex(Refusal, 'exact_prior_state_no_other_changes'):
            self.prepare()

    def test_parent_ledger_change_refuses(self):
        path = next(iter(self.route_receipt['ledger_pins']))
        Path(path).write_text('{}')
        with self.assertRaisesRegex(Refusal, 'durable_route_ledger_pins'):
            self.receiver.verify_prepared(self.prepared)

    def test_preserves_original_guard_confinement_and_learned_physical_one(self):
        _, result = self.prepare()
        old, new = read(self.binding['guard_path']), read(result['guard_path'])
        for key in ('copy_raw', 'resume', 'hard_end_unix', 'next_reserved_unix', 'host_sha256', 'schema'):
            self.assertEqual(old[key], new[key])
        self.assertEqual(result['dispatcher_module'], CONFINEMENT)
        self.assertEqual(result['plan']['think_act_learn']['controls'], 'learned-C2')
        self.assertFalse(result['parent_rebind_allowed'])

    def test_artifact_tampering_refuses_before_handoff(self):
        _, result = self.prepare()
        path = Path(result['guard_path'])
        guard = read(path)
        guard['copy_raw'] = '/different'
        path.write_text(json.dumps(guard))
        with self.assertRaisesRegex(Refusal, 'immutable_receiving_artifacts'):
            self.receiver.verify_receiver(result, self.candidate)

    def test_token_must_prove_exact_exited_native(self):
        _, result = self.prepare()
        token = self.token(result)
        token['old_native_exited'] = False
        token['sha256'] = digest({key: value for key, value in token.items() if key != 'sha256'})
        with self.assertRaisesRegex(Refusal, 'exact_unexpired_exited_source_epoch_token'):
            self.receiver.dispatch_once(token)
        self.dispatch.assert_not_called()

    def test_once_only_claim_uses_inert_test_callback_and_never_native(self):
        _, result = self.prepare()
        token = self.token(result)
        with patch('time.time', return_value=DEADLINE - 600):
            self.receiver.dispatch_once(token)
            with self.assertRaises(FileExistsError):
                self.receiver.dispatch_once(token)
        self.assertEqual(self.dispatch.call_count, 1)
        self.kill.assert_not_called()
        self.process_popen.assert_not_called()
        self.process_run.assert_not_called()

    def test_unknown_callback_outcome_cannot_be_retried(self):
        _, result = self.prepare()
        self.dispatch.side_effect = RuntimeError('synthetic-uncertain-result')
        with patch('time.time', return_value=DEADLINE - 600):
            with self.assertRaisesRegex(RuntimeError, 'synthetic-uncertain-result'):
                self.receiver.dispatch_once(self.token(result))
            with self.assertRaises(FileExistsError):
                self.receiver.dispatch_once(self.token(result))
        self.assertEqual(self.dispatch.call_count, 1)

    def test_import_contains_no_signal_or_service_manager_calls(self):
        for filename in ('receiver.py', 'cpu_probe.py'):
            source = (OWN / filename).read_text()
            for forbidden in ('os.kill(', 'pidfd_send_signal(', 'systemd-run', 'systemctl', 'Popen(', 'LinuxOperations('):
                self.assertNotIn(forbidden, source)
            ast.parse(source)

    def test_immutable_write_refuses_overwrite(self):
        path = self.root / 'immutable.json'
        write_once(path, {'value': 1})
        write_once(path, {'value': 1})
        with self.assertRaisesRegex(Refusal, 'immutable_receiving_artifact'):
            write_once(path, {'value': 2})

    def test_identical_preparation_is_idempotent(self):
        _, first = self.prepare()
        _, second = self.prepare()
        self.assertEqual(first, second)


if __name__ == '__main__':
    unittest.main()
