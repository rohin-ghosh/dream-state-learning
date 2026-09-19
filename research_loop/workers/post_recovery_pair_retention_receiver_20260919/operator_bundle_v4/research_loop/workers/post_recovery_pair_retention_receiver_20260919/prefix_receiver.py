"""Explicitly approved pair prefix hooks; old receiver/default sources are untouched."""

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import time

from research_loop.workers.post_recovery_retention_boundary_20260918.boundary import (
    Refusal, digest, plan_metadata_binding, read, require, sha, verify_source_only_plans)
from research_loop.workers.post_recovery_pair_retention_receiver_20260919.prefix_authority import (
    document, load_authority, reference)
from research_loop.workers.post_recovery_pair_retention_receiver_20260919.receiver import (
    PairReceiver, parent_handoff_contract, preservation, sync_directory, write_once)
from research_loop.workers.post_recovery_pair_retention_receiver_20260919.reserved_preflight import (
    ReservedPairLinuxOperations, execution_digest)
from research_loop.workers.post_recovery_pair_retention_receiver_20260919.parent_dependency_bridge import ParentDependencyBridge


class PrefixPairReceiver(PairReceiver):
    def __init__(self, *arguments, prefix_authority, **keywords):
        super().__init__(*arguments, **keywords)
        self.prefix_authority = deepcopy(prefix_authority)

    def verify_prepared(self, prepared):
        super().verify_prepared(prepared)
        cpu = read(self.cpu_receipt_path)
        require(cpu.get('pair_prefix_authority') == self.prefix_authority, 'explicit_prefix_authority_in_pinned_CPU_receipt')
        load_authority(self.prefix_authority, prepared['new_plan'], prepared['new_source_pins'],
            life_binding_sha256=digest(self.binding), epoch_id=prepared['epoch_id'], config=read(self.binding['guard_path']))

    def _probe(self, mode, candidate, selection=None):
        if mode not in ('tail', 'prefix-admission'):
            return super()._probe(mode, candidate, selection)
        if self.probe_override is not None:
            return super()._probe(mode, candidate, selection)
        budget = self.reservation_budget
        request = dict(source=str(self.source), candidate=candidate, plan=self.prepared['new_plan'], selection=selection,
            source_pins=self.prepared['new_source_pins'], prefix_authority=self.prefix_authority,
            life_binding_sha256=digest(self.binding), epoch_id=self.prepared['epoch_id'])
        path = self.control / 'cpu_requests' / (digest(request) + '.prefix.json')
        write_once(path, request)
        timeout = self.probe_timeout_seconds if budget is None else budget.timeout(self.probe_timeout_seconds)
        try:
            result = subprocess.run([self.python, '-B', str(Path(__file__).with_name('cpu_probe_prefix.py')),
                mode, '--request', str(path)], cwd=self.source, env=self.environment(), capture_output=True,
                text=True, timeout=timeout, check=True, close_fds=True)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as error:
            write_once(path.with_name(path.stem + '.failure.' + str(time.time_ns()) + '.json'),
                dict(status='PREFIX_PROBE_REFUSED_NO_FALLBACK_OR_AUTOMATIC_RETRY', timeout_seconds=timeout,
                    error_type=type(error).__name__, stderr=str(getattr(error, 'stderr', ''))[-4096:], native_actions=[]))
            raise Refusal('prefix_CPU_probe_failed_no_replay_fallback_or_automatic_retry') from error
        if budget is not None:
            budget.check()
        scanned = json.loads(result.stdout)
        write_once(path.with_suffix('.result.json'), dict(result=scanned, stderr=result.stderr,
            source_pins=self.prepared['new_source_pins'], prefix_authority=self.prefix_authority))
        return scanned

    def prepare_receiver(self, candidate, prepared, proof):
        self.verify_prepared(prepared)
        plan = deepcopy(prepared['new_plan'])
        require('authorized_wall_extension' not in plan and 'checkpoint_tail_recovery' not in plan,
            'pair_sidecar_enrollment_no_new_plan_semantics')
        stamp = plan_metadata_binding(self.binding, candidate, prepared['old_plan'], plan)
        receipts = dict(consumed_wall_extension=dict(self.consumed, binding=stamp, durable=True))
        verify_source_only_plans(prepared['old_plan'], plan, binding=self.binding, candidate=candidate, receipts=receipts)
        authority, _ = load_authority(self.prefix_authority, plan, prepared['new_source_pins'])
        selection = dict(authority['selection_policy'], complete_index=candidate['complete_index'],
            complete_sha256=candidate['complete_sha256'])
        root = Path(self.binding['journal_root'])
        sidecars = ([dict(name='correction_ledger.json', kind='R197_CORRECTION_CYCLE', required=True)]
            if (root / 'correction_ledger.json').exists() else [])
        require(selection == dict(policy='R233_PINNED_COMPLETE_TAIL_V1', root=str(root),
            journal_id=self.binding['journal_id'], complete_index=candidate['complete_index'],
            complete_sha256=candidate['complete_sha256'], life_id=plan['think_act_learn']['trial_id'],
            max_tail_records=2048, max_tail_bytes=1024**3, sidecars=sidecars, persist_complete_anchors=False),
            'same_original_pair_selection_and_current_sidecars')
        require(not (self.control / 'RETENTION_HANDOFF.json').exists()
            and not (self.control / 'DISPATCH_CLAIM.json').exists(), 'no_receiving_writer_or_dispatch_already_armed')
        attempt = self.control / 'attempts' / str(time.time_ns())
        old_guard = read(self.binding['guard_path'])
        require(sha(old_guard['lease_path']) == old_guard['lease_sha256']
            and sha(old_guard['allocation_path']) == old_guard['allocation_sha256'], 'unchanged_original_admission_evidence')
        write_once(attempt / 'PLAN.json', plan)
        write_once(attempt / 'LEASE_WINDOW.json', read(old_guard['lease_path']))
        derived = self._probe('prefix-admission', candidate, dict(selection=selection,
            cpu_parent=reference(self.cpu_receipt_path), cpu_path=str(attempt / 'RECEIVING_CPU.json')))
        require(derived['cpu'] == reference(attempt / 'RECEIVING_CPU.json')
            and derived['admission_granted'] is False and derived['checkpoint_tail_validated'] is False,
            'only_bounded_clause_derivation_not_admission_or_state_proof')
        cpu = document(derived['cpu'])
        require(cpu['pair_prefix_cpu_parent'] == reference(self.cpu_receipt_path)
            and cpu['pair_prefix_selection'] == derived['prefix_binding']
            and {key: value for key, value in cpu.items() if key not in
                ('pair_prefix_cpu_parent', 'pair_prefix_selection', 'pair_prefix_admission')}
                == read(self.cpu_receipt_path), 'preserve_original_CPU_evidence_only_add_exact_derivation')
        allocation = read(old_guard['allocation_path'])
        allocation.update(plan_sha256=sha(attempt / 'PLAN.json'), declared_unix=time.time(),
            cpu_receipt_path=str(attempt / 'RECEIVING_CPU.json'), cpu_receipt_sha256=sha(attempt / 'RECEIVING_CPU.json'),
            cpu_tests_passed=True)
        write_once(attempt / 'ALLOCATION.json', allocation)
        guard = deepcopy(old_guard)
        guard.update(attempt_dir=str(attempt), plan_path=str(attempt / 'PLAN.json'), plan_sha256=sha(attempt / 'PLAN.json'),
            lease_path=str(attempt / 'LEASE_WINDOW.json'), lease_sha256=sha(attempt / 'LEASE_WINDOW.json'),
            allocation_path=str(attempt / 'ALLOCATION.json'), allocation_sha256=sha(attempt / 'ALLOCATION.json'),
            source_pins=prepared['new_source_pins'])
        write_once(attempt / 'GUARD.json', guard)
        guard_proof = self._probe('guard', candidate, dict(guard_path=str(attempt / 'GUARD.json')))
        require(guard_proof['validated'] is True and guard_proof['admission_bypassed'] is False
            and guard_proof['guard_sha256'] == sha(attempt / 'GUARD.json'), 'actual_receiving_guard_CPU_validation')
        scanned = self._probe('tail', candidate, dict(selection=selection,
            guard_path=str(attempt / 'GUARD.json'), prefix_binding=derived['prefix_binding']))
        prefix = scanned['prefix_proof']
        require(scanned['restored_state_sha256'] == candidate['resume_state']['sha256']
            and scanned['head_sha256'] == candidate['head_sha256']
            and scanned['complete_index'] == candidate['complete_index']
            and scanned['complete_sha256'] == candidate['complete_sha256']
            and scanned['prefix_work'] == 'EXTERNALLY_PINNED_PREHASH_PLUS_METADATA_AND_RAW_EXTENSION'
            and prefix['full_raw_extension_verified'] is True and prefix['full_raw_tail_verified'] is True
            and prefix['implicit_fallback'] is False and scanned['read_only'] is True
            and scanned['journal_writes'] == 0, 'actual_bound_prefix_and_full_new_tail_CPU_proof')
        binding = scanned['prefix_binding']
        context = prefix['consumer_context']
        require(context['mode'] == authority['namespace_policy']
            and context['admission'] == dict(derived['cpu'], field_path=['pair_prefix_admission'])
            and context['producer_environment']['boot_id'] == context['consumer_environment']['boot_id'],
            'CPU_scan_used_exact_original_admission_clause_and_same_boot')
        require(binding == derived['prefix_binding'] and binding['authority'] == self.prefix_authority
            and binding['selection_sha256'] == digest(selection)
            and binding['selection_guard'] == dict(path=prefix['guard_path'], sha256=prefix['guard_sha256'])
            and prefix['proof_path'] == authority['proof']['path']
            and prefix['proof_sha256'] == authority['proof']['sha256'], 'same_approved_proof_in_real_scan')
        require(not (self.control / 'RETENTION_HANDOFF.json').exists()
            and not (self.control / 'DISPATCH_CLAIM.json').exists(), 'no_receiving_writer_or_dispatch_already_armed')
        preserved = preservation(candidate, selection)
        snapshot = self.control / ('PRESERVATION.' + digest(preserved) + '.json')
        write_once(snapshot, preserved)
        temporary = self.control / ('PRESERVATION.link.' + str(time.time_ns()))
        os.link(snapshot, temporary)
        os.replace(temporary, self.control / 'PRESERVATION.json')
        sync_directory(self.control)
        parent = parent_handoff_contract(self.binding, prepared['epoch_id'])
        parent.update(receiving_guard_path=str(attempt / 'GUARD.json'), receiving_guard_sha256=sha(attempt / 'GUARD.json'),
            receiving_plan_sha256=sha(attempt / 'PLAN.json'), source_pins_sha256=digest(prepared['new_source_pins']),
            dependency_proof=self.verify_parent_dependencies(prepared['epoch_id']))
        write_once(attempt / 'PARENT_REBIND_REQUIRED.json', parent)
        receiver = dict(source_epoch=prepared['epoch_id'], plan=plan, plan_sha256=digest(plan),
            plan_metadata_receipts=receipts, resume_state_sha256=candidate['resume_state']['sha256'],
            checkpoint_sha256=digest(candidate['checkpoint']), same_journal_root=self.binding['journal_root'],
            rescans_original_inbox=True, no_model_load_before_writer_lock=True, deadline_unix=self.binding['hard_end_unix'],
            source_adoption_not_wall_extension=True, preservation_sha256=sha(self.control / 'PRESERVATION.json'),
            guard_path=str(attempt / 'GUARD.json'), candidate=candidate, checkpoint_tail_receipt=scanned,
            prefix_binding=binding, parent_handoff_path=str(attempt / 'PARENT_REBIND_REQUIRED.json'),
            parent_rebind_allowed=False, artifact_pins={str(path): sha(path) for path in attempt.iterdir() if path.is_file()})
        receiver['artifact_pins'][binding['selection_guard']['path']] = binding['selection_guard']['sha256']
        write_once(attempt / 'RECEIVER.json', receiver)
        return receiver

    def verify_receiver(self, receiver, frozen):
        super().verify_receiver(receiver, frozen)
        load_authority(self.prefix_authority, receiver['plan'], self.prepared['new_source_pins'],
            life_binding_sha256=digest(self.binding), epoch_id=receiver['source_epoch'], config=read(receiver['guard_path']))
        require(receiver['prefix_binding']['authority'] == self.prefix_authority,
            'same_prefix_authority_before_destructive_commit_and_dispatch')
        cpu = document(dict(path=read(receiver['guard_path'])['allocation_path'],
            sha256=read(receiver['guard_path'])['allocation_sha256']))
        cpu = document(dict(path=cpu['cpu_receipt_path'], sha256=cpu['cpu_receipt_sha256']))
        require(cpu['pair_prefix_authority'] == self.prefix_authority, 'same_authority_in_original_admission_chain')


class PrefixReservedOperations(ReservedPairLinuxOperations):
    def verify_static(self, prepared, policy):
        super().verify_static(prepared, policy)
        receipt = document(dict(path=policy['static_receipt_path'], sha256=policy['static_receipt_sha256']))
        require(receipt.get('pair_prefix_authority') == self.receiving.prefix_authority
            and receipt['checks'].get('actual_confined_prefix_route_CPU') is True,
            'explicit_prefix_authority_and_real_confined_route_in_strategy_approval')


def build_prefix_operations(binding, prepared, authority, staged, *, prefix_authority, cpu_receipt_path,
        consumed_wall_receipt, python_executable, control_root, parent_owner_config,
        approved_execution_sha256, reserved_preflight_policy, probe_timeout_seconds=120):
    expected = execution_digest(binding, prepared, authority, reserved_preflight_policy)
    require(approved_execution_sha256 == expected, 'explicit_same_reserved_strategy_approval')
    static = document(dict(path=reserved_preflight_policy['static_receipt_path'],
        sha256=reserved_preflight_policy['static_receipt_sha256']))
    require(static.get('pair_prefix_authority') == prefix_authority, 'prefix_authority_must_be_bound_into_execution_digest')
    owner = ParentDependencyBridge(**parent_owner_config)
    receiving = PrefixPairReceiver(binding, staged, prefix_authority=prefix_authority, cpu_receipt_path=cpu_receipt_path,
        consumed_wall_receipt=consumed_wall_receipt, python_executable=python_executable,
        parent_dependency_receipt_path=owner.path, parent_owner=owner, probe_timeout_seconds=probe_timeout_seconds)
    operations = PrefixReservedOperations(binding, receiving, policy=reserved_preflight_policy,
        approved_execution_sha256=expected, control_root=control_root)
    return receiving, operations
