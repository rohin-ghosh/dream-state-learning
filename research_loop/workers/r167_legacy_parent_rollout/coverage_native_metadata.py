"""Read-only process/plan projection for parent coverage, without journal content."""

import hashlib
import json
from pathlib import Path
import socket
import time


def observe():
    rows = []
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            raw = (directory / 'cmdline').read_bytes()
            if len(raw) > 65536:
                continue
            argv = raw.rstrip(b'\0').decode().split('\0')
            if not Path(argv[0]).name.startswith('python'):
                continue
            if not any('orch_r' in argument for argument in argv):
                continue
            before = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
            documents = []
            paths = [argument for argument in argv if argument.startswith('/localhome/local-rohing/')
                     and argument.endswith('.json')]
            for name in paths[:8]:
                path = Path(name)
                if path.stat().st_size > 1048576:
                    continue
                payload = path.read_bytes()
                document = json.loads(payload)
                documents.append(dict(path=name, sha256=hashlib.sha256(payload).hexdigest(),
                    fields={key: document[key] for key in ('root', 'physical_gpu', 'gpu_uuid',
                        'hard_end_unix', 'plan_path', 'plan_sha256') if key in document}))
                if document.get('plan_path'):
                    plan_path = Path(document['plan_path'])
                    if plan_path.stat().st_size <= 1048576:
                        plan_raw = plan_path.read_bytes()
                        if hashlib.sha256(plan_raw).hexdigest() == document.get('plan_sha256'):
                            plan = json.loads(plan_raw)
                            documents.append(dict(path=str(plan_path), sha256=document['plan_sha256'],
                                fields={key: plan[key] for key in ('root', 'physical_gpu', 'gpu_uuid',
                                    'hard_end_unix') if key in plan}))
            after = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
            if before[19] != after[19] or raw != (directory / 'cmdline').read_bytes():
                continue
            rows.append(dict(pid=int(directory.name), start_ticks=after[19], state=after[0],
                argv_sha256=hashlib.sha256(raw).hexdigest(),
                entrypoints=[argument for argument in argv if argument.startswith('gpu.orch_')
                    or (argument.endswith('.py') and 'orch_r' in argument)],
                phases=[argument for argument in argv if argument in
                    ('native', 'control-native', 'supervise', 'run', 'initialize')], documents=documents))
        except (OSError, ValueError, UnicodeError, IndexError):
            continue
    return dict(observed_unix=time.time(), hostname=socket.gethostname(), processes=rows,
        no_signals=True, no_journal_reads=True)


if __name__ == '__main__':
    print(json.dumps(observe(), sort_keys=True))
