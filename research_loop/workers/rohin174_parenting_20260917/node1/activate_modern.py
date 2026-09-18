"""Prepare and activate the actual patched R166 policy for one owned node1 parent."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

from inventory_node1 import HERE, Reader, digest, identity, require
from parent_custody import quiet_parent, settled_manifest, validate_owner, write


REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))
from activate_parent import TABLE, TABLE_SHA, POLICY, POLICY_SHA, PREP, PREP_SHA, read_pin


def cpu(spec_path, directory):
    spec = json.loads(spec_path.read_text())
    environment = dict(os.environ, PYTHONPATH=spec['bundle'], PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
    result = subprocess.run([sys.executable, '-B', str(HERE / 'modern_parent_runner.py'), '--spec', str(spec_path),
                             '--preflight'], cwd=spec['bundle'], env=environment, capture_output=True, text=True, timeout=60)
    path = directory / ('CPU_' + str(time.time_ns()) + '.json')
    write(path, dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr,
                    observed_unix=time.time(), spec_sha256=digest(spec_path.read_bytes())))
    require(result.returncode == 0, 'receiving_CPU:' + str(path))
    return dict(path=str(path), sha256=digest(path.read_bytes()))


def legacy_publications(row, manifest):
    binding = read_pin(row['old_parent_binding']['path'], row['old_parent_binding']['sha256'])
    original = read_pin(row['original']['config']['path'], row['original']['config']['sha256'])
    outputs = {row['old_output'], binding['previous_output'], original['r167_parent_resume']['old_output']}
    reader = Reader(128 * 1024 * 1024)
    publications = {}
    refs = []
    for output in sorted(outputs):
        paths = sorted(Path(output).glob('parent_*/RESULT.json'))
        require(len(paths) <= 2048, 'bounded_legacy_outputs')
        for path in paths:
            result, reference = reader.document(path)
            refs.append(reference)
            if result.get('status') != 'PUBLISHED':
                continue
            publication = result['inbox_publication']
            entry = dict(publication=publication,
                         message_sha256=digest(result['response']['message'].encode()), result_reference=reference)
            require(publication['id'] not in publications, 'no_duplicate_legacy_publications')
            publications[publication['id']] = entry
    return list(publications.values()), refs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--physical', type=int, choices=range(2, 8), required=True)
    parser.add_argument('--execute', action='store_true')
    arguments = parser.parse_args()
    table = read_pin(TABLE, TABLE_SHA)
    row = next(row for row in read_pin(PREP, PREP_SHA)['rows'] if row['physical'] == arguments.physical)
    assignment = next(entry for entry in table['rows'] if entry['node'] == 'a100' and entry['gpu'] == arguments.physical)
    require(assignment['child'] == row['label'] and assignment['arm'] == row['arm'], 'exact_main_assignment')
    validate_owner(row, identity(Path('/proc') / str(row['old_parent']['pid'])))
    require(digest(POLICY.read_bytes()) == POLICY_SHA, 'exact_main_builder')
    from gpu import orch_r175_parent_arms as arms
    from gpu import orch_r166_parent_policy as original_policy
    directory = HERE / ('lane' + str(arguments.physical) + '_modern_' + str(time.time_ns()))
    directory.mkdir()
    bundle = directory / 'source'
    manifest = arms.build_bundle(REPO, bundle, row['arm'])
    with (bundle / 'gpu/orch_r175_parent_arms.py').open('xb') as stream:
        stream.write(POLICY.read_bytes())
    binding = read_pin(row['old_parent_binding']['path'], row['old_parent_binding']['sha256'])
    require(binding['provider_sha256'] == manifest['files'][arms.PROVIDER_PATH]['before_sha256'], 'unchanged_provider_route')
    remote_base = '/localhome/local-rohing/orch_rohin175_node1_20260917/' + directory.name
    remote_source = remote_base + '/source'
    transfer = subprocess.run(['bash', '-c', 'set -euo pipefail; tar -cf - -C "$1" . | bash gpu/a100_ssh.sh "$2"',
                              'transfer', str(bundle), 'mkdir -p ' + shlex.quote(remote_source) +
                              ' && tar -xf - -C ' + shlex.quote(remote_source)], cwd=REPO,
                             capture_output=True, text=True, timeout=120)
    require(transfer.returncode == 0, 'own_parent_source_transfer')
    original = read_pin(row['original']['config']['path'], row['original']['config']['sha256'])
    configured = arms.configure(original, row['arm'])
    configured.update(source_root=remote_source, r166_schema=original_policy.SCHEMA,
                      predecessor_config_sha256=original_policy._digest(original), community_learner=False,
                      object_turn_limit=3, prospective_label='Rohin175_assigned_baseline_and_arm',
                      cursor_store=remote_base + '/cursor', predecessor_seed={})
    write(directory / 'CONFIG_PREVIEW.json', configured)
    pin_script = 'import hashlib,json; from pathlib import Path; root=Path(' + repr(remote_source) + '); pins=' + repr(
        {name: details['sha256'] for name, details in manifest['files'].items()}) + '; '
    pin_script += 'assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in pins.items()); print(json.dumps({"verified":True}))'
    require(original_policy.parent.remote(REPO, configured, pin_script) == {'verified': True}, 'receiving_remote_source_pins')
    reference = None
    observed = None
    from modern_parent_runner import poll
    preview = dict(root=row['root'], config=str(directory / 'CONFIG_PREVIEW.json'), repository=str(REPO),
                   cursor_store=remote_base + '/cursor')
    for batch in range(8):
        observed = poll(original_policy, preview, reference, bootstrap=True)
        reference = observed['reference']
        write(directory / ('BOOTSTRAP_' + str(batch) + '.json'), observed)
        print(json.dumps(dict(physical=row['physical'], bootstrap_batch=batch,
              caught_up=observed['snapshot']['caught_up'], bytes_read=observed['read_bytes_this_call'])), flush=True)
        if observed['snapshot']['caught_up']:
            break
    require(observed['snapshot']['caught_up'], 'bounded_train_bootstrap_incomplete_original_parent_running')
    snapshot_path = directory / ('BOOTSTRAP_' + str(batch) + '.json')
    current_manifest = settled_manifest(row)
    publications, refs = legacy_publications(row, current_manifest)
    seed = dict(schema=original_policy.SCHEMA, journal_id=observed['snapshot']['journal_id'], attempts=[],
                object_delivered_turns={}, credits={}, grammar_delivered=False,
                last_response_count=current_manifest['reserved_response_count'], last_request_count=0,
                prospective_request_count=observed['snapshot']['request_count'],
                legacy_structured_memory='NOT_PRESENT_IN_ORIGINAL_R133_RUNTIME',
                legacy_results_preserved=refs, legacy_pending_checked_before_every_tick=True)
    write(directory / 'SEED_PREVIEW.json', seed)
    pins = {str(bundle / name): details['sha256'] for name, details in manifest['files'].items()}
    for path in (bundle / 'gpu/orch_r175_parent_arms.py', HERE / 'modern_parent_runner.py',
                 HERE / 'parent_custody.py', TABLE, POLICY):
        pins[str(path)] = digest(path.read_bytes())
    spec = dict(root=row['root'], arm=row['arm'], bundle=str(bundle), repository=str(REPO),
                config=str(directory / 'CONFIG_PREVIEW.json'), seed=str(directory / 'SEED_PREVIEW.json'),
                snapshot=str(snapshot_path), output=str(directory / 'parent'), cursor_store=remote_base + '/cursor',
                pins=pins, legacy_publications=publications, policy_sha256=POLICY_SHA, assignment_sha256=TABLE_SHA)
    write(directory / 'SPEC_PREVIEW.json', spec)
    receiving = cpu(directory / 'SPEC_PREVIEW.json', directory)
    if not arguments.execute:
        print(json.dumps(dict(status='PREPARED_NO_SIGNALS', directory=str(directory), cpu=receiving)))
        return
    with quiet_parent(row, directory, [dict(path=path, sha256=value) for path, value in pins.items()] + [receiving]) as paused:
        publications, refs = legacy_publications(row, paused.manifest)
        seed.update(last_response_count=paused.manifest['reserved_response_count'], legacy_results_preserved=refs)
        write(directory / 'SEED.json', seed)
        configured['predecessor_seed'] = dict(path=str(directory / 'SEED.json'), sha256=digest((directory / 'SEED.json').read_bytes()))
        write(directory / 'CONFIG.json', configured)
        spec.update(config=str(directory / 'CONFIG.json'), seed=str(directory / 'SEED.json'), legacy_publications=publications)
        for path in (directory / 'CONFIG.json', directory / 'SEED.json', snapshot_path):
            spec['pins'][str(path)] = digest(path.read_bytes())
        write(directory / 'SPEC_FINAL_CPU.json', spec)
        receiving_final = cpu(directory / 'SPEC_FINAL_CPU.json', directory)
        paused.retire()
    admission = directory / 'ADMISSION.json'
    write(admission, dict(status='PASS', main_policy_sha256=POLICY_SHA, main_assignment_sha256=TABLE_SHA,
          predecessor_terminal=True, pending_reconciled=True, reconciliation='PRESERVED_AND_RENDER_GATED_NEVER_REPUBLISHED',
          cpu=receiving_final, child_signals=0, observed_unix=time.time()))
    spec.update(admission=str(admission), admission_sha256=digest(admission.read_bytes()))
    write(directory / 'SPEC.json', spec)
    environment = dict(os.environ, PYTHONPATH=str(bundle), PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
    command = [sys.executable, '-B', str(HERE / 'modern_parent_runner.py'), '--spec', str(directory / 'SPEC.json')]
    with (directory / 'RUNNER.log').open('xb') as log:
        successor = subprocess.Popen(command, cwd=bundle, env=environment, stdin=subprocess.DEVNULL,
                                     stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    write(directory / 'SPAWNED.json', dict(pid=successor.pid, observed_unix=time.time(), command=command, child_signals=0))
    deadline = time.monotonic() + 30
    while not (directory / 'STARTED.json').exists():
        require(successor.poll() is None, 'successor_failed_before_STARTED')
        require(time.monotonic() < deadline, 'STARTED_observation_timeout')
        time.sleep(.1)
    print(json.dumps(dict(status='ACTUAL_PATCHED_R166_PARENT_STARTED_NOT_DELIVERY', arm=row['arm'],
          label=row['label'], pid=successor.pid, directory=str(directory))), flush=True)


if __name__ == '__main__':
    main()
