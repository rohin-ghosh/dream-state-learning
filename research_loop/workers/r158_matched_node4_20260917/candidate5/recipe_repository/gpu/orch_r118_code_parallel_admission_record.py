"""Prospective bounded scan recording; never launches or weakens admission."""

from pathlib import Path
import time

from gpu import orch_r118_code_parallel_handoff as handoff


io, require = handoff.io, handoff.require


def acquire(service, root, plan, *, deadline, scan=handoff.previous.scan,
            attempts=1, interval=5, clock=time.time, pause=time.sleep):
    service, root = Path(service), Path(root)
    require(service.resolve().is_relative_to(root.resolve()) and service != root, 'owned_service_scan_record')
    require(type(attempts) is int and 1 <= attempts <= 3 and 1 <= interval <= 10,
        'bounded_readonly_scans')
    require(clock() < deadline <= min(plan['hard_deadline_unix'], handoff.TRAIN_END),
        'unchanged_startup_deadline')
    directory = service / 'ADMISSION_ATTEMPTS'
    directory.mkdir(parents=True, exist_ok=False)
    for ordinal in range(attempts):
        require(clock() < deadline, 'scan_deadline_no_reset')
        started = clock()
        try:
            report = scan(root)
        except Exception as error:
            io.write(directory / f'ERROR_{ordinal:03d}.json', dict(error_type=type(error).__name__,
                observed_unix=clock(), scan_started_unix=started, GPU_launches=0))
            raise
        path = directory / f'SCAN_{ordinal:03d}.json'
        io.write(path, report)
        accepted = handoff.previous.admitted(report, plan)
        io.write(directory / f'DECISION_{ordinal:03d}.json', dict(snapshot=handoff.ref(path),
            accepted=accepted, started_unix=started, observed_unix=clock(), GPU_launches=0))
        if accepted:
            require(clock() < deadline, 'no_late_clear_admission')
            return report
        if ordinal + 1 < attempts and clock() + interval < deadline:
            pause(interval)
        else:
            break
    raise ValueError('fresh_privileged_full_admission_recorded_rejection')
