import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


driver = Path('/tmp/astra_level1_next_batch_20260913.py')
assert hashlib.sha256(driver.read_bytes()).hexdigest() == '03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2'
claim = Path('/tmp/astra_level1_a40_fallback_20260913_attempt2.launch')
claim.mkdir()
command = [sys.executable, '-B', str(driver), '--roster',
           '/tmp/astra_level1_a40_fallback_roster_20260913_attempt2/roster.json',
           '--roster-sha256', '781b9a3e21786c3b5ff5a78f97933fcf738b6e5d18720cb447c5e06140fb6179',
           '--node', 'node1', '--batch-name', 'batch_node1']
with (claim / 'stdout.log').open('xb') as output:
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output,
                               stderr=subprocess.STDOUT, start_new_session=True,
                               env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
receipt = dict(node='node1', batch_pid=process.pid, started_unix=time.time(),
               log=str(claim / 'stdout.log'), command=command, status='BATCH_STARTED_NOT_GPU_RESULT')
with (claim / 'receipt.json').open('x') as stream:
    json.dump(receipt, stream, sort_keys=True)
print(json.dumps(receipt, sort_keys=True), flush=True)
