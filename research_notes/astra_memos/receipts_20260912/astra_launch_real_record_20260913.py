import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def load(name, path, checksum):
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == checksum
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


runtime_path = '/tmp/astra_level1_real_record_run_20260913.py'
runtime = load('real_record_runtime', runtime_path,
               '3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e')
batch = load('checked_level1_batch', '/tmp/astra_level1_next_batch_20260913.py',
             '03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2')
root = '/localhome/local-rohing/astra_diagnostics/level1_real_record_20260913_attempt1'
plan_sha = '5895cf64abd372a598be802670789dbd0f7f99b04d1503184f7fd97ba8861e54'
runtime.offline()
plan, core, helper, probe, dependencies = runtime.verify(root, plan_sha, native=False)
precheck = Path('/tmp/astra_level1_roster_20260913_attempt1/prechecks.json')
assert batch.digest(precheck) == '71e8eaa0c326ddef4414539684d20315e3752c48ce425a280438100e32815929'
config = json.loads(precheck.read_text())['node2']
assert set(Path(root).iterdir()) == {Path(root) / name for name in ('prepare_started.json', 'initial_prompts.json', 'plan.json')}
claim = Path(root + '.launcher')
claim.mkdir()
process = None
try:
    runtime.write(claim / 'precheck.json', batch.reservations(config, plan['gpu_index'], plan['gpu_uuid']))
    assert probe.gpu_state(plan), 'all-process vacancy failed'
    assert plan['lease_end'] > time.time() + 1800 + 180 + 21600
    command = [sys.executable, '-B', runtime_path, 'controller', '--root', root,
               '--plan-sha256', plan_sha, '--allow-gpu']
    with (claim / 'stdout.log').open('xb') as output:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True,
                                   env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['gpu_uuid']))
    receipt = dict(status='LAUNCHED_NOT_RESULT', pid=process.pid, pgid=process.pid,
                   identity=batch.identity(Path('/proc') / str(process.pid)), started_unix=time.time(),
                   root=root, plan_sha256=plan_sha, gpu_index=plan['gpu_index'], gpu_uuid=plan['gpu_uuid'],
                   command=command, controller_seconds=1800, collection_seconds=180)
    runtime.write(claim / 'launched.json', receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)
except BaseException as error:
    runtime.write(claim / 'failure.json', dict(error=repr(error), pid=None if process is None else process.pid,
                                             controller_may_be_running=process is not None, retry=False))
    raise
