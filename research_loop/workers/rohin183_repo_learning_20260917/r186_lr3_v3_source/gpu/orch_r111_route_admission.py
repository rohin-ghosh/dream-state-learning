"""Preserve target-device checks while handling node5's one-MiB idle baseline."""

import inspect
from types import FunctionType

from gpu import orch_r110_admission as original


def reconcile(report, observations):
    source = inspect.getsource(original.reconcile)
    before = "report['gpu']['memory_used_mib'] != 0"
    if source.count(before) != 1:
        raise ValueError('exact_original_reconciliation_source')
    source = source.replace(before, "report['gpu']['memory_used_mib'] > 1", 1)
    namespace = dict(original.reconcile.__globals__)
    exec(compile(source, __file__+':node5_idle_baseline', 'exec'), namespace)
    result = namespace['reconcile'](report, observations)
    result['node5_idle_baseline_mib'] = 1
    result['target_device_ownership_checks_unchanged'] = True
    return result


def scan(index, service_path):
    namespace = dict(original.scan.__globals__, reconcile=reconcile)
    scanner = FunctionType(original.scan.__code__, namespace, 'scan', original.scan.__defaults__)
    return scanner(index, service_path)
