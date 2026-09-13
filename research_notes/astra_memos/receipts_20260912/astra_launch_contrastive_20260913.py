import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path('/localhome/local-rohing/astra_diagnostics/contrastive_perception_20260913_attempt1')
DRIVER = Path('/tmp/astra_contrastive_perception_run_20260913.py')
PIN = 'aea1b5d84d6d79efa7dbdd43ab8e93bf0483fd4383531eae363cdbb4b7583d55'
PLAN = 'f0060eb8d37a61aa1d9b25ba6798f19045a8a66cca715755f5e948d216702ec4'
PRECHECK = Path('/tmp/astra_node2_prelaunch_20260913.py')
PRECHECK_PIN = 'b3aa9e36b5e12893f9602a61d4b4575874f23dec58eddacdcab92c2a1b079bff'
LOG = Path('/tmp/astra_contrastive_20260913_attempt1.controller.log')


def launch():
    if hashlib.sha256(DRIVER.read_bytes()).hexdigest() != PIN:
        raise ValueError('driver pin mismatch')
    if hashlib.sha256(PRECHECK.read_bytes()).hexdigest() != PRECHECK_PIN:
        raise ValueError('precheck pin mismatch')
    specification = importlib.util.spec_from_file_location('contrastive_launch_runtime', DRIVER)
    runtime = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(runtime)
    runtime.offline()
    plan, probe = runtime.verify(ROOT, PLAN, native=False)
    if (ROOT / 'controller_started.json').exists() or (ROOT / 'run').exists():
        raise ValueError('existing controller or run; reconcile without retry')
    claim = ROOT.with_name(ROOT.name + '.launch_claim')
    claim.mkdir()
    process = None
    try:
        result = subprocess.run([sys.executable, '-B', str(PRECHECK),
                                 '--gpu-index', str(plan['gpu_index']), '--gpu-uuid', plan['gpu_uuid']],
                                capture_output=True, text=True, timeout=150, check=True)
        runtime.write(claim / 'environment_precheck.json', json.loads(result.stdout))
        if not probe.gpu_state(plan):
            raise ValueError('all-process XML check not vacant')
        runtime.write(claim / 'xml_precheck.json', dict(vacant=True, time=time.time(), gpu_uuid=plan['gpu_uuid']))
        if plan['lease_end'] <= time.time() + 2700 + 180 + 21600:
            raise ValueError('insufficient lease margin')
        command = [sys.executable, '-B', str(DRIVER), 'controller', '--root', str(ROOT),
                   '--plan-sha256', PLAN, '--allow-gpu']
        log = LOG
        with log.open('xb') as output:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output,
                                       stderr=subprocess.STDOUT, start_new_session=True,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
        fields = (Path('/proc') / str(process.pid) / 'stat').read_text().rsplit(')', 1)[1].split()
        receipt = dict(status='LAUNCHED_NOT_RESULT', command=command, pid=process.pid,
                       pgid=process.pid, start_ticks=int(fields[19]), root=str(ROOT),
                       plan_sha256=PLAN, driver_sha256=PIN, launched_unix=time.time(),
                       cap_seconds=2700, log=str(log), gpu_index=plan['gpu_index'],
                       gpu_uuid=plan['gpu_uuid'])
        runtime.write(claim / 'launched.json', receipt)
        print(json.dumps(receipt, sort_keys=True), flush=True)
    except BaseException as error:
        runtime.write(claim / 'failure.json', dict(error=repr(error),
                      pid=None if process is None else process.pid,
                      may_be_running=process is not None, retry=False))
        raise


if __name__ == '__main__':
    launch()
