"""Bind CPU delivery only after the exact continued P7 native actually loads."""

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import time


TARGET = Path('/localhome/local-rohing/orch_r233_p7_deadline_20260918')
ENDPOINT = Path('/localhome/local-rohing/orch_r233_p7_recovery_20260918/renewed')
sys.path.insert(0, str(ENDPOINT))
from native_binding import verify
from receipt_window import read_record
from deadline_resume import digest, identity, read, require, sha, write


def capture():
    control = TARGET / 'control'
    guard = read(control / 'GUARD.json')
    plan = read(control / 'PLAN.json')
    records = Path(plan['root']) / 'stream/records'
    preservation = read(control / 'PRESERVED.json')
    original = read_record(records / f'{preservation["complete_index"]:020d}.json',
        'e9d22d1e26234c4bbac761922929365f')
    wall = None
    for path in sorted(records.glob('[0-9]' * 20 + '.json')):
        if int(path.stem) <= preservation['complete_index']:
            continue
        with path.open('rb') as stream:
            stream.seek(max(0, path.stat().st_size - 512))
            ending = stream.read()
        if b'"kind":"WALL_EXTENDED"' in ending:
            candidate = read_record(path, original['journal_id'])
            if candidate['document']['plan_sha256'] == guard['plan_sha256']:
                wall = candidate
        if b'"kind":"LOADED"' not in ending or wall is None:
            continue
        loaded = read_record(path, original['journal_id'])
        native = identity(loaded['document']['pid'])
        require(native['argv'][-2:] == ['--config', str(control / 'GUARD.json')],
            'LOAD_from_exact_renewed_guard')
        require(loaded['document']['optimizer_steps'] == preservation['checkpoint']['optimizer_steps'],
            'same_saved_optimizer_step_at_LOAD')
        before = original['document']['resume_state']
        after = deepcopy(wall['document']['state'])
        require(after['sha256'] == digest(after['state'])
            and wall['document']['authorization']['previous_stream_sha256'] == before['sha256'],
            'actual_extension_exact_prior_saved_state')
        after['state']['deadline_unix'] = before['state']['deadline_unix']
        require(after['state'] == before['state'], 'whole_stream_only_deadline_changed')
        binding = dict(native, previous_pid=1100592, journal_id=original['journal_id'],
            guard_path=str(control / 'GUARD.json'), guard_sha256=sha(control / 'GUARD.json'),
            plan_sha256=sha(control / 'PLAN.json'), hard_end_unix=plan['hard_end_unix'],
            wall_index=wall['index'], wall_sha256=wall['sha256'],
            loaded_index=loaded['index'], loaded_sha256=loaded['sha256'],
            loaded_unix=loaded['document']['loaded_unix'], observed_unix=time.time())
        binding_path = ENDPOINT / 'NATIVE_BINDING.json'
        write(binding_path, binding)
        verify(binding_path, Path(plan['root']).parent, Path(plan['source_root']))
        old_exit = read(Path(plan['source_root']).parent / 'control/EXIT.json')['finished_unix']
        public = dict(status='WALL_EXTENDED_AND_LOADED', observed_unix=time.time(),
            native=dict(pid=native['pid'], start_ticks=native['start_ticks']),
            journal_id=original['journal_id'], preserved_complete_index=original['index'],
            preserved_complete_sha256=original['sha256'], checkpoint_cycle=original['document']['cycle'],
            optimizer_steps=loaded['document']['optimizer_steps'],
            loaded=dict(index=loaded['index'], sha256=loaded['sha256'], loaded_unix=loaded['document']['loaded_unix'],
                adapter_sha256=loaded['document']['adapter_sha256']),
            wall_extended=dict(index=wall['index'], sha256=wall['sha256'],
                authorization=wall['document']['authorization'], written_unix=(records / f'{wall["index"]:020d}.json').stat().st_mtime),
            old_natural_exit_unix=old_exit, reload_gap_seconds=loaded['document']['loaded_unix'] - old_exit,
            hard_end_unix=plan['hard_end_unix'], guard_sha256=binding['guard_sha256'],
            plan_sha256=binding['plan_sha256'], unchanged_source=True, whole_stream_only_deadline_changed=True,
            native_signals=[], training_policy_changed=False, all_exclusions_off_claim=False,
            cpu_binding_path=str(binding_path), cpu_binding_sha256=sha(binding_path))
        write(TARGET / 'NATIVE_CONTINUATION.public.json', public)
        print(json.dumps(public), flush=True)
        return True
    return False


if __name__ == '__main__':
    until = time.monotonic() + 3600
    while time.monotonic() < until:
        if capture():
            break
        time.sleep(2)
    else:
        raise TimeoutError('actual_new_P7_LOAD_not_observed_within_finite_receipt_watch')
