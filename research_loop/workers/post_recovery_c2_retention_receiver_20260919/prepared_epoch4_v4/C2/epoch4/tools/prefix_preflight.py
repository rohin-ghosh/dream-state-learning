"""Offline C2 prefix plumbing; no process-control implementation or implicit authority."""

from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import time


def require(condition, reason):
    if not condition:
        raise ValueError('C2_prefix_preflight_' + reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


class ReservationBudget:
    def __init__(self, deadline, *, clock=None):
        require(type(deadline) in (int, float) and math.isfinite(deadline), 'finite_monotonic_deadline')
        self.deadline = deadline
        self.clock = clock or time.monotonic

    def timeout(self, maximum):
        remaining = self.deadline - self.clock()
        require(remaining > 0, 'reserved_budget_expired_no_retry_or_fallback')
        return min(maximum, remaining)

    def check(self):
        self.timeout(float('inf'))

    def call(self, function, *arguments, **keywords):
        self.check()
        result = function(*arguments, **keywords)
        self.check()
        return result


def validate_policy(policy):
    require(type(policy) is dict and set(policy) == {'schema', 'stop_seconds', 'commit_margin_seconds',
        'static_receipt_path', 'static_receipt_sha256'}, 'exact_policy')
    require(policy['schema'] == 'C2_RESERVED_PREFLIGHT_POLICY_V1', 'C2_policy_not_pair_frozen')
    seconds, margin = policy['stop_seconds'], policy['commit_margin_seconds']
    require(type(seconds) in (int, float) and math.isfinite(seconds) and 0 < seconds <= 30
        and type(margin) in (int, float) and math.isfinite(margin) and 1 <= margin < seconds,
        'same_30_second_maximum_and_commit_margin')


def verify_static(policy, binding, prepared, api, approved):
    validate_policy(policy)
    receipt = api.document(dict(path=policy['static_receipt_path'], sha256=policy['static_receipt_sha256']))
    require(receipt['schema'] == 'C2_PREFIX_RESERVED_READINESS_V1'
        and receipt['life_binding_sha256'] == digest(binding)
        and receipt['prepared_sha256'] == digest(prepared)
        and receipt['source_pins_sha256'] == digest(prepared['new_source_pins'])
        and receipt['prefix_authority'] == approved
        and receipt['deadline_unix'] == 1789927200
        and receipt['epoch_id'] == prepared['epoch_id'], 'source_life_epoch_authority_bound_readiness')
    for name in ('actual_C2_saved_payload_CPU', 'actual_C2_prefix_and_new_tail_CPU',
            'actual_original_r188_consumer_context', 'producer_consumer_filesystem_objects_verified',
            'all_reserved_work_cost_bounded', 'source_control_tests_passed',
            'explicit_trust_review_ratification', 'parent_bridge_guard_work_cost_bounded'):
        require(receipt['checks'].get(name) is True, 'missing_' + name)
    bound = receipt['reserved_total_seconds_upper_bound']
    require(type(bound) in (int, float) and math.isfinite(bound) and 0 < bound
        < policy['stop_seconds'] - policy['commit_margin_seconds'], 'entire_reserved_work_fits_budget')
    require(receipt['evidence'] and all(api.pinned(reference) for reference in receipt['evidence']),
        'exact_external_review_and_measurement_bytes')
    authority, proof = api.load_authority(approved, prepared['new_plan'], prepared['new_source_pins'],
        life_binding_sha256=digest(binding), epoch_id=prepared['epoch_id'])
    context = receipt['consumer_context']
    require(context['admission_module'] == 'gpu.r188_node5_confinement'
        and context['original_guard_sha256'] == binding['guard_sha256']
        and context['producer_environment'] == proof['binding']['environment']
        and context['mode'] == authority['consumer_context_mode']
        and context['consumer_environment']['boot_id'] == proof['binding']['environment']['boot_id']
        and context['source_pins_sha256'] == digest(prepared['new_source_pins'])
        and context['filesystem_evidence'] and all(api.pinned(item) for item in context['filesystem_evidence']),
        'original_admission_bound_context_no_namespace_allowlist')
    if context['mode'] == 'SAME_MOUNT_NAMESPACE':
        require(context['consumer_environment'] == proof['binding']['environment'], 'strict_default_same_namespace')
    else:
        require(context['mode'] == 'SAME_FILESYSTEM_OBJECTS_ACROSS_ADMITTED_NAMESPACE'
            and receipt['checks'].get('bounded_context_clause_delegation_reviewed') is True,
            'explicit_Main_bound_mode_and_delegation')
    require(not any('allowlist' in key or 'allowed_namespace' in key for key in context),
        'no_namespace_allowlist')
    return receipt


class PrefixPreflight:
    def __init__(self, api, approved, policy):
        self.api = api
        self.approved = deepcopy(approved)
        self.policy = deepcopy(policy)
        self.reservation_budget = None
        self.static = None
        self.selection_binding = None

    def verify_before_reservation(self, binding, prepared):
        require(self.reservation_budget is None, 'static_proof_must_precede_stop')
        self.static = verify_static(self.policy, binding, prepared, self.api, self.approved)
        return deepcopy(self.static)

    @contextmanager
    def budget(self, deadline, *, clock=None):
        require(self.static is not None and self.reservation_budget is None, 'pre_stop_proof_required_no_nested_budget')
        budget = ReservationBudget(deadline, clock=clock)
        require(budget.timeout(float('inf')) <= self.policy['stop_seconds'] - self.policy['commit_margin_seconds'],
            'cannot_extend_reserved_budget')
        self.reservation_budget = budget
        try:
            yield budget
        finally:
            self.reservation_budget = None

    def derive_selection(self, prepared, plan, selection, write_once, directory):
        require(self.static is not None and self.reservation_budget is not None,
            'bounded_verified_reservation_required')
        budget = self.reservation_budget
        guard = budget.call(self.api.selection_guard, self.approved, plan, prepared['new_source_pins'], selection)
        path = Path(directory) / ('PREFIX_SELECTION_' + digest(guard) + '.json')
        budget.call(write_once, path, guard)
        binding = dict(schema='C2_PREFIX_SELECTION_BINDING_V1', authority=deepcopy(self.approved),
            selection_guard=self.api.reference(path), selection_sha256=digest(selection))
        budget.call(self.api.verify_selection_binding, binding, self.approved,
            plan, prepared['new_source_pins'], selection)
        self.selection_binding = binding
        return deepcopy(binding)

    def reader_argument(self, plan, pins, selection):
        require(self.selection_binding is not None and self.reservation_budget is not None,
            'no_implicit_unbounded_reader')
        return self.reservation_budget.call(self.api.verify_selection_binding,
            self.selection_binding, self.approved, plan, pins, selection)

    def attach_cpu_authority(self, cpu):
        require(cpu['passed'] is True, 'passed_source_CPU_required')
        require(cpu.get('c2_prefix_authority') == self.approved, 'authority_must_already_be_Main_pinned_in_CPU')
        return deepcopy(cpu)

    def receiving_cpu(self, cpu, plan, pins, selection):
        require(self.selection_binding is not None and self.reservation_budget is not None,
            'bounded_selection_before_receiving_CPU_copy')
        return self.reservation_budget.call(self.api.receiving_cpu, cpu, self.approved,
            plan, pins, selection, self.selection_binding)

    def cpu_context(self, prepared, plan, guard_path):
        require(self.selection_binding is not None and self.reservation_budget is not None, 'bounded_CPU_context')
        guard = self.api.reference(guard_path)
        return dict(life_binding_sha256=self.static['life_binding_sha256'], epoch_id=prepared['epoch_id'],
            new_source_pins=prepared['new_source_pins'], deadline_unix=plan['hard_end_unix'],
            receiver=dict(prefix_binding=deepcopy(self.selection_binding), guard_path=guard['path'],
                artifact_pins={guard['path']: guard['sha256']}))
