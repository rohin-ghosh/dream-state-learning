"""Assemble lease-bound evidence without counting dispatch as native restoration."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORKERS = REPO / 'research_loop/workers'
WRAPPERS = dict(node2='ovx', node3='ovx2', node4='a40r', node5='ovx3', ovx4='ovx4')
HORIZONS = dict(node2='2026-09-20T18:00:00+00:00', node3='2026-09-24T18:00:00+00:00',
    node4='2026-09-25T18:00:00+00:00', node5='2026-09-20T18:00:00+00:00', ovx4='2026-09-30T18:00:00+00:00')


def utc(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


def verified(row):
    try:
        actual = datetime.fromisoformat(row['resident_deadline_utc']).timestamp()
        target = datetime.fromisoformat(row['target_deadline_utc']).timestamp()
    except (KeyError, TypeError, ValueError):
        return False
    return bool(0 <= target - actual <= 60 and row.get('loaded_index') is not None and row.get('wall_index') is not None
        and row.get('resident_deadline_utc') and row.get('alive_now') is True
        and row.get('identity_matches') is True)


def collect():
    sources, rows, supports = [], [], []

    def read(path):
        raw = path.read_bytes()
        value = json.loads(raw)
        reference = dict(path=str(path.relative_to(REPO)), sha256=hashlib.sha256(raw).hexdigest())
        sources.append(reference)
        return value, reference

    def add(life, node, gpu, status, native, loaded, wall, deadline, reference, gap=None):
        rows.append(dict(life=life, node=node, gpu=gpu, source_status=status,
            pid=(native or {}).get('pid'), start_ticks=(native or {}).get('start_ticks'),
            loaded_index=(loaded or {}).get('index'), wall_index=(wall or {}).get('index'),
            resident_deadline_utc=deadline if loaded and wall else None,
            target_deadline_utc=HORIZONS[node], recorded_reload_gap_seconds=gap, evidence=reference))

    node3, reference = read(WORKERS / 'rohin233_focus_node3_20260918/DEADLINES.json')
    for entry in node3['lives']:
        add(entry['life'], 'node3', entry['gpu'], entry['status'], entry.get('actual_native'),
            entry.get('LOADED'), entry.get('WALL_EXTENDED'), entry.get('resident_deadline_utc'), reference,
            (entry.get('boundary_handoff') or {}).get('observed_reload_gap_seconds'))
    for name in ('Tool_feedback_projection', 'fifth_caption_parent', 'local_model_parent', 'math_debate', 'parent_classroom'):
        component = node3[name]
        supports.append(dict(component=name, node='local' if name == 'local_model_parent' else 'node3',
            pid=component.get('pid'), status=component.get('status'),
            deadline_utc=component.get('end_utc'), evidence=reference))

    node2 = WORKERS / 'rohin233_focus_node2_20260918/recovery_20260918T1646Z'
    for life, filename in (('C0', 'C0_CONTINUATION_LOADED.public.json'),
                           ('Astra7', 'ASTRA7_CONTINUATION_LOADED.public.json'),
                           ('caption_node2', 'CAPTION_CURRENT_LEASE.public.json')):
        entry, reference = read(node2 / filename)
        add(life, 'node2', entry['physical_gpu'], entry['status'], entry.get('native'),
            entry.get('loaded'), entry.get('wall_extended'), entry.get('hard_end_utc'), reference,
            entry.get('outage_seconds'))
    node2_table, reference = read(node2 / 'RENEWAL_TABLE.public.json')
    for entry in node2_table['lives'].values():
        parent = entry.get('parent', {})
        service = parent.get('service', parent.get('capacity', {}).get('service'))
        if service:
            supports.append(dict(component=entry['arm'] + '_parent',
                node='node2' if entry['arm'] == 'C0' else 'local',
                pid=service['pid'], start_ticks=service['start_ticks'],
                status='SCRIPTED_CURRICULUM' if entry['arm'] == 'C0' else 'MODEL_PARENT',
                deadline_utc=utc(service['deadline_unix']), evidence=reference))

    pair, reference = read(WORKERS / 'rohin231_curriculum_birth_20260918/recovery_20260918T1646Z/CURRENT_CONTINUATION.json')
    for entry in pair['observations']:
        loaded = entry.get('loaded', [])[-1:]
        wall = entry.get('wall_extended', [])[-1:]
        native = next((process for process in entry.get('native_processes', [])
            if loaded and process['pid'] == loaded[0]['pid']), loaded[0] if loaded else None)
        deadline = utc(wall[0]['authorization']['new_deadline_unix']) if wall else None
        gap = None
        if loaded and entry.get('exit_boundary', {}).get('observed_exit_unix'):
            gap = loaded[0]['loaded_unix'] - entry['exit_boundary']['observed_exit_unix']
        add('curriculum_learner' if entry['physical'] == 0 else 'curriculum_frozen_sibling',
            'ovx4', entry['physical'], entry['status'], native, loaded[0] if loaded else None,
            wall[0] if wall else None, deadline, reference, gap)
    for name, entry in pair['parents'].items():
        supports.append(dict(component='curriculum_' + name + '_parent', node='local',
            pid=entry.get('pid'), status='OWNER_VERIFIED_PROCESS',
            deadline_utc=utc(entry['expiry_unix']), evidence=reference))

    node4, reference = read(WORKERS / 'rohin233_recovery_node4_20260918/DEADLINES.json')
    for entry in node4['components']:
        name = entry['component']
        if name in ('P7', 'C2'):
            live_reference = reference
            receipt_path = WORKERS / 'rohin233_recovery_node4_20260918/NATIVE_CONTINUATION.public.json'
            if name == 'P7' and receipt_path.is_file():
                newer, newer_reference = read(receipt_path)
                if newer.get('status') == 'WALL_EXTENDED_AND_LOADED' and newer['guard_sha256'] == entry['guard_sha256']:
                    entry = dict(entry, loaded=newer['loaded'], wall_extended=newer['wall_extended'],
                        native=newer['native'], status=newer['status'],
                        recorded_exit_to_loaded_seconds=newer['reload_gap_seconds'])
                    live_reference = newer_reference
            add(name, 'node4' if name == 'P7' else 'node5', 7 if name == 'P7' else 1,
                entry['status'], entry.get('native'), entry.get('loaded'), entry.get('wall_extended'),
                entry.get('hard_end_utc'), live_reference, entry.get('recorded_exit_to_loaded_seconds'))
        else:
            supports.append(dict(component=name, node='node2' if name == 'ASTRA7_TRANSPORT' else 'local',
                pid=entry.get('pid', entry.get('native_pid')), status=entry['status'],
                deadline_utc=entry.get('hard_end_utc'), evidence=reference))

    p3, reference = read(HERE / 'P3_FINISH_STATUS.json')
    entry = p3.get('native', p3.get('evidence', {}))
    add('P3', 'node4', 3, entry.get('status', p3['status']), entry.get('native'),
        entry.get('loaded'), entry.get('wall_extended'), entry.get('actual_deadline_utc'), reference,
        entry.get('recorded_exit_to_loaded_seconds'))
    if p3.get('parent'):
        supports.append(dict(component='P3_parent', node='local', pid=p3['parent']['pid'],
            status=p3['status'], deadline_utc=utc(p3['parent']['hard_end_unix']), evidence=reference))
    else:
        supports.append(dict(component='P3_parent', node='local', pid=None,
            status='NOT_RUNNING_WAITING_FOR_NATIVE_LOAD', deadline_utc=None, evidence=reference))

    services = WORKERS / 'rohin233_ovx4_recovery_20260918'
    base, reference = read(services / 'LEASE_FLEET_CUT_1757.json')
    entry = base['base_loaded']
    rows.append(dict(life='frozen_base_player', node='ovx4', gpu=entry['physical'],
        source_status='LEASE_CONTINUATION_LOADED', pid=entry['pid'], start_ticks=None,
        loaded_unix=entry['unix'],
        loaded_index='SERVICE_LOAD', wall_index='LEASE_ADMITTED',
        resident_deadline_utc=utc(entry['deadline_unix']), target_deadline_utc=HORIZONS['ovx4'],
        recorded_reload_gap_seconds=None, evidence=reference))
    for name in ('SHARED2', 'SHARED3', 'BASE', 'P3'):
        value, reference = read(services / f'JUDGE_{name}_ADOPTED.json')
        entry = value['actual_loaded']
        supports.append(dict(component=name + '_scorer', node='node4' if name == 'P3' else 'ovx4',
            pid=entry['pid'], status=value['status'], deadline_utc=utc(entry['deadline_unix']),
            primary_step=entry['primary_step'], primary_rank=entry['primary_rank'], evidence=reference))
    return rows, supports, sources


def census(node, rows):
    identifiers = sorted({row['pid'] for row in rows if row['node'] == node and row.get('pid')})
    code = '''import hashlib,json,os,time
from pathlib import Path
results={}
boot_unix=int(next(line.split()[1] for line in Path('/proc/stat').read_text().splitlines() if line.startswith('btime ')))
for pid in json.load(__import__('sys').stdin):
    path=Path('/proc')/str(pid)
    try:
        fields=path.joinpath('stat').read_text().rsplit(') ',1)[1].split()
        results[str(pid)]=dict(alive=fields[0]!='Z',state=fields[0],start_ticks=fields[19],started_unix=boot_unix+int(fields[19])/os.sysconf('SC_CLK_TCK'),command_sha256=hashlib.sha256(path.joinpath('cmdline').read_bytes()).hexdigest())
    except FileNotFoundError:
        results[str(pid)]=dict(alive=False)
print(json.dumps(dict(observed_unix=time.time(),processes=results)))'''
    result = subprocess.run(['bash', str(REPO / f'gpu/{WRAPPERS[node]}_ssh.sh'),
        'python3 -c ' + shlex.quote(code)], input=json.dumps(identifiers), capture_output=True,
        text=True, timeout=40)
    if result.returncode:
        return node, dict(error='READ_ONLY_PROCESS_CENSUS_FAILED')
    return node, json.loads(result.stdout)


def main():
    rows, supports, sources = collect()
    with ThreadPoolExecutor(max_workers=5) as executor:
        observations = dict(executor.map(lambda node: census(node, rows + supports), WRAPPERS))
    for row in rows:
        process = observations[row['node']].get('processes', {}).get(str(row['pid']), {})
        row['alive_now'] = process.get('alive')
        identity = (str(row['start_ticks']) == process.get('start_ticks')) if row['start_ticks'] is not None else (
            row.get('loaded_unix') is not None and process.get('started_unix', float('inf')) <= row['loaded_unix'] + 1)
        row['identity_matches'] = bool(process.get('alive') and identity)
        row['renewal_verified'] = verified(row)
    stamp = datetime.now(timezone.utc).strftime('%H%M%S')
    result = dict(observed_utc=utc(time.time()), schema='R233_KEPT_FLEET_DEADLINES_V1',
        all_native_bounds_verified=all(row['renewal_verified'] for row in rows),
        all_support_components_verified=False,
        support_scope_note='Detailed supporting-component receipts linked; this aggregate does not infer unlisted support or fresh parent renders.',
        lives=rows, supporting_components=supports, source_receipts=sources, process_observations=observations,
        provider_expiry_independently_verified=False, lease_purchase_or_extension=False,
        uninterrupted_resident_continuity_claimed=False)
    path = HERE / f'DEADLINES_{stamp}.json'
    path.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    lines = [f'# Kept-fleet deadline evidence — {result["observed_utc"]}', '',
        '| Life | Node / GPU | Current process | Renewed native bound UTC | LOAD / WALL |',
        '| --- | --- | --- | --- | --- |']
    for row in rows:
        state = 'LOADED; alive' if row['renewal_verified'] else row['source_status']
        bound = row['resident_deadline_utc'] or 'PENDING; target ' + row['target_deadline_utc']
        lines.append(f'| {row["life"]} | {row["node"]} / {row["gpu"]} | {state} | {bound} | {row["loaded_index"]} / {row["wall_index"]} |')
    lines.extend(['', 'Dispatch/replay is not restoration. Actual reload gaps and source hashes are in the JSON.',
        'A running parent process is not proof of a rendered parent turn. Supporting-component coverage is explicitly incomplete.',
        'Existing user-reported lease dates, conservative safety margins; no lease purchase or provider-expiry assertion.'])
    path.with_suffix('.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps(dict(path=str(path.relative_to(REPO)), verified_lives=sum(row['renewal_verified'] for row in rows),
        total_lives=len(rows), pending=[row['life'] for row in rows if not row['renewal_verified']])))


if __name__ == '__main__':
    main()
