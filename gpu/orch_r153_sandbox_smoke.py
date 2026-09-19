"""Real confined CPU smoke for the new parser, with no learner or GPU access."""

import argparse
import hashlib
import json
from pathlib import Path
import time

from gpu import orch_r125_cpu_experiment as cpu
from gpu import orch_r153_code_blocks as blocks
from organism_v6.orch_r125_experiment_request import make_request


def save(path, value):
    with path.open('x') as output:
        json.dump(value, output, indent=2, sort_keys=True, allow_nan=False)


def run(root):
    root = Path(root).absolute()
    cpu.require(root.resolve() == root and '..' not in root.parts, 'new_operator_root')
    root.mkdir(parents=True, exist_ok=False)
    gate = root / 'gate'
    gate.mkdir()
    result = dict(status='STARTED', model_generated=False, gpu_access=False, started_unix=time.time())
    try:
        for mode in ('basic', 'output', 'timeout', 'memory', 'files'):
            receipt = cpu.profile.run(root / ('probe_' + mode), mode)
            save(gate / (mode + '.json'), receipt)
            cpu.require(receipt.get('passed') is True, 'real_CPU_profile_failed_' + mode)
        cpu.verify_gate(gate)
        examples = {'plain': '```python\nprint(6 * 7)\n```',
                    'punctuation': '```python\nprint（“normalized”）\n```',
                    'syntax_failure': '```python\ndef invalid(:\n```'}
        outcomes = {}
        for name, raw in examples.items():
            block = blocks.extract(raw)
            save(root / (name + '_TRANSFORMATION.json'), block)
            source_request = make_request(block['source'], dict(kind='BUILDER_TEST', record_index=0,
                                          record_sha256=hashlib.sha256(raw.encode()).hexdigest()))
            request = json.dumps(source_request, sort_keys=True).encode()
            receipt = cpu.run_request(request, root / 'spool', gate, code_policy=blocks.POLICY)
            cpu.require(receipt.get('cgroup_removed_after_stop') is True, 'smoke_teardown_verified')
            if name == 'syntax_failure':
                cpu.require(receipt['status'] == 'PROCESS_FAILED' and receipt['returncode'] != 0,
                            'real_syntax_failure_required')
            else:
                expected = '42' if name == 'plain' else 'normalized'
                cpu.require(receipt['status'] == 'COMPLETE' and receipt['returncode'] == 0
                            and receipt['stdout'].strip() == expected, 'real_stdout_required')
            outcomes[name] = dict(status=receipt['status'], stdout=receipt.get('stdout'),
                                  returncode=receipt.get('returncode'), request_id=source_request['request_id'])
        result.update(status='PASS', examples=outcomes, gate_root=str(gate),
                      source_closure=cpu.source_closure())
    except BaseException as error:
        result.update(status='FAIL', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        result['finished_unix'] = time.time()
        save(root / 'RESULT.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root), sort_keys=True))
