"""Explicit offline deadline-only sidecar continuation; never signals or launches."""

import argparse
import ast
from contextlib import ExitStack, contextmanager
from copy import deepcopy
import fcntl
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import stat
import time

from gpu import orch_r153_community_exchange as exchange
from gpu import orch_r153_community_parents as parents
from gpu.orch_r153_community_service import validate_config


AUTH_SHA = '05c50f8012559360221a889b26c00700a988878fbe4d32d30e3f786937dfc392'
HARD_END = 1789776000
RESOURCE_CEILING = 1789776600
LIMIT = 512 * 1024 * 1024
SCHEMA = 'R157_COMMUNITY_DEADLINE_PLAN_V1'
PROGRAMME_SOURCE_SHA = 'cc5599a8308c35c044720d4d8c9d988a5fcfdae25daa71cbc9b2c1f46de6658e'
require = exchange.require
encoded = exchange.encoded


def read_bytes(path, limit=2 * 1024 * 1024):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute_input')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= limit,
                'bounded_single_link_file')
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    require((before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            == (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            and len(raw) == before.st_size, 'input_changed')
    return raw


def reference(path):
    raw = read_bytes(path)
    return dict(path=str(Path(path).absolute()), sha256=exchange.sha(raw))


def bound(reference_value):
    require(type(reference_value) is dict and set(reference_value) == {'path', 'sha256'}, 'exact_file_reference')
    raw = read_bytes(reference_value['path'])
    require(exchange.sha(raw) == reference_value['sha256'], 'bound_file_changed')
    return exchange.decode(raw)


def write_new(path, document):
    path = Path(path)
    with exchange.console._directory(path.parent) as directory:
        exchange.immutable_file(directory, path.name, encoded(document))


def authority(reference_value):
    require(reference_value['sha256'] == AUTH_SHA, 'exact_Rohin_authority')
    document = bound(reference_value)
    require(document['authorization_is_runtime_budget_not_provider_booking'] is True
            and document['must_abort_on_conflicting_real_reservation'] is True,
            'runtime_not_provider_booking')
    require(time.time() < HARD_END, 'future_authorized_wall')


def extend(config, field):
    old = config[field]
    require(type(old) in (int, float) and math.isfinite(old) and 0 < old < HARD_END,
            'strict_future_deadline_extension')
    successor = deepcopy(config)
    successor[field] = HARD_END
    return successor


def checked_service(config):
    normalized = deepcopy(config)
    for field in ('repository', 'broker_root', 'mirror_root'):
        normalized[field] = str(Path(config[field]).resolve())
    validate_config(normalized)
    require(config.get('profile') == 'ALL5_OVX3', 'same_five_node5_only')


def checked_parent(config):
    normalized = deepcopy(config)
    for field in ('programme_path', 'principles_path'):
        raw = read_bytes(config[field])
        require(exchange.sha(raw) == config[field.replace('_path', '_sha256')], 'parent_policy_pin')
        normalized[field] = str(Path(config[field]).resolve())
    parents.validate(normalized)
    require(config['node'] == 'ovx3' and config['programme'] == 'raw_parented', 'same_node5_Astra_parent')


def prepare(authorization_path, service_path, parent_paths, gate_path):
    require(set(parent_paths) == set(parents.LEARNERS), 'exact_five_parent_configs')
    auth = reference(authorization_path)
    authority(auth)
    service_ref, gate_ref = reference(service_path), reference(gate_path)
    previous_service, previous_gate = bound(service_ref), bound(gate_ref)
    checked_service(previous_service)
    require(previous_gate.get('schema') == parents.GATE_SCHEMA and previous_gate.get('status') == 'MAIN_BOUND'
            and set(previous_gate['parents']) == set(parents.LEARNERS), 'previous_Main_parent_gate')
    successor_gate = deepcopy(previous_gate)
    entries = {}
    outputs = set()
    for actor in parents.LEARNERS:
        previous_ref = reference(parent_paths[actor])
        previous = bound(previous_ref)
        successor = extend(previous, 'hard_end_unix')
        checked_parent(successor)
        binding = previous_gate['parents'][actor]
        require(binding == dict(root=previous['root'], node=previous['node'], source_root=previous['source_root'],
                config_sha256=previous_ref['sha256'], output=binding['output'])
                and previous['branch'] == actor, 'exact_previous_parent_gate_binding')
        output = Path(binding['output'])
        require(output.is_absolute() and '..' not in output.parts and str(output.resolve()) not in outputs,
                'distinct_existing_parent_outputs')
        outputs.add(str(output.resolve()))
        require(previous['root'] == previous_service['agents'][actor]['root'], 'same_service_parent_life')
        successor_gate['parents'][actor]['config_sha256'] = exchange.sha(encoded(successor))
        entries[actor] = dict(previous=previous_ref, successor=successor, output=binding['output'])
    return dict(schema=SCHEMA, authorization=auth, hard_end_unix=HARD_END,
        runtime_resource_ceiling_unix=RESOURCE_CEILING, runtime_not_provider_booking=True,
        service=dict(previous=service_ref, successor=extend(previous_service, 'deadline_unix')),
        parents=entries, gate=dict(previous=gate_ref, successor=successor_gate))


def validate_plan(plan):
    require(plan.get('schema') == SCHEMA, 'deadline_plan_schema')
    expected = prepare(plan['authorization']['path'], plan['service']['previous']['path'],
        {actor: entry['previous']['path'] for actor, entry in plan['parents'].items()}, plan['gate']['previous']['path'])
    require(expected == plan, 'exact_deadline_only_plan')
    return plan


def stage(plan, output):
    validate_plan(plan)
    output = Path(output).resolve()
    state_roots = [Path(bound(plan['service']['previous'])['broker_root']).resolve()]
    state_roots.extend(Path(entry['output']).resolve() for entry in plan['parents'].values())
    require(all(output != root and root not in output.parents for root in state_roots), 'stage_outside_live_state')
    output.mkdir(mode=0o700)
    write_new(output / 'PLAN.json', plan)
    write_new(output / 'SERVICE.json', plan['service']['successor'])
    write_new(output / 'PARENT_GATE.json', plan['gate']['successor'])
    for actor, entry in plan['parents'].items():
        write_new(output / (actor + '.PARENT.json'), entry['successor'])
    return dict(status='PREPARED_NOT_ACTIVATED', plan_sha256=exchange.sha(encoded(plan)), output=str(output))


def process_absent(owner):
    require(type(owner['pid']) is int and owner['pid'] > 1
            and re.fullmatch('[0-9]+', owner['start_ticks']), 'exact_released_process_identity')
    process = Path('/proc') / str(owner['pid'])
    require(not process.exists(), 'old_owner_PID_still_present')


def approval(plan, scope, go_reference, release_reference):
    go, release = bound(go_reference), bound(release_reference)
    plan_sha = exchange.sha(encoded(plan))
    require(go.get('schema') == 'R157_COMMUNITY_SIDECAR_GO_V1' and go.get('decision') == 'GO'
            and go.get('approved_by') == 'Main' and go.get('authority_sha256') == AUTH_SHA
            and go.get('plan_sha256') == plan_sha and go.get('conflicting_real_reservation') is False,
            'explicit_bound_Main_GO_required')
    provenance = bound(go['reservation_provenance'])
    require(provenance.get('schema') == 'R157_NODE5_TARGETED_RESERVATION_AUDIT_V1'
            and provenance.get('authorization_sha256') == AUTH_SHA
            and provenance.get('host') == '[REDACTED_HOST]'
            and provenance.get('conflicting_real_reservation_found') is False,
            'bound_no_conflicting_reservation_evidence')
    require(release.get('schema') == 'R157_COMMUNITY_OWNER_RELEASE_V1'
            and release.get('plan_sha256') == plan_sha and release.get('scope') == scope
            and release.get('graceful') is True and release.get('remote_calls_settled') is True,
            'graceful_scoped_owner_release_required')
    expected = {'service': plan['service']['previous']['sha256']} if scope == 'service' else {
        actor: entry['previous']['sha256'] for actor, entry in plan['parents'].items()}
    require(set(release['owners']) == set(expected), 'exact_released_owners')
    if scope == 'parents':
        require(release.get('previous_parent_owner') == 'Euclid'
                and release.get('ownership_transfer_confirmed') is True, 'Euclid_parent_transfer_required')
    for role, config_sha in expected.items():
        owner = release['owners'][role]
        require(owner.get('config_sha256') == config_sha, 'released_owner_config_binding')
        process_absent(owner)
    return dict(go=go_reference, release=release_reference, plan_sha256=plan_sha, scope=scope)


def lock(stack, root, name):
    root = Path(root).resolve()
    directory = stack.enter_context(exchange.console._directory(root))
    current = os.fstat(directory)
    require(current.st_uid == os.geteuid() and current.st_mode & 0o077 == 0, 'private_owned_state_root')
    descriptor = os.open(name, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory)
    stack.callback(os.close, descriptor)
    current = os.fstat(descriptor)
    require(stat.S_ISREG(current.st_mode) and current.st_nlink == 1 and current.st_uid == os.geteuid(),
            'regular_owned_existing_lock')
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)


def database_fingerprint(database):
    hasher, used, count = hashlib.sha256(), 0, 0
    deadline = time.monotonic() + 120
    schema = database.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name").fetchall()
    hasher.update(encoded(schema))
    for name, in database.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        quoted = '"' + name.replace('"', '""') + '"'
        for row in database.execute('SELECT rowid,* FROM ' + quoted + ' ORDER BY rowid'):
            if name == 'metadata' and row[1] == 'service_config':
                continue
            data = encoded([dict(blob=value.hex()) if isinstance(value, bytes) else value for value in row])
            used += len(data)
            count += 1
            require(used <= LIMIT and count <= 1000000 and time.monotonic() < deadline, 'bounded_database_audit')
            hasher.update(encoded(name) + b'\n' + data + b'\n')
    return dict(sha256=hasher.hexdigest(), rows=count)


def parent_fingerprint(root):
    root = Path(root).resolve()
    hasher, used, count = hashlib.sha256(), 0, 0
    delivered, frontier = {}, 0
    pending = [root]
    while pending:
        directory = pending.pop()
        require(len(directory.relative_to(root).parts) <= 4, 'bounded_parent_depth')
        for path in sorted(directory.iterdir()):
            require(not path.is_symlink(), 'no_parent_state_symlinks')
            if path.is_dir():
                pending.append(path)
                require(len(pending) <= 10000, 'bounded_parent_directories')
                continue
            if path.parent == root and path.name in ('BINDING.json', 'PARENT.lock'):
                continue
            raw = read_bytes(path, 16 * 1024 * 1024)
            used += len(raw)
            count += 1
            require(used <= LIMIT and count <= 100000, 'bounded_parent_audit')
            hasher.update(encoded(str(path.relative_to(root))) + b'\n' + exchange.sha(raw).encode() + b'\n')
            if path.name == 'SOURCE.json':
                source = exchange.decode(raw)
                frontier = max(frontier, source['response_count'])
                result = exchange.decode(read_bytes(path.parent / 'RESULT.json'))
                require(result['source_sha256'] == exchange.sha(raw)
                        and result['status'] != 'PUBLICATION_UNKNOWN', 'settled_parent_attempt_required')
            if path.name == 'DELIVERED.json':
                receipt = exchange.decode(raw)
                require(receipt['status'] == 'RENDERED', 'rendered_consumption_receipt')
                key = receipt['object_id']
                delivered[key] = delivered.get(key, 0) + 1
    return dict(sha256=hasher.hexdigest(), files=count, response_frontier=frontier, consumed_by_object=delivered)


def evidence_intent(evidence, document):
    evidence = Path(evidence).resolve()
    if evidence.exists():
        require(exchange.decode(read_bytes(evidence / 'INTENT.json')) == document, 'exact_resumable_handoff_intent')
    else:
        evidence.mkdir(mode=0o700)
        write_new(evidence / 'INTENT.json', document)
    return evidence


def replace_binding(path, expected, successor):
    path = Path(path).resolve()
    current = read_bytes(path)
    if exchange.decode(current) == successor:
        return
    require(exchange.decode(current) == expected, 'previous_parent_binding_compare_and_swap')
    with exchange.console._directory(path.parent) as directory:
        exchange.immutable_file(directory, path.name, encoded(successor), replace_hashes=(exchange.sha(current),))


def handoff(bundle, scope, go_reference, release_reference, evidence):
    require(scope in ('service', 'parents'), 'explicit_handoff_scope')
    bundle = Path(bundle).resolve()
    plan = validate_plan(exchange.decode(read_bytes(bundle / 'PLAN.json')))
    control = approval(plan, scope, go_reference, release_reference)
    previous_service = bound(plan['service']['previous'])
    for name, expected in [('SERVICE.json', plan['service']['successor']), ('PARENT_GATE.json', plan['gate']['successor'])] + [
            (actor + '.PARENT.json', entry['successor']) for actor, entry in plan['parents'].items()]:
        require(read_bytes(bundle / name) == encoded(expected), 'unchanged_staged_successor')
    roots = [Path(previous_service['broker_root']).resolve()] + [Path(entry['output']).resolve() for entry in plan['parents'].values()]
    evidence = Path(evidence).resolve()
    require(all(evidence != root and root not in evidence.parents for root in roots)
            and evidence != bundle and bundle not in evidence.parents, 'external_handoff_evidence')
    with ExitStack() as stack:
        if scope == 'service':
            root = roots[0]
            lock(stack, root, 'SERVICE_OWNER.lock')
            lock(stack, root, 'LOCK')
            for name in ('state.sqlite3', 'state.sqlite3-wal', 'state.sqlite3-shm', 'state.sqlite3-journal'):
                path = root / name
                if path.exists() or path.is_symlink():
                    current = path.lstat()
                    require(stat.S_ISREG(current.st_mode) and current.st_nlink == 1
                            and current.st_uid == os.geteuid() and current.st_mode & 0o077 == 0
                            and current.st_size <= LIMIT, 'private_bounded_database')
            require((root / 'state.sqlite3').is_file(), 'existing_broker_only')
            database = sqlite3.connect((root / 'state.sqlite3').as_uri() + '?mode=rw', uri=True, isolation_level=None)
            stack.callback(database.close)
            current = database.execute("SELECT value FROM metadata WHERE key='service_config'").fetchone()
            require(current is not None and current[0] in (encoded(previous_service), encoded(plan['service']['successor'])),
                    'exact_existing_service_binding')
            before = database_fingerprint(database)
            intent = dict(control, preserved=before)
            if not evidence.exists():
                require(current[0] == encoded(previous_service), 'new_evidence_requires_previous_config')
            evidence = evidence_intent(evidence, intent)
            backup_path = evidence / 'BEFORE.sqlite3'
            if not backup_path.exists():
                require(current[0] == encoded(previous_service), 'backup_before_rebinding')
                with sqlite3.connect(str(backup_path)) as backup:
                    database.backup(backup)
                os.chmod(backup_path, 0o400)
            with sqlite3.connect(backup_path.as_uri() + '?mode=ro', uri=True) as backup:
                require(database_fingerprint(backup) == before
                        and backup.execute("SELECT value FROM metadata WHERE key='service_config'").fetchone()[0]
                        == encoded(previous_service), 'exact_previous_backup')
            database.execute('PRAGMA synchronous=FULL')
            database.execute('BEGIN IMMEDIATE')
            try:
                database.execute("UPDATE metadata SET value=? WHERE key='service_config' AND value=?",
                    (encoded(plan['service']['successor']), encoded(previous_service)))
                require(database_fingerprint(database) == before, 'all_nonconfig_rows_preserved')
                database.commit()
            except BaseException:
                database.rollback()
                raise
        else:
            for actor in parents.LEARNERS:
                lock(stack, plan['parents'][actor]['output'], 'PARENT.lock')
            changes, fingerprints = {}, {}
            for actor, entry in plan['parents'].items():
                old = bound(entry['previous'])
                previous = dict(config_sha256=entry['previous']['sha256'], root=old['root'], branch=actor,
                    gate_sha256=plan['gate']['previous']['sha256'])
                successor = dict(previous, config_sha256=exchange.sha(encoded(entry['successor'])),
                    gate_sha256=exchange.sha(encoded(plan['gate']['successor'])))
                path = Path(entry['output']).resolve() / 'BINDING.json'
                require(exchange.decode(read_bytes(path)) in (previous, successor), 'exact_existing_parent_binding')
                changes[actor] = dict(path=str(path), previous=previous, successor=successor)
                fingerprints[actor] = parent_fingerprint(entry['output'])
            if not evidence.exists():
                require(all(exchange.decode(read_bytes(change['path'])) == change['previous'] for change in changes.values()),
                        'new_evidence_requires_previous_bindings')
            evidence = evidence_intent(evidence, dict(control, preserved=fingerprints, binding_changes=changes))
            for actor, change in changes.items():
                replace_binding(change['path'], change['previous'], change['successor'])
            require({actor: parent_fingerprint(entry['output']) for actor, entry in plan['parents'].items()}
                    == fingerprints, 'all_parent_ledgers_preserved')
        result = dict(control, status='APPLIED_NOT_LAUNCHED', hard_end_unix=HARD_END, reset=False)
        write_new(evidence / 'APPLIED.json', result)
        return result


def programme_state(output, config):
    output = Path(output)
    require(output.is_dir() and not output.is_symlink(), 'existing_programme_output')
    clock = 'request_count' if config.get('schedule_on') == 'request' else 'response_count'
    last_count = config.get('start_after_' + clock, 0)
    segment = json.loads(read_bytes(output / 'SEGMENT.json'))
    started = json.loads(read_bytes(output / 'STARTED.json'))
    require(started['branch'] == config['branch'] and started['programme'] == config['programme'],
            'same_programme_parent_branch')
    attempts = sorted(output.glob('parent_*'))
    delivered, files, used = 0, {}, 0
    for position, directory in enumerate(attempts):
        require(directory.name == 'parent_' + str(position).zfill(6)
                and directory.is_dir() and not directory.is_symlink(), 'contiguous_parent_call_slots')
        source_raw = read_bytes(directory / 'SOURCE.json', 16 * 1024 * 1024)
        source = json.loads(source_raw)
        result = json.loads(read_bytes(directory / 'RESULT.json'))
        require(type(source[clock]) is int and source[clock] > last_count, 'strict_reserved_parent_frontier')
        require(result['schedule_count'] == source[clock]
                and result['source_response_count'] == source['response_count']
                and result['source_head_sha256'] == source['head_sha256']
                and result['branch'] == config['branch'] and result['programme'] == config['programme']
                and result['status'] in ('PUBLISHED', 'SILENT', 'MISSING')
                and result['finished_unix'] >= result['started_unix'], 'settled_bound_programme_result')
        intent = json.loads(read_bytes(directory / 'DISPATCH_INTENT.json'))
        require(intent['source_sha256'] == hashlib.sha256(source_raw).hexdigest()
                and intent['schedule_count'] == source[clock], 'original_dispatch_reservation')
        if result['status'] == 'PUBLISHED':
            require(type(result.get('inbox_publication')) is dict, 'original_parent_publication')
        if (directory / 'DELIVERED.json').exists():
            receipt = json.loads(read_bytes(directory / 'DELIVERED.json'))
            require(receipt['status'] == 'COMPLETE' and receipt['speaker'] == 'Astra'
                    and receipt['result_sha256'] == hashlib.sha256(read_bytes(directory / 'RESULT.json')).hexdigest(),
                    'original_Astra_consumption')
            delivered += 1
        last_count = source[clock]
    pending = [output]
    while pending:
        directory = pending.pop()
        require(len(directory.relative_to(output).parts) <= 4, 'bounded_programme_depth')
        for path in sorted(directory.iterdir()):
            require(not path.is_symlink(), 'unlinked_programme_state')
            if path.is_dir():
                pending.append(path)
                require(len(pending) <= 10000, 'bounded_programme_directories')
            elif path.name != 'R157_PARENT.lock' or path.parent != output:
                raw = read_bytes(path, 16 * 1024 * 1024)
                used += len(raw)
                require(used <= LIMIT and len(files) < 100000, 'bounded_programme_ledger')
                files[str(path.relative_to(output))] = hashlib.sha256(raw).hexdigest()
    return dict(last_count=last_count, calls=len(attempts), baseline=segment['baseline_response_count'],
                delivered=delivered, files=files)


def _r157_read(reference_value):
    raw = read_bytes(reference_value['path'])
    require(hashlib.sha256(raw).hexdigest() == reference_value['sha256'], 'pinned_programme_resume_input')
    return json.loads(raw)


@contextmanager
def _r157_lock(output):
    require(Path(output).is_dir(), 'same_existing_programme_state')
    descriptor = os.open(Path(output) / 'R157_PARENT.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'a') as lockfile:
        current = os.fstat(lockfile.fileno())
        require(stat.S_ISREG(current.st_mode) and current.st_nlink == 1
                and current.st_uid == os.geteuid(), 'owned_programme_lock')
        fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def _r157_guard(config_path, output, config):
    spec = _r157_read(R157_SPEC)
    require(spec['schema'] == 'R157_PROTECTED_PARENT_RESUME_V1' and spec['approved_by'] == 'Main'
            and spec['graceful_owner_release'] is True, 'explicit_protected_parent_GO')
    require(spec['authority']['sha256'] == AUTH_SHA, 'exact_R157_authority')
    _r157_read(spec['authority'])
    provenance = _r157_read(spec['provenance'])
    require(provenance['authorization_sha256'] == AUTH_SHA
            and provenance['conflicting_real_reservation_found'] is False, 'no_actual_reservation_conflict')
    previous = _r157_read(spec['previous_config'])
    require(config == dict(previous, hard_end_unix=HARD_END)
            and config == _r157_read(spec['successor_config'])
            and str(Path(config_path).resolve()) == str(Path(spec['successor_config']['path']).resolve())
            and str(Path(output).resolve()) == str(Path(spec['output']).resolve()), 'programme_deadline_only_same_output')
    require(config['root'] in ('/localhome/local-rohing/orch_r125_continual_20260916_attempt1/run1',
                              '/localhome/local-rohing/orch_r127_pilot_20260916_attempt1/run1'), 'exact_protected_life_roots')
    require(not (Path('/proc') / str(spec['previous_owner']['pid'])).exists(), 'old_programme_owner_absent')
    require(hashlib.sha256(read_bytes(spec['original_source']['path'])).hexdigest()
            == spec['original_source']['sha256'] == PROGRAMME_SOURCE_SHA, 'unchanged_original_programme_source')
    for name, digest in spec['before']['files'].items():
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts, 'relative_parent_evidence')
        require(hashlib.sha256(read_bytes(Path(output) / relative, 16 * 1024 * 1024)).hexdigest() == digest,
                'original_parent_evidence_preserved')
    current = programme_state(output, config)
    require(current['last_count'] >= spec['before']['last_count']
            and current['calls'] >= spec['before']['calls'] and current['baseline'] == spec['before']['baseline'],
            'no_parent_cursor_or_baseline_reset')
    return current


def _r157_started(config_path, output, config, state, transport):
    spec = _r157_read(R157_SPEC)
    path = Path(spec['receipt_directory']) / ('RESUMED_' + str(os.getpid()) + '.json')
    write(path, dict(schema='R157_PROGRAMME_PARENT_RUNNING_V1', pid=os.getpid(),
        config_sha256=hashlib.sha256(read_bytes(config_path)).hexdigest(), root=config['root'],
        output=str(output), hard_end_unix=config['hard_end_unix'], branch=config['branch'],
        baseline=state['baseline'], last_count=state['last_count'], next_call=state['calls'],
        delivered=state['delivered'], transport=transport, observed_unix=time.time()))


def programme_resume_source(original_raw, spec_reference):
    require(hashlib.sha256(original_raw).hexdigest() == PROGRAMME_SOURCE_SHA, 'reviewed_programme_source_only')
    tree = ast.parse(original_raw)
    serve = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'serve')
    original_loop = next(node for node in serve.body if isinstance(node, ast.While))
    body, replacements = [], set()
    for node in serve.body:
        rendered = ast.unparse(node)
        if rendered.startswith('output.mkdir('):
            replacements.add('mkdir')
            continue
        if rendered.startswith("write(output / 'STARTED.json',"):
            node = ast.parse('_r157_started(config_path, output, config, _r157_resume, transport)').body[0]
            replacements.add('started')
        elif rendered == 'last_count = resume_cursor(config)':
            node = ast.parse("last_count = _r157_resume['last_count']").body[0]
            replacements.add('last_count')
        elif rendered == 'calls = 0':
            node = ast.parse("calls = _r157_resume['calls']").body[0]
            replacements.add('calls')
        elif rendered == 'baseline = None':
            node = ast.parse("baseline = _r157_resume['baseline']").body[0]
            replacements.add('baseline')
        body.append(node)
        if rendered == 'config = validate(json.loads(config_path.read_text()))':
            body.append(ast.parse('_r157_resume = _r157_guard(config_path, output, config)').body[0])
            replacements.add('guard')
    require(replacements == {'mkdir', 'started', 'last_count', 'calls', 'baseline', 'guard'}, 'exact_programme_startup_sites')
    require(ast.dump(original_loop) == ast.dump(next(node for node in body if isinstance(node, ast.While))),
            'unchanged_entire_parent_learning_loop')
    serve.body = [body[0], ast.With(items=[ast.withitem(context_expr=ast.parse('_r157_lock(output)', mode='eval').body)],
                                  body=body[1:])]
    ast.fix_missing_locations(tree)
    prefix = ('import hashlib, json, os, stat, time, fcntl\nfrom pathlib import Path\n'
              'from contextlib import contextmanager\n' + repr('Exact R157 protected-parent startup adapter; original policy loop unchanged.') + '\n'
              + f'AUTH_SHA={AUTH_SHA!r}\nHARD_END={HARD_END!r}\nLIMIT={LIMIT!r}\n'
              + f'PROGRAMME_SOURCE_SHA={PROGRAMME_SOURCE_SHA!r}\nR157_SPEC={spec_reference!r}\n')
    for function in (read_bytes, programme_state, _r157_read, _r157_lock, _r157_guard, _r157_started):
        prefix += '\n' + inspect.getsource(function) + '\n'
    source = prefix + '\n' + ast.unparse(tree) + '\n'
    compile(source, '<R157 protected parent resume>', 'exec')
    return source


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    prepare_parser = modes.add_parser('prepare')
    prepare_parser.add_argument('--inputs', type=Path, required=True)
    prepare_parser.add_argument('--output', type=Path, required=True)
    apply_parser = modes.add_parser('handoff')
    apply_parser.add_argument('--bundle', type=Path, required=True)
    apply_parser.add_argument('--scope', choices=('service', 'parents'), required=True)
    for name in ('go', 'release', 'evidence'):
        apply_parser.add_argument('--' + name, type=Path, required=True)
    for name in ('go', 'release'):
        apply_parser.add_argument('--' + name + '-sha256', required=True)
    options = parser.parse_args(argv)
    if options.mode == 'prepare':
        inputs = exchange.decode(read_bytes(options.inputs.absolute()))
        result = stage(prepare(**inputs), options.output)
    else:
        result = handoff(options.bundle, options.scope,
            dict(path=str(options.go.absolute()), sha256=options.go_sha256),
            dict(path=str(options.release.absolute()), sha256=options.release_sha256), options.evidence)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
