import json
import os
from pathlib import Path
import select
import signal
import time


root = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
output = Path('/localhome/local-rohing/orch_r188_main_C2_stop_20260917')
pid = 1626817
expected_ticks = '20440733'
saved_cycle = 41
saved_steps = 4428
record_root = root / 'stream/records'
checkpoint_path = root / 'checkpoints/sleep_000041/COMMIT.json'
checkpoint = json.loads(checkpoint_path.read_bytes())
assert checkpoint['optimizer_steps'] == saved_steps, 'saved41_optimizer_binding'
assert Path(checkpoint['optimizer_rng_path']).is_file(), 'saved_optimizer_rng_present'
assert Path(checkpoint['adapter_path']).is_dir(), 'saved_adapter_present'
output.mkdir(exist_ok=True)
assert not (output / 'STOP.json').exists(), 'one_stop_only'
handle = os.pidfd_open(pid)
try:
    process = Path(f'/proc/{pid}')
    ticks = process.joinpath('stat').read_text().split(') ', 1)[1].split()[19]
    assert ticks == expected_ticks, 'same_C2_process'
    arguments = process.joinpath('cmdline').read_bytes().split(b'\0')
    assert any(b'orch_r125_continual_native' in argument for argument in arguments), 'C2_native_not_parent'
    paths = sorted(path for path in record_root.glob('*.json') if not path.name.endswith('.intent.json'))
    initial = json.loads(paths[-1].read_bytes())
    intent = dict(authorization='Rohin188', root=str(root), pid=pid, start_ticks=ticks,
        saved_cycle=saved_cycle, saved_optimizer_steps=saved_steps,
        saved_checkpoint=str(checkpoint_path), observed_head=initial['index'],
        started_unix=time.time(), full_root_preserved=True, partial_sleep_discard_authorized=True)
    with (output / 'INTENT.json').open('x') as target:
        json.dump(intent, target, sort_keys=True)
        target.flush()
        os.fsync(target.fileno())
    deadline = time.monotonic() + 80
    cursor = initial['index']
    boundary = None
    while time.monotonic() < deadline:
        path = record_root / f'{cursor + 1:020d}.json'
        if not path.exists():
            time.sleep(0.02)
            continue
        observed = json.loads(path.read_bytes())
        cursor = observed['index']
        if observed['kind'] == 'SLEEP_COMPLETE':
            raise RuntimeError('sleep_completed_use_exact_boundary_no_discard_stop')
        if observed['kind'] == 'UPDATE':
            boundary = observed
            break
    assert boundary is not None, 'no_update_safe_point_no_signal'
    signal.pidfd_send_signal(handle, signal.SIGTERM)
    signalled = time.time()
    poller = select.poll()
    poller.register(handle, select.POLLIN)
    exited = bool(poller.poll(20000))
    latest = sorted(path for path in record_root.glob('*.json') if not path.name.endswith('.intent.json'))
    records = [json.loads(path.read_bytes()) for path in latest if int(path.stem) >= 5129]
    updates = [record for record in records if record['kind'] == 'UPDATE']
    result = dict(intent, status='STOPPED_PARTIAL_SLEEP_DISCARDED' if exited else 'SIGTERM_SENT_EXIT_UNCONFIRMED',
        signal='SIGTERM', signalled_unix=signalled, observed_exit_unix=time.time() if exited else None,
        safe_point_record_index=boundary['index'], safe_point_record_sha256=boundary['sha256'],
        discarded_logged_updates=len(updates), unlogged_in_flight_updates='unknown; no in-flight checkpoint claimed',
        final_head=records[-1]['index'] if records else 5128,
        final_head_sha256=records[-1]['sha256'] if records else None,
        archival_or_reload_done=False, forced_kill=False, files_deleted=False)
    with (output / 'STOP.json').open('x') as target:
        json.dump(result, target, sort_keys=True)
        target.flush()
        os.fsync(target.fileno())
    print(json.dumps(result, sort_keys=True))
finally:
    os.close(handle)
