"""Scoped r110 three-observation argv reconciliation; full GPU checks remain."""

from copy import deepcopy
from types import FunctionType

from gpu import orch_r110_admission as original
from gpu import orch_r111_route_admission as one_mib


def reconcile(report, observations):
    eligible = {}
    for process_id, samples in observations.items():
        if len(samples) < 3:
            continue
        if any(not isinstance(sample.get('executable_identity'), (list, tuple))
                or len(sample['executable_identity']) != 2
                or any(type(value) is not int or value < 0 for value in sample['executable_identity'])
                for sample in samples):
            continue
        eligible[process_id] = samples
    result = one_mib.reconcile(report, eligible)
    result['argv_original_report'] = deepcopy(report)
    result['argv_reconciliation_contract'] = 'R110_AT_LEAST_THREE_STABLE_KERNEL_EXE_NO_TARGET_FD_CVD'
    return result


def scan(index, service_path):
    namespace = dict(original.scan.__globals__, reconcile=reconcile)
    observed_scan = FunctionType(original.scan.__code__, namespace, 'scan', original.scan.__defaults__)
    return observed_scan(index, service_path)
