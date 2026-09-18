"""Rohin96 selective handoff; never restart guards or touch the permanent lane."""

import json
import os
from pathlib import Path
import signal
import time

from gpu import orch_rich_hot_a100_run as existing
import orch_rich_hot_a100_minor_scan as minor_scanner


ASSIGNMENTS = {'Laplace': (2, 3), 'Anscombe': (4, 5, 7)}


def requested_indices(owner, request):
    existing.policy.require(owner in ASSIGNMENTS and request.get('requester') == owner and
                            request.get('launch_ready') is True, 'actual_named_ready_request_required')
    return ASSIGNMENTS[owner]


def signal_owned(index, expected):
    existing.policy.require(index in (2, 3, 4, 5, 7), 'permanent_or_peer_lane_forbidden')
    directory = Path('/proc') / str(expected['pid'])
    if not directory.exists():
        return False
    descriptor = os.pidfd_open(expected['pid'])
    try:
        existing.policy.require(existing.identity(directory) == expected and expected['uid'] == os.getuid(),
                                'exact_owned_process_required')
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        return True
    finally:
        os.close(descriptor)


def main():
    root = existing.ROOT
    existing.validate(root)
    lifetime = existing.read(root / 'LIFETIME.json')
    existing.policy.require(time.time() < lifetime['native_deadline_unix'], 'original_budget_expired')
    existing.exclusive(root / 'RELEASE_WATCH_IDENTITY.json', dict(
        identity=existing.identity(Path('/proc') / str(os.getpid())), driver_sha256=existing.sha(__file__),
        scanner_sha256=existing.sha(minor_scanner.__file__), assignments=ASSIGNMENTS,
        inherited_deadline=lifetime['hard_deadline_unix']))
    handled, pending, released = set(), {}, {}
    while time.time() < lifetime['hard_deadline_unix']:
        for owner in ASSIGNMENTS:
            request_path = root / f'{owner.upper()}_RELEASE_REQUEST.json'
            if owner in handled or not request_path.exists():
                continue
            try:
                request = existing.read(request_path)
                for index in requested_indices(owner, request):
                    pinned = existing.read(root / f'LAUNCH_{index}.json')['identity']
                    signalled = signal_owned(index, pinned)
                    pending[index] = (owner, pinned)
                    existing.write(root / f'FLOOR_STOP_{index}.json', dict(owner=owner, identity=pinned,
                        request_sha256=existing.sha(request_path), signalled=signalled, requested_unix=time.time()))
                handled.add(owner)
            except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
                existing.write(root / f'{owner.upper()}_REQUEST_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        for index, (owner, pinned) in list(pending.items()):
            directory = Path('/proc') / str(pinned['pid'])
            if directory.exists():
                continue
            report = minor_scanner.scan(index, root / 'SERVICE_IDENTITY.json')
            existing.write(root / f'FLOOR_RELEASE_{index}.json', report)
            if report['clear']:
                released[index] = dict(owner=owner, stopped_identity=pinned,
                    release_sha256=existing.sha(root / f'FLOOR_RELEASE_{index}.json'))
                del pending[index]
                existing.write(root / 'FLOOR_RELEASES.json', dict(released=released, updated_unix=time.time()))
        if len(released) == 5:
            break
        time.sleep(2)
    existing.write(root / 'RELEASE_WATCH_TERMINAL.json', dict(released=released, pending=list(pending),
                                                            finished_unix=time.time()))


if __name__ == '__main__':
    main()
