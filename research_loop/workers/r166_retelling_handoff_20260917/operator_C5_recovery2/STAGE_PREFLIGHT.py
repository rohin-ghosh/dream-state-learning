import json
from pathlib import Path
import subprocess
import time
from gpu import orch_r166_retelling_handoff as handoff

operator = Path('/localhome/local-rohing/orch_r166_retelling_operator_C5_20260917_recovery2')
output = operator.parent / 'orch_r166_retelling_C5_20260917_recovery2'
request = handoff.stage_recovery(operator / 'CPU.json', output)
source = output / 'source'
command = [str(handoff.saved.PYTHON), '-B', '-m', handoff.MODULE,
           'preflight-recovery', '--output', str(output)]
environment = handoff.saved.environment(source)
assert environment['CUDA_VISIBLE_DEVICES'] == ''
result = subprocess.run(command, cwd=source, env=environment,
    capture_output=True, text=True, timeout=240)
handoff.saved.write(operator / 'C5_SUBPROCESS.json', dict(command=command, cwd=str(source),
    returncode=result.returncode, stdout=result.stdout, stderr=result.stderr,
    CUDA_VISIBLE_DEVICES=environment['CUDA_VISIBLE_DEVICES'], observed_unix=time.time()))
assert result.returncode == 0, result.stderr
ready = json.loads(result.stdout)
assert ready == handoff.saved.read(output / 'readiness/READY.json')
receipt = dict(request=request, ready=handoff.saved.reference(output / 'readiness/READY.json'),
    document=ready, subprocess=handoff.saved.reference(operator / 'C5_SUBPROCESS.json'),
    helper_sha256=handoff.saved.sha(source / handoff.RELATIVE),
    tests_sha256=handoff.saved.sha(source / handoff.TEST_RELATIVE),
    no_GO=True, no_dispatch=True, no_signals=True, observed_unix=time.time())
handoff.saved.write(operator / 'C5_PREPARATION.json', receipt)
print(json.dumps(receipt, sort_keys=True))
