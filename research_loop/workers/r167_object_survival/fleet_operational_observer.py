"""Report operational metadata without opening sealed responses or annotations."""

import json
import os
from pathlib import Path
import time


ROOT = Path('/localhome/local-rohing/orch_r167_fleet_20260917_generation2')


def read(path):
    return json.loads(path.read_bytes())


def live(identity):
    try:
        fields = (Path('/proc') / str(identity['pid']) / 'stat').read_text().rsplit(')', 1)[1].split()
        boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        return fields[0] != 'Z' and fields[19] == str(identity['start_ticks']) and boot == identity['boot_id']
    except (FileNotFoundError, ProcessLookupError):
        return False


def observe(root=ROOT):
    reservations = [read(path) for path in (root / 'ledger').glob('*.RESERVED.json')]
    for row in reservations:
        config = read(Path(row['execution']['path']))
        row.update(condition=config['condition'], life_id=config['life_id'], sleep=config['sleep'])
    conditions = {}
    for condition in ('LORA_ON', 'LORA_OFF'):
        jobs = [row for row in reservations if row['condition'] == condition]
        completed = [row for row in jobs if (root / 'ledger' / (row['key'] + '.COMPLETE.json')).exists()]
        failed = [row for row in jobs if (root / 'ledger' / (row['key'] + '.FAILED.json')).exists()]
        responses = sum(len(list((root / 'attempts' / row['key'] / 'sealed').glob('*.RAW.private.json'))) for row in jobs)
        conditions[condition] = dict(reserved_jobs=len(jobs), calls_charged=3 * len(jobs),
            completed_jobs=len(completed), completed_job_calls=3 * len(completed), failed_jobs=len(failed),
            initial_completed_jobs=sum(row['sleep'] == 0 for row in completed),
            prospective_sleep_completed_jobs=sum(row['sleep'] > 0 for row in completed),
            response_files=responses, unterminated_jobs=len(jobs) - len(completed) - len(failed))
    completed_conditions = {}
    for row in reservations:
        if (root / 'ledger' / (row['key'] + '.COMPLETE.json')).exists():
            completed_conditions.setdefault((row['life_id'], row['sleep']), set()).add(row['condition'])
    blocks = []
    for path in root.glob('gpu_operation*/PHYSICAL*.BLOCKED.json'):
        record = read(path)
        blocks.append(dict(artifact=str(path), status=record['status'], key=record['key'],
            error_type=record['error_type'], error_class=record['error_class']))
    stage = root / 'gpu_takeover_20260917t1403z'
    launch = stage / 'CONTROLLER_LAUNCH.json'
    controller = read(launch) if launch.exists() else None
    controllers = []
    for name in ('gpu_takeover_20260917t1403z', 'gpu_unused_off_generation1'):
        path = root / name / 'CONTROLLER_LAUNCH.json'
        if path.exists():
            record = read(path)
            controllers.append(dict(stage=name, identity=record['identity'], live=live(record['identity'])))
    result = dict(status='OPERATIONAL_METADATA_ONLY', observed_unix=time.time(),
        controller_live=live(controller['identity']) if controller else False,
        controller_identity=controller['identity'] if controller else None,
        controllers=controllers,
        registered_lives=len(list((root / 'lives').glob('*/REGISTERED.json'))),
        receiving_checkpoints=len(list((root / 'receiving_transfers').glob('*/COMPLETE.json'))),
        incomplete_transfers=sum(not (path.parent / 'COMPLETE.json').exists()
            for path in (root / 'receiving_transfers').glob('*/ONCE.json')),
        conditions=conditions, calls_charged=sum(row['calls_charged'] for row in reservations),
        matched_completed_checkpoints=sum(value == {'LORA_ON', 'LORA_OFF'} for value in completed_conditions.values()),
        tokens_charged=sum(row['tokens_charged'] for row in reservations),
        completed_jobs=len(list((root / 'ledger').glob('*.COMPLETE.json'))),
        failed_jobs=len(list((root / 'ledger').glob('*.FAILED.json'))),
        unresolved_attempts=len(list((root / 'attempts').glob('*/UNRESOLVED.json'))),
        dispatch_errors=len(list((root / 'launches').glob('*/DISPATCH_ERROR.json'))),
        admission_refusals=len(list((root / 'attempts').glob('*/REFUSED.json'))),
        released_jobs=len(list(root.glob('gpu_operation*/*.RELEASED.json'))),
        blocked_slots=blocks, window_ended_slots=len(list(root.glob('gpu_operation*/PHYSICAL*.WINDOW_END.json'))),
        hard_end_unix=1789659000, provider_launch=False, sealed_content_read=False,
        evidence_root=str(root), runtime=str(stage / 'RUNTIME.json'))
    return result


def main():
    os.umask(0o077)
    result = observe()
    directory = ROOT / 'takeover_observations'
    directory.mkdir(mode=0o700, exist_ok=True)
    path = directory / (str(time.time_ns()) + '.json')
    result['evidence_path'] = str(path)
    with path.open('x') as stream:
        json.dump(result, stream, sort_keys=True)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
