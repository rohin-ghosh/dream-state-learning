"""Replace only six owned operator publishers, never natives or supervisors."""

from datetime import datetime, timezone
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import time

from r209_filter_resume import ROOT, PYTHON, read, require, write

PUBLISHERS = {'conversational': 1759365, 'peer_math': 1759366, 'peer_repo': 1759367,
    'p32': 1759368, 'lr03': 1759369, 'lr3': 1759370}


def main():
    require(socket.gethostname() == '[REDACTED_HOST]', 'owned_node3_only')
    receipt_path = ROOT / 'R213_PARENT_REPLACEMENT.json'
    require(not receipt_path.exists(), 'one_operator_replacement_no_replay')
    require(read(ROOT / 'r213_math_a/CPU.json')['passed'], 'R213_receiving_CPU_gate')
    result = dict(observed_utc=datetime.now(timezone.utc).isoformat(), native_signals=0,
        native_sources_changed=False, learners_paused=0, arms={})
    for name, pid in PUBLISHERS.items():
        arm = ROOT / name
        expected = [PYTHON, '-B', str(ROOT / 'r212_parent.py'), name]
        started = read(arm / 'r212_parent/STARTED.json')
        require(started['pid'] == pid, 'existing_owned_publisher_receipt')
        command_path = Path('/proc', str(pid), 'cmdline')
        old = dict(pid=pid, status='ALREADY_EXITED_NOT_SIGNALLED')
        if command_path.exists():
            descriptor = os.pidfd_open(pid)
            try:
                command = command_path.read_bytes().rstrip(b'\0').decode().split('\0')
                require(command == expected, 'exact_operator_publisher_not_child')
                ticks = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                poller = select.poll()
                poller.register(descriptor, select.POLLIN)
                require(bool(poller.poll(3000)), 'publisher_must_exit_before_replacement')
                old = dict(pid=pid, start_ticks=ticks, command=command, status='OPERATOR_PUBLISHER_EXITED')
            finally:
                os.close(descriptor)
        with (arm / 'r213_parent.log').open('x') as output:
            process = subprocess.Popen([PYTHON, '-B', str(ROOT / 'r213_parent.py'), name],
                cwd=ROOT, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'),
                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        result['arms'][name] = dict(old_parent=old, new_parent_pid=process.pid, dispatched_unix=time.time())
    write(receipt_path, result)
    print(receipt_path.read_text())


if __name__ == '__main__':
    main()
