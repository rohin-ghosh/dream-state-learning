"""Detach the read-only pinned snapshot transfer from the interactive tool process."""

import json
from pathlib import Path
import subprocess
import time


root = Path(__file__).resolve().parent
repo = root.parents[3]
command = ('set -o pipefail; '
    'bash gpu/a40r_ssh.sh "tar -cf - -C /localhome/local-rohing/orch_r177_local_qwen_vision_20260917 snapshot" '
    '| bash gpu/ovx5_ssh.sh "tar -xf - -C /localhome/local-rohing/rohin206_games_20260918/vision"; '
    'STATUS=$?; date -u; printf "MODEL_TRANSFER_EXIT=%s\\n" "$STATUS"; exit "$STATUS"')
with (root / 'MODEL_TRANSFER_2.log').open('x') as output:
    process = subprocess.Popen(['bash', '-c', command], cwd=repo, stdin=subprocess.DEVNULL,
        stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
with (root / 'MODEL_TRANSFER_2_PROCESS.json').open('x') as output:
    json.dump(dict(pid=process.pid, started_unix=time.time(), detached=True, command=command), output)
print(process.pid)
