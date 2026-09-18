"""Metadata-only fixed-fleet coverage; never open responses, scores or TRAIN."""

import hashlib
import json
from pathlib import Path
import time


ROOT = Path('/localhome/local-rohing/orch_r167_fleet_20260917_generation2')
PLAN_HASH = '1b3e26dc333de5201d4f1f943726f44a5d44652ccc69d3b8872497acfa1282fc'
CONDITIONS = ('LORA_ON', 'LORA_OFF')


def read(path):
    return json.loads(path.read_bytes())


def bound(reference):
    path = Path(reference['path'])
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != reference['sha256']:
        raise ValueError('metadata_reference_changed')
    return json.loads(raw)


def identity_live(identity):
    try:
        directory = Path('/proc') / str(identity['pid'])
        fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
        return (fields[0] != 'Z' and fields[19] == str(identity['start_ticks'])
            and directory.stat().st_uid == identity['uid']
            and Path('/proc/sys/kernel/random/boot_id').read_text().strip() == identity['boot_id'])
    except (FileNotFoundError, ProcessLookupError):
        return False


def coverage(root, plan):
    started = time.time()
    rows = {}
    for life in plan['lives']:
        life_id = life['life_id']
        registration = root / 'lives' / life_id / 'REGISTERED.json'
        fixed = []
        if registration.exists():
            queue = bound(read(registration)['plan'])
            if queue['life_id'] != life_id or queue['sleep_count'] != 3:
                raise ValueError('fixed_registration_mismatch')
            fixed = [0, *range(queue['first_sleep'], queue['first_sleep'] + 3)]
        rows[life_id] = dict(life_id=life_id, node=life['node'], source_status=life['status'],
            hold=life.get('hold'), registered=registration.exists(), fixed_checkpoints=fixed,
            receiving_checkpoints=[], complete={condition: [] for condition in CONDITIONS},
            completed_calls={condition: 0 for condition in CONDITIONS},
            charged_calls=0, current=[], permanent_missing=[], attempted=[])
    for path in (root / 'receiving_transfers').glob('*/COMPLETE.json'):
        transfer = read(path)
        if transfer['life_id'] not in rows or transfer['status'] != 'EXACT_RECEIVING_COPY_VERIFIED':
            raise ValueError('unregistered_receiving_transfer')
        rows[transfer['life_id']]['receiving_checkpoints'].append(transfer['sleep'])
    current = []
    for path in (root / 'jobs').glob('*.CONFIG.json'):
        config = read(path)
        row = rows[config['life_id']]
        sleep, condition = config['sleep'], config['condition']
        if sleep not in row['fixed_checkpoints'] or condition not in CONDITIONS:
            raise ValueError('unregistered_job_configuration')
        key = path.name.removesuffix('.CONFIG.json')
        cell = dict(sleep=sleep, condition=condition, physical=config['physical'])
        row['attempted'].append(cell)
        reservation_path = root / 'ledger' / (key + '.RESERVED.json')
        complete_path = root / 'ledger' / (key + '.COMPLETE.json')
        failed_path = root / 'ledger' / (key + '.FAILED.json')
        attempt = root / 'attempts' / key
        if reservation_path.exists():
            reservation = read(reservation_path)
            if bound(reservation['execution']) != config or reservation['calls_charged'] != 3:
                raise ValueError('exact_three_call_reservation')
            row['charged_calls'] += reservation['calls_charged']
        if complete_path.exists():
            complete = read(complete_path)
            if complete['status'] != 'COMPLETE' or complete['calls'] != 3:
                raise ValueError('exact_completed_three_probe_job')
            if Path(complete['reservation']['path']) != reservation_path:
                raise ValueError('completion_reservation_join')
            bound(complete['reservation'])
            row['complete'][condition].append(sleep)
            row['completed_calls'][condition] += 3
        elif (attempt / 'REFUSED.json').exists():
            row['permanent_missing'].append(dict(cell, reason='ADMISSION_REFUSED_NO_RETRY'))
        elif failed_path.exists():
            row['permanent_missing'].append(dict(cell, reason='FAILED_CHARGED_NO_RETRY'))
        elif (attempt / 'UNRESOLVED.json').exists():
            row['permanent_missing'].append(dict(cell, reason='UNRESOLVED_NO_RETRY'))
        else:
            process_path = attempt / 'sealed/PROCESS.json'
            identity = read(process_path)['identity'] if process_path.exists() else None
            active = dict(cell, life_id=config['life_id'], charged=reservation_path.exists(),
                native_live=identity_live(identity) if identity else False,
                native_identity=identity, execution_path=str(path))
            row['current'].append(active)
            current.append(active)
    candidates = {condition: [] for condition in CONDITIONS}
    for row in rows.values():
        row['receiving_checkpoints'].sort()
        row['missing_captures'] = sorted(set(row['fixed_checkpoints']) - set(row['receiving_checkpoints']))
        for condition in CONDITIONS:
            row['complete'][condition].sort()
        row['matched_completed_checkpoints'] = sorted(set(row['complete']['LORA_ON']) & set(row['complete']['LORA_OFF']))
    for ordinal in range(4):
        for row in rows.values():
            if not row['fixed_checkpoints']:
                continue
            sleep = row['fixed_checkpoints'][ordinal]
            if sleep not in row['receiving_checkpoints']:
                continue
            for condition in CONDITIONS:
                if not any(cell['sleep'] == sleep and cell['condition'] == condition for cell in row['attempted']):
                    candidates[condition].append(dict(life_id=row['life_id'], sleep=sleep, condition=condition))
    controllers = []
    admission_cutoffs = []
    for stage, role in (('gpu_takeover_20260917t1403z', 'ON_PHYSICAL0'),
            ('gpu_unused_off_generation1', 'UNUSED_OFF_PHYSICAL1')):
        path = root / stage / 'CONTROLLER_LAUNCH.json'
        if path.exists():
            launch = read(path)
            runtime = bound(launch['runtime'])
            common = runtime['common']
            pipeline = bound(common['pipeline'])
            controller_path = Path(common['source_root']) / 'fleet_gpu_controller.py'
            if hashlib.sha256(controller_path.read_bytes()).hexdigest() != common['sources']['fleet_gpu_controller.py']:
                raise ValueError('actual_controller_source_changed')
            if pipeline['hard_end_unix'] != 1789659000 or pipeline['call_cap'] != 504:
                raise ValueError('fixed_execution_window_changed')
            admission_cutoffs.append(pipeline['hard_end_unix'] - common['max_job_seconds'] - 15)
            controllers.append(dict(role=role, identity=launch['identity'], live=identity_live(launch['identity']),
                evidence_path=str(path), runtime=launch['runtime'], actual_controller_source_verified=True,
                max_job_seconds=common['max_job_seconds'], hard_end_unix=pipeline['hard_end_unix']))
    return dict(status='R159_SAFE_PER_LIFE_R167_EXECUTION_COVERAGE', observed_unix=time.time(),
        snapshot_started_unix=started, scope_count=len(rows), source_admitted_count=sum(row['registered'] for row in rows.values()),
        lives=list(rows.values()), current_jobs=current, controllers=controllers,
        next_eligible={condition: cells[:1] for condition, cells in candidates.items()},
        eligible_unattempted_initial={condition: sum(cell['sleep'] == 0 for cell in cells) for condition, cells in candidates.items()},
        completed_jobs=sum(len(row['complete'][condition]) for row in rows.values() for condition in CONDITIONS),
        completed_calls=sum(sum(row['completed_calls'].values()) for row in rows.values()),
        charged_calls=sum(row['charged_calls'] for row in rows.values()),
        receiving_checkpoints=sum(len(row['receiving_checkpoints']) for row in rows.values()),
        matched_completed_checkpoints=sum(len(row['matched_completed_checkpoints']) for row in rows.values()),
        completed_future_sleep_jobs=sum(sum(sleep > 0 for sleep in row['complete'][condition])
            for row in rows.values() for condition in CONDITIONS),
        call_cap=504, generated_token_cap=258048, hard_end_unix=1789659000,
        last_full_job_admission_before_unix=min(admission_cutoffs) if admission_cutoffs else None,
        provider_calls=0, model_calls=0,
        score_or_response_content_read=False, TRAIN_content_read=False)


if __name__ == '__main__':
    plan_path = ROOT / 'control2/PLAN.json'
    if hashlib.sha256(plan_path.read_bytes()).hexdigest() != PLAN_HASH:
        raise ValueError('unchanged_generation2_plan_required')
    print(json.dumps(coverage(ROOT, read(plan_path)), sort_keys=True))
