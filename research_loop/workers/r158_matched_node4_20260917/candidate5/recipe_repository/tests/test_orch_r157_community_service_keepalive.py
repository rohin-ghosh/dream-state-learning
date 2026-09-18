from copy import deepcopy
import ast
import fcntl
import json
import os
from pathlib import Path
import sqlite3

import pytest

from gpu import orch_r157_community_service_keepalive as keepalive


REPOSITORY = Path(__file__).resolve().parents[1]


def write(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(keepalive.encoded(document))
    return keepalive.reference(path)


@pytest.fixture
def prepared(tmp_path):
    original = json.loads((REPOSITORY / 'research_loop/workers/r153_service_v4_20260917/SERVICE_CONFIG_V4.json').read_text())
    broker = tmp_path / 'broker'
    broker.mkdir(mode=0o700)
    original['broker_root'] = str(broker)
    original['mirror_root'] = str(tmp_path / 'mirrors')
    original['repository'] = str(REPOSITORY)
    service_path = tmp_path / 'previous_service.json'
    write(service_path, original)
    for name in ('LOCK', 'SERVICE_OWNER.lock'):
        (broker / name).touch(mode=0o600)
    with sqlite3.connect(broker / 'state.sqlite3') as database:
        database.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value BLOB)')
        database.execute('INSERT INTO metadata VALUES (?,?)', ('service_config', keepalive.encoded(original)))
        database.execute('CREATE TABLE service_jobs(id TEXT,status TEXT,snapshot BLOB,outcome BLOB)')
        database.executemany('INSERT INTO service_jobs VALUES (?,?,?,?)', [
            ('known', 'CPU_DONE', b'snapshot', b'receipt'), ('unknown', 'CPU_UNKNOWN', b'original', None),
            ('intent', 'CPU_INTENT', b'no_replay', None), ('pending', 'PENDING', b'new', None)])
        database.execute('CREATE TABLE service_cursors(actor TEXT,next_index INTEGER,head TEXT)')
        database.execute("INSERT INTO service_cursors VALUES ('C1',777,'pinned_head')")
        database.execute('CREATE TABLE deliveries(handle TEXT,delivered INTEGER,packet BLOB)')
        database.execute("INSERT INTO deliveries VALUES ('stable_handle',0,?)", (b'unchanged_packet',))
        database.execute('CREATE TABLE artifacts(id TEXT,content BLOB)')
        database.execute("INSERT INTO artifacts VALUES ('chosen_publication',?)", (b'private chosen text',))
    (broker / 'state.sqlite3').chmod(0o600)
    old_directory = REPOSITORY / 'research_loop/workers/r153_measurement_parent_node5_staging_20260916'
    gate = json.loads((old_directory / 'MAIN_GATE.json').read_text())
    parent_paths = {}
    for actor in keepalive.parents.LEARNERS:
        config = json.loads((old_directory / 'prepared' / (actor + '.PARENT.json')).read_text())
        output = tmp_path / actor
        output.mkdir(mode=0o700)
        (output / 'PARENT.lock').touch(mode=0o600)
        parent_paths[actor] = str(tmp_path / (actor + '.previous.json'))
        config_ref = write(Path(parent_paths[actor]), config)
        gate['parents'][actor]['output'] = str(output)
        gate['parents'][actor]['config_sha256'] = config_ref['sha256']
        attempt = output / 'parent_000000000030'
        source = write(attempt / 'SOURCE.json', dict(response_count=30, journal_id=original['agents'][actor]['journal_id']))
        write(attempt / 'RESULT.json', dict(status='PUBLISHED', source_sha256=source['sha256'], speaker='Astra'))
        write(attempt / 'DELIVERED.json', dict(status='RENDERED', object_id='existing_object'))
        write(attempt / 'OBJECT_STATE.json', dict(object_delivered_turns={'existing_object': 1}, last_response_count=30))
    gate_path = tmp_path / 'previous_gate.json'
    gate_ref = write(gate_path, gate)
    for actor in keepalive.parents.LEARNERS:
        write(tmp_path / actor / 'BINDING.json', dict(root=original['agents'][actor]['root'], branch=actor,
            config_sha256=gate['parents'][actor]['config_sha256'], gate_sha256=gate_ref['sha256']))
    plan = keepalive.prepare(str(REPOSITORY / 'research_loop/workers/r157_keepalive_20260917/AUTHORIZATION.json'),
        str(service_path), parent_paths, str(gate_path))
    bundle = tmp_path / 'bundle'
    keepalive.stage(plan, bundle)
    return plan, bundle, tmp_path


def permissions(plan, root, scope, monkeypatch):
    monkeypatch.setattr(keepalive, 'process_absent', lambda owner: None)
    plan_sha = keepalive.exchange.sha(keepalive.encoded(plan))
    go = write(root / (scope + '_go.json'), dict(schema='R157_COMMUNITY_SIDECAR_GO_V1', decision='GO',
        approved_by='Main', authority_sha256=keepalive.AUTH_SHA, plan_sha256=plan_sha, conflicting_real_reservation=False,
        reservation_provenance=keepalive.reference(REPOSITORY / 'research_loop/workers/r157_community_wall_20260917/PROVENANCE.json')))
    configs = {'service': plan['service']['previous']} if scope == 'service' else {
        actor: entry['previous'] for actor, entry in plan['parents'].items()}
    release = write(root / (scope + '_release.json'), dict(schema='R157_COMMUNITY_OWNER_RELEASE_V1',
        plan_sha256=plan_sha, scope=scope, graceful=True, remote_calls_settled=True,
        previous_parent_owner='Euclid', ownership_transfer_confirmed=True,
        owners={role: dict(pid=99999999, start_ticks='1', config_sha256=entry['sha256']) for role, entry in configs.items()}))
    return go, release


def test_prepare_only_deadlines_no_live_changes(prepared):
    plan, bundle, root = prepared
    previous = keepalive.bound(plan['service']['previous'])
    expected = dict(previous, deadline_unix=keepalive.HARD_END)
    assert plan['service']['successor'] == expected
    for entry in plan['parents'].values():
        old = keepalive.bound(entry['previous'])
        assert entry['successor'] == dict(old, hard_end_unix=keepalive.HARD_END)
        assert old['object_turn_limit'] == old['cadence_responses'] == 3
    with sqlite3.connect(root / 'broker/state.sqlite3') as database:
        assert json.loads(database.execute('SELECT value FROM metadata').fetchone()[0]) == previous
    assert (bundle / 'PLAN.json').exists()


@pytest.mark.parametrize('fault', ['deadline', 'gate', 'quota', 'root', 'cadence', 'object', 'policy', 'frontier'])
def test_plan_refuses_non_deadline_deltas(prepared, fault):
    plan, unused_bundle, unused_root = prepared
    damaged = deepcopy(plan)
    if fault == 'deadline':
        damaged['service']['successor']['deadline_unix'] += 1
    elif fault == 'gate':
        damaged['gate']['successor']['status'] = 'RELAXED'
    elif fault == 'quota':
        damaged['service']['successor']['max_cpu_calls_per_actor'] += 1
    elif fault == 'root':
        damaged['service']['successor']['broker_root'] += '_new'
    else:
        field = {'cadence': 'cadence_responses', 'object': 'object_turn_limit', 'policy': 'parent_style',
                 'frontier': 'start_after_response_count'}[fault]
        damaged['parents']['C1']['successor'][field] = 999
    with pytest.raises(ValueError, match='exact_deadline_only_plan'):
        keepalive.validate_plan(damaged)


def test_service_handoff_preserves_inflight_all_rows_and_resumes(prepared, monkeypatch):
    plan, bundle, root = prepared
    go, release = permissions(plan, root, 'service', monkeypatch)
    with sqlite3.connect(root / 'broker/state.sqlite3') as database:
        before = keepalive.database_fingerprint(database)
    evidence = root / 'service_evidence'
    assert keepalive.handoff(bundle, 'service', go, release, evidence)['status'] == 'APPLIED_NOT_LAUNCHED'
    with sqlite3.connect(root / 'broker/state.sqlite3') as database:
        assert keepalive.database_fingerprint(database) == before
        assert json.loads(database.execute('SELECT value FROM metadata').fetchone()[0]) == plan['service']['successor']
    assert (evidence / 'BEFORE.sqlite3').is_file()
    keepalive.handoff(bundle, 'service', go, release, evidence)


def test_parent_handoff_preserves_rendered_budget_and_resumes(prepared, monkeypatch):
    plan, bundle, root = prepared
    go, release = permissions(plan, root, 'parents', monkeypatch)
    before = {actor: keepalive.parent_fingerprint(entry['output']) for actor, entry in plan['parents'].items()}
    keepalive.handoff(bundle, 'parents', go, release, root / 'parent_evidence')
    for actor, entry in plan['parents'].items():
        assert keepalive.parent_fingerprint(entry['output']) == before[actor]
        assert before[actor]['consumed_by_object'] == {'existing_object': 1}
        assert before[actor]['response_frontier'] == 30
        binding = json.loads((root / actor / 'BINDING.json').read_text())
        assert binding['config_sha256'] == keepalive.exchange.sha(keepalive.encoded(entry['successor']))
    keepalive.handoff(bundle, 'parents', go, release, root / 'parent_evidence')


@pytest.mark.parametrize('scope', ['service', 'parents'])
def test_live_owner_lock_blocks_before_mutation(prepared, monkeypatch, scope):
    plan, bundle, root = prepared
    go, release = permissions(plan, root, scope, monkeypatch)
    path = root / ('broker/SERVICE_OWNER.lock' if scope == 'service' else 'C3/PARENT.lock')
    with path.open('r+') as owner:
        fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            keepalive.handoff(bundle, scope, go, release, root / 'blocked')
    assert not (root / 'blocked').exists()


@pytest.mark.parametrize('fault', ['authority', 'no_go', 'conflict', 'release', 'ownership'])
def test_missing_authority_GO_reservation_or_release_blocks(prepared, monkeypatch, fault):
    plan, bundle, root = prepared
    go, release = permissions(plan, root, 'parents', monkeypatch)
    selected = go if fault in ('authority', 'no_go', 'conflict') else release
    document = keepalive.bound(selected)
    field, value = {'authority': ('authority_sha256', 'f' * 64), 'no_go': ('decision', 'WAIT'),
                    'conflict': ('conflicting_real_reservation', True), 'release': ('graceful', False),
                    'ownership': ('ownership_transfer_confirmed', False)}[fault]
    document[field] = value
    changed = write(root / 'changed.json', document)
    if selected is go:
        go = changed
    else:
        release = changed
    with pytest.raises(ValueError):
        keepalive.handoff(bundle, 'parents', go, release, root / 'blocked')
    assert not (root / 'blocked').exists()


@pytest.mark.parametrize('fault', ['missing_result', 'publication_unknown', 'hardlink', 'symlink'])
def test_parent_ambiguity_and_filesystem_escape_fail_closed(prepared, monkeypatch, fault):
    plan, bundle, root = prepared
    go, release = permissions(plan, root, 'parents', monkeypatch)
    result = root / 'C1/parent_000000000030/RESULT.json'
    if fault == 'missing_result':
        result.unlink()
    elif fault == 'publication_unknown':
        document = json.loads(result.read_text())
        document['status'] = 'PUBLICATION_UNKNOWN'
        write(result, document)
    elif fault == 'hardlink':
        os.link(result, root / 'alias.json')
    else:
        (root / 'C1/escape').symlink_to(root / 'C2', target_is_directory=True)
    with pytest.raises((ValueError, OSError)):
        keepalive.handoff(bundle, 'parents', go, release, root / 'blocked')
    assert not (root / 'blocked').exists()


def test_interrupted_parent_rebinding_resumes_without_ledger_reset(prepared, monkeypatch):
    plan, bundle, root = prepared
    go, release = permissions(plan, root, 'parents', monkeypatch)
    original = keepalive.replace_binding
    calls = []

    def interrupted(*args):
        calls.append(args)
        if len(calls) == 3:
            raise RuntimeError('simulated process interruption')
        return original(*args)

    with monkeypatch.context() as patcher:
        patcher.setattr(keepalive, 'replace_binding', interrupted)
        with pytest.raises(RuntimeError):
            keepalive.handoff(bundle, 'parents', go, release, root / 'resumable')
    keepalive.handoff(bundle, 'parents', go, release, root / 'resumable')
    assert (root / 'resumable/APPLIED.json').exists()


def test_existing_pid_cannot_be_claimed_released():
    with pytest.raises(ValueError, match='old_owner_PID_still_present'):
        keepalive.process_absent(dict(pid=os.getpid(), start_ticks='1'))


@pytest.fixture(params=['RUN1', 'PILOT'])
def programme_resume(tmp_path, request):
    parent_base = Path('/data/home/rohing/courier/r133_programme_parents_20260916')
    filename = 'RUN1_R138_SPARSE3_TRANSPORT2_CONFIG.json' if request.param == 'RUN1' else 'PILOT_R140_SPARSE2_RESUME_CONFIG.json'
    previous = json.loads((parent_base / filename).read_text())
    old_ref = write(tmp_path / 'old.json', previous)
    successor = dict(previous, hard_end_unix=keepalive.HARD_END)
    new_ref = write(tmp_path / 'new.json', successor)
    output = tmp_path / 'output'
    baseline = previous['start_after_response_count']
    write(output / 'STARTED.json', dict(branch=previous['branch'], programme=previous['programme'], pid=99999999))
    write(output / 'SEGMENT.json', dict(baseline_response_count=baseline))
    for position in range(2):
        count = baseline + (position + 1) * previous['cadence_responses']
        directory = output / ('parent_' + str(position).zfill(6))
        source = write(directory / 'SOURCE.json', dict(response_count=count, head_sha256='a' * 64))
        write(directory / 'DISPATCH_INTENT.json', dict(source_sha256=source['sha256'], schedule_count=count))
        result = write(directory / 'RESULT.json', dict(status='PUBLISHED', inbox_publication={'id': str(position)},
            source_response_count=count, source_head_sha256='a' * 64, schedule_count=count,
            branch=previous['branch'], programme=previous['programme'], started_unix=1, finished_unix=2))
        if position == 0:
            write(directory / 'DELIVERED.json', dict(status='COMPLETE', speaker='Astra', result_sha256=result['sha256']))
    state = keepalive.programme_state(output, previous)
    source_path = REPOSITORY / 'gpu/orch_r133_programme_parent.py'
    spec = dict(schema='R157_PROTECTED_PARENT_RESUME_V1', approved_by='Main', graceful_owner_release=True,
        authority=keepalive.reference(REPOSITORY / 'research_loop/workers/r157_keepalive_20260917/AUTHORIZATION.json'),
        provenance=keepalive.reference(REPOSITORY / 'research_loop/workers/r157_community_wall_20260917/PROVENANCE.json'),
        previous_config=old_ref, successor_config=new_ref, output=str(output), previous_owner=dict(pid=99999999),
        original_source=keepalive.reference(source_path), before=state, receipt_directory=str(tmp_path))
    spec_ref = write(tmp_path / 'SPEC.json', spec)
    code = keepalive.programme_resume_source(source_path.read_bytes(), spec_ref)
    namespace = {'__name__': '_r157_test_parent'}
    exec(compile(code, 'generated_parent.py', 'exec'), namespace)
    return namespace, spec, spec_ref, code, source_path.read_bytes()


def test_programme_adapter_preserves_entire_loop_and_policy_AST(programme_resume):
    unused_namespace, unused_spec, unused_ref, code, original = programme_resume
    previous = {node.name: node for node in ast.parse(original).body if isinstance(node, ast.FunctionDef)}
    successor = {node.name: node for node in ast.parse(code).body if isinstance(node, ast.FunctionDef)}
    for name, node in previous.items():
        if name == 'serve':
            old_loop = next(item for item in ast.walk(node) if isinstance(item, ast.While))
            new_loop = next(item for item in ast.walk(successor[name]) if isinstance(item, ast.While))
            assert ast.dump(old_loop) == ast.dump(new_loop)
        else:
            assert ast.dump(node) == ast.dump(successor[name])


def test_programme_resume_preserves_baseline_and_skips_reserved_turns(programme_resume):
    namespace, spec, unused_ref, unused_code, unused_source = programme_resume
    seen = []
    namespace['transport_preflight'] = lambda *args: {'fixture': True}
    namespace['record_deliveries'] = lambda *args: None
    namespace['snapshot'] = lambda *args: dict(response_count=spec['before']['last_count'])
    namespace['strong'] = lambda *args, **kwargs: seen.append('forbidden_replay')
    namespace['serve'](spec['successor_config']['path'], str(REPOSITORY), spec['output'], once=True)
    assert seen == []
    state = keepalive.programme_state(spec['output'], keepalive.bound(spec['previous_config']))
    assert state == spec['before']
    assert json.loads((Path(spec['output']) / 'STARTED.json').read_text())['pid'] == 99999999


def test_programme_next_new_turn_uses_existing_cadence_and_new_slot(programme_resume):
    namespace, spec, unused_ref, unused_code, unused_source = programme_resume
    config = keepalive.bound(spec['successor_config'])
    next_count = spec['before']['last_count'] + config['cadence_responses']
    namespace['transport_preflight'] = lambda *args: {'fixture': True}
    namespace['record_deliveries'] = lambda *args: None
    namespace['snapshot'] = lambda *args: dict(response_count=next_count, head_sha256='b' * 64)
    namespace['prompt'] = lambda *args: ('unchanged policy fixture', 'fixture')
    namespace['strong'] = lambda *args, **kwargs: ({'speak': False, 'message': '', 'rationale': ''}, namespace['STRONG'], {})
    namespace['serve'](spec['successor_config']['path'], str(REPOSITORY), spec['output'], once=True)
    state = keepalive.programme_state(spec['output'], config)
    assert state['last_count'] == next_count and state['calls'] == 3
    assert state['baseline'] == spec['before']['baseline'] and state['delivered'] == 1
    for name, digest in spec['before']['files'].items():
        assert keepalive.reference(Path(spec['output']) / name)['sha256'] == digest


def test_programme_incomplete_attempt_is_not_replayed(programme_resume):
    namespace, spec, unused_ref, unused_code, unused_source = programme_resume
    directory = Path(spec['output']) / 'parent_000002'
    write(directory / 'SOURCE.json', dict(response_count=999, head_sha256='c' * 64))
    with pytest.raises(FileNotFoundError):
        keepalive.programme_state(spec['output'], keepalive.bound(spec['previous_config']))


def test_programme_refuses_rewritten_past_receipts(programme_resume):
    namespace, spec, unused_ref, unused_code, unused_source = programme_resume
    write(Path(spec['output']) / 'SEGMENT.json', dict(baseline_response_count=0))
    config = keepalive.bound(spec['successor_config'])
    with pytest.raises(ValueError, match='original_parent_evidence_preserved'):
        namespace['_r157_guard'](spec['successor_config']['path'], spec['output'], config)


def test_programme_adapter_rejects_unknown_original_source():
    with pytest.raises(ValueError, match='reviewed_programme_source_only'):
        keepalive.programme_resume_source(b'def serve(): pass', {'path': '/tmp/not_used', 'sha256': 'a' * 64})
