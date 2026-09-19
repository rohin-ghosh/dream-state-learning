"""Read-only exact-incarnation and existing scorer-epoch checks."""

import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PRIOR = REPO / 'research_loop/workers/rohin233_ovx4_recovery_20260918'
SHARED = '/localhome/local-rohing/orch_r226_shared_caption_20260918/attempt2'
SOURCE = '/localhome/local-rohing/orch_r233_caption_transport32_20260918/source'
SCORER = '/localhome/local-rohing/orch_r233_judge15625_20260918/judge15625-shared2-v1'
HELPER_SHA = '44bc9e009fce0f46b731da9907342f4bf22788329cc5d59291538538d8830635'


def remote(wrapper, code, value):
    result = subprocess.run(['bash', str(REPO / 'gpu' / wrapper),
        'python3 -B -c ' + shlex.quote(code)], input=json.dumps(value), text=True,
        capture_output=True, check=True, timeout=90)
    return json.loads(result.stdout)


def inspect():
    bridge = (HERE / 'node_bridge.py').read_text().split("if __name__ == '__main__':")[0]
    baseline = json.loads((HERE / 'BINDINGS.json').read_bytes())
    native = remote('ovx2_ssh.sh', bridge + '''
value=json.load(sys.stdin)
retirement,adaptive,helper,bindings=load_helpers()
exact=exact_bindings(retirement,helper,bindings)
assert exact==value['bindings'],'native_incarnation_changed'
relay=retirement.identity(1970178)
assert relay['state'] not in ('Z','X') and 'node3_feedback.py' in ' '.join(relay['args'])
source=Path(value['source'])/'research_loop/workers/rohin233_ovx4_recovery_20260918/transport_entry.py'
assert retirement.sha(source)==value['helper_sha']
print(json.dumps(dict(unix=time.time(),bindings=exact,publishers=publishers(retirement),
    feedback_relay={key:relay[key] for key in ('pid','start_ticks','command_sha256')},
    aliases={str(slot):str(Path('/tmp/r226-caption-'+str(slot)+'.sock').readlink()) for slot in (0,3,5,6,7)})))
''', dict(bindings=baseline['bindings'], source=SOURCE, helper_sha=HELPER_SHA))
    scorer = remote('ovx4_ssh.sh', '''
from pathlib import Path
import hashlib,json,sys,time
value=json.load(sys.stdin)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
root=Path(value['root'])
loaded=json.loads((root/'LOADED.json').read_bytes())
assert sha(root/'LOADED.json')=='7326a438c9ab9613a2a0e8d6e8f94f043b3cbd3499d293377c802cbd3d383848'
assert {row['player']:row['epoch_sha256'] for row in loaded['sessions']}==value['epochs']
processes=[]
for pid,start in [(499900,'10094999'),(502015,'10101591'),(448173,'9898014')]:
 proc=Path('/proc',str(pid));fields=(proc/'stat').read_text().rsplit(')',1)[1].split()
 assert fields[19]==start and fields[0] not in ('Z','X'),'existing_scorer_or_bridge_changed'
 processes.append(dict(pid=pid,start_ticks=start,command_sha256=sha(proc/'cmdline')))
assert sha(Path(value['source'])/'research_loop/workers/rohin233_ovx4_recovery_20260918/transport_entry.py')==value['helper_sha']
renew=Path('/localhome/local-rohing/orch_r233_lease_renewal_20260918/attempt2/shared2')
assert json.loads((renew/'BRIDGE_CONFIG.private.json').read_bytes())['endpoint']==value['shared']+'/native.sock'
assert json.loads((renew/'bridge/TARGET.json').read_bytes())['socket']==str(renew/'sockets/native.sock')
assert json.loads((root/'BRIDGE_CONFIG.private.json').read_bytes())['endpoint']==str(renew/'sockets/native.sock')
assert json.loads((root/'bridge/TARGET.json').read_bytes())['socket']==str(root/'sockets/native.sock')
ledgers={}
for life,epoch in value['epochs'].items():
 directory=root/'epochs'/life
 files=list(directory.glob('*.json'))
 ledgers[life]=dict(epoch_sha256=epoch,binding_sha256=sha(directory/'BINDING.json'),
   files=len(files),latest_file_mtime=max(path.stat().st_mtime for path in files))
print(json.dumps(dict(unix=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
 processes=processes,loaded_sha256=sha(root/'LOADED.json'),ledgers=ledgers)))
''', dict(root=SCORER, shared=SHARED, source=SOURCE, helper_sha=HELPER_SHA,
        epochs={row['player']:row['epoch_sha256'] for row in json.loads(
            (PRIOR / 'JUDGE_SHARED2_ADOPTED.json').read_bytes())['actual_loaded']['sessions']}))
    return dict(unix=time.time(),native=native,scorer=scorer,
        no_native_or_scorer_restart=True, no_historical_replay=True)
