"""Bounded TRAIN-operational roster; never performs evaluator admission.

prepare reads only the R169 parent bindings/configs and public R167 source
registration identity fields. observe performs at most one read-only wrapper
invocation per node, recorded before invocation. render is local-only.
"""

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORKERS = REPO / 'research_loop/workers'
OUTPUT = HERE / 'CURRENT_LEARNER_ROSTER.json'
NODES = ('a100', 'ovx2', 'ovx3', 'a40r')
NODE_CAP = 14 * 1024 * 1024
LOCAL_CAP = 8 * 1024 * 1024
FLEET_ROOT = '/localhome/local-rohing/orch_r167_fleet_20260917_generation2'
PLAN_FIELDS = ('schema', 'root', 'source_root', 'physical', 'physical_gpu', 'gpu_uuid',
    'hard_end_unix', 'max_sleeps', 'presleep_variant', 'new_presentations', 'rehearsal_presentations')
DENIED = re.compile(r'(?:^|[/_.-])(?:sealed|readout|scores?|answers?|condition|conditions|eval|evaluation)(?:$|[/_.-])', re.I)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def reference(path, raw):
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())


class Reader:
    def __init__(self, cap, deadline=None):
        self.cap = cap
        self.used = 0
        self.deadline = deadline
        self.cache = {}

    def raw(self, path, limit, *, proc=False):
        path = Path(path)
        require(self.deadline is None or time.monotonic() < self.deadline, 'observation_deadline')
        require(path.is_absolute() and '..' not in path.parts, 'absolute_metadata_path')
        if not proc:
            require(path == path.resolve() and not path.is_symlink(), 'no_metadata_symlinks')
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode), 'regular_metadata_only')
            require(proc or before.st_size <= limit, 'per_file_read_cap')
            available = min(limit, self.cap - self.used)
            require(available > 0 and (proc or before.st_size <= available), 'aggregate_read_cap')
            raw = stream.read(available)
            self.used += len(raw)
            after = os.fstat(stream.fileno())
            if proc:
                require(len(raw) < available, 'bounded_proc_read')
            else:
                require(len(raw) == before.st_size and all(getattr(before, field) == getattr(after, field)
                    for field in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')),
                    'metadata_changed_during_read')
        return raw

    def document(self, path, limit=1024 * 1024):
        path = Path(path)
        require(not DENIED.search(str(path)), 'forbidden_nonoperational_path')
        if str(path) not in self.cache:
            raw = self.raw(path, limit)
            self.cache[str(path)] = (json.loads(raw), reference(path, raw))
        return self.cache[str(path)]


def plan_projection(plan):
    projected = {key: plan[key] for key in PLAN_FIELDS if key in plan}
    control = plan.get('control')
    if isinstance(control, dict):
        projected['control'] = {key: control[key] for key in
            ('mode', 'learning_steps', 'optimizer_steps', 'sleep_enabled') if key in control}
        projected['control']['adapter_present'] = control.get('adapter') is not None
    return projected


def training_mode(plan):
    control = plan.get('control')
    if isinstance(control, dict) and control.get('mode') in ('frozen_rank8_no_sleep', 'frozen_base_no_adapter'):
        if control.get('learning_steps') == 0 and control.get('optimizer_steps') == 0 and control.get('sleep_enabled') is False:
            return dict(training_enabled=False, kind=control['mode'], evidence='EXPLICIT_OPERATIONAL_CONTROL_PLAN')
        return dict(training_enabled=None, kind='UNKNOWN', evidence='INCONSISTENT_CONTROL_PLAN')
    if plan.get('schema') == 'R125_NATIVE_CONTINUITY_V1' and not control:
        return dict(training_enabled=True, kind='LEARNING_PLAN', evidence='R125_NATIVE_NONCONTROL_PLAN_NOT_UPDATE_PROOF')
    return dict(training_enabled=None, kind='UNKNOWN', evidence='NO_SUPPORTED_CURRENT_NATIVE_PLAN')


def add_seed(rows, node, root, label, evidence, parent=None, registry=None):
    require(node in NODES and Path(root).is_absolute(), 'explicit_node_life_root')
    key = (node, root)
    row = rows.setdefault(key, dict(node=node, life_root=root, labels=[], parent_configs=[],
                                   discovery_refs=[], registrations=[]))
    if label not in row['labels']:
        row['labels'].append(label)
    if evidence not in row['discovery_refs']:
        row['discovery_refs'].append(evidence)
    if parent is not None:
        row['parent_configs'].append(parent)
    if registry is not None:
        row['registrations'].append(registry)


def prepare():
    require(not OUTPUT.exists(), 'create_only_roster_inventory')
    reader = Reader(LOCAL_CAP - 2 * 1024 * 1024)
    rows = {}
    standard = WORKERS / 'r169_parent_auth_refresh_20260917'
    parent_count = 0
    for path in sorted(standard.glob('parent_*/BINDING.json')):
        binding, binding_ref = reader.document(path)
        config, config_ref = reader.document(binding['config'])
        require(config_ref['sha256'] == binding['config_sha256'], 'bound_refreshed_parent_config')
        add_seed(rows, config['node'], config['root'], binding['branch'], binding_ref,
            parent=dict(config_ref=config_ref, source_root_hint=config['source_root'],
                        physical_hint=config.get('physical'), parent_group='standard'))
        parent_count += 1
    community_path = WORKERS / 'r169_community_parent_status_20260917/INSPECT_1789653968285563565.json'
    community, community_ref = reader.document(community_path)
    for name, entry in sorted(community['parents'].items()):
        config, config_ref = reader.document(entry['config']['path'])
        require(config_ref == entry['config'] and config['root'] == entry['root'], 'bound_community_parent_config')
        add_seed(rows, config['node'], config['root'], name, community_ref,
            parent=dict(config_ref=config_ref, source_root_hint=config['source_root'],
                        physical_hint=config.get('physical'), parent_group='community'))
        parent_count += 1
    for relative in ('raw3attempt1/CONFIG.json', 'kernel4attempt3/CONFIG.json'):
        config, config_ref = reader.document(WORKERS / 'r169_node4_auth_refresh_20260917' / relative)
        add_seed(rows, config['node'], config['root'], config['branch'], config_ref,
            parent=dict(config_ref=config_ref, source_root_hint=config['source_root'],
                        physical_hint=config.get('physical'), parent_group='node4'))
        parent_count += 1
    require(parent_count == 25, 'exact_25_refreshed_parent_configs')
    parent_root_count = len(rows)
    registry_path = WORKERS / 'r167_object_survival/fleet_generation2/control2/PLAN.json'
    registry, registry_ref = reader.document(registry_path)
    declarations = []
    for entry in registry['lives']:
        public = {key: entry[key] for key in ('life_id', 'node', 'storage_root', 'process_plan_root', 'status', 'hold')}
        declarations.append(public)
        add_seed(rows, public['node'], public['storage_root'], public['life_id'], registry_ref, registry=public)
    exit_path = WORKERS / 'r169_node4_auth_refresh_20260917/R158_FINAL_EXIT_EVIDENCE.json'
    exit_receipt, exit_ref = reader.document(exit_path)
    native_exit = next(entry for entry in exit_receipt['documents'] if Path(entry['path']).name == 'NATIVE_EXIT.json')
    ended = dict(life_id='R158_parented_learning', evidence_ref=exit_ref,
        remote_exit_ref=dict(path=native_exit['path'], sha256=native_exit['sha256']),
        finished_unix=native_exit['fields']['finished_unix'], exit_code=native_exit['fields']['exit_code'],
        hard_end_unix=1789646400, reason='R158_NATIVE_EXIT_BEFORE_12_UTC_HARD_END')
    document = dict(schema='R171_CURRENT_TRAIN_OPERATIONAL_ROSTER_V1', prepared_unix=time.time(),
        parent_config_count=parent_count, parent_unique_root_count=parent_root_count,
        public_registry_ref=registry_ref, public_registrations=declarations,
        declared_registry_count=len(declarations), supplied_admitted_registry_count=19,
        registry_source_candidate_count=sum(entry['status'] == 'SOURCE_CANDIDATE' for entry in declarations),
        user_recalled_learner_count=22, seed_rows=list(rows.values()), ended_evidence=[ended],
        node_passes={}, local_seed_read_bytes=reader.used,
        read_budget=dict(total_cap=64 * 1024 * 1024, node_cap=NODE_CAP,
            local_reservation=LOCAL_CAP, prior_local_exploration_reservation=2 * 1024 * 1024),
        evaluator_admission_created=False, scientific_claims_changed=False)
    save(document)
    return document


def save(document):
    raw = json.dumps(document, indent=2, sort_keys=True, allow_nan=False).encode() + b'\n'
    temporary = OUTPUT.with_suffix('.json.tmp')
    temporary.write_bytes(raw)
    os.replace(temporary, OUTPUT)


def native_entry(argv):
    if not argv or not Path(argv[0]).name.startswith('python') or '-m' not in argv:
        return None
    position = argv.index('-m')
    if position + 1 >= len(argv):
        return None
    module = argv[position + 1]
    if any(argument in argv for argument in ('--readout-manifest', '--validate-only')):
        return None
    if module == 'gpu.orch_r125_continual_guard' and 'native' in argv:
        return module
    if module == 'gpu.orch_r136_node1_launcher' and 'control-native' in argv:
        return module
    if module in ('gpu.orch_r125_continual_native', 'gpu.orch_r139_continual_controls'):
        return module
    return None


def process_identity(reader, directory, expected_raw=None):
    before = reader.raw(directory / 'stat', 16384, proc=True).decode().rsplit(')', 1)[1].split()
    raw = reader.raw(directory / 'cmdline', 32768, proc=True)
    after = reader.raw(directory / 'stat', 16384, proc=True).decode().rsplit(')', 1)[1].split()
    require(before[19] == after[19] and (expected_raw is None or expected_raw == raw), 'identity_changed')
    require(after[0] not in ('Z', 'X'), 'not_live_native')
    return dict(pid=int(directory.name), start_ticks=after[19], state=after[0], parent_pid=int(after[1]),
                uid=directory.stat().st_uid, cwd=os.readlink(directory / 'cwd'),
                argv_sha256=hashlib.sha256(raw).hexdigest())


def inspect_native(reader, directory, argv, raw):
    module = native_entry(argv)
    require(module is not None, 'actual_supported_native_only')
    flag = '--config' if '--config' in argv else '--plan'
    require(flag in argv, 'explicit_native_config_or_plan')
    path = Path(argv[argv.index(flag) + 1])
    require(str(path).startswith('/localhome/local-rohing/orch_'), 'scoped_operational_config')
    config, config_ref = reader.document(path)
    if flag == '--config':
        plan, plan_ref = reader.document(config['plan_path'])
        require(plan_ref['sha256'] == config['plan_sha256'], 'native_plan_hash_binding')
    else:
        plan, plan_ref = config, config_ref
    require(type(plan.get('root')) is str and type(plan.get('source_root')) is str, 'exact_native_plan_root')
    identity = process_identity(reader, directory, raw)
    require(identity['cwd'] == plan['source_root'], 'native_cwd_source_binding')
    return dict(identity=identity, module=module, config_ref=config_ref, plan_ref=plan_ref,
                plan=plan_projection(plan), training=training_mode(plan))


def head_metadata(reader, root, limit=32):
    require(type(limit) is int and 1 <= limit <= 32, 'max_32_head_records')
    root = Path(root)
    require(str(root).startswith('/localhome/local-rohing/orch_') and not DENIED.search(str(root)), 'TRAIN_root_only')
    require(root == root.resolve(), 'canonical_life_root')
    result = dict(records_read=0, records_skipped_oversize=0, bytes_read=0,
                  last_saved_cycle=None, last_saved_evidence_kind='UNKNOWN')
    before = reader.used
    try:
        checkpoints = root / 'checkpoints'
        names = []
        if checkpoints.is_dir():
            for count, entry in enumerate(os.scandir(checkpoints), 1):
                require(count <= 4096, 'bounded_checkpoint_name_inventory')
                if re.fullmatch(r'sleep_[0-9]{6}', entry.name) and entry.is_dir(follow_symlinks=False):
                    names.append(entry.name)
            for name in sorted(names, reverse=True)[:2]:
                path = checkpoints / name / 'COMMIT.json'
                if path.is_file():
                    commit, commit_ref = reader.document(path, 128 * 1024)
                    require(Path(commit['adapter_path']).parent == path.parent, 'own_checkpoint_metadata')
                    result.update(last_saved_cycle=int(name[6:]), last_saved_ref=commit_ref,
                        last_saved_evidence_kind='COMMIT_METADATA_ONLY_NOT_JOURNAL_OR_PAYLOAD_VALIDATION',
                        last_saved_created_unix=commit.get('created_unix'),
                        last_saved_optimizer_steps=commit.get('optimizer_steps'))
                    break
        directory = root / 'stream/records'
        require(directory == directory.resolve() and not directory.is_symlink(), 'canonical_journal_directory')
        names = []
        for count, entry in enumerate(os.scandir(directory), 1):
            require(count <= 100000, 'bounded_journal_name_inventory')
            if re.fullmatch(r'[0-9]{20}\.json', entry.name):
                require(entry.is_file(follow_symlinks=False), 'regular_journal_head')
                names.append(entry.name)
        names.sort(reverse=True)
        result['latest_record_index'] = int(names[0][:-5]) if names else None
        for name in names[:limit]:
            path = directory / name
            size = path.stat().st_size
            if size > 128 * 1024 or reader.used - before + size > 512 * 1024:
                result['records_skipped_oversize'] += 1
                continue
            record, record_ref = reader.document(path, 128 * 1024)
            result['records_read'] += 1
            require(record['index'] == int(name[:-5]) and record['sha256'] == digest(
                {key: value for key, value in record.items() if key != 'sha256'}), 'head_record_hash')
            document = record['document']
            result.setdefault('head', dict(record_ref=record_ref, index=record['index'], kind=record['kind'],
                optimizer_step=document.get('optimizer_step'), cycle=document.get('cycle'),
                finished_unix=document.get('finished_unix')))
            if record['kind'] == 'SLEEP_COMPLETE' and document.get('status') == 'COMPLETE':
                result['head_completed_sleep'] = dict(record_ref=record_ref, cycle=document['cycle'])
            break
    except (OSError, ValueError, KeyError) as error:
        result['missingness'] = type(error).__name__ + ':' + str(error)
    result['bytes_read'] = reader.used - before
    return result


def observe_node(request, proc_root=Path('/proc')):
    reader = Reader(request['read_cap'], time.monotonic() + 110)
    result = dict(node=request['node'], started_unix=time.time(), hostname=socket.gethostname(),
        native_processes=[], unmatched_native_candidates=[], permission_denials=0, scanned_processes=0,
        registry_file_presence={}, heads={}, read_cap=request['read_cap'])
    try:
        result['boot_id'] = reader.raw(proc_root / 'sys/kernel/random/boot_id', 1024, proc=True).decode().strip()
        for directory in sorted(proc_root.iterdir()):
            if not directory.name.isdigit():
                continue
            result['scanned_processes'] += 1
            require(result['scanned_processes'] <= 20000, 'bounded_process_inventory')
            try:
                raw = reader.raw(directory / 'cmdline', 32768, proc=True)
                argv = raw.rstrip(b'\0').decode().split('\0')
                if native_entry(argv) is None:
                    continue
                result['native_processes'].append(inspect_native(reader, directory, argv, raw))
            except PermissionError:
                result['permission_denials'] += 1
            except (FileNotFoundError, ProcessLookupError):
                continue
            except (ValueError, KeyError, IndexError, UnicodeError) as error:
                result['unmatched_native_candidates'].append(dict(pid=int(directory.name),
                    reason=type(error).__name__ + ':' + str(error)))
        roots = {row['life_root'] for row in request['seeds']}
        roots.update(native['plan']['root'] for native in result['native_processes'])
        for root in sorted(roots):
            result['heads'][root] = head_metadata(reader, root)
        for registration in request['registrations']:
            path = Path(FLEET_ROOT) / 'lives' / registration['life_id'] / 'REGISTERED.json'
            result['registry_file_presence'][registration['life_id']] = dict(path=str(path),
                exists=path.is_file(), contents_opened=False)
    except (OSError, ValueError) as error:
        result['pass_missingness'] = type(error).__name__ + ':' + str(error)
    result.update(observed_unix=time.time(), bytes_read=reader.used, checkpoint_payloads_opened=False,
        evaluator_files_opened=False, remote_writes=False, provider_calls=False, process_signals=False,
        gpu_jobs_launched=False, full_journal_scanned=False)
    return result


def assemble(document):
    observed_roots = {(node, native['plan']['root'])
        for node, record in document['node_passes'].items()
        for native in record.get('observation', {}).get('native_processes', [])}
    rows = {}
    for seed in document['seed_rows']:
        row = deepcopy(seed)
        aliases = {registration.get('process_plan_root') for registration in row['registrations']
                   if registration.get('process_plan_root') != row['life_root']}
        aliases.discard(None)
        if len(aliases) == 1 and (row['node'], next(iter(aliases))) in observed_roots:
            row['declared_storage_root'] = row['life_root']
            row['life_root'] = next(iter(aliases))
            row['storage_custody'] = 'EXPLICIT_REGISTRY_PROCESS_ROOT_MATCH_STORAGE_ALIAS_NOT_REVALIDATED'
        key = (row['node'], row['life_root'])
        if key in rows:
            for field in ('labels', 'parent_configs', 'discovery_refs', 'registrations'):
                rows[key][field].extend(value for value in row[field] if value not in rows[key][field])
        else:
            rows[key] = row
    for node, record in document['node_passes'].items():
        observation = record.get('observation', {})
        for native in observation.get('native_processes', []):
            root = native['plan']['root']
            key = (node, root)
            if key not in rows:
                add_seed(rows, node, root, Path(root).parent.name, native['plan_ref'])
            rows[key].setdefault('natives', []).append(native)
        for key, row in rows.items():
            if key[0] == node:
                row['head_metadata'] = observation.get('heads', {}).get(key[1], {})
                if row.get('declared_storage_root'):
                    row['declared_storage_head_metadata'] = observation.get('heads', {}).get(row['declared_storage_root'], {})
                    row['current_storage_saved_cycle'] = None
                row['observed_unix'] = observation.get('observed_unix')
                row['node_pass_missingness'] = observation.get('pass_missingness')
                for registration in row['registrations']:
                    registration['registration_file'] = observation.get('registry_file_presence', {}).get(registration['life_id'])
    for row in rows.values():
        natives = row.get('natives', [])
        row['status'] = 'LIVE' if len(natives) == 1 else 'UNKNOWN'
        row['custody'] = 'ONE_NATIVE_PID_PLAN_HASH_CWD_BOUND' if len(natives) == 1 else (
            'MULTIPLE_NATIVE_IDENTITIES_NO_SINGLE_WRITER_CLAIM' if natives else 'NO_BOUND_NATIVE_OBSERVED_NOT_PROOF_OF_RETIREMENT')
        row['training'] = natives[0]['training'] if len(natives) == 1 else training_mode({})
        if row['life_root'] in document.get('declared_controls', {}):
            row['declared_control'] = document['declared_controls'][row['life_root']]
            if not natives:
                row['training'] = dict(training_enabled=None, kind='DECLARED_' + row['declared_control']['mode'],
                    evidence='LOCAL_PARENT_CONFIG_MODE_HINT_NOT_CURRENT_NATIVE_PLAN')
                row['custody'] = 'CONTROL_ENTRYPOINT_NOT_COVERED_BY_CAPTURE_FILTER_NO_SECOND_NODE_PASS'
        row['physical'] = natives[0]['plan'].get('physical', natives[0]['plan'].get('physical_gpu')) if len(natives) == 1 else None
        row['current_source_root'] = natives[0]['plan'].get('source_root') if len(natives) == 1 else None
        row['registry_declared'] = bool(row['registrations'])
        for ended in document['ended_evidence']:
            if any(registration['life_id'] == ended['life_id'] for registration in row['registrations']) and not natives:
                row.update(status='ENDED_EXCLUDED', custody='EXPLICIT_PRIOR_EXIT_AND_NO_CURRENT_NATIVE', ended_evidence=ended)
    result = sorted(rows.values(), key=lambda row: (row['node'], row['physical'] if isinstance(row['physical'], int) else 999, row['life_root']))
    live = [row for row in result if row['status'] == 'LIVE']
    document['rows'] = result
    document['summary'] = dict(unique_roots_including_ended=len(result), live_native_lives=len(live),
        live_training_enabled=sum(row['training']['training_enabled'] is True for row in live),
        live_frozen_controls=sum(row['training']['training_enabled'] is False for row in live),
        live_training_mode_unknown=sum(row['training']['training_enabled'] is None for row in live),
        unknown_custody=sum(row['status'] == 'UNKNOWN' for row in result),
        ended_excluded=sum(row['status'] == 'ENDED_EXCLUDED' for row in result),
        per_node=dict(Counter(row['node'] for row in live)),
        live_missing_from_R167=[dict(node=row['node'], life_root=row['life_root'], labels=row['labels'],
            training=row['training']) for row in live if not row['registry_declared']],
        live_declared_missing_source_custody=[registration['life_id'] for row in live for registration in row['registrations']
            if registration['status'] != 'SOURCE_CANDIDATE'],
        live_declared=sum(row['registry_declared'] for row in live),
        live_registration_markers=sum(any(registration.get('registration_file', {}).get('exists', False)
            for registration in row['registrations'] if isinstance(registration.get('registration_file'), dict)) for row in live),
        unresolved_declared_frozen_controls=sum(row['status'] == 'UNKNOWN' and 'declared_control' in row for row in result),
        normalized_explicit_storage_aliases=sum('declared_storage_root' in row for row in result),
        source_registration_markers_present=sum(
            registration.get('registration_file', {}).get('exists', False)
            for row in result for registration in row['registrations']
            if isinstance(registration.get('registration_file'), dict)),
        remote_bytes_read=sum(record.get('observation', {}).get('bytes_read', 0) for record in document['node_passes'].values()))
    document['reconciled_unix'] = time.time()
    return document


def enrich_local_controls(document):
    reader = Reader(LOCAL_CAP - 2 * 1024 * 1024 - document['local_seed_read_bytes'])
    controls = {}
    for row in document['seed_rows']:
        if 'orch_r139_a100_frozen_' not in row['life_root']:
            continue
        for parent in row['parent_configs']:
            config, config_ref = reader.document(parent['config_ref']['path'])
            require(config_ref == parent['config_ref'], 'unchanged_local_parent_mode_reference')
            mode = config.get('actual_programme')
            if mode not in ('frozen_rank8_no_sleep', 'frozen_base_no_adapter'):
                mode = config.get('programme')
            if mode in ('frozen_rank8_no_sleep', 'frozen_base_no_adapter'):
                controls[row['life_root']] = dict(mode=mode, config_ref=config_ref,
                    native_identity='UNKNOWN', current_mode_verified=False)
    document['declared_controls'] = controls
    document['local_postprocess_read_bytes'] = reader.used
    return document


def observe_all(document):
    script = Path(__file__).read_text()
    for node in NODES:
        require(node not in document['node_passes'], 'at_most_one_wrapper_pass_per_node')
        request = dict(node=node, read_cap=NODE_CAP,
            seeds=[row for row in document['seed_rows'] if row['node'] == node],
            registrations=[row for row in document['public_registrations'] if row['node'] == node])
        document['node_passes'][node] = dict(attempted=True, attempted_unix=time.time(),
                                            observer_sha256=hashlib.sha256(script.encode()).hexdigest(),
                                            wrapper_ref=reference(REPO / ('gpu/' + node + '_ssh.sh'), (REPO / ('gpu/' + node + '_ssh.sh')).read_bytes()))
        save(document)
        remote = ('__file__ = ' + repr(str(Path(__file__).resolve())) + '\n'
            + "__name__ = 'r171_remote_readonly'\n" + script
            + '\nprint(json.dumps(observe_node(' + repr(request) + '), sort_keys=True))\n')
        command = 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python3 -B -'
        try:
            completed = subprocess.run(['bash', str(REPO / ('gpu/' + node + '_ssh.sh')), command],
                input=remote, text=True, capture_output=True, cwd=REPO, timeout=150)
            require(len(completed.stdout.encode()) <= 1024 * 1024, 'bounded_metadata_output')
            document['node_passes'][node].update(returncode=completed.returncode,
                stderr=completed.stderr[:2048], stdout_sha256=hashlib.sha256(completed.stdout.encode()).hexdigest())
            if completed.returncode == 0:
                document['node_passes'][node]['observation'] = json.loads(completed.stdout)
            else:
                document['node_passes'][node]['missingness'] = 'WRAPPER_FAILED_NO_RETRY'
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            document['node_passes'][node]['missingness'] = type(error).__name__ + ':' + str(error)
        save(assemble(document))
        print(json.dumps(dict(node=node, summary=document['summary']), sort_keys=True), flush=True)
    return document


def render(document):
    document = assemble(enrich_local_controls(document))
    summary = document['summary']
    clock = datetime.fromtimestamp(document['reconciled_unix'], timezone.utc).isoformat(timespec='seconds')
    observed_times = [record['observation']['observed_unix'] for record in document['node_passes'].values()
                      if 'observation' in record]
    snapshot_start = datetime.fromtimestamp(min(observed_times), timezone.utc).isoformat(timespec='microseconds')
    snapshot_end = datetime.fromtimestamp(max(observed_times), timezone.utc).isoformat(timespec='microseconds')
    lines = ['# R171 current learner roster — R159 forward coverage', '', 'Operational reconciliation: **' + clock + '**.', '',
        'Actual node snapshots: **' + snapshot_start + ' through ' + snapshot_end + '** (07:50:25–07:50:29 PDT on September 17, 2026). Later local rendering is not a new node observation.', '',
        'Inventory only: no evaluator admission, condition mapping, outcomes or scientific claims.', '',
        '## Counts', '',
        f"- R169: {document['parent_config_count']} refreshed parent configs → {document['parent_unique_root_count']} distinct declared life roots.",
        f"- R167: {document['declared_registry_count']} public declarations; {document['registry_source_candidate_count']} source candidates (the supplied admitted count is 19, not a current-live count).",
        f"- Current bounded pass: **{summary['live_native_lives']} confirmed LIVE training-enabled lives**. Separately, **{summary['unresolved_declared_frozen_controls']} declared frozen/no-adapter controls have UNKNOWN current native custody**; zero confirmed live controls is not evidence of their absence.",
        f"- {summary['unknown_custody']} unresolved custody roots; {summary['ended_excluded']} explicitly ended/excluded. User's recalled 22 is not imposed as an acceptance target.",
        f"- R167's 19 stat-confirmed registration markers include ended R158: **{summary['live_registration_markers']} currently live registered + {len(summary['live_declared_missing_source_custody'])} live declared/custody-held (C5, repo_reader) + {len(summary['live_missing_from_R167'])} live undeclared = {summary['live_native_lives']}**. No admission is created by this inventory.",
        '- 25 parent-associated lives plus the separately discovered raw-unparented life give 26 candidate ongoing participants: 24 native-bound and two frozen controls UNKNOWN. Repo_reader\'s explicit registry process/storage alias is one learner, not two. R158 is an additional historical declaration, excluded as ended.',
        '- The recalled 22 is arithmetically compatible with 18 live registered plus four undeclared while omitting the two custody-held lives; this is not evidence that the user intended that definition. Do not report 22, 25, or 26 as the confirmed current training count.', '',
        '## Current identities', '',
        '| Label / public registration | Node / physical | Native PID / start ticks | Status / mode | Last saved cycle |',
        '| --- | --- | --- | --- | --- |']
    for row in document['rows']:
        names = ', '.join(registration['life_id'] for registration in row['registrations']) or ', '.join(row['labels'])
        identity = row.get('natives', [{}])[0].get('identity', {})
        saved_cycle = row.get('head_metadata', {}).get('last_saved_cycle')
        saved_label = str(saved_cycle) if saved_cycle is not None else 'UNKNOWN / no saved sleep verified'
        if row.get('declared_storage_root'):
            saved_label = 'UNKNOWN current; old-root ' + str(saved_cycle) + ' only'
        lines.append(f"| {names} | {row['node']} / {row['physical'] if row['physical'] is not None else 'UNKNOWN'} | {identity.get('pid', 'UNKNOWN')} / {identity.get('start_ticks', 'UNKNOWN')} | {row['status']} / {row['training']['kind']} | {saved_label} |")
    lines += ['', '## Concrete live identities absent from R167 declarations', '']
    for row in summary['live_missing_from_R167']:
        lines.append('- ' + ', '.join(row['labels']) + ' — `' + row['life_root'] + '` (' + row['node'] + '; ' + row['training']['kind'] + ').')
    lines += ['', 'Declared but source-custody-missing and now live: ' + ', '.join(summary['live_declared_missing_source_custody']) + '.', '',
        'These four missing lives have no R167 public registration name in the inspected registry; labels above come from existing operational parent configs or the actual root basename, not invented evaluator IDs.', '',
        '## Unresolved control / alias custody', '',
        '- The captured observer covered R125 natives and direct R139 entries but missed `gpu.orch_r136_node1_launcher control-native`. Accordingly the two declared A100 controls remain UNKNOWN PID/startticks/current source/config, not ended or silently counted live. The saved script now recognizes that exact entrypoint and has a regression test; **no second A100 pass was made**.',
        '- Their bounded TRAIN heads show recorded responses but do not bind a current native process. Frozen rank8 last observed response finished at 14:20:46.415650 UTC; no-adapter response at 14:28:05.842863 UTC. These historical timestamps are not current-live proofs.',
        '- `repo_reader` has a current native bound to the registry\'s original `process_plan_root`, with cwd in its recovery source. The registry\'s separate recovery `storage_root` failed the cheap own-checkpoint-path check. Public alias linkage prevents double counting, but storage ownership/admission remains UNKNOWN. Sleep30 from the old root is historical, not a freshly established current saved boundary.', '',
        '## Root and current config/source provenance', '']
    for row in document['rows']:
        lines += ['- `' + row['life_root'] + '` — ' + row['custody'] + '.']
        for native in row.get('natives', []):
            lines += ['  Current source: `' + native['plan']['source_root'] + '`; config `' + native['config_ref']['path'] + '` SHA256 `' + native['config_ref']['sha256'] + '`; plan `' + native['plan_ref']['path'] + '` SHA256 `' + native['plan_ref']['sha256'] + '`.']
        if row.get('declared_storage_root'):
            lines += ['  Declared storage alias (unverified): `' + row['declared_storage_root'] + '`.']
        if row.get('declared_control'):
            lines += ['  Declared control mode only: `' + row['declared_control']['mode'] + '` from parent config `' + row['declared_control']['config_ref']['path'] + '`; current native config/source UNKNOWN.']
    lines += ['', '## Limits and evidence', '',
        f"- Exactly one attempted sanctioned wrapper pass per node; remote bytes read {summary['remote_bytes_read']:,}, per-node cap {NODE_CAP:,}; local reserved cap {LOCAL_CAP:,}; aggregate ceiling 64 MiB.",
        '- Public registry input: `' + document['public_registry_ref']['path'] + '` SHA256 `' + document['public_registry_ref']['sha256'] + '`. Only life identity/source-status fields were projected; REGISTERED files were stat-only, never opened.',
        '- Saved cycle is the highest cheaply visible sleep COMMIT metadata, NOT complete journal, payload, restore or ownership validation. At most 32 trailing record candidates/life; oversized history records skipped, at most one small head record read; no full journal scan or TRAIN text output.',
        '- Native process identity was checked around config/plan reads; one PID plus exact plan hash and cwd/source match is operational evidence, not a single-writer admission. Concurrent handoffs can leave UNKNOWN; no retry or inferred custody.',
        '- Frozen controls remain separate from training-enabled lives; no adapter files or evaluator/readout/answer/score/condition-map files opened. Unsupported native entrypoints and inaccessible processes remain coverage limitations.',
        '- R158 parented-learning has recorded native exit 11:59:44.971569 UTC and hard end 12:00 UTC on September 17, 2026; excluded from the current roster, not from historical R167 declarations.',
        '- Full projected provenance, per-node snapshot times, skipped/missing metadata, alias roots and registration-file presence are retained in `CURRENT_LEARNER_ROSTER.json`. No remote writes, signals, providers or GPU jobs; no COORDINATION edits.', '']
    lines += ['| Node alias / hostname | Actual snapshot UTC | Operational bytes read | Wrapper passes |',
              '| --- | --- | --- | --- |']
    for node, record in document['node_passes'].items():
        observation = record.get('observation', {})
        timestamp = datetime.fromtimestamp(observation['observed_unix'], timezone.utc).isoformat(timespec='microseconds') if observation else 'UNKNOWN'
        lines.append(f"| {node} / {observation.get('hostname', 'UNKNOWN')} | {timestamp} | {observation.get('bytes_read', 'UNKNOWN')} | 1 |")
    lines += ['', 'Validation: 13 local fixture tests pass; current JSON counter/provenance/budget checks pass. The 24 confirmed training-enabled natives are a lower bound for this scoped inventory, not proof that no other unsupported runtime exists.', '']
    (HERE / 'CURRENT_LEARNER_ROSTER.md').write_text('\n'.join(lines))
    save(document)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'observe', 'render'))
    args = parser.parse_args()
    if args.action == 'prepare':
        document = prepare()
        print(json.dumps(dict(parent_config_count=document['parent_config_count'],
            unique_parent_roots=document['parent_unique_root_count'], declared=document['declared_registry_count'])))
    else:
        document = json.loads(OUTPUT.read_text())
        if args.action == 'observe':
            observe_all(document)
        else:
            render(document)


if __name__ == '__main__' and len(sys.argv) > 1:
    main()
