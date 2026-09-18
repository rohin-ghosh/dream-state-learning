import hashlib
import json
from pathlib import Path
import time


BASE = Path('/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET')
NAMES = ('creative_b1', 'r203_creative_structured_a4', 'r203_math_comm_b2',
         'r203_math_self_derive_c5')


def read(path):
    return json.loads(path.read_bytes())


def identity(path):
    fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
    command = (path / 'cmdline').read_bytes()
    return dict(pid=int(path.name), parent_pid=int(fields[1]), state=fields[0],
                start_ticks=fields[19], command_sha256=hashlib.sha256(command).hexdigest())


def main():
    processes = []
    for path in Path('/proc').glob('[0-9]*'):
        try:
            command = (path / 'cmdline').read_bytes()
            working_directory = str((path / 'cwd').resolve())
            matches = [name for name in NAMES if str(BASE / name).encode() in command
                       or str(BASE / name) in working_directory]
            if matches:
                processes.append(dict(identity(path), matches=matches))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    rows = []
    for name in NAMES:
        root = BASE / name
        active = read(root / 'ACTIVE_CONTROL.json')
        control = Path(active['control_root'])
        guard = read(control / 'GUARD.json')
        plan = read(Path(guard['plan_path']))
        checkpoints = sorted((root / 'life/checkpoints').glob('sleep_*/COMMIT.json'))
        latest = checkpoints[-1]
        checkpoint = read(latest)
        related_controls = []
        for directory in BASE.glob(name + '*'):
            for marker in sorted((directory / 'control').glob('*.json')):
                if marker.name in ('STARTED.json', 'EXIT.json', 'NATIVE_STARTED.json', 'SPAWNED.json', 'GUARD_STARTED.json'):
                    related_controls.append(dict(path=str(marker), document=read(marker)))
        rows.append(dict(name=name, root=str(root), active=active,
                         guard_keys=sorted(guard), plan_keys=sorted(plan),
                         plan_projection={key: plan.get(key) for key in ('root', 'physical', 'physical_gpu', 'hard_end_unix', 'lease_end_unix', 'trial_id')},
                         control_files=sorted(path.name for path in control.iterdir()),
                         related_controls=related_controls,
                         checkpoint_path=str(latest), checkpoint=checkpoint,
                         checkpoint_files=[dict(path=str(path), bytes=path.stat().st_size) for path in latest.parent.rglob('*') if path.is_file()],
                         stream_files=sorted(path.name for path in (root / 'life/stream').iterdir())))
    print(json.dumps(dict(node='node1', observed_unix=time.time(), matches=processes, lives=rows), indent=2))


if __name__ == '__main__':
    main()
