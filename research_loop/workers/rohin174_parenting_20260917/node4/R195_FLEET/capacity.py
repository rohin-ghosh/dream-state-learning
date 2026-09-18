"""Reuse the privileged node4 admission scanner without launching or signaling."""

import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

from math_c import HOME, SOURCE, HOST_SHA, require, write


def main():
    require(os.geteuid() == 0 and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_privileged_scan')
    import hashlib
    import socket
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA, 'exact_node4')
    candidates = {2: 'GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8',
                  7: 'GPU-6eac3b9d-551a-d786-f598-04ef6d701c98'}
    sys.path.insert(0, str(SOURCE))
    from gpu import orch_rich_hot_a100_minor_scan as minor
    from gpu import orch_r111_route_admission as admission
    minor.pinned.policy = SimpleNamespace(HOST_SHA=HOST_SHA, DEVICES=candidates, require=require,
        allocation=lambda physical: require(physical in candidates, 'only_user_requested_spare_candidates'))
    output = HOME.parent / ('CAPACITY_' + str(time.time_ns()))
    output.mkdir()
    service = output / 'SERVICE_IDENTITY.json'
    minor.pinned.service(service)
    results = []
    for physical in candidates:
        report = admission.scan(physical, service)
        write(output / f'physical{physical}.json', report)
        results.append(dict(physical=physical, gpu_uuid=candidates[physical],
            clear=report['clear'], blocking_reasons=report['blocking_reasons'],
            minor=report['device_minor'], memory_used_mib=report['gpu']['memory_used_mib'],
            scanner_euid=report['scanner_euid']))
    summary = dict(observed_unix=time.time(), candidates=results, evidence=str(output),
        launches=0, signals=0, reservation_or_dispatch=False,
        note='Point-in-time shared-device scan; every launch still uses unchanged fresh admission.')
    write(output / 'SUMMARY.json', summary)
    for path in output.iterdir():
        os.chown(path, 2524, 2524)
    os.chown(output, 2524, 2524)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
