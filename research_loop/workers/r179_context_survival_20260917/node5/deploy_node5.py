"""Transfer scoped operator evidence through the sanctioned NODE5 wrapper."""

import argparse
import base64
import json
from pathlib import Path
import shlex
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', choices=('C2', 'C5', 'pilot', 'run1', 'C1', 'C3', 'C4', 'repo_reader'), required=True)
    parser.add_argument('--attempt', type=int, required=True)
    arguments = parser.parse_args()
    root = Path.cwd()
    own = Path(__file__).resolve().parent
    preparation = json.loads((own / 'PREPARATION_1789664527216450780.json').read_bytes())
    row = next(entry for entry in preparation['rows'] if entry['label'] == arguments.label)
    output = '/localhome/local-rohing/orch_r179_context_' + arguments.label + '_20260917_attempt' + str(arguments.attempt)
    sources = {
        'rollout_operator.py': own / 'rollout_operator.py',
        'cpu_actual.py': own / 'cpu_actual.py',
        'stage_node5.py': own / 'stage_node5.py',
        'test_stage_node5.py': own / 'test_stage_node5.py',
        'test_rollout_operator.py': own / 'test_rollout_operator.py',
        'controller_transfer.py': own / 'controller_transfer.py',
        'test_controller_transfer.py': own / 'test_controller_transfer.py',
        'detach_cpu_integration.py': own / 'detach_cpu_integration.py',
        'prove_device.py': own / 'prove_device.py',
        'policy.py': root / 'gpu/orch_r179_context_survival.py',
        'BUILDER_SCOPE.json': own.parent / 'BUILDER_SCOPE.json',
        'MAIN_TESTS.py': root / 'tests/test_orch_r179_context_survival.py',
        'CPU_MAIN.log': own.parent / 'CPU_MAIN_1.log',
        'saved_primitives.py': root / 'gpu/orch_r157_community_wall_extension.py',
        'protected_primitives.py': root / 'gpu/orch_r157_node5_keepalive.py',
        'containment_primitives.py': root / 'gpu/orch_r153_community_runtime.py',
    }
    package = dict(output=output, files={name: base64.b64encode(path.read_bytes()).decode()
                                       for name, path in sources.items()})
    package['files']['INPUT.json'] = base64.b64encode(json.dumps(row, sort_keys=True).encode()).decode()
    command = '/localhome/local-rohing/v2/venv/bin/python -B -c ' + shlex.quote((own / 'rollout_operator.py').read_text()) + ' bootstrap'
    finished = subprocess.run(['bash', str(root / 'gpu/ovx3_ssh.sh'), command],
        input=json.dumps(package), text=True, capture_output=True, timeout=330)
    receipt = dict(label=arguments.label, attempt=arguments.attempt, output=output,
                   wrapper_returncode=finished.returncode, observed_unix=time.time())
    if finished.returncode == 0:
        receipt['result'] = json.loads(finished.stdout)
    else:
        receipt['error'] = 'WRAPPER_FAILED_STDERR_NOT_EXPORTED'
    destination = own / ('STAGE_' + arguments.label + '_' + str(arguments.attempt) + '.json')
    with destination.open('x') as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write('\n')
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
