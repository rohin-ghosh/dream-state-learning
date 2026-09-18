"""Operator-only real fixed-kernel smoke under fresh confinement and custody."""

import argparse
import datetime
import json
import os
from pathlib import Path
import time

from gpu import orch_r125_cpu_experiment as cpu
from gpu import orch_r132_kernel_executor as executor
from gpu import orch_r148_kernel_tool_service as service
from gpu import orch_r153_code_blocks as blocks


def save(path, value):
    with path.open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2, allow_nan=False)


def locked_census(root, name, lease_path, wall):
    previous = os.read(root, 65537)
    cpu.require(len(previous) <= 65536, 'bounded_executor_lock')
    if previous:
        state = cpu.read_document(previous)
        cpu.require(state.get('result_status') in ('CORRECT', 'INCORRECT', 'KERNEL_ERROR',
                    'PROCESS_FAILED', 'OUTPUT_LIMIT', 'TIMEOUT', 'TRUSTED_PROBES_PASSED'),
                    'no_ambiguous_executor_predecessor')
    observed = time.time()
    census = service.census()
    return dict(schema='R132_KERNEL_ADMISSION_V1', main_authorized=True, census_clear=True,
                gpu_uuid=executor.GPU_UUID, device_minor=executor.GPU_MINOR,
                observed_unix=observed, expires_unix=min(observed + 210, wall),
                hard_wall_unix=wall, lease_receipt_path=str(lease_path),
                lease_receipt_sha256=service.sha(lease_path.read_bytes()),
                census_sha256=service.sha(census), operator=name)


def write_lock(descriptor, value):
    os.lseek(descriptor, 0, os.SEEK_SET)
    os.ftruncate(descriptor, 0)
    os.write(descriptor, json.dumps(value, sort_keys=True).encode())
    os.fsync(descriptor)


def run(root, runtime_root, lease_path):
    root, runtime_root, lease_path = map(executor.trusted_path, (root, runtime_root, lease_path))
    root.mkdir(exist_ok=False)
    report = dict(status='STARTED', model_generated=False, started_unix=time.time())
    try:
        lease = cpu.read_document(cpu.read_regular(lease_path, 65536))
        end = datetime.datetime.fromisoformat(lease['conservative_lease_end_utc'])
        cpu.require(end.tzinfo is not None and lease['margin_seconds'] >= 21600, 'original_lease_safety_margin')
        wall = min(end.timestamp() - lease['margin_seconds'], time.time() + 900)
        runtime_hash = executor.validate_runtime(runtime_root)
        identity = executor.policy_identity(runtime_root, runtime_hash, executor.device_identity())
        with service.lock_file(executor.LOCK_PATH) as descriptor:
            admission = locked_census(descriptor, 'R153_CONFIRMED_OPERATOR_SMOKE', lease_path, wall)
            save(root / 'PROBE_ADMISSION.json', admission)
            executor.validate_admission(root / 'PROBE_ADMISSION.json', time.time())
            write_lock(descriptor, dict(result_status='DISPATCH_INCOMPLETE', last_finished_unix=time.time(),
                                        owner=str(root)))
            probe = executor.run_trusted_probes(root / 'probes', runtime_root, root / 'PROBE_ADMISSION.json')
            save(root / 'PROBE_RESULT.json', probe)
            cpu.require(probe.get('passed') is True and probe.get('checks') == 26, 'complete_kernel_profile_gate')
            gate_hash = executor.validate_gate(root / 'probes/GATE.json', identity, time.time())
            write_lock(descriptor, dict(result_status='TRUSTED_PROBES_PASSED', last_finished_unix=time.time(),
                                        gate_sha256=gate_hash, owner=str(root)))
        raw = '```python\n' + executor.EXAMPLE_SOURCE + '```\n'
        block = blocks.extract(raw)
        save(root / 'TRANSFORMATION.json', block)
        request = executor.make_request(block['source'], dict(kind='BUILDER_TEST', record_index=0,
                                                              record_sha256=blocks.sha(raw)))
        save(root / 'REQUEST.json', request)
        with service.lock_file(executor.LOCK_PATH) as descriptor:
            admission = locked_census(descriptor, 'R153_CONFIRMED_OPERATOR_SMOKE', lease_path, wall)
            admission.update(request_id=request['request_id'], source_sha256=request['source_sha256'],
                             origin=request['origin'])
            save(root / 'ADMISSION.json', admission)
        result = executor.run_request(json.dumps(request).encode(), spool=root / 'spool',
                    runtime_root=runtime_root, gate_path=root / 'probes/GATE.json',
                    admission_path=root / 'ADMISSION.json')
        save(root / 'KERNEL_RESULT.json', result)
        cpu.require(result.get('status') == 'CORRECT' and result.get('launch_attempted') is True
                    and result.get('cgroup_removed') is True, 'actual_correct_reaped_kernel_required')
        report.update(status='PASS', gate_path=str(root / 'probes/GATE.json'),
                      runtime_root=str(runtime_root), request_id=request['request_id'],
                      result_status=result['status'], measurement=result['measurement'])
    except BaseException as error:
        report.update(status='FAIL', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        report['finished_unix'] = time.time()
        save(root / 'RESULT.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'runtime_root', 'lease_path'):
        parser.add_argument('--' + name.replace('_', '-'), required=True)
    options = parser.parse_args()
    print(json.dumps(run(options.root, options.runtime_root, options.lease_path), sort_keys=True))
