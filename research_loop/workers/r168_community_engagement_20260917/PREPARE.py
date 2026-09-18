"""Neutral-path receiving/preflight only; fresh Main takeover GO still required."""

import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import tarfile
import time

from gpu import orch_r153_community_parents as community
from gpu import orch_r167_parent_takeover as files


TARGET = Path(__file__).resolve().parent
ROOT = TARGET.parents[2]
ORIGINAL = ROOT/'research_loop/workers/r168_community_prompt_final_20260917'
OLD = ORIGINAL/'attempt3'
CURRENT = ROOT/'research_loop/workers/r168_parent_execution_20260917'
REMOTE = '/localhome/local-rohing/orch_r168_community_engagement_20260917_attempt1/source'


def ref(path):
    return dict(path=str(Path(path).resolve()),sha256=files.sha(path))


def write(name, value):
    community.write(TARGET/name, value)


def main():
    assert files.sha(OLD/'INDEX.json') == '7369963ca25e3963101f40cb5eadaa9360bbde68e0321d049f7c7e990b4cc88d'
    original_index = json.loads(files.read_file(OLD/'INDEX.json'))
    draft = json.loads(files.read_file(OLD/'PARENT_GATE_DRAFT.json'))
    test_names = ['tests/test_orch_r168_parent_rollout.py','tests/test_orch_r167_parent_takeover.py',
        'tests/test_orch_r167_parent_watchdog.py','tests/test_orch_r168_manual_parent_turn.py',
        'tests/test_orch_r168_community_prompt_patch.py']
    names = test_names + ['gpu/orch_r168_parent_rollout.py','gpu/orch_r167_parent_takeover.py',
        'gpu/orch_r167_parent_watchdog.py','gpu/orch_r168_manual_parent_turn.py',
        'gpu/orch_r168_community_prompt_patch.py',str(Path(__file__))]
    pins = {name:files.sha(ROOT/name) for name in names}
    result = subprocess.run(['uv','run','--with','pytest','--with','pytest-subtests','python','-m','pytest','-q',*test_names],
        cwd=ROOT,capture_output=True,text=True,timeout=60,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES=''))
    (TARGET/'CPU_OUTPUT.txt').write_text(result.stdout+result.stderr)
    assert result.returncode == 0 and all(files.sha(ROOT/name)==expected for name,expected in pins.items())
    write('CPU_GATE.json',dict(status='PASS',execution_kind='CPU_ONLY',pins=pins,output=ref(TARGET/'CPU_OUTPUT.txt'),
        finished_unix=time.time(),new_guard_path_regressions=True))
    for side,source_pins in (('local_source',draft['source_pins']),('remote_source',draft['remote_source_pins']['ovx3'])):
        for name,expected in source_pins.items():
            source = OLD/side/name
            assert files.sha(source)==expected
            destination=TARGET/side/name
            destination.parent.mkdir(parents=True,exist_ok=True)
            with destination.open('xb') as stream:stream.write(files.read_file(source))
            destination.chmod(source.stat().st_mode&0o777)
    env_source=ROOT/'gpu/hosts.env'
    old_env=json.loads(files.read_file(ORIGINAL/'ROLLOUT/EXISTING_TRANSPORT_ENV_BINDING.json'))
    assert files.sha(env_source)==old_env['target_sha256']
    (TARGET/'local_source/gpu/hosts.env').symlink_to(env_source)
    write('TRANSPORT_ENV_BINDING.json',dict(path=str(TARGET/'local_source/gpu/hosts.env'),
        target=str(env_source),target_sha256=files.sha(env_source),credential_modified=False,credential_copied=False))
    archive=io.BytesIO()
    source_pins=draft['remote_source_pins']['ovx3']
    with tarfile.open(fileobj=archive,mode='w:gz') as package:
        for name in sorted(source_pins):package.add(TARGET/'remote_source'/name,arcname=name,recursive=False)
    raw=archive.getvalue()
    assert len(raw)<4194304
    with (TARGET/'SOURCE.tar.gz').open('xb') as stream:stream.write(raw)
    script='''import hashlib,io,json,os,sys,tarfile
from pathlib import Path
root=Path(REMOTE);pins=PINS;expected=SHA
raw=sys.stdin.buffer.read(4194305);assert len(raw)<=4194304 and hashlib.sha256(raw).hexdigest()==expected
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
 members=archive.getmembers();assert len(members)==len(pins) and {entry.name for entry in members}==set(pins)
 assert all(entry.isfile() and not Path(entry.name).is_absolute() and '..' not in Path(entry.name).parts and entry.size<=16777216 for entry in members)
 assert sum(entry.size for entry in members)<=33554432
 contents={entry.name:archive.extractfile(entry).read() for entry in members}
 assert all(hashlib.sha256(contents[name]).hexdigest()==expected for name,expected in pins.items())
 root.parent.mkdir(mode=0o700);root.mkdir(mode=0o700)
 for entry in members:
  path=root/entry.name;path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
  with path.open('xb') as stream:stream.write(contents[entry.name]);stream.flush();os.fsync(stream.fileno())
  path.chmod(entry.mode&0o777)
 assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==expected for name,expected in pins.items())
sys.path.insert(0,str(root))
from gpu import orch_r153_community_parents as module
from gpu import orch_r127_pilot_console as console
assert Path(module.__file__).resolve()==root/'gpu/orch_r153_community_parents.py'
assert Path(console.__file__).resolve()==root/'gpu/orch_r127_pilot_console.py'
assert callable(console.publish_parent)
print(json.dumps(dict(status='PASS',source_root=str(root),source_pins=pins,files=len(pins),
 module=str(Path(module.__file__).resolve()),console=str(Path(console.__file__).resolve()),
 python=sys.executable,provider_calls=0,native_changes=0)))
'''.replace('REMOTE',repr(REMOTE)).replace('PINS',repr(source_pins)).replace('SHA',repr(hashlib.sha256(raw).hexdigest()))
    received=subprocess.run(['bash',str(ROOT/'gpu/ovx3_ssh.sh'),'PYTHONDONTWRITEBYTECODE=1 python3 -c '+shlex.quote(script)],
        input=raw,capture_output=True,timeout=45)
    if received.returncode:
        write('RECEIVING_FAILURE.json',dict(exit_code=received.returncode,stderr=received.stderr.decode()[-4000:],
            no_signals=True,no_implicit_retry=True))
        raise ValueError('receiving_failed')
    receiving=json.loads(received.stdout)
    assert receiving['source_pins']==source_pins and receiving['source_root']==REMOTE
    write('RECEIVING.json',dict(receiving,observed_unix=time.time(),archive=ref(TARGET/'SOURCE.tar.gz')))
    candidates={}
    for branch in ('C1','C2','C3','C4','C5'):
        previous=(CURRENT/'ROLLOUT'/branch/'STARTED.json' if branch in ('C2','C3','C4')
                  else Path(original_index['candidates'][branch]['predecessor_start']['path']))
        started=json.loads(files.read_file(previous))
        observed=files.identity(started['successor']['pid'])
        assert observed['start_ticks']==started['successor']['start_ticks'] and observed['argv']==started['command']
        assert observed['state'] not in ('T','t','Z','X')
        old=json.loads(files.read_file(started['config']['path']))
        config=dict(old,source_root=REMOTE,cadence_responses=2)
        directory=TARGET/branch
        directory.mkdir(mode=0o700)
        community.write(directory/'CONFIG.json',config)
        candidates[branch]=dict(config=ref(directory/'CONFIG.json'),predecessor_start=ref(previous),
            observed_parent=observed,predecessor_output=started['command'][started['command'].index('--output')+1],
            output=str(directory/'parent'),hard_end_unix=config['hard_end_unix'],
            changed_fields=sorted(key for key in config if config[key]!=old[key]))
        draft['parents'][branch]=dict(root=config['root'],node=config['node'],source_root=REMOTE,
            config_sha256=files.sha(directory/'CONFIG.json'),output=str(directory/'parent'))
    write('PARENT_GATE_DRAFT.json',draft)
    write('PREFLIGHT_AUTHORITY.json',dict(authorized_by='Main',scope='actual_verify_gate_and_transport_preflight_only',
        instruction_received_utc='2026-09-17T08:43:00Z',basis='Main requested neutral local and remote paths, receiving verification and actual verify_gate subprocess; fresh takeover GO will follow',
        parent_takeover_authorized=False,no_signals=True))
    preflight=copy.deepcopy(draft)
    preflight['status']='MAIN_BOUND'
    preflight['operational_go']=ref(TARGET/'PREFLIGHT_AUTHORITY.json')
    preflight['preflight_only_no_takeover_GO']=True
    preflight['actual_receiving']=ref(TARGET/'RECEIVING.json')
    preflight['cpu_gate']=ref(TARGET/'CPU_GATE.json')
    write('PREFLIGHT_GATE.json',preflight)
    for branch in candidates:
        config_path=TARGET/branch/'CONFIG.json'
        script=('import json;from pathlib import Path;from gpu import orch_r153_community_parents as module;'
            'from gpu import orch_r133_programme_parent as parent;'
            'config,gate=module.verify_gate(Path('+repr(str(config_path))+'),Path('+repr(str(TARGET/'local_source'))+'),Path('
            +repr(candidates[branch]['output'])+'),Path('+repr(str(TARGET/'PREFLIGHT_GATE.json'))+'),'+repr(files.sha(TARGET/'PREFLIGHT_GATE.json'))+');'
            'print(json.dumps(parent.transport_preflight(Path('+repr(str(TARGET/'local_source'))+'),config)))')
        checked=subprocess.run(['/usr/bin/python3','-B','-c',script],cwd=TARGET/'local_source',
            env=dict(os.environ,PYTHONPATH=str(TARGET/'local_source'),PYTHONDONTWRITEBYTECODE='1'),
            capture_output=True,text=True,timeout=50)
        write(branch+'/EXECUTABLE_PREFLIGHT.json',dict(exit_code=checked.returncode,stdout=checked.stdout,
            stderr=checked.stderr,observed_unix=time.time(),not_native_liveness_or_adoption=True))
        assert checked.returncode==0,checked.stderr
    write('INDEX.json',dict(status='NEUTRAL_PATHS_RECEIVED_PREFLIGHT_PASS_AWAITING_FRESH_MAIN_TAKEOVER_GO',
        original_index=ref(OLD/'INDEX.json'),unchanged_patch_sha256=source_pins['gpu/orch_r153_community_parents.py'],
        cpu_gate=ref(TARGET/'CPU_GATE.json'),receiving=ref(TARGET/'RECEIVING.json'),gate_draft=ref(TARGET/'PARENT_GATE_DRAFT.json'),
        preflight_gate=ref(TARGET/'PREFLIGHT_GATE.json'),candidates=candidates,local_source=str(TARGET/'local_source'),
        remote_source=REMOTE,signals=0,provider_calls=0,publications=0,native_changes=0,created_unix=time.time(),
        C1_requires_manual229eb_render=True,C5_requires_Banach_sleep28_LOADED=True))
    print(json.dumps(ref(TARGET/'INDEX.json')))


if __name__=='__main__':
    main()
