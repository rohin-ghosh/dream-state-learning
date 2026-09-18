"""Bounded read-only TRAIN delivery check; emits hashes/indices, never text."""

import hashlib
import json
import os
from pathlib import Path
import sys
import time


def visible_kind(messages, document):
    message = document['message']
    visible = message['speaker'] + ': ' + message['text'] if message.get('schema') == 'R127_ATTRIBUTED_INBOX_V1' else message['text']
    for position, entry in enumerate(messages):
        if position < 2 or entry.get('role') != 'user':
            continue
        content = entry.get('content')
        if content == visible:
            return 'EXACT_PLAIN_TEXT_MATCH_NOT_UNIQUE_ID_ATTRIBUTION'
        if not isinstance(content, str):
            continue
        pieces = content.split('\n', 2)
        if len(pieces) != 3 or pieces[0] != 'Parent advice (not an observed fact)' or pieces[2] != visible:
            continue
        try:
            metadata = json.loads(pieces[1])
        except ValueError:
            continue
        if (metadata.get('event_id') == 'parent:inbox:' + message['id']
                and metadata.get('actor') == 'parent' and metadata.get('split') == 'TRAIN'
                and metadata.get('source_id') == document.get('source_id')
                and metadata.get('source_sha256') == document.get('source_sha256')):
            return 'EXACT_STRUCTURED_ID_AND_TEXT_MATCH'
    return None


def probe(request):
    sys.path.insert(0, request['source_root'])
    from gpu.orch_r125_stream_console import _open_stream_directory, _read_record
    answer = dict(root=request['root'], inbox_id=request['inbox_id'], observed_unix=time.time(),
        status='NOT_OBSERVED_WITHIN_BOUNDED_WINDOW', bytes_read=0)
    previous, inbox = None, None
    with _open_stream_directory(request['root'], 'records') as (directory, unused):
        for index in range(request['start_index'], request['start_index'] + 64):
            name = f'{index:020d}.json'
            try:
                size = os.stat(name, dir_fd=directory, follow_symlinks=False).st_size
            except FileNotFoundError:
                break
            if size > 32 * 1024 * 1024 or answer['bytes_read'] + size > 128 * 1024 * 1024:
                answer['limit_reached'] = True
                break
            record = _read_record(directory, index)
            answer['bytes_read'] += size
            if previous is None:
                assert record['sha256'] == request['start_record_sha256']
            else:
                assert record['previous_sha256'] == previous
            previous = record['sha256']
            document = record['document']
            if record['kind'] == 'INBOX' and document['message']['id'] == request['inbox_id']:
                message = document['message']
                assert message['actor'] == 'parent' and message.get('speaker') == 'Astra' and message['split'] == 'TRAIN'
                raw = (json.dumps(message, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
                assert hashlib.sha256(raw).hexdigest() == request['publication_sha256']
                inbox = document
                answer.update(status='INBOX_CONSUMED_REQUEST_NOT_YET_MATCHED', inbox_record_index=index,
                    inbox_record_sha256=record['sha256'])
            elif record['kind'] == 'REQUEST' and inbox is not None:
                match = visible_kind(document.get('messages', []), inbox)
                if match:
                    answer.update(status='RENDERED_TEXT_VERIFIED', match_kind=match,
                        request_record_index=index, request_record_sha256=record['sha256'],
                        request_started_unix=document.get('started_unix'))
                    break
    return answer


if __name__ == '__main__':
    print(json.dumps(probe(json.loads(sys.argv[1])), sort_keys=True))
