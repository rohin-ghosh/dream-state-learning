"""New lease-bound transports; preserve source registries and all in-flight RPCs."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


WORKER = Path(__file__).resolve().parent
REPO = WORKER.parents[2]
DEADLINE = 1790791170
LEASE = 1790812800


def main():
    old = Path('/tmp/r233-transport32-20260918T1721Z')
    root = Path('/tmp/r233-lease-transport-20260918')
    root.mkdir(mode=0o700, exist_ok=False)
    source = root / 'source'
    shutil.copytree(old / 'source', source)
    relative = Path('research_loop/workers/rohin233_ovx4_recovery_20260918')
    shutil.copyfile(WORKER / 'transport_proxy.py', source / relative / 'transport_proxy.py')
    results = []
    for name, wrapper in [('node3','ovx2'), ('node2','ovx')]:
        output = root / name
        output.mkdir(mode=0o700)
        config = json.loads((old / (name+'_CONFIG.private.json')).read_bytes())
        registry = json.loads(Path(config['registry']['path']).read_bytes())
        assert hashlib.sha256(Path(config['registry']['path']).read_bytes()).hexdigest() == config['registry']['sha256']
        config.update(root=str(output / 'proxy'), shared_forward=str(output / 'shared.sock'),
            deadline_unix=DEADLINE, lease_boundary_unix=LEASE)
        path = output / 'CONFIG.private.json'
        path.write_text(json.dumps(config))
        environment = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1')
        log = (output / 'transport.log').open('ab')
        bound = ['timeout', str(int(DEADLINE-time.time()))]
        upstream = subprocess.Popen(bound+['bash','gpu/ovx4_ssh.sh','-N','-o','ExitOnForwardFailure=yes',
            '-o','StreamLocalBindMask=0177','-L',config['shared_forward']+':'+config['shared_root']+'/native.sock'],
            cwd=REPO, stdout=log, stderr=log, start_new_session=True)
        proxy = subprocess.Popen(bound+['/usr/bin/python3','-B',str(source / relative / 'transport_large_proxy.py'),
            '--config',str(path)], cwd=REPO, env=environment, stdout=log, stderr=log, start_new_session=True)
        end = time.time()+20
        while not (output / 'proxy/READY.json').exists() or not Path(config['shared_forward']).exists():
            assert time.time() < end and proxy.poll() is None and upstream.poll() is None
            time.sleep(.1)
        arguments = bound+['bash','gpu/'+wrapper+'_ssh.sh','-N','-o','ExitOnForwardFailure=yes','-o','StreamLocalBindMask=0177']
        routes = []
        for row in registry['rows']:
            temporary = '/tmp/r233-lease-caption-'+str(row['physical'])+'.sock'
            original = '/tmp/r226-caption-'+str(row['physical'])+'.sock'
            arguments += ['-R',temporary+':'+str(output / 'proxy' / (str(row['physical'])+'.sock'))]
            routes.append((original,temporary))
        downstream = subprocess.Popen(arguments, cwd=REPO, stdout=log, stderr=log, start_new_session=True)
        time.sleep(.8)
        assert downstream.poll() is None
        code = '''import json,os,pathlib,stat,subprocess
routes=ROUTES
listeners=subprocess.check_output(['ss','-xlnH'],text=True)
for original,target in routes:
 assert target in listeners and stat.S_ISSOCK(pathlib.Path(target).stat().st_mode)
 pending=pathlib.Path(original+'.leasepending');pending.symlink_to(target);os.replace(pending,original)
print(json.dumps(dict(routes=len(routes),ready=True)))
'''.replace('ROUTES',repr(routes))
        result = subprocess.run(['bash','gpu/'+wrapper+'_ssh.sh','python3 -B -'], input=code,
            cwd=REPO, text=True, capture_output=True, timeout=25)
        assert result.returncode == 0, result.stderr[-400:]
        results.append(dict(group=name, unix=time.time(), proxy=json.loads((output / 'proxy/READY.json').read_bytes()),
            upstream_wrapper_pid=upstream.pid, downstream_wrapper_pid=downstream.pid,
            deadline_unix=DEADLINE, authenticated_registry_sha256=config['registry']['sha256'],
            preserved_future_frontiers=True, routes=len(routes), native_signals=[], history_replays=0))
    (WORKER / 'LEASE_TRANSPORTS_RENEWED.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results))


if __name__ == '__main__':
    main()
