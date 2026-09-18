"""Continue the declared three-source block; observe live jobs without restarting."""

import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

from epoch import DEADLINE, sha


ROOT = Path('/localhome/local-rohing/orch_post_recovery_age_20260918_attempt3')
ARMS = ('base', 'learner24', 'frozen24')


def complete_source(complete, loaded):
    if (complete.get('actual_generated_tokens') != 6144 or len(complete.get('cells', [])) != 6
            or any(cell.get('generated_tokens') != 1024 for cell in complete['cells'])
            or complete.get('judge_epoch_sha256') != loaded.get('judge_epoch_sha256')
            or complete.get('source_age') != loaded.get('source_age')
            or complete.get('parent_tokens') != 0 or complete.get('training_updates') != 0
            or complete.get('unchanged_identity', {}).get('all_parameters_frozen') is not True
            or any(complete['unchanged_identity'].get(name) != loaded.get('identity', {}).get(name)
                for name in ('base_sha256', 'adapter_state_sha256'))):
        raise ValueError('actual_equal_budget_frozen_source_completion')
    return True


def write(path, value):
    temporary = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2))
    temporary.replace(path)


def unit_state(unit):
    result = subprocess.run(['systemctl', 'show', unit, '-p', 'ActiveState', '-p', 'SubState',
        '-p', 'MainPID', '-p', 'ExecMainStatus'], text=True, capture_output=True, timeout=10)
    if result.returncode:
        raise RuntimeError('unit_observation_failed_not_proof_of_termination')
    return dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)


def main():
    os.umask(0o077)
    lock = (ROOT / 'BATCH.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    configs = {arm: sha(ROOT / arm / 'CONFIG.json') for arm in ARMS}
    write(ROOT / 'BATCH_STARTED.json', dict(pid=os.getpid(), unix=time.time(), arms=list(ARMS),
        config_sha256=configs, deadline_unix=DEADLINE, no_native_signals=True,
        scope='THREE_PREDECLARED_SOURCES_NOT_ALL_BACKLOG'))
    completed = []
    while time.time() < DEADLINE:
        try:
            for arm in ARMS:
                root = ROOT / arm
                if sha(root / 'CONFIG.json') != configs[arm]:
                    raise ValueError('pinned_batch_configuration')
                config = json.loads((root / 'CONFIG.json').read_bytes())
                output = root / 'players' / config['identity']['condition']
                complete_path = output / 'COMPLETE.json'
                failed = [mode for mode in ('player', 'judge') if (root / (mode + '_FAILED.json')).exists()]
                if failed:
                    write(ROOT / 'BATCH_STATUS.json', dict(unix=time.time(), pid=os.getpid(),
                        status='EXPLICIT_PROBE_FAILURE_PRESERVED_NO_AUTOMATIC_RESTART', arm=arm,
                        failed=failed, completed=completed, remaining=list(ARMS[len(completed):])))
                    return
                if complete_path.exists():
                    complete = json.loads(complete_path.read_bytes())
                    loaded = json.loads((output / 'LOADED.json').read_bytes())
                    complete_source(complete, loaded)
                    if arm not in completed:
                        completed.append(arm)
                    continue
                states = {}
                for mode in ('judge', 'player'):
                    dispatched = root / (mode + '_DISPATCHED.json')
                    if not dispatched.exists():
                        result = subprocess.run(['/localhome/local-rohing/v2/venv/bin/python', '-B',
                            str(ROOT / 'tools/dispatch.py'), '--root', str(root), '--mode', mode],
                            text=True, capture_output=True, timeout=45)
                        if result.returncode:
                            raise RuntimeError('dispatch_not_completed_or_device_busy')
                    receipt = json.loads(dispatched.read_bytes())
                    states[mode] = unit_state(receipt['unit'])
                    if states[mode]['ActiveState'] in ('failed', 'inactive') and not complete_path.exists():
                        write(ROOT / 'BATCH_STATUS.json', dict(unix=time.time(), pid=os.getpid(),
                            status='TERMINAL_WITHOUT_COMPLETE_PRESERVED', arm=arm, mode=mode,
                            actual_unit_state=states[mode], completed=completed))
                        return
                loaded_path = output / 'LOADED.json'
                write(ROOT / 'BATCH_STATUS.json', dict(unix=time.time(), pid=os.getpid(),
                    status='ACTUAL_EVALUATION_RUNNING' if loaded_path.exists() else 'DISPATCHED_LOAD_PENDING',
                    arm=arm, states=states, completed=completed, remaining=list(ARMS[len(completed):]),
                    no_native_signals=True))
                break
            if len(completed) == len(ARMS):
                write(ROOT / 'BATCH_STATUS.json', dict(unix=time.time(), pid=os.getpid(),
                    status='THREE_SOURCE_BLOCK_COMPLETE', completed=completed,
                    every_sleep_backlog_complete=False, no_native_signals=True))
                return
        except Exception as error:
            write(ROOT / 'BATCH_OBSERVATION_ERROR.json', dict(unix=time.time(), pid=os.getpid(),
                error_type=type(error).__name__, error=str(error), completed=completed,
                action='REOBSERVE_SAME_HANDLES_NO_RESTART'))
        time.sleep(min(15, max(0, DEADLINE - time.time())))


if __name__ == '__main__':
    main()
