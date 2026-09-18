"""Replace only idle owned R181 waiters; never signal a learner directly."""

import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time


OLD = Path('/localhome/local-rohing/orch_r179_node4_r181_20260917t2150z')
NEW = Path('/localhome/local-rohing/orch_r179_node4_r181journal_20260917t2220z')
WAITERS = {3: 1189573, 4: 1174519}
CONSUMED = ('RETIREMENT_STARTED.json', 'RETIRED.json', 'DISPATCHED.json', 'LOADED_RECEIPT.json', 'HANDOFF_COMPLETE.json')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def check_owner(physical, helpers):
    code = ('import sys; from pathlib import Path; import node4_rollout as operator; '
        'bundle=Path.cwd(); helpers=operator.helper_module(bundle); physical=int(sys.argv[1]); '
        'stage=helpers.read(bundle / ("lane" + str(physical)) / "STAGED.json"); '
        'operator.require(operator.selected(physical, helpers)[-1] == stage["processes"], "same_actual_owner")')
    result = subprocess.run([str(helpers.PYTHON), '-B', '-c', code, str(physical)], cwd=NEW,
        env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(NEW), PYTHONDONTWRITEBYTECODE='1'),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30, check=False)
    require(result.returncode == 0, 'isolated_exact_owner_validation:' + result.stderr[-2000:])


def main():
    require(os.getuid() == 2524, 'exact_NODE4_owner')
    spec = importlib.util.spec_from_file_location('existing_node4_operator', NEW / 'node4_rollout.py')
    operator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(operator)
    helpers = operator.helper_module(NEW)
    helpers.current_node('a40r')
    require(helpers.sha(NEW / 'node4_rollout.py') == '3bebf07c0eb71b8dfaef71511cc01662973da335a8e781bdc1034cb6742a3874',
        'exact_existing_custody_operator')
    for physical in (0, 1, 3, 4):
        stage = helpers.read(NEW / f'lane{physical}/STAGED.json')
        require(stage['status'] == 'STAGED_CPU_AND_GUARD_VALIDATED', 'all_receiving_tests_complete')
        require(not any((NEW / f'lane{physical}' / name).exists() for name in CONSUMED), 'no_new_consumed_handoff')
        require(not any((OLD / f'lane{physical}' / name).exists() for name in CONSUMED), 'no_old_consumed_handoff')
        check_owner(physical, helpers)
    records = []
    for physical, pid in WAITERS.items():
        actor = helpers.identity(pid)
        expected = [str(helpers.PYTHON), '-B', 'node4_rollout.py', 'handoff', '--bundle', str(OLD),
            '--physical', str(physical), '--wait-seconds', '5400']
        require(actor['uid'] == os.getuid() and actor['argv'] == expected and actor['cwd'] == str(OLD),
            'exact_superseded_waiter_not_native')
        descriptor = os.pidfd_open(pid)
        try:
            require(helpers.identity(pid) == actor, 'pinned_waiter_start_args_root')
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                if (Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()[0] == 'T':
                    break
                time.sleep(.01)
            require((Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()[0] == 'T',
                'waiter_only_pause_observed')
            require(not any((OLD / f'lane{physical}' / name).exists() for name in CONSUMED),
                'never_interrupt_retirement_or_launch')
            helpers.write(NEW / f'CUT_WAITER_{physical}_INTENT.json', dict(actor=actor, physical=physical,
                observed_unix=time.time(), direct_native_signals=0))
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            require(bool(select.select([descriptor], [], [], 10)[0]), 'old_waiter_exited')
        finally:
            if not select.select([descriptor], [], [], 0)[0]:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            os.close(descriptor)
        require(not any((OLD / f'lane{physical}' / name).exists() for name in CONSUMED),
            'old_waiter_no_retirement')
        records.append(dict(physical=physical, actor=actor, exited=True))
    helpers.write(NEW / 'SUPERSEDED_WAITERS_CUT.json', dict(observed_unix=time.time(), waiters=records,
        direct_native_signals=0, deleted_files=0, old_outputs_preserved=True))
    result = []
    for physical in (0, 1, 3, 4):
        stage = helpers.read(NEW / f'lane{physical}/STAGED.json')
        check_owner(physical, helpers)
        command = [str(helpers.PYTHON), '-B', 'node4_rollout.py', 'handoff', '--bundle', str(NEW),
            '--physical', str(physical), '--wait-seconds', '5400']
        with (NEW / f'WAIT_{physical}.log').open('x') as log:
            process = subprocess.Popen(command, cwd=NEW, env=dict(os.environ, CUDA_VISIBLE_DEVICES='',
                PYTHONPATH=str(NEW), PYTHONDONTWRITEBYTECODE='1'), stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        result.append(dict(physical=physical, pid=process.pid, command=command, observed_unix=time.time(),
            preflight_status='PENDING_FRESH_ORIGINAL_SCAN_NOT_YET_ARMED'))
        helpers.write(NEW / f'WAITER_{physical}.json', result[-1])
    helpers.write(NEW / 'WAITERS_DISPATCHED.json', dict(rows=result, observed_unix=time.time(),
        final_admission_unchanged=True, direct_native_signals=0))
    return result


if __name__ == '__main__':
    print(json.dumps(main(), sort_keys=True))
