"""Bound Node3 parent-only handoff; never signal a child or change its config."""

import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
import types


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
HELPER_SHA = 'ae2c9df909d9b48ebebef968690ee2e4c9085452151dbb96474311cf55b11923'
ASSIGNMENT_SHA = '25b45432bebb388e920d5cc8dc8fed6c705cd54156cbfd530828e1520a9174b2'
HARD_END = 1789689000
MODEL = 'openai/openai/gpt-6-astra'
PHYSICALS = (0, 1, 2, 3, 4, 7)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reference(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))


def write(path, document):
    path = Path(path)
    require(path.resolve().is_relative_to(HERE), 'owned_artifacts_only')
    require(not path.exists(), 'immutable_artifact')
    text = document if isinstance(document, str) else json.dumps(document, indent=2, sort_keys=True) + '\n'
    patch = '*** Begin Patch\n*** Add File: ' + str(path) + '\n'
    patch += ''.join('+' + line + '\n' for line in text.splitlines()) + '*** End Patch\n'
    subprocess.run(['apply_patch'], input=patch, text=True, check=True, capture_output=True)


def load_file(path, name):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def project_artifact_writer(bundle):
    path = bundle / 'gpu/orch_l2_shared_run.py'
    function = next(node for node in ast.parse(path.read_text()).body if isinstance(node, ast.FunctionDef) and node.name == 'write')
    module = types.ModuleType('gpu.orch_l2_shared_run')
    module.__file__ = str(path)
    module.Path, module.json = Path, json
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'), module.__dict__)
    sys.modules[module.__name__] = module
    system_path = bundle / 'gpu/orch_route_parent_campaign_parent.py'
    assignment = next(node for node in ast.parse(system_path.read_text()).body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'SYSTEM' for target in node.targets))
    system_module = types.ModuleType('gpu.orch_route_parent_campaign_parent')
    system_module.__file__ = str(system_path)
    exec(compile(ast.Module(body=[assignment], type_ignores=[]), str(system_path), 'exec'), system_module.__dict__)
    sys.modules[system_module.__name__] = system_module
    guard_module = types.ModuleType('organism_v6.orch_route_parent_campaign')
    guard_module.__file__ = str(bundle / 'organism_v6/orch_route_parent_campaign.py')
    guard_module.require = require
    sys.modules[guard_module.__name__] = guard_module
    bridge_path = bundle / 'organism_v6/orch_guided_bridge.py'
    file_hash = next(node for node in ast.parse(bridge_path.read_text()).body if isinstance(node, ast.FunctionDef) and node.name == 'file_sha256')
    bridge_module = types.ModuleType('organism_v6.orch_guided_bridge')
    bridge_module.__file__ = str(bridge_path)
    bridge_module.Path, bridge_module.sha256 = Path, hashlib.sha256
    exec(compile(ast.Module(body=[file_hash], type_ignores=[]), str(bridge_path), 'exec'), bridge_module.__dict__)
    sys.modules[bridge_module.__name__] = bridge_module


def release():
    helper_path = REPO / 'gpu/orch_r175_parent_arms.py'
    assignment_path = HERE.parent / 'ASSIGNMENTS_V1.json'
    require(sha(helper_path) == HELPER_SHA, 'exact_Main_helper_GO')
    require(sha(assignment_path) == ASSIGNMENT_SHA, 'exact_Main_assignments_GO')
    rows = {row['gpu']: row for row in read(assignment_path)['rows'] if row['node'] == 'ovx2'}
    require(set(rows) == set(PHYSICALS), 'six_Node3_assignments')
    return load_file(helper_path, 'bound_Main_arms'), rows


def identity(pid):
    process = Path('/proc') / str(pid)
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    return dict(pid=pid, ticks=fields[19], state=fields[0], uid=process.stat().st_uid,
                argv=(process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0'))


def same(expected, observed):
    return expected['pid'] == observed['pid'] and str(expected['ticks']) == observed['ticks'] and expected['argv'] == observed['argv']


def ledger(output, original):
    requests = original.get('start_after_request_count', 0)
    responses = original.get('start_after_response_count', 0)
    pending, attempts = [], []
    for directory in sorted(Path(output).glob('parent_*')):
        require(directory.is_dir() and not directory.is_symlink(), 'regular_attempt')
        source_path, result_path = directory / 'SOURCE.json', directory / 'RESULT.json'
        require(source_path.exists() and result_path.exists(), 'inflight_attempt_preserve_and_retry')
        source, result = read(source_path), read(result_path)
        require(result['source_head_sha256'] == source['head_sha256'] and
                result['source_response_count'] == source['response_count'], 'exact_result_source')
        require(result['status'] in ('MISSING', 'PUBLISHED', 'SILENT'), 'known_legacy_status')
        requests = max(requests, source['request_count'])
        responses = max(responses, source['response_count'])
        if result['status'] == 'PUBLISHED' and not (directory / 'DELIVERED.json').exists():
            pending.append(result['inbox_publication']['id'])
        attempts.append(dict(source=reference(source_path), result=reference(result_path), status=result['status']))
    return dict(request_cursor=requests, response_cursor=responses,
                pending_existing_inbox_ids=pending, attempts=attempts)


def make_config(original, assignment, helper, principles, previous_output, previous_started, reserved):
    config = helper.configure(original, assignment['arm'])
    config.update(principles_path=str(principles.resolve()), principles_sha256=sha(principles),
                  predecessor_output=str(previous_output), predecessor_started_sha256=previous_started,
                  start_after_request_count=reserved['request_cursor'],
                  start_after_response_count=reserved['response_cursor'],
                  r166_schema='R166_PARENT_SUCCESSOR_V1', object_turn_limit=3, community_learner=False,
                  prospective_label='R175_Main_bound_legacy_to_R166_parent_only')
    require(config['root'] == original['root'] and config['source_root'] == original['source_root']
            and config['hard_end_unix'] == HARD_END, 'child_and_wall_unchanged')
    require(config['schedule_on'] == 'response' and config['cadence_responses'] == assignment['cadence'], 'frozen_response_clock')
    return config


def prepare():
    helper, assignments = release()
    sys.path.insert(0, str(REPO))
    for arm in sorted({row['arm'] for row in assignments.values()}):
        destination = HERE / ('source_' + arm)
        if not destination.exists():
            helper.build_bundle(REPO, destination, arm)
        manifest = read(destination / 'ARM_BUNDLE.json')
        require(manifest['builder_sha256'] == HELPER_SHA and manifest['arm'] == arm, 'bound_owned_bundle')
    for physical, assignment in assignments.items():
        folder = HERE / 'parents' / ('physical' + str(physical))
        prepared = read(folder / 'PREPARATION.json')
        original = read(folder / 'PREDECESSOR_CONFIG.json')
        require(prepared['assignment']['life'] == assignment['child'] and
                prepared['assignment']['arm'] == assignment['arm'], 'frozen_life_arm')
        old_principles = Path(original['principles_path'])
        require(sha(old_principles) == original['principles_sha256'], 'preserve_original_principles')
        principles = folder / 'PRINCIPLES_R175.md'
        if not principles.exists():
            write(principles, old_principles.read_text() + helper.instruction(assignment['arm']))
        reserved = ledger(prepared['predecessor']['output'], original)
        config = make_config(original, assignment, helper, principles, prepared['predecessor']['output'],
                             prepared['predecessor']['started']['sha256'], reserved)
        candidate = folder / 'CANDIDATE_CONFIG.json'
        if not candidate.exists():
            write(candidate, config)
    print(json.dumps(dict(status='BUNDLES_AND_CANDIDATES_READY_NO_SIGNALS', rows=list(assignments.values()))))


def runtime(physical, config_path):
    helper, assignments = release()
    assignment = assignments[physical]
    bundle = HERE / ('source_' + assignment['arm'])
    manifest = read(bundle / 'ARM_BUNDLE.json')
    require(manifest['builder_sha256'] == HELPER_SHA, 'exact_builder')
    for name, item in manifest['files'].items():
        require(sha(bundle / name) == item['sha256'], 'immutable_bundle_file')
    sys.path.insert(0, str(bundle))
    project_artifact_writer(bundle)
    parent = importlib.import_module('gpu.orch_r133_programme_parent')
    provider = importlib.import_module('gpu.orch_route_parent_campaign_providers')
    policy = importlib.import_module('gpu.orch_r166_parent_policy')
    require(Path(parent.__file__).resolve().is_relative_to(bundle) and
            Path(provider.__file__).resolve().is_relative_to(bundle), 'owned_runtime_modules')
    require(provider.STRONG == MODEL, 'exact_Astra_alias')
    config = parent.validate(read(config_path))
    config.update(r166_schema=policy.SCHEMA, object_turn_limit=3, community_learner=False,
                  prospective_label='R175_Main_bound_legacy_to_R166_parent_only')
    policy.validate(config)
    require(config['r175_schema'] == helper.SCHEMA and config['r175_arm'] == assignment['arm']
            and config['r175_word_limit'] == helper.specification(assignment['arm'])['words']
            and config['cadence_responses'] == assignment['cadence']
            and config['schedule_on'] == 'response', 'runtime_arm_clock_cap_binding')
    recovery = load_file(REPO / 'research_loop/workers/r179_context_survival_20260917/node3/parent_recovery.py', 'unchanged_R179_clock')
    prepared = read(HERE / 'parents' / ('physical' + str(physical)) / 'PREPARATION.json')
    routing = read(prepared['predecessor']['binding']['path'])['row']
    snapshot = parent.snapshot

    def preserved_snapshot(repository, current_config):
        require(current_config['root'] == routing['active_host_root'], 'same_recovered_life')
        return recovery.recover_clock(snapshot(repository, current_config), routing)

    parent.snapshot = preserved_snapshot
    return parent, provider, config, helper


def preflight(physical, final=False):
    folder = HERE / 'parents' / ('physical' + str(physical))
    config_path = folder / ('CONFIG.json' if final else 'CANDIDATE_CONFIG.json')
    parent, provider, config, helper = runtime(physical, config_path)
    policy = importlib.import_module('gpu.orch_r166_parent_policy')
    state = dict(events=[], delivered={}, journal_id='CPU', split='TRAIN', response_count=100,
                 request_count=100, sleep_count=0, caught_up=True, head_sha256='0' * 64)
    seed = dict(journal_id='CPU', object_delivered_turns={}, last_response_count=100,
                last_request_count=100, prospective_request_count=100, credits={}, grammar_delivered=False, attempts=[])
    instruction, unused_payload = policy.prompt(config, state, policy.memory(seed, [], state))
    require('ROHIN175_OBSERVATION_TO_ACTION_BASELINE_V1' in instruction, 'actual_prompt_baseline')
    words = helper.specification(config['r175_arm'])['words']
    require(f'at most {words} words' in instruction, 'actual_prompt_cap')
    response = dict(speak=True, message=' '.join(['word'] * words), rationale='CPU fixture')
    require(provider.response_schema(json.dumps(response)) == response, 'actual_provider_accepts_arm_cap')
    for invalid in (' '.join(['word'] * (words + 1)), 'x' * 4097):
        response['message'] = invalid
        try:
            provider.response_schema(json.dumps(response))
        except ValueError:
            pass
        else:
            raise ValueError('actual_provider_rejects_over_cap')
    cursor = parent.resume_cursor(config)
    require(cursor >= config['start_after_response_count'], 'predecessor_response_cursor_preserved')
    fixture_output = folder / ('CPU_TICK_' + str(time.time_ns()))
    write(fixture_output / 'FIXTURE.json', dict(CPU_only=True, real_policy_tick=True, provider_stub=True))
    calls = []
    previous_strong = parent.strong
    def fixture_strong(*arguments, **keywords):
        calls.append(True)
        return dict(speak=False, message='', rationale=''), MODEL, dict(CPU_fixture=True)
    parent.strong = fixture_strong
    try:
        state['events'] = [dict(actor='child', text='CPU fixture: operation not executed.', record_index=1, record_sha256='1' * 64)]
        state['request_count'] = 200
        state['response_count'] = 100 + config['cadence_responses'] - 1
        require(policy.tick(REPO, config, fixture_output, seed, state)['status'] == 'WAITING_FOR_NEW_CHILD_BOUNDARY', 'actual_tick_uses_response_not_request_clock')
        require(not calls, 'no_early_dispatch')
        state['response_count'] += 1
        require(policy.tick(REPO, config, fixture_output, seed, state)['status'] == 'SILENT' and len(calls) == 1, 'actual_patched_tick_runs_at_exact_cadence')
    finally:
        parent.strong = previous_strong
    return dict(status='NODE_TAKEOVER_CPU_PASS', physical=physical, arm=config['r175_arm'],
                words=words, clock='response', cadence=config['cadence_responses'],
                response_cursor=cursor, request_cursor=config['start_after_request_count'],
                config=reference(config_path), baseline_in_actual_prompt=True,
                owned_parent=reference(parent.__file__), owned_provider=reference(provider.__file__),
                owned_tick_and_prompt=reference(policy.__file__), actual_tick='gpu.orch_r166_parent_policy.tick',
                actual_tick_clock_test='PASS', actual_tick_dispatch_test='PASS', fixture=str(fixture_output),
                no_provider_call=True, no_child_restart=True)


def quiet_pause(expected, output, original, deadline):
    descriptor = os.pidfd_open(expected['pid'])
    stopped = False
    try:
        while time.monotonic() < deadline:
            require(same(expected, identity(expected['pid'])) and expected['uid'] == os.getuid(), 'exact_owned_parent')
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            stopped = True
            for unused in range(100):
                if identity(expected['pid'])['state'] in ('T', 't'):
                    break
                time.sleep(0.01)
            try:
                require(identity(expected['pid'])['state'] in ('T', 't'), 'pause_confirmed')
                children = [child for path in (Path('/proc') / str(expected['pid']) / 'task').glob('*/children') for child in path.read_text().split()]
                require(not children, 'transport_inflight')
                return descriptor, ledger(output, original)
            except (ValueError, FileNotFoundError):
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                stopped = False
                time.sleep(0.5)
        raise ValueError('quiet_boundary_deadline_original_parent_preserved')
    except BaseException:
        if stopped:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)
        raise


def takeover(physical):
    helper, assignments = release()
    require(bool(os.environ.get('NVIDIA_API_KEY')), 'privately_inherited_credential_required')
    require(time.time() < HARD_END - 120, 'unchanged_hard_end')
    folder = HERE / 'parents' / ('physical' + str(physical))
    require(not (folder / 'TERMINATION_ONCE.json').exists(), 'no_duplicate_takeover')
    prepared = read(folder / 'PREPARATION.json')
    predecessor = prepared['predecessor']
    original = read(folder / 'PREDECESSOR_CONFIG.json')
    bootstrap = read(folder / 'LIVE_BOOTSTRAP_READY.json')['snapshot']
    require(bootstrap['caught_up'], 'verified_live_bootstrap_before_takeover')
    require(sha(predecessor['config']['path']) == predecessor['config']['sha256'], 'unchanged_predecessor_config')
    expected = dict(pid=predecessor['process']['pid'], ticks=predecessor['process']['start_ticks'], argv=predecessor['expected_argv'], uid=os.getuid())
    check = subprocess.run([sys.executable, '-B', __file__, 'preflight', '--physical', str(physical)], capture_output=True, text=True, timeout=30)
    require(check.returncode == 0, 'receiving_CPU_preflight_before_pause')
    descriptor, reserved = quiet_pause(expected, predecessor['output'], original, time.monotonic() + 150)
    terminated = False
    try:
        config = make_config(original, assignments[physical], helper, folder / 'PRINCIPLES_R175.md',
                             predecessor['output'], predecessor['started']['sha256'], reserved)
        require(bootstrap['response_count'] >= reserved['response_cursor'] and bootstrap['request_count'] >= reserved['request_cursor'], 'bootstrap_covers_reserved_lifetime_cursors')
        write(folder / 'PREDECESSOR_SETTLED_LEDGER.json', reserved)
        seed = dict(schema='R166_PARENT_SUCCESSOR_V1', journal_id=bootstrap['journal_id'],
            object_delivered_turns={}, last_response_count=reserved['response_cursor'],
            last_request_count=reserved['request_cursor'], prospective_request_count=bootstrap['request_count'],
            credits={}, grammar_delivered=False, attempts=[],
            legacy_ledger=reference(folder / 'PREDECESSOR_SETTLED_LEDGER.json'),
            legacy_pending_ids_preserved=reserved['pending_existing_inbox_ids'],
            structured_object_and_credit_state='not present in legacy ledger; new prospective accounting, no inferred credits',
            old_publications_not_replayed_or_used_as_new_policy_exposure=True)
        write(folder / 'SEED.json', seed)
        config['predecessor_seed'] = reference(folder / 'SEED.json')
        write(folder / 'CONFIG.json', config)
        check = subprocess.run([sys.executable, '-B', __file__, 'preflight', '--physical', str(physical), '--final'], capture_output=True, text=True, timeout=30)
        require(check.returncode == 0, 'final_receiving_CPU_preflight')
        write(folder / 'CPU_PREFLIGHT.json', json.loads(check.stdout))
        require(same(expected, identity(expected['pid'])), 'identity_before_termination')
        require(ledger(predecessor['output'], original) == reserved, 'settled_ledger_unchanged')
        write(folder / 'TERMINATION_ONCE.json', dict(identity=expected, at_unix=time.time(), reason='GO_bound_parent_only_takeover', child_signal=False))
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        terminated = True
        require(bool(select.select([descriptor], [], [], 20)[0]), 'old_parent_exit_before_new_lead')
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'serve', '--physical', str(physical)]
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
        process = subprocess.Popen(command, env=environment, cwd=REPO, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        successor_identity = identity(process.pid)
        receipt = dict(status='NEW_PARENT_STARTED_NOT_DELIVERY', physical=physical, arm=assignments[physical]['arm'],
                       identity=successor_identity, predecessor=expected, source_bundle=str(HERE / ('source_' + assignments[physical]['arm'])),
                       helper_sha256=HELPER_SHA, assignments_sha256=ASSIGNMENT_SHA,
                       config=reference(folder / 'CONFIG.json'), pending_existing_inbox_ids=reserved['pending_existing_inbox_ids'],
                       started_unix=time.time(), child_restarts=0, hard_end_unix=HARD_END)
        write(folder / 'SPAWNED.json', receipt)
        return receipt
    finally:
        if not terminated:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


def serve(physical):
    import snapshot_transport
    folder = HERE / 'parents' / ('physical' + str(physical))
    try:
        require(bool(os.environ.get('NVIDIA_API_KEY')), 'private_inherited_credential')
        parent, provider, config, helper = runtime(physical, folder / 'CONFIG.json')
        policy = importlib.import_module('gpu.orch_r166_parent_policy')
        seed = read(folder / 'SEED.json')
        output = folder / 'parent'
        observed = read(folder / 'LIVE_BOOTSTRAP_READY.json')
        cursor = observed['cursor']
        sequence = 0
        first = None
        with policy.community.parent_lock(output):
            write(output / 'STARTED.json', dict(pid=os.getpid(), started_unix=time.time(),
                config_sha256=sha(folder / 'CONFIG.json'), model=MODEL, branch=config['branch'],
                programme=config['programme'], schedule_on='response', arm=config['r175_arm'],
                actual_tick=reference(policy.__file__), actual_provider=reference(provider.__file__),
                legacy_ledger=seed['legacy_ledger'], no_child_restart=True))
            while time.time() < HARD_END:
                observed = snapshot_transport.poll(physical, cursor)
                cursor, state = observed['cursor'], observed['snapshot']
                if first is not None and not (folder / 'FIRST_RENDERED_REQUEST.json').exists():
                    delivery = state['delivered'].get(first['publication']['id'])
                    if delivery is not None:
                        require(delivery['text_sha256'] == first['message_sha256'], 'exact_first_rendered_message')
                        write(folder / 'FIRST_RENDERED_REQUEST.json', dict(status='VERIFIED_RENDERED_TRAIN_REQUEST',
                            physical=physical, arm=config['r175_arm'], publication=reference(folder / 'FIRST_PUBLICATION.json'),
                            delivered=delivery, snapshot_head=state['head_sha256'], journal_id=state['journal_id'],
                            verified_by=reference(HERE / ('source_' + config['r175_arm']) / 'gpu/orch_r166_parent_snapshot.py'),
                            observed_unix=time.time(), baseline_sleep_count=delivery['sleep_count']))
                rendered_path = folder / 'FIRST_RENDERED_REQUEST.json'
                withdrawing = False
                if rendered_path.exists():
                    anchor = read(rendered_path)
                    if state['sleep_count'] >= anchor['baseline_sleep_count'] + 3:
                        if not (folder / 'AUDIT_AT_3_SLEEPS.json').exists():
                            write(folder / 'AUDIT_AT_3_SLEEPS.json', dict(status='THREE_ACTUAL_COMPLETED_SLEEPS_EVIDENCE_REVIEW_DUE',
                                baseline=reference(rendered_path), observed_sleep_count=state['sleep_count'],
                                changed_intention_per_cycle='UNKNOWN_UNTIL_ACTUAL_TRAIN_EVIDENCE_INSPECTION',
                                compaction_carry='UNKNOWN_UNTIL_ACTUAL_COMPACTION_INSPECTION',
                                recent_events=state['events'], snapshot_head=state['head_sha256'], no_invented_outcomes=True))
                        if not (folder / 'WITHDRAWAL_STARTED.json').exists():
                            write(folder / 'WITHDRAWAL_STARTED.json', dict(started_unix=time.time(),
                                start_sleep_count=state['sleep_count'], resume_after_sleep_count=state['sleep_count']+1,
                                no_new_parent_turns=True, peer_service='NOT_ACTIVE_ASSIGNED_ONLY',
                                old_invitations_remain_visible=True, clean_context_claim=False))
                    withdrawal_path = folder / 'WITHDRAWAL_STARTED.json'
                    if withdrawal_path.exists() and not (folder / 'WITHDRAWAL_COMPLETE.json').exists():
                        withdrawal = read(withdrawal_path)
                        if state['sleep_count'] >= withdrawal['resume_after_sleep_count']:
                            write(folder / 'WITHDRAWAL_COMPLETE.json', dict(observed_unix=time.time(),
                                actual_sleep_count=state['sleep_count'], started=reference(withdrawal_path)))
                        else:
                            withdrawing = True
                status = dict(status='ONE_COMPLETED_SLEEP_PARENT_WITHDRAWAL') if withdrawing else policy.tick(REPO, config, output, seed, state)
                write(folder / ('STATUS_%06d.json' % sequence), dict(status=status['status'], observed_unix=time.time(),
                    physical=physical, response_count=state['response_count'], request_count=state['request_count'],
                    sleep_count=state['sleep_count'], caught_up=state['caught_up'], head_sha256=state['head_sha256'],
                    actual_tick='gpu.orch_r166_parent_policy.tick', cadence=config['cadence_responses']))
                if first is None:
                    for attempt in sorted(output.glob('parent_*')):
                        result_path = attempt / 'RESULT.json'
                        if not result_path.exists():
                            continue
                        result = read(result_path)
                        if result['status'] == 'PUBLISHED':
                            first = dict(status='PUBLISHED_RENDER_NOT_YET_VERIFIED', physical=physical,
                                arm=config['r175_arm'], config=reference(folder / 'CONFIG.json'), result=reference(result_path),
                                source=reference(attempt / 'SOURCE.json'), prompt=reference(attempt / 'PROMPT.json'),
                                requested_model=MODEL, actual_model=result['model'], publication=result['publication'],
                                message_sha256=hashlib.sha256(result['message'].encode()).hexdigest(),
                                source_response_count=read(attempt / 'SOURCE.json')['response_count'], schedule_on='response',
                                published_observed_unix=time.time(), helper_sha256=HELPER_SHA, assignments_sha256=ASSIGNMENT_SHA)
                            write(folder / 'FIRST_PUBLICATION.json', first)
                            break
                sequence += 1
                time.sleep(max(2, config.get('poll_interval_seconds', 0.25)))
            write(folder / 'TERMINAL.json', dict(status='UNCHANGED_1650_PDT_PARENT_STOP', at_unix=time.time()))
    except BaseException as error:
        if not (folder / 'SERVICE_FAILED.json').exists():
            write(folder / 'SERVICE_FAILED.json', dict(status='PARENT_SERVICE_FAILED', error_type=type(error).__name__,
                reason=str(error)[:500] if isinstance(error, ValueError) else 'inspect_owned_operational_receipts', at_unix=time.time()))
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'preflight', 'takeover', 'serve'))
    parser.add_argument('--physical', type=int, choices=PHYSICALS)
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare()
    elif args.action == 'preflight':
        print(json.dumps(preflight(args.physical, args.final), sort_keys=True))
    elif args.action == 'takeover':
        print(json.dumps(takeover(args.physical), sort_keys=True))
    else:
        serve(args.physical)


if __name__ == '__main__':
    main()
