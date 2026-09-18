"""Warm CPU reverse-SSH routes with each destination's own lease-safe horizon."""

import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


ROOT=Path('/tmp/r233-lease-transport-20260918')
WORKER=Path(__file__).resolve().parent
REPO=WORKER.parents[2]


def safe_end(group):
    day={'node2':20,'node3':24}[group]
    return datetime.datetime(2026,9,day,17,59,20,tzinfo=datetime.timezone.utc).timestamp()


def start_ticks(pid):
    return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]


def remote(wrapper,code):
    result=subprocess.run(['bash',str(REPO/'gpu'/wrapper),'python3 -B -'],input=code,text=True,
        capture_output=True,timeout=25,check=True)
    return json.loads(result.stdout)


def renew(group,wrapper,old_pid):
    output=ROOT/group
    config=json.loads((output/'CONFIG.private.json').read_bytes())
    reference=config['registry']
    raw=Path(reference['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==reference['sha256']
    registry=json.loads(raw)
    end=safe_end(group)
    assert time.time()<end<=config['deadline_unix']
    old_start=start_ticks(old_pid)
    commandline=Path('/proc',str(old_pid),'cmdline').read_bytes().split(b'\0')
    assert Path(commandline[0].decode()).name=='timeout' and any(wrapper.encode() in item for item in commandline)
    routes=[]
    command=['timeout','--signal=TERM','--kill-after=5',str(int(end-time.time())),
        'bash',str(REPO/'gpu'/wrapper),'-N','-o','ExitOnForwardFailure=yes','-o','StreamLocalBindMask=0177']
    for row in registry['rows']:
        physical=row['physical']
        target=f'/tmp/r233-source-lease-{group}-{physical}.sock'
        previous=f'/tmp/r233-lease-caption-{physical}.sock'
        alias=f'/tmp/r226-caption-{physical}.sock'
        routes.append(dict(alias=alias,target=target,previous=previous))
        command+=['-R',target+':'+str(output/'proxy'/(str(physical)+'.sock'))]
    log=(output/'source_lease_tunnel.log').open('ab')
    process=subprocess.Popen(command,cwd=REPO,stdout=log,stderr=log,stdin=subprocess.DEVNULL,start_new_session=True)
    time.sleep(1)
    assert process.poll() is None
    code='''from pathlib import Path
import os,stat,json,subprocess,hashlib,time
routes=ROUTES
listeners=subprocess.check_output(['ss','-xlnH'],text=True)
for row in routes:
 assert row['target'] in listeners and stat.S_ISSOCK(Path(row['target']).stat().st_mode)
 assert Path(row['alias']).resolve()==Path(row['previous'])
 pending=Path(row['alias']+'.sourceleasepending');pending.symlink_to(row['target']);os.replace(pending,row['alias'])
print(json.dumps(dict(unix=time.time(),host_identity_sha256=hashlib.sha256(subprocess.check_output(['hostname']).strip()).hexdigest(),routes=routes,ready=True)))
'''.replace('ROUTES',repr(routes))
    evidence=remote(wrapper,code)
    limit=time.time()+90
    while True:
        proof=remote(wrapper,"import json,subprocess\npaths="+repr([row['previous'] for row in routes])+"\nlines=subprocess.check_output(['ss','-xanH'],text=True).splitlines()\nprint(json.dumps({'active':sum('ESTAB' in line and any(path in line for path in paths) for line in lines)}))")
        if proof['active']==0:
            break
        assert time.time()<limit,'preserve_inflight_no_forced_tunnel_stop'
        time.sleep(.25)
    assert start_ticks(old_pid)==old_start
    os.kill(old_pid,signal.SIGTERM)
    time.sleep(.5)
    assert process.poll() is None
    receipt=dict(unix=time.time(),group=group,local_process_host_alias='operator_vm',remote_endpoint_host_alias=group,
        local_timeout_pid=process.pid,local_timeout_start_ticks=start_ticks(process.pid),
        actual_deadline=end,deadline_utc=datetime.datetime.fromtimestamp(end,datetime.timezone.utc).isoformat(),
        kill_grace_seconds=5,previous_timeout_pid=old_pid,previous_start_ticks=old_start,
        previous_tunnel_drained=True,source_registry_sha256=reference['sha256'],remote=evidence,
        native_signals=[],scoring_calls=0,replayed_requests=0,
        authority='Main explicit node2 Sep20 18Z / node3 Sep24 18Z safe bounds; no lease extension')
    (output/'SOURCE_LEASE_CAPPED.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    values=[renew('node2','ovx_ssh.sh',3044341),renew('node3','ovx2_ssh.sh',3044185)]
    (WORKER/'TRANSPORT_SOURCE_LEASE_CAPPED.json').write_text(json.dumps(values,indent=2)+'\n')
    print(json.dumps(values))
