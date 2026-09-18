"""P7-only incremental reply lookup; preserve the existing publication checks."""

import json
import os
from pathlib import Path
import sys
import time

from receipt_window import linked_reply, read_record


OPERATOR = Path('/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/MATH_C')
JOURNAL = 'e9d22d1e26234c4bbac761922929365f'
LOADED_SHA = '68cbee223e0ba397c970209dee232ec49bc83be8ceabe358835364fa40f9b076'


def install():
    sys.path.insert(0, str(OPERATOR))
    import r229_node4_endpoint as endpoint
    engine = endpoint.parent.engine

    def poll(reference=None):
        root, previous, source, output = engine.paths()
        engine.require(engine.read(output / 'PHASE.json')['phase'] == engine.PHASE, 'same_existing_parent_phase')
        process = Path('/proc/1100592')
        fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
        engine.require(fields[19] == '28670738' and os.readlink(process / 'cwd') == str(source),
            'same_P7_native_start_and_source')
        records = root / 'life/stream/records'
        loaded = read_record(records / '00000000000000001986.json', JOURNAL)
        engine.require(loaded['sha256'] == LOADED_SHA and loaded['document']['pid'] == 1100592,
            'same_bound_loaded_P7')
        snapshot = engine.load('r233_p7_snapshot', engine.HOME / 'read_snapshot.py')
        result = snapshot.stored_poll(root / 'life', output / 'cursor', reference)
        state = result['snapshot']
        published = engine.publications(output)
        for entry in published:
            delivered = state['delivered'].get(entry['publication']['id'])
            receipt = output / ('RENDERED_' + entry['publication']['id'] + '.json')
            if delivered and not receipt.exists():
                path = records / f'{delivered["record_index"]:020d}.json'
                request = read_record(path, JOURNAL)
                positions = [position for position, message in enumerate(request['document']['messages'])
                    if isinstance(message.get('content'), str) and 'Astra: ' + entry['message'] in message['content']]
                engine.require(request['sha256'] == delivered['record_sha256'] and request['kind'] == 'REQUEST'
                    and request['document']['render_receipt']['all_history_tokens_masked'] is True
                    and positions, 'actual_exact_masked_REQUEST_text')
                engine.write(receipt, dict(publication=entry['publication'], delivery=delivered, turn=entry['turn'],
                    request_path=str(path), request_sha256=request['sha256'], request_mtime_unix=path.stat().st_mtime,
                    exact_text_in_messages=True, message_indices=positions, all_history_tokens_masked=True,
                    observed_unix=time.time(), source_commit=engine.COMMIT, protocol_sha256=engine.PROTOCOL_SHA))
        delivered = state['delivered'].get(published[-1]['publication']['id'])
        reply, earlier = (None, []) if not delivered else linked_reply(records, delivered['record_index'],
            delivered['record_sha256'], JOURNAL)
        if reply is not None:
            receipt = output / f'REPLY_{published[-1]["sequence"]:06d}.json'
            if not receipt.exists():
                engine.write(receipt, dict(publication=published[-1]['publication'], reply=reply,
                    observed_unix=time.time(), scoring=False))
        result.update(publications=published, reply=reply, earlier=earlier,
            render_receipts=[engine.read(path) for path in sorted(output.glob('RENDERED_*.json'))],
            completed=(output / 'COMPLETED.json').exists(),
            reply_reader='R233_P7_EXACT_RECORD_METADATA_LOOKUP_V1')
        return result

    engine.poll = poll
    return endpoint


if __name__ == '__main__':
    endpoint = install()
    endpoint.host()
    request = json.loads(sys.stdin.read())
    if request['op'] not in ('poll', 'advance', 'return'):
        raise ValueError('existing_P7_operations_only_no_rebind')
    print(json.dumps(endpoint.main(request), ensure_ascii=False))
