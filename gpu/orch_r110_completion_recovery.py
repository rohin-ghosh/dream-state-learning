"""Continue after a completion-metadata failure without repeating science calls."""

import argparse
import json
import os
from pathlib import Path

from gpu import orch_r110_guided_run as run
from gpu import orch_r110_guided_supervisor as supervisor


def recovery_evidence(root):
    run.validate(root)
    run.policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only_recovery')
    failure_path = root / 'cycle1/sleep/FAILED.json'
    failure = run.read(failure_path)
    run.policy.require(failure['status'] == 'FAILED' and failure['phase'] == 'sleep'
        and failure['cycle'] == 1 and failure['error_type'] == 'TypeError'
        and failure['error'] == "dict() got multiple values for keyword argument 'started_unix'",
        'exact_metadata_only_failure')
    request = run.read(root / 'cycle1/sleep/REQUEST.json')
    boot, pid, start = request['process']
    stat_path = Path('/proc') / str(pid) / 'stat'
    if stat_path.exists():
        fields = stat_path.read_text().rsplit(')', 1)[1].split()
        run.policy.require(fields[0] == 'Z' or int(fields[19]) != start
            or Path('/proc/sys/kernel/random/boot_id').read_text().strip() != boot,
            'old_native_still_alive')
    sleep = run.read(root / 'cycle1/sleep/SLEEP.json')
    initial = run.read(root / 'INITIAL.json')
    carry = run.read(root / 'cycle1/sleep/carry/CARRY.json')
    run.seed.validate(carry)
    run.policy.require(carry['generation'] == 1
        and carry['parent_binding_sha256'] == initial['binding_sha256']
        and carry['optimizer_summary']['step'] == initial['optimizer_summary']['step'] + sleep['optimizer_updates'],
        'all_updates_saved_without_reset')
    updates = sorted((root / 'cycle1/sleep/UPDATES').glob('*.json'))
    run.policy.require(len(updates) == sleep['optimizer_updates'] > 0
        and [run.read(path)['update'] for path in updates] == list(range(1, len(updates) + 1)),
        'continuous_update_receipts')
    reservations = [json.loads(line) for line in (root / 'RESERVATIONS.jsonl').read_text().splitlines() if line.strip()]
    run.policy.require(sum(item['kind'] == 'NATIVE' for item in reservations) == 8
        and sum(item['kind'] == 'PARENT' for item in reservations) == 3
        and not (root / 'cycle1/readout').exists() and not (root / 'LAUNCH_1_readout.json').exists(),
        'no_repeated_calls_or_readout')
    run.policy.require(run.read(root / 'cycle1/collection/COMPLETE.json')['status'] == 'COMPLETE'
        and not (root / 'cycle1/sleep/COMPLETE.json').exists(), 'original_evidence_preserved')
    names = ('READY.json', 'PLAN.json', 'INITIAL.json', 'RESERVATIONS.jsonl',
        'cycle1/collection/COMPLETE.json', 'cycle1/sleep/REQUEST.json', 'cycle1/sleep/SLEEP.json',
        'cycle1/sleep/FAILED.json', 'cycle1/sleep/carry/CARRY.json')
    return dict(schema='R110_METADATA_RECOVERY_READY_V2', input_sha256={name: run.sha(root / name) for name in names},
        repair_sha256=run.sha(run.SOURCE_ROOT / 'REPAIR.json'), preserved_updates=len(updates),
        optimizer_step=carry['optimizer_summary']['step'], adapter_sha256=carry['adapter']['state_sha256'],
        next_phase='cycle1/readout', repeated_native_calls=0, repeated_parent_calls=0, repeated_training_updates=0,
        original_deadlines_unchanged=True)


def prepare(root):
    evidence = recovery_evidence(root)
    directory = root / 'recovery_v2'
    directory.mkdir(exist_ok=False)
    run.write(directory / 'PREPARE.json', evidence)
    return evidence


def resume(root):
    expected = run.read(root / 'recovery_v2/PREPARE.json')
    run.policy.require(recovery_evidence(root) == expected, 'recovery_inputs_changed')
    publication = root / 'recovery_v2/PUBLICATION.json'
    run.policy.require(publication.is_file(), 'recovery_publication_required')
    terminal = root / 'TERMINAL.json'
    run.policy.require(run.read(terminal)['status'] == 'FAILED', 'original_terminal_preserved')
    destination = root / 'recovery_v2/ORIGINAL_TERMINAL.json'
    run.policy.require(not destination.exists(), 'no_terminal_overwrite')
    terminal.rename(destination)
    run.write(root / 'RECOVERY_V2_READY.json', dict(expected,
        original_terminal_sha256=run.sha(destination), publication_sha256=run.sha(publication)))
    supervisor.supervise(root, recovery=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'resume'))
    args = parser.parse_args()
    if args.mode == 'prepare':
        print(json.dumps(prepare(run.ROOT)))
    else:
        resume(run.ROOT)
