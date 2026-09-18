"""Read-only R136 control-native ownership; never opens readout manifests."""

import hashlib
import json
from pathlib import Path
import socket
import time


def selected(argv):
    return (len(argv) >= 6 and Path(argv[0]).name.startswith('python') and '-m' in argv
        and argv[argv.index('-m') + 1] == 'gpu.orch_r136_node1_launcher'
        and argv[argv.index('-m') + 2] == 'control-native' and '--config' in argv)


def scan():
    natives = []
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            raw = (path / 'cmdline').read_bytes()
            if len(raw) > 65536:
                continue
            argv = raw.rstrip(b'\0').decode().split('\0')
            if not selected(argv):
                continue
            fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
            guard_path = Path(argv[argv.index('--config') + 1])
            if not str(guard_path).startswith('/localhome/local-rohing/orch_r139_'):
                continue
            if guard_path.stat().st_size > 1048576:
                continue
            guard_raw = guard_path.read_bytes()
            guard = json.loads(guard_raw)
            plan_path = Path(guard['plan_path'])
            if plan_path.stat().st_size > 1048576:
                continue
            plan_raw = plan_path.read_bytes()
            assert hashlib.sha256(plan_raw).hexdigest() == guard['plan_sha256']
            plan = json.loads(plan_raw)
            after = (path / 'stat').read_text().rsplit(')', 1)[1].split()
            if after[19] != fields[19] or (path / 'cmdline').read_bytes() != raw:
                continue
            natives.append(dict(pid=int(path.name), start_ticks=fields[19], state=after[0],
                argv_sha256=hashlib.sha256(raw).hexdigest(), entrypoint='R136_CONTROL_NATIVE',
                plans=[dict(path=str(guard_path), sha256=hashlib.sha256(guard_raw).hexdigest(), root=None),
                    dict(path=str(plan_path), sha256=guard['plan_sha256'], root=plan['root'],
                        hard_end_unix=plan.get('hard_end_unix'))]))
        except (OSError, ValueError, UnicodeError, KeyError):
            continue
    return dict(schema='R167_CONTROL_NATIVE_CENSUS_V1', hostname=socket.gethostname(),
        observed_unix=time.time(), natives=natives, no_signals=True, no_readouts_read=True)


if __name__ == '__main__':
    print(json.dumps(scan(), sort_keys=True))
