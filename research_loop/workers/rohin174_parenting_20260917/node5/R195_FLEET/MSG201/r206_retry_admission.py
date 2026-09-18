"""Fresh launch attempt after R206 failed admission before native startup."""

import importlib.util
from pathlib import Path
import os
import select
import shutil
import signal
import stat
import subprocess
import time


FAILED = Path('/localhome/local-rohing/orch_r206_C2_20260918_resume1')
ROOT = Path('/localhome/local-rohing/orch_r206_C2_20260918_resume2')
specification = importlib.util.spec_from_file_location('receiver', FAILED / 'r206_resume_original.py')
receiver = importlib.util.module_from_spec(specification)
specification.loader.exec_module(receiver)
receiver.ROOT = ROOT
saved = receiver.saved


def main():
    saved.require(saved.read(FAILED / 'control/OUTER_FAILED.json')['error'] == 'fresh_privileged_target_clear',
        'only_admission_failure_before_native')
    saved.require(not (FAILED / 'control/LAUNCH.json').exists(), 'no_failed_attempt_native')
    pause = saved.read(receiver.BOUNDARY / 'PAUSED.json')
    saved.require(saved.reference(receiver.records()[-1]) == pause['exact_head'], 'same_saved57_head')
    if ROOT.exists():
        saved.require(saved.read(ROOT / 'RETRY_AUTHORITY.json')['failed_attempt'] == str(FAILED)
            and not (ROOT / 'bridge.log').exists() and not (ROOT / 'supervisor.log').exists()
            and not (ROOT / 'control/OUTER_STARTED.json').exists(), 'only_staged_socket_recovery')
    else:
        ROOT.mkdir(mode=0o700)
        shutil.copytree(FAILED / 'main_ready', ROOT / 'main_ready')
        receiver.stage()
        saved.write(ROOT / 'RETRY_AUTHORITY.json', dict(observed_unix=time.time(),
            authority='Rohin206 same-life deployment; fresh admission attempt after no native launched',
            failed_attempt=str(FAILED), prior_failure=saved.reference(FAILED / 'control/OUTER_FAILED.json'),
            same_preserved_boundary=str(receiver.BOUNDARY), no_check_relaxed=True, human_inbox_writes=0))
    if Path('/proc/3253449').exists():
        bridge = saved.identity(3253449)
        saved.require(bridge['start_ticks'] == '24030672' and bridge['cwd'] == str(FAILED / 'source')
            and bridge['argv'][-1] == str(FAILED / 'BRIDGE.json'), 'exact_failed_attempt_bridge')
        descriptor = os.pidfd_open(bridge['pid'])
        saved.same(bridge)
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        saved.require(bool(select.select([descriptor], [], [], 10)[0]), 'failed_bridge_exited')
        os.close(descriptor)
    bridge_config = saved.read(ROOT / 'BRIDGE.json')
    socket_path = Path(bridge_config['socket'])
    if socket_path.exists():
        metadata = socket_path.lstat()
        saved.require(str(socket_path) == saved.read(FAILED / 'BRIDGE.json')['socket']
            and str(socket_path) == '/tmp/r206_node5_c2_resume1.sock'
            and stat.S_ISSOCK(metadata.st_mode) and metadata.st_uid == os.getuid()
            and not Path('/proc/3253449').exists(), 'exact_stale_socket_after_owner_exit')
        socket_path.unlink()
        saved.write(ROOT / 'STALE_SOCKET_REMOVED.json', dict(observed_unix=time.time(),
            path=str(socket_path), inode=metadata.st_ino, device=metadata.st_dev,
            old_bridge_pid=3253449, owner_exited=True, no_native_launched=True))
    processes = {}
    for name, command in (
        ('bridge', [receiver.PYTHON, '-B', str(ROOT / 'math_bridge.py'), '--config', str(ROOT / 'BRIDGE.json')]),
        ('supervisor', [receiver.PYTHON, '-B', '-m', 'gpu.r188_node5_confinement', 'dispatch',
            '--config', str(ROOT / 'control/GUARD.json')]),
    ):
        with (ROOT / (name + '.log')).open('x') as log:
            process = subprocess.Popen(command, cwd=ROOT / 'source', env=receiver.environment(),
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        processes[name] = saved.identity(process.pid)
        if name == 'bridge':
            deadline = time.monotonic() + 20
            while not list((ROOT / 'bridge_receipts').glob('READY*')):
                saved.require(process.poll() is None and time.monotonic() < deadline, 'new_bridge_ready')
                time.sleep(.1)
    saved.write(ROOT / 'STARTED.json', dict(observed_unix=time.time(), processes=processes,
        source_cycle=57, complete_index=6365, optimizer_steps=5212, loaded=False,
        same_root=str(receiver.LIFE), pinned_messages_policy='R206_VERBATIM_ROHIN_MESSAGES_V1',
        console_reply_policy='R205_CONSOLE_REPLY_ACT_V1', human_inbox_writes=0, same_parent_untouched=True))
    print('R206_FRESH_ADMISSION_ATTEMPT_STARTED', flush=True)


if __name__ == '__main__':
    main()
