"""Bind P3's existing parent to the public tolerant caption environment only."""

import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

import parent_c as base


def run():
    output = base.OWN / 'r210_parent3'
    receipt = output / 'R213_TOLERANT_CAPTION_BOUND.json'
    if receipt.exists():
        print(receipt.read_text(), flush=True)
        return
    environment_path = base.OWN / 'CHILD_ENVIRONMENT_R213.json'
    environment = base.read(environment_path)
    assert set(environment) == {'policy', 'scenes', 'help', 'scoring'}
    assert 'rank <= 50 of 65' in environment['scoring'] and 'humour' in environment['help']
    started = base.read(sorted(output.glob('STARTED_*.json'))[-1])
    process = Path('/proc', str(started['pid']))
    arguments = (process / 'cmdline').read_bytes().decode().strip('\0').split('\0')
    assert arguments[-4:] == [str(base.OWN / 'r210_parent.py'), 'serve', '--physical', '3']
    assert not [path for path in (output / 'turns').glob('*/DISPATCH_INTENT.json')
        if not (path.parent / 'RESULT.json').exists()], 'preserve_unfinished_parent_call'
    ticks = (process / 'stat').read_text().rsplit(') ', 1)[1].split()[19]
    descriptor = os.pidfd_open(started['pid'])
    try:
        assert (process / 'stat').read_text().rsplit(') ', 1)[1].split()[19] == ticks
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        poller = select.poll()
        poller.register(descriptor, select.POLLIN)
        assert poller.poll(5000), 'exact_parent_exited'
    finally:
        os.close(descriptor)
    archive = output / ('R213_REBIND_' + str(time.time_ns()))
    archive.mkdir()
    config = base.read(output / 'CONFIG.json')
    (output / 'CONFIG.json').rename(archive / 'CONFIG_ORIGINAL.json')
    programme = output / 'PROGRAMME_R213_CAPTION.txt'
    with programme.open('x') as stream:
        stream.write(
            'NEW R213 HUMOUR caption-game phase after the preserved prior guided/withdrawn screen. '
            'Respond only to this exact child and the public environment below. No inherited V, mathematics '
            'homework, original C2 story test, private judge references, base-comparison results, or invented tools. '
            'The task is a HUMOUR contest against human captions: seek distinct accepted joke ideas over tokens, '
            'not scene descriptions, acceptance rate, or one best score. The rule is rank at most 50 of 65 plus '
            'relevance and novelty; only actual attributed Tool feedback establishes a result. '
            'Formatting is NEVER an acceptance gate. Missing Caption prefixes recover literal ACT lines and '
            'Count follows actual caption lines; format faults are diagnostics only. THINK candidates are not '
            'submissions. Recommend clear Scene, Direction, Count and Caption lines as a convenience, not a '
            'condition of scientific acceptance. Feedback arrives before LEARN. Keep the same style-B walkthrough '
            'and 160-word limit, exact child RESPONSE hashes/quotes and frozen validators. Keep next_task null '
            'and continuity absent for continue; do not invent child choices or set_aside evidence. '
            'Rohin console is genuine and separate. No messages to isolated P7. Public CHILD_ENVIRONMENT:\n'
            + json.dumps(environment, ensure_ascii=False))
    config.update(source_root=config['root'].removesuffix('/life') + '/r212/source',
        branch='R213_CAPTION_HUMOUR_B', programme_path=str(programme), programme_sha256=base.sha(programme))
    base.write(output / 'CONFIG.json', config)
    with (output / 'OPERATOR.log').open('a') as log:
        parent = subprocess.Popen([sys.executable, '-B', str(base.OWN / 'r210_parent.py'), 'serve', '--physical', '3'],
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    base.write(receipt, dict(parent_pid=parent.pid, previous_parent_pid=started['pid'],
        previous_start_ticks=ticks, bound_unix=time.time(), config_sha256=base.sha(output / 'CONFIG.json'),
        public_environment_path=str(environment_path), public_environment_sha256=base.sha(environment_path),
        child_signals=[], private_references_read=False, historical_turns_preserved=True))
    print(receipt.read_text(), flush=True)


if __name__ == '__main__':
    run()
