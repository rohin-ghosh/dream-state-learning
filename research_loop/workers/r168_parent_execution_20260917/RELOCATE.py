"""Same-byte neutral-path execution staging; original no-evaluation guard unchanged."""

import json
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_r153_community_parents as community
from gpu import orch_r167_parent_takeover as files


TARGET = Path(__file__).resolve().parent
ROOT = TARGET.parents[2]
ORIGINAL = ROOT/'research_loop/workers/r168_community_prompt_final_20260917'
OLD = ORIGINAL/'attempt3'


def ref(path):
    return dict(path=str(path.resolve()), sha256=files.sha(path))


def main():
    index = json.loads(files.read_file(OLD/'INDEX.json'))
    assert files.sha(OLD/'INDEX.json') == '7369963ca25e3963101f40cb5eadaa9360bbde68e0321d049f7c7e990b4cc88d'
    gate = json.loads(files.read_file(ORIGINAL/'ROLLOUT/PARENT_GATE.json'))
    copied = {}
    for relative in ('INDEX.json','CPU_GATE.json',*[branch+'/CONFIG.json' for branch in ('C1','C2','C3','C4','C5')]):
        destination = TARGET/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        raw = files.read_file(OLD/relative)
        with destination.open('xb') as stream:stream.write(raw)
        assert files.sha(destination) == files.sha(OLD/relative)
        copied[relative] = ref(destination)
    for name, expected in gate['source_pins'].items():
        source = OLD/'local_source'/name
        assert files.sha(source) == expected
        destination = TARGET/'local_source'/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('xb') as stream:stream.write(files.read_file(source))
        destination.chmod(source.stat().st_mode & 0o777)
    for name, expected in gate['remote_source_pins']['ovx3'].items():
        source = OLD/'remote_source'/name
        assert files.sha(source) == expected
        destination = TARGET/'remote_source'/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('xb') as stream:stream.write(files.read_file(source))
        destination.chmod(source.stat().st_mode & 0o777)
    env_source = ROOT/'gpu/hosts.env'
    (TARGET/'local_source/gpu/hosts.env').symlink_to(env_source)
    assert files.sha(env_source) == json.loads(files.read_file(ORIGINAL/'ROLLOUT/EXISTING_TRANSPORT_ENV_BINDING.json'))['target_sha256']
    for name in ('MAIN_GO.json','RECEIVING.json'):
        with (TARGET/'ROLLOUT'/name).open('xb') as stream:stream.write(files.read_file(ORIGINAL/'ROLLOUT'/name))
    tests = ['tests/test_orch_r168_parent_rollout.py','tests/test_orch_r167_parent_takeover.py',
        'tests/test_orch_r167_parent_watchdog.py','tests/test_orch_r168_manual_parent_turn.py',
        'tests/test_orch_r168_community_prompt_patch.py']
    names = tests + ['gpu/orch_r168_parent_rollout.py','gpu/orch_r167_parent_takeover.py',
        'gpu/orch_r167_parent_watchdog.py','gpu/orch_r168_manual_parent_turn.py',
        'gpu/orch_r168_community_prompt_patch.py',str(TARGET/'ROLLOUT/EXECUTE.py'),str(Path(__file__))]
    pins = {name:files.sha(ROOT/name) for name in names}
    command = ['uv','run','--with','pytest','--with','pytest-subtests','python','-m','pytest','-q',*tests]
    result = subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=60,
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES=''))
    (TARGET/'ROLLOUT/CPU_OUTPUT.txt').write_text(result.stdout+result.stderr)
    assert result.returncode == 0 and all(files.sha(ROOT/name) == expected for name,expected in pins.items())
    community.write(TARGET/'ROLLOUT/CPU_GATE.json',dict(status='PASS',execution_kind='CPU_ONLY',command=command,
        pins=pins,output=ref(TARGET/'ROLLOUT/CPU_OUTPUT.txt'),finished_unix=time.time()))
    community.write(TARGET/'RELOCATION.json',dict(kind='same_bytes_path_relocation_no_guard_change',
        original_index=ref(OLD/'INDEX.json'),copied=copied,source_pins=gate['source_pins'],
        runtime_host_configuration=dict(path=str(TARGET/'local_source/gpu/hosts.env'),target=str(env_source),
            target_sha256=files.sha(env_source),credential_modified=False),
        unchanged_remote_source=index['proposed_remote_source'],unchanged_parent_outputs=True,
        original_gate=ref(ORIGINAL/'ROLLOUT/PARENT_GATE.json'),old_deferrals=[ref(ORIGINAL/'ROLLOUT'/branch/'DEFERRED_OR_FAILED.json')
            for branch in ('C2','C3','C4')],observed_unix=time.time()))
    gate['lifecycle_cpu_gate'] = ref(TARGET/'ROLLOUT/CPU_GATE.json')
    gate['samebytes_path_relocation'] = ref(TARGET/'RELOCATION.json')
    community.write(TARGET/'ROLLOUT/PARENT_GATE.json',gate)
    for branch in ('C2','C3','C4'):
        output = index['candidates'][branch]['output']
        script = ('from pathlib import Path;import json;from gpu import orch_r153_community_parents as module;'
            'from gpu import orch_r133_programme_parent as parent;'
            'config,gate=module.verify_gate(Path('+repr(str(TARGET/branch/'CONFIG.json'))+'),Path('
            +repr(str(TARGET/'local_source'))+'),Path('+repr(output)+'),Path('
            +repr(str(TARGET/'ROLLOUT/PARENT_GATE.json'))+'),'+repr(files.sha(TARGET/'ROLLOUT/PARENT_GATE.json'))+');'
            'print(json.dumps(parent.transport_preflight(Path('+repr(str(TARGET/'local_source'))+'),config)))')
        checked = subprocess.run(['/usr/bin/python3','-B','-c',script],cwd=TARGET/'local_source',capture_output=True,
            text=True,timeout=50,env=dict(os.environ,PYTHONPATH=str(TARGET/'local_source'),PYTHONDONTWRITEBYTECODE='1'))
        community.write(TARGET/'ROLLOUT'/('PREFLIGHT_'+branch+'.json'),dict(exit_code=checked.returncode,
            stdout=checked.stdout,stderr=checked.stderr,observed_unix=time.time()))
        assert checked.returncode == 0, checked.stderr
    with (ROOT/'research_loop/COORDINATION.md').open('a') as stream:
        stream.write('\n[Builder] 2026-09-17 '+time.strftime('%H:%M:%S',time.gmtime())+' UTC — R168 all original parents remain alive; '
            'first preflight rejected neutral TRAIN staging path containing token final before any signals. Guard unchanged. '
            'Same-byte local source/config relocation '+str(TARGET/'RELOCATION.json')+' SHA'+files.sha(TARGET/'RELOCATION.json')+
            '; actual remote67-file closure unchanged; fresh local executable+actual transport preflight PASS allC2/C3/C4. '
            '84 focusedCPU PASS '+str(TARGET/'ROLLOUT/CPU_GATE.json')+' SHA'+files.sha(TARGET/'ROLLOUT/CPU_GATE.json')+
            '. Main exact source/config pins preserved; no runtime science/credential/wall changes.\n')


if __name__=='__main__':
    main()
