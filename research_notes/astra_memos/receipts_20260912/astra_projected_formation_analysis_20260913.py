"""Offline paired projection capsule analysis; author reproduction, not review."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tarfile

sys.dont_write_bytecode = True
PROTOCOL = 'projected_auth_off_rulegame_formation_run_v1_20260913'
ROLE_SHA = '2cb24cf0447d3e5a7d8e61c9a0a65658e033f2c0bfc01b4b60ae15bce437a945'
PROJECTION_SHA = '47564a630b166cadda546ac5ae65c79bd9ca223a8574b0cfc693d6bc0177ad19'
MAX_FILE, MAX_TOTAL, MAX_MEMBERS = 32*1024*1024, 256*1024*1024, 2048
PREFIX = 'metadata/formation/'
DATA = 'run/formation/data/'
LIMITS = dict(wake=40, record=12, parent=4, restate=4)
TOKENS = dict(wake=400, record=100, parent=200, restate=120)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def stream_hash(stream):
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024*1024), b''):
        digest.update(chunk)
    return digest.hexdigest()


def decode(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('nonfinite JSON constant: '+value)
    return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)


def file_bytes(filename, limit=MAX_TOTAL):
    path = Path(filename)
    require(path.is_file() and not path.is_symlink(), 'regular input file required')
    with path.open('rb') as stream:
        data = stream.read(limit+1)
    require(len(data) <= limit, 'input size limit')
    return data


def allowed_names():
    names = {'plan.json', 'plan.sha256.json', 'normalized_birth.json', 'preparation.started.json',
             'collection.claim.json', 'run/controller.json', 'run/result.json', 'run/formation/receipt.json'}
    names.update('run/formation/worker/'+name for name in ('process.json', 'supervision.json', 'stdout.log'))
    names.update(DATA+name for name in ('isolation.json', 'backend.ready.json', 'backend.cleanup.json',
                                      'capture.json', 'capture_barrier.json', 'manifest.json'))
    names.update(DATA+f'calls/{index:04d}.{kind}.json' for index in range(60) for kind in ('request', 'response'))
    return ({PREFIX+name for name in names} |
            {'metadata/launch/'+name for name in ('launch.json', 'exit.json', 'gpu.xml', 'controller.log', 'launcher.log')} |
            {'metadata/collection/'+name for name in ('started.json', 'initial_vacancy.xml', 'audit.json')})


def load_capsule(archive, validation, validation_sha256):
    receipt_bytes = file_bytes(validation, MAX_FILE)
    require(sha(receipt_bytes) == validation_sha256, 'validation hash mismatch')
    receipt = decode(receipt_bytes)
    require(receipt['protocol'] == PROTOCOL and receipt['status'] == 'COLLECTED_RELEASED'
            and receipt['phase_complete'] is True and receipt['full_release'] is True,
            'completed and released phase required')
    require(receipt['costs_nested_not_added'] is True and receipt['automatic_progression'] is False
            and receipt['archived_adapter_bytes'] is False, 'collection claim boundary mismatch')
    require(0 < receipt['collection_seconds'] <= 300, 'collection bound mismatch')
    pins = receipt['archive_files']
    require(isinstance(pins, dict) and 0 < len(pins) <= MAX_MEMBERS and set(pins) <= allowed_names(),
            'unknown/extra archive members')
    require(all(isinstance(pin, str) and re.fullmatch('[0-9a-f]{64}', pin) for pin in pins.values()), 'invalid member hashes')
    members, total = {}, 0
    with Path(archive).open('rb') as stream:
        require(not Path(archive).is_symlink(), 'archive symlink')
        digest = stream_hash(stream)
        require(digest == receipt['archive_sha256'], 'archive hash mismatch')
        stream.seek(0)
        with tarfile.open(fileobj=stream, mode='r:gz') as bundle:
            for member in bundle:
                name = PurePosixPath(member.name)
                require(member.isfile() and not member.issym() and not member.islnk()
                        and not name.is_absolute() and '..' not in name.parts and str(name) == member.name
                        and member.name in pins and member.name not in members, 'unsafe/extra/duplicate member')
                total += member.size
                require(0 <= member.size <= MAX_FILE and total <= MAX_TOTAL, 'archive size bound')
                data = bundle.extractfile(member).read(MAX_FILE+1)
                require(len(data) == member.size and sha(data) == pins[member.name], 'member hash mismatch')
                members[member.name] = data
        stream.seek(0)
        require(stream_hash(stream) == digest, 'archive changed during read')
    require(set(members) == set(pins), 'missing archive members')
    return dict(archive=str(Path(archive).absolute()), validation=str(Path(validation).absolute()),
                validation_sha256=validation_sha256, receipt=receipt, members=members)


def load_role(source):
    source = Path(source).absolute()
    for name, pin in (('born_rulegame_formation.py', ROLE_SHA), ('rulegame_action_projection.py', PROJECTION_SHA)):
        require(sha(file_bytes(source/'organism_v6'/name)) == pin, 'frozen replay source mismatch')
    sys.path.insert(0, str(source))
    role = importlib.import_module('organism_v6.born_rulegame_formation')
    require(Path(role.__file__).absolute() == source/'organism_v6/born_rulegame_formation.py', 'cached wrong replay source')
    return role


def verify_capsule(bundle, mode, role):
    members, validation = bundle['members'], bundle['receipt']
    def read(name, prefix=PREFIX):
        require(prefix+name in members, 'missing required member: '+prefix+name)
        return decode(members[prefix+name])
    def pin(name):
        return sha(members[PREFIX+name])
    plan = read('plan.json')
    binding, normalized = plan['binding'], read('normalized_birth.json')
    require(pin('plan.json') == validation['plan_sha256'] == read('plan.sha256.json')['sha256'], 'plan seal mismatch')
    require(plan['protocol'] == PROTOCOL and plan['phase'] == 'formation' and plan['root'] == validation['root']
            and plan['child_mode'] == mode == plan['child'] == binding['child_mode'], 'missing/wrong mode or plan')
    require(plan['interface'] == binding['interface'] == role.projection.INTERFACE
            and binding['schema'] == role.PROJECTION_SCHEMA, 'projection interface required')
    require(plan['limits'] == LIMITS and plan['tokens'] == TOKENS and plan['max_calls'] == 60
            and plan['max_output_tokens'] == 18480 and plan['members'] == ['formation']
            and plan['worker_seconds'] == 600 and plan['cleanup_seconds'] == 140
            and 140 < plan['controller_seconds'] <= 900 and plan['collection_seconds'] == 300, 'budget mismatch')
    require(plan['automatic_progression'] is False and plan['automatic_pass'] is False
            and plan['teacher'] == 'same fixed base OFF', 'scope mismatch')
    require(normalized == plan['normalized'] and pin('normalized_birth.json') == plan['normalized_file_sha256']
            and normalized['pin'] == binding['birth'] and normalized['pin_sha256'] == role.diagnostic.value_hash(binding['birth'])
            and normalized['full_release'] is True and normalized['both_fits_complete'] is True, 'birth normalization mismatch')
    require(plan['model_files'] == binding['birth']['model_files'] and plan['model'] == binding['birth']['child_identity']['model_input'],
            'model pin mismatch')
    require(plan['role_sha256'] == ROLE_SHA and plan['source_hashes'] == {
        str(PurePosixPath(plan['source_root'])/'organism_v6'/name): value for name, value in binding['sources'].items()},
        'plan/source pin mismatch')
    role._binding(binding, plan['binding_sha256'])
    require(validation['collector_sha256'] == plan['sidecar_sha256'] and validation['claims'] == plan['claims'], 'collector/claims mismatch')
    capture, barrier, manifest = read(DATA+'capture.json'), read(DATA+'capture_barrier.json'), read(DATA+'manifest.json')
    data_pins = {name[len(PREFIX+DATA):]: sha(value) for name, value in members.items()
                 if name.startswith(PREFIX+DATA) and name != PREFIX+DATA+'manifest.json'}
    require(manifest['files'] == data_pins, 'data manifest mismatch')
    expected_journals = {f"{row['request']['call_id']}.{kind}.json" for row in capture['calls'] for kind in ('request', 'response')}
    journal_pins = {name[6:]: value for name, value in data_pins.items() if name.startswith('calls/')}
    require(set(journal_pins) == expected_journals and barrier['files'] == journal_pins
            and barrier['calls'] == len(capture['calls']) <= 60 and barrier['replay_not_started'] is True,
            'partial/extra raw calls or barrier mismatch')
    costs = dict(calls=0, input_tokens=0, output_tokens=0, output_token_ceiling=0, call_seconds=0.0)
    for row in capture['calls']:
        request = row['request']
        sent = read(DATA+'calls/'+request['call_id']+'.request.json')
        got = read(DATA+'calls/'+request['call_id']+'.response.json')
        require(sent['request'] == request and sent['identity'] == row['identity'] and got['envelope'] == row['envelope']
                and row['started'] <= sent['started'] <= got['ended'] <= row['ended'] <= barrier['completed_monotonic']
                and row['ended']-row['started'] <= 120, 'raw journal/time join mismatch')
        costs['calls'] += 1
        costs['input_tokens'] += len(got['envelope']['response']['prompt_token_ids'])
        costs['output_tokens'] += len(got['envelope']['response']['output_token_ids'])
        costs['output_token_ceiling'] += request['max_tokens']
        costs['call_seconds'] += got['ended']-sent['started']
    terminal, receipt = read('run/result.json'), read('run/formation/receipt.json')
    controller = read('run/controller.json')
    worker, supervision = read('run/formation/worker/process.json'), read('run/formation/worker/supervision.json')
    launch, exited = read('launch.json', 'metadata/launch/'), read('exit.json', 'metadata/launch/')
    require(terminal['status'] == 'COMPLETE_AWAITING_MAIN_AUDIT' and terminal['plan_sha256'] == validation['plan_sha256']
            and terminal['receipt_sha256'] == pin('run/formation/receipt.json')
            and terminal['supervision_sha256'] == pin('run/formation/worker/supervision.json')
            and validation['terminal_sha256'] == pin('run/result.json'), 'terminal receipt join mismatch')
    require(exited['returncode'] == 0 and exited['launch_sha256'] == sha(members['metadata/launch/launch.json'])
            and launch['plan_sha256'] == validation['plan_sha256'] and launch['driver_sha256'] == plan['sidecar_sha256']
            and launch['root'] == plan['root'] and launch['continuous_reservation'] is True
            and controller['continuous_reservation'] is True, 'launch/exit mismatch')
    require(launch['pid'] == launch['pgid'] == launch['session'] > 1
            and all(controller[key] == launch[key] for key in ('pid', 'pgid', 'session'))
            and controller['argv'] == launch['command'] and worker['pid'] == worker['pgid'] > 1
            and worker['pid'] != controller['pid'] and worker['device'] == supervision['device'] == plan['device'],
            'owned process identity mismatch')
    require(supervision['error'] is None and supervision['returncode'] == 0
            and all(supervision[key] is True for key in ('ok', 'owned_group_empty', 'gpu_processes_absent', 'reservation_release_verified'))
            and 0 < worker['timeout'] <= 600 and 0 < supervision['reserved_seconds'] <= worker['timeout']+140,
            'worker release mismatch')
    require(normalized['released_wall'] <= launch['started_wall'] <= controller['started_wall']
            <= terminal['ended_wall'] <= exited['ended_wall'] <= validation['released_wall'] <= plan['lease_cutoff']
            and terminal['ended_wall'] <= controller['hard_end']
            and 0 < terminal['controller_seconds'] <= plan['controller_seconds']
            and 0 <= validation['launch_to_release_seconds'] <= plan['controller_seconds']+300
            and math.isclose(validation['launch_to_release_seconds'], validation['released_wall']-launch['started_wall']),
            'release chronology/bound mismatch')
    isolated, ready = read(DATA+'isolation.json'), read(DATA+'backend.ready.json')
    require(isolated == dict(pid=worker['pid'], parent_pid=controller['pid'], pgid=worker['pgid'],
            plan_sha256=validation['plan_sha256'], binding_sha256=plan['binding_sha256'], hard_end=controller['hard_end'],
            cutoff=capture['cutoff'], one_engine=True, prompt_parent=False, online_updates=False)
            and ready['pid'] == worker['pid'] and worker['started'] <= ready['ready'] <= worker['started']+180
            and ready['ready'] < isolated['cutoff'] <= worker['started']+worker['timeout']
            and barrier['completed_monotonic'] <= worker['started']+supervision['reserved_seconds']
            and read(DATA+'backend.cleanup.json') == dict(closed=True, error=None), 'isolation/cleanup/barrier mismatch')
    require(receipt['capture_sha256'] == pin(DATA+'capture.json') and receipt['manifest_sha256'] == pin(DATA+'manifest.json')
            and receipt['binding_sha256'] == plan['binding_sha256'] and receipt['costs'] == costs, 'capture receipt/cost mismatch')
    require(costs['output_token_ceiling'] <= plan['max_output_tokens'], 'output token ceiling exceeded')
    audit = read('audit.json', 'metadata/collection/')
    require(audit['phase_complete'] is True and audit['formation'] == receipt
            and audit['controller_seconds'] == terminal['controller_seconds'] and audit['costs_nested_not_added'] is True,
            'collection audit mismatch')
    bundle.update(plan=plan, capture=capture, costs=costs, formation_receipt=receipt,
                  terminal=terminal, supervision=supervision)
    return bundle


def summarize(bundle, role):
    capture, plan = bundle['capture'], bundle['plan']
    replay = role.replay_formation(capture, plan['binding'], expected_binding_sha256=plan['binding_sha256'], cutoff=capture['cutoff'])
    require(replay == bundle['formation_receipt']['replay'], 'saved replay mismatch')
    rows = {row['request']['call_id']: row for row in capture['calls']}
    extracts = []
    for interaction in replay['result']['interactions']:
        parent = rows[interaction['parent_call_id']]
        restate = rows[interaction['restatement_call_id']]
        eid, arm = parent['request']['eid'], parent['request']['arm']
        extracts.append(dict(arm=arm, lesson=interaction['lesson'], parent=parent, restatement=restate,
            exact_source_calls=[row for row in capture['calls'] if row['request']['eid'] == eid
                                and row['request']['arm'] == arm and row['request']['role'] == 'wake'],
            exact_source_events=[event for event in capture['events'] if event.get('eid') == eid and event.get('arm') == arm],
            first_apply_request=next(row['request'] for row in capture['calls'] if row['request']['role'] == 'wake'
                and row['request']['arm'] == arm and row['request']['eid'] == role.projection.task_id(interaction['lesson'], 'apply')),
            parent_visible_transcript_contract='Exact parent request retained; original helper applies 4000-character transcript tail',
            source_events_visibility='Analyst evidence, not additional parent-visible input; only parent.request.prompt was sent',
            semantics='UNREVIEWED_MAIN_JUDGMENT_REQUIRED'))
    by_arm = {}
    for arm in ('P', 'A'):
        calls = [row for row in capture['calls'] if row['request']['arm'] == arm]
        by_arm[arm] = dict(metrics=replay['result']['interface_metrics'][arm], calls=len(calls),
            input_tokens=sum(len(row['envelope']['response']['prompt_token_ids']) for row in calls),
            output_tokens=sum(len(row['envelope']['response']['output_token_ids']) for row in calls),
            tasks=[task for task in replay['result']['tasks'] if task['arm'] == arm],
            per_role={name: dict(calls=sum(row['request']['role'] == name for row in calls),
                input_tokens=sum(len(row['envelope']['response']['prompt_token_ids']) for row in calls if row['request']['role'] == name),
                output_tokens=sum(len(row['envelope']['response']['output_token_ids']) for row in calls if row['request']['role'] == name))
                for name in role.ROLES})
    return dict(mode=plan['child_mode'], plan_sha256=bundle['receipt']['plan_sha256'],
        archive=bundle['archive'], validation=bundle['validation'], validation_sha256=bundle['validation_sha256'],
        archive_sha256=bundle['receipt']['archive_sha256'], verified_member_count=len(bundle['members']),
        replay_verified=True, per_arm=by_arm, costs=dict(**bundle['costs'],
        worker_reserved_seconds=bundle['supervision']['reserved_seconds'], controller_seconds=bundle['terminal']['controller_seconds'],
        collection_seconds=bundle['receipt']['collection_seconds'], launch_to_release_seconds=bundle['receipt']['launch_to_release_seconds'],
        nested_not_added=True), semantic_audit_extracts=extracts,
        call_ledger=[dict(call_id=row['request']['call_id'], role=row['request']['role'], arm=row['request']['arm'],
            eid=row['request']['eid'], tick=row['request']['tick'], seed=row['request']['seed'],
            temperature=row['request']['temperature'], max_tokens=row['request']['max_tokens'],
            input_tokens=len(row['envelope']['response']['prompt_token_ids']),
            output_tokens=len(row['envelope']['response']['output_token_ids']),
            finish_reason=row['envelope']['response']['finish_reason'], stop_reason=row['envelope']['response']['stop_reason'],
            lora_request=row['envelope']['lora_request'], prompt_sha256=row['prompt_sha256'],
            envelope_sha256=row['envelope_sha256']) for row in capture['calls']],
        raw_paths=dict(capture=PREFIX+DATA+'capture.json', journals=PREFIX+DATA+'calls/',
                       plan=PREFIX+'plan.json', terminal=PREFIX+'run/result.json'),
        release_evidence=dict(full_release=bundle['receipt']['full_release'], final_vacancy=bundle['receipt']['final_vacancy'],
                              final_vacancy_sha256=bundle['receipt']['final_vacancy_sha256']))


def analyze_pair(*, auth_archive, auth_validation, auth_validation_sha256,
                 off_archive, off_validation, off_validation_sha256, source, both_closed=False):
    require(both_closed is True, 'Main must declare BOTH captures closed before any result reads')
    role = load_role(source)
    bundles = [load_capsule(auth_archive, auth_validation, auth_validation_sha256),
               load_capsule(off_archive, off_validation, off_validation_sha256)]
    for mode, bundle in zip(('AUTH', 'OFF'), bundles):
        verify_capsule(bundle, mode, role)
    auth, off = (bundle['plan'] for bundle in bundles)
    require(auth['root'] != off['root'], 'reused paired root')
    for field in ('protocol', 'interface', 'source_root', 'source_hashes', 'role_sha256', 'sidecar_sha256',
                  'birth_driver_sha256', 'normalized', 'model', 'model_files', 'public_model_binding', 'limits',
                  'tokens', 'max_calls', 'max_output_tokens', 'controller_seconds', 'worker_seconds',
                  'cleanup_seconds', 'collection_seconds', 'origin', 'claims', 'teacher'):
        require(auth[field] == off[field], 'paired mismatch: '+field)
    require(auth['binding']['task_schedule'] == off['binding']['task_schedule'], 'paired schedule mismatch')
    results = {mode: summarize(bundle, role) for mode, bundle in zip(('AUTH', 'OFF'), bundles)}
    return dict(schema='projected_formation_paired_analysis_v1', status='VERIFIED_AWAITING_MAIN_SEMANTIC_AUDIT',
        analyzer_sha256=sha(file_bytes(__file__)),
        author_reproduction_not_independent_review=True, modes=results, matched_birth_pin=auth['binding']['birth'],
        source_hashes=auth['binding']['sources'], task_schedule=auth['binding']['task_schedule'],
        total_calls=sum(result['costs']['calls'] for result in results.values()),
        total_input_tokens=sum(result['costs']['input_tokens'] for result in results.values()),
        total_output_tokens=sum(result['costs']['output_tokens'] for result in results.values()),
        parent_purity='UNREVIEWED_MAIN_JUDGMENT_REQUIRED', automatic_pass=False,
        limitations=['Receipt/replay integrity is not parent semantic purity, efficacy, retention or learning.',
                     'No independent live process/GPU/queue observation; release is pinned collector evidence.',
                     'Final vacancy XML is not in the capsule; its hash/summary are validation assertions.',
                     'Source-authored birth NOT_CLEAN; original ancestry labels unchanged.',
                     'Nested call/worker/controller/release costs must not be added; no A40-minute equivalence inferred.',
                     'Finish/stop reasons are reported verbatim; stop is not automatically classified as EOS.',
                     'Full token IDs and raw source text retained in capsules; no tokenizer/model replay.'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--both-closed', action='store_true', required=True)
    for mode in ('auth', 'off'):
        for field in ('archive', 'validation', 'validation-sha256'):
            parser.add_argument('--'+mode+'-'+field, required=True)
    parser.add_argument('--out', required=True, help='New exclusive JSON file; never overwritten')
    args = vars(parser.parse_args(argv))
    output = Path(args.pop('out'))
    require(not output.exists() and not output.is_symlink(), 'output exists; no overwrite/retry')
    result = analyze_pair(**args)
    data = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(data)
    print(json.dumps(dict(output=str(output.absolute()), sha256=sha(data), status=result['status'])))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
