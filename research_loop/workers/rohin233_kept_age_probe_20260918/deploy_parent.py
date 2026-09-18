"""Deploy only the tested CPU envelope, keeping both GPU owners untouched."""

import base64
import hashlib
import json
from pathlib import Path
import subprocess


WORKER = Path(__file__).resolve().parent
ROOT = '/localhome/local-rohing/orch_r233_base_parent_20260918'


def main():
    raw = (WORKER / 'parent_bridge.py').read_bytes()
    payload = '''import base64,hashlib,json,pathlib,os,subprocess,time
root=pathlib.Path(ROOT)
source=base64.b64decode(SOURCE)
assert hashlib.sha256(source).hexdigest()==SHA
assert not root.exists()
root.mkdir(mode=0o700)
(root/'parent_bridge.py').write_bytes(source)
compile(source,str(root/'parent_bridge.py'),'exec')
namespace={'__file__':str(root/'parent_bridge.py'),'__name__':'receiving_test'}
exec(compile(source,str(root/'parent_bridge.py'),'exec'),namespace)
epoch=pathlib.Path('/localhome/local-rohing/orch_r226_base_schedule_20260918/r232_epoch3')
binding=json.loads((epoch/'BINDING.json').read_bytes())
assert binding['controller']['plan']['condition']=='R224_CONTINUOUS_FROZEN_BASE'
assert binding['backend']['kind']=='FROZEN_BASE_NO_LORA_NO_LEARNING'
endpoint=epoch/'scorer/base.sock'
for role,pid in [('player',162813),('scorer',162806)]:
 assert subprocess.check_output(['systemctl','show','orch-r232-base-epoch3-'+role+'-20260918','--property=MainPID','--value'],text=True).strip()==str(pid)
config=dict(endpoint=str(endpoint),endpoint_inode=endpoint.stat().st_ino,
 player_pid=162813,player_start_ticks=namespace['proc_start'](162813),
 scorer_pid=162806,scorer_start_ticks=namespace['proc_start'](162806),
 generation_root='/localhome/local-rohing/orch_r224_continuous_base_20260918/player/private/generations',
 deadline_unix=1789739990,condition=binding['controller']['plan']['condition'],
 rule_sha256=binding['controller']['plan']['rule_sha256'])
assert 0<config['deadline_unix']-time.time()<10800
(root/'CONFIG.private.json').write_text(json.dumps(config,sort_keys=True))
os.chmod(root/'CONFIG.private.json',0o600)
unit='orch-r233-frozen-base-parent-20260918'
command=['sudo','-n','systemd-run','--unit='+unit,'--property=User=1352','--property=Group=1352',
 '--property=RuntimeMaxSec='+str(int(config['deadline_unix']-time.time())+20),
 '--property=TimeoutStopSec=5','--property=KillMode=control-group','--property=UMask=0077',
 '--property=DevicePolicy=closed','--property=NoNewPrivileges=yes','--property=CPUQuota=25%',
 '--property=StandardOutput=append:'+str(root/'parent.log'),'--property=StandardError=append:'+str(root/'parent.log'),
 '/usr/bin/python3','-B',str(root/'parent_bridge.py'),'--root',str(root)]
subprocess.run(command,check=True,capture_output=True,timeout=15)
deadline=time.time()+15
while not (root/'ACTIVE.json').exists() and time.time()<deadline:time.sleep(.1)
assert (root/'ACTIVE.json').exists(), 'bridge_not_active_no_claim'
receipt=json.loads((root/'ACTIVE.json').read_bytes())
receipt.update(unit=unit,source_sha256=SHA,policy='NEW_PARENTED_TREATMENT_NOT_PRECEDING_UNPARENTED_CONTROL',
 weights='FROZEN',generation_budgets_unchanged=True,parent_free_age_evaluation=True)
(root/'DISPATCHED.json').write_text(json.dumps(receipt,sort_keys=True))
print(json.dumps(receipt))
'''
    payload = ('ROOT=' + repr(ROOT) + '\nSOURCE=' + repr(base64.b64encode(raw).decode())
        + '\nSHA=' + repr(hashlib.sha256(raw).hexdigest()) + '\n' + payload)
    result = subprocess.run(['bash', 'gpu/ovx4_ssh.sh', 'python3 -B -'], input=payload,
        text=True, capture_output=True, timeout=40)
    if result.returncode:
        raise RuntimeError(result.stderr[-1800:])
    receipt = json.loads(result.stdout)
    (WORKER / 'PARENT_BRIDGE_ACTIVE.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
