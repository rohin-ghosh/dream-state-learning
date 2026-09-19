"""Offline C2 policy preparation and read-only continuation checks."""

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
WORKERS = REPO / 'research_loop/workers'
ORIGINAL_MANIFEST = WORKERS / 'post_reboot_c2_p7_20260919/c2_session1/MANIFEST.json'
STRONG = WORKERS / 'rohin233_recovery_node4_20260918/checkpoint_tail_parent_strong.py'
BASE = REPO / 'gpu/orch_r133_programme_parent.py'
CONTINUE = STRONG.with_name('c2_parent_continue.py')
HOOK = WORKERS / 'rohin174_parenting_20260917/node5/R195_FLEET/MSG201/r202_parent.py'
SERVICE_LOCK = WORKERS / 'post_reboot_c2_p7_20260919/C2_SERVICE.lock'
CONTROLLER_LOCK = STRONG.parent / 'private/C2_WAIT_CONTROLLER.lock'
SERVICE = SERVICE_LOCK.parent / 'c2_service.py'
MEASUREMENT = HERE.parents[1] / 'operations/C2_REFINEMENT_MEASUREMENT_PLAN.md'
LEDGER_FILES = ('SOURCE.json', 'SYSTEM.txt', 'PROMPT.txt', 'DISPATCH_INTENT.json',
                'OUTBOUND_ROUTE.json', 'RESULT.json', 'DELIVERED.json')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def encoded(document):
    return (json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode()


def digest(content):
    return hashlib.sha256(content).hexdigest()


def sha(path):
    return digest(Path(path).read_bytes())


def check_pins(manifest):
    for filename, expected in manifest['local_source_sha256'].items():
        require(sha(filename) == expected, 'pinned_source_changed:' + filename)


def function(path, name, namespace, *, hook=False):
    tree = ast.parse(Path(path).read_bytes())
    nodes = tree.body
    if hook:
        main = next(node for node in nodes if isinstance(node, ast.FunctionDef) and node.name == 'main')
        branch = next(node for node in main.body if isinstance(node, ast.If)
                      and isinstance(node.test, ast.Attribute) and node.test.attr == 'policy_addendum')
        nodes = branch.body
    selected = next(node for node in nodes if isinstance(node, ast.FunctionDef) and node.name == name)
    module = ast.fix_missing_locations(ast.Module(body=[selected], type_ignores=[]))
    exec(compile(module, str(path) + ':isolated_original_function', 'exec'), namespace)
    return namespace[name]


def original_validators(previous):
    namespace = dict(Path=Path, hashlib=hashlib, json=json, require=require, sha=sha,
                     STYLE=previous['parent_style'], ROOT=previous['root'],
                     ORIGINAL_SOURCE=previous['source_root'])
    function(CONTINUE, 'validate_config_change', namespace)
    function(STRONG, 'validate_config', namespace)
    function(STRONG, 'validate_manifest', namespace)
    function(BASE, 'resume_cursor', namespace)
    return namespace


def no_question_bank(config):
    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                require(not key.startswith('questions_only_'), 'question_bank_mode_conflicts_with_mixed_policy')
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(config)


def ledger(output, config):
    output = Path(output)
    started = read(output / 'STARTED.json')
    require(started['branch'] == config['branch'] == 'C2', 'C2_ledger_only')
    signatures = {'STARTED.json': sha(output / 'STARTED.json')}
    counts, usage = Counter(), Counter()
    reservations, pending, failures = [], [], []
    last_result = None
    for directory in sorted(output.glob('parent_*')):
        if not directory.is_dir():
            continue
        for name in LEDGER_FILES:
            path = directory / name
            if path.exists():
                signatures[str(path.relative_to(output))] = sha(path)
        source_path, result_path = directory / 'SOURCE.json', directory / 'RESULT.json'
        source = read(source_path) if source_path.exists() else None
        result = read(result_path) if result_path.exists() else None
        if source:
            reservations.append(source['response_count'])
        else:
            pending.append(dict(attempt=directory.name, kind='missing_source_reservation'))
        counts['attempt_directories'] += 1
        counts['dispatch_intents'] += int((directory / 'DISPATCH_INTENT.json').exists())
        counts['outbound_route_receipts'] += int((directory / 'OUTBOUND_ROUTE.json').exists())
        status = result.get('status', 'UNKNOWN') if result else 'UNSETTLED'
        counts[status] += 1
        last_result = status
        if result:
            for key in ('input_tokens', 'output_tokens', 'total_tokens'):
                usage[key] += (result.get('usage') or {}).get(key) or 0
        if status == 'PUBLISHED':
            publication = result.get('inbox_publication', {})
            delivery_path = directory / 'DELIVERED.json'
            if not delivery_path.exists():
                pending.append(dict(attempt=directory.name, kind='publication_consumption_unknown',
                                    inbox_id=publication.get('id'), result_sha256=sha(result_path)))
            else:
                delivery = read(delivery_path)
                require(delivery.get('status') == 'COMPLETE' and delivery.get('result_sha256') == sha(result_path)
                        and delivery.get('inbox_id') == publication.get('id'), 'delivery_bound_to_actual_publication')
        elif status == 'MISSING':
            failure = dict(attempt=directory.name, error_type=result.get('error_type'),
                           result_sha256=sha(result_path), retry=False)
            failures.append(failure)
            if result.get('response') or result.get('inbox_publication') or result.get('error_type') != 'HTTPError':
                pending.append(dict(failure, kind='uncertain_attempt_requires_reconciliation'))
        elif status != 'SILENT':
            pending.append(dict(attempt=directory.name, kind='incomplete_or_unknown_attempt'))
    return dict(output=str(output), signature=digest(encoded(signatures)), counts=dict(counts),
                usage_recorded=dict(usage), reserved=max([config['start_after_response_count']] + reservations),
                pending=pending, failures=failures, last_status=last_result,
                failed_attempts_remain_reserved=True, missing_usage_not_estimated=True)


def audit(manifest):
    configs = {}
    for filename, expected in manifest['local_source_sha256'].items():
        if 'CONFIG' in Path(filename).name and filename.endswith('.json'):
            value = read(filename)
            if isinstance(value, dict) and value.get('branch') == 'C2':
                configs[expected] = value
    config = read(manifest['config_path'])
    output = Path(manifest['output'])
    visited, ledgers, totals = set(), [], Counter()
    older_boundary = None
    while str(output) not in visited:
        visited.add(str(output))
        item = ledger(output, config)
        ledgers.append(item)
        totals.update(item['counts'])
        predecessor = config.get('predecessor_output')
        if not predecessor:
            break
        started_path = Path(predecessor) / 'STARTED.json'
        require(sha(started_path) == config['predecessor_started_sha256'], 'preserved_predecessor_started')
        started = read(started_path)
        if started['config_sha256'] not in configs:
            older_boundary = dict(output=predecessor, started_sha256=sha(started_path),
                                  config_sha256=started['config_sha256'], status='retained_not_fully_audited')
            break
        config = configs[started['config_sha256']]
        output = Path(predecessor)
    return dict(observed_utc=datetime.now(timezone.utc).isoformat(), ledgers=ledgers,
                totals_known=dict(totals), older_boundary=older_boundary,
                whole_life_totals_known=older_boundary is None, replay_authorized=False)


def process_identity(pid):
    process = Path('/proc') / str(pid)
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, start_ticks=fields[19], state=fields[0], cwd=str((process / 'cwd').resolve()),
                argv=(process / 'cmdline').read_bytes().decode().rstrip('\0').split('\0'))


def prepare_documents():
    manifest = read(ORIGINAL_MANIFEST)
    check_pins(manifest)
    previous = read(manifest['config_path'])
    no_question_bank(previous)
    require(read(Path(manifest['output']) / 'STARTED.json')['config_sha256'] == sha(manifest['config_path']),
            'actual_started_publisher_uses_nested_config')
    identity_receipt = read(HERE / 'CPU_IDENTITY_OBSERVATION.json')
    publisher, service = identity_receipt['publisher'], identity_receipt['CPU_service']
    require(publisher['start_ticks'] == '753205' and service['start_ticks'] == '822432', 'recorded_exact_CPU_incarnations')
    require(publisher['argv'] == ['/usr/bin/python3', '-B', str(STRONG), '--manifest', str(ORIGINAL_MANIFEST),
                                 '--manifest-sha256', sha(ORIGINAL_MANIFEST)], 'actual_manifest_argument')
    require(service['argv'] == ['/usr/bin/python3', '-B', str(SERVICE_LOCK.parent / 'c2_service.py')],
            'actual_CPU_service_argument')
    snapshot = audit(manifest)
    documents = {}
    config_path = HERE / 'session1/CONFIG.json'
    config = dict(previous, predecessor_output=manifest['output'],
                  predecessor_started_sha256=sha(Path(manifest['output']) / 'STARTED.json'),
                  start_after_response_count=snapshot['ledgers'][0]['reserved'])
    original_validators(previous)['validate_config'](previous, config)
    original_validators(previous)['resume_cursor'](config)
    documents[config_path] = encoded(config)
    documents[HERE / 'COMBINED_ADDENDUM.md'] = (Path(manifest['policy_addendum']).read_bytes()
                                               + b'\n\n' + (HERE / 'POLICY_DELTA.md').read_bytes())
    snapshot.update(publisher=publisher, CPU_service=service, identity_observation=identity_receipt,
                    identity_refresh_required_at_deployment=True,
                    native_remote_observation=read(HERE / 'NATIVE_OBSERVATION.json'))
    documents[HERE / 'SOURCE_AUDIT.json'] = encoded(snapshot)
    pins = dict(manifest['local_source_sha256'])
    for path in (HERE / 'candidate.py', HERE / 'test_c2_refinement.py',
                 HERE / 'POLICY_DELTA.md', HERE / 'PROVENANCE.json', MEASUREMENT,
                 SERVICE_LOCK.parent / 'c2_service.py', ORIGINAL_MANIFEST):
        pins[str(path)] = sha(path)
    pins.update({str(path): digest(content) for path, content in documents.items()})
    candidate_manifest = dict(manifest, config_path=str(config_path), predecessor_config_path=manifest['config_path'],
        output=str(HERE / 'session1/parent'), policy_addendum=str(HERE / 'COMBINED_ADDENDUM.md'),
        local_source_sha256=pins, status='READY_CANDIDATE_NOT_AUTHORIZED_OR_DEPLOYED',
        old_parent_must_be_drained_by_owner=publisher,
        explicit_parent_treatment='C2_SHORT_TASK_ARTIFACT_CHECK_MIXED_EXPLORATORY',
        candidate=dict(schema='C2_REFINEMENT_CANDIDATE_V1', deployment_authorized=False,
            predecessor_manifest=str(ORIGINAL_MANIFEST), predecessor_manifest_sha256=sha(ORIGINAL_MANIFEST),
            audit_path=str(HERE / 'SOURCE_AUDIT.json'), audit_sha256=digest(documents[HERE / 'SOURCE_AUDIT.json']),
            measurement_plan=dict(path=str(MEASUREMENT), sha256=sha(MEASUREMENT)),
            design='one_life_exploratory_not_randomized', credential_scope='existing_C2_supervisor_inheritance_authentication_untested',
            original_addendum_sha256=sha(manifest['policy_addendum']),
            policy_delta_sha256=sha(HERE / 'POLICY_DELTA.md'), epoch_start='first_verified_new_policy_delivery'))
    candidate_manifest.pop('old_waiter_must_be_drained_by_owner', None)
    candidate_manifest['active_CPU_supervisor_must_remain'] = service
    documents[HERE / 'MANIFEST.json'] = encoded(candidate_manifest)
    seed = dict(manifest, policy_addendum=candidate_manifest['policy_addendum'], local_source_sha256=pins,
                status='PROSPECTIVE_SUPERVISOR_SEED_REFERENCES_REAL_OLD_LEDGER_NOT_NEW_POLICY_DEPLOYMENT',
                explicit_parent_treatment=candidate_manifest['explicit_parent_treatment'],
                candidate=dict(candidate_manifest['candidate'], seed_role='next_session_policy_only',
                    referenced_old_STARTED_sha256=sha(Path(manifest['output']) / 'STARTED.json'),
                    referenced_output_was_old_policy=True,
                    cursor_refresh='original_c2_service_recomputes_max_reserved_SOURCE_at_restart'),
                active_CPU_supervisor_must_remain=service, old_parent_must_be_drained_by_owner=publisher)
    seed.pop('old_waiter_must_be_drained_by_owner', None)
    documents[HERE / 'SUPERVISOR_SEED_MANIFEST.json'] = encoded(seed)
    live_seed_path = SERVICE_LOCK.parent / 'c2_session_refinement_seed_20260919/MANIFEST.json'
    install_patch = ('*** Begin Patch\n*** Add File: ' + str(live_seed_path.relative_to(REPO)) + '\n'
                     + ''.join('+' + line + '\n' for line in encoded(seed).decode().splitlines())
                     + '*** End Patch\n')
    documents[HERE / 'INSTALL_NEXT_SESSION.patch'] = install_patch.encode()
    return documents


def handoff_preflight(manifest):
    check_pins(manifest)
    previous = read(manifest['predecessor_config_path'])
    config = read(manifest['config_path'])
    no_question_bank(previous)
    no_question_bank(config)
    require({key: value for key, value in config.items() if key not in
             ('predecessor_output', 'predecessor_started_sha256', 'start_after_response_count')} ==
            {key: value for key, value in previous.items() if key not in
             ('predecessor_output', 'predecessor_started_sha256', 'start_after_response_count')},
            'only_cursor_and_predecessor_change')
    validators = original_validators(previous)
    validators['validate_manifest'](manifest)
    validators['resume_cursor'](config)
    snapshot = read(manifest['candidate']['audit_path'])
    require(sha(manifest['candidate']['audit_path']) == manifest['candidate']['audit_sha256'], 'pinned_audit')
    fresh = ledger(config['predecessor_output'], previous)
    require(fresh['signature'] == snapshot['ledgers'][0]['signature'], 'ledger_advanced_refresh_candidate_and_review')
    require(not fresh['pending'], 'pending_attempts_or_publications_must_settle_before_handoff')
    require(fresh['last_status'] in ('PUBLISHED', 'SILENT'), 'no_restart_after_unresolved_provider_failure')
    require(config['start_after_response_count'] == fresh['reserved'], 'exact_last_reserved_source')
    return config


def seed_preflight(seed, *, verify_live=False):
    check_pins(seed)
    old_manifest = read(seed['candidate']['predecessor_manifest'])
    require(sha(seed['candidate']['predecessor_manifest']) == seed['candidate']['predecessor_manifest_sha256'],
            'exact_original_session_manifest')
    require(seed['config_path'] == old_manifest['config_path'] and seed['output'] == old_manifest['output'],
            'seed_references_actual_unchanged_predecessor_not_fabricated_START')
    config = read(seed['config_path'])
    no_question_bank(config)
    started = Path(seed['output']) / 'STARTED.json'
    require(sha(started) == seed['candidate']['referenced_old_STARTED_sha256']
            and read(started)['config_sha256'] == sha(seed['config_path']), 'real_old_STARTED_binding')
    require(seed['candidate']['referenced_output_was_old_policy'] is True, 'no_retroactive_policy_claim')
    require(Path(seed['policy_addendum']).read_bytes() == Path(old_manifest['policy_addendum']).read_bytes()
            + b'\n\n' + (HERE / 'POLICY_DELTA.md').read_bytes(), 'original_addendum_exact_prefix')
    if verify_live:
        expected = seed['active_CPU_supervisor_must_remain']
        actual = process_identity(expected['pid'])
        require(all(actual[key] == expected[key] for key in ('pid', 'start_ticks', 'cwd', 'argv')),
                'same_live_C2_supervisor_no_credential_transfer')
    return ledger(seed['output'], config)


def emit_patch(documents):
    print('*** Begin Patch')
    for path, content in documents.items():
        require(path.is_relative_to(HERE), 'candidate_write_scope')
        relative = path.relative_to(REPO)
        if path.exists():
            print('*** Update File: ' + str(relative))
            print('@@')
            for line in path.read_text().splitlines():
                print('-' + line)
        else:
            print('*** Add File: ' + str(relative))
        for line in content.decode().splitlines():
            print('+' + line)
    print('*** End Patch')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-patch', action='store_true')
    parser.add_argument('--check', type=Path)
    parser.add_argument('--check-seed', type=Path)
    parser.add_argument('--require-live-identity', action='store_true')
    options = parser.parse_args()
    if options.prepare_patch:
        emit_patch(prepare_documents())
    elif options.check:
        handoff_preflight(read(options.check))
        print('Offline handoff checks pass; NOT deployment approval or live delivery.')
    elif options.check_seed:
        fresh = seed_preflight(read(options.check_seed), verify_live=options.require_live_identity)
        print(json.dumps(dict(status='READ_ONLY_SUPERVISOR_SEED_CHECK_NOT_DEPLOYMENT', ledger=fresh,
                              live_supervisor_identity_checked=options.require_live_identity,
                              settled_current_ledger=not fresh['pending'] and fresh['last_status'] in ('PUBLISHED', 'SILENT'),
                              deployment_authorized=False)))
    else:
        parser.error('choose --prepare-patch, --check MANIFEST or --check-seed SEED')


if __name__ == '__main__':
    main()
