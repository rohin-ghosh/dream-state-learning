"""Finite, once-only recovery from preserved completed sleep; never signal a learner."""

import argparse
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
TARGETS = {
    'C0': ('/localhome/local-rohing/orch_r216_C0_20260918_attempt2', 2561156, 98, 2856,
           'e0c3b033023e43c7a3dfa494d68011af'),
    'CAPTION': ('/localhome/local-rohing/orch_r229_unparented_caption_20260918/r213_r226_caption_unparented_fork',
                2884345, 76, 3213, '1840899d7847437093d41eae072b8d26'),
    'ASTRA7': ('/localhome/local-rohing/orch_r229_Astra7_20260918', 2863450, 87, 3068,
               '6a2fa591a1304fd8b3eff24f65e5caff'),
}
LEASE_SOURCE = Path('/localhome/local-rohing/orch_r119_l1_generation_20260915_attempt2/FORKS.json')
LEASE_SHA = '621e1391285bcad9ee075106b4afab28970616b663876dc4ebeba7834e7b81e3'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def environment(source):
    return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
        PYTHONPATH=os.pathsep.join((str(source), str(source / 'tests'), str(source / 'gpu'),
            '/localhome/local-rohing/orch_r229_unparented_caption_20260918/cpu_test_deps')))


def offline_type(plan, physical_stream):
    from gpu.r233_node2_recovery import journal_type

    class OfflineJournal(journal_type(plan)):
        def _reload_state(self, *arguments, **keywords):
            self.inbox = Path(plan['root']) / 'stream/inbox'
            return super()._reload_state(*arguments, **keywords)

        def _inbox_event(self, message, path, source_sha256):
            if plan['physical'] != 1 or message.get('actor') != 'parent':
                return super()._inbox_event(message, path, source_sha256)
            from gpu.r229_p7_inbox import p7_event
            logical = Path(plan['root']) / 'stream'
            require(Path(path).parent == logical / 'inbox', 'original_logical_inbox_path')
            receipt_path = Path(message['source_receipt']['path'])
            require(receipt_path.parent == logical / 'p7_receipts' and '..' not in receipt_path.parts,
                'original_P7_receipt_namespace')
            mapped = deepcopy(message)
            mapped['source_receipt']['path'] = str(physical_stream / 'p7_receipts' / receipt_path.name)
            previous = self.inbox
            try:
                self.inbox = physical_stream / 'inbox'
                event = p7_event(self, mapped, str(self.inbox / Path(path).name), source_sha256)
            finally:
                self.inbox = previous
            return replace(event, source_id=path)

    return OfflineJournal


def locations(name):
    root = Path(TARGETS[name][0])
    return root, root / 'source_r233_recovery', root / 'control_r233_recovery', root / 'r233_preserved'


def absent(name):
    root, _, _, _ = locations(name)
    require(not Path('/proc', str(TARGETS[name][1])).exists(), 'old_exact_native_must_be_absent')
    matches = []
    for process in Path('/proc').glob('[0-9]*'):
        try:
            arguments = (process / 'cmdline').read_bytes().split(b'\0')
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if b'native' in arguments and any(str(root).encode() in argument for argument in arguments):
            matches.append(process.name)
    require(not matches, 'no_current_native_for_exact_physical_root')


def prepare(name):
    absent(name)
    root, source, control, preserved = locations(name)
    require(not control.exists() and not source.exists() and not preserved.exists(), 'new_recovery_attempt_only')
    require(sha(LEASE_SOURCE) == LEASE_SHA, 'original_authoritative_node2_lease_source')
    previous = read(root / 'control/PLAN.json')
    lease = read(root / 'LEASE.json')
    authority = read(LEASE_SOURCE)
    require(previous['lease_end_unix'] == lease['lease_end_unix'] <= authority['lease_end_unix'],
        'conservative_bound_within_original_lease')
    outer_exit = read(root / 'control/OUTER_EXIT.json')
    require(outer_exit['status'] != 0, 'diagnosed_stopped_life_not_live_restart')
    deadline = min(time.time() + 21600, previous['lease_end_unix'] - 1200,
        authority['hard_deadline_unix'])
    require(deadline > time.time() + 1800, 'unexpired_finite_recovery_budget')
    control.mkdir(mode=0o700)
    preserved.mkdir(mode=0o700)
    shutil.copytree(root / 'source', source)
    overlay = read(HERE / 'SOURCE_OVERLAY.public.json')
    for relative, expected in overlay['files'].items():
        incoming = HERE / 'overlay.private' / relative
        require(sha(incoming) == expected, 'published_overlay_bytes')
        (source / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(incoming, source / relative)
    shutil.copy2(HERE / 'runtime.py', source / 'gpu/r233_node2_recovery.py')
    shutil.copy2(HERE / 'test_recovery.py', source / 'tests/test_r233_node2_recovery.py')
    sys.path.insert(0, str(source))
    from gpu.r213_recovery_runtime import RecoveryJournal, saved_state
    from gpu.orch_r125_continual_native import NativeChild, validate_plan
    from organism_v6.orch_r125_continual_stream import verify_experiment_resume
    from organism_v6.orch_r227_learning_policy import POLICY, SEMANTIC_FILTER_FIELDS
    paths = sorted((root / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))
    head = read(paths[-1])
    complete_path = root / 'raw/stream/records' / f'{TARGETS[name][3]:020d}.json'
    complete = read(complete_path)
    require(head['journal_id'] == complete['journal_id'] == TARGETS[name][4], 'same_original_journal_identity')
    require(complete['document']['cycle'] == TARGETS[name][2], 'known_completed_sleep')
    subprocess.run(['cp', '-a', '--reflink=auto', str(root / 'raw/stream'), str(preserved / 'stream')], check=True)
    checkpoint_dir = root / 'raw/checkpoints' / f'sleep_{TARGETS[name][2]:06d}'
    subprocess.run(['cp', '-a', '--reflink=auto', str(checkpoint_dir), str(preserved / checkpoint_dir.name)], check=True)
    manifest = {str(path.relative_to(preserved)): sha(path) for path in preserved.rglob('*') if path.is_file()}
    write(preserved / 'MANIFEST.json', manifest)
    checkpoint = deepcopy(read(checkpoint_dir / 'COMMIT.json'))
    require(checkpoint == complete['document']['checkpoint'], 'completed_record_matches_COMMIT')
    checkpoint['adapter_path'] = str(checkpoint_dir / 'adapter')
    checkpoint['optimizer_rng_path'] = str(checkpoint_dir / 'optimizer_rng.pt')
    NativeChild.verify_checkpoint(checkpoint)
    import torch
    payload = torch.load(checkpoint_dir / 'optimizer_rng.pt', map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == checkpoint['optimizer_steps'] and not torch.cuda.is_initialized(),
        'CPU_optimizer_RNG_restore_without_CUDA')
    require(all(key in payload for key in ('optimizer', 'cpu_rng', 'cuda_rng', 'python_rng')), 'all_saved_RNG_components')
    restored = saved_state(complete, deadline)
    plan = deepcopy(previous)
    plan.update(source_root=str(source), hard_end_unix=deadline)
    for key in ('authorized_wall_extension', 'preupdate_recovery'):
        plan.pop(key, None)
    for scope in (plan, plan['think_act_learn']):
        scope['learn_row_policy'] = POLICY
        for key in SEMANTIC_FILTER_FIELDS:
            scope.pop(key, None)
    if 'startup_context' in plan:
        plan['startup_context']['path'] = str(source / Path(previous['startup_context']['path']).relative_to(root / 'source'))
    verify_experiment_resume(plan, restored['state']['experiment'])
    validate_plan(plan)
    tail = [read(path) for path in paths if int(path.stem) > complete['index']]
    receipt = dict(old_native_absent=True, old_native_pid=TARGETS[name][1], old_outer_exit_status=outer_exit['status'],
        old_outer_exit=outer_exit, exact_resident_continuity_claimed=False, old_head_index=head['index'],
        old_head_sha256=head['sha256'], complete_path=str(complete_path), complete_sha256=complete['sha256'],
        new_deadline_unix=deadline, complete_cycle=complete['document']['cycle'], optimizer_steps=checkpoint['optimizer_steps'],
        checkpoint_sha256=checkpoint['checkpoint_sha256'], saved_state_sha256=complete['document']['resume_state']['sha256'],
        restored_state_sha256=restored['sha256'], journal_id=head['journal_id'],
        preservation_manifest_sha256=sha(preserved / 'MANIFEST.json'), old_plan_sha256=sha(root / 'control/PLAN.json'),
        lost_tail_updates=sum(record['kind'] == 'UPDATE' for record in tail),
        tail_record_count=len(tail), original_tail_records_retained=True, birth_compaction_repeated=False,
        policy_change='Prospective approved R227, both scopes; history unchanged', authorization='R233 explicit kept-life restart after diagnosis')
    write(control / 'RECOVERY.json', receipt)
    write(control / 'PLAN.json', plan)
    lease.update(hard_end_unix=deadline, physical_lease_changed=False, authoritative_source_sha256=LEASE_SHA)
    write(control / 'LEASE.json', lease)

    OfflineJournal = offline_type(plan, preserved / 'stream')
    with OfflineJournal(preserved / 'stream') as journal:
        proof = journal.record('R213_SAVED_BOUNDARY_RECOVERY', dict(receipt_path=str(control / 'RECOVERY.json'),
            receipt_sha256=sha(control / 'RECOVERY.json'), state=restored))
        require(journal.latest_checkpoint()['expected_sha256'] == restored['sha256'], 'actual_archive_recovery_replay')
    write(control / 'ARCHIVE_REPLAY.json', dict(proof=proof, verified=True, original_journal_unchanged=True))
    print(json.dumps(dict(phase='PREPARED_NOT_TESTED', name=name, cycle=receipt['complete_cycle'],
        optimizer_steps=receipt['optimizer_steps'], tail_updates_not_carried=receipt['lost_tail_updates'])), flush=True)


def check(name):
    root, source, control, _ = locations(name)
    tests = ['test_r233_node2_recovery', 'test_orch_r227_learning_policy',
        'test_orch_r125_continual_native', 'test_orch_r184_think_act_learn']
    with (control / 'CPU.log').open('x') as output:
        result = subprocess.run([PYTHON, '-B', '-m', 'unittest', '-q', *tests], cwd=source,
            env=environment(source), stdout=output, stderr=subprocess.STDOUT, timeout=240)
    require(result.returncode == 0, 'receiving_CPU_tests_see_CPU_log')
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    write(control / 'RECEIVING_CPU.json', dict(passed=True, source_pins=pins, tests=tests,
        log_sha256=sha(control / 'CPU.log'), model_calls=0, observed_unix=time.time(),
        archive_replay_sha256=sha(control / 'ARCHIVE_REPLAY.json')))
    print(json.dumps(dict(name=name, status='CPU_PASS_NOT_LAUNCHED', cpu_sha256=sha(control / 'RECEIVING_CPU.json'))))


def publish(name, commit):
    root, source, control, _ = locations(name)
    require(commit and len(commit) == 40 and all(character in '0123456789abcdef' for character in commit), 'actual_pushed_builder_commit')
    cpu = read(control / 'RECEIVING_CPU.json')
    require(cpu['passed'], 'CPU_pass_required')
    plan = read(control / 'PLAN.json')
    write(control / 'ALLOCATION.json', dict(plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        gpu_uuid=plan['gpu_uuid'], physical=plan['physical'], builder_entry_logged=True, builder_entry_pushed=True,
        builder_entry_commit=commit, cpu_receipt_path=str(control / 'RECEIVING_CPU.json'),
        cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'), declared_unix=time.time()))
    old_guard = root / 'control/GUARD_PUBLISHED.json'
    if not old_guard.exists():
        old_guard = root / 'control/GUARD.json'
    guard = read(old_guard)
    guard.update(source_pins=cpu['source_pins'], resume=True, copy_raw=str(root / 'raw'), attempt_dir=str(control),
        plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'), hard_end_unix=plan['hard_end_unix'],
        lease_path=str(control / 'LEASE.json'), lease_sha256=sha(control / 'LEASE.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'))
    write(control / 'GUARD.json', guard)
    subprocess.run([PYTHON, '-B', '-c', 'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
        str(control / 'GUARD.json')], cwd=source, env=environment(source), check=True)
    write(control / 'READY.json', dict(status='CPU_AND_ACTUAL_ARCHIVE_REPLAY_PASS_NOT_LAUNCHED', builder_commit=commit))


def reconcile(name):
    absent(name)
    root, source, control, preserved = locations(name)
    require((control / 'READY.json').is_file() and not (control / 'RECOVERY_APPENDED.json').exists(), 'new_once_only_dispatch')
    sys.path.insert(0, str(source))
    from gpu.r213_recovery_runtime import RecoveryJournal, saved_state
    receipt, plan = read(control / 'RECOVERY.json'), read(control / 'PLAN.json')
    moved = []
    for category in ('checkpoints', 'readouts'):
        for path in sorted((root / 'raw' / category).glob('sleep_*')):
            if int(path.name.split('_')[1]) > receipt['complete_cycle']:
                destination = preserved / 'tail_artifacts' / category / path.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                path.rename(destination)
                moved.append(dict(original=str(path), preserved=str(destination)))
    write(control / 'TAIL_ARTIFACTS_PRESERVED.json', dict(moved=moved, deleted=False))

    OfflineJournal = offline_type(plan, root / 'raw/stream')
    with OfflineJournal(root / 'raw/stream') as journal:
        proof = journal.record('R213_SAVED_BOUNDARY_RECOVERY', dict(receipt_path=str(control / 'RECOVERY.json'),
            receipt_sha256=sha(control / 'RECOVERY.json'),
            state=saved_state(read(receipt['complete_path']), receipt['new_deadline_unix'])))
    write(control / 'RECOVERY_APPENDED.json', proof)


def launch(name):
    absent(name)
    root, source, control, _ = locations(name)
    require(not (control / 'DISPATCHED.json').exists(), 'no_duplicate_dispatch_or_automatic_retry')
    if not (control / 'RECOVERY_APPENDED.json').exists():
        reconcile(name)
    proof = read(control / 'RECOVERY_APPENDED.json')
    paths = sorted((root / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))
    head = read(paths[-1])
    require(head['index'] == proof['index'] and head['sha256'] == proof['sha256']
        and head['kind'] == 'R213_SAVED_BOUNDARY_RECOVERY', 'unchanged_reconciled_head_before_dispatch')
    write(control / 'DISPATCHED.json', dict(observed_unix=time.time(), pid=os.getpid(), status='DISPATCHED_NOT_LOADED'))
    os.chdir(source)
    os.execve(PYTHON, [PYTHON, '-B', '-m', 'gpu.r233_node2_recovery', 'dispatch',
        '--config', str(control / 'GUARD.json')], environment(source))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'check', 'publish', 'reconcile', 'launch'))
    parser.add_argument('name', choices=tuple(TARGETS))
    parser.add_argument('--commit')
    arguments = parser.parse_args()
    if arguments.mode == 'publish':
        publish(arguments.name, arguments.commit)
    else:
        globals()[arguments.mode](arguments.name)
