"""Preserve initial proof and test malformed repository request handling."""

import json
import os
from pathlib import Path
import re
import subprocess
import time

from prepare_repo_c import ROOT, SOURCE, PYTHON, read, write, sha, require


def main():
    driver = SOURCE / 'gpu/orch_r184_think_act_learn.py'
    text = driver.read_text()
    before = "            if request(raw_act) is not None:\n                route = 'REPO'\n"
    after = "            try:\n                action = request(raw_act)\n            except (ValueError, TypeError):\n                route = 'REPO'\n            else:\n                if action is not None:\n                    route = 'REPO'\n"
    require(text.count(before) == 1, 'one_unconsumed_repo_adapter')
    driver.write_text(text.replace(before, after, 1))
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONPATH=os.pathsep.join((str(ROOT), str(SOURCE), str(SOURCE / 'tests'), str(ROOT / 'test_support'))))
    files = [str(SOURCE / name) for name in read(ROOT.parent / 'main_ready/READY.json')['files'] if name.startswith('tests/')]
    files.extend([str(SOURCE / 'research_loop/workers/rohin183_repo_learning_20260917/test_tools.py'), str(ROOT / 'repo_receiving_checks.py')])
    with (ROOT / 'CPU2.log').open('x') as output:
        result = subprocess.run([PYTHON, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *files],
            cwd=SOURCE, env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=180)
    require(result.returncode == 0, 'repo_actual_routing_regressions')
    count = int(re.search(r'(\d+) passed', (ROOT / 'CPU2.log').read_text())[1])
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    cpu = dict(passed=True, tests_run=count, source_pins=pins, log_sha256=sha(ROOT / 'CPU2.log'), observed_unix=time.time(),
        repository_smoke_sha256=sha(ROOT / 'REPOSITORY_SMOKE.json'), malformed_repo_request_is_refused_not_native_crash=True)
    source = dict(read(ROOT / 'SOURCE.json'), source_pins=pins)
    for path in [ROOT / 'CPU.json', ROOT / 'SOURCE.json', ROOT / 'control/RECEIVING_CPU.json']:
        path.rename(path.with_name('PRE_DEFENSE_' + path.name))
    write(ROOT / 'CPU.json', cpu)
    write(ROOT / 'SOURCE.json', source)
    write(ROOT / 'control/RECEIVING_CPU.json', cpu)
    print(json.dumps(dict(status='PASS', tests_run=count, cpu_sha256=sha(ROOT / 'CPU.json'), source_sha256=sha(ROOT / 'SOURCE.json'))))


if __name__ == '__main__':
    main()
