"""Read-only, no-import node3 preparation; never open readouts or model payloads."""

import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import time


MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
PHYSICALS = {0, 1, 2, 3, 4, 7}
REPLAY_STAGE = Path('/localhome/local-rohing/orch_r170_creative_replay_20260917_attempt1')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


class Reader:
    def __init__(self):
        self.total = 0

    def raw(self, path):
        path = Path(path)
        require(path.is_absolute() and path.resolve() == path and not path.is_symlink(), 'canonical_read')
        require('readouts' not in path.parts and path.suffix not in ('.pt', '.bin', '.safetensors'), 'no_sealed_or_model_payload')
        with path.open('rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_FILE_BYTES, 'bounded_regular_read')
            raw = stream.read(MAX_FILE_BYTES + 1)
            after = os.fstat(stream.fileno())
        self.total += len(raw)
        require(len(raw) <= MAX_FILE_BYTES and self.total <= MAX_TOTAL_BYTES, 'read_budget')
        require(all(getattr(before, field) == getattr(after, field)
                    for field in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')), 'read_changed')
        return raw

    def bound_json(self, reference):
        require(set(reference) == {'path', 'sha256'}, 'exact_reference')
        raw = self.raw(reference['path'])
        require(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'reference_hash')
        return json.loads(raw)

    def json(self, path):
        raw = self.raw(path)
        return json.loads(raw), dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())


def process_record(pid):
    require(type(pid) is int and pid > 1, 'process_id')
    root = Path('/proc') / str(pid)
    fields = root.joinpath('stat').read_text().rsplit(') ', 1)[1].split()
    environment = root.joinpath('environ').read_bytes()
    return dict(pid=pid, state=fields[0], parent=int(fields[1]), group=int(fields[2]), start_ticks=fields[19],
        uid=root.stat().st_uid, cwd=str(root.joinpath('cwd').resolve()),
        argv=root.joinpath('cmdline').read_bytes().rstrip(b'\0').decode().split('\0'),
        cgroup=root.joinpath('cgroup').read_text().strip(),
        cvd=[entry.decode().split('=', 1)[1] for entry in environment.split(b'\0')
             if entry.startswith(b'CUDA_VISIBLE_DEVICES=')])


def topology(pid):
    actor = process_record(pid)
    timer = process_record(actor['parent'])
    supervisor = process_record(timer['parent'])
    return dict(actor=actor, timer=timer, supervisor=supervisor)


def identity_only(processes):
    return {role: {key: value for key, value in process.items() if key != 'state'}
            for role, process in processes.items()}


def validate_topology(seed, config, plan, processes):
    actor, timer, supervisor = (processes[role] for role in ('actor', 'timer', 'supervisor'))
    require(actor['pid'] == seed['identity']['pid'] and actor['start_ticks'] == seed['identity']['start_ticks'], 'original_native_identity')
    prefix = [PYTHON, '-B', '-m']
    expected_actor = prefix + ['gpu.orch_r125_continual_guard', 'native', '--config', seed['guard_ref']['path']]
    require(actor['argv'] == expected_actor, 'native_argv')
    require(timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
            and len(timer['argv']) == 11 and re.fullmatch(r'[1-9][0-9]*s', timer['argv'][3])
            and timer['argv'][4:] == expected_actor, 'timer_argv')
    physical = seed['physical']
    wrapper, action = (('gpu.orch_r125_continual_guard', 'supervise') if physical in (0, 2) else
        ('gpu.orch_r133_node3_handoff' if physical == 1 else 'gpu.orch_r133_node3_programmes', 'contained-native'))
    require(supervisor['argv'] == prefix + [wrapper, action, '--config', seed['guard_ref']['path']], 'supervisor_argv')
    require(actor['group'] == timer['group'] == timer['pid'] and supervisor['group'] == supervisor['pid']
            and supervisor['parent'] == 1, 'exact_lifecycle_groups')
    require(all(process['uid'] == os.getuid() and process['cwd'] == plan['source_root']
                and process['state'] not in ('Z', 'X', 'T', 't') for process in processes.values()), 'live_owned_source')
    require(actor['cvd'] == timer['cvd'] == [plan['gpu_uuid']], 'native_timer_device')
    if physical in (0, 2):
        require(supervisor['cvd'] == [''] and 'device_containment' not in config, 'direct_supervisor_scope')
        require(re.fullmatch(r'0::/user.slice/user-[0-9]+.slice/session-[0-9]+.scope', actor['cgroup']), 'direct_cgroup')
    else:
        require(supervisor['cvd'] == [plan['gpu_uuid']], 'contained_supervisor_device')
        require(actor['cgroup'] == '0::/system.slice/' + config['device_containment']['unit'] + '.service', 'contained_cgroup')
    require(actor['cgroup'] == timer['cgroup'] == supervisor['cgroup'], 'same_cgroup')


def current_head(reader, life):
    paths = sorted(path for path in (life / 'stream/records').glob('*.json')
                   if re.fullmatch(r'[0-9]{20}\.json', path.name))
    require(paths, 'journal_head_exists')
    document, reference = reader.json(paths[-1])
    require(document['sha256'] == digest({key: value for key, value in document.items() if key != 'sha256'}), 'head_record_hash')
    result = dict(reference=reference, index=document['index'], kind=document['kind'],
                  cycle=document['document'].get('cycle'), clean_saved_boundary=False)
    if document['kind'] == 'SLEEP_COMPLETE':
        saved = document['document']['resume_state']
        state = saved['state']
        require(saved['sha256'] == digest(state), 'saved_state_hash')
        result.update(state_sha256=saved['sha256'], state_fields=sorted(state),
            row_count=len(state['rows']), sleep_frontier=state['sleep_frontier'],
            pending_is_none=state['pending'] is None,
            clean_saved_boundary=document['document']['status'] == 'COMPLETE'
                and state['pending'] is None and state['sleep_frontier'] == len(state['rows']))
    return result


def inspect_lane(seed, reader):
    config = reader.bound_json(seed['guard_ref'])
    require(dict(path=config['plan_path'], sha256=config['plan_sha256']) == seed['plan_ref'], 'same_plan_reference')
    plan = reader.bound_json(seed['plan_ref'])
    require(plan['root'] == seed['life_root'] and plan['source_root'] == seed['source_root']
            and plan['physical'] == seed['physical'] and plan['gpu_uuid'] == seed['gpu_uuid'], 'exact_life_scope')
    require(config['hard_end_unix'] == plan['hard_end_unix'], 'same_wall')
    require(config['host_sha256'] == hashlib.sha256(socket.gethostname().encode()).hexdigest(), 'same_host')
    processes = topology(seed['identity']['pid'])
    validate_topology(seed, config, plan, processes)
    source = Path(plan['source_root'])
    paths = sorted(source.rglob('*.py'))
    pins = {str(path.relative_to(source)): hashlib.sha256(reader.raw(path)).hexdigest() for path in paths}
    require(pins == config['source_pins'], 'entire_original_python_closure')
    for reference in seed['source_census'].values():
        require(hashlib.sha256(reader.raw(reference['path'])).hexdigest() == reference['sha256'], 'census_source_unchanged')
    startup_ref = dict(path=plan['startup_context']['path'], sha256=plan['startup_context']['sha256'])
    require(hashlib.sha256(reader.raw(startup_ref['path'])).hexdigest() == startup_ref['sha256'], 'startup_hash')
    launch, launch_ref = reader.json(Path(config['attempt_dir']) / 'LAUNCH.json')
    require(launch['pid'] == processes['timer']['pid'] and launch['parent_start_ticks'] == processes['timer']['start_ticks']
            and launch['guard_sha256'] == seed['guard_ref']['sha256'] and launch['plan_sha256'] == seed['plan_ref']['sha256'], 'launch_binding')
    life = Path(plan['root'])
    head = current_head(reader, life)
    commits = sorted(path for path in (life / 'checkpoints').glob('sleep_*/COMMIT.json')
                     if re.fullmatch(r'sleep_[0-9]{6}', path.parent.name))
    checkpoint = None
    if commits:
        metadata, reference = reader.json(commits[-1])
        checkpoint = dict(reference=reference, cycle=int(commits[-1].parent.name[6:]),
            optimizer_steps=metadata.get('optimizer_steps'), adapter_state_sha256=metadata.get('adapter_state_sha256'),
            checkpoint_sha256=metadata.get('checkpoint_sha256'), latest_commit_is_not_current_boundary=True,
            payloads_opened=False)
    after = topology(seed['identity']['pid'])
    validate_topology(seed, config, plan, after)
    require(identity_only(processes) == identity_only(after), 'stable_full_topology')
    reader.bound_json(seed['guard_ref'])
    return dict(physical=seed['physical'], life_root=seed['life_root'], guard_ref=seed['guard_ref'],
        plan_ref=seed['plan_ref'], source_root=str(source), plan=plan, guard=config, startup_ref=startup_ref,
        source_python_count=len(pins), source_manifest_sha256=digest(pins), full_source_closure_verified=True,
        original_runtime_validator_executed=False, launch_ref=launch_ref, processes=after, topology_twice_verified=True,
        head=head, latest_commit=checkpoint, source_census=seed['source_census'],
        status='READONLY_PREP_VERIFIED_NOT_ADMISSION', learner_signal_authorized=False)


def replay_status(reader):
    result = dict(parked_for_context_priority=True, observer_modified=False, receipts_preserved=True)
    for name in ('SELECTION_OBSERVER_STARTED.json', 'SELECTION_OBSERVER_RESULT.json',
                 'SELECTION_FREEZE_RECEIPT.json', 'MAIN_GO.json', 'DRIVER_BINDING.json',
                 'PROPOSED_GUARD.json'):
        path = REPLAY_STAGE / 'physical1' / name
        if path.exists():
            document, reference = reader.json(path)
            result[name] = dict(reference=reference, document=document)
        else:
            result[name] = dict(exists=False)
    for pid in (503582, 503583):
        try:
            result[str(pid)] = process_record(pid)
        except FileNotFoundError:
            result[str(pid)] = dict(absent=True)
    result['observer_result_exists'] = (REPLAY_STAGE / 'physical1/SELECTION_OBSERVER_RESULT.json').exists()
    return result


def collect(seed):
    require(seed['schema'] == 'R179_NODE3_READONLY_SEED_V1' and len(seed['lanes']) == 6
            and {lane['physical'] for lane in seed['lanes']} == PHYSICALS, 'six_scoped_lives')
    reader = Reader()
    result = dict(schema='R179_NODE3_READONLY_PREPARATION_V1', started_unix=time.time(),
        hostname=socket.gethostname(), source_census_ref=seed['source_census_ref'], roster_ref=seed['roster_ref'],
        lanes=[], signals_sent=0, remote_writes=0, model_calls=0, sealed_readouts_opened=0,
        checkpoint_payloads_opened=0, parent_actions=0, handoff_or_GPU_GO=False)
    for lane in seed['lanes']:
        try:
            result['lanes'].append(inspect_lane(lane, reader))
        except Exception as error:
            result['lanes'].append(dict(physical=lane['physical'], life_root=lane['life_root'],
                status='PREPARATION_REFUSED_NO_ACTION', error_type=type(error).__name__, error=str(error)))
    result['r170'] = replay_status(reader)
    result.update(bytes_read=reader.total, max_read_bytes=MAX_TOTAL_BYTES, finished_unix=time.time())
    return result
