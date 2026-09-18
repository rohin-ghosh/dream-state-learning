"""Read exact journal links without repeatedly loading historical bodies."""

import hashlib
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def read_record(path, journal_id):
    record = json.loads(Path(path).read_bytes())
    if record['journal_id'] != journal_id or record['sha256'] != digest(
            {key: value for key, value in record.items() if key != 'sha256'}):
        raise ValueError('exact_canonical_journal_record')
    return record


def header(path):
    with Path(path).open('rb') as stream:
        stream.seek(max(0, Path(path).stat().st_size - 4096))
        ending = stream.read()
    offset = ending.rfind(b',"index":')
    record = json.loads(b'{' + ending[offset + 1:]) if offset >= 0 else json.loads(Path(path).read_bytes())
    return {key: record[key] for key in ('index', 'kind', 'sha256', 'journal_id')}


def linked_reply(directory, request_index, request_sha256, journal_id):
    directory = Path(directory)
    request = read_record(directory / f'{request_index:020d}.json', journal_id)
    if request['kind'] != 'REQUEST' or request['sha256'] != request_sha256:
        raise ValueError('exact_delivered_REQUEST')
    request_digest = digest({key: value for key, value in request['document'].items()
        if key != 'resume_state'})
    headers = [header(path) for path in sorted(directory.glob('[0-9]' * 20 + '.json'))]
    response = None
    commit = None
    earlier = []
    candidates = [row for row in headers if row['kind'] == 'RESPONSE'
        and row['index'] < request_index][-8:]
    selected = candidates + [row for row in headers if row['index'] > request_index
        and row['kind'] in ('RESPONSE', 'COMMITTED', 'CONTEXT_COMMITTED')]
    documents = {row['index']: read_record(directory / f'{row["index"]:020d}.json', journal_id)
        for row in selected}
    for row in documents.values():
        if row['kind'] == 'RESPONSE' and row['index'] > request_index:
            if row['document']['request_sha256'] == request_digest:
                if response is not None:
                    raise ValueError('one_actual_reply_per_REQUEST')
                response = row
    if response is not None:
        matches = [row for row in documents.values()
            if row['kind'] in ('COMMITTED', 'CONTEXT_COMMITTED')
            and row['index'] > response['index']
            and row['document'].get('source_sha256') == digest(response['document'])]
        if len(matches) > 1:
            raise ValueError('one_committed_source_response')
        commit = matches[0] if matches else None
    for candidate in candidates:
        row = documents[candidate['index']]
        followers = [item for item in headers if candidate['index'] < item['index'] < request_index
            and item['kind'] in ('COMMITTED', 'CONTEXT_COMMITTED')][:2]
        if any(read_record(directory / f'{item["index"]:020d}.json', journal_id)['document'].get(
                'source_sha256') == digest(row['document']) for item in followers):
            earlier.append(dict(actor='child', record_index=row['index'], record_sha256=row['sha256'],
                text=row['document']['response']['raw']))
    if response is None or commit is None:
        return None, earlier
    return dict(actor='child', record_index=response['index'], record_sha256=response['sha256'],
        text=response['document']['response']['raw'], commit_record_index=commit['index'],
        commit_record_sha256=commit['sha256'], request_record_index=request_index,
        request_record_sha256=request_sha256), earlier
