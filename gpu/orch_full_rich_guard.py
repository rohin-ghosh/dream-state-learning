"""Own-root finite A100 guardian; reuses the existing fail-closed process scan."""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import orch_replication_guard as guard
from gpu.orch_full_rich import DEVICES, UNUSED, source, write


LEASE_CUTOFF = datetime(2026, 9, 26, 23, 5, tzinfo=timezone.utc).timestamp()


def scan(index, uuid):
    report = guard.scan(index, uuid)
    inventory = guard.query('index,name,uuid', 'gpu')
    if not any(row[0] == str(index) and 'A100' in row[1] and row[2] == uuid for row in inventory):
        raise ValueError('A100_physical_name_binding')
    identities, partial_reservations = [], []
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            if entry.stat().st_uid != os.getuid() or not (entry / 'cmdline').read_bytes():
                continue
            before = (entry / 'stat').read_text().rsplit(')', 1)[1].split()
            environment, unused_privileged = guard.environment_bytes(entry)
            after = (entry / 'stat').read_text().rsplit(')', 1)[1].split()
            if before[19] != after[19]:
                raise ValueError('process_identity_drift')
            visible = next((value.split(b'=', 1)[1].decode() for value in environment.split(b'\0')
                            if value.startswith(b'CUDA_VISIBLE_DEVICES=')), '')
            if any(uuid.startswith(device) for device in visible.split(',') if device.startswith('GPU-')):
                partial_reservations.append(int(entry.name))
            identities.append(dict(pid=int(entry.name), start_ticks=after[19], pgid=after[2],
                                   uid=entry.stat().st_uid, boot_id=boot, cuda_visible_devices=visible))
        except (FileNotFoundError, ProcessLookupError):
            continue
    report.update(process_identities=identities, partial_uuid_reservations=partial_reservations)
    report['safe'] = report['safe'] and not partial_reservations
    return report


def sequence(root):
    if root != Path('/tmp/orch_full_rich_20260914_attempt1') or root.is_symlink():
        raise ValueError('own_root_required')
    if not (root / 'PUBLICATION.json').is_file():
        raise ValueError('published_preGPU_required')
    publication = source.read(root / 'PUBLICATION.json')
    prepared = source.read(root / 'prepare/PREPARE.json')
    if (publication['status'] != 'PUSHED_PRE_GPU' or publication['source_commit'] != prepared['source_commit']
            or publication['prepare_sha256'] != source.file_hash(root / 'prepare/PREPARE.json')
            or publication['source_sha256'] != prepared['source_sha256']):
        raise ValueError('published_preGPU_binding_mismatch')
    started = time.time()
    deadline = min(started + 2640, LEASE_CUTOFF - 60)
    if deadline - started < 2640:
        raise ValueError('finite_lease_margin')
    children, streams, launches = [], [], []

    def interrupted(signum, frame):
        for child in children:
            guard.stop(child)
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)

    def launch(phase, state):
        label = 'collection' if phase == 'collect' else state
        report = scan(*DEVICES[state])
        write(root / f'{label}_ADMISSION.json', report)
        if not report['safe']:
            raise ValueError('physical_admission_failed:' + label)
        stream = (root / f'{label}_native.log').open('x')
        streams.append(stream)
        command = [guard.PYTHON, '-B', '-m', 'gpu.orch_full_rich', '--root', str(root),
                   '--phase', phase, '--state', state, '--deadline', str(deadline)]
        child = subprocess.Popen(command, env=dict(os.environ, CUDA_VISIBLE_DEVICES=DEVICES[state][1]),
                                 stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        children.append(child)
        launch_receipt = dict(state=state, phase=phase, native_pid=child.pid, guardian_pid=os.getpid(),
                              gpu_uuid=DEVICES[state][1], started_unix=time.time(), deadline_epoch=deadline,
                              lease_cutoff_epoch=LEASE_CUTOFF, command=command)
        launches.append(launch_receipt)
        write(root / f'{label}_LAUNCH.json', launch_receipt)
        return child

    result = dict(status='FAILED', started_unix=started, scope_seconds=2700, lease_cutoff_epoch=LEASE_CUTOFF)
    try:
        collection = launch('collect', 'ORIGINAL37EC')
        if collection.wait(timeout=max(1, deadline-time.time())) != 0:
            raise ValueError('original_collection_failed_no_replacement')
        readers = [launch('readout', state) for state in DEVICES]
        codes = [child.wait(timeout=max(1, deadline-time.time())) for child in readers]
        if any(codes):
            raise ValueError('readout_failed_no_retry')
        result['status'] = 'COMPLETE'
    except Exception as error:
        result['error'] = dict(type=type(error).__name__, message=str(error))
    finally:
        for child in children:
            guard.stop(child)
        for stream in streams:
            stream.close()
        result.update(elapsed_seconds=time.time()-started, launches=launches,
                      finished_utc=datetime.now(timezone.utc).isoformat())
        write(root / 'TERMINAL.json', result)
        for index, uuid in [*DEVICES.values(), UNUSED]:
            write(root / f'RELEASE_GPU{index}.json', scan(index, uuid))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--scan', action='store_true')
    options = parser.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                      TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                      PYTHONDONTWRITEBYTECODE='1')
    if options.scan:
        write(options.root / 'PREPARE_ADMISSION.json', {state: scan(*device) for state, device in DEVICES.items()})
    else:
        sequence(options.root)


if __name__ == '__main__':
    main()
