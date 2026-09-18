"""Stage fixed clone source closures on the two observed node4 spare candidates."""

import argparse
import json
from pathlib import Path
import shutil
import time

from math_c import HOME, SOURCE, SNAPSHOT, MANIFEST_SHA, ARCHIVE_SHA, host, read, require, sha, write


DEVICES = {0: ('GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d', 3),
    1: ('GPU-4b071167-a06a-773c-f947-60cb8c2f7512', 2),
    2: ('GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8', 1),
    3: ('GPU-4d0f10af-119f-10bb-a28f-f7b7703a3b14', 0),
    5: ('GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30', 6),
    7: ('GPU-6eac3b9d-551a-d786-f598-04ef6d701c98', 4)}


def main(physicals):
    host()
    require(sha(SNAPSHOT / 'MANIFEST.json') == MANIFEST_SHA
        and sha(SNAPSHOT / 'SNAPSHOT.tar') == ARCHIVE_SHA, 'fixed_source51_console5846')
    manifest = read(SNAPSHOT / 'MANIFEST.json')
    cpu = read(HOME / 'RECEIVING_CPU_R202.json')
    pins = cpu['source_pins']
    require(cpu['passed'] and all(sha(SOURCE / name) == digest for name, digest in pins.items()),
        'same_tested_R201_R202_closure')
    results = []
    for physical in physicals:
        device, minor = DEVICES[physical]
        target = HOME.parent / f'SCALE_physical{physical}'
        target.mkdir()
        shutil.copytree(SOURCE, target / 'source', ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
        shutil.copytree(SNAPSHOT, target / 'snapshot')
        for name in ('main_ready', 'r202_ready', 'inputs'):
            shutil.copytree(HOME / name, target / name)
        for name in ('CPU_SANDBOX.json', 'RECEIVING_CPU.json', 'RECEIVING_CPU_R202.json'):
            shutil.copyfile(HOME / name, target / name)
        require(all(sha(target / 'source' / name) == digest for name, digest in pins.items()), 'copied_source_exact')
        require(all(sha(target / 'snapshot' / item['relative']) == item['sha256']
            for item in manifest['files']), 'copied_fixed_snapshot_exact')
        receipt = dict(status='FIXED_SOURCE_RECEIVER_STAGED_NOT_LAUNCHED', observed_unix=time.time(),
            candidate_physical=physical, gpu_uuid=device, device_minor=minor, receiver=str(target),
            source_manifest_sha256=MANIFEST_SHA, source_archive_sha256=ARCHIVE_SHA,
            source_cycle=51, optimizer_steps=4908, common_masked_context_record=5846,
            tested_source_receipt_sha256=sha(target / 'RECEIVING_CPU_R202.json'),
            signals=0, GPU_model_calls=0, live_inbox_copies=0, final_arm_assignment=None,
            note='Receiving materials only; no slot reservation, new journal, parent publication or launch claim.')
        write(target / 'STAGED.json', receipt)
        results.append(receipt)
    print(json.dumps(results))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, choices=tuple(DEVICES), nargs='+', default=[2, 7])
    main(parser.parse_args().physical)
