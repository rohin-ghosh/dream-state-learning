"""Read one pinned historical COMPLETE record, never replay or resume observation."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
READY = ROOT / "research_loop/workers/post_recovery_c2_age_sources_20260918/READY.json"
TARGET = HERE / "CHECKPOINT117_TIME.json"
STOP = HERE / "CHECKPOINT117_TIME_LIMIT.json"
HARD_END = 1789927200
REMOTE = r'''
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat

path = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life/stream/records/00000000000000011831.json')
descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
with os.fdopen(descriptor, 'rb') as stream:
    before = os.fstat(stream.fileno())
    assert stat.S_ISREG(before.st_mode) and before.st_size <= 2_000_000, ('bounded_regular_file_required', before.st_size)
    raw = stream.read(2_000_001)
    after = os.fstat(stream.fileno())
assert (before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns)
record = json.loads(raw)
expected = 'e6ae76769b29b2ae43d056f3ef6ee832f35960b2a7190ad605236031704c0539'
canonical = json.dumps({key:value for key,value in record.items() if key != 'sha256'}, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
assert record['sha256'] == hashlib.sha256(canonical).hexdigest() == expected
assert record['journal_id'] == '260be8b8710a42559b291797c6e14983'
assert record['index'] == 11831 and record['kind'] == 'SLEEP_COMPLETE'
document = record['document']
assert document['cycle'] == 117 and document['status'] == 'COMPLETE'
assert document['total_optimizer_steps'] == 7948
assert before.st_mtime <= 1789768727.607578, ('mtime_after_selection_not_original_save_time', before.st_mtime)
print(json.dumps({
    'path':str(path), 'bytes':len(raw), 'file_sha256':hashlib.sha256(raw).hexdigest(),
    'record':{key:record[key] for key in ('index','kind','sha256','journal_id','previous_sha256')},
    'cycle':document['cycle'], 'status':document['status'],
    'optimizer_steps':document['total_optimizer_steps'],
    'complete_record_mtime_unix':before.st_mtime,
    'complete_record_mtime_ns':before.st_mtime_ns,
    'complete_record_mtime_utc':datetime.fromtimestamp(before.st_mtime, timezone.utc).isoformat(),
    'time_basis':'Original SLEEP_COMPLETE record filesystem mtime, same observational basis as sleep51; not an internal timestamp encoded by the canonical record hash.',
    'stable_read':True, 'canonical_hash_verified':True,
    'remote_files_read':1, 'remote_record_bytes_limit':2_000_000,
    'remote_writes':0, 'model_calls':0, 'signals':0,
    'observed_utc':datetime.now(timezone.utc).isoformat()
}))
'''


def receipt(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    if TARGET.exists() or STOP.exists() or time.time() >= HARD_END:
        raise ValueError("Existing receipt or expired historical-read authority; do not recollect")
    ready = json.loads(READY.read_bytes())
    source = next(item for item in ready["sources"] if item["absolute_sleep"] == 117)
    response = subprocess.run(
        ["bash", str(ROOT / "gpu/ovx3_ssh.sh"),
         "CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -"],
        input=REMOTE, text=True, capture_output=True, timeout=45, check=False,
    )
    if response.returncode:
        raise RuntimeError("Exact-record read failed: " + response.stderr[:3000])
    if len(response.stdout.encode()) > 12000:
        raise ValueError("Unexpected metadata output size")
    result = json.loads(response.stdout)
    assert result["record"]["sha256"] == source["sleep_complete_sha256"]
    assert result["optimizer_steps"] == source["optimizer_steps"]
    result.update(
        schema="c2_pinned_checkpoint117_time_v1", source_ready_receipt=receipt(READY),
        reader_receipt=receipt(Path(__file__)),
        adapter_state_sha256=source["adapter_state_sha256"],
        selected_utc=datetime.fromtimestamp(ready["selection"]["selected_unix"], timezone.utc).isoformat(),
        source_sha256=source["source_sha256"],
        scope="One exact historical COMPLETE record only; no live observer reset, new ACT capture, raw journal export, checkpoint payload, or sealed panel read.",
    )
    print("*** Begin Patch\n*** Add File: " + str(TARGET.relative_to(ROOT)))
    for line in json.dumps(result, indent=2).splitlines():
        print("+" + line)
    print("*** End Patch")


if __name__ == "__main__":
    main()
