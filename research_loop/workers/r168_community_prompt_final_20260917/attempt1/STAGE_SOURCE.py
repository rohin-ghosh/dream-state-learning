"""Create-only CPU/source staging. No signals, publication, or remote writes."""

import ast
import base64
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_r133_programme_parent as parent
from gpu import orch_r153_community_parents as community
from gpu import orch_r166_parent_policy as policy
from gpu import orch_r167_parent_takeover as files
from gpu import orch_r168_community_prompt_patch as repair


ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
PRIOR = ROOT/'research_loop/workers/r167_parent_policy_candidates_20260917/R154_ATTENTION_V2'
EXPECTED_GATE = 'd87b7cc9db9f4aa8d4199e170694d9b65a9cae0787d476767d76ad6cfc6623dd'


def ref(path):
    return dict(path=str(path.resolve()), sha256=files.sha(path))


def main():
    output = STAGE/'attempt1'
    output.mkdir(mode=0o700)
    gate_path = PRIOR/'ROLLOUT/PARENT_GATE.json'
    assert files.sha(gate_path) == EXPECTED_GATE
    original_gate = json.loads(files.read_file(gate_path))
    tests = ['tests/test_orch_r168_community_prompt_patch.py',
        'tests/test_orch_r153_community_parents.py', 'tests/test_orch_r166_parent_policy.py',
        'tests/test_orch_r167_parent_watchdog.py']
    test_sources = list(original_gate['source_pins']) + tests + [
        'gpu/orch_r168_community_prompt_patch.py', 'gpu/orch_r166_parent_policy.py',
        'gpu/orch_r167_parent_watchdog.py', 'gpu/orch_r167_parent_takeover.py']
    pins = {name: files.sha(ROOT/name) for name in test_sources}
    pins[str(Path(__file__).resolve())] = files.sha(Path(__file__))
    command = ['uv', 'run', '--with', 'pytest', '--with', 'pytest-subtests',
               'python', '-m', 'pytest', '-q', *tests]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
        timeout=60, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    (output/'CPU_OUTPUT.txt').write_text(completed.stdout+completed.stderr)
    assert completed.returncode == 0
    assert all(files.sha(ROOT/name) == value for name, value in pins.items())
    community.write(output/'CPU_GATE.json', dict(status='PASS', execution_kind='CPU_ONLY',
        command=command, exit_code=0, pins=pins, output=ref(output/'CPU_OUTPUT.txt'),
        finished_unix=time.time(), not_delivery_or_scientific_evidence=True))
    local_source = output/'local_source'
    remote_source = output/'remote_source'
    local_source.mkdir()
    remote_source.mkdir()
    original_bytes = {}
    for name, expected in original_gate['source_pins'].items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        raw = files.read_file(ROOT/name)
        assert hashlib.sha256(raw).hexdigest() == expected
        original_bytes[name] = raw
    assert sum(map(len, original_bytes.values())) < 32*1024*1024
    target = 'gpu/orch_r153_community_parents.py'
    patched, proof = repair.patch_source(original_bytes[target],
        expected_sha256=original_gate['source_pins'][target], policy_text=policy.PROMPT_POLICY)
    community.write(output/'PATCH_PROOF.json', proof)
    config_path = Path(original_gate['parents']['C1']['output']).parent/'STARTED.json'
    started = json.loads(files.read_file(config_path))
    current_config = json.loads(files.read_file(started['config']['path']))
    remote_pins = original_gate['remote_source_pins']['ovx3']
    script = '''import base64,hashlib,json
from pathlib import Path
root=Path(SOURCE_ROOT);pins=PINS;local=LOCAL
result={}
for name,expected in pins.items():
 path=root/name;assert path.is_file() and not path.is_symlink() and path.stat().st_size<=16777216
 raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==expected
 if expected!=local[name]:result[name]=base64.b64encode(raw).decode()
print(json.dumps(dict(original_remote_source_verified=True,different_files=result)))
'''.replace('SOURCE_ROOT', repr(current_config['source_root'])).replace('PINS', repr(remote_pins)).replace(
        'LOCAL', repr(original_gate['source_pins']))
    remote_observed = parent.remote(ROOT, current_config, script)
    assert remote_observed['original_remote_source_verified'] is True
    remote_bytes = dict(original_bytes)
    for name, encoded in remote_observed['different_files'].items():
        assert name in remote_pins and len(encoded) < 24*1024*1024
        remote_bytes[name] = base64.b64decode(encoded, validate=True)
    assert all(hashlib.sha256(remote_bytes[name]).hexdigest() == expected
               for name, expected in remote_pins.items())
    community.write(output/'ORIGINAL_REMOTE_VERIFIED.json', dict(node='ovx3',
        source_root=current_config['source_root'], pins=remote_pins, observed_unix=time.time(),
        read_only=True))
    for directory, contents in ((local_source, original_bytes), (remote_source, remote_bytes)):
        for name, raw in contents.items():
            destination = directory/name
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as stream:
                stream.write(patched if name == target else raw)
            destination.chmod((ROOT/name).stat().st_mode & 0o777)
        for name in ('gpu/__init__.py', 'organism_v6/__init__.py'):
            assert files.read_file(ROOT/name) == b''
            (directory/name).write_bytes(b'')
    local_pins = {name: files.sha(local_source/name) for name in original_bytes}
    new_remote_pins = {name: files.sha(remote_source/name) for name in remote_bytes}
    assert [name for name in local_pins if local_pins[name] != original_gate['source_pins'][name]] == [target]
    assert [name for name in new_remote_pins if new_remote_pins[name] != remote_pins[name]] == [target]
    for name in ('gpu/__init__.py', 'organism_v6/__init__.py'):
        local_pins[name] = files.sha(local_source/name)
        new_remote_pins[name] = files.sha(remote_source/name)
    draft = copy.deepcopy(original_gate)
    draft['status'] = 'AWAITING_MAIN_BOUND_GO'
    draft['source_pins'] = local_pins
    draft['remote_source_pins'] = dict(ovx3=new_remote_pins)
    draft.pop('operational_go', None)
    draft.pop('lifecycle_cpu_gate', None)
    candidates = {}
    new_remote_root = '/localhome/local-rohing/orch_r168_parent_prompt_final_20260917_attempt1/source'
    for branch in ('C1', 'C3', 'C2', 'C4', 'C5'):
        prior = PRIOR/'ROLLOUT'/branch
        start = json.loads(files.read_file(prior/'STARTED.json'))
        observed = files.identity(start['successor']['pid'])
        assert observed['start_ticks'] == start['successor']['start_ticks']
        assert observed['argv'] == start['command'] and observed['state'] not in ('T', 't', 'Z', 'X')
        old = json.loads(files.read_file(start['config']['path']))
        assert files.sha(start['config']['path']) == start['config']['sha256']
        candidate = dict(old, source_root=new_remote_root)
        community.validate(candidate)
        directory = output/branch
        directory.mkdir()
        community.write(directory/'CONFIG.json', candidate)
        new_output = directory/'parent'
        draft['parents'][branch] = dict(root=candidate['root'], node=candidate['node'],
            source_root=new_remote_root, config_sha256=files.sha(directory/'CONFIG.json'),
            output=str(new_output))
        candidates[branch] = dict(config=ref(directory/'CONFIG.json'), predecessor_start=ref(prior/'STARTED.json'),
            observed_parent=observed, predecessor_output=str(prior/'parent'), output=str(new_output),
            config_changed_fields=['source_root'], original_wall=candidate['hard_end_unix'])
    community.remote_source_pins(draft, 'ovx3')
    community.write(output/'PARENT_GATE_DRAFT.json', draft)
    attempt = PRIOR/'ROLLOUT/C1/parent/parent_000000000096'
    state = json.loads(files.read_file(attempt/'SOURCE.json'))
    memory = json.loads(files.read_file(attempt/'OBJECT_STATE.json'))
    recorded = json.loads(files.read_file(attempt/'PROMPT.json'))
    original_prompt, original_payload = community.prompt(current_config, state, memory)
    assert original_prompt == recorded['instruction'] and original_payload == recorded['payload']
    function = next(node for node in ast.parse(patched).body
                    if isinstance(node, ast.FunctionDef) and node.name == 'prompt')
    namespace = dict(vars(community))
    exec(compile(ast.Module(body=[function], type_ignores=[]), '<CPU-rebuilt-real-prompt>', 'exec'), namespace)
    instruction, payload = namespace['prompt'](current_config, state, memory)
    assert instruction == recorded['instruction'] + policy.PROMPT_POLICY + repair.FINAL_RULES
    assert payload == recorded['payload']
    community.write(output/'C1_REBUILT_PROMPT_NOT_DISPATCHED.json', dict(instruction=instruction, payload=payload,
        source=ref(attempt/'SOURCE.json'), original_prompt=ref(attempt/'PROMPT.json'),
        not_dispatched=True, not_publication=True))
    observer_path = PRIOR/'OBSERVE.py'
    specification = importlib.util.spec_from_file_location('r154_read_only_observer', observer_path)
    observer = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(observer)
    community.write(output/'CURRENT_PHASES.json', dict(observed_unix=time.time(), parents=observer.phases()))
    community.write(output/'INDEX.json', dict(status='PREPARED_NOT_ADMITTED_NOT_LIVE',
        original_gate=ref(gate_path), cpu_gate=ref(output/'CPU_GATE.json'), patch=ref(output/'PATCH_PROOF.json'),
        helper=ref(ROOT/'gpu/orch_r168_community_prompt_patch.py'), tests=ref(ROOT/tests[0]),
        policy=ref(ROOT/'gpu/orch_r166_parent_policy.py'), local_source=str(local_source),
        remote_source_package=str(remote_source), proposed_remote_source=new_remote_root,
        gate_draft=ref(output/'PARENT_GATE_DRAFT.json'), candidates=candidates,
        remote_staged=False, provider_calls=0, publications=0, signals=0,
        cadence_responses=3, delivered_floor_not_established=True, created_unix=time.time()))
    print(json.dumps(ref(output/'INDEX.json')))


if __name__ == '__main__':
    main()
