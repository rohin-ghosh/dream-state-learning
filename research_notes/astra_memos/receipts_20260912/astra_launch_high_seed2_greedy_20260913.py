import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


runner = Path('/tmp/astra_l2_high_seed2_greedy_20260913.py')
root = Path('/localhome/local-rohing/astra_diagnostics/l2_high_seed2_greedy_20260913_attempt1')
prepared_sha = '1d08018f9614d975d83e6f83d0990cf0d007769f833f1170a7c83c710efb588e'
assert hashlib.sha256(runner.read_bytes()).hexdigest() == 'a5f644c6660dc398a330bd51025f1d6c3ee75e7dda8a99310e5f3a91b1dea28f'
assert hashlib.sha256((root / 'prepared.json').read_bytes()).hexdigest() == prepared_sha
assert not (root / 'controller_started.json').exists()
for directory in ('pending', 'running'):
    assert not list((Path('/localhome/local-rohing/queue') / directory).iterdir())
claim = root.with_name(root.name + '.launcher')
claim.mkdir()
command = [sys.executable, '-B', str(runner), 'controller', '--root', str(root),
           '--prepared-sha256', prepared_sha, '--allow-gpu']
with (claim / 'stdout.log').open('xb') as output:
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                               env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1'),
                               start_new_session=True)
fields = Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()
receipt = dict(status='LAUNCHED_NOT_RESULT', root=str(root), pid=process.pid, pgid=int(fields[2]),
               start_ticks=int(fields[19]), started_unix=time.time(), prepared_sha256=prepared_sha,
               command=command, gpu_index=3, gpu_uuid='GPU-e1277146-04f2-c38f-d1ae-1a98132f907e',
               controller_seconds=1200, calls=64, updates=0)
with (claim / 'launched.json').open('x') as stream:
    json.dump(receipt, stream, sort_keys=True)
    stream.write('\n')
print(json.dumps(receipt), flush=True)
