"""Repair only the private receiving adapter, preserve failed test evidence."""

import ast
import json
import os
from pathlib import Path
import subprocess
import tarfile
import time

from receive_math_d import ROOT, SOURCE, MAIN, PYTHON, MATH_ROOT, sha, read, write, require


def main():
    driver_path = 'gpu/orch_r184_think_act_learn.py'
    with tarfile.open(MAIN / 'runtime_overlay.tar.gz') as archive:
        original = archive.extractfile(driver_path).read().decode()
    method = next(node for node in ast.walk(ast.parse(original)) if isinstance(node, ast.FunctionDef) and node.name == '_cpu')
    lines = original.splitlines(keepends=True)
    prior = ''.join(lines[method.lineno - 1:method.end_lineno])
    replacement = "    def _cpu(self, origin):\n        if self.config['trial_id'] == 'R201_MATH_D_node2_clone1':\n            from gpu.r184_cpu_bridge import call\n            return call(self.config, origin)\n"
    replacement += ''.join(prior.splitlines(keepends=True)[1:])
    (SOURCE / driver_path).write_text(original.replace(prior, replacement, 1))
    ready = read(MAIN / 'READY.json')
    files = [name for name in ready['files'] if name.startswith('tests/')]
    support = ROOT / 'test_support'
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONPATH=os.pathsep.join((str(SOURCE), str(SOURCE / 'tests'), str(support))))
    with (ROOT / 'CPU3.log').open('x') as output:
        result = subprocess.run([PYTHON, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *files],
            cwd=SOURCE, env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=180)
    require(result.returncode == 0, 'actual_receiving_pytest_see_CPU3.log')
    import re
    count = re.findall(r'(\d+) passed', (ROOT / 'CPU3.log').read_text())
    require(len(count) == 1, 'actual_pass_count')
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    write(ROOT / 'SOURCE.json', dict(source_root=str(SOURCE), source_pins=pins,
        Main_READY_sha256=sha(MAIN / 'READY.json'), capture_manifest_sha256=sha(ROOT.parent / 'snapshot/MANIFEST.json'),
        transport_adapter='Bound R201_MATH_D trial only; Main default _cpu unchanged'))
    cpu = dict(passed=True, tests_run=int(count[0]), source_pins=pins, log_sha256=sha(ROOT / 'CPU3.log'),
        math_result_sha256=sha(MATH_ROOT / 'RESULT.json'), observed_unix=time.time(),
        failed_initial_test_log_preserved='CPU.log', receiving_interpreter=PYTHON, cuda_visible_devices='')
    write(ROOT / 'CPU.json', cpu)
    write(ROOT / 'control/RECEIVING_CPU.json', cpu)
    print(json.dumps(dict(status='RECEIVING_TESTS_PASS_NOT_LAUNCHED', tests_run=int(count[0]),
        cpu_sha256=sha(ROOT / 'CPU.json'), source_manifest_sha256=sha(ROOT / 'SOURCE.json'))))


if __name__ == '__main__':
    main()
