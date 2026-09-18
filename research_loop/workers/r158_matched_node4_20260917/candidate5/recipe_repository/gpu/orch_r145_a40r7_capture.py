"""CPU-only, append-only capture of the single failed A40R none life."""

import hashlib
import json
from pathlib import Path
import subprocess
import time


BASE = Path('/localhome/local-rohing/orch_r136_raw_unparented_none_a40r7_20260916_attempt1')
OUTPUT = BASE / 'control_r145_a40r7_prepare_20260916t1620z_v2'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    OUTPUT.mkdir(exist_ok=False)
    control = BASE / 'control1'
    guard = json.loads((control / 'GUARD.json').read_text())
    plan = json.loads(Path(guard['plan_path']).read_text())
    records = []
    for path in sorted((BASE / 'run1/stream/records').glob('*.json')):
        if not path.name.endswith('.intent.json'):
            records.append(json.loads(path.read_text()))
    assert len(records) == 1375 and records[-1]['sha256'] == '1b542ccb0d93b2aadeb02b9c1ab7655c932ebd834d808b7d1134ba9bb3c6258f'
    selected = ['control1/GUARD.json', 'control1/PLAN.json', 'control1/EXIT.json',
                'control1/NATIVE.log', 'control1/LAUNCH.json', 'run1/checkpoints/sleep_000022/COMMIT.json',
                'source1/gpu/orch_r125_continual_native.py', 'source1/gpu/orch_r125_continual_guard.py',
                'source1/organism_v6/orch_r125_plain_context.py']
    pins = {name: sha(BASE / name) for name in selected}
    source = Path(plan['source_root'])
    assert all(sha(source / name) == expected for name, expected in guard['source_pins'].items())
    inventory = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid', '--format=csv,noheader'], text=True)
    topology = [line.strip() for line in inventory.splitlines() if 'GPU-6eac3b9d-551a-d786-f598-04ef6d701c98' in line]
    assert len(topology) == 1
    device = [path.read_text() for path in Path('/proc/driver/nvidia/gpus').glob('*/information')
              if 'GPU-6eac3b9d-551a-d786-f598-04ef6d701c98' in path.read_text()]
    assert len(device) == 1
    metadata = dict(observed_unix=time.time(), root=str(BASE / 'run1'), pins=pins,
        guard_keys=sorted(guard), topology=topology, device_information=device[0], record_count=len(records),
        saved=records[1365]['document']['checkpoint'], eligibility=records[1373]['document'],
        abandoned_update=records[1374]['document'], plan={key: plan.get(key) for key in
            ('physical', 'gpu_uuid', 'root', 'source_root', 'hard_end_unix', 'context_limit',
             'segment_tokens', 'presentation_version', 'device_containment')},
        exit=json.loads((control / 'EXIT.json').read_text()),
        launch=json.loads((control / 'LAUNCH.json').read_text()),
        source_closure_verified=True, held_contents_read=False)
    for name, value in [('CAPTURE.json', metadata), ('TRAIN_SUFFIX.json', records[1365:]),
                        ('ORIGINAL_GUARD.json', guard), ('ORIGINAL_PLAN.json', plan)]:
        with (OUTPUT / name).open('x') as handle:
            json.dump(value, handle, sort_keys=True, indent=2)
            handle.write('\n')
    print(json.dumps(dict(output=str(OUTPUT), capture_sha256=sha(OUTPUT / 'CAPTURE.json'),
        topology=topology, device_information=device[0], record_count=len(records), saved_steps=metadata['saved']['optimizer_steps'],
        eligibility_counts={key: len(metadata['eligibility'].get(key, [])) for key in
                            ('new_row_sha256', 'rehearsal_row_sha256', 'excluded')},
        guard_keys=metadata['guard_keys'], pins=pins), indent=2))


if __name__ == '__main__':
    main()
