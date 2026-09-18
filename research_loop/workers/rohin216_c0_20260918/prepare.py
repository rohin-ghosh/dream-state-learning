"""Assemble, test and launch one new snapshot51 C0 on reserved node2 GPU4."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write(path, value):
    path.parent.mkdir(exist_ok=True, parents=True)
    if path.exists():
        require(read(path) == value, 'existing_receipt_must_match:' + str(path))
        return
    with path.open('x') as output:
        json.dump(value, output, indent=2, sort_keys=True)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def prepare(args):
    root, snapshot = args.root.resolve(), args.snapshot.resolve()
    source = root / 'source'
    require(root.name in ('orch_r216_C0_20260918', 'orch_r216_C0_20260918_attempt2')
        and not (root / 'READY.json').exists(), 'new_C0_once_only')
    require(sha(snapshot / 'MANIFEST.json') == '29ca04c2c51671c7df922a4b05448586e74eec35da45b03009877baccbccce84', 'exact_requested_snapshot')
    manifest = read(snapshot / 'MANIFEST.json')
    for entry in manifest['files']:
        relative = entry['relative']
        require(sha(snapshot / relative) == entry['sha256'], 'snapshot_file_hash:' + relative)
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r184_think_act_learn import ARTIFACT_ELICITATION_POLICY
    from gpu.r205_runtime import ControlJournal
    from organism_v6.orch_r194_code_target_filter import POLICY as CODE, REVIEW_POLICY
    from organism_v6.orch_r203_prose_target_filter import POLICY as PROSE
    from organism_v6.orch_r213_content_target_filter import POLICY as CONTENT
    ready = read(args.ready)
    plan = deepcopy(read(snapshot / 'source_binding/PLAN.json'))
    lease = read(args.lease)
    deadline = min(time.time() + 21600, lease['lease_end_unix'] - 600)
    require(deadline > time.time() + 3600, 'existing_lease_has_safe_runway')
    plan.update(source_root=str(source), physical=4, gpu_uuid='GPU-d304a15c-516a-16a0-a926-a560304077cc',
        hard_end_unix=deadline, lease_end_unix=lease['lease_end_unix'], max_sleeps=None,
        code_target_filter=CODE, learn_review_filter=REVIEW_POLICY, new_presentations=16, rehearsal_presentations=0)
    for key in ('authorized_wall_extension', 'preupdate_recovery', 'plasticity'):
        plan.pop(key, None)
    gate = root / 'NO_EXECUTOR.json'
    write(gate, dict(executed=False, environment='C0_prose_math_games', no_tool_receipts_invented=True))
    facts = ('You are C0, a new snapshot51 fork, not original C2. Your current object is new math games '
        'with Astra. Move on from the old V coefficient. Show calculations and arguments in prose; '
        'no Python, repository, network or GPU tool is connected. Parent words and historical '
        'transcript are masked context, not your own training targets. No claim is verified merely '
        'because you said it. After two unsuccessful attempts change the approach or the problem.')
    plan['think_act_learn'] = dict(ready['required_driver_options'], trial_id='R216_C0_SNAPSHOT51_MATH',
        cpu_gate_root=str(root), cpu_gate_sha256=sha(gate), environment_facts=facts, think_segments=3,
        prose_target_filter=PROSE, content_target_filter=CONTENT,
        artifact_elicitation_policy=ARTIFACT_ELICITATION_POLICY)
    startup = source / 'context/R216_STARTUP.md'
    startup.parent.mkdir(exist_ok=True)
    startup.write_text(plan['birth_prompt'])
    plan['startup_context'] = dict(version='R127_STARTUP_V1', path=str(startup), sha256=sha(startup))
    native.validate_plan(plan)
    require(Path(plan['model_dir']).is_dir() and Path(plan['anchors']).is_dir(), 'base_and_anchors_exist')
    control = root / 'control'
    write(control / 'PLAN.json', plan)
    shutil.copytree(snapshot / 'complete', root / 'raw/checkpoints/sleep_000051')
    state = deepcopy(read(snapshot / 'console/CONTEXT_COMMITTED.json')['document']['state'])
    state['state']['deadline_unix'] = deadline
    state['sha256'] = native.digest(state['state'])
    with ControlJournal(root / 'raw/stream', create=True) as journal:
        journal.record('R205_FIXED_C2_FORK', dict(manifest_path=str(snapshot / 'MANIFEST.json'),
            source_context_path=str(snapshot / 'console/CONTEXT_COMMITTED.json'),
            hard_end_unix=deadline, state=state))
        require(journal.latest_checkpoint()['expected_sha256'] == state['sha256'], 'exact_source_state_restore')
    import torch
    payload = torch.load(snapshot / 'complete/optimizer_rng.pt', map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == 4908 and not torch.cuda.is_initialized(), 'optimizer4908_cpu_restore')
    write(root / 'LINEAGE.json', dict(name='C0', new_life=True, original_C2_modified=False,
        snapshot='C2_SNAPSHOT_20260918T021847Z', source_checkpoint=51, source_context_record=5846,
        source_optimizer_steps=4908, expected_adapter_state_sha256='82a988a0ded69ce85723192b366251d21f8ec5fe8466e9ca98202fb09b57ce92',
        snapshot_manifest_sha256=sha(snapshot / 'MANIFEST.json'), source_working_state_verbatim=True,
        transcript_sha256=sha(source / 'context/ROHIN_C2_TRANSCRIPT.md'), physical=4,
        zero_eligible_rows='zero_dose_no_optimizer_or_anchor_update'))
    write(root / 'LEASE.json', dict(lease_end_unix=lease['lease_end_unix'], hard_end_unix=deadline,
        source_sha256=sha(args.lease), machine_lease_changed=False))
    check(args)


def check(args):
    root = args.root.resolve()
    source, control = root / 'source', root / 'control'
    sys.path.insert(0, str(source))
    plan = read(control / 'PLAN.json')
    lease, deadline = read(root / 'LEASE.json'), plan['hard_end_unix']
    tests = ['tests/test_orch_r213_content_target_filter.py', 'tests/test_orch_r203_prose_target_filter.py',
        'tests/test_orch_r194_code_target_filter.py', 'tests/test_orch_r195_learn_review_filter.py',
        'tests/test_orch_r184_think_act_learn.py', 'tests/test_r216_c0.py']
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONPATH=os.pathsep.join(
            (str(source), str(source / 'tests'), str(root / 'test_support'))))
    with (root / 'CPU.log').open('x') as output:
        result = subprocess.run([sys.executable, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *tests],
            cwd=source, env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=150)
    require(result.returncode == 0, 'receiving_cpu_tests_see_log')
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    cpu = dict(passed=True, source_pins=pins, tests=tests, log_sha256=sha(root / 'CPU.log'),
        observed_utc=datetime.now(timezone.utc).isoformat(), cuda_initialized=False)
    write(root / 'CPU.json', cpu)
    write(control / 'RECEIVING_CPU.json', cpu)
    write(control / 'ALLOCATION.json', dict(plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        gpu_uuid=plan['gpu_uuid'], physical=4, builder_entry_logged=True,
        cpu_receipt_path=str(root / 'CPU.json'), cpu_receipt_sha256=sha(root / 'CPU.json'), declared_unix=time.time()))
    config = dict(schema='R125_CONTINUAL_GUARD_V1', source_pins=pins, resume=True,
        copy_raw=str(root / 'raw'), plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        attempt_dir=str(control), host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),
        hard_end_unix=deadline, lease_path=str(root / 'LEASE.json'), lease_sha256=sha(root / 'LEASE.json'),
        next_reserved_unix=lease['lease_end_unix'], allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=sha(control / 'ALLOCATION.json'))
    write(control / 'GUARD.json', config)
    write(root / 'CPU_READY.json', dict(status='CPU_PASS_WAITING_PUBLICATION', cpu_sha256=sha(root / 'CPU.json')))


def publish(args):
    root = args.root.resolve()
    sys.path.insert(0, str(root / 'source'))
    require(args.commit is not None and len(args.commit) == 40
        and all(character in '0123456789abcdef' for character in args.commit), 'actual_published_commit_required')
    control = root / 'control'
    allocation = read(control / 'ALLOCATION.json')
    require(sha(root / 'CPU.json') == allocation['cpu_receipt_sha256'], 'same_tested_receipt')
    allocation.update(builder_entry_pushed=True, builder_entry_commit=args.commit)
    write(control / 'ALLOCATION_PUBLISHED.json', allocation)
    config = read(control / 'GUARD.json')
    config.update(allocation_path=str(control / 'ALLOCATION_PUBLISHED.json'),
        allocation_sha256=sha(control / 'ALLOCATION_PUBLISHED.json'))
    write(control / 'GUARD_PUBLISHED.json', config)
    from gpu.orch_r125_continual_guard import validate
    validate(control / 'GUARD_PUBLISHED.json')
    write(root / 'READY.json', dict(status='CPU_PASS_NOT_LAUNCHED', cpu_sha256=sha(root / 'CPU.json'),
        prelaunch_commit=args.commit))


def launch(args):
    root = args.root.resolve()
    require(read(root / 'READY.json')['status'] == 'CPU_PASS_NOT_LAUNCHED'
        and not (root / 'DISPATCHED.json').exists(), 'tested_once_only_dispatch')
    source = root / 'source'
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(source))
    processes = {}
    for label, command in (
        ('parent', [sys.executable, '-B', str(root / 'parent.py'), '--root', str(root)]),
        ('supervisor', [sys.executable, '-B', '-m', 'gpu.r216_c0_runtime', 'dispatch', '--config', str(root / 'control/GUARD_PUBLISHED.json')])):
        with (root / (label + '.log')).open('x') as output:
            process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        processes[label] = process.pid
    write(root / 'DISPATCHED.json', dict(status='STARTED_NOT_LOADED_PROOF', processes=processes, observed_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'check', 'publish', 'launch'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--ready', type=Path)
    parser.add_argument('--lease', type=Path)
    parser.add_argument('--commit')
    arguments = parser.parse_args()
    globals()[arguments.mode](arguments)
