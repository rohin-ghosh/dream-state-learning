"""Read-only receipt/cursor adapter and exact new MATH-C parent publication."""

import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

from math_c import HOME, SOURCE, WALL, host, read, require, sha, write

ROOT = HOME / 'life'
OPENING = ("I'm Astra, your new MATH-C parent. This is a new math clone with your saved adapter and masked context, "
    "not the original C2 life. Your actual confined Python environment includes read-only SymPy 1.14.0 and mpmath 1.3.0; "
    "it has no network, GPU, Torch, or home access. We are testing structured THINK: wide to narrow to wide, not one correct way to think. "
    "What mathematical question in your current work deserves an attempt? What do you predict, and what actual tool observation "
    "would distinguish your possibilities? When is acting more useful than more reflection, and what small next action will you choose?")


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(specification)
    sys.modules[name] = loaded
    specification.loader.exec_module(loaded)
    return loaded


def once(name, document):
    path = HOME / (name + '.json')
    if not path.exists():
        write(path, document)


def poll(reference=None):
    sys.path.insert(0, str(SOURCE))
    load('gpu.orch_r127_pilot_transcript', HOME / 'read_transcript.py')
    snapshot = load('math_c_read_snapshot', HOME / 'read_snapshot.py')
    result = snapshot.stored_poll(ROOT, HOME / 'parent_cursor', reference)
    state = result['snapshot']
    records = [read(path) for path in sorted((ROOT / 'stream/records').glob('[0-9]' * 20 + '.json'))]
    cycle = 51
    for record in records:
        if record['index'] < 4:
            continue
        kind, document = record['kind'], record['document']
        evidence = dict(record_index=record['index'], record_sha256=record['sha256'],
            record_mtime=(ROOT / 'stream/records' / f'{record["index"]:020d}.json').stat().st_mtime)
        if kind == 'LOADED':
            once('FIRST_LOADED', dict(evidence, **{key: document.get(key) for key in
                ('pid', 'resume', 'loaded_unix', 'optimizer_steps')}))
        if kind == 'R184_STAGE' and document.get('stage') == 'THINK':
            once('FIRST_THINK', dict(evidence, stage='THINK', structured_think_policy='R202_WIDE_NARROW_WIDE_V1'))
        if kind == 'RESPONSE':
            text = document['response']['raw']
            once('FIRST_GENERATION', dict(evidence, finished_unix=document.get('finished_unix'),
                response_sha256=hashlib.sha256(text.encode()).hexdigest(), response_bytes=len(text.encode())))
        if kind == 'SLEEP_COMPLETE':
            cycle = max(cycle, document['cycle'])
    for label, publication_file in (('ROHIN', 'ROHIN_FIRST_INPUT'), ('PARENT_OPENING', 'PARENT_OPENING')):
        path = HOME / (publication_file + '.json')
        if path.exists():
            publication = read(path)['publication']
            delivered = state['delivered'].get(publication['id'])
            if delivered is not None:
                once(label + '_RENDERED', dict(delivered, publication=publication,
                    observed_unix=time.time(), all_history_tokens_masked=True))
    result.update(completed_cycle=cycle, first_input_rendered=(HOME / 'ROHIN_RENDERED.json').exists(),
        opening_published=(HOME / 'PARENT_OPENING.json').exists(),
        opening_rendered=(HOME / 'PARENT_OPENING_RENDERED.json').exists(),
        withdrawal_closed=(HOME / 'PARENT_WITHDRAWAL_CLOSED.json').exists())
    return result


def publish(message, opening=False):
    require(time.time() < WALL, 'same_wall')
    require((HOME / 'ROHIN_RENDERED.json').exists(), 'actual_Rohin_render_before_parent')
    require(len(message.split()) <= 120 and len(message.encode()) <= 4096, 'style_C_publication_limit')
    if opening:
        require(message == OPENING and not (HOME / 'PARENT_OPENING.json').exists(), 'one_new_parent_opening')
    with (HOME / 'PARENT_PUBLICATION.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        require(not (HOME / 'PARENT_WITHDRAWAL_CLOSED.json').exists(), 'parent_withdrawn_no_late_publication')
        records = [read(path) for path in sorted((ROOT / 'stream/records').glob('[0-9]' * 20 + '.json'))]
        require(not any(record['kind'] == 'SLEEP_REQUEST' and record['document']['cycle'] >= 54
            for record in records), 'no_publications_after_last_guided_sleep_request')
        native = next(record['document'] for record in records if record['kind'] == 'LOADED')
        process = Path('/proc') / str(native['pid'])
        require(process.exists() and os.readlink(process / 'cwd') == str(SOURCE), 'exact_new_clone_live')
        sys.path.insert(0, str(SOURCE))
        from gpu.orch_r127_pilot_console import publish_parent
        publication = publish_parent(str(ROOT), 'Astra', message)
        if opening:
            write(HOME / 'PARENT_OPENING.json', dict(publication=publication, message=message,
                parent_style='C_QUESTIONS_ONLY_SELF_DERIVATION', published_unix=time.time(),
                status='NEW_PARENT_OPENING_PUBLISHED_NOT_YET_RENDERED', operator_intro_not_model_generation=True))
        return publication


if __name__ == '__main__':
    host()
    request = json.loads(sys.stdin.read())
    if request['op'] == 'poll':
        result = poll(request.get('reference'))
    elif request['op'] == 'opening':
        result = publish(OPENING, opening=True)
    elif request['op'] == 'publish':
        result = publish(request['message'])
    else:
        raise ValueError('known_parent_operation')
    print(json.dumps(result))
