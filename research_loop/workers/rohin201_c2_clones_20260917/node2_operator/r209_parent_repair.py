"""Finite, explicitly operator-authored parent reattachment after the preserved screen."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


BASE = Path('/localhome/local-rohing/orch_r153_r201_node2_clones_20260917_operator1')
REFERENCE_SHA = '3d0d9dc7fbdefc7ccc24c2625b56b05a6a8c07baea41e3753038813f86da541d'
ARMS = {'math_d1', 'repo_c1', 'creative_d1', 'math_transfer_c1'}


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)


def opener(arm):
    common = ('I am Astra, your parent in this environment, not Rohin. I am reattaching with a new '
        'operator-authored opening after the earlier screen. Preserve V as historical and unresolved; '
        'do not erase it or pretend a new task resolves it. Let us choose a fresh working object and '
        'keep claims tied to observations. ')
    tasks = {
        'math_d1': 'Choose a small new mathematical claim, predict one check, and use the actual math sandbox output to decide your next step. What would distinguish a true result from an unsupported assertion?',
        'repo_c1': 'Choose a fresh concrete question about the visible repository. Read the relevant code and distinguish the actual returned file text and receipt from a claim that the tool ran. What would one real observation let you establish?',
        'creative_d1': 'The earlier statement that this was reviewed with Rohin is unsupported; I have not verified such a review. My feedback here is from Astra, not Rohin. Choose a new small creative object of your own, try one revision, and explain what you notice; there is no hidden creative test or claimed human review.',
        'math_transfer_c1': 'Which new modular-arithmetic or divisibility puzzle would you like to investigate? What prediction could you check with the real sandbox, and what would the returned result change?'
    }
    return common + tasks[arm]


def active(plan, control):
    for process in Path('/proc').glob('[0-9]*'):
        try:
            arguments = (process / 'cmdline').read_bytes().decode().split('\0')
            fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
            if ('gpu.orch_r125_continual_guard' in arguments and 'native' in arguments
                    and str(control / 'GUARD.json') in arguments and fields[0] not in ['Z', 'X']
                    and os.readlink(process / 'cwd') == plan['source_root']):
                return int(process.name)
        except (OSError, UnicodeDecodeError):
            continue
    return None


def main(arm):
    os.umask(0o077)
    root = BASE / arm
    control = root / 'r206_phase2_withdrawn_20260918/control'
    plan = json.loads((control / 'PLAN.json').read_bytes())
    reference = (Path(__file__).parent / 'ROHIN_C2_CONVERSATION_2026-09-17.md').read_bytes()
    if hashlib.sha256(reference).hexdigest() != REFERENCE_SHA or len(reference) != 17358:
        raise ValueError('full_clean_reference_required')
    output = root / 'r209_parent_reattachment_20260918'
    output.mkdir(mode=0o700)
    sys.path.insert(0, plan['source_root'])
    from gpu.orch_r127_pilot_console import publish_parent
    write(output / 'STARTED.json', dict(pid=os.getpid(), started_unix=time.time(), arm=arm,
        phase='R209_PARENT_REATTACHED_NOT_PARENT_WITHDRAWN_FROM_FIRST_NEW_INBOX',
        treatment='FINITE_OPERATOR_AUTHORED_SPARSE_PARENT_NOT_ADAPTIVE_EXTERNAL_MODEL',
        full_clean_reference_read=True, reference_sha256=REFERENCE_SHA, reference_bytes=len(reference),
        original_screen_52_through_57_preserved=True, V_retained_unresolved=True,
        no_peer_messages=True, no_creative_test=True, no_new_Rohin_attribution=True,
        maximum_publications=3, pending_async_generation=0))
    waiting = []
    rendered = set()
    seen = set()
    publications = 0
    initial_complete = None
    latest_complete = None
    deadline = min(plan['hard_end_unix'] - 60, time.time() + 2400)
    while time.time() < deadline:
        native = active(plan, control)
        if (control / 'OUTER_FAILED.json').exists():
            break
        for path in sorted((root / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))[-100:]:
            if path.name in seen:
                continue
            seen.add(path.name)
            record = json.loads(path.read_bytes())
            if record['index'] <= 5846:
                continue
            if record['kind'] == 'SLEEP_COMPLETE':
                latest_complete = record['document']['cycle']
            if record['kind'] != 'REQUEST':
                continue
            for message in waiting:
                if message['id'] in rendered:
                    continue
                if any(message['text'] in item.get('content', '') for item in record['document']['messages']):
                    write(output / ('RENDERED_' + message['id'] + '.json'), dict(id=message['id'],
                        request_index=record['index'], request_sha256=record['sha256'], observed_unix=time.time(),
                        all_history_tokens_masked=record['document'].get('render_receipt', {}).get('all_history_tokens_masked'),
                        exact_text_rendered=True, message_sha256=hashlib.sha256(message['text'].encode()).hexdigest()))
                    rendered.add(message['id'])
        due = publications == 0 or (initial_complete is not None and latest_complete is not None
            and latest_complete >= initial_complete + publications)
        if native and due and publications < 3 and all(message['id'] in rendered for message in waiting):
            text = opener(arm) if publications == 0 else (
                'Astra here. For your new working object, what did the actual last observation establish, '
                'what remains unresolved, and what is the smallest next check or revision? Keep historical V '
                'separate and do not attribute my words to Rohin or invent human review.')
            if arm == 'math_transfer_c1' and publications:
                text = 'Which actual sandbox observation supports your new claim, what remains unresolved, and what small divisibility check would you try next?'
            publication = publish_parent(root / 'raw', 'Astra', text)
            write(output / f'PUBLICATION_{publications}.json', dict(publication=publication, published_unix=time.time(),
                native_pid=native, after_complete=latest_complete, text=text, phase='R209_PARENT_REATTACHED', rendered=False))
            waiting.append(dict(id=publication['id'], text=text))
            publications += 1
            if initial_complete is None:
                initial_complete = latest_complete
        if publications == 3 and len(rendered) == 3:
            break
        if (control / 'EXIT.json').exists() and not native:
            break
        time.sleep(2)
    write(output / 'EXIT.json', dict(finished_unix=time.time(), publications=publications,
        rendered_ids=sorted(rendered), pending_automatic_guidance=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', choices=sorted(ARMS), required=True)
    main(parser.parse_args().arm)
