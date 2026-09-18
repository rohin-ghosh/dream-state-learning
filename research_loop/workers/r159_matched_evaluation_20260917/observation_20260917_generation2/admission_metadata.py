import hashlib
import json
import os
from pathlib import Path
import socket
import stat
import time


root = Path('/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5')
assert socket.gethostname() == '[REDACTED_HOST]' and time.time() < 1789632000
result = dict(schema='R159_ADMISSION_HEADER_WITNESSES_V1', artifacts={}, bytes_read=0)
for arm, attempt in (('parented_learning', 1), ('parented_frozen', 2), ('unparented_learning', 1)):
    path = root / f'attempts/run-{arm}-attempt{attempt}/ADMISSION.json'
    assert not any(part.is_symlink() for part in (path, *path.parents))
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, 'rb') as stream:
        metadata = os.fstat(stream.fileno())
        assert stat.S_ISREG(metadata.st_mode) and metadata.st_size < 2 * 1024 * 1024
        raw = stream.read(metadata.st_size + 1)
        assert len(raw) == metadata.st_size
    document = json.loads(raw)
    result['bytes_read'] += len(raw)
    result['artifacts'][arm] = dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(),
        bytes=len(raw), clear=document.get('clear'), blocking_reason_count=len(document.get('blocking_reasons', [])))
result.update(observed_unix=time.time(), source_written=False, held_contents_read=False)
print(json.dumps(result, sort_keys=True))
