"""Rebind only MATH-C's parent and publish the authorized quitting-judgment turn."""

import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

import parent_c as base
from r210_parent import remote


def run():
    output = base.OWN / 'r210_parent6'
    receipt = output / 'R213_QUITTING_JUDGMENT.json'
    if receipt.exists():
        print(receipt.read_text(), flush=True)
        return
    started = base.read(sorted(output.glob('STARTED_*.json'))[-1])
    process = Path('/proc', str(started['pid']))
    arguments = (process / 'cmdline').read_bytes().decode().strip('\0').split('\0')
    expected = [str(base.OWN / 'r210_parent.py'), 'serve', '--physical', '6']
    assert arguments[-4:] == expected, 'exact_owned_MATH_C_parent'
    assert not [path for path in (output / 'turns').glob('*/DISPATCH_INTENT.json')
        if not (path.parent / 'RESULT.json').exists()], 'preserve_unfinished_provider_call'
    identity = dict(pid=started['pid'], start_ticks=(process / 'stat').read_text().rsplit(') ', 1)[1].split()[19],
        arguments=arguments)
    archive = output / ('R213_REBIND_' + str(time.time_ns()))
    archive.mkdir()
    old_config = base.read(output / 'CONFIG.json')
    base.write(archive / 'CONFIG.json', old_config)
    base.write(archive / 'PARENT_IDENTITY.json', identity)
    descriptor = os.pidfd_open(started['pid'])
    try:
        assert (process / 'stat').read_text().rsplit(') ', 1)[1].split()[19] == identity['start_ticks']
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        poller = select.poll()
        poller.register(descriptor, select.POLLIN)
        assert poller.poll(5000), 'exact_parent_exited'
    finally:
        os.close(descriptor)
    programme = base.OWN / 'R213_MATH_PROGRAMME.txt'
    config = dict(old_config, programme_path=str(programme), programme_sha256=base.sha(programme))
    (output / 'CONFIG.json').rename(archive / 'CONFIG_ORIGINAL.json')
    base.write(output / 'CONFIG.json', config)
    message = (base.OWN / 'R213_MATH_QUITTING_PARENT.txt').read_text().strip()
    assert len(message.split()) <= 120
    publication = remote(6, dict(op='publish', message=message))
    with (output / 'OPERATOR.log').open('a') as log:
        parent = subprocess.Popen([sys.executable, '-B', str(base.OWN / 'r210_parent.py'), 'serve', '--physical', '6'],
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    base.write(receipt, dict(publication=publication, published_unix=time.time(), new_parent_pid=parent.pid,
        previous_parent=identity, prior_config=str(archive / 'CONFIG_ORIGINAL.json'),
        config_sha256=base.sha(output / 'CONFIG.json'), message=message,
        operator_authored_parent_turn=True, child_signals=[], new_task_assigned=False,
        previous_V_claim='UNRESOLVED_NOT_SOLVED', child_rendered=False))
    print(receipt.read_text(), flush=True)


if __name__ == '__main__':
    run()
