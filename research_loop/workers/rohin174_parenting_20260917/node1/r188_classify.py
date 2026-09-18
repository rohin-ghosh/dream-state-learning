"""Bounded metadata-only NODE1 sleep and process classification."""

import hashlib
import json
from pathlib import Path
import re
import time


LABELS = ('teach_replay', 'teach_perception', 'teach_parenting', 'classroom_brain', 'classroom_creative', 'classroom_support')
charged = 0


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path, cap=64 * 1024 * 1024):
    global charged
    metadata = path.lstat()
    assert not path.is_symlink() and metadata.st_size <= cap
    charged += metadata.st_size
    assert charged <= 128 * 1024 * 1024
    raw = path.read_bytes()
    assert len(raw) == metadata.st_size and path.stat().st_mtime_ns == metadata.st_mtime_ns
    return json.loads(raw)


def main():
    global charged
    rows = []
    for label in LABELS:
        root = Path('/localhome/local-rohing/orch_r136_a100_' + label + '_20260916_attempt1/run1')
        paths = sorted(path for path in (root / 'stream/records').iterdir() if re.fullmatch(r'[0-9]{20}\.json', path.name))
        row = dict(life=label, root=str(root), head=int(paths[-1].stem), head_mtime=paths[-1].stat().st_mtime)
        selected, updates = {}, []
        for path in paths[-400:]:
            size = path.stat().st_size
            length = min(size, 4096)
            charged += length
            assert charged <= 128 * 1024 * 1024
            with path.open('rb') as stream:
                stream.seek(size - length)
                tail = stream.read(length)
            marker = list(re.finditer(rb',\s*"index"\s*:', tail))[-1]
            metadata = json.loads(b'{' + tail[marker.start() + 1:])
            if metadata['kind'] in ('SLEEP_COMPLETE', 'SLEEP_REQUEST', 'SLEEP_RECIPE', 'LOADED'):
                selected[metadata['kind']] = path
            if metadata['kind'] == 'UPDATE':
                updates.append(path)
        for kind, path in list(selected.items()) + [('update' + str(index), path) for index, path in enumerate(updates[-8:])]:
            record = read(path)
            assert record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'})
            document = record['document']
            item = dict(index=record['index'], mtime=path.stat().st_mtime, sha256=record['sha256'], keys=list(document))
            for key in ('cycle', 'update', 'update_index', 'step', 'steps', 'total_updates', 'total_steps', 'new_rows',
                        'available_old_rows', 'selected_old_rows', 'new_presentations', 'optimizer_step', 'optimizer_steps', 'total_optimizer_steps', 'source_root', 'policy', 'status'):
                if key in document:
                    item[key] = document[key]
            if kind in ('SLEEP_REQUEST', 'SLEEP_COMPLETE', 'LOADED') and 'resume_state' in document:
                envelope = document['resume_state']
                state = envelope['state']
                assert envelope['sha256'] == digest(state)
                item.update(state_sha256=envelope['sha256'], rows=len(state['rows']), sleep_frontier=state['sleep_frontier'])
                if state.get('pending'):
                    pending = state['pending']
                    item['pending_metadata'] = ({key: value for key, value in pending.items() if isinstance(value, (int, float, bool)) or key in ('kind', 'status')}
                        if isinstance(pending, dict) else pending)
            row[kind] = item
        rows.append(row)
    roots = {row['root']: row for row in rows}
    for process in Path('/proc').iterdir():
        if not process.name.isdecimal():
            continue
        try:
            args = [part.decode() for part in (process / 'cmdline').read_bytes().split(b'\0') if part]
            if 'native' not in args or '--config' not in args or args[0] == 'timeout':
                continue
            configpath = Path(args[args.index('--config') + 1])
            if not str(configpath).startswith('/localhome/local-rohing/orch_'):
                continue
            config = read(configpath, 4 * 1024 * 1024)
            planpath = Path(config['plan_path'])
            plan = read(planpath, 1024 * 1024)
            if plan['root'] not in roots:
                continue
            before = (process / 'stat').read_text().rsplit(')', 1)[1].split()
            after = (process / 'stat').read_text().rsplit(')', 1)[1].split()
            assert before[19] == after[19]
            roots[plan['root']].setdefault('natives', []).append(dict(pid=int(process.name), start_ticks=after[19], state=after[0],
                config=str(configpath), source=plan['source_root'], rehearsal_presentations=plan.get('rehearsal_presentations'),
                new_presentations=plan.get('new_presentations'), hard_end_unix=plan['hard_end_unix']))
        except (OSError, KeyError, ValueError):
            continue
    print(json.dumps(dict(observed_unix=time.time(), lives=rows, bytes_charged=charged, sealed_reads=0)))


if __name__ == '__main__':
    main()
