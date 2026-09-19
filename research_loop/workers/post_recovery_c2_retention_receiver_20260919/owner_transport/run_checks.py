"""Offline tests and immutable source/hash receipts; no live owner or node actions."""

import argparse
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import time

import common as core
from common import literal, pins_match, read, reference, require, sha, write_once


TESTS = ('test_owner_transport.py', 'test_binding.py', 'test_coordinator.py', 'test_integration.py')
RUNTIME = ('common.py', 'owner.py', 'transport.py', 'c2_owner_binding.py', 'successor.py',
    'coordinator.py', 'integration.py', 'cli.py')


def snapshot():
    bundle = core.HERE.parent / 'prepared_epoch4_v5/C2/epoch4'
    manifest_path = bundle / 'EPOCH4_SOURCE.json'
    require(sha(manifest_path) == 'f51ad85c16dbfc4f683baeee7147aecc9730ea993a9ef194dee6037555edac01',
        'sealed_epoch4_manifest_unchanged')
    manifest = read(manifest_path)
    sources = {str(bundle / 'source' / name): expected for name, expected in manifest['new_source_pins'].items()}
    sources.update({str(bundle / 'tools' / name): expected for name, expected in manifest['helper_pins'].items()})
    sources.update({str(bundle / 'source' / name): entry['sha256'] for name, entry in manifest['additional_assets'].items()})
    pins_match(sources)
    archive = bundle.parents[1] / 'C2_EPOCH4_OFFLINE_CANDIDATE.tar.gz'
    require(sha(archive) == '79b5d29bd6bc44e3e11ec5a44cb44f087c55f989a28dd67ae702452753cb13eb', 'sealed_epoch4_archive_unchanged')
    original_manifest = core.OWNER / 'c2_session1/MANIFEST.json'
    original = read(original_manifest)
    pins_match(original['local_source_sha256'])
    boundary = core.REPO / 'research_loop/workers/post_recovery_retention_boundary_20260918'
    inputs = {str(path): sha(path) for path in (original_manifest, core.OWNER / 'c2_service.py',
        core.REPO / 'gpu/ovx3_ssh.sh', core.REPO / 'research_loop/__init__.py',
        *(boundary / name for name in ('boundary.py', 'coordinator.py', 'operations.py', 'test_boundary.py', 'test_coordinator.py')))}
    inputs.update(original['local_source_sha256'])
    authored = {str(path): sha(path) for path in sorted(core.HERE.iterdir()) if path.suffix in ('.py', '.md')}
    overlay = {str((core.HERE / name).relative_to(core.REPO)): sha(core.HERE / name) for name in RUNTIME}
    for path in (core.REPO / 'research_loop/__init__.py', *(boundary / name for name in ('boundary.py', 'coordinator.py', 'operations.py'))):
        overlay[str(path.relative_to(core.REPO))] = sha(path)
    return dict(schema='C2_OWNER_TRANSPORT_OFFLINE_SOURCE_MANIFEST_V1', authored=authored,
        unchanged_original_inputs=inputs, node_coordinator_overlay=overlay,
        readonly_node_helpers={name: sha(core.HERE / name) for name in ('common.py', 'c2_owner_binding.py')},
        sealed_epoch4=dict(manifest=reference(manifest_path), archive=reference(archive),
            python_files=len(manifest['new_source_pins']), all_source_helper_asset_pins_verified=True),
        permission_granted=False, native_source_changes=[])


def package(output, manifest):
    archive = output / 'C2_OWNER_COORDINATOR_OVERLAY.tar.gz'
    with tarfile.open(archive, 'x:gz') as stream:
        for name in sorted(manifest['node_coordinator_overlay']):
            stream.add(core.REPO / name, arcname=name, recursive=False)
    with tarfile.open(archive, 'r:gz') as stream:
        require(set(stream.getnames()) == set(manifest['node_coordinator_overlay']), 'exact_overlay_members')
        for member in stream.getmembers():
            require(member.isfile() and hashlib.sha256(stream.extractfile(member).read()).hexdigest()
                == manifest['node_coordinator_overlay'][member.name], 'exact_overlay_member_bytes')
    return reference(archive)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    arguments = parser.parse_args()
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = literal(arguments.output or core.HERE / ('checks_' + timestamp))
    require(output.parent == core.HERE and not output.exists(), 'new_scoped_check_receipt_directory')
    before = snapshot()
    for path in core.HERE.glob('*.py'):
        compile(path.read_bytes(), str(path), 'exec')
    output.mkdir(mode=0o700)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
    groups = []
    commands = [(name, [sys.executable, '-B', str(core.HERE / name)]) for name in TESTS]
    commands.append(('cli_help', [sys.executable, '-B', str(core.HERE / 'cli.py'), '--help']))
    for name, command in commands:
        started = time.monotonic()
        result = subprocess.run(command, cwd=core.REPO, env=environment, capture_output=True, timeout=60)
        text = result.stdout + result.stderr
        log = output / (name + '.log')
        with log.open('xb') as stream:
            stream.write(text)
        matched = re.search(rb'Ran (\d+) tests? in', text)
        count = int(matched.group(1)) if matched else 0
        groups.append(dict(name=name, command=command, returncode=result.returncode, tests=count,
            elapsed_seconds=time.monotonic() - started, log=reference(log)))
    unchanged = snapshot() == before
    passed = unchanged and all(group['returncode'] == 0 for group in groups)
    manifest = write_once(output / 'SOURCE_MANIFEST.json', before)
    overlay = package(output, before) if passed else None
    main_observation = core.REPO / 'research_loop/workers/post_recovery_pair_receiving_checks_20260919/C2_EPOCH4_FORWARD_B_1789787815.json'
    receipt = dict(schema='C2_OWNER_TRANSPORT_OFFLINE_TEST_RECEIPT_V1', completed_utc=datetime.now(timezone.utc).isoformat(),
        passed=passed, total_tests=sum(group['tests'] for group in groups), groups=groups,
        source_manifest=manifest, node_coordinator_overlay=overlay, all_python_compiled=True,
        original_owner_and_epoch4_inputs_unchanged=unchanged, source_and_provenance_unchanged_during_tests=unchanged,
        native_actions=[], parent_actions=[], registry_mutations=[], GPU_calls=0, remote_commands=[],
        simulated_actions_only=True, operational_fence_verified=False, operational_rebind_verified=False,
        actual_30_second_all_in_route_proven=False, dispatch_ready=False,
        Main_readonly_observation=reference(main_observation), Main_observation_handoff_eligible=False,
        blockers=['fresh_original_owner_identity_locks_idle_drain_and_2s_authenticated_bridge_measurement',
            'exact_eligible_COMPLETE_plus_LEARN_head_no_pending_REQUEST',
            'original_admission_bound_consumer_context_and_all_reserved_work_cost_receipt',
            'unchanged_r188_inner_100s_admission_limits_no_shared_startup_deadline_ABI',
            'explicit_current_Main_plan_action_approvals_and_execution_digest'])
    result = write_once(output / 'TEST_RECEIPT.json', receipt)
    print(core.encoded(dict(receipt=result, passed=passed, total_tests=receipt['total_tests'],
        source_manifest=manifest, overlay=overlay, dispatch_ready=False)).decode())
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
