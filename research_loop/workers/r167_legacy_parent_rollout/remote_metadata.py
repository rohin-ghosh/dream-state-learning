"""Read-only native ownership projection; no journal text, imports, or signals."""

import hashlib
import json
from pathlib import Path
import socket
import time


def scan():
    observations = []
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            raw = (directory / 'cmdline').read_bytes()
            if len(raw) > 65536:
                continue
            argv = raw.rstrip(b'\0').decode().split('\0')
            if ('native' not in argv or 'gpu.orch_r125_continual_guard' not in argv
                    or not Path(argv[0]).name.startswith('python')):
                continue
            fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
            documents = []
            for item in argv:
                path = Path(item)
                if not item.startswith('/localhome/local-rohing/orch_') or not item.endswith('.json'):
                    continue
                if path.stat().st_size > 1048576:
                    continue
                payload = path.read_bytes()
                document = json.loads(payload)
                documents.append(dict(path=item, sha256=hashlib.sha256(payload).hexdigest(),
                    root=document.get('root'), physical_gpu=document.get('physical_gpu'),
                    gpu_uuid=document.get('gpu_uuid'), hard_end_unix=document.get('hard_end_unix')))
                if document.get('plan_path'):
                    plan_path = Path(document['plan_path'])
                    if plan_path.stat().st_size > 1048576:
                        continue
                    plan_raw = plan_path.read_bytes()
                    if hashlib.sha256(plan_raw).hexdigest() != document['plan_sha256']:
                        continue
                    plan = json.loads(plan_raw)
                    documents.append(dict(path=str(plan_path), sha256=document['plan_sha256'],
                        root=plan.get('root'), physical_gpu=plan.get('physical_gpu'),
                        gpu_uuid=plan.get('gpu_uuid'), hard_end_unix=plan.get('hard_end_unix')))
            after = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
            if after[19] != fields[19] or (directory / 'cmdline').read_bytes() != raw:
                continue
            observations.append(dict(pid=int(directory.name), start_ticks=fields[19],
                state=fields[0], argv_sha256=hashlib.sha256(raw).hexdigest(), plans=documents))
        except (OSError, ValueError, UnicodeError):
            continue
    return dict(schema='R167_READ_ONLY_NATIVE_CENSUS_V1', hostname=socket.gethostname(),
        observed_unix=time.time(), natives=observations, signals=False, journal_content_read=False)


if __name__ == '__main__':
    print(json.dumps(scan(), sort_keys=True))
