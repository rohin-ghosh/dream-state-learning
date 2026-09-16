"""Operator-only committed-child kernel dispatch and attributed result delivery."""

import argparse
import hashlib
import json
from pathlib import Path
import re

from gpu.orch_r125_cpu_experiment import read_document, read_regular, verify_origin
from gpu.orch_r127_pilot_console import _directory, _inbox, _read


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def child_request(root, index):
    from gpu.orch_r132_kernel_executor import make_request

    require(type(index) is int and index > 0, 'positive_record_index')
    record = read_document(read_regular(Path(root)/'stream/records'/f'{index:020d}.json', 33554432))
    require(record.get('kind') == 'RESPONSE', 'child_response_only')
    blocks = re.findall(r'^```python experiment\n(.*?)^```[ \t]*$',
                        record['document']['response']['raw'], re.MULTILINE | re.DOTALL)
    require(len(blocks) == 1, 'one_explicit_kernel_request')
    request = make_request(blocks[0], dict(kind='TRAIN_CHILD_RESPONSE', record_index=index,
                                         record_sha256=record['sha256']))
    verify_origin(request, root)
    return request


def result_summary(result):
    require(result.get('schema') == 'R132_KERNEL_RESULT_V1', 'kernel_result_schema')
    require(result.get('origin', {}).get('child_generated') is True, 'actual_child_origin')
    status = result.get('status')
    require(status in ('CORRECT', 'INCORRECT', 'KERNEL_ERROR', 'PROCESS_FAILED', 'TIMEOUT',
                       'OUTPUT_LIMIT', 'TEARDOWN_UNVERIFIED', 'DISPATCH_FAILED_NO_RETRY'),
            'finished_kernel_result_status')
    lines = ['Kernel tool result: ' + status]
    measurement = result.get('measurement', {})
    if status in ('CORRECT', 'INCORRECT'):
        require(result.get('launch_attempted') is True and result.get('cgroup_removed') is True,
                'executed_and_reaped_kernel')
        require(result.get('capture', {}).get('returncode') == 0, 'successful_harness_process')
        require(measurement.get('status') == status and type(measurement.get('cases')) is dict,
                'matching_measurement')
        require(set(measurement['cases']) == {'1', '1024', '65537', '1048576'}, 'all_task_shapes')
        for size, case in measurement['cases'].items():
            lines.append('Length ' + size + ': correctness=' + str(case['correct'])
                         + ', reference_ms=' + str(case['reference_ms'])
                         + ', candidate_ms=' + str(case['candidate_ms'])
                         + ', reported_speedup=' + str(case['reported_speedup']))
        lines.append('These are this tool execution\'s measurements, not proof of general speedup.')
    error = result.get('error') or measurement.get('reported_error', {}).get('error')
    if error:
        lines.append('Error: ' + str(error)[:2048])
    if status not in ('CORRECT', 'INCORRECT'):
        lines.append('This result does not establish a correct, faster kernel.')
    return '\n'.join(lines)


def publish_result(root, result_path):
    path = Path(result_path)
    with _directory(path.parent) as directory:
        raw = _read(directory, path.name, 1048576)
    result = read_document(raw)
    request_path = path.parent/'REQUEST.json'
    request = read_document(read_regular(request_path, 100000))
    verified = verify_origin(request, root)
    require(result.get('request_id') == request.get('request_id')
            and result.get('source_sha256') == request.get('source_sha256')
            and result.get('origin') == verified, 'result_request_origin_binding')
    return _inbox(root, 'Tool', result_summary(result),
                  dict(path=str(path.absolute()), sha256=hashlib.sha256(raw).hexdigest()))


def dispatch(root, index, *, spool, runtime_root, gate_path, admission_path):
    from gpu.orch_r132_kernel_executor import run_request

    request = child_request(root, index)
    result = run_request(json.dumps(request).encode(), spool=spool, runtime_root=runtime_root,
                         gate_path=gate_path, admission_path=admission_path,
                         origin_verifier=lambda value: verify_origin(value, root))
    path = Path(spool)/request['request_id']/'RESULT.json'
    require(read_document(read_regular(path, 1048576)) == result, 'persisted_result_required')
    receipt = publish_result(root, path)
    return dict(result_path=str(path), status=result['status'], delivery=receipt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--record-index', type=int, required=True)
    for name in ('spool', 'runtime-root', 'gate-path', 'admission-path'):
        parser.add_argument('--' + name, type=Path, required=True)
    arguments = vars(parser.parse_args())
    arguments['index'] = arguments.pop('record_index')
    print(json.dumps(dispatch(**arguments), sort_keys=True))
