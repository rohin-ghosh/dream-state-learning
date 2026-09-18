"""Finite TRAIN-only journal readout; executed with the retained R195 helpers."""

import collections
import datetime
import hashlib
import json
import os
import pathlib
import re
import time


MAX_RECORDS = 2000
MAX_NODE_BYTES = 256 * 1024 * 1024
MAX_NODE_SECONDS = 110
started = time.monotonic()
node_bytes = 0
prefix_read_limit = 65536


def read_bytes(path, limit=2 * 1024 * 1024, tail=False):
    global node_bytes
    if time.monotonic() - started > MAX_NODE_SECONDS:
        raise RuntimeError('NODE_TIME_LIMIT')
    size = path.stat().st_size
    if not tail and size > limit:
        raise RuntimeError('FILE_SIZE_LIMIT')
    charge = min(size, limit)
    if node_bytes + charge > MAX_NODE_BYTES:
        raise RuntimeError('NODE_BYTE_LIMIT')
    with path.open('rb') as handle:
        if tail:
            handle.seek(max(0, size - limit))
        raw = handle.read(limit)
    node_bytes += len(raw)
    return raw


def prefix_bytes(path, limit=None):
    global node_bytes
    limit = limit or prefix_read_limit
    if time.monotonic() - started > MAX_NODE_SECONDS or node_bytes + limit > MAX_NODE_BYTES:
        raise RuntimeError('PREFIX_BUDGET')
    with path.open('rb') as handle:
        raw = handle.read(limit)
    node_bytes += len(raw)
    return raw


def reference(path, meta, root):
    return dict(index=meta['index'], kind=meta['kind'], record_sha256=meta['sha256'],
        path=str(path), configured_path=str(root / 'stream/records' / path.name),
        mtime_unix=path.stat().st_mtime)


def request_fields(path, with_prompt=True):
    global prefix_read_limit
    try:
        prefix_read_limit = 262144
        document = leading_document(path) if with_prompt else {}
    finally:
        prefix_read_limit = 65536
    tail = read_bytes(path, 16384, tail=True).decode()
    suffix = tail.rsplit('},"index":', 1)[0].rsplit(',"schema":', 1)[1]
    ending = json.loads('{"schema":' + suffix + '}')
    return {key: value for key, value in dict(document, **ending).items()
            if key in ('prompt_tokens', 'split', 'segment', 'started_unix', 'training_eligible')}


def loaded_matches(document, pid, process_started_unix):
    loaded = document.get('loaded_unix')
    return (document.get('pid') == pid and isinstance(loaded, (int, float))
            and loaded >= process_started_unix - 1)


def incarnation_paths(paths, loaded):
    return [path for path in paths if int(path.stem) >= loaded['reference']['index']] if loaded else []


def state_reason(reason):
    if not isinstance(reason, str):
        return {}
    overflow = re.match(r'^working_state_overflow:(\d+)>(\d+);', reason)
    if overflow:
        return dict(consolidation_reason='working_state_overflow',
            working_state_bytes=int(overflow[1]), working_state_byte_budget=int(overflow[2]))
    return dict(consolidation_reason=reason if re.fullmatch(r'[A-Za-z0-9_:. -]{1,128}', reason)
        else 'UNCLASSIFIED_REASON')


def timestamp(document, ref, now):
    for key in ('finished_unix', 'started_unix', 'loaded_unix', 'created_unix'):
        value = document.get(key)
        if isinstance(value, (int, float)) and 946684800 < value <= now + 60:
            return value, 'document.' + key
    value = ref['mtime_unix']
    return (value, 'mtime') if 946684800 < value <= now + 60 else (None, 'UNVERIFIED')


def audit_life(native):
    plan = native['plan']
    root = pathlib.Path(plan['root'])
    if not root.is_absolute() or '..' in root.parts or not str(root).startswith('/localhome/local-rohing/orch_'):
        raise RuntimeError('UNSCOPED_ROOT')
    process = pathlib.Path('/proc') / str(native['pid'])
    records = process / 'root' / str(root).lstrip('/') / 'stream/records'
    all_paths = sorted(path for path in records.glob('*.json') if re.fullmatch(r'\d{20}\.json', path.name))
    selected = all_paths[-MAX_RECORDS:]
    now = time.time()
    boot = next(int(line.split()[1]) for line in pathlib.Path('/proc/stat').read_text().splitlines()
                if line.startswith('btime '))
    row = dict(pid=native['pid'], start_ticks=native['start_ticks'], uid=os.getuid(),
        state=native['state'], source_root=native['cwd'], configured_root=str(root),
        physical=plan.get('physical'), trial_id=plan.get('think_act_learn', {}).get('trial_id'),
        native_identity_verified=False, record_count=len(all_paths), records_scanned=len(selected),
        raw_last10=[], raw_unverified=0, stages=[], sleeps=[], compactions=[], errors=[],
        requests_hour=0, parent_inbox_hour=0, working_state_statuses={}, latest_request=None)
    row['think_policy'] = {key: value for key, value in plan.get('think_act_learn', {}).items()
        if key in ('think_segments', 'stage_boundary_policy', 'structured_think_policy', 'effort_policy')}
    row['parent_messages_hour'] = []
    row['process_started_unix'] = boot + int(native['start_ticks']) / os.sysconf('SC_CLK_TCK')
    row['plan_path'] = native['plan_path']
    row['plan_file_sha256'] = hashlib.sha256(read_bytes(pathlib.Path(native['plan_path']))).hexdigest()
    if not selected:
        row['errors'].append('NO_JOURNAL_RECORDS')
        row['status'] = 'UNVERIFIED_READOUT'
        return row
    cache = {}
    def get_meta(path):
        if path not in cache:
            cache[path] = metadata(path)
        return cache[path]
    loaded = None
    for path in reversed(all_paths[-10000:]):
        meta = get_meta(path)
        if meta['kind'] == 'LOADED':
            document = full_record(path)['document']
            if loaded_matches(document, native['pid'], row['process_started_unix']):
                loaded = dict(reference=reference(path, meta, root), pid=document['pid'],
                    loaded_unix=document['loaded_unix'], trial_id=row['trial_id'], record_hash_verified=True)
                break
    row['current_loaded'] = loaded
    row['incarnation_status'] = 'LOADED_VERIFIED' if loaded else 'LOADING_OR_LOAD_UNVERIFIED'
    boundary = loaded['reference']['index'] if loaded else int(all_paths[-1].stem) + 1
    inherited = [path for path in selected if int(path.stem) < boundary]
    row['inherited_source'] = dict(records_before_load=sum(int(path.stem) < boundary for path in all_paths))
    if inherited:
        inherited_head = inherited[-1]
        row['inherited_source']['head'] = reference(inherited_head, get_meta(inherited_head), root)
        for path in reversed(inherited):
            meta = get_meta(path)
            if meta['kind'] == 'REQUEST':
                row['inherited_source']['latest_request'] = dict(request_fields(path), reference=reference(path, meta, root))
                break
    selected = incarnation_paths(selected, loaded)
    row['records_scanned'] = len(selected)
    row['hour_window_complete'] = bool(loaded and (loaded['loaded_unix'] >= now - 3600
        or len(selected) == sum(int(path.stem) >= boundary for path in all_paths)
        or (selected and selected[0].stat().st_mtime <= now - 3600)))
    row['parent_window_exposure_seconds'] = min(3600, max(0, now - loaded['loaded_unix'])) if loaded else None
    row['window_first_index'] = int(selected[0].stem) if selected else None
    latest_request = None
    sleep_start = None
    recipe = None
    statuses = collections.Counter()
    responses = collections.deque(maxlen=10)
    state_edits = {}
    stage_window = []
    for path in selected:
        meta = get_meta(path)
        ref = reference(path, meta, root)
        kind = meta['kind']
        stamp, clock = timestamp({}, ref, now)
        recent = stamp is not None and stamp >= now - 3600
        row['head'] = dict(ref, age_seconds=max(0, now - stamp) if stamp is not None else None,
            timestamp_unix=stamp, timestamp_source=clock)
        if kind == 'REQUEST':
            try:
                document = request_fields(path, with_prompt=False)
            except (ValueError, IndexError, KeyError):
                latest_request = None
                row['errors'].append('REQUEST_METADATA_UNVERIFIED:' + str(meta['index']))
                continue
            latest_request = dict(document, reference=ref)
            stamp, clock = timestamp(document, ref, now)
            row['head'].update(age_seconds=max(0, now - stamp) if stamp is not None else None,
                timestamp_unix=stamp, timestamp_source=clock)
            recent = stamp is not None and stamp >= now - 3600
            if document.get('split') == 'TRAIN':
                row['latest_request'] = latest_request
                row['requests_hour'] += int(recent)
        elif kind == 'RESPONSE':
            responses.append((path, ref, latest_request))
        elif kind == 'SLEEP_REQUEST':
            sleep_start = ref
        elif kind == 'LOADED':
            document = full_record(path)['document']
            row['latest_loaded'] = dict(reference=ref, pid=document.get('pid'),
                optimizer_steps=document.get('optimizer_steps'))
            stamp, clock = timestamp(document, ref, now)
            row['head'].update(age_seconds=max(0, now - stamp) if stamp is not None else None,
                timestamp_unix=stamp, timestamp_source=clock)
        elif kind == 'SLEEP_RECIPE':
            document = full_record(path)['document']
            recipe = dict(reference=ref, **{key: document.get(key) for key in
                ('new_rows', 'selected_old_rows', 'available_old_rows', 'new_presentations', 'policy')})
        elif kind == 'SLEEP_COMPLETE':
            document = leading_document(path)
            presentations = document.get('presentations')
            new_hashes = set(document.get('new_row_sha256', []))
            entry = dict(reference=ref, cycle=document.get('cycle'),
                optimizer_steps=document.get('optimizer_steps'), total_optimizer_steps=document.get('total_optimizer_steps'),
                new_rows=len(document['new_row_sha256']) if 'new_row_sha256' in document else None,
                new_updates=sum(count for source, count in presentations.items() if source in new_hashes)
                    if isinstance(presentations, dict) else None,
                replay_updates=sum(count for source, count in presentations.items() if source not in new_hashes)
                    if isinstance(presentations, dict) else None,
                recipe=recipe, start_reference=sleep_start,
                duration_mtime_seconds=round(ref['mtime_unix'] - sleep_start['mtime_unix'], 3) if sleep_start else None)
            row['sleeps'] = (row['sleeps'] + [entry])[-3:]
            sleep_start = None
            recipe = None
        elif kind in ('COMPACTION', 'COMPACTION_SKIPPED', 'R203_CONTEXT_BUDGET_BLOCKED'):
            document = leading_document(path)
            row['compactions'] = (row['compactions'] + [dict(reference=ref,
                fields={key: document[key] for key in ('kind', 'reason', 'before_tokens', 'after_tokens', 'threshold_tokens')
                        if key in document})])[-5:]
        elif kind == 'R184_STAGE':
            document = full_record(path)['document']
            consolidation = document.get('consolidation') or {}
            entry = dict(reference=ref, stage=document.get('stage'), segment=document.get('segment'),
                consolidation_status=consolidation.get('status'),
                consolidation_source=consolidation.get('source_event_id'))
            entry.update(state_reason(consolidation.get('reason')))
            stage_window.append(entry)
            if consolidation.get('source_event_id') and consolidation.get('status'):
                state_edits[consolidation['source_event_id']] = consolidation['status']
        elif kind == 'INBOX' and recent:
            document = full_record(path)['document']
            message = document.get('message', {})
            if message.get('split') == 'TRAIN' and message.get('actor') == 'parent':
                row['parent_inbox_hour'] += 1
                row['last_parent_inbox'] = ref
                row['parent_messages_hour'] = (row['parent_messages_hour'] + [dict(reference=ref,
                    speaker=message.get('speaker', 'LEGACY_UNATTRIBUTED_PARENT'))])[-20:]
    for path, ref, request in responses:
        if request is None or request.get('split') != 'TRAIN':
            row['raw_unverified'] += 1
            continue
        record = full_record(path)
        response = record['document'].get('response', {})
        raw = response.get('raw')
        if not isinstance(raw, str) or re.fullmatch(r'(?:sha256:)?[a-fA-F0-9]{64}', raw.strip()):
            row['raw_unverified'] += 1
            continue
        row['raw_last10'].append(dict(reference=ref, request_reference=request['reference'], raw=raw,
            raw_sha256=hashlib.sha256(raw.encode()).hexdigest(), raw_chars=len(raw),
            truncated=response.get('truncated'), record_hash_verified=True))
    row['stages'] = stage_window[-12:]
    if row['latest_request'] is not None:
        request_path = pathlib.Path(row['latest_request']['reference']['path'])
        document = request_fields(request_path)
        row['latest_request']['prompt_tokens'] = document.get('prompt_tokens')
        row['latest_request']['after_current_process_start'] = (
            row['latest_request'].get('started_unix', 0) >= row['process_started_unix'])
    think_runs = []
    consecutive = 0
    for stage in stage_window:
        if stage['stage'] == 'THINK':
            consecutive += 1
        elif consecutive:
            think_runs.append(consecutive)
            consecutive = 0
    if consecutive:
        think_runs.append(consecutive)
    row['think_runs'] = think_runs[-12:]
    row['stage_opportunities'] = len(stage_window)
    row['response_opportunities'] = len(responses)
    statuses.update(state_edits.values())
    row['working_state_statuses'] = dict(statuses)
    row['working_state_edit_opportunities'] = sum(value for status, value in statuses.items()
        if status != 'NO_EXPLICIT_STATE_DELTA')
    row['state_observations'] = sum(statuses.values())
    row['sleep_in_progress'] = dict(reference=sleep_start, recipe=recipe,
        duration_so_far_seconds=round(now - sleep_start['mtime_unix'], 3)) if sleep_start else None
    fields = process.joinpath('stat').read_text().rsplit(')', 1)[1].split()
    row['native_identity_verified'] = (fields[19] == native['start_ticks']
        and process.stat().st_uid == row['uid'] and str(process.joinpath('cwd').resolve()) == native['cwd'])
    row['state_at_end'] = fields[0]
    if row.get('head', {}).get('kind') == 'RESPONSE' and row['raw_last10']:
        response_path = pathlib.Path(row['head']['path'])
        document = full_record(response_path)['document']
        stamp, clock = timestamp(document, row['head'], now)
        row['head'].update(age_seconds=max(0, now - stamp) if stamp is not None else None,
            timestamp_unix=stamp, timestamp_source=clock)
    return row


def main():
    output = []
    natives = [row for row in census if row.get('native')]
    for native in natives:
        try:
            output.append(audit_life(native))
        except (OSError, ValueError, KeyError, RuntimeError, IndexError) as error:
            reason = str(error)
            reason = reason if re.fullmatch(r'[A-Z][A-Z_0-9:]{0,95}', reason) else type(error).__name__
            output.append(dict(pid=native['pid'], physical=native['plan'].get('physical'),
                configured_root=native['plan'].get('root'), error_type=type(error).__name__,
                failure_reason=reason, bytes_read_at_failure=node_bytes,
                status='UNVERIFIED_READOUT', native_identity_verified=False))
    print(json.dumps(dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        native_count=len(natives), lives=output, bytes_read=node_bytes,
        elapsed_seconds=time.monotonic() - started,
        unclassified_native=[dict(pid=row['pid'], entrypoints=row['entrypoints']) for row in census
            if not row.get('native') and any('native' in entry for entry in row['entrypoints'])])))


if __name__ == '__main__':
    main()
