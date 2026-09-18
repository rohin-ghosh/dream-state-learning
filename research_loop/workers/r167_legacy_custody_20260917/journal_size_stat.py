"""Stat-only TRAIN record accounting; no journal content reads or writes."""

import json
import os
from pathlib import Path
import re
import socket
import stat
import sys
import time


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def directory(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute_directory')
    descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for name in path.parts[1:]:
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def native_matches(expected):
    path = Path('/proc') / str(expected['pid'])
    fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
    require(fields[19] == str(expected['start_ticks']) and fields[0] not in ('Z', 'X'),
        'same_live_native')
    require(Path('/proc/sys/kernel/random/boot_id').read_text().strip() == expected['boot_id'],
        'same_boot')


def collect(root, completed_index):
    descriptor = directory(Path(root) / 'stream/records')
    try:
        before = os.fstat(descriptor)
        records, intents = {}, {}
        unknown, count = 0, 0
        with os.scandir(descriptor) as entries:
            for entry in entries:
                count += 1
                require(count <= 20000, '20000_entry_stat_cap')
                match = re.fullmatch(r'(\d{20})(\.intent)?\.json', entry.name)
                if not match:
                    unknown += 1
                    continue
                info = os.stat(entry.name, dir_fd=descriptor, follow_symlinks=False)
                require(stat.S_ISREG(info.st_mode), 'regular_TRAIN_file_only')
                index = int(match[1])
                target = intents if match[2] else records
                target[index] = info.st_size
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    stream = directory(Path(root) / 'stream')
    try:
        header = os.stat('JOURNAL.json', dir_fd=stream, follow_symlinks=False)
        require(stat.S_ISREG(header.st_mode), 'regular_JOURNAL_header')
    finally:
        os.close(stream)
    selected = list(range(completed_index + 1))
    require(all(index in records and index in intents for index in selected),
        'complete_names_through_verified_frontier')
    matched = set(records) & set(intents)
    prefix_record_bytes = sum(records[index] for index in selected)
    prefix_intent_bytes = sum(intents[index] for index in selected)
    prefix_bytes = header.st_size + prefix_record_bytes + prefix_intent_bytes
    full_bytes = header.st_size + sum(records.values()) + sum(intents.values())
    budget = 320 * 1024 * 1024
    return dict(directory_entries=count, other_name_count=unknown,
        journal_header_bytes=header.st_size, record_files=len(records), intent_files=len(intents),
        unpaired_record_count=len(set(records) - matched), unpaired_intent_count=len(set(intents) - matched),
        maximum_record_index=max(records) if records else None,
        completed_prefix=dict(last_index=completed_index, record_files=len(selected),
            record_bytes=prefix_record_bytes, intent_bytes=prefix_intent_bytes, total_bytes=prefix_bytes),
        full_observed=dict(record_bytes=sum(records.values()), intent_bytes=sum(intents.values()), total_bytes=full_bytes),
        proposed_budget_bytes=budget, completed_prefix_exceeds_320MiB=prefix_bytes > budget,
        full_observed_exceeds_320MiB=full_bytes > budget,
        completed_prefix_remaining_320MiB=budget-prefix_bytes,
        directory_changed_during_scan=(before.st_mtime_ns, before.st_ctime_ns) != (after.st_mtime_ns, after.st_ctime_ns),
        allocated_budget_changed=False, TRAIN_content_bytes_read=0,
        excludes='PLAN/COMMIT metadata, future growth, repeated reads and all adapter/model/optimizer bytes')


def observe(request):
    rows = []
    require(1 <= len(request['lives']) <= 6, 'bounded_lives')
    for life in request['lives']:
        row = dict(life_id=life['life_id'], node=request['node'], source_root=life['source_root'],
            observed_start_unix=time.time(), native_identity=life['native_identity'])
        try:
            require(life['node'] == request['node'] and life['node'] in ('ovx2', 'a100', 'a40r'),
                'assigned_nodes_only')
            native_matches(life['native_identity'])
            row.update(collect(life['source_root'], life['completed_boundary']['record']['index']))
            native_matches(life['native_identity'])
            row['status'] = 'STAT_ONLY_COMPLETE'
        except Exception as error:
            row.update(status='INCOMPLETE_STAT', error=dict(type=type(error).__name__, reason=str(error)))
        row['observed_end_unix'] = time.time()
        rows.append(row)
    return dict(hostname=socket.gethostname(), lives=rows, no_signals=True, no_writes=True,
        TRAIN_content_bytes_read=0)


if __name__ == '__main__':
    print(json.dumps(observe(json.loads(sys.argv[1])), sort_keys=True))
