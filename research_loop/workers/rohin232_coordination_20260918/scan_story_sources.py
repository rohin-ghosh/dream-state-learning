"""Collect early genuine story responses for operator-only recall grading."""

import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PARENT = REPO / 'research_loop/workers/rohin174_parenting_20260917/node5/R195_FLEET/MSG201'
sys.path.insert(0, str(PARENT))
import r202_parent as existing


SCRIPT = r'''
from datetime import datetime, timezone
import hashlib, json, re
from pathlib import Path
root = Path(ROOT)
found = {'Byte': [], 'Neo': []}
scanned = 0
for path in sorted((root / 'stream/records').glob('[0-9]' * 20 + '.json')):
    with path.open('rb') as stream:
        stream.seek(max(0, path.stat().st_size - 4096))
        tail = stream.read()
    position = tail.rfind(b',"index":')
    if position < 0:
        raise ValueError('canonical_record_trailer_required')
    metadata = json.loads(b'{' + tail[position + 1:])
    scanned += 1
    if metadata['kind'] != 'RESPONSE':
        continue
    payload = path.read_bytes()
    record = json.loads(payload)
    raw = record['document']['response']['raw']
    for name in found:
        if len(found[name]) < 8 and re.search(r'\b' + name + r'\b', raw, re.I):
            found[name].append(dict(index=record['index'], record_sha256=record['sha256'],
                file_sha256=hashlib.sha256(payload).hexdigest(),
                raw_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                finished_unix=record['document'].get('finished_unix'),
                request_sha256=record['document'].get('request_sha256'), raw=raw))
    if all(len(values) == 8 for values in found.values()):
        break
print(json.dumps(dict(observed_utc=datetime.now(timezone.utc).isoformat(),
    root=str(root), records_scanned=scanned, earliest_matches=found,
    learner_controls=0, child_publications=0), ensure_ascii=False))
'''


def main():
    config = json.loads((PARENT / 'LIVE_CONVERSATION_PARENT14_CONFIG.json').read_bytes())
    result = existing.parent.remote(existing.REPOSITORY, config, SCRIPT.replace('ROOT', repr(config['root'])))
    output = HERE / 'private'
    output.mkdir(mode=0o700, exist_ok=True)
    with (output / 'EARLY_STORY_RESPONSES.json').open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2, ensure_ascii=False)
    print(json.dumps(dict(observed_utc=result['observed_utc'], records_scanned=result['records_scanned'],
        indices={name: [row['index'] for row in values] for name, values in result['earliest_matches'].items()})))


if __name__ == '__main__':
    main()
