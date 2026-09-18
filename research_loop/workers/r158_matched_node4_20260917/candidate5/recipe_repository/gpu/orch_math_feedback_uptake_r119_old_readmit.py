"""One fresh admission after a proven pre-model transient holder exited."""

import argparse
import importlib.util
import json
from pathlib import Path
import time
from types import FunctionType


def proof(report, root, *, exists=lambda pid: Path('/proc', str(pid)).exists()):
    reasons = report['blocking_reasons']
    if report['clear'] or len(reasons) != 1 or not reasons[0].startswith('open_device_pid:'):
        raise ValueError('exact_one_transient_holder')
    pid = int(reasons[0].split(':')[1])
    entries = [entry for entry in report['processes'] if entry['pid'] == pid]
    if len(entries) != 1 or not entries[0].get('identity_consistent') or exists(pid):
        raise ValueError('exact_observed_holder_gone')
    if (root / 'LAUNCH.json').exists() or list(root.glob('cycle*')):
        raise ValueError('no_prior_native_or_charged_task')
    return dict(previous_holder=entries[0], observed_absent=True, observed_unix=time.time(),
                original_admission_retained=True, old_report_not_cleared=True)


def run(source, index):
    spec = importlib.util.spec_from_file_location('bound_old_math_guard', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    old, lane, output, plan = module.validate(index)
    evidence = proof(module.read(output / 'ADMISSION.json'), output)
    module.write(output / 'PREMODEL_EXIT.json', dict(evidence, source_sha256=module.sha(source),
        launcher_sha256=module.sha(__file__), plan_sha256=module.sha(output / 'PLAN.json')))
    def write(path, value):
        if Path(path) == output / 'ADMISSION.json':
            path = output / 'ADMISSION_AFTER_EXIT.json'
        return module.write(path, value)
    fresh = FunctionType(module.guard.__code__, dict(module.guard.__globals__, write=write),
                         'fresh_guard', module.guard.__defaults__)
    fresh(index)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--index', type=int, choices=(2,), required=True)
    arguments = parser.parse_args()
    run(arguments.source, arguments.index)
