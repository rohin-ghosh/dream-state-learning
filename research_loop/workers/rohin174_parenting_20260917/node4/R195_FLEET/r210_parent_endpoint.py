"""R210 parent transport, separate from the preserved withdrawn screen."""

import fcntl
import json
import os
from pathlib import Path
import sys
import time

from math_c import HOME, WALL, host, read, require, sha, write
from parent_endpoint import load
from r206_handoff import records, root_for


def configure(physical):
    require(physical in (2, 3, 5, 6, 7), 'only_R210_clone_parents')
    root = root_for(physical)
    target = root / 'r210'
    source = target / 'source'
    if physical == 7 and (root / 'r224_language_v3/DISPATCHED.json').exists():
        current = root / 'r224_language_v3'
        require(read(current / 'DISPATCHED.json')['new_phase'] == 'R224_P7_LANGUAGE_POLICY', 'exact_P7_language_phase')
        require(sha(current / 'control/GUARD.json') == read(current / 'RECEIVING_READY.json')['guard_sha256'],
            'exact_P7_language_receiving_guard')
        source = current / 'source'
    if physical == 3 and (root / 'r212/DISPATCHED.json').exists():
        current = root / 'r212'
        require(read(current / 'DISPATCHED.json')['new_phase'] == 'R212_CAPTION_HUMOUR', 'exact_P3_caption_phase')
        require(sha(current / 'control/GUARD.json') == read(current / 'RECEIVING_READY.json')['guard_sha256'],
            'exact_P3_receiving_guard')
        source = current / 'source'
    require(read(target / 'DISPATCHED.json')['new_phase'] == 'R210_ENRICHMENT', 'separate_authorized_phase')
    sys.path.insert(0, str(source))
    load('gpu.orch_r127_pilot_transcript', HOME / 'read_transcript.py')
    return root, target, source


def poll(physical, reference=None):
    root, target, source = configure(physical)
    snapshot = load('r210_read_snapshot', HOME / 'read_snapshot.py')
    if physical in (2, 3, 5, 6):
        reference = resume_verified_cursor(root, target, reference)
    result = snapshot.stored_poll(root / 'life', target / 'parent_cursor', reference)
    frontier = read(target / 'PRESERVED.json')['last_record_index']
    current = [entry for entry in records(root) if entry['index'] > frontier]
    receipts = []
    for entry in current:
        if entry['kind'] in ('LOADED', 'R184_STAGE', 'R205_CONSOLE_REPLY'):
            document = entry['document']
            receipts.append(dict(index=entry['index'], sha256=entry['sha256'], kind=entry['kind'],
                mtime=(root / 'life/stream/records' / f'{entry["index"]:020d}.json').stat().st_mtime,
                document={key: document[key] for key in ('pid', 'loaded_unix', 'resume', 'optimizer_steps',
                    'stage', 'segment', 'source_inbox_events', 'response_origin', 'source_sha256', 'outcome') if key in document}))
    opening = target / 'PARENT_OPENING.json'
    publication = read(opening)['publication'] if opening.exists() else None
    delivered = result['snapshot']['delivered'].get(publication['id']) if publication else None
    if delivered and not (target / 'PARENT_OPENING_RENDERED.json').exists():
        write(target / 'PARENT_OPENING_RENDERED.json', dict(publication=publication, delivered=delivered,
            observed_unix=time.time(), new_phase='R210_ENRICHMENT'))
    result.update(receipts=receipts, opening_published=publication is not None, opening_rendered=delivered,
        console_replied=any(entry['kind'] == 'R205_CONSOLE_REPLY' for entry in current))
    return result


def resume_verified_cursor(root, target, reference):
    marker = target / 'R230_BOOTSTRAP_CURSOR.json'
    if not marker.exists():
        return reference
    candidate = read(marker)['reference']
    store = target / 'parent_cursor'
    states = []
    for selected in (candidate, reference):
        if selected is None:
            states.append(None)
            continue
        path = Path(selected['path'])
        require(path.parent == store and not path.is_symlink()
            and path.stat().st_size <= 16 * 1024 * 1024
            and sha(path) == selected['sha256'], 'pinned_operator_cursor')
        state = read(path)
        require(state['root'] == str((root / 'life').resolve()), 'same_cursor_life')
        states.append(state)
    newer, current = states
    if current is not None:
        require(newer['journal_id'] == current['journal_id'], 'same_cursor_journal')
        if newer['next_index'] <= current['next_index']:
            return reference
    return candidate


def publish(physical, message, opening=False):
    root, target, source = configure(physical)
    word_limit = 160 if physical in (2, 3, 5) else 120
    require(time.time() < WALL and type(message) is str and len(message.split()) <= word_limit
        and len(message.encode()) <= 4096, 'bounded_Astra_publication')
    with (target / 'PARENT_PUBLICATION.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        require(not (target / 'R211_ISOLATION.json').exists(), 'R211_no_inbound_parent_publication')
        current = records(root)
        loaded = [entry for entry in current if entry['kind'] == 'LOADED'][-1]
        require(loaded['index'] > read(target / 'PRESERVED.json')['last_record_index'], 'current_R210_loaded')
        process = Path('/proc', str(loaded['document']['pid']))
        require(process.exists() and os.readlink(process / 'cwd') == str(source), 'actual_same_life_incarnation')
        if opening:
            require(not (target / 'PARENT_OPENING.json').exists(), 'one_R210_opening')
        from gpu.orch_r127_pilot_console import publish_parent
        publication = publish_parent(str(root / 'life'), 'Astra', message)
        if opening:
            write(target / 'PARENT_OPENING.json', dict(publication=publication, message=message,
                published_unix=time.time(), operator_intro_not_model_response=True, new_phase='R210_ENRICHMENT'))
        return publication


if __name__ == '__main__':
    host()
    request = json.loads(sys.stdin.read())
    if request['op'] == 'poll':
        result = poll(request['physical'], request.get('reference'))
    elif request['op'] in ('publish', 'opening'):
        result = publish(request['physical'], request['message'], request['op'] == 'opening')
    else:
        raise ValueError('known_parent_operation')
    print(json.dumps(result))
