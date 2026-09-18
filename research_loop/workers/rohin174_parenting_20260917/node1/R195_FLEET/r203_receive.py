"""Apply Main's released overlay and arm the existing exact-boundary handoff."""

import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile
import time


OWN = Path(__file__).resolve().parent
BASE = Path('/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
READY_SHA = '4ae57685c0b66de37a96e53442d187da968c7e6d96af051e4ac59db5f1947063'
OVERLAY_SHA = 'ca6c1b006260c677bdbb003baf52333e354d7a9e0ec266ebdacac08992f89544'
PART_SHA = '48921afaf6c1a7dec7fbe7cbb79c3be8c52bd9612cbcdad3ff6da64fc7469e30'


def sha(path):
    with Path(path).open('rb') as incoming:
        return hashlib.file_digest(incoming, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    with Path(path).open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2)


def overlay(path, destination, expected):
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        assert len(members) == len(expected) and {item.name for item in members} == set(expected)
        for member in members:
            name = Path(member.name)
            assert member.isfile() and not name.is_absolute() and '..' not in name.parts
            assert hashlib.file_digest(archive.extractfile(member), 'sha256').hexdigest() == expected[member.name]
            target = destination / name
            if target.exists():
                assert target.is_file() and not target.is_symlink() and target.stat().st_nlink == 1
                target.chmod(0o600)
        archive.extractall(destination, filter='data')
    assert all(sha(destination/name) == expected_hash for name, expected_hash in expected.items())


def start_process(root, name, command, environment):
    with (root/(name+'.log')).open('xb', buffering=0) as output:
        process = subprocess.Popen(command, cwd=root/'source', env=environment,
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    ticks = (Path('/proc')/str(process.pid)/'stat').read_text().rsplit(') ', 1)[1].split()[19]
    receipt = dict(pid=process.pid, start_ticks=ticks, started_unix=time.time())
    write(root/(name+'_STARTED.json'), receipt)
    return receipt


def configure(root):
    import sys
    root = Path(root)
    assert root.parent == BASE and os.getuid() == 1395 and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    arm = read(root/'ARM.json')
    assert arm['physical'] in (2, 3, 4, 5) and arm['remote_root'] == str(root)
    assert (root/'STAGED.json').is_file() and not (root/'control').exists()
    assert sha(root/'R203_READY.json') == READY_SHA and sha(root/'r203_runtime_overlay.tar.gz') == OVERLAY_SHA
    ready = read(root/'R203_READY.json')
    assert ready['status'] == 'CPU_TESTED_NOT_LIVE' and ready['archive_sha256'] == OVERLAY_SHA
    assert len(ready['files']) == 37 and all(item.get('failed', 0) == 0 for item in ready['validation'])
    source = root/'source'
    overlay(root/'r203_runtime_overlay.tar.gz', source, ready['files'])
    adapted = read(root/'ADAPTER_FILES.json')
    overlay(root/'R203_RECEIVING_ADAPTER.tar', source, adapted)
    received = dict(ready['files'], **adapted)
    plan = read(root/'PLAN_DRAFT_WAIT_R203.json')['plan']
    plan.update(ready['required_native_options'])
    plan['think_act_learn'].update(ready['required_driver_options'])
    plan['think_act_learn'].update(trial_id=arm['trial_id'],
        environment_facts=arm['task']+' A confined standard-library Python tool is available through '
        'an external CPU bridge, without network, GPU, home access, SymPy, mpmath or Torch. '
        'Only returned receipts establish execution. No peer is connected. Parent guidance is '
        'offered for complete cycles52–54, then withdrawn for55–57. No future original-C2 inbox is copied.')
    if arm['structured']:
        plan['think_act_learn']['structured_think_policy'] = ready['optional_structured_think_policy']
    else:
        plan['think_act_learn'].pop('structured_think_policy', None)
    startup = source/'context'/Path(plan['startup_context']['path']).name
    assert sha(startup) == plan['startup_context']['sha256']
    plan['startup_context']['path'] = str(startup)
    write(root/'PLAN_R203.json', plan)
    write(root/'R203_OVERLAY_BINDING.json', dict(ready_sha256=READY_SHA, archive_sha256=OVERLAY_SHA,
        received_files=received, adapter_files=adapted, plan_sha256=sha(root/'PLAN_R203.json'),
        Main_default_CPU_unchanged=True, no_broad_tests_repeated=True, observed_unix=time.time()))
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(source), OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    for action in ('prepare', 'check'):
        with (root/('R203_'+action+'.log')).open('xb') as output:
            result = subprocess.run([PYTHON, '-B', str(root/'receive_creative_b_v3.py'), action],
                cwd=source, env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=300)
        assert result.returncode == 0, 'receiving_'+action+'_failed_preserved_log'
    sys.path.insert(0, str(source))
    from gpu.orch_r127_pilot_console import publish_parent
    part = (root/'PART_ONE_INPUT.txt').read_text()
    assert hashlib.sha256(part.encode()).hexdigest() == PART_SHA
    assert not (root/'R202_PART_ONE_INTENT.json').exists()
    write(root/'R202_PART_ONE_INTENT.json', dict(text_sha256=PART_SHA, authorized_speaker='Rohin',
        new_clone_input_ordinal=1, first_new_parent_opening_must_wait_for_Rohin_render=True,
        created_unix=time.time()))
    with (root/'R202_PART_ONE.txt').open('x') as output:
        output.write(part)
    publication = publish_parent(str(root/'life'), 'Rohin', part)
    publication.update(status='PUBLISHED_NOT_CONSUMED', published_unix=time.time(),
        text_sha256=PART_SHA, speaker='Rohin', new_clone_input_ordinal=1,
        original_C2_calls=0, parent_opening_published=False)
    write(root/'R202_PART_ONE_PUBLICATION.json', publication)
    bridge = start_process(root, 'BRIDGE', [PYTHON, '-B', str(source/'gpu/r184_cpu_bridge.py'),
        '--config', str(root/'BRIDGE.json')], environment)
    deadline = time.monotonic()+20
    while not list((root/'bridge_receipts').glob('READY_*.json')) and time.monotonic() < deadline:
        assert Path('/proc', str(bridge['pid'])).exists(), 'bridge_exited_before_ready'
        time.sleep(.2)
    assert list((root/'bridge_receipts').glob('READY_*.json')), 'existing_bridge_readiness'
    operator = start_process(root, 'RETIRE_OPERATOR', [PYTHON, '-B', str(root/'retire_support.py')], environment)
    write(root/'R203_OPERATOR_PREPARED.json', dict(observed_unix=time.time(), arm=arm['name'],
        physical=arm['physical'], fixed_source=51, fixed_context=5846, bridge=bridge,
        retirement_operator=operator, actual_loaded=False, no_degradation_claim=True))
    print(json.dumps(read(root/'R203_OPERATOR_PREPARED.json')), flush=True)


def deliver():
    repo = OWN.parents[4]
    ready_root = repo/'research_loop/workers/rohin201_c2_clones_20260917/r203_ready'
    assert sha(ready_root/'READY.json') == READY_SHA and sha(ready_root/'runtime_overlay.tar.gz') == OVERLAY_SHA
    files = {
        'R203_READY.json': ready_root/'READY.json',
        'r203_runtime_overlay.tar.gz': ready_root/'runtime_overlay.tar.gz',
        'ADAPTER_FILES.json': OWN/'R203_ADAPTER_FILES.json',
        'R203_RECEIVING_ADAPTER.tar': OWN/'R203_RECEIVING_ADAPTER.tar',
        'receive_creative_b_v3.py': OWN/'receive_creative_b.py',
        'retire_support.py': OWN/'retire_support.py',
        'r203_receive.py': Path(__file__),
        'PART_ONE_INPUT.txt': repo/'research_notes/analysis/R202_CLONE_PART_ONE_2026-09-17.txt',
    }
    archive_path = OWN/'R203_DELIVERY.tar'
    with tarfile.open(archive_path, 'x') as archive:
        for name, path in files.items():
            archive.add(path, arcname=name)
    expected = sha(archive_path)
    specs = read(OWN/'R203_SELECTED_ARMS.json')['arms']
    for arm in specs:
        root = arm['remote_root']
        code = f'''import hashlib,json,pathlib,subprocess,sys,tarfile,time,os
root=pathlib.Path({root!r})
assert (root/'STAGED.json').is_file() and not (root/'R203_READY.json').exists()
path=root/'R203_DELIVERY.tar'
with path.open('xb') as output:
 while chunk:=sys.stdin.buffer.read(1024*1024):output.write(chunk)
with path.open('rb') as incoming:assert hashlib.file_digest(incoming,'sha256').hexdigest()=={expected!r}
with tarfile.open(path) as archive:
 assert all(member.isfile() and pathlib.Path(member.name).name==member.name for member in archive.getmembers())
 archive.extractall(root,filter='data')
with (root/'R203_CONFIGURE.log').open('xb',buffering=0) as output:
 process=subprocess.Popen([{PYTHON!r},'-B',str(root/'r203_receive.py'),'configure',str(root)],cwd=root,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),stdin=subprocess.DEVNULL,
  stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
receipt=dict(pid=process.pid,start_ticks=(pathlib.Path('/proc')/str(process.pid)/'stat').read_text().rsplit(') ',1)[1].split()[19],started_unix=time.time())
with (root/'R203_CONFIGURE_STARTED.json').open('x') as output:json.dump(receipt,output,sort_keys=True)
print(json.dumps(receipt))'''
        with archive_path.open('rb') as incoming:
            result = subprocess.run(['bash', 'gpu/a100_ssh.sh', '/usr/bin/python3 -B -c '+shlex.quote(code)],
                cwd=repo, stdin=incoming, capture_output=True, timeout=45)
        write(OWN/('R203_RECEIVER_DISPATCH_'+str(arm['physical'])+'.json'), dict(returncode=result.returncode,
            stdout=result.stdout.decode(), stderr=result.stderr.decode(), observed_unix=time.time()))
        assert result.returncode == 0, 'delivery_unknown_reconcile_no_retry'
        print(arm['name']+': receiving/configuration dispatched; not yet LOADED', flush=True)


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['deliver']:
        deliver()
    elif len(sys.argv) == 3 and sys.argv[1] == 'configure':
        configure(sys.argv[2])
    else:
        raise ValueError('expected deliver or configure ROOT')
