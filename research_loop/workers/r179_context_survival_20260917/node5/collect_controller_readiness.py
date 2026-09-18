"""Read immutable receiving evidence for Main's separate narrow addendum."""

import json
from pathlib import Path
import shlex
import subprocess
import sys
import time


def inspect():
    rows = []
    for label, attempt in [('C2', 4), ('C5', 3)]:
        root = Path('/localhome/local-rohing') / f'orch_r179_context_{label}_20260917_attempt{attempt}'
        sys.path.insert(0, str(root))
        import controller_transfer as helper
        binding = helper.read(root / 'CONTROLLER_BINDING.json')
        request, ready = helper.read(root / 'INPUT.json'), helper.read(root / 'READY.json')
        helper.verify_binding(binding, helper.read(request['config_ref']['path']), ready['pair'])
        names = ('READY.json', 'controller_transfer.py', 'rollout_operator.py', 'CONTROLLER_BINDING.json',
                 'CONTROLLER_PREFLIGHT.json', 'DEVICE_CPU.json', 'DETACH_CPU_INTEGRATION.json')
        extra = ('OPERATOR_CPU.log', 'STAGE_CPU.json', 'COMMAND_PREFLIGHT.json', 'SOURCE_MANIFEST.json',
                 'test_controller_transfer.py', 'detach_cpu_integration.py')
        helper.require(not any((root / name).exists() for name in
            ('CONTROLLER_STOP_INTENT.json', 'TERMINATION_INTENT.json', 'OPERATOR_STARTED.json')),
            'receiving_preparation_only_no_live_signals')
        rows.append(dict(label=label, output=str(root), files={name: helper.sha(root / name) for name in names},
            extra_files={name: helper.sha(root / name) for name in extra},
            holder_still_live_and_unchanged=True, controller_stop_intent=False, native_stop_intent=False,
            receiving_operator_tests_tail=(root / 'OPERATOR_CPU.log').read_text().splitlines()[-4:],
            device_cpu=helper.read(root / 'DEVICE_CPU.json'),
            detach_cpu=helper.read(root / 'DETACH_CPU_INTEGRATION.json'),
            source_proof=binding['source_proof'], observed_unix=time.time()))
    return rows


def main():
    if '--remote' in sys.argv:
        print(json.dumps(inspect(), sort_keys=True))
        return
    source = Path(__file__).read_text()
    command = '/localhome/local-rohing/v2/venv/bin/python -B -c ' + shlex.quote(source) + ' --remote'
    result = subprocess.run(['bash', 'gpu/ovx3_ssh.sh', command], capture_output=True, text=True, timeout=25)
    if result.returncode:
        raise RuntimeError('readiness_observation_failed: ' + result.stderr[-1500:])
    rows = json.loads(result.stdout)
    document = dict(schema='R179_NODE5_CONTROLLER_TRANSFER_REQUEST_V1',
        supersedes='CONTROLLER_TRANSFER_READY_1789667544747957194.json',
        main_addendum_required_before_signals=True, observed_unix=time.time(), rows=rows)
    path = Path(__file__).parent / f'CONTROLLER_TRANSFER_READY_{time.time_ns()}.json'
    with path.open('x') as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write('\n')
    print(path)
    for row in rows:
        print(row['label'], json.dumps(row['files'], sort_keys=True), row['receiving_operator_tests_tail'])


if __name__ == '__main__':
    main()
