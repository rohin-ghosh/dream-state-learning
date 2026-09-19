"""Explicit C2 reservation orchestration using the unchanged original guardian."""

from copy import deepcopy
import json
import math

from research_loop.workers.post_recovery_retention_boundary_20260918.boundary import (
    ObservationRace, Refusal, digest, require, same_boundary)
from research_loop.workers.post_recovery_retention_boundary_20260918.coordinator import (
    validate_prepared, verify_receiver_plan)


def execution_digest(configuration):
    return digest(dict(strategy='C2_OWNER_FENCED_PREFIX_RESERVED_V1', configuration=configuration))


def coordinate(configuration, operations, *, max_observations=200):
    binding, prepared, authority = deepcopy((configuration['binding'], configuration['prepared'], configuration['authority']))
    validate_prepared(binding, prepared, authority)
    policy = configuration['prefix_policy']
    require(policy['schema'] == 'C2_RESERVED_PREFLIGHT_POLICY_V1'
        and type(policy['stop_seconds']) in (int, float) and math.isfinite(policy['stop_seconds'])
        and type(policy['commit_margin_seconds']) in (int, float) and math.isfinite(policy['commit_margin_seconds'])
        and 0 < policy['stop_seconds'] <= 30 and 1 <= policy['commit_margin_seconds'] < policy['stop_seconds'],
        'unchanged_C2_30_second_reservation')
    require(type(max_observations) is int and 0 < max_observations <= 10000, 'bounded_readonly_observations')
    operations.require_execution_approval(execution_digest(configuration))
    operations.verify_static(prepared)
    seconds = policy['stop_seconds']
    with operations.exclusive_life_lock(binding):
        handle = operations.open_exact_handle(binding)
        try:
            for attempt in range(max_observations):
                operations.require_exact_identity(handle, binding)
                require(operations.wall_time() < binding['hard_end_unix'] - 2 * seconds - 30, 'original_wall_margin')
                try:
                    candidate = operations.observe(binding)
                except (ObservationRace, FileNotFoundError, json.JSONDecodeError):
                    operations.wait()
                    continue
                if candidate is None:
                    operations.wait()
                    continue
                require(operations.dependents_clear(handle), 'actual_owner_fence_before_native_reservation')
                operations.begin_attempt(candidate)
                deadline = operations.monotonic() + seconds - policy['commit_margin_seconds']
                with operations.bounded_path(deadline) as budget:
                    with operations.reserve(handle, seconds) as reservation:
                        budget.call(operations.require_exact_identity, handle, binding, stopped=True)
                        frozen = same_boundary(candidate, budget.call(operations.observe, binding))
                        budget.call(operations.verify_prepared, prepared)
                        require(budget.call(operations.dependents_clear, handle), 'owner_still_fenced')
                        proof = budget.call(operations.verify_checkpoint, frozen)
                        require(proof['complete_sha256'] == frozen['complete_sha256']
                            and proof['checkpoint_sha256'] == digest(frozen['checkpoint'])
                            and all(proof.get(key) is True for key in ('adapter_verified', 'optimizer_verified',
                                'python_cpu_cuda_rng_verified', 'working_state_verified', 'durable_files_and_directories')),
                            'actual_saved_payload_verified_before_irreversible_commit')
                        receiver = budget.call(operations.prepare_receiver, frozen, prepared, proof)
                        verify_receiver_plan(binding, prepared, receiver, frozen)
                        require(receiver['source_epoch'] == prepared['epoch_id']
                            and receiver['same_journal_root'] == binding['journal_root']
                            and receiver['deadline_unix'] == binding['hard_end_unix']
                            and receiver['rescans_original_inbox'] is True
                            and receiver['no_model_load_before_writer_lock'] is True
                            and receiver['source_adoption_not_wall_extension'] is True, 'exact_original_C2_receiver')
                        budget.call(operations.recheck_checkpoint, proof, frozen)
                        budget.call(operations.verify_receiver, receiver, frozen)
                        final = same_boundary(frozen, budget.call(operations.observe, binding, durable=True))
                        verify_receiver_plan(binding, prepared, receiver, final)
                        require(final['durable'] is True, 'durable_COMPLETE_LEARN_INBOX')
                        require(budget.call(operations.dependents_clear, handle), 'effective_owner_fence_at_commit')
                        budget.call(operations.require_exact_identity, handle, binding, stopped=True)
                        budget.call(operations.record, 'C2_RETENTION_HANDOFF_INTENT', dict(binding=binding,
                            complete=final, receiver=receiver, execution_sha256=execution_digest(configuration)))
                        budget.check()
                        require(reservation.commit_and_wait_exit(), 'guardian_expired_no_automatic_retry')
                    budget.call(operations.require_handle_exited, handle)
                    with operations.exclusive_writer_check(binding):
                        exited = same_boundary(final, budget.call(operations.observe, binding, durable=True))
                        budget.call(operations.verify_receiver, receiver, exited)
                        verify_receiver_plan(binding, prepared, receiver, exited)
                        token = dict(schema='RETENTION_HANDOFF_TOKEN_V1', epoch_id=prepared['epoch_id'],
                            life_binding_sha256=digest(binding), prepared_sha256=digest(prepared), authority_sha256=digest(authority),
                            old_pid=binding['pid'], old_start_ticks=binding['start_ticks'], old_native_exited=True,
                            exact_complete=exited, receiver=receiver, new_source_pins=prepared['new_source_pins'],
                            deadline_unix=binding['hard_end_unix'], no_cold_start=True, no_unresolved_work_replayed=True,
                            epoch_record_required_before_first_THINK=True)
                        token['sha256'] = digest(token)
                        budget.call(operations.record, 'C2_RETENTION_HANDOFF_READY', token)
                    require(operations.wall_time() < binding['hard_end_unix'], 'same_wall_before_dispatch')
                    budget.call(operations.dispatch_once, token)
                    return token
            raise Refusal('bounded_readonly_observation_exhausted_no_native_action')
        finally:
            operations.close_handle(handle)
