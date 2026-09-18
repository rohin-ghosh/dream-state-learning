"""Bounded two-clone state transport; publication is not THINK-render proof."""

import hashlib
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parent
ARMS = ('math_d1', 'repo_c1')


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, document):
    with path.open('x') as output:
        json.dump(document, output, sort_keys=True, indent=2)


def verified(path):
    if path.is_symlink() or path.stat().st_size > 32 * 1024**2:
        raise ValueError('bounded_regular_clone_record')
    record = read(path)
    if digest({key: value for key, value in record.items() if key != 'sha256'}) != record['sha256']:
        raise ValueError('actual_peer_record_hash')
    return record


def capsule(sender, complete):
    if sender not in ARMS or complete['kind'] != 'R184_LEARN_COMPLETE' or complete['document']['cycle'] < 52:
        raise ValueError('new_clone_carried_state_only')
    state = complete['document']['working_state']
    environment = 'mathematical investigation with confined SymPy/mpmath' if sender == 'math_d1' else 'repository inspection and private proposals, without code execution'
    lines = [f'Peer state transport from {sender}, environment: {environment}.',
        f'Carried state after its completed cycle {complete["document"]["cycle"]}, revision {state["revision"]}.',
        'This is an explicitly different-environment paired treatment, not matched parent-only evidence.',
        'These are the peer\'s carried assertions and intentions; unchanged inherited entries are not new discoveries.']
    for entry in state['entries']:
        lines.append(entry['kind'] + ': ' + entry['text'])
    if not state['entries']:
        lines.append('No explicit carried-state entries exist; no finding is fabricated.')
    lines.append('Form a prediction and check it in your own environment. This transported peer report is not a verified result from your own tools, and is not parent guidance.')
    text = '\n'.join(lines)
    if len(text.encode()) > 6000:
        raise ValueError('bounded_peer_capsule_no_silent_rewrite')
    return text


def recent(root):
    rows = []
    for path in sorted((root / 'raw/stream/records').glob('*.json'))[-240:]:
        if path.name.endswith('.intent.json') or int(path.stem) < 5847:
            continue
        with path.open('rb') as handle:
            handle.seek(max(0, path.stat().st_size - 4096))
            tail = handle.read()
        marker = tail.rfind(b',"index":')
        if marker < 0:
            raise ValueError('record_metadata_layout')
        meta = json.loads(b'{' + tail[marker + 1:])
        rows.append((path, meta))
    return rows


def inspect_delivery(receiver, publication, rows):
    for path, meta in rows:
        if meta['kind'] != 'REQUEST' or meta['index'] <= publication['receiver_boundary_index']:
            continue
        request = verified(path)
        document = request['document']
        visible = any(message.get('role') == 'user' and message.get('content') == 'Tool: ' + publication['text']
            for message in document['messages'])
        if not visible:
            continue
        stage = next((verified(stage_path) for stage_path, stage_meta in rows
            if stage_meta['kind'] == 'R184_STAGE' and stage_meta['index'] > meta['index']
            and read(stage_path)['document']['segment'] == document['segment']), None)
        if stage is None:
            continue
        return dict(receiver=receiver, request_index=meta['index'], request_sha256=meta['sha256'],
            request_started_unix=document['started_unix'], segment=document['segment'],
            stage=stage['document']['stage'], stage_sha256=stage['sha256'],
            peer_text_actually_rendered=True, all_history_tokens_masked=document['render_receipt']['all_history_tokens_masked'],
            qualifies_as_THINK_exchange=stage['document']['stage'] == 'THINK'
                and document['render_receipt']['all_history_tokens_masked'], observed_unix=time.time())
    return None


def main():
    config = read(ROOT / 'CONFIG.json')
    if config.get('screen_complete_before_peer') is not True:
        raise ValueError('R203_no_peer_during_initial_three_plus_three_screen')
    bases = {name: Path(config['arms'][name]['root']) for name in ARMS}
    if len(set(bases.values())) != 2 or any(root.name != name for name, root in bases.items()):
        raise ValueError('distinct_actual_clone_roots')
    for root in bases.values():
        complete_cycles = [verified(path)['document']['cycle'] for path, meta in recent(root)
            if meta['kind'] == 'R184_LEARN_COMPLETE']
        if not complete_cycles or max(complete_cycles) < 57:
            raise ValueError('both_six_cycle_screens_must_be_complete_before_peer_activation')
    sys.path.insert(0, str(bases['repo_c1'] / 'source'))
    from gpu.orch_r127_pilot_console import _inbox
    from organism_v6.orch_r125_plain_context import has_scaffolding
    write(ROOT / 'STARTED.json', dict(pid=os.getpid(), started_unix=time.time(), end_unix=config['end_unix'],
        max_publications=10, peer_continues_during_parent_withdrawal=True, parent_publications=0,
        treatment='R202_MATH_D_REPO_C_OPEN_THINK_PEER_PAIR', source_config_sha256=hashlib.sha256((ROOT / 'CONFIG.json').read_bytes()).hexdigest()))
    publications = {}
    verified_publications = set()
    seen_boundaries = set()
    cached = {}
    while time.time() < config['end_unix'] and len(publications) <= 10:
        rows = {}
        complete = {}
        for name, root in bases.items():
            if hashlib.sha256((root / 'control/GUARD.json').read_bytes()).hexdigest() != config['arms'][name]['guard_sha256']:
                raise ValueError('clone_guard_changed_stop_transport')
            rows[name] = recent(root)
            for path, meta in reversed(rows[name]):
                if meta['kind'] == 'R184_LEARN_COMPLETE':
                    cache_key = (name, meta['sha256'])
                    if cache_key not in cached:
                        cached[cache_key] = verified(path)
                    complete[name] = cached[cache_key]
                    break
        for key, publication in publications.items():
            if key not in verified_publications:
                proof = inspect_delivery(publication['receiver'], publication, rows[publication['receiver']])
                if proof is not None:
                    write(ROOT / ('RENDER_' + key + '.json'), proof)
                    verified_publications.add(key)
        for sender, receiver in (('math_d1', 'repo_c1'), ('repo_c1', 'math_d1')):
            if sender not in complete or receiver not in complete or len(publications) >= 10:
                continue
            boundary = complete[receiver]
            cycle = boundary['document']['cycle']
            key = receiver + '_after_' + str(cycle)
            if not 57 <= cycle < 60 or key in seen_boundaries or rows[receiver][-1][1]['index'] != boundary['index']:
                continue
            text = capsule(sender, complete[sender])
            seen_boundaries.add(key)
            if has_scaffolding('Tool: ' + text):
                write(ROOT / ('SKIP_' + key + '.json'), dict(reason='Peer state would be hidden by unchanged renderer; no publication or normalization', observed_unix=time.time()))
                continue
            source = dict(sender=sender, sender_root=str(bases[sender]), sender_guard_sha256=config['arms'][sender]['guard_sha256'],
                source_record_index=complete[sender]['index'], source_record_sha256=complete[sender]['sha256'],
                source_journal_id=complete[sender]['journal_id'], receiver=receiver, receiver_root=str(bases[receiver]),
                receiver_boundary_index=boundary['index'], receiver_boundary_sha256=boundary['sha256'],
                source_working_state_sha256=digest(complete[sender]['document']['working_state']), text=text,
                text_sha256=hashlib.sha256(text.encode()).hexdigest(), observed_unix=time.time(),
                tool_is_peer_transport_not_calculation=True, human_or_peer_target_created=False)
            source_path = ROOT / ('SOURCE_' + key + '.json')
            write(source_path, source)
            publication = _inbox(bases[receiver] / 'raw', 'Tool', text,
                dict(path=str(source_path), sha256=hashlib.sha256(source_path.read_bytes()).hexdigest()))
            publication.update(source, published_unix=time.time(), peer_THINK_render_verified=False)
            write(ROOT / ('PUBLICATION_' + key + '.json'), publication)
            publications[key] = publication
        if all((root / 'control/EXIT.json').exists() for root in bases.values()):
            break
        time.sleep(1)
    write(ROOT / 'EXIT.json', dict(finished_unix=time.time(), publications=len(publications),
        render_receipts=len(verified_publications), parent_publications=0, no_automatic_restart=True))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        write(ROOT / 'FAILED.json', dict(error_type=type(error).__name__, error=str(error), finished_unix=time.time(), no_retry=True))
        raise
