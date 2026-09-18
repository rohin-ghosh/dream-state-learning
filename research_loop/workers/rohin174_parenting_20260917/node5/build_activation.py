"""Build and CPU-test immutable Main R175 bundles inside NODE5's write scope."""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
BUILDER_SHA = 'ae2c9df909d9b48ebebef968690ee2e4c9085452151dbb96474311cf55b11923'
ASSIGNMENTS_SHA = '25b45432bebb388e920d5cc8dc8fed6c705cd54156cbfd530828e1520a9174b2'
RESPONSE_SHA = 'a0f8d74530b558724a8b5636a5b53556abd21267c316d94b3beeb08cd41c61a1'
ASSIGNMENTS = REPO / 'research_loop/workers/rohin174_parenting_20260917/ASSIGNMENTS_V1.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, indent=2, sort_keys=True)
        stream.write('\n')


def add_copy(path, raw):
    assert path.is_relative_to(HERE) and not path.exists()
    patch = '*** Begin Patch\n*** Add File: ' + str(path) + '\n'
    patch += ''.join('+' + line + '\n' for line in raw.decode().splitlines())
    patch += '*** End Patch\n'
    subprocess.run(['apply_patch', patch], check=True, stdout=subprocess.DEVNULL)
    assert path.read_bytes() == raw, 'byte_exact_copy'
    path.chmod(0o444)


def dependency_closure(source, names):
    pending, checked, added = list(names), set(), {}
    while pending:
        name = pending.pop()
        if name in checked or not name.endswith('.py'):
            continue
        checked.add(name)
        require_source = source / name
        tree = ast.parse(require_source.read_text(), str(require_source))
        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
                modules.add(node.module)
                modules.update(node.module + '.' + alias.name for alias in node.names)
        for module in modules:
            if module.split('.')[0] not in ('gpu', 'organism_v6'):
                continue
            base = Path(*module.split('.'))
            candidates = [base.with_suffix('.py'), base / '__init__.py']
            candidates.extend(parent / '__init__.py' for parent in base.parents if str(parent) != '.')
            for relative in candidates:
                origin, target = REPO / relative, source / relative
                if not origin.is_file():
                    continue
                relative_name = str(relative)
                if not target.exists():
                    assert origin.stat().st_size <= 16 * 1024 * 1024
                    add_copy(target, origin.read_bytes())
                    added[relative_name] = sha(target)
                if relative_name not in checked:
                    pending.append(relative_name)
        assert len(checked) <= 500, 'bounded_local_dependency_closure'
    return added


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arm', choices=('A', 'B', 'C', 'D'), required=True)
    parser.add_argument('--label', choices=('run1', 'pilot', 'repo_reader', 'C1', 'C3', 'C4', 'C5'))
    arguments = parser.parse_args()
    assert sha(REPO / 'gpu/orch_r175_parent_arms.py') == BUILDER_SHA
    assert sha(ASSIGNMENTS) == ASSIGNMENTS_SHA
    assert sha(REPO / 'gpu/orch_r175_parent_response.py') == RESPONSE_SHA
    sys.path.insert(0, str(REPO))
    from gpu import orch_r175_parent_arms as arms
    activation = HERE / ('ACTIVATION_' + arguments.arm + '_' + str(time.time_ns()))
    source = activation / 'source'
    bundle = arms.build_bundle(REPO, source, arguments.arm)
    extras = {
        'gpu/orch_r175_parent_arms.py': REPO / 'gpu/orch_r175_parent_arms.py',
        'gpu/orch_r175_parent_response.py': REPO / 'gpu/orch_r175_parent_response.py',
        'gpu/ovx3_ssh.sh': REPO / 'gpu/ovx3_ssh.sh',
        'activate_parent.py': HERE / 'activate_parent.py',
        'snapshot_identity.py': HERE / 'snapshot_identity.py',
        'tests/test_node5_r175_activation.py': HERE / 'test_activate_parent.py',
        'tests/test_node5_snapshot_identity.py': HERE / 'test_snapshot_identity.py',
        'tests/test_original_r166_parent_snapshot.py': REPO / 'tests/test_orch_r166_parent_snapshot.py',
        'PARENT_METADATA_ERRATA_V1.md': ASSIGNMENTS.parent / 'PARENT_METADATA_ERRATA_V1.md',
    }
    for name, origin in extras.items():
        if name == 'gpu/ovx3_ssh.sh':
            raw = ('#!/bin/bash\nset -euo pipefail\nexec bash ' + shlex.quote(str(origin)) + ' "$@"\n').encode()
            add_copy(source / name, raw)
        else:
            add_copy(source / name, origin.read_bytes())
    transport = dict(path=str(REPO / 'gpu/ovx3_ssh.sh'), sha256=sha(REPO / 'gpu/ovx3_ssh.sh'),
                     mode='SANCTIONED_EXISTING_HOST_WRAPPER_DELEGATION', credentials_copied=False)
    add_copy(source / 'TRANSPORT_REFERENCE.json',
             (json.dumps(transport, sort_keys=True, indent=2) + '\n').encode())
    closure = dependency_closure(source, [*bundle['files'], *extras])
    pins = {name: sha(source / name) for name in
            (*bundle['files'], *extras, *closure, 'ARM_BUNDLE.json', 'TRANSPORT_REFERENCE.json')}
    command = ['uv', 'run', '--offline', '--no-project', '--with', 'pytest', '--python', '/usr/bin/python3',
               'python', '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-c', '/dev/null',
               '--basetemp', str(activation / 'CPU_TMP'), str(source / 'tests/test_node5_r175_activation.py'),
               str(source / 'tests/test_node5_snapshot_identity.py'), str(source / 'tests/test_original_r166_parent_snapshot.py')]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(source))
    result = subprocess.run(command, cwd=source, env=environment, capture_output=True, text=True)
    (activation / 'CPU.stdout').write_text(result.stdout)
    (activation / 'CPU.stderr').write_text(result.stderr)
    cpu = dict(schema='R175_NODE5_ACTUAL_BUNDLE_CPU_V1', status='PASS' if result.returncode == 0 else 'FAIL',
        execution_kind='CPU_ONLY', source_pins=pins, command=command, returncode=result.returncode,
        activation_tests_executed=result.returncode == 0, observed_unix=time.time(),
        stdout_sha256=sha(activation / 'CPU.stdout'), stderr_sha256=sha(activation / 'CPU.stderr'),
        test_pins={'tests/test_node5_r175_activation.py': pins['tests/test_node5_r175_activation.py']},
        Main_builder_tests_are_separate=True, builder_sha256=BUILDER_SHA)
    cpu['unchanged_dependency_closure_added'] = closure
    write(activation / 'CPU.json', cpu)
    if result.returncode:
        print(json.dumps(dict(status='CPU_FAILED_NO_PARENT_ACTION', path=str(activation))))
        return 1
    remote = '/localhome/local-rohing/orch_r175_node5_20260917_' + activation.name.lower()
    archive = activation / 'SOURCE.tar'
    subprocess.run(['tar', '-cf', str(archive), '-C', str(source), *pins], check=True)
    receiving_command = ('test ! -e ' + shlex.quote(remote) + ' && mkdir -p ' +
        shlex.quote(remote + '/source') + ' && tar -xf - -C ' + shlex.quote(remote + '/source'))
    with archive.open('rb') as handle:
        transfer = subprocess.run(['bash', str(source / 'gpu/ovx3_ssh.sh'), receiving_command],
                                  stdin=handle, capture_output=True, text=True, timeout=40)
    assert transfer.returncode == 0, 'receiving_source_transfer_failed_no_parent_action'
    receiving_script = ('import hashlib,json; from pathlib import Path; root=Path(' + repr(remote + '/source') +
        '); pins=' + repr(pins) + '; assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value '
        'for name,value in pins.items()); '
        '[compile((root/name).read_text(),str(root/name),"exec") for name in pins if name.endswith(".py")]; '
        'print(json.dumps({"source_verified":True,"compile_pass":True,"gpu_model_launch":False}))')
    receiving = subprocess.run(['bash', str(source / 'gpu/ovx3_ssh.sh'),
        'python3 -B -c ' + shlex.quote(receiving_script)], capture_output=True, text=True, timeout=40)
    assert receiving.returncode == 0, 'receiving_CPU_failed_no_parent_action'
    receiving_proof = json.loads(receiving.stdout)
    write(activation / 'RECEIVING_CPU.json', dict(receiving_proof, observed_unix=time.time(), source_pins=pins))
    inventory = json.loads((HERE / 'INVENTORY_1789676353816670694.json').read_bytes())
    table = json.loads(ASSIGNMENTS.read_bytes())
    assigned = {row['child']: row for row in table['rows'] if row['node'] == 'ovx3' and row['arm'] == arguments.arm}
    manifests = []
    for row in inventory['rows']:
        if row['label'] not in assigned:
            continue
        if arguments.label and row['label'] != arguments.label:
            continue
        assert row['label'] != 'C2'
        original_config = json.loads(Path(row['config']['path']).read_bytes())
        remote_cursor = remote + '/' + row['label'] + '_cursor'
        snapshot_script = ('import json; from snapshot_identity import install,stored_poll; install(); ref=None\n'
            'for sequence in range(256):\n'
            ' observed=stored_poll(' + repr(original_config['root']) + ',' + repr(remote_cursor) + ',ref); ref=observed["reference"]\n'
            ' if observed["snapshot"]["caught_up"]: break\n'
            'assert observed["snapshot"]["caught_up"],"actual_snapshot_bootstrap_incomplete"\n'
            'print(json.dumps(observed))')
        actual_snapshot = subprocess.run(['bash', str(source / 'gpu/ovx3_ssh.sh'),
            'PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=' + shlex.quote(remote + '/source') +
            ' python3 -B -c ' + shlex.quote(snapshot_script)], capture_output=True, text=True, timeout=120)
        (activation / (row['label'] + '_SNAPSHOT.stderr')).write_text(actual_snapshot.stderr)
        if actual_snapshot.returncode:
            write(activation / (row['label'] + '_SNAPSHOT_FAILED.json'), dict(returncode=actual_snapshot.returncode,
                source_pins=pins, no_parent_signals=True, stderr_sha256=sha(activation / (row['label'] + '_SNAPSHOT.stderr'))))
            print(json.dumps(dict(status='ACTUAL_SNAPSHOT_FAILED_NO_PARENT_ACTION', label=row['label'], path=str(activation))))
            continue
        snapshot_path = activation / (row['label'] + '_RECEIVING_SNAPSHOT.json')
        write(snapshot_path, json.loads(actual_snapshot.stdout))
        path = activation / (row['label'] + '_MANIFEST.json')
        document = dict(schema='R175_NODE5_PARENT_ACTIVATION_V1', label=row['label'], arm=arguments.arm,
            predecessor=row, assignments=dict(path=str(ASSIGNMENTS), sha256=ASSIGNMENTS_SHA),
            source=str(source), source_pins=pins, operator_sha256=pins['activate_parent.py'],
            sanctioned_transport=transport,
            output=str(activation / row['label']), remote_source=remote + '/source',
            remote_cursor=remote_cursor,
            receiving_snapshot=dict(path=str(snapshot_path), sha256=sha(snapshot_path)),
            cpu_receipt=dict(path=str(activation / 'CPU.json'), sha256=sha(activation / 'CPU.json')),
            receiving_cpu_receipt=dict(path=str(activation / 'RECEIVING_CPU.json'),
                                       sha256=sha(activation / 'RECEIVING_CPU.json')))
        write(path, document)
        manifests.append(dict(label=row['label'], path=str(path), sha256=sha(path)))
    write(activation / 'READY.json', dict(status='CPU_AND_RECEIVING_READY_NOT_STARTED', manifests=manifests,
        source=str(source), observed_unix=time.time(), peer_channels_active=False))
    print(json.dumps(dict(status='CPU_AND_RECEIVING_READY_NOT_STARTED', path=str(activation), manifests=manifests)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
