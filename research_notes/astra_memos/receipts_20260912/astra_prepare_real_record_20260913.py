import hashlib
import json
from pathlib import Path
import subprocess
import sys


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path, checksum):
    assert digest(path) == checksum
    return dict(path=str(path), sha256=checksum)


source = Path('/tmp/astra_level1_real_record_source_20260913_attempt1')
driver = Path('/tmp/astra_level1_real_record_run_20260913.py')
runtime_sha = '3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e'
assert digest(driver) == runtime_sha
directory = Path('/tmp/astra_real_record_spec_20260913_attempt1')
directory.mkdir()
upstream = []
for seed in range(3):
    root = Path(f'/localhome/local-rohing/astra_diagnostics/level1_perception_seed{seed}_20260913_attempt1')
    completed = root / 'capture_complete.json'
    assert not (root / 'controller_failure.json').exists()
    fit = json.loads((root / 'run/fit/fit.json').read_text())
    collection = root.with_name(root.name + '_collected') / 'collection.json'
    upstream.append(dict(seed=seed, root=str(root), plan_sha256=digest(root / 'plan.json'),
                         completion_sha256=digest(completed),
                         collection=dict(path=str(collection), sha256=digest(collection)),
                         adapter_files=fit['adapter_files']))
spec = dict(runner_sha256=runtime_sha, source=str(source),
            source_files={str(path.relative_to(source)): digest(path) for path in source.rglob('*') if path.is_file()},
            model='/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28',
            core=pin('/tmp/astra_level1_real_record_core_20260913.py', '1c7723fcbb07ad75464d9ceae9fbd1cb8953f6dc0cb7a2e22d3046421167a15c'),
            level1_runtime=pin('/tmp/astra_level1_skill_run_20260913.py', '6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e'),
            public=pin('/tmp/astra_birth_skill_probe_run_20260913.py', '59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c'),
            protocol=pin('/tmp/ASTRA_REAL_RECORD_FORMATION_PROTOCOL_2026-09-13.md', '8ce5a11df34c6ed7b35b30cfd14079de3744bc1d3f70eea20fb18fc686710625'),
            binding=pin('/tmp/astra_qwen_public_binding_receipt_20260913_attempt1.json', 'e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019'),
            gpu_index=1, gpu_uuid='GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4', lease_end=1789980180,
            upstream=upstream)
assert len(spec['source_files']) == 6
spec_path = directory / 'spec.json'
with spec_path.open('x') as stream:
    stream.write(json.dumps(spec, sort_keys=True) + '\n')
command = [sys.executable, '-B', str(driver), 'prepare', '--root',
           '/localhome/local-rohing/astra_diagnostics/level1_real_record_20260913_attempt1',
           '--spec-path', str(spec_path), '--spec-sha256', digest(spec_path), '--allow-native']
with (directory / 'prepare.log').open('x') as output:
    result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, timeout=180)
assert result.returncode == 0, 'CPU native preparation failed; preserve root and log'
print((directory / 'prepare.log').read_text())
