"""Read only operational parent receipts; never expose generated or sealed text."""

import argparse
import hashlib
import json
from pathlib import Path
import time


HERE = Path(__file__).resolve().parent


def observe(root):
    rows = []
    for directory in sorted((root / 'parents').glob('physical*')):
        binding = json.loads((directory / 'BINDING.json').read_text())
        row = dict(physical=binding['physical'], active_host_root=binding['row']['active_host_root'],
                   statuses={}, registered_deliveries=0, calls=[])
        spawned = directory / 'SPAWNED.json'
        if spawned.exists():
            identity = json.loads(spawned.read_text())['identity']
            process = Path('/proc', str(identity['pid']))
            try:
                fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
                argv = (process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
                row.update(pid=identity['pid'], alive=fields[0] != 'Z' and fields[19] == identity['ticks']
                    and argv == identity['argv'], state=fields[0])
            except FileNotFoundError:
                row.update(pid=identity['pid'], alive=False)
        for attempt in sorted((directory / 'parent').glob('parent_*')):
            result_path = attempt / 'RESULT.json'
            if not result_path.exists():
                row['calls'].append(dict(attempt=attempt.name, status='PENDING'))
                continue
            result = json.loads(result_path.read_text())
            status = result['status']
            row['statuses'][status] = row['statuses'].get(status, 0) + 1
            call = {key: result.get(key) for key in ('status', 'actual_model', 'source_response_count',
                'schedule_count', 'started_unix', 'finished_unix', 'error_type', 'error_code')}
            call.update(attempt=attempt.name, result_path=str(result_path),
                        result_sha256=hashlib.sha256(result_path.read_bytes()).hexdigest())
            delivered = attempt / 'DELIVERED.json'
            if delivered.exists():
                delivery = json.loads(delivered.read_text())
                call['registered_consumption'] = delivery['consumption']
                row['registered_deliveries'] += 1
            row['calls'].append(call)
        rows.append(row)
    return dict(schema='R179_NODE3_PARENT_METADATA_V1', observed_unix=time.time(), rows=rows,
                registration_not_verified_rendered_exposure=True, sealed_files_opened=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = observe(HERE)
    with args.output.open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    print(json.dumps({**result, 'rows': [{key: row.get(key) for key in
        ('physical', 'pid', 'alive', 'statuses', 'registered_deliveries')} for row in result['rows']]}))


if __name__ == '__main__':
    main()
