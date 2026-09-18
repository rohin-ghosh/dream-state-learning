"""Read-only parent/source custody preparation; writes new local evidence only."""

import json
import os
from pathlib import Path
import subprocess
import time

import legacy_takeover as legacy


def prepare(branches=None, census_paths=None, gate_name='CPU_GATE.json', tests_passed=34,
            log_name='CPU_attempt1.log', index_name='PREPARED_INDEX.json'):
    legacy.require(legacy.ref(legacy.INDEX)['sha256'] == legacy.INDEX_SHA, 'approved_index')
    policy = legacy.REPOSITORY / 'gpu/orch_r166_parent_policy.py'
    legacy.require(legacy.ref(policy)['sha256'] == legacy.POLICY_SHA, 'approved_policy')
    policy_cpu = legacy.INDEX.with_name('CPU_GATE.json')
    legacy.require(legacy.ref(policy_cpu)['sha256'] ==
        '2687c787d90fdcec33ce2389263a9b3f3c0a201cf4be8ff443a60357c6a60289', 'approved_policy_CPU')
    gate_path = legacy.HERE / gate_name
    legacy.write(gate_path, dict(schema='R167_LEGACY_CPU_GATE_V1', status='PASS', tests_passed=tests_passed,
        operator_sha256=legacy.ref(legacy.HERE / 'legacy_takeover.py')['sha256'],
        tests=legacy.ref(legacy.HERE / 'test_legacy_takeover.py'),
        output=legacy.ref(legacy.HERE / log_name), policy_gate=legacy.ref(policy_cpu),
        observed_unix=time.time(), no_signals=True, no_provider_calls=True))
    census_paths = census_paths or dict(ovx2=legacy.HERE / 'NODE3_NATIVE_20260917T0815Z.json',
        ovx3=legacy.HERE / 'NODE5_NATIVE_20260917T0815Z.json')
    summaries = []
    for item in json.loads(legacy.read(legacy.INDEX))['candidates']:
        receipt = json.loads(legacy.bound(item['receipt']))
        old = json.loads(legacy.bound(receipt['original_config']))
        if old['branch'] not in (branches or legacy.BRANCHES):
            continue
        directory = legacy.HERE / receipt['candidate']
        directory.mkdir(mode=0o700)
        try:
            candidate = json.loads(legacy.bound(receipt['candidate_config']))
            observed = legacy.identity(receipt['prior_parent_pid'])
            legacy.require(observed['start_ticks'] == receipt['parent_identity_observation']['start_ticks'],
                'original_parent_start_ticks')
            census = json.loads(legacy.read(census_paths[receipt['node']]))
            if old['branch'] == 'R136_repo_reader_seed0':
                natives = [census['native']] if census['native']['root_binding']['host_root'] == old['root'] else []
            else:
                natives = [native for native in census['natives'] if any(plan.get('root') == old['root']
                    for plan in native['plans'])]
            legacy.require(len(natives) == 1, 'one_current_native')
            source = receipt['original_source']
            successor_source = source
            successor_cwd = observed['cwd']
            binding = dict(schema='R167_LEGACY_PARENT_BINDING_V1', candidate=receipt['candidate'],
                branch=old['branch'], root=old['root'], node=old['node'], parent=observed,
                original_config=receipt['original_config'], candidate_config=receipt['candidate_config'],
                original_source=source, old_output=receipt['parent_output'], native=natives[0],
                observed_unix=time.time(), policy_marker='ROHIN154_EXISTING_PARENTED_ATTENTION_ALLOCATION_V2')
            if old['branch'] in legacy.PROTECTED_BRANCHES:
                successor_source = legacy.ref(legacy.REPOSITORY / 'gpu/orch_r133_programme_parent.py')
                successor_cwd = str(legacy.REPOSITORY)
                binding['R157_AST_EQUIVALENCE'] = legacy.equivalent(legacy.bound(successor_source), legacy.bound(source))
                binding['r157_lock'] = str(Path(receipt['parent_output']) / 'R157_PARENT.lock')
                legacy.require(old['hard_end_unix'] == 1789776000, 'same_protected_wall')
            legacy.require(successor_source['sha256'] in legacy.SOURCE_HASHES, 'supported_exact_source')
            binding.update(successor_source=successor_source, successor_cwd=successor_cwd,
                python=str(Path('/proc') / str(observed['pid']) / 'exe'), quiet_window_wait_seconds=30)
            binding['python'] = str(Path(binding['python']).resolve())
            legacy.verify_identity(binding, observed)
            previous = legacy.ledger(receipt['parent_output'], old, successor_source['sha256'])
            proposed = legacy.successor_config(old, candidate, previous, receipt['parent_output'])
            legacy.write(directory / 'PROPOSED_CONFIG.json', proposed)
            preflight = legacy.cpu_preflight(binding, directory / 'PROPOSED_CONFIG.json')
            script = ('import hashlib,json,sys; from pathlib import Path; '
                'from gpu import orch_r133_programme_parent; '
                'print(json.dumps([{ "path":str(Path(module.__file__).resolve()),'
                '"sha256":hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()}'
                ' for name,module in sorted(sys.modules.items()) '
                'if (name.startswith("gpu.") or name.startswith("organism_v6.")) '
                'and getattr(module,"__file__",None)]))')
            result = subprocess.run([binding['python'], '-B', '-c', script], cwd=successor_cwd,
                env=dict(os.environ, PYTHONPATH=successor_cwd, PYTHONDONTWRITEBYTECODE='1'),
                capture_output=True, timeout=15)
            legacy.require(result.returncode == 0, 'actual_source_imports')
            imports = json.loads(result.stdout)
            legacy.require(any(pin['sha256'] == successor_source['sha256'] for pin in imports), 'actual_selected_source')
            pins = [receipt['original_config'], receipt['original_source'], receipt['candidate_config'],
                receipt['principles'], item['receipt'], legacy.ref(policy), legacy.ref(policy_cpu),
                legacy.ref(legacy.INDEX), legacy.ref(legacy.HERE / 'remote_metadata.py'),
                legacy.ref(legacy.REPOSITORY / 'gpu' / (old['node'] + '_ssh.sh')),
                legacy.ref(old['programme_path']), successor_source] + imports
            if old['branch'] == 'R136_repo_reader_seed0':
                pins.append(legacy.ref(legacy.HERE / 'reader_native_metadata.py'))
            binding['pins'] = pins
            for pin in pins:
                legacy.bound(pin)
            legacy.write(directory / 'BINDING.json', binding)
            legacy.write(directory / 'PREPARATION.json', dict(status='CPU_PROVENANCE_READY_NO_SIGNALS',
                binding=legacy.ref(directory / 'BINDING.json'), preflight=preflight,
                initial_ledger=previous, imported_source_pins=imports, native_census=legacy.ref(census_paths[old['node']]),
                no_mutation=True, observed_unix=time.time()))
            proposal = dict(schema='R167_LEGACY_PARENT_GO_V1', approved_by='Main',
                action='R167_EXACT_PARENT_ONLY_HANDOFF', binding=legacy.ref(directory / 'BINDING.json'),
                operator_sha256=legacy.ref(legacy.HERE / 'legacy_takeover.py')['sha256'],
                cpu_gate=legacy.ref(gate_path), not_before_unix=None, expires_unix=None,
                status='PROPOSAL_ONLY_NOT_AUTHORIZATION')
            legacy.write(directory / 'MAIN_GO_PROPOSAL.json', proposal)
            summaries.append(dict(candidate=receipt['candidate'], status='READY_FOR_SCOPED_MAIN_GO',
                binding=legacy.ref(directory / 'BINDING.json'), parent_pid=observed['pid'],
                native_pid=natives[0]['pid'], reserved=previous['reserved'], pending_ids=len(previous['pending_inbox_ids'])))
        except Exception as error:
            legacy.write(directory / 'PREPARATION_REFUSAL.json', dict(reason=str(error),
                error_type=type(error).__name__, observed_unix=time.time(), no_signals=True))
            summaries.append(dict(candidate=receipt['candidate'], status='DEFER_UNTOUCHED', reason=str(error)))
    legacy.write(legacy.HERE / index_name, dict(candidates=summaries, observed_unix=time.time(),
        cpu_gate=legacy.ref(gate_path), no_signals=True))
    print(json.dumps(summaries, indent=2))


if __name__ == '__main__':
    prepare()
