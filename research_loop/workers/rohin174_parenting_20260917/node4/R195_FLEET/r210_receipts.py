"""Bounded public operator metadata from actual TRAIN rendering and replies."""

import argparse
import hashlib
import json
from pathlib import Path
import time

from math_c import host, read, sha
from r206_handoff import root_for


def collect(physical):
    root = root_for(physical)
    target = root / 'r210'
    preserved = read(target / 'PRESERVED.json')
    paths = sorted((root / 'life/stream/records').glob('[0-9]' * 20 + '.json'))
    history = [read(path) for path in paths[preserved['last_record_index'] + 1:]]
    requests = [entry for entry in history if entry['kind'] == 'REQUEST']
    reply_rows = []
    for entry in history:
        if entry['kind'] != 'R205_CONSOLE_REPLY':
            continue
        document = entry['document']
        origin = document['response_origin']
        response_path = root / 'life/stream/records' / f'{origin["record_index"]:020d}.json'
        response = read(response_path)
        assert response['sha256'] == origin['record_sha256'] and response['kind'] == 'RESPONSE'
        request = next(item for item in reversed(requests) if item['index'] < response['index'])
        supplied = []
        for event in document['source_inbox_events']:
            source = Path(event['source_id'])
            assert source.parent == root / 'life/stream/inbox' and sha(source) == event['source_sha256']
            message = read(source)
            assert message['actor'] == 'parent' and message['speaker'] == 'Rohin' and message['split'] == 'TRAIN'
            supplied.append(dict(id=message['id'], source_sha256=event['source_sha256'],
                exact_text_rendered=any(message['text'] in item['content'] for item in request['document']['messages'])))
        raw = response['document']['response']['raw']
        committed = [item for item in history if response['index'] < item['index'] < entry['index']
            and item['kind'] == 'COMMITTED']
        reply_rows.append(dict(index=entry['index'], sha256=entry['sha256'],
            time=(root / 'life/stream/records' / f'{entry["index"]:020d}.json').stat().st_mtime,
            inputs=supplied, request_index=request['index'], prompt_tokens=request['document']['prompt_tokens'],
            all_history_tokens_masked=request['document']['render_receipt']['all_history_tokens_masked'],
            response_origin=origin, response_sha256=hashlib.sha256(raw.encode()).hexdigest(), response_bytes=len(raw.encode()),
            generated_tokens=len(response['document']['response']['token_ids']),
            committed_indices=[item['index'] for item in committed], outcome=document['outcome']))
    openings = []
    for name in ('PARENT_OPENING.json', 'CREATIVE_ANSWER.json'):
        path = target / name
        if not path.exists():
            continue
        publication = read(path)['publication']
        message = read(publication['path'])
        rendered = [entry for entry in requests if any(message['text'] in item['content']
            for item in entry['document']['messages'])]
        subsequent = next((entry for entry in history if rendered and entry['index'] > rendered[0]['index']
            and entry['kind'] == 'RESPONSE'), None)
        openings.append(dict(publication=publication, label=name, operator_intro_not_model_response=True,
            exact_text_rendered=bool(rendered), first_request_index=rendered[0]['index'] if rendered else None,
            first_request_unix=rendered[0]['document']['started_unix'] if rendered else None,
            all_history_tokens_masked=rendered[0]['document']['render_receipt']['all_history_tokens_masked'] if rendered else None,
            first_following_child_response=(dict(index=subsequent['index'], sha256=subsequent['sha256'],
                finished_unix=subsequent['document']['finished_unix'],
                generated_tokens=len(subsequent['document']['response']['token_ids'])) if subsequent else None)))
    loaded = [entry for entry in history if entry['kind'] == 'LOADED']
    last = history[-1] if history else read(paths[-1])
    return dict(physical=physical, root=str(root / 'life'), observed_unix=time.time(),
        preserved=preserved['saved'], new_phase='R210_ENRICHMENT', prior_screen_untouched=True,
        loaded=[dict(index=entry['index'], sha256=entry['sha256'], **{key: entry['document'][key]
            for key in ('pid', 'loaded_unix', 'optimizer_steps', 'resume')}) for entry in loaded],
        first_think=next((dict(index=entry['index'], sha256=entry['sha256'],
            time=paths[entry['index']].stat().st_mtime) for entry in history
            if entry['kind'] == 'R184_STAGE' and entry['document'].get('stage') == 'THINK'), None),
        console_replies=reply_rows, parent_openings=openings,
        latest=dict(index=last['index'], kind=last['kind'], sha256=last['sha256'], time=paths[last['index']].stat().st_mtime))


if __name__ == '__main__':
    host()
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, nargs='+', choices=(2, 3, 5, 6, 7), required=True)
    options = parser.parse_args()
    print(json.dumps(dict(observed_unix=time.time(), slots=[collect(physical) for physical in options.physical])))
