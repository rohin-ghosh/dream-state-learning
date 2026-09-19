"""Construct reviewed pair integration objects without running the coordinator."""

from research_loop.workers.post_recovery_retention_boundary_20260918.boundary import digest, require
from research_loop.workers.post_recovery_retention_boundary_20260918.coordinator import validate_prepared
from research_loop.workers.post_recovery_pair_retention_receiver_20260919.parent_dependency_bridge import ParentDependencyBridge
from research_loop.workers.post_recovery_pair_retention_receiver_20260919.pair_operations import PairLinuxOperations
from research_loop.workers.post_recovery_pair_retention_receiver_20260919.receiver import PairReceiver
from research_loop.workers.post_recovery_pair_retention_receiver_20260919.reserved_preflight import (
    ReservedPairLinuxOperations, execution_digest)


def build_operations(binding, prepared, authority, staged, *, cpu_receipt_path, consumed_wall_receipt,
        python_executable, control_root, parent_owner_config, approved_execution_sha256,
        probe_timeout_seconds=120, reserved_preflight_policy=None):
    validate_prepared(binding, prepared, authority)
    expected = digest(dict(binding=binding, prepared=prepared, authority=authority))
    if reserved_preflight_policy is not None:
        expected = execution_digest(binding, prepared, authority, reserved_preflight_policy)
    require(approved_execution_sha256 == expected, 'main_explicit_exact_execution_approval_required')
    owner = ParentDependencyBridge(**parent_owner_config)
    receiving = PairReceiver(binding, staged, cpu_receipt_path=cpu_receipt_path,
        consumed_wall_receipt=consumed_wall_receipt, python_executable=python_executable,
        parent_dependency_receipt_path=owner.path, parent_owner=owner,
        probe_timeout_seconds=probe_timeout_seconds)
    if reserved_preflight_policy is None:
        operations = PairLinuxOperations(binding, receiving.hooks(), prepared=prepared,
            approved_execution_sha256=expected, control_root=control_root)
    else:
        operations = ReservedPairLinuxOperations(binding, receiving, policy=reserved_preflight_policy,
            approved_execution_sha256=expected, control_root=control_root)
    return receiving, operations
