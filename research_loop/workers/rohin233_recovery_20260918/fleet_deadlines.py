"""Assemble lease-bound evidence without counting dispatch as native restoration."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
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


def runtime_status(row):
    if row.get('renewal_verified'):
        return 'LOADED; alive'
    if row.get('alive_now') is False:
        return 'NOT ALIVE; prior receipt: ' + row['source_status']
    if row.get('alive_now') is True:
        if 'REPLAY' in row.get('source_status', '') and row.get('loaded_index') is None:
            return 'REPLAY PROCESS ALIVE; renewed LOAD not observed'
        return 'PROCESS ALIVE; renewal identity/bound unverified'
    if row.get('pid'):
        return 'CURRENT PROCESS NOT VERIFIED; prior receipt: ' + row['source_status']
    return row['source_status']


def checkpoint_tail_entry(entry, binding):
    if (binding.get('status') != 'LOADED' or binding.get('journal_id') != '260be8b8710a42559b291797c6e14983'
            or binding.get('complete_index') != 11502
            or binding.get('complete_sha256') != '9c59fe6c59a01948b6ffe894aaa681010346ccc671c2f774a10fe7399a49080f'
            or binding.get('optimizer_steps') != 7756
            or not 11502 < binding.get('wall_extended', {}).get('index', 0)
            < binding.get('loaded', {}).get('index', 0)):
        raise ValueError('exact_C2_checkpoint_tail_LOAD_binding_required')
    return dict(entry, loaded=binding['loaded'], wall_extended=binding['wall_extended'],
        native=binding['native'], status='CHECKPOINT_TAIL_LOADED',
        hard_end_utc=utc(binding['hard_end_unix']), guard_sha256=binding['guard_sha256'],
        recorded_exit_to_loaded_seconds=binding['loaded_unix']-1789756101.421838)


def support_row(entry, reference):
    return dict(component=entry['name'], node='local' if entry['actual_host_alias'] == 'operator_vm'
        else entry['actual_host_alias'], pid=entry.get('pid'), start_ticks=entry.get('start_ticks'),
        command_sha256=entry.get('command_sha256'), status=entry.get('status', 'OWNER_OBSERVED_LIVE'),
        deadline_utc=entry.get('actual_deadline'), execution_proof=entry.get('proof', []),
        deadline_mechanism=entry.get('deadline_mechanism'), source_admission=entry.get('source_admission'),
        evidence=reference)


def actual_parent_delivery(delivery, loaded_index, reference):
    if (delivery.get('status') != 'REQUEST_TO_COMMITTED_ACT_OBSERVED'
            or not loaded_index < delivery.get('request_index', 0)
            < delivery.get('act_index', 0) < delivery.get('committed_index', 0)):
        return None
    return dict(status='PARENT_REQUEST_TO_COMMITTED_ACT',loaded_index=loaded_index,
        request_index=delivery['request_index'],act_index=delivery['act_index'],
        inbox_id=delivery['inbox_id'],evidence=reference)


def annotate_support(row, observation, observed_unix):
    process = observation.get('processes', {}).get(str(row.get('pid')), {})
    row['alive_now'] = process.get('alive')
    ticks_match = row.get('start_ticks') is not None and str(row['start_ticks']) == process.get('start_ticks')
    command_match = not row.get('command_sha256') or row['command_sha256'] == process.get('command_sha256')
    row['identity_matches'] = bool(process.get('alive') and ticks_match and command_match)
    try:
        deadline = datetime.fromisoformat(row['deadline_utc']).timestamp()
    except (KeyError, TypeError, ValueError):
        deadline = None
    row['future_bound_observed'] = deadline is not None and deadline > observed_unix
    row['runtime_identity_and_bound_verified'] = row['identity_matches'] and row['future_bound_observed']
    row['parent_delivery_inferred'] = False


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
            pid=component.get('pid'), start_ticks=component.get('start_ticks'),
            command_sha256=component.get('command_sha256'), status=component.get('status'),
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
            fast_path = WORKERS / 'rohin233_recovery_node4_20260918/C2_CHECKPOINT_TAIL_LOADED.json'
            if name == 'C2' and fast_path.is_file():
                binding, live_reference = read(fast_path)
                entry = checkpoint_tail_entry(entry, binding)
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
                pid=entry.get('pid', entry.get('native_pid')), start_ticks=entry.get('start_ticks'), status=entry['status'],
                deadline_utc=entry.get('hard_end_utc'), evidence=reference))

    retry_status = HERE / 'P3_RETRY_STATUS.json'
    p3, reference = read(retry_status if retry_status.is_file() else HERE / 'P3_FINISH_STATUS.json')
    entry = p3.get('native', p3.get('evidence', {}))
    if retry_status.is_file() and (HERE / 'P3_RETRY_LOADED.json').is_file():
        entry, reference = read(HERE / 'P3_RETRY_LOADED.json')
    deadline = entry.get('actual_deadline_utc')
    if (entry.get('wall_extended') or {}).get('deadline_unix') is not None:
        deadline = utc(entry['wall_extended']['deadline_unix'])
    add('P3', 'node4', 3, entry.get('status', p3['status']), entry.get('native'),
        entry.get('loaded'), entry.get('wall_extended'), deadline, reference,
        entry.get('recorded_exit_to_loaded_seconds'))
    if not p3.get('parent') and (HERE / 'P3_RETRY_WAITER_STARTED.json').is_file():
        waiter, waiter_reference = read(HERE / 'P3_RETRY_WAITER_STARTED.json')
        supports.append(dict(component='P3_retry_parent_waiter', node='local', pid=waiter['pid'],
            start_ticks=waiter['start_ticks'], deadline_utc=utc(waiter['hard_end_unix']),
            status='WAITING_VERIFIED_RETRY_LOAD_NOT_A_PARENT', evidence=waiter_reference))
    if p3.get('parent'):
        supports.append(dict(component='P3_parent', node='local', pid=p3['parent']['pid'],
            start_ticks=p3['parent'].get('start_ticks'),
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
    parent_deliveries = {}
    parent_path = WORKERS / 'rohin233_focus_node3_20260918/FOLLOWUP_CURRENT.json'
    if parent_path.is_file():
        followup, reference = read(parent_path)
        for entry in followup['rows']:
            chain = entry.get('latest_completed_model_parent', {})
            act = chain.get('actual_ACT_after_parent', {})
            if act:
                parent_deliveries[entry['life']] = dict(status='MODEL_PARENT_REQUEST_TO_ACT',
                    loaded_index=entry['LOADED']['index'], request_index=act['ACT_REQUEST']['index'],
                    act_index=act['ACT']['index'], observed_utc=followup['parent_cut_utc'], evidence=reference)
    pair_path = WORKERS / 'rohin231_curriculum_birth_20260918/recovery_20260918T1646Z/CURRENT_CONTINUATION.json'
    pair, reference = read(pair_path)
    for name, entry in pair.get('post_LOAD_parent_bindings', {}).items():
        life = 'curriculum_frozen_sibling' if name == 'frozen' else 'curriculum_learner'
        parent_deliveries[life] = dict(status='MODEL_PARENT_REQUEST_TO_ACT',
            request_index=entry['render_request_index'], act_index=entry['act_response_index'],
            observed_utc=entry['observed_utc'], evidence=reference)
    node2_table, reference = read(node2 / 'RENEWAL_TABLE.public.json')
    for entry in node2_table['lives'].values():
        parent = entry.get('parent', {})
        if entry['arm'] == 'C0' and parent.get('fresh_post_renewal_turn'):
            turn = parent['fresh_post_renewal_turn']
            parent_deliveries['C0'] = dict(status='SCRIPTED_CURRICULUM_REQUEST_TO_RESPONSE',
                request_index=turn['render']['index'], act_index=turn['actual_response']['index'], evidence=reference)
        elif entry['arm'] == 'CAPTION' and parent.get('render') and parent.get('answer'):
            parent_deliveries['caption_node2'] = dict(status='MODEL_PARENT_RENDER_AND_FOLLOWING_ACT',
                detail=parent['answer'], evidence=reference)
    parent_path = WORKERS / 'rohin233_recovery_node4_20260918/CONTINUED_PARENT_RENDER.json'
    if parent_path.is_file():
        parent, reference = read(parent_path)
        parent_deliveries['P7'] = dict(status=parent['status'], loaded_index=parent['loaded_index'],
            request_index=parent['request']['index'], response_index=parent['response']['index'], evidence=reference)
    p3_path = HERE/'P3_RETRY_ACTUAL.json'
    if p3_path.is_file():
        parent, reference = read(p3_path)
        for turn in parent.get('parent_turns', []):
            delivery = actual_parent_delivery(turn.get('delivery', {}), parent['loaded_index'], reference)
            if delivery is not None:
                parent_deliveries['P3'] = delivery
    c2_delivery = WORKERS/'rohin233_recovery_node4_20260918/CHECKPOINT_TAIL_V_DELIVERY.json'
    if c2_delivery.is_file():
        parent, reference = read(c2_delivery)
        if parent.get('first_render') is not None:
            parent_deliveries['C2'] = dict(status='SOURCE_GROUNDED_PARENT_REQUEST_RENDERED',
                loaded_index=parent['native']['loaded_index'],detail=parent['first_render'],
                following_ACT=parent.get('first_ACT'),evidence=reference)
    for row in rows:
        row['parent_delivery'] = parent_deliveries.get(row['life'], dict(status='NOT_ESTABLISHED_IN_THIS_AGGREGATE'))
    support_path = services / 'SUPPORT_COMPONENT_TABLE.json'
    if support_path.is_file():
        table, reference = read(support_path)
        supports.extend(support_row(entry, reference) for entry in table['rows'])
    hourly_path=HERE/'CAPTION_HOURLY_STARTED.json'
    if hourly_path.is_file():
        hourly, reference=read(hourly_path)
        supports.append(dict(component='adopted_epoch_hourly_collector',node='local',pid=hourly['pid'],
            start_ticks=hourly['start_ticks'],deadline_utc=utc(hourly['until_unix']),
            status='SINGLE_OWNER_AGGREGATE_ONLY_COLLECTOR',evidence=reference))
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
    command = [sys.executable, '-c', code] if node == 'local' else [
        'bash', str(REPO / f'gpu/{WRAPPERS[node]}_ssh.sh'), 'python3 -c ' + shlex.quote(code)]
    result = subprocess.run(command, input=json.dumps(identifiers), capture_output=True,
        text=True, timeout=40)
    if result.returncode:
        return node, dict(error='READ_ONLY_PROCESS_CENSUS_FAILED')
    return node, json.loads(result.stdout)


def main():
    rows, supports, sources = collect()
    with ThreadPoolExecutor(max_workers=6) as executor:
        observations = dict(executor.map(lambda node: census(node, rows + supports), [*WRAPPERS, 'local']))
    observed_unix = time.time()
    for row in rows:
        process = observations[row['node']].get('processes', {}).get(str(row['pid']), {})
        row['alive_now'] = process.get('alive')
        identity = (str(row['start_ticks']) == process.get('start_ticks')) if row['start_ticks'] is not None else (
            row.get('loaded_unix') is not None and process.get('started_unix', float('inf')) <= row['loaded_unix'] + 1)
        row['identity_matches'] = bool(process.get('alive') and identity)
        row['renewal_verified'] = verified(row)
    for row in supports:
        annotate_support(row, observations.get(row['node'], {}), observed_unix)
    stamp = datetime.now(timezone.utc).strftime('%H%M%S')
    result = dict(observed_utc=utc(time.time()), schema='R233_KEPT_FLEET_DEADLINES_V1',
        all_native_bounds_verified=all(row['renewal_verified'] for row in rows),
        all_support_components_verified=False,
        support_scope_note='Native, parent and service process identities are censused separately; on-demand endpoints and absent age dispatch are not running daemons. Process liveness never proves rendered parent guidance.',
        lives=rows, supporting_components=supports, source_receipts=sources, process_observations=observations,
        provider_expiry_independently_verified=False, lease_purchase_or_extension=False,
        uninterrupted_resident_continuity_claimed=False)
    path = HERE / f'DEADLINES_{stamp}.json'
    path.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    lines = [f'# Kept-fleet deadline evidence — {result["observed_utc"]}', '',
        '| Life | Node / GPU | Current process | Renewed native bound UTC | LOAD / WALL | Parent receipt |',
        '| --- | --- | --- | --- | --- | --- |']
    for row in rows:
        state = runtime_status(row)
        bound = row['resident_deadline_utc'] or 'PENDING; target ' + row['target_deadline_utc']
        parent = row['parent_delivery']
        parent_summary = parent['status']
        if parent.get('request_index') is not None:
            parent_summary += f' {parent["request_index"]} → {parent.get("act_index", parent.get("response_index", "pending"))}'
        lines.append(f'| {row["life"]} | {row["node"]} / {row["gpu"]} | {state} | {bound} | {row["loaded_index"]} / {row["wall_index"]} | {parent_summary} |')
    lines.extend(['', '## Supporting components', '',
        '| Component | Execution node | Process identity | Observed deadline UTC |',
        '| --- | --- | --- | --- |'])
    for row in supports:
        state = 'alive; identity matched' if row['identity_matches'] else (
            'alive; identity unbound' if row['alive_now'] else (
                'NOT ALIVE; prior: ' + row['status'] if row['alive_now'] is False else row['status']))
        lines.append(f'| {row["component"]} | {row["node"]} | {state} | {row["deadline_utc"] or "not established"} |')
    lines.extend(['', 'Dispatch/replay is not restoration. Actual reload gaps and source hashes are in the JSON.',
        'A running parent process is not proof of a rendered parent turn. Supporting-component coverage is explicitly incomplete.',
        'Existing user-reported lease dates, conservative safety margins; no lease purchase or provider-expiry assertion.'])
    path.with_suffix('.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps(dict(path=str(path.relative_to(REPO)), verified_lives=sum(row['renewal_verified'] for row in rows),
        total_lives=len(rows), pending=[row['life'] for row in rows if not row['renewal_verified']])))


if __name__ == '__main__':
    main()
