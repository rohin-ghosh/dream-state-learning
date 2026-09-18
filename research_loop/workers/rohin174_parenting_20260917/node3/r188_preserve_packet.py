"""Capture an immutable complete-state relocation packet without touching learners."""

import argparse
import json
from pathlib import Path
import shutil
import socket
import subprocess
import time

import r181_boundary as base
from r188_recovery import prefix_file, suffix_counts


def copy(source, target):
    subprocess.run(['cp', '-a', '--reflink=auto', str(source), str(target)], check=True)


def capture(physical, batch, final=False):
    base.require(batch.replace('_', '').isalnum(), 'owned_batch_name')
    control = base.HERE / ('r188' if physical in (1, 2) else 'r181') / ('physical' + str(physical))
    spec = base.read(control / 'LIVE_HANDOFF.json')
    plan = base.read(control / 'PLAN.json')
    root = Path(spec['backing_root'])
    stop_folder = base.HERE / 'r188/saved_stop' / ('physical' + str(physical))
    if final:
        armed = base.read(stop_folder / 'ARMED.json')
        while time.time() < base.HARD_END + 60:
            active = []
            for actor in armed['actors']:
                try:
                    fields = (Path('/proc') / str(actor['pid']) / 'stat').read_text().rsplit(') ', 1)[1].split()
                    if fields[19] == actor['ticks'] and fields[0] not in ('Z', 'X'):
                        active.append(actor['pid'])
                except FileNotFoundError:
                    pass
            if not active:
                break
            time.sleep(1)
        base.require(not active, 'original_native_timer_supervisor_must_all_exit')
    records = root / 'stream/records'
    for path in sorted(records.glob('*.json'), reverse=True):
        if path.stem.isdigit():
            record = base.read(path)
            if record['kind'] == 'SLEEP_COMPLETE':
                saved, saved_path = record, path
                break
    else:
        raise ValueError('actual_complete_checkpoint_required')
    state = base.saved_state(saved)
    packet = base.HERE / 'r188' / batch / ('physical' + str(physical))
    packet.mkdir(parents=True, exist_ok=False)
    target = packet / 'root'
    (target / 'checkpoints').mkdir(parents=True)
    (target / 'stream/records').mkdir(parents=True)
    cycle = saved['document']['cycle']
    checkpoint = root / 'checkpoints' / ('sleep_%06d' % cycle)
    copy(checkpoint, target / 'checkpoints' / checkpoint.name)
    copy(root / 'stream/JOURNAL.json', target / 'stream/JOURNAL.json')
    copy(root / 'stream/inbox', target / 'stream/inbox')
    selected = [path for path in records.iterdir() if prefix_file(path.name, saved['index'])]
    base.require(len(selected) == 2 * (saved['index'] + 1), 'all_journal_and_intent_prefix_files')
    subprocess.run(['cp', '-a', '--reflink=auto', '-t', str(target / 'stream/records'),
        *map(str, selected)], check=True)
    copy(root / 'readouts', target / 'readouts')
    if final:
        copy(root / 'stream', packet / 'final_live_stream')
        copy(stop_folder, packet / 'source_stop')
        suffix = [base.read(path) for path in sorted(records.glob('*.json'))
            if path.stem.isdigit() and int(path.stem) > saved['index']]
        counts = suffix_counts([saved, *suffix], saved)
        clean = (stop_folder / 'STOPPED.json').exists() and not suffix
        if clean:
            counts['unknown_inflight_update'] = 'NONE_AT_VERIFIED_COMPLETE_BOUNDARY'
        base.write(packet / 'FINAL_STOP.json', dict(observed_unix=time.time(),
            actors=armed['actors'], original_actors_exited=True, clean_saved_boundary=clean,
            latest_complete_index=saved['index'], latest_complete_cycle=cycle,
            source_full_stream_archived='final_live_stream', current_suffix_accounting=counts,
            partial_files_preserved=[path.name for path in records.iterdir() if '.partial' in path.name],
            source_hard_end_unix=base.HARD_END, source_machine_ceiling_unix=1789689600))
    copy(Path(plan['source_root']), packet / 'source')
    for relative in (base.NATIVE, 'gpu/orch_r125_stream_journal.py'):
        candidate = packet / 'source' / relative
        candidate.chmod(candidate.stat().st_mode | 0o200)
    copy(control / 'new_native.py', packet / 'source' / base.NATIVE)
    copy(control / 'new_journal.py', packet / 'source/gpu/orch_r125_stream_journal.py')
    (packet / 'control').mkdir()
    for name in ('PLAN.json', 'GUARD.json', 'ALLOCATION.json', 'LIVE_HANDOFF.json',
            'STOPPED.json', 'RESTORED.json', 'BOUNDARY.json', 'BOUNDARY_RECONCILED.json'):
        if not (control / name).exists():
            continue
        copy(control / name, packet / 'control' / name)
    pins = {str(path.relative_to(packet / 'source')): base.sha(path)
        for path in (packet / 'source').rglob('*.py')}
    base.require(pins == base.read(control / 'GUARD.json')['source_pins'], 'effective_live_source_exact')
    commit_path = target / 'checkpoints' / checkpoint.name / 'COMMIT.json'
    commit = base.read(commit_path)
    mapped = lambda value: target / Path(value).relative_to(plan['root'])
    base.require(base.sha(mapped(commit['optimizer_rng_path'])) ==
        commit['checkpoint_sha256']['optimizer'] == commit['checkpoint_sha256']['rng'],
        'copied_exact_optimizer_RNG')
    adapter = {path.name: base.sha(path) for path in mapped(commit['adapter_path']).iterdir()
        if path.is_file()}
    base.require(adapter == commit['adapter_files'] and base.digest(adapter) ==
        commit['checkpoint_sha256']['adapter'] and base.digest(commit['checkpoint_sha256']) ==
        state['model_state_sha256'], 'copied_exact_adapter_state')
    base.require(base.sha(target / 'stream/records' / saved_path.name) == base.sha(saved_path),
        'copied_exact_COMPLETE_record')
    inventory = {str(path.relative_to(packet)): dict(bytes=path.stat().st_size, sha256=base.sha(path))
        for path in packet.rglob('*') if path.is_file() and 'readouts' not in path.parts}
    base.write(packet / 'FILES.json', inventory)
    base.write(packet / 'PACKET.json', dict(status='COMPLETE_STATE_PACKET_VERIFIED', physical=physical,
        observed_unix=time.time(), original_root=spec['backing_root'], logical_root=plan['root'],
        source_root=plan['source_root'], captured_cycle=cycle, saved_record_index=saved['index'],
        saved_record_sha256=saved['sha256'], model_state_sha256=state['model_state_sha256'],
        checkpoint_file_sha256=base.sha(commit_path), total_optimizer_steps=commit['optimizer_steps'],
        inventory_sha256=base.sha(packet / 'FILES.json'), native_sha256=pins[base.NATIVE],
        journal_sha256=pins['gpu/orch_r125_stream_journal.py'], original_hard_end_unix=base.HARD_END,
        opaque_readout_archive_not_inspected=True, current_learner_continues=not final,
        later_live_updates_not_in_this_packet=not final, parent_rebind_required=True,
        final_full_stream_included=final,
        target_host_device_and_wall_binding_required=True, base_weights_not_copied=True))
    print(json.dumps(dict(physical=physical, packet=str(packet), cycle=cycle,
        saved_record_index=saved['index'], status='COMPLETE_STATE_PACKET_VERIFIED')), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, choices=(0, 1, 2, 3, 4, 7), required=True)
    parser.add_argument('--batch', required=True)
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args()
    base.require(socket.gethostname() == '[REDACTED_HOST]', 'node3_only')
    capture(args.physical, args.batch, args.final)
