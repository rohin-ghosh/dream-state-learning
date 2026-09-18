"""R178 explicit two-control parent-only takeover, using existing exact quiet custody."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from activate_parent import POLICY, POLICY_SHA, REPO, complete_imports
from frozen_parent_custody import quiet_parent, settled_manifest
from inventory_node1 import HERE, Reader, digest, identity, require, unchanged
from parent_custody import write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--physical', type=int, choices=(0, 1), required=True)
    arguments = parser.parse_args()
    inventory = json.loads(Reader().raw(HERE / 'R178_CONTROL_INVENTORY.json'))
    original = next(row for row in inventory['rows'] if row['physical'] == arguments.physical)
    require(not any(item['common_baseline'] for item in original['native']['inbox']), 'actual_control_common_baseline_absent')
    require(unchanged(original['parent'], identity(Path('/proc') / str(original['parent']['pid']))), 'exact_current_control_parent')
    binding = original['binding']
    require(digest(Reader().raw(original['binding_path'])) == original['binding_sha256']
            and digest(Reader().raw(binding['config'])) == binding['config_sha256']
            and digest(Reader().raw(binding['source_copy'])) == binding['source_sha256'], 'unchanged_control_parent_sources')
    row = dict(physical=arguments.physical, old_parent=original['parent'],
               old_parent_binding=dict(path=original['binding_path'], sha256=original['binding_sha256']),
               root=original['config']['root'], old_output=binding['output'])
    require(digest(Reader().raw(POLICY)) == POLICY_SHA, 'same_Main_A_arm_policy')
    module_spec = importlib.util.spec_from_file_location('r178_main_arms', POLICY)
    arms = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(arms)
    directory = HERE / ('frozen' + str(arguments.physical) + '_parenting_' + str(time.time_ns()))
    directory.mkdir(mode=0o700)
    bundle = directory / 'source'
    manifest = arms.build_bundle(REPO, bundle, 'A')
    with (bundle / 'gpu/orch_r175_parent_arms.py').open('xb') as stream:
        stream.write(Reader().raw(POLICY))
    complete_imports(bundle, manifest)
    configured = arms.configure(original['config'], 'A')
    principles = Reader().raw(configured['principles_path'])
    require(digest(principles) == configured['principles_sha256'], 'original_control_principles_pin')
    updated = arms.replace_once(principles.decode(), '90-word message cap', '240-word message cap')
    principles_path = directory / 'PRINCIPLES.md'
    with principles_path.open('x') as stream:
        stream.write(updated)
    configured.update(principles_path=str(principles_path), principles_sha256=digest(updated.encode()))
    write(directory / 'CONFIG.json', configured)
    legacy = arms.replace_once(Reader().raw(binding['source_copy']).decode(), 'message(string, at most90 words)', 'message(string, at most 240 words)')
    with (directory / 'LEGACY_PARENT.py').open('x') as stream:
        stream.write(legacy)
    phase = dict(phase='R178_PROSPECTIVE_FROZEN_PARENT_CURRICULUM', physical=arguments.physical, root=row['root'],
          arm='A', cadence=1, baseline_once=True, matched_prior_curriculum_claim=False,
          preserved_native_pid=original['native']['pid'], preserved_native_plan_sha256=original['native']['plan_sha256'],
          preserved_native_guard_sha256=original['native']['guard_sha256'], weight_or_sleep_changes=False,
          authority='Main R178 explicit all26 includes two frozen parents; preserve frozen/no-adapter/no-sleep conditions',
          observed_unix=time.time())
    write(directory / 'PHASE.json', phase)
    pins = {str(bundle / name): details['sha256'] for name, details in manifest['files'].items()}
    for path in (bundle / 'gpu/orch_r175_parent_arms.py', directory / 'CONFIG.json', directory / 'LEGACY_PARENT.py',
                 principles_path, Path(configured['programme_path']), HERE / 'parent_runner.py', HERE / 'forward_parent.py',
                 HERE / 'frozen_forward_parent.py', HERE / 'activate_frozen_parents.py', HERE / 'frozen_parent_custody.py',
                 REPO / 'gpu/orch_r175_parent_response.py', directory / 'PHASE.json'):
        pins[str(path)] = digest(Reader().raw(path))
    prior = settled_manifest(row)
    spec = dict(root=row['root'], arm='A', physical=arguments.physical, bundle=str(bundle), repository=str(REPO),
          legacy_source=str(directory / 'LEGACY_PARENT.py'), config=str(directory / 'CONFIG.json'), output=str(directory / 'parent'),
          reserved_response_count=prior['reserved_response_count'], pins=pins, policy_sha256=POLICY_SHA,
          assignment_sha256=digest(Reader().raw(directory / 'PHASE.json')), phase=phase['phase'],
          predecessor_spec=original['binding_path'], peer_relay_enabled=False)
    write(directory / 'PREVIEW_SPEC.json', spec)
    environment = dict(os.environ, PYTHONPATH=str(bundle), PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
    cpu = subprocess.run([sys.executable, '-B', str(HERE / 'parent_runner.py'), '--spec', str(directory / 'PREVIEW_SPEC.json'), '--preflight'],
                         cwd=bundle, env=environment, capture_output=True, text=True, timeout=45)
    write(directory / 'CPU.json', dict(returncode=cpu.returncode, stdout=cpu.stdout, stderr=cpu.stderr))
    require(cpu.returncode == 0, 'actual_frozen_parent_loop_CPU')
    refs = [dict(path=path, sha256=expected) for path, expected in pins.items()]
    with quiet_parent(row, directory, refs) as paused:
        for result_path in Path(binding['output']).glob('parent_*/RESULT.json'):
            result = json.loads(Reader().raw(result_path))
            require(result['status'] == 'PUBLISHED' or 'sent_unix' not in result, 'unknown_old_publication_requires_reconciliation')
        spec['reserved_response_count'] = paused.manifest['reserved_response_count']
        spec['preserved_pending_publications'] = paused.manifest['pending_publications']
        write(directory / 'SPEC.json', spec)
        paused.retire()
    command = [sys.executable, '-B', str(HERE / 'frozen_forward_parent.py'), '--spec', str(directory / 'SPEC.json')]
    with (directory / 'RUNNER.log').open('xb') as output:
        child = subprocess.Popen(command, cwd=bundle, env=environment, stdin=subprocess.DEVNULL,
                                 stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    deadline = time.monotonic() + 30
    while not (directory / 'parent/STARTED.json').exists():
        require(child.poll() is None and time.monotonic() < deadline, 'actual_control_parent_started')
        time.sleep(.1)
    receipt = dict(phase, actor=identity(Path('/proc') / str(child.pid)), observed_unix=time.time(),
                   spec_sha256=digest(Reader().raw(directory / 'SPEC.json')), publication_verified=False, child_signals=0)
    write(directory / 'PARENT_ACTIVATED.json', receipt)
    print(json.dumps(dict(physical=arguments.physical, parent_pid=child.pid, directory=str(directory),
                          status='PROSPECTIVE_A1_PARENT_STARTED_NOT_DELIVERY', native_pid_untouched=original['native']['pid'])))


if __name__ == '__main__':
    main()
