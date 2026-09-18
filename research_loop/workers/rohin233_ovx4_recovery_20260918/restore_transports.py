"""One finite renewal of expired authenticated caption bridges, future ACTs only."""

import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import time


REPO = Path(__file__).resolve().parents[3]
WORKER = Path(__file__).resolve().parent
MODULE = 'research_loop.workers.rohin233_ovx4_recovery_20260918'
DEADLINE = 1789754370


def ssh(alias, code):
    result = subprocess.run(['bash', str(REPO / ('gpu/' + alias + '_ssh.sh')),
        'python3 -c ' + shlex.quote(code)], check=True, text=True, capture_output=True, timeout=35)
    return json.loads(result.stdout)


def receipt(path, document):
    payload = json.dumps(document, indent=2, sort_keys=True) + '\n'
    patch = '*** Begin Patch\n*** Add File: ' + str(path) + '\n' + ''.join('+'+line+'\n' for line in payload.splitlines()) + '*** End Patch\n'
    subprocess.run(['apply_patch', patch], check=True, capture_output=True)


def main():
    assert 120 < DEADLINE - time.time() < 3600 and DEADLINE + 21600 <= 1789776000
    root = Path('/tmp/r233-caption-recovery-20260918T1712Z')
    root.mkdir(mode=0o700, exist_ok=True)
    definitions = [dict(name='node3', wrapper='ovx2',
        registry=REPO / 'research_loop/workers/rohin205_node3_20260918/R226_CAPTION_BINDINGS.json',
        local_source=Path('/tmp/r230-extra-caption-binding/source'),
        native_source='/localhome/local-rohing/orch_r227_caption_transport_20260918T084331Z/source',
        scorer_source='/localhome/local-rohing/orch_r227_caption_transport_20260918T084331Z/source',
        shared_root='/localhome/local-rohing/orch_r226_shared_caption_20260918/attempt2'),
        dict(name='node2', wrapper='ovx', registry=Path('/tmp/r230-extra-caption-binding/REGISTRY.json'),
        local_source=Path('/tmp/r230-extra-caption-binding/source'),
        native_source='/localhome/local-rohing/orch_r230_extra_caption_scorer_20260918/source',
        scorer_source='/localhome/local-rohing/orch_r230_extra_caption_scorer_20260918/source',
        shared_root='/localhome/local-rohing/orch_r230_extra_caption_scorer_20260918')]
    results = []
    for definition in definitions:
        if definition['name'] == 'node3' and (root / 'node3/proxy/READY.json').exists():
            ready_path = root / 'node3/proxy/READY.json'
            ready = json.loads(ready_path.read_bytes())
            assert Path('/proc', str(ready['pid'])).exists()
            tunnel_args = Path('/proc/9845/cmdline').read_bytes().decode().split('\0')
            listeners = subprocess.check_output(['ss', '-xlnH'], text=True)
            for physical in (0, 3, 5, 6, 7):
                stable = Path('/tmp/r226-caption-proxy') / (str(physical)+'.sock')
                target = root / 'node3/proxy' / stable.name
                assert str(stable) not in listeners and target.is_socket()
                assert '/tmp/r226-caption-'+str(physical)+'.sock:'+str(stable) in tunnel_args
                backup = stable.with_name(stable.name+'.before-r233-recovery')
                assert not backup.exists() and not backup.is_symlink()
                stable.rename(backup)
                temporary = stable.with_name(stable.name+'.r233.pending')
                temporary.symlink_to(target)
                os.replace(temporary, stable)
            result = dict(unix=time.time(), group='node3', proxy=ready, existing_downstream_pid=9845,
                stable_routes_rebound=5, native_signals=[], historical_replays=0,
                first_future_score='pending', runtime_root=str(root / 'node3'), deadline_unix=DEADLINE)
            receipt(WORKER / 'TRANSPORT_NODE3_READY.json', result)
            print(json.dumps(dict(group='node3', proxy_pid=ready['pid'], status='EXISTING_TUNNEL_FUTURE_ROUTES_RESTORED')), flush=True)
            continue
        output = root / definition['name']
        output.mkdir(mode=0o700)
        registry = json.loads(definition['registry'].read_bytes())
        frontiers = ssh(definition['wrapper'], 'import json\nfrom pathlib import Path\nrows='+repr(registry['rows'])+'''
result=[]
for row in rows:
 paths=(Path(row['life_root'])/'stream/records').glob('*.json')
 index=max(int(path.stem) for path in paths if path.stem.isdigit())
 record=json.loads((Path(row['life_root'])/'stream/records'/f'{index:020d}.json').read_bytes())
 assert record['journal_id']==row['journal']['journal_id']
 result.append(dict(session_id=row['session_id'],minimum_origin_record_index=index+1))
print(json.dumps(result))
''')
        for row in registry['rows']:
            row['minimum_origin_record_index'] = next(item['minimum_origin_record_index'] for item in frontiers if item['session_id'] == row['session_id'])
            assert row['host_alias'] == definition['wrapper']
        local_registry = output / 'REGISTRY.private.json'
        local_registry.write_text(json.dumps(registry))
        source = output / 'source'
        shutil.copytree(definition['local_source'], source, ignore=shutil.ignore_patterns('__pycache__'))
        relative = Path('research_loop/workers/rohin233_ovx4_recovery_20260918/transport_proxy.py')
        (source / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(WORKER / 'transport_proxy.py', source / relative)
        config = dict(root=str(output / 'proxy'), deadline_unix=DEADLINE, lease_boundary_unix=1789776000,
            registry=dict(path=str(local_registry), sha256=hashlib.sha256(local_registry.read_bytes()).hexdigest()),
            native_source=definition['native_source'], scorer_source=definition['scorer_source'],
            shared_root=definition['shared_root'], shared_forward=str(output / 'shared.sock'))
        config_path = output / 'CONFIG.private.json'
        config_path.write_text(json.dumps(config))
        environment = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1')
        subprocess.run(['/usr/bin/python3', '-B', '-c', 'from '+MODULE+'.transport_proxy import validate_deadline;validate_deadline('+str(DEADLINE)+',1789776000,__import__("time").time())'],
            cwd=source, env=environment, check=True, capture_output=True)
        log = (output / 'transport.log').open('ab')
        seconds = str(int(DEADLINE-time.time()))
        upstream = subprocess.Popen(['timeout', seconds, 'bash', 'gpu/ovx4_ssh.sh', '-N',
            '-o', 'ExitOnForwardFailure=yes', '-o', 'StreamLocalBindMask=0177', '-L',
            config['shared_forward']+':'+definition['shared_root']+'/native.sock'], cwd=REPO,
            stdout=log, stderr=log, start_new_session=True)
        proxy = subprocess.Popen(['timeout', seconds, '/usr/bin/python3', '-B', str(source / relative),
            '--config', str(config_path)], cwd=REPO, env=environment, stdout=log, stderr=log, start_new_session=True)
        until = time.monotonic()+20
        ready = output / 'proxy/READY.json'
        while not ready.exists() or not Path(config['shared_forward']).exists():
            assert time.monotonic() < until and proxy.poll() is None and upstream.poll() is None, 'actual_proxy_ready'
            time.sleep(.1)
        endpoints = ['/tmp/r226-caption-'+str(row['physical'])+'.sock' for row in registry['rows']]
        preserved = ssh(definition['wrapper'], 'import json,os,stat,subprocess\nfrom pathlib import Path\npaths='+repr(endpoints)+'''
listeners=subprocess.check_output(['ss','-xlnH'],text=True)
saved=[]
for name in paths:
 assert name not in listeners,'no_live_listener_replacement'
 path=Path(name)
 if path.exists() or path.is_symlink():
  assert path.is_symlink() or stat.S_ISSOCK(path.lstat().st_mode)
  destination=path.with_name(path.name+'.before-r233-recovery-1711')
  assert not destination.exists() and not destination.is_symlink()
  path.rename(destination)
  saved.append(dict(endpoint=name,previous_inode=destination.lstat().st_ino))
print(json.dumps(saved))
''')
        arguments = ['timeout', str(int(DEADLINE-time.time())), 'bash', 'gpu/'+definition['wrapper']+'_ssh.sh',
            '-N', '-o', 'ExitOnForwardFailure=yes', '-o', 'StreamLocalBindMask=0177']
        for row, endpoint in zip(registry['rows'], endpoints):
            arguments += ['-R', endpoint+':'+str(output / 'proxy' / (str(row['physical'])+'.sock'))]
        downstream = subprocess.Popen(arguments, cwd=REPO, stdout=log, stderr=log, start_new_session=True)
        time.sleep(1)
        assert downstream.poll() is None and proxy.poll() is None and upstream.poll() is None
        endpoint_proof = ssh(definition['wrapper'], 'import json,stat,subprocess\nfrom pathlib import Path\npaths='+repr(endpoints)+'''
listeners=subprocess.check_output(['ss','-xlnH'],text=True)
proof=[]
for name in paths:
 status=Path(name).stat()
 assert stat.S_ISSOCK(status.st_mode) and stat.S_IMODE(status.st_mode)==0o600 and name in listeners
 proof.append(dict(endpoint=name,mode='0600',listening=True))
print(json.dumps(proof))
''')
        result = dict(unix=time.time(), group=definition['name'], deadline_unix=DEADLINE,
            source_sha256=hashlib.sha256((source / relative).read_bytes()).hexdigest(),
            proxy=json.loads(ready.read_bytes()), upstream_pid=upstream.pid, downstream_pid=downstream.pid,
            endpoints=endpoint_proof, preserved_endpoints=preserved, frontier=frontiers,
            native_signals=[], historical_replays=0, first_future_score='pending', runtime_root=str(output))
        results.append(result)
        receipt(WORKER / ('TRANSPORT_'+definition['name'].upper()+'_READY.json'), result)
        print(json.dumps(dict(group=definition['name'], proxy_pid=result['proxy']['pid'], endpoints=len(endpoints), status='LISTENERS_READY_FUTURE_SCORE_PENDING')), flush=True)


if __name__ == '__main__':
    main()
