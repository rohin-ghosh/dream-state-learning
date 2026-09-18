"""Trace original rejected samples for one raw1 handoff, with no predicate change."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import FunctionType, SimpleNamespace


BUNDLE = Path('/localhome/local-rohing/orch_r179_node4_r181journal_20260917t2220z')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
SOURCE = BUNDLE / 'lane1/source'
CONFIG = BUNDLE / 'lane1/control/GUARD.json'
EXPECTED = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
    'PYTHONPATH=' + str(SOURCE), PYTHON, '-B', '-m', 'gpu.orch_r179_busy_preflight', '--config', str(CONFIG)]


def traced_command(command, script):
    if command != EXPECTED:
        return command
    return EXPECTED[:8] + [str(script), 'scan']


def scan():
    from gpu import orch_r179_busy_preflight as helper
    if Path(helper.__file__).resolve() != SOURCE / 'gpu/orch_r179_busy_preflight.py':
        raise ValueError('exact_actual_helper_import')
    captured = []

    def annotate(report, observations):
        result = helper.annotate(report, observations)
        captured.append(dict(original_report=report, all_original_observations=observations,
            exact_helper_annotation=result['r179_preflight_evidence'], predicate_changed=False))
        return result

    namespace = dict(helper.scan.__globals__, annotate=annotate)
    copied = FunctionType(helper.scan.__code__, namespace, helper.scan.__name__, helper.scan.__defaults__)
    report = copied(CONFIG)
    if len(captured) != 1:
        raise ValueError('exactly_one_original_scan')
    with (BUNDLE / 'RAW1_ORIGINAL_REJECTED_SAMPLES.json').open('x') as stream:
        json.dump(captured[0], stream, sort_keys=True, allow_nan=False)
    return report


def handoff():
    spec = importlib.util.spec_from_file_location('unchanged_journal_handoff', BUNDLE / 'node4_rollout.py')
    operator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(operator)
    helpers = operator.helper_module(BUNDLE)
    operator.require(helpers.sha(BUNDLE / 'node4_rollout.py') ==
        '3bebf07c0eb71b8dfaef71511cc01662973da335a8e781bdc1034cb6742a3874', 'unchanged_exact_handoff')
    operator.require(not (BUNDLE / 'RAW1_ORIGINAL_REJECTED_SAMPLES.json').exists(), 'one_trace_attempt_only')
    original = subprocess.check_output

    def check_output(command, **options):
        return original(traced_command(command, Path(__file__).resolve()), **options)

    operator.subprocess = SimpleNamespace(**dict(vars(subprocess), check_output=check_output))
    return operator.handoff(BUNDLE, BUNDLE / 'lane1', 5400)


if __name__ == '__main__':
    if sys.argv[1:] == ['scan']:
        print(json.dumps(scan(), sort_keys=True))
    elif sys.argv[1:] == ['handoff']:
        print(json.dumps(handoff(), sort_keys=True))
    else:
        raise ValueError('scan_or_handoff_only')
