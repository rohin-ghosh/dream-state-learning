"""Correct the known pre-native containment-unit name, without replaying work."""

from copy import deepcopy
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time
import uuid

from recover_support_identity import helpers, read, require, sha, write, PYTHON, BASE


def main():
    root = BASE / 'r188/lane2'
    failed = root / 'control'
    config = read(failed / 'GUARD.json')
    plan = read(config['plan_path'])
    require(plan['physical'] == 2 and plan['rehearsal_presentations'] == 0, 'only_replay_R188_recovery')
    require('ValueError: unique_probe_unit' in (root / 'SUPERVISOR.log').read_text(), 'exact_pre_native_unit_rejection')
    require(not any((failed / name).exists() for name in ('LAUNCH.json', 'NATIVE.log', 'CONTAINED_COMMAND.json')), 'known_no_native_publication_or_load')
    require(read(failed / 'ADMISSION.json')['clear'] is True, 'original_device_admission_passed')
    restored = read(root / 'RESTORED.json')
    base = helpers()
    boundary = base.sleep_boundary(plan['root'])
    require(boundary is not None and boundary['record_sha256'] == restored['complete_sha256'], 'still_exact_restored_complete42')
    control = root / 'control_unit_fixed'
    control.mkdir()
    updated = deepcopy(config)
    updated['attempt_dir'] = str(control)
    updated['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    write(control / 'GUARD.json', updated)
    source = Path(plan['source_root'])
    env = dict(os.environ, PYTHONPATH=str(source), CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
    code = ('from gpu.orch_r125_continual_guard import validate; from gpu.orch_r136_node1_launcher import device_containment_command;'
        'import sys;config,plan=validate(sys.argv[1]);p=config["device_containment"];'
        'device_containment_command(plan["physical"],p["minor"],p["uid"],p["gid"],p["unit"],plan["source_root"],[sys.executable,"-B","-c","pass"],10);print("ACTUAL_CONTAINMENT_COMMAND_PASS")')
    result = subprocess.run([PYTHON, '-B', '-c', code, str(control / 'GUARD.json')], cwd=source, env=env, capture_output=True, text=True, timeout=90)
    write(root / 'UNIT_COMMAND_CPU.json', dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr))
    require(result.returncode == 0, 'actual_containment_command_not_guessed')
    write(root / 'UNIT_REPAIR.json', dict(reason='pre-native unique_probe_unit rejection; correct orch-r136-native namespace',
        old_guard_sha256=sha(failed / 'GUARD.json'), new_guard_sha256=sha(control / 'GUARD.json'),
        plan_unchanged=True, source_unchanged=True, checkpoint_unchanged=True, no_extra_discard=True, observed_unix=time.time()))
    with (root / 'UNIT_FIXED_SUPERVISOR.log').open('xb') as log:
        process = subprocess.Popen([PYTHON, '-B', '-m', 'gpu.orch_r136_node1_launcher', 'contained-supervise', '--config', str(control / 'GUARD.json')],
            cwd=source, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    write(root / 'UNIT_FIXED_DISPATCHED.json', dict(supervisor_pid=process.pid, observed_unix=time.time(), no_retry=True))
    print(json.dumps(dict(status='SAME_SAVED42_UNIT_CORRECTED_DISPATCHED', supervisor_pid=process.pid)), flush=True)


if __name__ == '__main__':
    require(os.getuid() == 1395 and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'owned_CPU_only')
    descriptor = os.open(BASE / 'lane2.lock', os.O_RDWR | os.O_NOFOLLOW)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        main()
    finally:
        os.close(descriptor)
