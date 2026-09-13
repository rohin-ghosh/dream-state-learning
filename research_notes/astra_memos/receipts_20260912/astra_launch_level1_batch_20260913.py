import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


parser = argparse.ArgumentParser()
parser.add_argument('--node', choices=('node1', 'node2'), required=True)
options = parser.parse_args()
driver = Path('/tmp/astra_level1_batch_20260913.py')
assert hashlib.sha256(driver.read_bytes()).hexdigest() == '7a0a7628e04d0f54a3e5b28e307d30b17f3412316d1dcf2ed7a14d7b7e7ebfce'
claim = Path(f'/tmp/astra_level1_batch_{options.node}_20260913_attempt1.launch')
claim.mkdir()
with (claim / 'stdout.log').open('xb') as output:
    process = subprocess.Popen([sys.executable, '-B', str(driver), '--node', options.node],
        stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True,
        env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
receipt = dict(node=options.node, batch_pid=process.pid, started_unix=time.time(),
               log=str(claim / 'stdout.log'), status='BATCH_STARTED_NOT_GPU_RESULT')
with (claim / 'receipt.json').open('x') as stream:
    json.dump(receipt, stream, sort_keys=True)
print(json.dumps(receipt, sort_keys=True), flush=True)
