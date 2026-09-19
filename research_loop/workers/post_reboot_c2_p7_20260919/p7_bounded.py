"""Same P7 parent policy; store small polling receipts and full actual turns."""

import hashlib
import json
from pathlib import Path


def compact_poll(document):
    reply = document.get('reply')
    return dict(schema='P7_POLL_RECEIPT_V1', reference=document.get('reference'),
        actual_native=document.get('actual_native'), after_sleep=document.get('after_sleep'),
        reply_reference=({key: reply.get(key) for key in ('record_index', 'record_sha256',
            'request_record_index', 'commit_record_index')} if reply else None),
        publications=len(document.get('publications', [])),
        observation_sha256=hashlib.sha256(json.dumps(document, sort_keys=True,
            separators=(',', ':'), ensure_ascii=False).encode()).hexdigest(),
        full_actual_turn_inputs_preserved=True, policy_changed=False)


def main():
    import p7_restore
    original_write = p7_restore.original.base.write

    def write(path, document):
        if Path(path).name.startswith('POLL_'):
            document = compact_poll(document)
        return original_write(path, document)

    p7_restore.original.base.write = write
    p7_restore.serve()


if __name__ == '__main__':
    main()
