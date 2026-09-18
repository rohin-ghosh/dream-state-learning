"""Deliver the explicitly requested creative parent answer; preserve all prior turns."""

import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import parent_c as base
from r210_parent import remote


def run():
    output = base.OWN / 'r210_parent7'
    started = base.read(sorted(output.glob('STARTED_*.json'))[-1])
    process = Path('/proc', str(started['pid']))
    if process.exists():
        expected = [str(base.OWN / 'r210_parent.py'), 'serve', '--physical', '7']
        arguments = (process / 'cmdline').read_bytes().decode().strip('\0').split('\0')
        assert arguments[-4:] == expected
        assert not list((output / 'turns').glob('*/DISPATCH_INTENT.json')), 'no_provider_call_interrupted'
        descriptor = os.pidfd_open(started['pid'])
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        os.close(descriptor)
        time.sleep(.2)
    old_config = base.read(output / 'CONFIG.json')
    base.write(output / 'CONFIG_BEFORE_CREATIVE_ANSWER.json', old_config)
    programme = output / 'PROGRAMME_CREATIVE_ANSWER.txt'
    programme.write_text(
        'R210 CREATIVE-OPEN-C enrichment, NOT mathematics. No more V or inherited formula prompting. '
        'The child asked what format and tasks Astra works with; the operator has answered honestly via '
        'an attributed Astra inbox: own plain-English turns and actual tool feedback. '
        'Concrete new object: a three-line dialogue between a lighthouse and the fog, distinct desires, '
        'last line reframes the first. Respond promptly to the actual draft with specific attentive feedback '
        'or a useful creative question. Do not leave an unanswered ask-Astra affordance. '
        'Do not claim a message was read unless its actual render is present. '
        'This phase preserves the ended guided/withdrawn screen, history, and genuine Rohin console channel. '
        'No sealed or private judge information, no original C2 story-test replay. '
        'Actual attributed turns only. Own prose English, no fabricated tool or LoRA-change claims. '
        'Keep existing strict child RESPONSE index/hash/quote evidence and parent style validators. '
        'For disposition continue, next_task is null and continuity absent; put creative feedback in message.')
    config = dict(old_config, programme_path=str(programme), programme_sha256=base.sha(programme))
    (output / 'CONFIG.json').rename(output / 'CONFIG_ORIGINAL_R210.json')
    base.write(output / 'CONFIG.json', config)
    message = (base.OWN / 'R210_CREATIVE_PARENT.txt').read_text().strip()
    assert len(message.split()) <= 120
    publication = remote(7, dict(op='publish', message=message))
    base.write(output / 'CREATIVE_ANSWER.json', dict(publication=publication, message=message,
        observed_unix=time.time(), operator_parent_not_model_generation=True, no_private_judge_text=True))
    with (output / 'OPERATOR.log').open('a') as log:
        parent = subprocess.Popen([sys.executable, '-B', str(base.OWN / 'r210_parent.py'), 'serve', '--physical', '7'],
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    print('CREATIVE_PARENT_ANSWER_PUBLISHED', publication['id'], 'ATTACHED_PARENT_PID', parent.pid, flush=True)


if __name__ == '__main__':
    run()
