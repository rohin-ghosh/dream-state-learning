"""Report actual own-child objects, ACT origins and parent renders, not assignments."""

import hashlib
import json
from pathlib import Path
import time

from math_c import HOME, host, read, sha
from r206_handoff import root_for


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def reference(root, record):
    return dict(index=record['index'], sha256=record['sha256'],
        unix=(root / 'life/stream/records' / f'{record["index"]:020d}.json').stat().st_mtime)


def observe(physical):
    root = root_for(physical)
    target = root / 'r210'
    cutoff = read(target / 'PRESERVED.json')['last_record_index']
    paths = sorted((root / 'life/stream/records').glob('[0-9]' * 20 + '.json'))
    history = [read(path) for path in paths[cutoff + 1:]]
    loaded = [record for record in history if record['kind'] == 'LOADED']
    native_pid = loaded[-1]['document']['pid'] if loaded else None
    process = Path('/proc', str(native_pid)) if native_pid else None
    live = process is not None and process.exists()
    process_state = (process / 'stat').read_text().rsplit(') ', 1)[1].split()[0] if live else None
    responses = {digest(record['document']): record for record in history if record['kind'] == 'RESPONSE'}
    acts = [record for record in history if record['kind'] == 'R184_STAGE' and record['document']['stage'] == 'ACT']
    thoughts = [record for record in history if record['kind'] == 'R184_STAGE' and record['document']['stage'] == 'THINK']
    act = acts[-1] if acts else None
    thought = thoughts[-1] if thoughts else None
    act_response = responses.get(act['document']['source_sha256']) if act else None
    thought_response = responses.get(thought['document']['source_sha256']) if thought else None
    working = [record for record in history if record['kind'] == 'R184_LEARN_COMPLETE']
    working_state = working[-1]['document']['working_state'] if working else None
    current_object = [entry for entry in working_state['entries'] if entry['kind'] in
        ('investigation', 'next_intention', 'uncertainty')] if working_state else []
    parent_renders = []
    for inbox in [record for record in history if record['kind'] == 'INBOX'
            and record['document']['message']['speaker'] == 'Astra']:
        text = inbox['document']['message']['text']
        rendered = next((record for record in history if record['kind'] == 'REQUEST'
            and record['index'] > inbox['index'] and any(text in message['content']
                for message in record['document']['messages'])), None)
        parent_renders.append(dict(id=inbox['document']['message']['id'], inbox=reference(root, inbox),
            render=reference(root, rendered) if rendered else None,
            all_history_tokens_masked=rendered['document']['render_receipt']['all_history_tokens_masked'] if rendered else None))
    outcomes = [record for record in history if record['kind'] == 'R184_ACT']
    outcome = outcomes[-1] if outcomes else None
    latest = history[-1] if history else read(paths[-1])
    return dict(physical=physical, root=str(root / 'life'), observed_unix=time.time(), native_pid=native_pid,
        live=live, process_state=process_state, operator_held=False,
        loaded=reference(root, loaded[-1]) if loaded else None,
        current_object_from_latest_completed_LEARN=current_object,
        latest_THINK=(dict(origin=reference(root, thought_response),
            actual_text=thought_response['document']['response']['raw'][:1800]) if thought_response else None),
        latest_ACT=(dict(stage=reference(root, act), origin=reference(root, act_response),
            actual_text=act_response['document']['response']['raw'][:1800],
            generated_tokens=len(act_response['document']['response']['token_ids'])) if act_response else None),
        latest_ACT_outcome=(dict(receipt=reference(root, outcome), origin=outcome['document'].get('origin'),
            status=outcome['document'].get('outcome', {}).get('status'),
            executed=outcome['document'].get('outcome', {}).get('executed')) if outcome else None),
        parent_renders=parent_renders[-4:], latest=reference(root, latest), latest_kind=latest['kind'],
        parent_silent_isolation=physical == 7,
        current_blocker=('historical_zero_step_prose_proof_replay_before_LOADED' if physical == 3 and not loaded else None))


def scorer():
    base = Path('/localhome/local-rohing/orch_r210_caption_service_20260918')
    sessions = []
    for folder in sorted(base.glob('session*')):
        if not folder.is_dir():
            continue
        loaded = read(folder / 'LOADED.json') if (folder / 'LOADED.json').exists() else {}
        listening = read(folder / 'LISTENING.json') if (folder / 'LISTENING.json').exists() else {}
        public = read(folder / 'CHILD_ENVIRONMENT.json') if (folder / 'CHILD_ENVIRONMENT.json').exists() else {}
        results = list(folder.glob('*/RESULT.json'))
        sessions.append(dict(root=str(folder), pid=loaded.get('pid'),
            live=bool(loaded.get('pid') and Path('/proc', str(loaded['pid'])).exists()),
            loaded_unix=loaded.get('unix'), top_k=loaded.get('top_k'), life_root=loaded.get('life_root'),
            listening=listening, public_scoring=public.get('scoring'), actual_result_count=len(results),
            actual_result_paths=[str(path) for path in results], private_references_read=False))
    return sessions


if __name__ == '__main__':
    host()
    print(json.dumps(dict(observed_unix=time.time(), clones=[observe(physical) for physical in (2, 3, 5, 6, 7)],
        scorer=scorer(), watcher_actions=read(HOME.parent / 'R212_NO_HOLDS.json'))))
