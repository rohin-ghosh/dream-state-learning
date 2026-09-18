"""Freeze Ampere's executed explicit scaffold for the same NODE5 C2 slot."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
AMPERE = HERE.parents[1] / 'rohin183_repo_learning_20260917'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = HERE / ('R188_SOURCE_' + str(time.time_ns()))
    source = root / 'source'
    declared = json.loads((AMPERE / 'R184_EXPLICIT_SOURCE.json').read_bytes())
    for name, expected in declared['source_pins'].items():
        origin = AMPERE / 'r184_explicit_source' / name
        assert sha(origin) == expected
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origin, target)
    original = source / 'gpu/r184_node2_confinement.py'
    text = original.read_text()
    replacements = {
        "DEVICE='GPU-c9450d3d-0455-f034-b9bf-7f8956e44733'": "DEVICE='GPU-7fc4e5b2-060c-ada8-8f91-3fe262c3573c'",
        'MINOR=3': 'MINOR=1',
        "MODULE='gpu.r184_node2_confinement'": "MODULE='gpu.r188_node5_confinement'",
        'remaining=min(7200,int(plan[\'hard_end_unix\']-now-15))': "remaining=int(plan['hard_end_unix']-now-15)",
        "30<remaining<=21600": "30<remaining<=plan['hard_end_unix']-now",
        "'orch-r184-c2-explicit-'": "'orch-r188-node5-c2-'",
        "    properties['BindPaths']=config['copy_raw']+':'+plan['root']\n": '',
        "[0, 1, 2, 4, 5, 6, 7]": '[0, 2, 3, 4, 5, 6, 7]',
        '0000:57:00.0': '0000:52:00.0',
    }
    for before, after in replacements.items():
        assert text.count(before) == 1, before
        text = text.replace(before, after)
    assert text.count('/dev/nvidia3') == 2
    text = text.replace('/dev/nvidia3', '/dev/nvidia1')
    compile(text, 'r188_node5_confinement.py', 'exec')
    with (source / 'gpu/r188_node5_confinement.py').open('x') as handle:
        handle.write(text)
    pins = {str(path.relative_to(source)):sha(path) for path in source.rglob('*.py')}
    manifest = dict(source_pins=pins, original_ampere_source_sha256=sha(AMPERE/'R184_EXPLICIT_SOURCE.json'),
        unchanged_runtime_native=sha(source/'gpu/orch_r125_continual_native.py'),
        deltas=['same_NODE5_C2_UUID_minor1_PCI52','same_host_root_no_BindPaths','original_wall_not_copy_7200_limit'],
        no_native_wholesale_rewrite=True, complete_episode_encoder_integrated=False)
    (root / 'SOURCE.json').write_text(json.dumps(manifest, sort_keys=True, indent=2))
    archive = root / 'SOURCE.tar'
    with tarfile.open(archive, 'x') as handle:
        handle.add(source, arcname='source')
        handle.add(root/'SOURCE.json', arcname='SOURCE.json')
        handle.add(HERE/'r188_recover.py', arcname='recover.py')
    remote = '/localhome/local-rohing/orch_r153_r188_C2_20260917_recovery1'
    with archive.open('rb') as stream:
        subprocess.run(['bash',str(REPO/'gpu/ovx3_ssh.sh'), 'test -f '+remote+'/STOPPED.json && test ! -e '+remote+'/source && tar -xf - -C '+remote], stdin=stream, check=True)
    print(json.dumps(dict(root=str(root),remote=remote,source_manifest_sha256=sha(root/'SOURCE.json'))))


if __name__ == '__main__':
    main()
