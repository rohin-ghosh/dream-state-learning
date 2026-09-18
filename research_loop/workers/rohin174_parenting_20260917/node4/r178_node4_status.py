"""Read-only, bounded NODE4 inbox, TRAIN journal, and saved-boundary census."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


HOME = Path(__file__).resolve().parent
REPO = HOME.parents[3] if '--remote' not in sys.argv else None
ROWS = {
    0: ('kernel0', 'B', 653202, '24650415', 'orch_r132_kernel_child_20260916_attempt1', '/localhome/local-rohing/orch_r179_node4_20260917t1814z/lane0'),
    1: ('raw_unparented', 'PENDING_MAIN_R178_PRESERVATION', 294158, '24386173', 'orch_r136_raw_unparented_a40r1_20260916_attempt1', '/localhome/local-rohing/orch_r179_node4_20260917t1810z/lane1'),
    3: ('raw_parented', 'D', 259097, '24359775', 'orch_r136_raw_parented_seed1_a40r3_20260916_attempt1', '/localhome/local-rohing/orch_r179_node4_recovery_20260917t2000z/lane3'),
    4: ('kernel_parented', 'A', 310254, '24398138', 'orch_r136_kernel_parented_a40r4_20260916_attempt1', '/localhome/local-rohing/orch_r179_node4_20260917t1810z/lane4'),
}
BASELINE_END = 'question in your work? Choose a step and carry it out.'
WITHDRAWN = '11a39e52e43540f8839c312cf64e86ff'
WALL = 1789754400


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path, limit=64 * 1024 * 1024):
    path = Path(path)
    require(not path.is_symlink() and path.is_file(), 'regular_metadata_only')
    before = path.stat()
    require(before.st_size <= limit, 'bounded_metadata')
    raw = path.read_bytes()
    after = path.stat()
    require((before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns), 'stable_metadata_read')
    return json.loads(raw)


def actor(pid, start):
    root = Path('/proc', str(pid))
    try:
        before = (root / 'stat').read_text().rsplit(')', 1)[1].split()
        argv = [part.decode() for part in (root / 'cmdline').read_bytes().split(b'\0') if part]
        after = (root / 'stat').read_text().rsplit(')', 1)[1].split()
        require(before[19] == after[19] == start, 'exact_native_start_ticks')
        return dict(pid=pid, start_ticks=start, state=after[0], cpu_ticks=int(after[11]) + int(after[12]),
                    argv=argv, cwd=str((root / 'cwd').resolve()), uid=root.stat().st_uid,
                    alive=after[0] not in ('Z', 'X'))
    except (FileNotFoundError, ProcessLookupError):
        return dict(pid=pid, start_ticks=start, alive=False)


def collect_remote():
    sys.path.insert(0, '/localhome/local-rohing/orch_r175_node4_20260917t2040z/physical0/source')
    from gpu import orch_r127_pilot_transcript as transcript
    from gpu import orch_r166_parent_snapshot as snapshots
    result = []
    for physical, (label, arm, pid, start, name, stage_name) in ROWS.items():
        root = Path('/localhome/local-rohing') / name / 'run1'
        successor = Path('/localhome/local-rohing/orch_r179_node4_r181_20260917t2150z') / f'lane{physical}'
        if (successor / 'LOADED_RECEIPT.json').exists():
            loaded = read(successor / 'LOADED_RECEIPT.json')
            require(loaded['physical'] == physical and loaded['status'] == 'EXACT_SAVED_SUCCESSOR_LOADED', 'actual_R181_loaded_receipt')
            pid, start, stage_name = loaded['actor']['pid'], loaded['actor']['start_ticks'], str(successor)
        stage = Path(stage_name)
        guard = read(stage / 'control/GUARD.json')
        require(sha(guard['plan_path']) == guard['plan_sha256'], 'exact_current_plan')
        plan = read(guard['plan_path'])
        require(plan['root'] == str(root) and plan['physical'] == physical
                and plan['hard_end_unix'] == WALL, 'unchanged_root_physical_wall')
        reference = REFERENCES[physical]
        require(sha(reference['path']) == reference['sha256'], 'existing_cursor_exact_pin')
        cursor = read(reference['path'], snapshots.MAX_STATE_BYTES)
        polled = snapshots.poll(root, cursor, cursor_sha256=snapshots._digest(cursor))
        require(polled['snapshot']['caught_up'], 'bounded_cursor_caught_up')
        cursor = polled['cursor']
        inbox, delivered, ingested = cursor['inbox'], dict(cursor['delivered']), {}
        requests, responses, sleeps = cursor['request_count'], cursor['response_count'], cursor['sleep_count']
        for identifier, binding in delivered.items():
            request = read(root / 'stream/records' / f"{binding['record_index']:020d}.json")
            require(request['kind'] == 'REQUEST' and request['sha256'] == binding['record_sha256'], 'render_record_pin')
            binding['request_started_unix'] = request['document']['started_unix']
        head = update = last_sleep = last_retained = None
        tail_start = max(0, cursor['next_index'] - 280)
        previous = None
        for index in range(tail_start, cursor['next_index']):
            path = root / 'stream/records' / f'{index:020d}.json'
            record = read(path)
            require(record['sha256'] == snapshots._digest({key: value for key, value in record.items() if key != 'sha256'})
                and (previous is None or record['previous_sha256'] == previous), 'actual_tail_chain')
            previous = record['sha256']
            mtime, file_sha = path.stat().st_mtime, sha(path)
            document, kind = record['document'], record['kind']
            evidence = dict(record_index=record['index'], record_sha256=record['sha256'],
                            record_file_sha256=file_sha, file_mtime_unix=mtime)
            head = dict(evidence, kind=kind)
            if kind == 'INBOX':
                entry = transcript._inbox(document)
                inbox[entry['inbox_id']] = entry
                ingested[entry['inbox_id']] = evidence
            elif kind == 'REQUEST':
                require(document.get('split') == 'TRAIN', 'TRAIN_only_no_held_readouts')
                visible, ambiguous = transcript._visible(document['messages'], inbox)
                for identifier in visible - delivered.keys() - ambiguous:
                    delivered[identifier] = dict(evidence, request_started_unix=document['started_unix'],
                        request_count=requests, sleep_count=sleeps, inbox_sha256=inbox[identifier]['inbox_source_sha256'])
            elif kind == 'SLEEP_COMPLETE':
                last_sleep = dict(evidence, metadata={key: document[key] for key in
                    ('cycle', 'finished_unix', 'checkpoint_sha256') if key in document})
            elif kind == 'CONTEXT_RETAINED':
                last_retained = evidence
            elif kind == 'UPDATE':
                update = dict(evidence, optimizer_step=document['optimizer_step'], finished_unix=document['finished_unix'])
        require(head['record_sha256'] == cursor['head_sha256'], 'tail_ends_at_verified_cursor')
        messages = []
        for path in sorted((root / 'stream/inbox').glob('*.json')):
            message = read(path, 65536)
            require(message['split'] == 'TRAIN', 'TRAIN_inbox_only')
            identifier = message['id']
            require(path.name == identifier + '.json', 'exact_inbox_filename')
            baseline = message['text'].endswith(BASELINE_END)
            if identifier in delivered and not baseline and path.stat().st_mtime < 1789676400:
                continue
            messages.append(dict(id=identifier, path=str(path), sha256=sha(path),
                text_sha256=hashlib.sha256(message['text'].encode()).hexdigest(), speaker=message.get('speaker'),
                file_mtime_unix=path.stat().st_mtime, common_baseline=baseline,
                ingested=ingested.get(identifier), rendered=delivered.get(identifier),
                status='RENDERED' if identifier in delivered else ('INGESTED_NOT_RENDERED' if identifier in ingested else 'QUEUED_NOT_INGESTED')))
        checkpoints = sorted((root / 'checkpoints').glob('sleep_*/COMMIT.json'))
        saved = None
        if checkpoints:
            path = checkpoints[-1]
            checkpoint = read(path)
            saved = dict(path=str(path), sha256=sha(path), metadata={key: checkpoint[key] for key in
                ('optimizer_steps', 'checkpoint_sha256', 'adapter_state_sha256', 'adapter_path', 'optimizer_rng_path', 'experiment') if key in checkpoint})
        source = stage / 'source/gpu/orch_r125_continual_native.py'
        result.append(dict(physical=physical, label=label, arm=arm, root=str(root), actor=actor(pid, start),
            plan_path=guard['plan_path'], plan_sha256=guard['plan_sha256'], guard_path=str(stage / 'control/GUARD.json'),
            guard_sha256=sha(stage / 'control/GUARD.json'), source_path=str(source), source_sha256=sha(source),
            current_recipe={key: plan[key] for key in ('context_limit', 'segment_tokens', 'segments_per_sleep',
                'new_presentations', 'rehearsal_presentations', 'hard_end_unix')},
            head=head, journal_id=cursor['journal_id'], request_count=requests, response_count=responses,
            completed_sleeps=sleeps, latest_update=update, latest_saved_checkpoint=saved,
            latest_sleep_complete=last_sleep, latest_context_retained=last_retained, messages=messages,
            withdrawn_ingested=WITHDRAWN in inbox, withdrawn_rendered=WITHDRAWN in delivered,
            native_boundary_ready=False, boundary_state='OBSERVATION_ONLY_REVALIDATE_EXACT_SAVED_BOUNDARY'))
    return dict(schema='NODE4_R178_READ_ONLY_ACTUAL_STATUS_V1', observed_unix=time.time(), rows=result,
        model_calls=0, signals_sent=0, journal_writes=0, inbox_writes=0, readout_contents_read=0,
        raw_preservation_or_requeue_owner='Main', new_runtime_recipe_not_inferred=True)


def collect(output):
    require(output.parent.resolve() == HOME and not output.exists(), 'new_owned_receipt_only')
    references = {}
    for physical in ROWS:
        parent_path = HOME / f'activation_20260917T2057Z/physical{physical}/parent'
        if physical == 1:
            parent_path = HOME / 'activation_r178_20260917T2148Z/physical1/parent'
        paths = sorted(parent_path.glob('POLL_*.json'))
        references[physical] = read(paths[-2])['reference']
    script = f'REFERENCES = {references!r}\n' + Path(__file__).read_text()
    command = ['bash', str(REPO / 'gpu/a40r_ssh.sh'),
        'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B - --remote']
    execution = subprocess.run(command, input=script, text=True, capture_output=True, timeout=90)
    require(execution.returncode == 0, 'readonly_remote_failure:' + execution.stderr[-1000:])
    result = json.loads(execution.stdout)
    result['collector_sha256'] = sha(__file__)
    with output.open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
    return dict(path=str(output), sha256=sha(output), observed_unix=result['observed_unix'],
                rows=[dict(physical=row['physical'], alive=row['actor']['alive'], optimizer_step=row['latest_update']['optimizer_step'],
                    pending_ids=[message['id'] for message in row['messages'] if not message['rendered']]) for row in result['rows']])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remote', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seconds', type=int, default=0)
    arguments = parser.parse_args()
    if arguments.remote:
        print(json.dumps(collect_remote(), sort_keys=True))
    else:
        require(0 <= arguments.seconds <= 5400, 'bounded_readonly_observer')
        started = time.time()
        for sequence in range(181):
            target = arguments.output if not arguments.seconds else arguments.output.with_name(arguments.output.stem + f'_{sequence:04d}.json')
            try:
                print(json.dumps(collect(target), sort_keys=True), flush=True)
            except Exception as error:
                print(json.dumps(dict(status='READONLY_OBSERVER_ERROR_NOT_CHILD_FAILURE', error=str(error), observed_unix=time.time())), flush=True)
            if time.time() >= min(started + arguments.seconds, WALL):
                break
            time.sleep(min(30, max(0, started + arguments.seconds - time.time())))
