"""Retire only settled old parent leaders before receiving transport rebinding."""

from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import select
import signal
import time

import metadata_rebind
import node3_route_binding as route
import takeover as base


PARENTS = {0: 1234080, 1: 1353671, 2: 1353660, 3: 1237059, 4: 1237074, 7: 1237079}
OUTPUT = base.HERE / 'r188/final_parent_handoff'


def stop(physical):
    folder = route.folder_for(physical)
    pid = PARENTS[physical]
    descriptor = None
    terminated = False
    try:
        if not Path('/proc', str(pid)).exists():
            ledger = metadata_rebind.modern_ledger(folder / 'parent', base.read(folder / 'CONFIG.json'))
            status = 'ORIGINAL_PARENT_ALREADY_ABSENT'
            expected = dict(pid=pid)
        else:
            expected = base.identity(pid)
            wrapper = 'r188_parent.py' if physical in (1, 2) else 'r184_effort_parent.py'
            base.require(expected['argv'][2:] == [str(base.HERE / wrapper), 'serve', '--physical', str(physical)],
                'exact_original_owned_parent_command')
            base.ledger = metadata_rebind.modern_ledger
            descriptor, ledger = base.quiet_pause(expected, folder / 'parent',
                base.read(folder / 'CONFIG.json'), time.monotonic() + 20)
            base.write(OUTPUT / ('physical' + str(physical) + '.STOP_INTENT.json'),
                dict(identity=expected, observed_unix=time.time(), ledger=ledger))
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            terminated = True
            base.require(bool(select.select([descriptor], [], [], 20)[0]), 'actual_old_parent_exit')
            status = 'SETTLED_ORIGINAL_PARENT_STOPPED'
        base.write(OUTPUT / ('physical' + str(physical) + '.json'), dict(status=status,
            identity=expected, observed_unix=time.time(), config=base.reference(folder / 'CONFIG.json'),
            seed=base.reference(folder / 'SEED.json'), original_output=str(folder / 'parent'),
            ledger=ledger, pending_publications_not_resent=True, receiving_parent_not_started=True))
    except BaseException as error:
        base.write(OUTPUT / ('physical' + str(physical) + '.BLOCKED.json'),
            dict(reason=str(error)[:500], error_type=type(error).__name__, observed_unix=time.time(),
                no_receiving_parent_authorized=True))
    finally:
        if descriptor is not None:
            if not terminated and not select.select([descriptor], [], [], 0)[0]:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            os.close(descriptor)


if __name__ == '__main__':
    OUTPUT.mkdir(exist_ok=False)
    base.write(OUTPUT / 'ARMED.json', dict(observed_unix=time.time(),
        not_before_unix=base.HARD_END - 45, no_provider_call=True))
    time.sleep(max(0, base.HARD_END - 45 - time.time()))
    with ThreadPoolExecutor(max_workers=6) as executor:
        list(executor.map(stop, PARENTS))
