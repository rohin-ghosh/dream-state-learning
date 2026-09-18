"""Read-only NODE2 CPU transport inspection; never dispatch or mutate a journal."""

import argparse
import hashlib
import json
from pathlib import Path
import socket
import sys
import time


SOURCE = '/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1/receiving_source1/source'
GATE = '/localhome/local-rohing/orch_r153_cpu_smoke_20260916t2212z/gate'
LEASE = '/localhome/local-rohing/orch_r183_repo_learning_20260917/birth1/LEASE.json'
PLAIN_FENCE = '```python\nprint(6 * 7)\n```\n'


def probe(source, gate_root):
    source = Path(source).resolve(strict=True)
    sys.path.insert(0, str(source))
    from gpu import orch_r125_cpu_experiment as cpu
    from gpu import orch_r153_code_blocks as blocks
    from gpu import orch_r153_community_transport as transport
    from organism_v6.orch_r125_experiment_request import make_request

    modules = (cpu, blocks, transport, sys.modules[make_request.__module__])
    if not all(Path(module.__file__).resolve().is_relative_to(source) for module in modules):
        raise ValueError('imports_must_use_selected_installed_source')
    route, extracted = transport.code_route(PLAIN_FENCE)
    request = make_request(extracted['source'], dict(kind='BUILDER_TEST', record_index=0,
        record_sha256=hashlib.sha256(PLAIN_FENCE.encode()).hexdigest()))
    report = dict(schema='R184_NODE2_CPU_AVAILABILITY_V1', observed_unix=time.time(),
        host=socket.gethostname(), read_only=True, callback_ready=False,
        source_root=str(source), source_pins=transport.source_pins(source),
        dispatcher_closure=cpu.source_closure(), gate_root=gate_root, gate_sha256=None,
        gate_verified=False, supported_wrappers=transport.WRAPPERS,
        plain_fence=dict(raw=PLAIN_FENCE, route=route, source=extracted['source'],
            code_policy=blocks.POLICY, request_id=request['request_id'],
            origin_proof=cpu.verify_origin(request, None, code_policy=blocks.POLICY)),
        smoke=dict(status='NOT_RUN', executed=False, stdout=None, child_generated=False))
    home = Path('/localhome/local-rohing')
    report['compatible_gate_roots'] = [str(path / 'gate') for path in sorted(
        home.glob('orch_r153_cpu_smoke_*')) if path.is_dir() and (path / 'gate').is_dir()]
    try:
        gate = cpu.verify_gate(gate_root)
    except (ValueError, OSError) as error:
        report.update(status='BLOCKED_GATE_NOT_VERIFIED',
            gate_error=dict(type=type(error).__name__, message=str(error)))
    else:
        report.update(status='GATE_VERIFIED_SMOKE_STILL_REQUIRED', gate_verified=True,
            gate_sha256=cpu.digest(gate), gate_references=gate)
    lease_path = Path(LEASE)
    if lease_path.is_file():
        raw = lease_path.read_bytes()
        lease = json.loads(raw)
        fields = ('lease_end_unix', 'hard_end_unix', 'experiment_hard_end_unix',
            'original_bound_lease_path', 'original_bound_lease_sha256', 'machine_lease_changed')
        report['lease'] = dict(path=str(lease_path), sha256=hashlib.sha256(raw).hexdigest(),
            fields={key: lease[key] for key in fields if key in lease})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default=SOURCE)
    parser.add_argument('--gate-root', default=GATE)
    options = parser.parse_args()
    print(json.dumps(probe(options.source, options.gate_root), sort_keys=True))


if __name__ == '__main__':
    main()
