"""Build/admit Main's bundle and replace only one exact node1 legacy parent."""

import argparse
import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from inventory_node1 import HERE, Reader, digest, identity, require
from parent_custody import quiet_parent, settled_manifest, validate_owner, write


REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))
TABLE = HERE.parent / 'ASSIGNMENTS_V1.json'
TABLE_SHA = '25b45432bebb388e920d5cc8dc8fed6c705cd54156cbfd530828e1520a9174b2'
POLICY = REPO / 'gpu/orch_r175_parent_arms.py'
POLICY_SHA = 'ae2c9df909d9b48ebebef968690ee2e4c9085452151dbb96474311cf55b11923'
PREP = HERE / 'ACTIVATION_PREP_1789677032315502264/ASSIGNMENTS.json'
PREP_SHA = 'f04a5e04f285b190d5210e98db5f2078b176afdbe6bc1c493d9626a13294d67d'


def complete_imports(bundle, manifest):
    pending = [POLICY.relative_to(REPO).as_posix(), 'gpu/orch_route_parent_campaign_providers.py']
    visited = set()
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        require(len(visited) <= 256, 'bounded_parent_source_import_closure')
        destination = bundle / name
        if not destination.exists():
            raw = Reader().raw(REPO / name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as stream:
                stream.write(raw)
            manifest['files'][name] = dict(sha256=digest(raw), before_sha256=digest(raw),
                                           node1_import_dependency_only=True)
        for node in ast.walk(ast.parse(destination.read_text())):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module] + [node.module + '.' + alias.name for alias in node.names]
            for module in modules:
                if module.split('.')[0] not in ('gpu', 'organism_v6'):
                    continue
                for relative in (module.replace('.', '/') + '.py', module.replace('.', '/') + '/__init__.py'):
                    if (REPO / relative).is_file():
                        pending.append(relative)
    return sorted(visited)


def read_pin(path, expected):
    raw = Reader().raw(path)
    require(digest(raw) == expected, 'explicit_authorized_bytes:' + str(path))
    return json.loads(raw)


def preflight(spec_path, directory):
    spec = json.loads(spec_path.read_text())
    environment = dict(os.environ, PYTHONPATH=spec['bundle'], PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
    result = subprocess.run([sys.executable, '-B', str(HERE / 'parent_runner.py'), '--spec', str(spec_path),
                             '--preflight'], cwd=spec['bundle'], env=environment,
                            capture_output=True, text=True, timeout=45)
    path = directory / ('RECEIVING_CPU_' + str(time.time_ns()) + '.json')
    write(path, dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr,
                    spec_sha256=digest(spec_path.read_bytes()), observed_unix=time.time()))
    require(result.returncode == 0, 'actual_parent_receiving_cpu_failed:' + str(path))
    return dict(path=str(path), sha256=digest(path.read_bytes()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--physical', type=int, required=True, choices=range(2, 8))
    parser.add_argument('--execute', action='store_true')
    arguments = parser.parse_args()
    table = read_pin(TABLE, TABLE_SHA)
    prepared = read_pin(PREP, PREP_SHA)
    row = next(row for row in prepared['rows'] if row['physical'] == arguments.physical)
    assignment = next(row for row in table['rows'] if row['node'] == 'a100' and row['gpu'] == arguments.physical)
    require(assignment['child'] == row['label'] and assignment['arm'] == row['arm'], 'exact_main_lane_assignment')
    validate_owner(row, identity(Path('/proc') / str(row['old_parent']['pid'])))
    require(digest(POLICY.read_bytes()) == POLICY_SHA, 'exact_main_policy')
    module_spec = importlib.util.spec_from_file_location('main_r175_arms', POLICY)
    arms = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(arms)
    directory = HERE / ('lane' + str(arguments.physical) + '_activation_' + str(time.time_ns()))
    directory.mkdir()
    bundle = directory / 'source'
    manifest = arms.build_bundle(REPO, bundle, row['arm'])
    with (bundle / 'gpu/orch_r175_parent_arms.py').open('xb') as stream:
        stream.write(POLICY.read_bytes())
    (bundle / 'gpu/orch_r175_parent_arms.py').chmod(0o444)
    dependencies = complete_imports(bundle, manifest)
    write(directory / 'IMPORT_CLOSURE.json', dict(files=manifest['files'], visited=dependencies))
    original_binding = read_pin(row['old_parent_binding']['path'], row['old_parent_binding']['sha256'])
    require(original_binding['provider_sha256'] == manifest['files'][arms.PROVIDER_PATH]['before_sha256'],
            'same_actual_provider_route_before_cap_only_patch')
    config = read_pin(row['original']['config']['path'], row['original']['config']['sha256'])
    configured = arms.configure(config, row['arm'])
    require(configured['root'] == row['root'] and configured['hard_end_unix'] == row['original_hard_end_unix'],
            'unchanged_life_and_wall')
    principles = Reader().raw(config['principles_path'])
    require(digest(principles) == config['principles_sha256'], 'original_principles_pin')
    updated = arms.replace_once(principles.decode(), '90-word message cap',
                                str(arms.specification(row['arm'])['words']) + '-word message cap')
    principles_path = directory / 'PRINCIPLES.md'
    with principles_path.open('x') as stream:
        stream.write(updated)
    configured.update(principles_path=str(principles_path), principles_sha256=digest(updated.encode()))
    write(directory / 'PRINCIPLES_PROVENANCE.json', dict(original_path=config['principles_path'],
          original_sha256=config['principles_sha256'], updated_sha256=configured['principles_sha256'],
          sole_change='selected word cap; all other English/masking/private/budget instructions unchanged'))
    write(directory / 'CONFIG.json', configured)
    legacy = Reader().raw(row['original']['source']['path']).decode()
    require(digest(legacy.encode()) == row['original']['source']['sha256'], 'actual_legacy_source')
    legacy = arms.replace_once(legacy, 'message(string, at most90 words)',
                               'message(string, at most ' + str(arms.specification(row['arm'])['words']) + ' words)')
    with (directory / 'LEGACY_PARENT.py').open('x') as stream:
        stream.write(legacy)
    pins = {str(bundle / name): details['sha256'] for name, details in manifest['files'].items()}
    for path in (bundle / 'gpu/orch_r175_parent_arms.py', directory / 'CONFIG.json', directory / 'LEGACY_PARENT.py',
                 principles_path, Path(configured['programme_path']), HERE / 'activate_parent.py',
                 HERE / 'parent_runner.py', HERE / 'parent_custody.py', TABLE, POLICY):
        pins[str(path)] = digest(path.read_bytes())
    current_manifest = settled_manifest(row)
    spec = dict(root=row['root'], arm=row['arm'], bundle=str(bundle), repository=str(REPO),
                legacy_source=str(directory / 'LEGACY_PARENT.py'), config=str(directory / 'CONFIG.json'),
                output=str(directory / 'parent'), reserved_response_count=current_manifest['reserved_response_count'],
                pins=pins, policy_sha256=POLICY_SHA, assignment_sha256=TABLE_SHA,
                runtime='ACTUAL_LEGACY_PARENT_LOOP_WITH_MAIN_ARM_INSTRUCTION_AND_BUNDLE_PROVIDER',
                original_root=row['root'], original_parent=row['old_parent'], peer_relay_enabled=False)
    write(directory / 'PREVIEW_SPEC.json', spec)
    cpu = preflight(directory / 'PREVIEW_SPEC.json', directory)
    write(directory / 'PREPARED.json', dict(status='ACTUAL_RECEIVING_CPU_PASS', cpu=cpu,
          row=row, assignment=assignment, bundle_manifest_sha256=digest((bundle / 'ARM_BUNDLE.json').read_bytes()),
          parent_signals=0, child_signals=0))
    if not arguments.execute:
        print(json.dumps(dict(status='PREPARED_NO_SIGNALS', directory=str(directory), cpu=cpu)))
        return
    references = [dict(path=path, sha256=expected) for path, expected in pins.items()] + [cpu]
    try:
        with quiet_parent(row, directory, references) as paused:
            spec['reserved_response_count'] = paused.manifest['reserved_response_count']
            spec['preserved_pending_publications'] = paused.manifest['pending_publications']
            write(directory / 'SPEC.json', spec)
            final_cpu = preflight(directory / 'SPEC.json', directory)
            write(directory / 'OWN_CPU_PROVENANCE_GO.json', dict(status='PASS', execution_kind='CPU_ONLY',
                  main_policy_sha256=POLICY_SHA, main_assignment_sha256=TABLE_SHA, cpu=final_cpu,
                  child_mutations=0, observed_unix=time.time()))
            paused.retire()
        environment = dict(os.environ, PYTHONPATH=str(bundle), PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
        command = [sys.executable, '-B', str(HERE / 'parent_runner.py'), '--spec', str(directory / 'SPEC.json')]
        with (directory / 'RUNNER.log').open('xb') as output:
            successor = subprocess.Popen(command, cwd=bundle, env=environment, stdin=subprocess.DEVNULL,
                                         stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        write(directory / 'SPAWNED.json', dict(pid=successor.pid, observed_unix=time.time(), command=command,
              child_signals=0, retired_parent_pid=row['old_parent']['pid']))
        deadline = time.monotonic() + 30
        while not (directory / 'parent/STARTED.json').exists():
            require(successor.poll() is None, 'new_parent_failed_before_STARTED')
            require(time.monotonic() < deadline, 'new_parent_started_observation_timeout')
            time.sleep(.1)
        started = json.loads((directory / 'parent/STARTED.json').read_text())
        require(started['pid'] == successor.pid and started['config_sha256'] == pins[str(directory / 'CONFIG.json')],
                'actual_successor_started_config')
        actor = identity(Path('/proc') / str(successor.pid))
        write(directory / 'PARENT_ACTIVATED.json', dict(status='ACTUAL_PARENT_STARTED_NOT_DELIVERY',
              arm=row['arm'], label=row['label'], actor=actor, source_spec_sha256=digest((directory / 'SPEC.json').read_bytes()),
              started_sha256=digest((directory / 'parent/STARTED.json').read_bytes()), observed_unix=time.time(),
              child_signals=0, publication_verified=False, request_exposure_verified=False))
        print(json.dumps(dict(status='ACTUAL_PARENT_STARTED_NOT_DELIVERY', directory=str(directory),
                              parent_pid=successor.pid, arm=row['arm'], label=row['label'])))
    except BaseException as error:
        write(directory / 'ACTIVATION_FAILURE.json', dict(error_type=type(error).__name__,
              error=str(error), observed_unix=time.time(), child_signals=0))
        raise


if __name__ == '__main__':
    main()
