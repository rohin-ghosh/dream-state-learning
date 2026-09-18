"""Read-only retrieval of this attempt's closed JSON receipts, never GPU work."""

import base64
import json
import os
from pathlib import Path
import shlex
import subprocess

root = Path(__file__).resolve().parent
remote_root = '/tmp/research_loop/workers/r177_caption_game_stage1_20260917/generation_profile/standalone_04'
code = "import base64,json; from pathlib import Path; root=Path(" + repr(remote_root) + "); print(json.dumps([dict(name=path.name,data=base64.b64encode(path.read_bytes()).decode()) for path in sorted(root.glob('*.json'))]))"
result = subprocess.run(['bash', 'gpu/a40r_ssh.sh', '/usr/bin/python3 -B -c ' + shlex.quote(code)],
                        text=True, capture_output=True, timeout=30)
if result.returncode:
    raise RuntimeError(result.stderr)
destination = root / 'attempt_receipts'
destination.mkdir(exist_ok=True)
documents = []
for entry in json.loads(result.stdout):
    if Path(entry['name']).name != entry['name']:
        raise ValueError('receipt_basename_only')
    raw = base64.b64decode(entry['data'], validate=True)
    document = json.loads(raw)
    path = destination / entry['name']
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('immutable_receipt_changed:' + entry['name'])
    else:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    if entry['name'].startswith('TRIAL_'):
        documents.append(document)
    elif entry['name'].startswith('FAILURE_') or entry['name'] in ('SERVICE_EXIT.json', 'COMPLETE.json'):
        print(entry['name'], json.dumps(document))
documents.sort(key=lambda document: document['observed_unix'])
print('Persisted trials:', len(documents))
for document in documents[-4:]:
    print(json.dumps(dict(name=document['name'], counts=document['generation']['actual_tokens_per_life'],
        hf_seconds=document['generation']['seconds'], per_life_tok_s=document['generation']['per_life_tokens_per_second'],
        aggregate_tok_s=document['generation']['aggregate_tokens_per_second'])))
