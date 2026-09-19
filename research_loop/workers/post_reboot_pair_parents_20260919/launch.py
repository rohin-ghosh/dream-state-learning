"""Launch only the two CPU parents on the real VM host, not a private PID sandbox."""

import os
from pathlib import Path
import subprocess
import sys
import time

from parent_service import HERE, REPO, require, write


def main():
    os.umask(0o077)
    require(bool(os.environ.get('NVIDIA_API_KEY')), 'inherited_provider_credential_required')
    private = HERE / 'private'
    private.mkdir(mode=0o700, exist_ok=True)
    for arm in ('learner', 'frozen'):
        for path in Path('/proc').glob('[0-9]*/cmdline'):
            try:
                argv = path.read_bytes().split(b'\0')
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                continue
            if b'--arm' in argv and arm.encode() in argv:
                require(not any(value.endswith((b'/resume_parent.py', b'/post_reboot_pair_parents_20260919/parent_service.py'))
                                for value in argv), 'existing_pair_parent_requires_operator_inspection_' + arm)
        stamp = str(time.time_ns())
        command = [sys.executable, '-B', str(HERE / 'parent_service.py'), '--arm', arm]
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='', PYTHONUNBUFFERED='1')
        with (private / ('PARENT_' + arm + '_' + stamp + '.log')).open('x') as output:
            child = subprocess.Popen(command, cwd=REPO, stdin=subprocess.DEVNULL, stdout=output,
                                     stderr=subprocess.STDOUT, env=environment, start_new_session=True, close_fds=True)
        fields = Path('/proc', str(child.pid), 'stat').read_text().rsplit(')', 1)[1].split()
        receipt = dict(pid=child.pid, start_ticks=fields[19], arm=arm, argv=command, cwd=str(REPO),
                       observed_unix=time.time(), launched_on_real_host=True, native_signals=0,
                       env_nonsecret={key: environment[key] for key in
                                      ('PYTHONDONTWRITEBYTECODE', 'CUDA_VISIBLE_DEVICES', 'PYTHONUNBUFFERED')},
                       secret_env_names=['NVIDIA_API_KEY'], lock=str(private / arm / 'PUBLISHER.lock'))
        write(private / ('LAUNCH_' + arm + '_' + stamp + '.json'), receipt)
        print(arm, child.pid, fields[19], flush=True)


if __name__ == '__main__':
    main()
