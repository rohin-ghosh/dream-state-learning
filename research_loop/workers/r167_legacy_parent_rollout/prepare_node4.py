"""Prepare only the exact authorized node4 parents with available original source."""

import json
from pathlib import Path
import time

import legacy_takeover as legacy
import node4_rollout as rollout


def prepare():
    coverage = json.loads(legacy.bound(dict(path=str(rollout.COVERAGE), sha256=rollout.COVERAGE_SHA)))
    policy_cpu = legacy.INDEX.with_name('CPU_GATE.json')
    legacy.require(legacy.ref(policy_cpu)['sha256'] ==
        '2687c787d90fdcec33ce2389263a9b3f3c0a201cf4be8ff443a60357c6a60289', 'policy_CPU_pin')
    legacy.require(legacy.ref(legacy.INDEX)['sha256'] == legacy.INDEX_SHA, 'policy_index_pin')
    principles = legacy.INDEX.parent / 'KERNEL0_RESUMED_SPARSE2_1045188/PRINCIPLES.md'
    legacy.require(legacy.ref(principles)['sha256'] ==
        'c94f92d5c994cab3594b06ca1163e8d211ccb5760b29b2999a2d26f5a831c248', 'principles_pin')
    gate = legacy.HERE / 'NODE4_CPU_GATE.json'
    log = legacy.HERE / 'NODE4_CPU_attempt1.log'
    legacy.require(b'77 passed' in legacy.read(log), 'actual_CPU_success')
    legacy.write(gate, dict(status='PASS', tests_passed=77,
        operator_sha256=legacy.ref(rollout.__file__)['sha256'],
        tests=legacy.ref(legacy.HERE / 'test_node4_rollout.py'), output=legacy.ref(log),
        policy_gate=legacy.ref(policy_cpu), observed_unix=time.time(), no_signals=True))
    rows = []
    for item in coverage['still_original_live_parented']:
        parent = item['parent']
        pid = parent['identity']['pid']
        name = 'NODE4_' + str(pid) + '_attention_attempt1'
        home = legacy.HERE / name
        home.mkdir(mode=0o700)
        try:
            old = json.loads(legacy.bound(parent['config']))
            current = legacy.identity(pid)
            cwd = current['cwd']
            source = legacy.ref(Path(cwd) / 'gpu/orch_r133_programme_parent.py')
            if old.get('parent_module_sha256'):
                legacy.require(source['sha256'] == old['parent_module_sha256'],
                    'original_parent_module_unavailable_no_substitution:' + old['parent_module_sha256'])
            legacy.require(source['sha256'] in legacy.SOURCE_HASHES, 'inspected_original_source')
            candidate = dict(old, principles_path=str(principles), principles_sha256=legacy.ref(principles)['sha256'])
            legacy.write(home / 'CANDIDATE_CONFIG.json', candidate)
            binding = dict(schema='R167_NODE4_PARENT_BINDING_V1', candidate=name,
                branch=old['branch'], root=old['root'], node='a40r', parent=current,
                native=item['native'], entrypoint=rollout.SLOTS[old['branch']][0],
                original_config=parent['config'], candidate_config=legacy.ref(home / 'CANDIDATE_CONFIG.json'),
                old_output=parent['output'], original_source=source, successor_source=source,
                successor_cwd=cwd, python=str(Path('/proc', str(pid), 'exe').resolve()),
                quiet_window_wait_seconds=30, observed_unix=time.time())
            rollout.verify_identity(binding, current)
            census = rollout.native_check(binding)
            previous = legacy.ledger(parent['output'], old, source['sha256'])
            proposed = legacy.successor_config(old, candidate, previous, parent['output'])
            legacy.write(home / 'PROPOSED_CONFIG.json', proposed)
            preflight = rollout.cpu_preflight(binding, home / 'PROPOSED_CONFIG.json')
            legacy.require(preflight['cursor'] == previous['reserved'], 'exact_actual_cursor')
            binding['pins'] = [source, parent['config'], binding['candidate_config'], legacy.ref(principles),
                legacy.ref(rollout.COVERAGE), legacy.ref(legacy.INDEX), legacy.ref(policy_cpu),
                legacy.ref(legacy.__file__), legacy.ref(rollout.__file__),
                legacy.ref(legacy.HERE / 'coverage_native_metadata.py'),
                legacy.ref(legacy.REPOSITORY / 'gpu/a40r_ssh.sh'), legacy.ref(old['programme_path'])] + preflight['imports']
            for pin in binding['pins']:
                legacy.bound(pin)
            legacy.write(home / 'BINDING.json', binding)
            legacy.write(home / 'PREPARATION.json', dict(status='CPU_PROVENANCE_READY_NO_SIGNALS',
                preflight=preflight, initial_ledger=previous, native=census, observed_unix=time.time()))
            rows.append(dict(candidate=name, status='READY', binding=legacy.ref(home / 'BINDING.json')))
        except Exception as error:
            legacy.write(home / 'PREPARATION_REFUSAL.json', dict(reason=str(error),
                error_type=type(error).__name__, no_signals=True, observed_unix=time.time()))
            rows.append(dict(candidate=name, status='DEFER_UNTOUCHED', reason=str(error)))
    legacy.write(legacy.HERE / 'NODE4_PREPARED_INDEX.json', dict(cpu_gate=legacy.ref(gate), candidates=rows,
        observed_unix=time.time(), no_signals=True))
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    prepare()
