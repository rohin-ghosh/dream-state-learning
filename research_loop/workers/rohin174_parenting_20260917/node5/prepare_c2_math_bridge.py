"""Write a new original-C2 phase binding; preparation does not signal or route."""

import argparse
import json
import os
from pathlib import Path
import time

import c2_math_bridge_phase as phase


def prepare(root):
    phase.require(root.parent == Path('/localhome/local-rohing')
                  and root.name == 'orch_r153_r188_C2_math_env_20260917_phase1', 'owned_phase_root')
    phase.require(not (root / 'BRIDGE.json').exists(), 'fresh_phase_binding')
    preservation = json.loads((root / 'PRESERVATION.json').read_bytes())
    candidate = Path(phase.CANDIDATE)
    control = Path(phase.CONTROL)
    old = json.loads((control / 'BRIDGE.json').read_bytes())
    pins = {
        str(root / 'c2_math_bridge_phase.py'): phase.sha(root / 'c2_math_bridge_phase.py'),
        str(candidate / 'CANDIDATE.json'): '04f188ca9df5bf602ba02c5b355561e85efb247e5f851b2a8de3c61935538f76',
        str(candidate / 'RESULT.json'): '1cabe76f2e851fd9eb381bf0e36598566ff76424965d35b80cf8d1275c06fbbd',
        str(candidate / 'MATH_BUNDLE.json'): '38381e95b6d810e8fb40a1e3466a747e54673f2c205cf757efd029e624fe686d',
        str(candidate / 'source/gpu/orch_r125_cpu_confinement_probe.py'): '81408d62fb926f4c61411084c56a7e08db842095dfc2b0d354b9b1cd95caa474',
        str(control / 'source/gpu/r184_cpu_bridge.py'): '43e2c8f4f1bf68b4613d508fd25db97f37f843cfd8ba1e93e8e2d3c154ac7a69',
        str(control / 'source/gpu/orch_r153_community_transport.py'): 'b798199a10508164de724631fc8a81bf28fb3500db5bc0048ec486cb7707905a',
    }
    preserved = {value['path']: value['sha256'] for value in preservation['preserved'].values()}
    preserved.update({item['file']['path']: item['file']['sha256'] for item in preservation['window_records']})
    for relative in ('control/PLAN.json', 'control/GUARD.json'):
        preserved[str(control / relative)] = phase.sha(control / relative)
    source_manifest = json.loads((candidate / 'CANDIDATE.json').read_bytes())
    for relative, expected in source_manifest['source_files'].items():
        preserved[str(control / 'source' / relative)] = (
            source_manifest['original_profile_sha256'] if relative == 'gpu/orch_r125_cpu_confinement_probe.py' else expected)
    pins.update(preserved)
    owners = {name: phase.identity(pid) for name, pid in
              (('native', 2718196), ('supervisor', 2718170), ('old_bridge', 2718169))}
    phase.require(owners['native']['start'] == 22275637 and owners['supervisor']['start'] == 22275473
                  and owners['old_bridge']['start'] == 22275473, 'original_process_start_pins')
    phase.require(all(owner['uid'] == ['2524'] * 4 and owner['cwd'] == phase.CONTROL + '/source'
                      for owner in owners.values()), 'original_identity_scope')
    phase.require(owners['old_bridge']['argv'] == ['/localhome/local-rohing/v2/venv/bin/python', '-B', '-m',
                  'gpu.r184_cpu_bridge', '--config', phase.CONTROL + '/BRIDGE.json']
                  and owners['old_bridge']['sigcgt'] == '0000000000000002', 'passive_old_CPU_bridge_only')
    socket_stat = os.lstat(old['socket'])
    socket_lines = [line.split() for line in Path('/proc/net/unix').read_text().splitlines()
                    if line.split()[-1] == old['socket'] and line.split()[3] == '00010000']
    phase.require(len(socket_lines) == 1, 'unique_original_listener')
    config = dict(old, phase=phase.PHASE, source=str(candidate / 'source'),
                  gate_root=str(candidate / 'gate'),
                  gate_sha256='c7821ed5b02651ed624c6dbe29a488bd15496440b59364e98e52ff2afe705e82',
                  old_config=str(control / 'BRIDGE.json'), pins=pins, preserved_pins=preserved,
                  old_socket_inode=int(socket_lines[0][6]), socket_stat=[socket_stat.st_dev, socket_stat.st_ino],
                  temporary_socket='/tmp/r188_c2_math_env_phase1.sock',
                  created_unix=time.time(), pure_matched_arm_result=False, **owners)
    phase.preflight(config)
    with (root / 'BRIDGE.json').open('x') as stream:
        json.dump(config, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(root / 'BRIDGE.json', 0o444)
    print(json.dumps(dict(status='PREFLIGHT_READY_NO_LIVE_CHANGE', config=str(root / 'BRIDGE.json'),
                          config_sha256=phase.sha(root / 'BRIDGE.json'), owners=owners,
                          preserved_files=len(preserved), helper_sha256=phase.sha(root / 'c2_math_bridge_phase.py'))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    prepare(parser.parse_args().root)
