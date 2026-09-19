"""Prospective same-lineage route clocks and completed-FINAL custody."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path

from gpu import orch_r119_lease_clock as clock


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def reference(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def checked(pointer):
    require(reference(pointer['path']) == pointer, 'immutable_route_reference')
    return json.loads(Path(pointer['path']).read_bytes())


def current():
    backend = Path(__file__).with_name('orch_r118_parallel_consolidation.py')
    result = clock.from_environment(os.environ, backend)
    require(result is not None, 'explicit_common_lease_clock_required')
    return result


def updated_bounds(original, limits):
    result = deepcopy(original)
    result.update(hard_end_unix=limits['hard_end_unix'], lease_end_unix=limits['lease_end_unix'])
    return result


def same_life(plan, original):
    limits = current()
    require(plan['bounds'] == updated_bounds(original['bounds'], limits),
            'clock_only_no_call_cycle_quota_reset')
    require(plan['shared_learner'] == original['shared_learner'], 'unchanged_shared_lineage')
    branch = plan['shared_learner']['branch']
    require(branch in ('F1', 'A1'), 'route_branch_only')
    require(plan['parent_wait_seconds'] == (600 if branch == 'F1' else 120),
            'explicit_general_transport_era_not_refusal_workaround')
    require(plan['lease_continuation']['policy'] == dict(
        path=os.environ['ORCH_R119_LEASE_CLOCK'], sha256=os.environ['ORCH_R119_LEASE_CLOCK_SHA256']),
        'same_manifest_clock')
    return True


def preserve_final(plan):
    custody = plan['lease_continuation']['completed_final']
    terminal = checked(custody['terminal'])
    require(terminal['success'] is True and terminal['returncode'] == 0,
            'actual_successful_original_FINAL_exit')
    checked(custody['complete'])
    require(reference(custody['selection']['path']) == custody['selection'],
            'report_selection_unchanged')
    return dict(status='PRESERVED_COMPLETED_FINAL_NO_REPLAY', custody=custody)


def supervision(root, plan, actor, guardian, binding, final_binding):
    def minimal(identity):
        return dict(pid=identity['pid'], boot_id=identity['boot_id'], start_ticks=int(identity['start_ticks']))
    preserve_final(plan)
    from gpu import orch_r120_route_final_custody as custody
    document = checked(final_binding['evidence'])
    require(document['role'] == custody.ROLE and document['never_dispatch'] is True
            and document['identity'] == final_binding['identity'] and custody.alive(final_binding['identity']),
            'actual_completed_FINAL_custodian_not_evaluator')
    return dict(native_identity=minimal(actor), guard_identity=minimal(guardian),
        guard_binding=binding, final_identity_bindings=[final_binding],
        completed_final_bindings=[plan['lease_continuation']['completed_final']],
        owner_verified_safe_for_parallel=True, lease_policy=plan['lease_continuation']['policy'])
