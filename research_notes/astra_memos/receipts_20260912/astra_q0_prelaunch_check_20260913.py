import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True)
parser.add_argument('--root', required=True)
parser.add_argument('--manifest-sha256', required=True)
args = parser.parse_args()
root = Path(args.root)
raw = (root / 'manifest.json').read_bytes()
assert hashlib.sha256(raw).hexdigest() == args.manifest_sha256
manifest = json.loads(raw)
assert manifest['ready']
assert not (root / 'STARTED.json').exists()
assert not (root / 'SEAL.json').exists()
sys.path.insert(0, args.source)
from organism_v6 import multikey_writer_gateway_simple as gateway
gateway.gpu_identity(manifest['config'])
gateway.assert_gpu_idle(manifest['config'])
matches = []
unreadable = []
excluded = []
scanned = 0
for entry in Path('/proc').glob('[0-9]*/environ'):
    try:
        if entry.stat().st_uid != os.getuid():
            continue
        try:
            fields = entry.read_bytes().split(b'\0')
        except PermissionError:
            process = entry.parent
            status = (process / 'stat').read_text().rsplit(')', 1)[1].split()
            identity = dict(pid=int(process.name), comm=(process / 'comm').read_text().strip(),
                            ppid=int(status[1]), start_ticks=int(status[19]))
            if identity == dict(pid=3245, comm='systemd', ppid=1, start_ticks=2469):
                excluded.append(identity)
            else:
                unreadable.append(identity)
            continue
        scanned += 1
        device = next((field.split(b'=', 1)[1].decode() for field in fields
                       if field.startswith(b'CUDA_VISIBLE_DEVICES=')), '')
        if set(value.strip() for value in device.split(',')) & {'2', manifest['config']['gpu_uuid']}:
            matches.append(int(entry.parent.name))
    except FileNotFoundError:
        continue
result = dict(checked_unix=time.time(), compute_idle=True, same_user_environments_scanned=scanned,
              matching_reservations=matches, unreadable_same_user=unreadable,
              verified_nonlearner_exclusions=excluded, manifest_sha256=args.manifest_sha256,
              gpu_uuid=manifest['config']['gpu_uuid'], same_user_scope_only=True)
print(json.dumps(result, sort_keys=True), flush=True)
assert not matches and not unreadable, 'unresolved learner reservation'
