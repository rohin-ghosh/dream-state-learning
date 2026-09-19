"""Opt-in bounded reserved preflight; no CLI and no implicit activation."""

from contextlib import contextmanager
from copy import deepcopy
import json
import hashlib
import math
from pathlib import Path
import re
import time

from research_loop.workers.post_recovery_retention_boundary_20260918.boundary import (
    ObservationRace, Refusal, digest, file_bytes, require, same_boundary, sha)
from research_loop.workers.post_recovery_retention_boundary_20260918.coordinator import (
    validate_prepared, verify_receiver_plan)
from research_loop.workers.post_recovery_retention_boundary_20260918.operations import LinuxOperations
from research_loop.workers.post_recovery_pair_retention_receiver_20260919.receiver import sync_directory, write_once


class BudgetExpired(Refusal):
    pass


class EarlyBoundaryRace(ObservationRace):
    pass


class ReservationBudget:
    def __init__(self, deadline, *, clock=None):
        self.deadline = deadline
        self.clock = clock or time.monotonic

    def timeout(self, maximum):
        remaining = self.deadline - self.clock()
        if remaining <= 0:
            raise BudgetExpired('reserved_preflight_budget_expired_review_required_no_retry')
        return min(maximum, remaining)

    def check(self):
        self.timeout(float('inf'))

    def call(self, function, *arguments, **keywords):
        self.check()
        result = function(*arguments, **keywords)
        self.check()
        return result


def validate_policy(policy):
    require(set(policy) == {'schema', 'stop_seconds', 'commit_margin_seconds',
        'static_receipt_path', 'static_receipt_sha256'}, 'exact_reserved_preflight_policy')
    require(policy['schema'] == 'PAIR_RESERVED_PREFLIGHT_POLICY_V1', 'explicit_reserved_preflight_policy')
    seconds, margin = policy['stop_seconds'], policy['commit_margin_seconds']
    require(type(seconds) in (int, float) and math.isfinite(seconds) and 0 < seconds <= 30
        and type(margin) in (int, float) and math.isfinite(margin) and 1 <= margin < seconds,
        'unchanged_30_second_cap_and_commit_margin')
    path = Path(policy['static_receipt_path'])
    require(path.is_absolute() and '..' not in path.parts
        and re.fullmatch(r'[a-f0-9]{64}', policy['static_receipt_sha256']), 'pinned_static_preflight_receipt')


def execution_digest(binding, prepared, authority, policy):
    validate_policy(policy)
    return digest(dict(binding=binding, prepared=prepared, authority=authority,
        strategy='PAIR_RESERVED_PREFLIGHT_V1', reserved_preflight_policy=policy))


def verify_static_receipt(binding, prepared, policy):
    validate_policy(policy)
    raw = file_bytes(policy['static_receipt_path'])
    require(hashlib.sha256(raw).hexdigest() == policy['static_receipt_sha256'], 'unchanged_static_preflight_receipt')
    receipt = json.loads(raw)
    require(receipt['schema'] == 'PAIR_RESERVED_PREFLIGHT_READINESS_V1'
        and receipt['life_binding_sha256'] == digest(binding)
        and receipt['prepared_sha256'] == digest(prepared)
        and receipt['source_pins_sha256'] == digest(prepared['new_source_pins'])
        and receipt['epoch_id'] == prepared['epoch_id']
        and receipt['deadline_unix'] == binding['hard_end_unix']
        and receipt['physical'] == prepared['new_plan']['physical'], 'exact_static_family_source_control_binding')
    checks = ('actual_saved_payload_CPU', 'actual_checkpoint_tail_CPU', 'exact_source_control_tests',
        'original_confinement_admission_available', 'owner_transport_and_guard_cost_bounded')
    require(all(receipt['checks'].get(name) is True for name in checks), 'all_static_readiness_checks_required')
    cost = receipt['reserved_total_seconds_upper_bound']
    require(type(cost) in (int, float) and math.isfinite(cost) and 0 < cost
        < policy['stop_seconds'] - policy['commit_margin_seconds'], 'all_reserved_costs_fit_bound_not_reader_cost_alone')
    require(receipt['evidence_pins'] and all(sha(path) == expected
        for path, expected in receipt['evidence_pins'].items()), 'original_static_evidence_bytes_required')
    return receipt


class ReservedPairLinuxOperations(LinuxOperations):
    def __init__(self, binding, receiving, *, policy, **arguments):
        super().__init__(binding, receiving.hooks(), **arguments)
        self.receiving = receiving
        self.policy = deepcopy(policy)
        self.review_gate = self.control_root / 'RESERVED_PREFLIGHT_REVIEW_REQUIRED.json'
        self.attempt_sha256 = None

    def verify_static(self, prepared, policy):
        require(policy == self.policy and not self.review_gate.exists(), 'no_blind_reserved_attempt_retry')
        verify_static_receipt(self.binding, prepared, policy)
        self.verify_prepared(prepared)

    def verify_candidate_family(self, candidate):
        self.receiving.verify_candidate_family(candidate)

    def begin_reserved_attempt(self, candidate):
        require(not self.review_gate.exists(), 'prior_reserved_attempt_requires_main_reconciliation')
        write_once(self.review_gate, dict(schema='PAIR_RESERVED_ATTEMPT_REVIEW_GATE_V1',
            life_binding_sha256=digest(self.binding), candidate_sha256=digest(candidate),
            execution_sha256=self.approved_execution_sha256, started_unix=time.time(),
            automatic_retry_allowed=False))
        self.attempt_sha256 = sha(self.review_gate)

    def finish_early_race(self):
        require(self.attempt_sha256 is not None and sha(self.review_gate) == self.attempt_sha256,
            'only_own_noncommitted_early_race_gate_may_clear')
        self.review_gate.unlink()
        sync_directory(self.review_gate.parent)
        self.attempt_sha256 = None

    @contextmanager
    def preflight_budget(self, budget):
        owner = self.receiving.parent_owner
        require(self.receiving.reservation_budget is None and owner.reservation_budget is None,
            'no_nested_reserved_preflight')
        self.receiving.reservation_budget = owner.reservation_budget = budget
        try:
            yield
        finally:
            self.receiving.reservation_budget = owner.reservation_budget = None

    @staticmethod
    def monotonic():
        return time.monotonic()


def _initial_boundary(candidate, current):
    if current is None:
        raise EarlyBoundaryRace('COMPLETE_window_lost_before_reservation')
    require(current['journal_id'] == candidate['journal_id']
        and current['journal_identity'] == candidate['journal_identity'], 'same_reserved_journal_identity')
    if current['complete_index'] > candidate['complete_index']:
        raise EarlyBoundaryRace('COMPLETE_advanced_before_reservation')
    return same_boundary(candidate, current)


def coordinate_reserved(binding, prepared, authority, operations, *, policy, max_attempts=200):
    """Main must explicitly review this strategy's distinct approval digest."""
    binding, prepared, authority, policy = deepcopy((binding, prepared, authority, policy))
    validate_prepared(binding, prepared, authority)
    validate_policy(policy)
    require(type(max_attempts) is int and 0 < max_attempts <= 10000, 'bounded_observation_attempts')
    operations.require_execution_approval(execution_digest(binding, prepared, authority, policy))
    seconds = policy['stop_seconds']
    attempted = set()
    with operations.exclusive_life_lock(binding):
        handle = operations.open_exact_handle(binding)
        try:
            operations.verify_static(prepared, policy)
            for attempt in range(max_attempts):
                operations.require_exact_identity(handle, binding)
                require(operations.wall_time() < binding['hard_end_unix'] - 2 * seconds - 30,
                    'insufficient_unchanged_deadline_margin')
                try:
                    candidate = operations.observe(binding)
                except (ObservationRace, FileNotFoundError, json.JSONDecodeError):
                    operations.wait()
                    continue
                if candidate is None or not operations.dependents_clear(handle):
                    operations.wait()
                    continue
                key = (candidate['complete_index'], candidate['complete_sha256'])
                if key in attempted:
                    operations.wait()
                    continue
                operations.verify_candidate_family(candidate)
                operations.begin_reserved_attempt(candidate)
                attempted.add(key)
                budget = ReservationBudget(operations.monotonic() + seconds - policy['commit_margin_seconds'],
                    clock=operations.monotonic)
                raced = False
                with operations.reserve(handle, seconds) as reservation:
                    with operations.preflight_budget(budget):
                        try:
                            budget.call(operations.require_exact_identity, handle, binding, stopped=True)
                            frozen = budget.call(_initial_boundary, candidate, budget.call(operations.observe, binding))
                        except (ObservationRace, FileNotFoundError, json.JSONDecodeError) as error:
                            operations.record('REOBSERVE_SAME_NATIVE', dict(attempt=attempt, reason=str(error),
                                old_pid=binding['pid'], old_start_ticks=binding['start_ticks']))
                            raced = True
                        if not raced:
                            require(budget.call(operations.dependents_clear, handle), 'no_active_readout_or_child_at_handoff')
                            budget.call(operations.verify_prepared, prepared)
                            proof = budget.call(operations.verify_checkpoint, frozen)
                            require(proof['complete_sha256'] == frozen['complete_sha256']
                                and proof['checkpoint_sha256'] == digest(frozen['checkpoint'])
                                and all(proof.get(name) is True for name in ('adapter_verified', 'optimizer_verified',
                                    'python_cpu_cuda_rng_verified', 'working_state_verified', 'durable_files_and_directories')),
                                'full_actual_saved_state_proof_before_any_destructive_commit')
                            receiver = budget.call(operations.prepare_receiver, frozen, prepared, proof)
                            verify_receiver_plan(binding, prepared, receiver, frozen)
                            require(receiver['source_epoch'] == prepared['epoch_id']
                                and receiver['resume_state_sha256'] == frozen['resume_state']['sha256']
                                and receiver['checkpoint_sha256'] == digest(frozen['checkpoint'])
                                and receiver['same_journal_root'] == binding['journal_root']
                                and receiver['rescans_original_inbox'] is True
                                and receiver['no_model_load_before_writer_lock'] is True
                                and receiver['deadline_unix'] == binding['hard_end_unix']
                                and receiver['source_adoption_not_wall_extension'] is True, 'exact_reserved_receiver')
                            budget.call(operations.verify_prepared, prepared)
                            require(budget.call(operations.dependents_clear, handle), 'dependents_still_clear_before_commit')
                            budget.call(operations.recheck_checkpoint, proof, frozen)
                            budget.call(operations.verify_receiver, receiver, frozen)
                            final = same_boundary(frozen, budget.call(operations.observe, binding, durable=True))
                            verify_receiver_plan(binding, prepared, receiver, final)
                            require(final['durable'] is True, 'durable_COMPLETE_LEARN_and_all_INBOX_before_commit')
                            budget.call(operations.require_exact_identity, handle, binding, stopped=True)
                            require(operations.wall_time() < binding['hard_end_unix'] - seconds - 30,
                                'unchanged_deadline_margin_before_commit')
                            budget.call(operations.record, 'RETENTION_HANDOFF_INTENT', dict(epoch_id=prepared['epoch_id'],
                                binding=binding, prepared_sha256=digest(prepared), authority_sha256=digest(authority),
                                complete=final, receiver=receiver, strategy='PAIR_RESERVED_PREFLIGHT_V1',
                                same_weights_optimizer_RNG_targets_and_deadline=True))
                            budget.check()
                            if not reservation.commit_and_wait_exit():
                                raise BudgetExpired('guardian_expired_resumed_same_handle_review_required_no_retry')
                    if not raced:
                        operations.require_handle_exited(handle)
                        with operations.exclusive_writer_check(binding):
                            exited = same_boundary(final, operations.observe(binding, durable=True))
                            operations.verify_receiver(receiver, exited)
                            verify_receiver_plan(binding, prepared, receiver, exited)
                            require(operations.wall_time() < binding['hard_end_unix'], 'same_deadline_before_dispatch')
                            token = dict(schema='RETENTION_HANDOFF_TOKEN_V1', epoch_id=prepared['epoch_id'],
                                life_binding_sha256=digest(binding), prepared_sha256=digest(prepared),
                                authority_sha256=digest(authority), old_pid=binding['pid'],
                                old_start_ticks=binding['start_ticks'], old_native_exited=True,
                                exact_complete=exited, receiver=receiver, new_source_pins=prepared['new_source_pins'],
                                deadline_unix=binding['hard_end_unix'], no_cold_start=True,
                                no_unresolved_work_replayed=True, epoch_record_required_before_first_THINK=True)
                            token['sha256'] = digest(token)
                            operations.record('RETENTION_HANDOFF_READY', token)
                        require(operations.wall_time() < binding['hard_end_unix'], 'same_deadline_before_dispatch')
                        operations.dispatch_once(token)
                        return token
                operations.require_exact_identity(handle, binding)
                operations.finish_early_race()
                operations.wait()
            raise Refusal('bounded_observation_expired_same_native_left_running')
        finally:
            operations.close_handle(handle)
