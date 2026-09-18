"""Operator-only committed-child kernel dispatch and attributed result delivery."""

import argparse
import hashlib
import json
from pathlib import Path
import re

from gpu.orch_r125_cpu_experiment import digest, read_document, read_regular, verify_origin
from gpu.orch_r127_pilot_console import _directory, _inbox, _read
from organism_v6.orch_r125_experiment_request import make_request
from gpu import orch_r153_code_blocks as code_blocks


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def child_request(root, index, *, code_policy=code_blocks.LEGACY):
    require(type(index) is int and index > 0, 'positive_record_index')
    record = read_document(read_regular(Path(root)/'stream/records'/f'{index:020d}.json', 33554432))
    require(record.get('kind') == 'RESPONSE', 'child_response_only')
    require(code_policy in (code_blocks.LEGACY, code_blocks.POLICY), 'known_code_policy')
    if code_policy == code_blocks.LEGACY:
        blocks = re.findall(r'^```python experiment\n(.*?)^```[ \t]*$',
                            record['document']['response']['raw'], re.MULTILINE | re.DOTALL)
        require(len(blocks) == 1, 'one_explicit_kernel_request')
        source = blocks[0]
    else:
        source = code_blocks.extract(record['document']['response']['raw'])['source']
        require(source is not None, 'one_explicit_kernel_request')
    request = make_request(source, dict(kind='TRAIN_CHILD_RESPONSE', record_index=index,
                                         record_sha256=record['sha256']))
    request.update(schema='R132_KERNEL_REQUEST_V1', task='triton_add_f32_v1')
    request['request_id'] = digest({key: value for key, value in request.items() if key != 'request_id'})
    verify_source_origin(request, root, code_policy)
    return request


def verify_source_origin(request, root, policy):
    return (verify_origin(request, root) if policy == code_blocks.LEGACY
            else verify_origin(request, root, code_policy=policy))


def result_summary(result):
    require(result.get('schema') == 'R132_KERNEL_RESULT_V1', 'kernel_result_schema')
    require(result.get('origin', {}).get('child_generated') is True, 'actual_child_origin')
    status = result.get('status')
    require(status in ('CORRECT', 'INCORRECT', 'KERNEL_ERROR', 'PROCESS_FAILED', 'TIMEOUT',
                       'OUTPUT_LIMIT', 'TEARDOWN_UNVERIFIED', 'DISPATCH_FAILED_NO_RETRY',
                       'REQUEST_REJECTED'),
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


def publish_result(root, result_path, *, code_policy=code_blocks.LEGACY):
    path = Path(result_path)
    with _directory(path.parent) as directory:
        raw = _read(directory, path.name, 1048576)
    result = read_document(raw)
    request_path = path.parent/'REQUEST.json'
    request = read_document(read_regular(request_path, 100000))
    verified = verify_source_origin(request, root, code_policy)
    require(result.get('request_id') == request.get('request_id')
            and result.get('source_sha256') == request.get('source_sha256')
            and result.get('origin') == verified, 'result_request_origin_binding')
    return _inbox(root, 'Tool', result_summary(result),
                  dict(path=str(path.absolute()), sha256=hashlib.sha256(raw).hexdigest()))


def dispatch(root, index, *, spool, runtime_root, gate_path, admission_path, code_policy=code_blocks.LEGACY):
    from gpu.orch_r132_kernel_executor import parse_request, run_request

    request = child_request(root, index, code_policy=code_policy)
    raw = json.dumps(request).encode()
    try:
        parse_request(raw)
    except ValueError as error:
        destination = Path(spool)/request['request_id']
        destination.mkdir(parents=True, exist_ok=False, mode=0o700)
        result = dict(schema='R132_KERNEL_RESULT_V1', request_id=request['request_id'],
                      source_sha256=request['source_sha256'], origin=verify_source_origin(request, root, code_policy),
                      status='REQUEST_REJECTED', launch_attempted=False, error=str(error))
        with (destination/'REQUEST.json').open('xb') as output:
            output.write(raw)
        with (destination/'RESULT.json').open('x') as output:
            json.dump(result, output, sort_keys=True, allow_nan=False)
    else:
        result = run_request(raw, spool=spool, runtime_root=runtime_root,
                             gate_path=gate_path, admission_path=admission_path,
                             origin_verifier=lambda value: verify_source_origin(value, root, code_policy))
    path = Path(spool)/request['request_id']/'RESULT.json'
    require(read_document(read_regular(path, 1048576)) == result, 'persisted_result_required')
    receipt = (publish_result(root, path) if code_policy == code_blocks.LEGACY
               else publish_result(root, path, code_policy=code_policy))
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
