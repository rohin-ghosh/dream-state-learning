"""Exact-owner R175 parent-only takeover and rendered-exposure observation."""

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import sys
import time


ASSIGNMENTS_SHA = '25b45432bebb388e920d5cc8dc8fed6c705cd54156cbfd530828e1520a9174b2'
BUILDER_SHA = 'ae2c9df909d9b48ebebef968690ee2e4c9085452151dbb96474311cf55b11923'
ERRATA_SHA = 'cd51e8bacdfa171127c537502c2159f59e1e0fdfa80f4ec7ed684e3e65ff22b9'
RESPONSE_SHA = 'a0f8d74530b558724a8b5636a5b53556abd21267c316d94b3beeb08cd41c61a1'
LANES = {'run1': 'A', 'pilot': 'B', 'repo_reader': 'C', 'C1': 'B', 'C3': 'A', 'C4': 'C', 'C5': 'D'}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def reference(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def install_private_errata(policy, path):
    require(sha(path) == ERRATA_SHA, 'exact_Main_private_errata')
    base_prompt = policy.prompt
    errata = Path(path).read_text()

    def prompt_with_errata(config, state, memory_state):
        instruction, payload = base_prompt(config, state, memory_state)
        return instruction + '\n\n' + errata, payload

    policy.prompt = prompt_with_errata
    return base_prompt


def install_response_compatibility(policy, source):
    from gpu import orch_r175_parent_response as response
    from gpu import orch_route_parent_campaign_providers as providers
    require(Path(response.__file__).resolve() == (source / 'gpu/orch_r175_parent_response.py').resolve()
            and sha(response.__file__) == RESPONSE_SHA, 'exact_Main_lossless_response_adapter')
    originals = dict(provider=providers.response_schema, community=policy.community.response_schema)
    for original in originals.values():
        require(Path(original.__code__.co_filename).resolve().is_relative_to(source.resolve()),
                'original_strict_parser_is_owned')
    providers.response_schema = response.compatible_parser(originals['provider'])
    policy.community.response_schema = response.compatible_parser(originals['community'])
    return dict(adapter=reference(response.__file__),
        original_files={name: parser.__code__.co_filename for name, parser in originals.items()},
        effective_files=dict(provider=providers.response_schema.__code__.co_filename,
                             community=policy.community.response_schema.__code__.co_filename),
        strict_validators_preserved=True, messages_ids_counters_unchanged=True)


def identity(pid):
    process = Path('/proc') / str(pid)
    before = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    raw = (process / 'cmdline').read_bytes()
    current = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    require(before[19] == current[19], 'stable_pid_identity')
    return dict(pid=pid, start_ticks=int(current[19]), uid=process.stat().st_uid,
        state=current[0], cwd=os.readlink(process / 'cwd'), argv_sha256=hashlib.sha256(raw).hexdigest())


def validate_owner(row, actual, *, paused=False):
    require(row['label'] in LANES and actual['uid'] == os.getuid(), 'owned_assigned_parent_C2_excluded')
    require(all(actual[key] == row[key] for key in ('pid', 'start_ticks', 'cwd', 'argv_sha256')),
            'exact_bound_parent_identity')
    require(actual['state'] not in ('Z', 'X') and
            (paused or actual['state'] not in ('T', 't')), 'parent_not_externally_stopped')


def children(pid):
    result = set()
    for path in (Path('/proc') / str(pid) / 'task').glob('*/children'):
        result.update(path.read_text().split())
    return sorted(result)


def validate_predecessor_pins(row):
    for key in ('config', 'gate', 'binding', 'source_on_disk', 'operator'):
        pin = row.get(key)
        if pin:
            require(sha(pin['path']) == pin['sha256'], 'unchanged_predecessor_' + key)


def verify_admission(policy, config, manifest, gate, source, output):
    policy.validate(config)
    require(gate['status'] == 'MAIN_DELEGATED_R175_GO' and
            gate['assignments']['sha256'] == ASSIGNMENTS_SHA and
            sha(gate['assignments']['path']) == ASSIGNMENTS_SHA, 'exact_Main_delegation')
    require(config['r175_arm'] == LANES[manifest['label']] and
            config['schedule_on'] == 'response' and
            config['root'] == read(manifest['predecessor']['config']['path'])['root'], 'exact_arm_root_clock')
    require(gate['config_sha256'] == policy._digest(config) and gate['output'] == str(output) and
            time.time() < gate['expires_unix'] == config['hard_end_unix'], 'exact_config_output_wall')
    require(all(gate['custody'][key] for key in
                ('predecessor_terminal', 'no_competing_parent', 'pending_reconciled')), 'actual_custody')
    for pin in (gate['custody']['receipt'], gate['cpu_receipt']):
        require(sha(pin['path']) == pin['sha256'], 'admission_receipt_pin')
    cpu = read(gate['cpu_receipt']['path'])
    require(cpu['status'] == 'PASS' and cpu['execution_kind'] == 'CPU_ONLY' and
            cpu['source_pins'] == manifest['source_pins'] and cpu['activation_tests_executed'] is True,
            'actual_owned_source_activation_tests')
    require(set(policy.SOURCE_FILES) | {'gpu/ovx3_ssh.sh'} <= set(manifest['source_pins']), 'complete_source_closure')
    for name, expected in manifest['source_pins'].items():
        require(sha(source / name) == expected, 'immutable_admitted_source')
    require(Path(policy.tick.__code__.co_filename).resolve() ==
            (source / 'gpu/orch_r166_parent_policy.py').resolve(), 'actual_admitted_tick')
    seed = policy.pinned(config['predecessor_seed'])
    for entry in seed['attempts']:
        require(policy.pinned(entry['refs']['source']) == entry['source'] and
                policy.pinned(entry['refs']['result']) == entry['result'], 'preserved_seed_evidence')


def legacy_seed(output, snapshot, config):
    attempts, pins, last_response, last_request = [], [], 0, 0
    for directory in sorted(Path(output).glob('parent_*')):
        require((directory / 'SOURCE.json').is_file() and (directory / 'RESULT.json').is_file(),
                'unfinished_legacy_attempt_no_replay')
        source, result = read(directory / 'SOURCE.json'), read(directory / 'RESULT.json')
        require(source['schema'] == 'R133_TRAIN_PARENT_SNAPSHOT_V1' and
                result['branch'] == config['branch'] and
                result['source_head_sha256'] == source['head_sha256'] and
                result['source_response_count'] == source['response_count'], 'legacy_source_binding')
        require(result['status'] in ('MISSING', 'SILENT', 'PUBLISHED'), 'legacy_terminal_status')
        require(not (result['status'] == 'MISSING' and 'sent_unix' in result),
                'uncertain_legacy_publication_requires_reconciliation')
        if result['status'] == 'PUBLISHED':
            publication = result['inbox_publication']
            delivered = snapshot['delivered'].get(publication['id'])
            require(delivered is not None and delivered['speaker'] == 'Astra' and
                    delivered['inbox_sha256'] == publication['sha256'] and
                    delivered['text_sha256'] == hashlib.sha256(result['response']['message'].encode()).hexdigest(),
                    'legacy_publication_must_be_actually_rendered')
            attempts.append(dict(publication=publication, rendered=delivered))
        last_response = max(last_response, source['response_count'])
        last_request = max(last_request, source['request_count'])
        pins.extend((reference(directory / 'SOURCE.json'), reference(directory / 'RESULT.json')))
    require(snapshot['response_count'] >= last_response and snapshot['request_count'] >= last_request,
            'no_legacy_cursor_rewind')
    seed = dict(schema='R166_PARENT_SUCCESSOR_V1', journal_id=snapshot['journal_id'], attempts=[],
        object_delivered_turns={}, last_response_count=last_response, last_request_count=last_request,
        prospective_request_count=snapshot['request_count'], credits={}, grammar_delivered=False)
    return seed, dict(schema='R175_LEGACY_STATE_RECONCILIATION_V1', preserved_receipts=pins,
        rendered_publications=attempts, old_source_has_no_structured_object_credit_ledger=True,
        old_INBOX_only_DELIVERED_not_used_as_render_proof=True, child_context_unchanged=True)


def exposure(publication, message, snapshot):
    delivery = snapshot['delivered'].get(publication['id'])
    if delivery is None:
        return None
    require(delivery['speaker'] == 'Astra' and delivery['inbox_sha256'] == publication['sha256'] and
            delivery['text_sha256'] == hashlib.sha256(message.encode()).hexdigest(),
            'exact_new_rendered_Astra_publication')
    require(all(type(delivery[key]) is int for key in ('record_index', 'request_count', 'sleep_count')),
            'actual_REQUEST_and_sleep_anchor')
    return dict(publication=publication, rendered=delivery,
        first_exposure_sleep_count=delivery['sleep_count'],
        three_sleep_check_at=delivery['sleep_count'] + 3,
        withdrawal_complete_at=delivery['sleep_count'] + 4,
        publication_is_not_alone_exposure=True)


def watchdog(descriptor, read_end, output):
    ready = select.select([read_end], [], [], 45)[0]
    cancelled = bool(ready and os.read(read_end, 1) == b'C')
    if not cancelled and not select.select([descriptor], [], [], 0)[0]:
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        write(output / 'WATCHDOG_RESUMED_EXACT_PARENT.json', dict(observed_unix=time.time(), child_signals=0))
    os._exit(0)


def snapshot_poll(policy, source, config, cursor_reference, *, bootstrap=False):
    script = ('import json; from snapshot_identity import install, stored_poll; install(); '
              'root=' + repr(config['root']) + '; store=' + repr(config['cursor_store']) + '; '
              'ref=' + repr(cursor_reference) + '\n'
              'for index in range(' + ('256' if bootstrap else '1') + '):\n'
              ' observed=stored_poll(root,store,ref); ref=observed["reference"]\n'
              ' if observed["snapshot"]["caught_up"]: break\n'
              'print(json.dumps(observed))')
    return policy.parent.remote(source, config, script)


def activate(manifest_path, manifest_sha):
    require(sha(manifest_path) == manifest_sha, 'exact_activation_manifest')
    manifest = read(manifest_path)
    label, row = manifest['label'], manifest['predecessor']
    require(label in LANES and row['label'] == label and manifest['arm'] == LANES[label], 'assigned_lane_only')
    require(sha(manifest['assignments']['path']) == ASSIGNMENTS_SHA, 'exact_Main_assignment_bytes')
    source, output = Path(manifest['source']), Path(manifest['output'])
    require(not output.exists(), 'fresh_operator_output_no_consumed_retry')
    require(sha(__file__) == manifest['operator_sha256'], 'pinned_operator_source')
    require(sha(manifest['sanctioned_transport']['path']) == manifest['sanctioned_transport']['sha256'],
            'unchanged_sanctioned_transport_no_credential_copy')
    output.mkdir(mode=0o700)
    sys.path.insert(0, str(source))
    from gpu import orch_r166_parent_policy as policy
    from gpu import orch_r175_parent_arms as arms
    require(sha(arms.__file__) == BUILDER_SHA, 'pinned_Main_configure_helper')
    policy_file = source / 'gpu/orch_r166_parent_policy.py'
    require(Path(policy.__file__).resolve() == policy_file.resolve() and
            Path(policy.tick.__code__.co_filename).resolve() == policy_file.resolve() and
            Path(policy.prompt.__code__.co_filename).resolve() == policy_file.resolve(),
            'actual_owned_r166_tick_and_prompt_imports')
    base_prompt = install_private_errata(policy, source / 'PARENT_METADATA_ERRATA_V1.md')
    parser_provenance = install_response_compatibility(policy, source)
    for name, expected in manifest['source_pins'].items():
        require(sha(source / name) == expected, 'admitted_source_pin')
    cpu = read(manifest['cpu_receipt']['path'])
    require(sha(manifest['cpu_receipt']['path']) == manifest['cpu_receipt']['sha256'] and
            cpu['status'] == 'PASS' and cpu['source_pins'] == manifest['source_pins'], 'bound_CPU_pass')
    write(output / 'OPERATOR_STARTED.json', dict(pid=os.getpid(), observed_unix=time.time(), label=label,
        status='WAITING_QUIET_PARENT_NOT_SWITCHED', predecessor=row,
        tick_file=policy.tick.__code__.co_filename, base_prompt_file=base_prompt.__code__.co_filename,
        private_prompt_wrapper_file=policy.prompt.__code__.co_filename,
        private_errata=reference(source / 'PARENT_METADATA_ERRATA_V1.md'),
        parser_provenance=parser_provenance,
        executed_policy_sha256=sha(policy_file), child_signals=0))
    require(sha(row['config']['path']) == row['config']['sha256'], 'original_config_unchanged')
    original = read(row['config']['path'])
    validate_predecessor_pins(row)
    config = arms.configure(original, manifest['arm'])
    config.update(source_root=manifest['remote_source'], cursor_store=manifest['remote_cursor'])
    probe = ('import json; from pathlib import Path; import hashlib; root=Path(' + repr(config['source_root']) +
        '); pins=' + repr(manifest['source_pins']) + '; '
        'assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in pins.items()); '
        'print(json.dumps({"source_verified":True}))')
    require(policy.parent.remote(source, config, probe) == {'source_verified': True}, 'receiving_exact_source_closure')
    policy.parent.transport_preflight(source, config)
    observed = snapshot_poll(policy, source, config, None, bootstrap=True)
    write(output / 'BOOTSTRAP.json', observed)
    cursor_reference = observed['reference']
    descriptor, paused, retired, watchdog_pid, cancel_end = None, False, False, None, None
    deadline = min(time.time() + 600, original['hard_end_unix'])
    try:
        while True:
            validate_owner(row, identity(row['pid']))
            validate_predecessor_pins(row)
            require(time.time() < deadline, 'quiet_parent_wait_expired_original_preserved')
            require(sha(row['config']['path']) == row['config']['sha256'], 'predecessor_config_pin')
            state = observed['snapshot']
            if state['caught_up'] and not children(row['pid']):
                try:
                    if row['entry_kind'] == 'DIRECT_COMMUNITY_PARENT':
                        seed = policy.export_predecessor(row['output_path'], state)
                        reconciliation = dict(kind='R153_EXACT_ATTEMPT_EXPORT')
                    else:
                        seed, reconciliation = legacy_seed(row['output_path'], state, original)
                    require(not policy.memory(seed, [], state)['awaiting_render'], 'pending_publication_not_rendered')
                    break
                except (ValueError, FileNotFoundError) as error:
                    write(output / ('WAIT_' + str(time.time_ns()) + '.json'),
                          dict(reason=type(error).__name__, detail=str(error)[:160], child_signals=0))
            time.sleep(2)
            observed = snapshot_poll(policy, source, config, cursor_reference, bootstrap=True)
            cursor_reference = observed['reference']
        write(output / 'PREPAUSE_RECONCILIATION.json', reconciliation)
        seed_before = copy.deepcopy(seed)
        descriptor = os.pidfd_open(row['pid'])
        validate_owner(row, identity(row['pid']))
        read_end, cancel_end = os.pipe()
        watchdog_pid = os.fork()
        if watchdog_pid == 0:
            os.close(cancel_end)
            watchdog(descriptor, read_end, output)
        os.close(read_end)
        write(output / 'PARENT_PAUSE_INTENT.json', dict(parent=row, observed_unix=time.time(), child_signals=0))
        signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
        paused = True
        for unused in range(100):
            if identity(row['pid'])['state'] in ('T', 't'):
                break
            time.sleep(.01)
        validate_owner(row, identity(row['pid']), paused=True)
        validate_predecessor_pins(row)
        require(identity(row['pid'])['state'] in ('T', 't') and not children(row['pid']),
                'quiet_parent_no_transport_children')
        if row['entry_kind'] == 'DIRECT_COMMUNITY_PARENT':
            seed = policy.export_predecessor(row['output_path'], state)
        else:
            seed, reconciliation = legacy_seed(row['output_path'], state, original)
        require(seed == seed_before, 'predecessor_ledger_unchanged_at_pause')
        write(output / 'SEED.json', seed)
        write(output / 'RECONCILIATION.json', reconciliation)
        config = policy.build_config(original, seed_ref=reference(output / 'SEED.json'),
            cursor_store=manifest['remote_cursor'], community_learner=row['entry_kind'] == 'DIRECT_COMMUNITY_PARENT')
        config = arms.configure(config, manifest['arm'])
        config['source_root'] = manifest['remote_source']
        policy.validate(config)
        write(output / 'CONFIG.json', config)
        custody = dict(predecessor=row, predecessor_terminal=False, pending_reconciled=True,
            no_competing_parent=True, seed=reference(output / 'SEED.json'), observed_unix=time.time(), child_signals=0)
        write(output / 'PARENT_RETIRE_INTENT.json', custody)
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        retired = True
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        paused = False
        require(bool(select.select([descriptor], [], [], 20)[0]), 'predecessor_exit_required_before_successor')
        custody.update(predecessor_terminal=True, observed_unix=time.time())
        write(output / 'PARENT_EXITED.json', custody)
        gate = dict(schema='R175_NODE5_DELEGATED_PARENT_ADMISSION_V1', status='MAIN_DELEGATED_R175_GO',
            prepared_by='NODE5_BUILDER', assignments=manifest['assignments'],
            confirmation_basis='User GO delegates node activation using exact Main assignments and tested builder API; not a new Main signature',
            config_sha256=policy._digest(config), output=str(output), parented_scope=True,
            expires_unix=original['hard_end_unix'],
            custody=dict(predecessor_terminal=True, no_competing_parent=True, pending_reconciled=True,
                         receipt=reference(output / 'PARENT_EXITED.json')),
            cpu_receipt=manifest['cpu_receipt'], intake=manifest['assignments'],
            source_pins=manifest['source_pins'], remote_source_pins=manifest['source_pins'])
        write(output / 'GATE.json', gate)
        verify_admission(policy, config, manifest, gate, source, output)
        with policy.community.parent_lock(output):
            write(output / 'ACTIVE_PARENT.json', dict(pid=os.getpid(), identity=identity(os.getpid()),
                observed_unix=time.time(), label=label, arm=manifest['arm'], config=reference(output / 'CONFIG.json'),
                gate=reference(output / 'GATE.json'), tick_file=policy.tick.__code__.co_filename,
                base_prompt_file=base_prompt.__code__.co_filename,
                private_prompt_wrapper_file=policy.prompt.__code__.co_filename,
                private_errata=reference(source / 'PARENT_METADATA_ERRATA_V1.md'),
                parser_provenance=parser_provenance,
                executed_policy_sha256=sha(policy_file),
                legacy_r153_tick_used=False, first_publication=None, first_rendered_REQUEST=None))
            if cancel_end is not None:
                os.write(cancel_end, b'C')
                os.close(cancel_end)
                cancel_end = None
            if watchdog_pid:
                os.waitpid(watchdog_pid, 0)
                watchdog_pid = None
            first = None
            sequence = 0
            while time.time() < gate['expires_unix']:
                observed = snapshot_poll(policy, source, config, cursor_reference, bootstrap=True)
                cursor_reference = observed['reference']
                state = observed['snapshot']
                write(output / f'POLL_{sequence:08d}.json', observed)
                for path in sorted(output.glob('parent_*/RESULT.json')):
                    result = read(path)
                    if result.get('status') == 'PUBLISHED':
                        if not (output / 'FIRST_PUBLICATION.json').exists():
                            write(output / 'FIRST_PUBLICATION.json', dict(result=reference(path),
                                publication=result['publication'], observed_unix=time.time(), rendered=False))
                        proof = exposure(result['publication'], result['message'], state)
                        if proof is not None and first is None:
                            first = proof
                            write(output / 'FIRST_RENDERED_REQUEST.json', dict(proof,
                                result=reference(path), snapshot=reference(output / f'POLL_{sequence:08d}.json'),
                                observed_unix=time.time(), peer_channel_active=False))
                if first is not None and state['sleep_count'] >= first['three_sleep_check_at']:
                    status = dict(status='WITHDRAWAL_NO_NEW_PARENT_OR_PEER', sleep_count=state['sleep_count'],
                        pending_old_invitations_preserved=True, failure_assessment='UNKNOWN_NOT_RETIREMENT')
                    if state['sleep_count'] >= first['withdrawal_complete_at']:
                        write(output / 'WITHDRAWAL_COMPLETE.json', dict(status, observed_unix=time.time()))
                        return
                else:
                    status = policy.tick(source, config, output, seed, state)
                write(output / f'STATUS_{sequence:08d}.json', status)
                sequence += 1
                time.sleep(config.get('poll_interval_seconds', 5))
    except BaseException as error:
        write(output / 'FAILED_CLOSED.json', dict(error_type=type(error).__name__, error=str(error)[:240],
            retired=retired, parent_paused=paused, child_signals=0, observed_unix=time.time()))
        raise
    finally:
        if paused and descriptor is not None and not retired:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        if cancel_end is not None:
            os.write(cancel_end, b'C')
            os.close(cancel_end)
        if watchdog_pid:
            os.waitpid(watchdog_pid, 0)
        if descriptor is not None:
            os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    arguments = parser.parse_args()
    try:
        activate(arguments.manifest, arguments.manifest_sha256)
    except BaseException as error:
        if sha(arguments.manifest) == arguments.manifest_sha256:
            failed_output = Path(read(arguments.manifest)['output'])
            if failed_output.is_dir() and not (failed_output / 'FAILED_CLOSED.json').exists():
                write(failed_output / 'FAILED_CLOSED.json', dict(error_type=type(error).__name__,
                    error=str(error)[:240], retired=(failed_output / 'PARENT_RETIRE_INTENT.json').exists(),
                    child_signals=0, observed_unix=time.time(), status='OPERATOR_FAILED_NOT_CHILD_FAILURE'))
        raise
