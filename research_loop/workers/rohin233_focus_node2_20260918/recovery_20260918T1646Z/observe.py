"""Current-incarnation receipts only; no transcript or judge payload export."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time

from recover import TARGETS, locations, read, require, sha


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def utc(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def header(path):
    with path.open('rb') as stream:
        stream.seek(max(0, path.stat().st_size - 4096))
        tail = stream.read()
    position = tail.rfind(b',"index":')
    require(position >= 0, 'canonical_journal_layout')
    return json.loads(b'{' + tail[position + 1:])


def checked(path):
    require(not path.is_symlink() and path.stat().st_size < 32 * 1024**2, 'bounded_source_record')
    record = read(path)
    require(hashlib.sha256(canonical({key: value for key, value in record.items() if key != 'sha256'})).hexdigest()
        == record['sha256'], 'actual_source_record_hash')
    return record


def observation(name):
    root, _, control, _ = locations(name)
    plan = read(control / 'PLAN.json')
    directory = root / 'raw/stream/records'
    paths = sorted(directory.glob('[0-9]' * 20 + '.json'))
    heads = [header(path) for path in paths[-256:]]
    matches = []
    for process in Path('/proc').glob('[0-9]*'):
        try:
            command = (process / 'cmdline').read_bytes()
            arguments = command.split(b'\0')
            if b'native' not in arguments or str(control / 'GUARD.json').encode() not in arguments:
                continue
            fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
            matches.append(dict(pid=int(process.name), start_ticks=int(fields[19]), state=fields[0],
                uid=process.stat().st_uid, command_sha256=hashlib.sha256(command).hexdigest()))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    require(len(matches) <= 1, 'no_duplicate_native_for_recovery_guard')
    loaded = None
    for metadata in reversed(heads):
        if metadata['kind'] == 'LOADED':
            record = checked(directory / f'{metadata["index"]:020d}.json')
            if matches and record['document']['pid'] == matches[0]['pid']:
                loaded = record
                break
    result = dict(observed_utc=utc(time.time()), arm=name, physical_gpu=plan['physical'], gpu_uuid=plan['gpu_uuid'],
        native=matches[0] if matches else None, status='LOADED' if loaded else 'STARTING' if matches else 'NOT_RUNNING',
        original_journal_id=TARGETS[name][4], head=heads[-1],
        hard_end_utc=utc(plan['hard_end_unix']), lease_end_utc=utc(plan['lease_end_unix']),
        semantic_policies=[scope.get('learn_row_policy') for scope in (plan, plan['think_act_learn'])],
        raw_text_exported=False, judge_content_or_scores_exported=False)
    if not loaded:
        return result
    doc = loaded['document']
    boot = next(int(line.split()[1]) for line in Path('/proc/stat').read_text().splitlines() if line.startswith('btime '))
    started = boot + matches[0]['start_ticks'] / os.sysconf('SC_CLK_TCK')
    require(loaded['journal_id'] == TARGETS[name][4] and doc['loaded_unix'] >= started - 2,
        'same_journal_current_native_loaded_after_start')
    recovery = read(control / 'RECOVERY.json')
    result.update(loaded=dict(index=loaded['index'], sha256=loaded['sha256'], loaded_utc=utc(doc['loaded_unix']),
        adapter_sha256=doc['adapter_sha256'], optimizer_steps=doc['optimizer_steps'], resume=doc['resume']),
        outage_seconds=doc['loaded_unix'] - recovery['old_outer_exit']['finished_unix'],
        checkpoint_cycle=recovery['complete_cycle'], saved_state_sha256=recovery['saved_state_sha256'])
    current = [item for item in heads if item['index'] > loaded['index']]
    requests = [checked(directory / f'{item["index"]:020d}.json') for item in current if item['kind'] == 'REQUEST']
    result['requests'] = [dict(index=record['index'], sha256=record['sha256'],
        started_utc=utc(record['document']['started_unix']), prompt_tokens=record['document']['prompt_tokens'])
        for record in requests[:3]]
    responses = {}
    acts = []
    for metadata in current:
        if metadata['kind'] not in ('RESPONSE', 'R184_STAGE', 'SLEEP_RECIPE'):
            continue
        record = checked(directory / f'{metadata["index"]:020d}.json')
        doc = record['document']
        if record['kind'] == 'RESPONSE':
            responses[hashlib.sha256(canonical(doc)).hexdigest()] = record
        elif record['kind'] == 'R184_STAGE' and doc.get('stage') == 'ACT' and doc['source_sha256'] in responses:
            response = responses[doc['source_sha256']]
            acts.append(dict(index=response['index'], sha256=response['sha256'], stage_index=record['index'],
                stage_sha256=record['sha256'], finished_utc=utc(response['document']['finished_unix']),
                raw_sha256=hashlib.sha256(response['document']['response']['raw'].encode()).hexdigest()))
        elif record['kind'] == 'SLEEP_RECIPE':
            result['sleep_recipe'] = dict(index=record['index'], sha256=record['sha256'],
                learn_row_policy=doc.get('learn_row_policy'), active_semantic_filters=doc.get('active_semantic_filters'),
                semantic_row_exclusion=doc.get('semantic_row_exclusion'))
    result['actual_acts'] = acts[:3]
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('name', choices=tuple(TARGETS))
    options = parser.parse_args()
    print(json.dumps(observation(options.name), indent=2, sort_keys=True))
