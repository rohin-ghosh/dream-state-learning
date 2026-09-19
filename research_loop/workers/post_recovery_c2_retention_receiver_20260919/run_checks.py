"""Run CPU-only checks and publish hash-bound artifacts in this worker directory."""

from datetime import datetime, timezone
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[2]
WORKERS = OWN.parent
BOUNDARY = WORKERS / 'post_recovery_retention_boundary_20260918'
SOURCE = WORKERS / 'rohin233_recovery_node4_20260918/private/port_C2'
sys.path.insert(0, str(REPO))

from research_loop.workers.post_recovery_c2_retention_receiver_20260919.ports import proposed_ports, changes_for


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def publish(path, content):
    path = Path(path)
    content = content if isinstance(content, str) else json.dumps(content, sort_keys=True, indent=2, allow_nan=False) + '\n'
    if not path.is_relative_to(OWN):
        raise ValueError('worker_only_generated_artifacts')
    previous = path.read_text() if path.exists() else None
    if previous == content:
        return
    if previous is None:
        patch = '*** Begin Patch\n*** Add File: ' + str(path) + '\n'
    else:
        patch = '*** Begin Patch\n*** Update File: ' + str(path) + '\n@@\n'
        patch += ''.join('-' + line + '\n' for line in previous.splitlines())
    patch += ''.join('+' + line + '\n' for line in content.splitlines()) + '*** End Patch\n'
    subprocess.run(['apply_patch'], input=patch, text=True, capture_output=True, check=True, cwd=REPO)


def main():
    stage_path = WORKERS / 'post_recovery_retention_rollout_20260919/C2_STAGED.json'
    stage = json.loads(stage_path.read_bytes())
    dependency_paths = [stage_path,
        WORKERS / 'post_recovery_retention_rollout_20260919/node5_INVENTORY2.json',
        WORKERS / 'post_recovery_c2_age_eval_20260918/REPORT_VALIDATION.json']
    dependency_paths += sorted(BOUNDARY.glob('*.py'))
    for variant in ('C0', 'Astra7', 'P7', 'P3', 'C2'):
        port = WORKERS / 'post_recovery_retention_ports_20260919' / variant
        dependency_paths += [port / name for name in ('READY.json', 'TEST_RECEIPT.json',
            'SOURCE_PINS.before.json', 'SOURCE_PINS.after.json')]
    dependency_paths += [SOURCE / name for name in ('gpu/orch_r125_stream_journal.py',
        'gpu/checkpoint_tail_runtime.py', 'gpu/orch_r125_continual_native.py',
        'tests/test_orch_r125_stream_journal.py', 'organism_v6/orch_r124_train_history.py',
        'organism_v6/orch_r125_continual_stream.py', 'organism_v6/orch_r125_plain_context.py')]
    dependency_paths.append(WORKERS / 'post_recovery_matched_cohort_runtime_20260918/receiving/source/gpu/r188_node5_confinement.py')
    inputs = {str(path.relative_to(REPO)): sha(path) for path in dependency_paths}
    for name in ('gpu/orch_r125_stream_journal.py', 'gpu/checkpoint_tail_runtime.py', 'gpu/orch_r125_continual_native.py'):
        if sha(SOURCE / name) != stage['new_source_pins'][name]:
            raise ValueError('exact_C2_reader_native_fixture_source_required:' + name)
    outputs = proposed_ports(SOURCE)
    extra_changes = changes_for(SOURCE)
    receiving_pins = dict(stage['new_source_pins'])
    patch_parts = []
    for name, data in outputs.items():
        publish(OWN / 'overlay' / name, data.decode())
        receiving_pins[name] = hashlib.sha256(data).hexdigest()
        original = (SOURCE / name).read_text() if (SOURCE / name).exists() else ''
        patch_parts.extend(difflib.unified_diff(original.splitlines(keepends=True), data.decode().splitlines(keepends=True),
            fromfile='a/' + name if original else '/dev/null', tofile='b/' + name))
    publish(OWN / 'ADOPTION.patch', ''.join(patch_parts))
    publish(OWN / 'SOURCE_PINS.epoch1.json', stage['new_source_pins'])
    publish(OWN / 'SOURCE_PINS.receiving.json', receiving_pins)
    complete_delta = {name: dict(before=stage['old_source_pins'].get(name), after=value)
        for name, value in receiving_pins.items() if stage['old_source_pins'].get(name) != value}
    publish(OWN / 'C2_ADOPTION_PORT.json', dict(schema='C2_RETENTION_ADOPTION_PORT_V1',
        original_stage_path=str(stage_path.relative_to(REPO)), original_stage_sha256=sha(stage_path),
        original_stage_status=stage['status'], live_native=stage['native'],
        old_source=stage['old_source'], epoch1_source=stage['new_source'],
        new_receiving_source='MAIN_MUST_SELECT_A_NEW_IMMUTABLE_ROOT_NOT_EPOCH1',
        extra_source_changes=extra_changes, complete_old_live_to_receiver_delta=complete_delta,
        overlay_paths={name: str((OWN / 'overlay' / name).relative_to(REPO)) for name in outputs},
        existing_stage_modified=False, applied_to_live=False, same_r188_confinement=True,
        same_checkpoint_tail_reader=True, hard_end_unix=1789927200,
        parent_rebind_allowed=False, dispatchable=False))
    patch_checks = []
    for directory, reverse in ((SOURCE, False), (OWN / 'overlay', True)):
        command = ['git', 'apply', '--check', '--directory=' + str(directory.relative_to(REPO))]
        if reverse:
            command.append('--reverse')
        command.append(str(OWN / 'ADOPTION.patch'))
        result = subprocess.run(command, cwd=REPO, text=True, capture_output=True, timeout=30)
        patch_checks.append(dict(command=command, passed=result.returncode == 0,
            returncode=result.returncode, stdout=result.stdout, stderr=result.stderr))
    groups = [
        ('HOOK_TESTS', REPO, ['-m', 'unittest',
            'research_loop.workers.post_recovery_c2_retention_receiver_20260919.test_receiver.ReceivingTests', '-v']),
        ('CPU_PROBE_TESTS', REPO, ['-m', 'unittest',
            'research_loop.workers.post_recovery_c2_retention_receiver_20260919.test_cpu_probe', '-v']),
        ('RUNTIME_TESTS', REPO, ['-m', 'unittest',
            'research_loop.workers.post_recovery_c2_retention_receiver_20260919.test_runtime.RuntimeTests', '-v']),
        ('BOUNDARY_TESTS', BOUNDARY, ['-m', 'unittest', 'discover', '-p', 'test_*.py', '-v']),
    ]
    checks = {}
    for name, cwd, arguments in groups:
        command = [sys.executable, '-B', *arguments]
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=60)
        content = result.stdout + result.stderr
        publish(OWN / (name + '.log'), content)
        match = re.search(r'Ran (\d+) tests? in ', content)
        checks[name] = dict(command=command, cwd=str(cwd.relative_to(REPO)) or '.',
            passed=result.returncode == 0 and match is not None,
            returncode=result.returncode, tests=int(match.group(1)) if match else None,
            log_sha256=sha(OWN / (name + '.log')))
        print(name, 'PASS' if checks[name]['passed'] else 'FAIL', checks[name]['tests'], flush=True)
    unchanged = all(sha(REPO / name) == expected for name, expected in inputs.items())
    passed = all(check['passed'] for check in checks.values()) and all(check['passed'] for check in patch_checks) and unchanged
    code_paths = sorted(OWN.glob('*.py')) + sorted((OWN / 'overlay').rglob('*.py'))
    code_pins = {str(path.relative_to(OWN)): sha(path) for path in code_paths}
    artifacts = {str(path.relative_to(OWN)): sha(path) for path in OWN.iterdir()
        if path.is_file() and path.name not in ('READY.json', 'TEST_RECEIPT.json')}
    receipt = dict(schema='C2_RETENTION_RECEIVER_CPU_TESTS_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        passed=passed, scope='SYNTHETIC_HOOK_RUNTIME_AND_PINNED_READER_CPU_ONLY', tests=checks,
        total_tests=sum(check['tests'] or 0 for check in checks.values()),
        nonmutating_patch_checks=patch_checks,
        own_tests=sum(check['tests'] or 0 for name, check in checks.items() if name != 'BOUNDARY_TESTS'),
        input_sha256=inputs, input_bytes_unchanged=unchanged, code_sha256=code_pins, artifact_sha256=artifacts,
        torch_available=importlib.util.find_spec('torch') is not None,
        real_checkpoint_payload_tested=False, real_guard_validated=False, actual_node_preflight=False,
        remote_commands=[], live_source_changes=[], live_signals=[], live_dispatches=[],
        service_manager_invocations=[], parent_deliveries=[], commits=[],
        synthetic_dispatch_callbacks_only=True, no_live_adoption_claim=True)
    publish(OWN / 'TEST_RECEIPT.json', receipt)
    publish(OWN / 'READY.json', dict(schema='C2_RETENTION_RECEIVER_READY_V1',
        status='CPU_READY_MAIN_INTEGRATION_REQUIRED' if passed else 'CPU_TESTS_FAILED', cpu_ready=passed,
        dispatchable=False, ready_receiving_source=False, original_stage_still_epoch1=True,
        test_receipt_sha256=sha(OWN / 'TEST_RECEIPT.json'), test_count=receipt['total_tests'],
        own_test_count=receipt['own_tests'], original_stage_sha256=sha(stage_path),
        adoption_port_sha256=sha(OWN / 'C2_ADOPTION_PORT.json'),
        receiving_source_pins_sha256=sha(OWN / 'SOURCE_PINS.receiving.json'),
        patch_sha256=sha(OWN / 'ADOPTION.patch'), hard_end_unix=1789927200,
        original_r188_preserved=True, original_root_journal_preserved=True,
        blockers=['Main_new_immutable_five_delta_receiving_closure_and_exact_authority',
            'exact_historical_WALL_EXTENDED_record_and_intent',
            'fresh_same_COMPLETE_LEARN_checkpoint_and_actual_receiving_CPU_guard_tests',
            'Main_r188_dispatch_bridge_parent_ledger_and_uid_access_preflight',
            'receiving_builder_entry_allocation_fresh_privileged_admission',
            'real_prefix_latency_gate_and_explicit_post_LOADED_owner_rebind'],
        live_signals=[], live_dispatches=[], live_source_changes=[]))
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
