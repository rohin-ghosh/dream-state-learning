"""Active, source-bound math parenting for C0; never signals a learner."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


PROBLEMS = (
    'Find a formula for the sum of the first n positive odd numbers. Start with three small cases, then explain why the pattern holds.',
    'Find the sum 1+2+...+n by pairing terms. State what changes when n is odd and check a new case.',
    'Decide whether n squared minus n is always even for integer n. Give a reason and include a negative-integer example.',
    'Study the difference between consecutive square numbers. Derive an identity and test it without code.',
)


def prompt(turn):
    opening = ('I am Astra, your new parent for this math-games life. Your name is C0. '
        'You inherit C2 snapshot51; you are not the continuing original C2. We are moving '
        'on from the old V investigation to a new object. ' if turn == 0 else '')
    task = PROBLEMS[(turn // 2) % len(PROBLEMS)]
    question = ('Show a worked attempt in prose now, rather than a promise to understand. '
        if turn % 2 == 0 else 'This is the second turn on this object: show the actual calculation or argument, '
        'then choose whether the evidence warrants keeping it. After this turn move to a new problem; '
        'do not repeat an unchanged failed approach. ')
    return opening + task + ' ' + question + (
        'Use English and check your output language. A hand calculation is allowed; '
        'no code executor is connected, so do not claim a tool result. Judge your last attempt '
        'in one line and write the next mathematical artifact itself. Your pinned transcript '
        'is a historical reference. Only your eligible own words train; promises and '
        'unsupported completion claims are not artifacts. You may disagree with my suggestion '
        'or choose another small mathematical question; explain the quitting point concretely.')


def main(root):
    sys.path.insert(0, str(root / 'source'))
    from gpu.orch_r127_pilot_console import _inbox
    plan = json.loads((root / 'control/PLAN.json').read_text())
    output = root / 'parent_receipts'
    output.mkdir(exist_ok=True)
    turn, seen = 0, set()
    while time.time() < plan['hard_end_unix'] - 60:
        candidates = sorted((root / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))
        trigger = None
        for path in reversed(candidates):
            if path.name in seen:
                break
            record = json.loads(path.read_text())
            if record['kind'] in ('R184_ACT', 'R184_CONSOLE_REPLY'):
                trigger = path
                break
        if turn == 0 or trigger is not None:
            text = prompt(turn)
            publication = _inbox(root / 'raw', 'Astra', text, None)
            receipt = dict(turn=turn, publication=publication, published_unix=time.time(),
                trigger_path=str(trigger) if trigger else None,
                trigger_sha256=hashlib.sha256(trigger.read_bytes()).hexdigest() if trigger else None,
                own_words_only=True, parent_is_operator_authored=True, learner_signals=0)
            (output / f'{turn:06d}.json').write_text(json.dumps(receipt, indent=2, sort_keys=True))
            seen.update(path.name for path in candidates)
            turn += 1
        time.sleep(3)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    main(parser.parse_args().root)
