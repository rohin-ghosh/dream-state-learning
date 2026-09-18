"""R188 exact kernel0 interruption and full-root archive; never launch a child."""

import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time


BUNDLE = Path('/localhome/local-rohing/orch_r179_node4_r181journal_20260917t2220z')
OUTPUT = Path('/localhome/local-rohing/orch_r188_node4_20260917t2315z/kernel0')
ROOT = Path('/localhome/local-rohing/orch_r132_kernel_child_20260916_attempt1/run1')
OPERATOR_SHA = '3bebf07c0eb71b8dfaef71511cc01662973da335a8e781bdc1034cb6742a3874'
CONSUMED = ('RETIREMENT_STARTED.json', 'RETIRED.json', 'DISPATCHED.json', 'LOADED_RECEIPT.json')


def main():
    spec = importlib.util.spec_from_file_location('r188_original_operator', BUNDLE / 'node4_rollout.py')
    operator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(operator)
    helpers = operator.helper_module(BUNDLE)
    require = helpers.require
    require(helpers.sha(BUNDLE / 'node4_rollout.py') == OPERATOR_SHA, 'original_handoff_primitives')
    require(not OUTPUT.exists(), 'new_R188_stop_attempt')
    require(os.getuid() == 2524 and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'exact_CPU_operator')
    config_path, config, plan, original, pair = operator.selected(0, helpers)
    require(plan['root'] == str(ROOT) and plan['rehearsal_presentations'] == 1,
        'only_original_full_rehearsal_kernel0')
    require(pair['actor']['pid'] == 653202 and pair['actor']['start_ticks'] == '24650415',
        'exact_R188_kernel0_owner')
    children = Path('/proc/653202/task/653202/children').read_text().split()
    require(not children, 'no_readout_child_during_interrupted_training')
    waiter = helpers.identity(1362329)
    require(waiter['uid'] == 2524 and waiter['cwd'] == str(BUNDLE)
        and waiter['argv'] == [str(helpers.PYTHON), '-B', 'node4_rollout.py', 'handoff',
            '--bundle', str(BUNDLE), '--physical', '0', '--wait-seconds', '5400'], 'exact_superseded_waiter')
    require(not any((BUNDLE / 'lane0' / name).exists() for name in CONSUMED), 'no_handoff_started')
    OUTPUT.mkdir(parents=True)
    helpers.write(OUTPUT / 'INTENT.json', dict(schema='R188_AUTHORIZED_OLD_SLEEP_DISCARD',
        directive='R188 authorizes stopping/discarding old full-rehearsal sleeps >15min ETA; recover from lastCOMPLETE; preserve FULL oldroot/journal/inbox including suffix; do not claim exact in-flight continuation.',
        physical=0, root=str(ROOT), expected_processes=pair, old_waiter=waiter,
        exact_inflight_continuation=False, no_model_launch=True, observed_unix=time.time()))
    descriptor = os.pidfd_open(waiter['pid'])
    try:
        helpers.pause_exact(waiter, descriptor)
        require(not any((BUNDLE / 'lane0' / name).exists() for name in CONSUMED), 'no_waiter_race')
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        require(bool(select.select([descriptor], [], [], 20)[0]), 'superseded_waiter_exit')
    finally:
        os.close(descriptor)
    descriptors = {name: os.pidfd_open(process['pid']) for name, process in pair.items()}
    paused = []
    try:
        for name in ('supervisor', 'timer', 'actor'):
            helpers.pause_exact(pair[name], descriptors[name])
            paused.append(name)
        helpers.write(OUTPUT / 'PAUSED.json', dict(processes=pair, paused_unix=time.time(),
            all_threads_quiescent=True, inplace_training_halted=True, uncertain_inflight_update=True))
        archive = OUTPUT / 'FULL_OLD_ROOT'
        archive.mkdir()
        subprocess.run(['cp', '-a', '--reflink=auto', str(ROOT) + '/.', str(archive)], check=True, timeout=300)
        before = helpers.inventory_files(ROOT)
        copied = helpers.inventory_files(archive)
        require(before == copied, 'entire_old_root_archive_exact')
        helpers.write(OUTPUT / 'FULL_OLD_ROOT_MANIFEST.json', before)
        helpers.write(OUTPUT / 'ARCHIVED.json', dict(root=str(ROOT), archive=str(archive), files=len(before),
            manifest_sha256=helpers.sha(OUTPUT / 'FULL_OLD_ROOT_MANIFEST.json'),
            full_journal_inbox_suffix_checkpoints_readouts_preserved=True, observed_unix=time.time()))
        helpers.write(OUTPUT / 'STOP_INTENT.json', dict(processes=pair,
            archive_receipt_sha256=helpers.sha(OUTPUT / 'ARCHIVED.json'), observed_unix=time.time()))
        for name in ('actor', 'timer', 'supervisor'):
            require(helpers.identity(pair[name]['pid']) == pair[name], 'exact_owner_before_stop')
            signal.pidfd_send_signal(descriptors[name], signal.SIGTERM)
            signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
            require(bool(select.select([descriptors[name]], [], [], 30)[0]), 'directed_owner_exit')
            paused.remove(name)
        helpers.write(OUTPUT / 'STOPPED.json', dict(processes=pair, stopped_unix=time.time(),
            physical=0, last_complete_cycle=40, actual_discard_requires_logged_update_census=True,
            uncertain_inflight_update=True, exact_inflight_continuation=False, no_model_launch=True))
        print(json.dumps(dict(status='EXACT_R188_KERNEL0_STOPPED_FULL_ROOT_ARCHIVED', output=str(OUTPUT))))
    finally:
        for name in reversed(paused):
            if not select.select([descriptors[name]], [], [], 0)[0]:
                signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
        for descriptor in descriptors.values():
            os.close(descriptor)


if __name__ == '__main__':
    main()
