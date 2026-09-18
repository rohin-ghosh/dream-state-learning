"""Build and transfer a create-only rearm namespace, without learner signals."""

import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[3]
REMOTE = '/localhome/local-rohing/orch_r179_node1_20260917_attempt3'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, document):
    with path.open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.write('\n')


def remote(command, timeout=120, payload=None):
    result = subprocess.run(['bash', 'gpu/a100_ssh.sh', command], cwd=REPOSITORY,
                            text=True, capture_output=True, timeout=timeout, input=payload)
    if result.returncode:
        raise RuntimeError('rearm_remote_command_failed:' + result.stderr[-1500:])
    return json.loads(result.stdout)


def bootstrap():
    from rearm_node1 import PRIOR_OPERATOR_SHA
    original = (HERE / 'node1_operator.py').read_bytes()
    if sha(original) != PRIOR_OPERATOR_SHA:
        raise ValueError('exact_prior_operator_required')
    old_literal = 'REMOTE = Path("/localhome/local-rohing/orch_r179_node1_20260917_attempt2")'
    new_literal = 'REMOTE = Path("' + REMOTE + '")'
    text = original.decode()
    if text.count(old_literal) != 1:
        raise ValueError('one_namespace_literal_only')
    proposed = text.replace(old_literal, new_literal, 1)
    if proposed.replace(new_literal, old_literal, 1) != text:
        raise ValueError('only_operator_output_namespace_changes')
    package = HERE / 'rearm_package'
    package.mkdir()
    files = {'node1_operator.py': proposed.encode()}
    for name in ('test_node1_operator.py', 'receiving_cpu.py', 'rearm_node1.py', 'test_rearm_node1.py', 'PREPARED_NODE1.json'):
        files[name] = (HERE / name).read_bytes()
    for name, path in (
        ('r144_base.py', REPOSITORY / 'gpu/orch_r144_a100_a40r_target_rollout.py'),
        ('policy.py', REPOSITORY / 'gpu/orch_r179_context_survival.py'),
        ('BUILDER_SCOPE.json', HERE.parent / 'BUILDER_SCOPE.json'),
        ('CPU_MAIN_1.log', HERE.parent / 'CPU_MAIN_1.log'),
    ):
        files[name] = path.read_bytes()
    for name, raw in files.items():
        with (package / name).open('xb') as stream:
            stream.write(raw)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
    tested = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(package), '-p', 'test_*.py', '-v'],
                            env=environment, text=True, capture_output=True)
    log = tested.stdout + tested.stderr
    match = re.search(r'Ran (\d+) tests', log)
    if tested.returncode or match is None or int(match.group(1)) != 20:
        raise RuntimeError('rearm_own_CPU_failed:' + log[-3000:])
    stamp = str(time.time_ns())
    with (HERE / ('REARM_CPU_' + stamp + '.log')).open('x') as stream:
        stream.write(log)
    cpu = dict(returncode=0, passed=20, operator_sha256=sha(files['node1_operator.py']),
               test_sha256=sha(files['test_node1_operator.py']), test_log_sha256=sha(log.encode()),
               helper_sha256=sha(files['rearm_node1.py']), helper_test_sha256=sha(files['test_rearm_node1.py']),
               parent_operator_sha256=PRIOR_OPERATOR_SHA, only_operator_namespace_changed=True,
               observed_unix=time.time())
    save(HERE / ('REARM_CPU_' + stamp + '.json'), cpu)
    files['LOCAL_CPU.json'] = json.dumps(cpu, sort_keys=True).encode()
    files['PACKAGE.json'] = json.dumps(dict(files={name: sha(raw) for name, raw in files.items()},
                                          created_unix=time.time()), sort_keys=True).encode()
    for name in ('LOCAL_CPU.json', 'PACKAGE.json'):
        with (package / name).open('xb') as stream:
            stream.write(files[name])
    code = '''import base64,hashlib,json,os,socket,sys
from pathlib import Path
root=Path(sys.argv[1]); payload=json.load(sys.stdin)
assert socket.gethostname()=='[REDACTED_HOST]' and os.getuid()==1395
assert root==Path('/localhome/local-rohing/orch_r179_node1_20260917_attempt3/operator')
assert not root.exists()
decoded={name:base64.b64decode(raw,validate=True) for name,raw in payload['files'].items()}
assert sum(map(len,decoded.values()))<2*1024*1024
for name,raw in decoded.items():
 assert Path(name).name==name and hashlib.sha256(raw).hexdigest()==payload['hashes'][name]
root.mkdir(parents=True)
for name,raw in decoded.items():
 with (root/name).open('xb') as stream: stream.write(raw)
 (root/name).chmod(0o444)
print(json.dumps(dict(path=str(root),files=payload['hashes'],signals_sent=0)))
'''
    command = shlex.join(['env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1', PYTHON,
                          '-B', '-c', code, REMOTE + '/operator'])
    transferred = remote(command, payload=json.dumps(dict(files={name: base64.b64encode(raw).decode() for name, raw in files.items()},
                                                         hashes={name: sha(raw) for name, raw in files.items()})))
    save(HERE / ('REARM_TRANSFER_' + stamp + '.json'), transferred)
    code = '''import hashlib,io,json,sys,time,unittest
from pathlib import Path
root=Path(sys.argv[1]); sys.path.insert(0,str(root))
suite=unittest.defaultTestLoader.discover(str(root),pattern='test_*.py')
stream=io.StringIO(); result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
import torch
assert result.wasSuccessful() and result.testsRun==20 and not torch.cuda.is_initialized()
report=dict(passed=result.testsRun,cuda_initialized=False,log=stream.getvalue(),log_sha256=hashlib.sha256(stream.getvalue().encode()).hexdigest(),operator_sha256=hashlib.sha256((root/'node1_operator.py').read_bytes()).hexdigest(),helper_sha256=hashlib.sha256((root/'rearm_node1.py').read_bytes()).hexdigest(),observed_unix=time.time(),signals_sent=0)
with (root/'RECEIVING_PACKAGE_CPU.json').open('x') as output: json.dump(report,output,sort_keys=True)
print(json.dumps(report))
'''
    command = shlex.join(['env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1', PYTHON,
                          '-B', '-c', code, REMOTE + '/operator'])
    receiving = remote(command)
    if receiving['operator_sha256'] != cpu['operator_sha256'] or receiving['helper_sha256'] != cpu['helper_sha256']:
        raise ValueError('actual_receiving_package_byte_binding')
    path = HERE / ('REARM_RECEIVING_CPU_' + stamp + '.json')
    save(path, receiving)
    print(json.dumps(dict(path=str(path), sha256=sha(path.read_bytes()), passed=receiving['passed'],
                          operator_sha256=cpu['operator_sha256'], helper_sha256=cpu['helper_sha256'],
                          cuda_initialized=False, signals_sent=0)))


if __name__ == '__main__':
    bootstrap()
