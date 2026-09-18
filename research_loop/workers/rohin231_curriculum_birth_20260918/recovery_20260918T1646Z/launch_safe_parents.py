"""Keep the inherited provider environment private; never signal a learner."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    own = Path(__file__).resolve().parent
    private = own / 'private'
    if not os.environ.get('NVIDIA_API_KEY'):
        raise ValueError('existing_provider_environment_missing')
    commands = {
        'learner_wall': [sys.executable, '-B', str(own / 'parent_wall_guard.py'),
            '--pid', '2779281', '--start-ticks', '185782871'],
        'frozen': [sys.executable, '-B', str(own / 'resume_parent.py'),
            '--arm', 'frozen', '--deadline', '1789754400'],
    }
    for label, command in commands.items():
        receipt = private / ('SAFE_PARENT_LAUNCH_' + label + '.json')
        if receipt.exists():
            raise ValueError('never_duplicate_parent_launcher_' + label)
        with (private / ('SAFE_PARENT_' + label + '.log')).open('x') as output:
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), start_new_session=True, close_fds=True)
        fields = Path('/proc', str(child.pid), 'stat').read_text().rsplit(')', 1)[1].split()
        document = dict(observed_unix=time.time(), label=label, pid=child.pid, start_ticks=fields[19],
            deadline_unix=1789754400, native_signals=0, provider_secret_written=False,
            actual_provider_response_not_yet_claimed=True)
        with receipt.open('x') as handle:
            json.dump(document, handle, indent=2)
        print(json.dumps(document, sort_keys=True))


if __name__ == '__main__':
    main()
