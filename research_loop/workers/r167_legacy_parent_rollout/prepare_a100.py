"""Stage only live A100 candidates with Main's pinned startup adapter."""

import json
import os
from pathlib import Path
import subprocess
import time

import a100_rollout as rollout
import legacy_takeover as legacy


def prepare(branches=None, census_name='A100_NATIVE_CURRENT.json', index_name='A100_PREPARED_INDEX.json'):
    legacy.require(legacy.ref(rollout.ADAPTER_PATH)['sha256'] == rollout.ADAPTER_SHA, 'exact_Main_adapter')
    legacy.require(legacy.ref(legacy.INDEX)['sha256'] == legacy.INDEX_SHA, 'exact_policy_index')
    census_path = legacy.HERE / census_name
    census = json.loads(legacy.read(census_path))
    summaries = []
    candidates = json.loads(legacy.read(legacy.INDEX))['candidates']
    for branch in branches or rollout.ALLOWED:
        matches = [item for item in candidates if item['candidate'].startswith(branch + '_')]
        legacy.require(len(matches) == 1, 'one_exact_candidate')
        item = matches[0]
        receipt = json.loads(legacy.bound(item['receipt']))
        directory = legacy.HERE / receipt['candidate']
        directory.mkdir(mode=0o700)
        try:
            old = json.loads(legacy.bound(receipt['original_config']))
            candidate = json.loads(legacy.bound(receipt['candidate_config']))
            legacy.require({key for key in set(old) | set(candidate) if old.get(key) != candidate.get(key)}
                == {'principles_path', 'principles_sha256'}, 'principles_only')
            observed = legacy.identity(receipt['prior_parent_pid'])
            legacy.require(observed['start_ticks'] == receipt['parent_identity_observation']['start_ticks'],
                'original_parent_start_ticks')
            natives = [native for native in census['natives'] if any(plan.get('root') == old['root']
                for plan in native['plans'])]
            legacy.require(len(natives) == 1, 'one_current_native')
            previous = rollout.ledger(receipt['parent_output'], old, receipt['original_source']['sha256'])
            resume = dict(schema=rollout.adapter.SCHEMA, root=old['root'], branch=old['branch'],
                programme=old['programme'], old_output=receipt['parent_output'],
                started_sha256=previous['started_sha256'], reserved_response_count=previous['reserved_response_count'])
            generated = rollout.adapter.patch_source(legacy.bound(receipt['original_source']).decode(), resume)
            with (directory / 'PARENT.py').open('x') as stream:
                stream.write(generated)
            config = rollout.adapter.resume_config(candidate, resume)
            legacy.write(directory / 'CONFIG.json', config)
            binding = dict(schema='R167_A100_CUSTODY_V1', candidate=receipt['candidate'], branch=branch,
                root=old['root'], node='a100', parent=observed, original_source=receipt['original_source'],
                original_config=receipt['original_config'], candidate_config=receipt['candidate_config'],
                old_output=receipt['parent_output'], native=natives[0], resume_binding=resume,
                python=str((Path('/proc') / str(observed['pid']) / 'exe').resolve()), observed_unix=time.time())
            rollout.verify(binding, observed)
            receiving = rollout.receiving_cpu(binding, directory)
            script = ('import hashlib,json,sys; from pathlib import Path; '
                'from gpu import orch_r133_programme_parent; '
                'print(json.dumps([{ "path":str(Path(module.__file__).resolve()),'
                '"sha256":hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()}'
                ' for name,module in sorted(sys.modules.items()) '
                'if (name.startswith("gpu.") or name.startswith("organism_v6.")) '
                'and getattr(module,"__file__",None)]))')
            result = subprocess.run([binding['python'], '-B', '-c', script], cwd=observed['cwd'],
                env=dict(os.environ, PYTHONPATH=observed['cwd'], PYTHONDONTWRITEBYTECODE='1'),
                capture_output=True, timeout=15)
            legacy.require(result.returncode == 0, 'original_imported_closure')
            imports = json.loads(result.stdout)
            pins = [item['receipt'], receipt['original_config'], receipt['candidate_config'],
                receipt['original_source'], receipt['principles'], legacy.ref(legacy.INDEX),
                legacy.ref(rollout.ADAPTER_PATH), legacy.ref(directory / 'PARENT.py'),
                legacy.ref(directory / 'CONFIG.json'), legacy.ref(legacy.HERE / 'legacy_takeover.py'),
                legacy.ref(legacy.HERE / 'remote_metadata.py'), legacy.ref(old['programme_path']),
                legacy.ref(legacy.REPOSITORY / 'gpu/a100_ssh.sh')] + imports
            if branch in rollout.CONTROLS:
                pins.append(legacy.ref(legacy.HERE / 'remote_control_metadata.py'))
            for pin in pins:
                legacy.bound(pin)
            binding['pins'] = pins
            legacy.write(directory / 'BINDING.json', binding)
            legacy.write(directory / 'PREPARATION.json', dict(status='PASS_CPU_PROVENANCE_NO_SIGNALS',
                receiving_cpu=receiving, native_census=legacy.ref(census_path), previous=previous,
                generated_source=legacy.ref(directory / 'PARENT.py'), original_source=receipt['original_source'],
                source_adapter=legacy.ref(rollout.ADAPTER_PATH), observed_unix=time.time(),
                original_state_untouched=True))
            summaries.append(dict(candidate=receipt['candidate'], binding=legacy.ref(directory / 'BINDING.json'),
                native_pid=natives[0]['pid'], reserved=previous['reserved_response_count'], status='CPU_PROVENANCE_READY'))
        except Exception as error:
            legacy.write(directory / 'PREPARATION_REFUSAL.json', dict(reason=str(error),
                error_type=type(error).__name__, observed_unix=time.time(), no_signals=True))
            summaries.append(dict(candidate=receipt['candidate'], status='DEFER_UNTOUCHED', reason=str(error)))
    legacy.write(legacy.HERE / index_name, dict(candidates=summaries, observed_unix=time.time()))
    print(json.dumps(summaries, indent=2))


if __name__ == '__main__':
    prepare()
