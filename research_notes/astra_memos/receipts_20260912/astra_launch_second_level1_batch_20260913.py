import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


parser = argparse.ArgumentParser()
parser.add_argument('--node', choices=('node2', 'a100'), required=True)
arguments = parser.parse_args()
driver = Path('/tmp/astra_level1_next_batch_20260913.py')
assert hashlib.sha256(driver.read_bytes()).hexdigest() == '03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2'
claim = Path(f'/tmp/astra_level1_second_batch_{arguments.node}_20260913_attempt1.launch')
claim.mkdir()
command = [sys.executable, '-B', str(driver), '--roster',
           '/tmp/astra_level1_second_roster_20260913_attempt1_clockfix/roster.json',
           '--roster-sha256', '2bca9e4a66cc576993119fc1d5fddcac77de7cc3f93686327b962c45c2d17c69',
           '--node', arguments.node, '--batch-name', 'batch_' + arguments.node]
with (claim / 'stdout.log').open('xb') as output:
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output,
                               stderr=subprocess.STDOUT, start_new_session=True,
                               env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
receipt = dict(node=arguments.node, batch_pid=process.pid, started_unix=time.time(),
               log=str(claim / 'stdout.log'), command=command, status='BATCH_STARTED_NOT_GPU_RESULT')
with (claim / 'receipt.json').open('x') as stream:
    json.dump(receipt, stream, sort_keys=True)
print(json.dumps(receipt, sort_keys=True), flush=True)
