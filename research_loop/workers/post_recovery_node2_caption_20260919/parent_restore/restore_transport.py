"""Recover only node2's original CPU caption route, preserving the scorer epoch."""

import hashlib
import importlib.util
import inspect as source_inspect
import json
from pathlib import Path
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
BORROWED = REPO / 'research_loop/workers/post_reboot_node3_parents_20260919'
PRIOR = REPO / 'research_loop/workers/rohin233_ovx4_recovery_20260918'
sys.path.insert(0, str(BORROWED))
import transport_preflight

spec = importlib.util.spec_from_file_location('existing_route_recovery', BORROWED / 'restore_transport.py')
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)

DEADLINE = 1789927160
REGISTRY_SHA = '571086cf18af0cade3365aca9462a099d7961104fbc251d5e2c6d6826f3d806d'
SHARED = '/localhome/local-rohing/orch_r230_extra_caption_scorer_20260918'
SCORER = '/localhome/local-rohing/orch_r233_judge15625_20260918/judge15625-shared3-v1'
SOURCE = '/localhome/local-rohing/orch_r233_caption_transport32_20260918/source'
TRANSPORT_ROOT = HERE / 'transport'
SESSION = 'r229_extra_unparented_node2_gpu2'


def registry_bytes():
    registry = json.loads((REPO / 'research_loop/workers/rohin221_continuous_caption_20260918/R230_EXTRA_BINDING_LIVE.json').read_bytes())['registry']
    prior = next(row for row in json.loads((PRIOR / 'LEASE_TRANSPORTS_RENEWED.json').read_bytes()) if row['group'] == 'node2')
    for row in registry['rows']:
        row['minimum_origin_record_index'] = prior['proxy']['future_frontiers'][row['session_id']]
    raw = json.dumps(registry).encode()
    if hashlib.sha256(raw).hexdigest() != REGISTRY_SHA:
        raise ValueError('exact_original_node2_registry_required')
    return raw


def forwarding_commands(runtime, rows, suffix):
    if len(rows) != 1 or rows[0]['physical'] != 2 or rows[0]['host_alias'] != 'ovx' or rows[0]['session_id'] != SESSION:
        raise ValueError('only_existing_node2_caption_route')
    options = ['-N', '-o', 'ExitOnForwardFailure=yes', '-o', 'StreamLocalBindMask=0177', '-o', 'ServerAliveCountMax=3']
    target = '/tmp/n2cap-' + suffix + '-2.sock'
    upstream = ['bash', 'gpu/ovx4_ssh.sh', *options, '-L', str(runtime / 'shared.sock') + ':' + SHARED + '/native.sock']
    downstream = ['bash', 'gpu/ovx_ssh.sh', *options, '-R', target + ':' + str(runtime / 'proxy/2.sock')]
    return upstream, downstream, [dict(slot='2', alias='/tmp/r226-caption-2.sock', target=target)]


def preflight():
    endpoint = (HERE / 'endpoint.py').read_text().split("if __name__ == '__main__':")[0]
    native = transport_preflight.remote('ovx_ssh.sh', endpoint + '''
import subprocess
focus,plan,owner=identity()
alias=Path('/tmp/r226-caption-2.sock')
require(alias.is_symlink(),'existing_route_alias_required')
listeners=subprocess.check_output(['ss','-xlnH'],text=True)
require(str(alias.readlink()) not in listeners,'existing_listening_route_not_replaced')
helper=Path('/localhome/local-rohing/orch_r233_caption_transport32_20260918/source/research_loop/workers/rohin233_ovx4_recovery_20260918/transport_entry.py')
require(sha(helper)=='44bc9e009fce0f46b731da9907342f4bf22788329cc5d59291538538d8830635','original_export_helper')
print(json.dumps(dict(identity=owner,aliases={'2':str(alias.readlink())},no_native_changes=True)))
''', {})
    expected = json.loads((PRIOR / 'JUDGE_SHARED3_ADOPTED.json').read_bytes())['actual_loaded']
    scorer = transport_preflight.remote('ovx4_ssh.sh', '''
from pathlib import Path
import hashlib,json,sys,time
value=json.load(sys.stdin)
root=Path(value['root']);renew=Path('/localhome/local-rohing/orch_r233_lease_renewal_20260918/attempt2/shared3')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
loaded=json.loads((root/'LOADED.json').read_bytes())
assert loaded==value['expected_loaded'],'same_adopted_scorer_epoch'
assert sha(root/'LOADED.json')=='6c870c896a67f96e86cf1a50dc59be2bc2778795e01fcd94f5139851aaa151d4'
proc=Path('/proc/499905');fields=(proc/'stat').read_text().rsplit(')',1)[1].split()
assert fields[19]=='10095034' and fields[0] not in ('Z','X') and str(root).encode() in (proc/'cmdline').read_bytes()
assert json.loads((renew/'BRIDGE_CONFIG.private.json').read_bytes())['endpoint']==value['shared']+'/native.sock'
assert json.loads((renew/'bridge/TARGET.json').read_bytes())['socket']==str(renew/'sockets/native.sock')
assert json.loads((root/'BRIDGE_CONFIG.private.json').read_bytes())['endpoint']==str(renew/'sockets/native.sock')
assert json.loads((root/'bridge/TARGET.json').read_bytes())['socket']==str(root/'sockets/native.sock')
assert sha(Path(value['source'])/'research_loop/workers/rohin233_ovx4_recovery_20260918/transport_entry.py')=='44bc9e009fce0f46b731da9907342f4bf22788329cc5d59291538538d8830635'
bridges=[]
for config in [renew/'BRIDGE_CONFIG.private.json',root/'BRIDGE_CONFIG.private.json']:
 matches=[]
 for process in Path('/proc').iterdir():
  if not process.name.isdecimal(): continue
  try:
   command=(process/'cmdline').read_bytes().split(b'\\0')
   state=(process/'stat').read_text().rsplit(')',1)[1].split()
  except (OSError,IndexError): continue
  if str(config).encode() in command and state[0] not in ('Z','X'):
   matches.append(dict(pid=int(process.name),start_ticks=state[19],command_sha256=sha(process/'cmdline')))
 assert len(matches)==1,'exact_existing_bridge_required'
 bridges+=matches
directory=root/'epochs'/value['session']
print(json.dumps(dict(unix=time.time(),scorer_pid=499905,scorer_start_ticks=fields[19],bridges=bridges,
 loaded_sha256=sha(root/'LOADED.json'),epoch_sha256=loaded['sessions'][0]['epoch_sha256'],
 binding_sha256=sha(directory/'BINDING.json'),ledger_files=len(list(directory.glob('*.json'))))))
''', dict(root=SCORER, expected_loaded=expected, shared=SHARED, source=SOURCE, session=SESSION))
    return dict(unix=time.time(), native=native, scorer=scorer, no_native_or_scorer_restart=True, no_historical_replay=True)


def scoped_main(source):
    changes = {
        "Path('/tmp/n3cap-' + suffix)": "Path('/tmp/n2cap-' + suffix)",
        "remote('ovx2_ssh.sh',": "remote('ovx_ssh.sh',",
        "/localhome/local-rohing/orch_r205_node3_20260918/R233_NODE3_TRANSPORT_RECOVERY.lock":
            "/localhome/local-rohing/orch_r229_unparented_caption_20260918/r213_r226_caption_unparented_fork/TRANSPORT_RECOVERY.lock",
    }
    for original, replacement in changes.items():
        if source.count(original) != 1:
            raise ValueError('existing_transport_implementation_changed')
        source = source.replace(original, replacement)
    return source


def main():
    manifest = json.loads((HERE / 'TRANSPORT_MANIFEST.json').read_text())
    for relative, expected in manifest['sources'].items():
        if hashlib.sha256((REPO / relative).read_bytes()).hexdigest() != expected:
            raise ValueError('reviewed_transport_source_changed')
    TRANSPORT_ROOT.mkdir(mode=0o700, exist_ok=True)
    (TRANSPORT_ROOT / 'locks').mkdir(mode=0o700, exist_ok=True)
    recovery.HERE, recovery.DEADLINE, recovery.REGISTRY_SHA = TRANSPORT_ROOT, DEADLINE, REGISTRY_SHA
    recovery.SHARED, recovery.SOURCE = SHARED, SOURCE
    recovery.registry_bytes, recovery.forwarding_commands, recovery.inspect = registry_bytes, forwarding_commands, preflight
    namespace = dict(recovery.main.__globals__)
    exec(compile(scoped_main(source_inspect.getsource(recovery.main)), __file__ + ':existing_CPU_route_only', 'exec'), namespace)
    namespace['main']()


if __name__ == '__main__':
    main()
