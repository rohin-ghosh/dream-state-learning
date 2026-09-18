"""One-parent route rebind carrying pending publications, never a baseline replay."""

import argparse
import copy
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

from console_baseline import parent_census, read, ref, require, retire_exact, sha, write


def terminal_parent_receipt(output):
    withdrawal = output / 'WITHDRAWAL_COMPLETE.json'
    if withdrawal.exists():
        return ref(withdrawal)
    failed = output / 'FAILED_CLOSED.json'
    document = read(failed)
    require(document.get('error_type') == 'FileExistsError' and document.get('child_signals') == 0
            and str(output / 'parent_') in document.get('error', ''), 'only_consumed_CPU_parent_failure')
    return ref(failed)


def load(source):
    sys.path.insert(0, str(source))
    specification = importlib.util.spec_from_file_location('owned_activation', source / 'activate_parent.py')
    runtime = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(runtime)
    from gpu import orch_r166_parent_policy as policy
    from provider_route import install
    runtime.install_private_errata(policy, source / 'PARENT_METADATA_ERRATA_V1.md')
    parser = runtime.install_response_compatibility(policy, source)
    route = install(policy, source)
    from r184_parent_effort import install as install_effort
    effort = install_effort(policy, source)
    return runtime, policy, dict(parser=parser, route=route, effort=effort)


def export_state(policy, old, state, original):
    pending = []
    if (old / 'SEED.json').exists():
        seed = copy.deepcopy(read(old / 'SEED.json'))
        seed['attempts'].extend(policy.export_predecessor(old, state)['attempts'])
        policy.memory(seed, [], state)
        return seed, pending
    last_response = original.get('start_after_response_count', 0)
    last_request = original.get('start_after_request_count', 0)
    for directory in sorted(old.glob('parent_*')):
        source, result = read(directory / 'SOURCE.json'), read(directory / 'RESULT.json')
        require(result['status'] in ('PUBLISHED', 'SILENT', 'MISSING'), 'uncertain_legacy_no_replay')
        require(source['head_sha256'] == result['source_head_sha256'] and
                source['response_count'] == result['source_response_count'], 'legacy_source_binding')
        require(not (result['status'] == 'MISSING' and 'sent_unix' in result), 'uncertain_legacy_send')
        last_response = max(last_response, source['response_count'])
        last_request = max(last_request, source['request_count'])
        if result['status'] == 'PUBLISHED':
            pending.append(dict(publication=result['inbox_publication'], message=result['response']['message'],
                source=ref(directory / 'SOURCE.json'), result=ref(directory / 'RESULT.json')))
    require(last_response <= state['response_count'] and last_request <= state['request_count'], 'no_cursor_rewind')
    seed = dict(schema=policy.SCHEMA, journal_id=state['journal_id'], attempts=[],
        object_delivered_turns={}, last_response_count=last_response, last_request_count=last_request,
        prospective_request_count=state['request_count'], credits={}, grammar_delivered=False)
    return seed, pending


def pending_render(pending, state):
    unresolved = []
    for entry in pending:
        publication = entry['publication']
        delivery = state['delivered'].get(publication['id'])
        if delivery is None:
            unresolved.append(publication['id'])
        else:
            import hashlib
            require(delivery['speaker'] == 'Astra' and delivery['inbox_sha256'] == publication['sha256'] and
                delivery['text_sha256'] == hashlib.sha256(entry['message'].encode()).hexdigest(), 'exact_legacy_render')
    return unresolved


def eligible_exposure(attempt, identifiers):
    result = attempt['result']
    return result.get('status') == 'PUBLISHED' and result['publication']['id'] in identifiers


def verify_pending_receiver(policy, source, config, pending):
    entries = [dict(publication=entry['publication'], message=entry['message']) for entry in pending]
    script = ('import json,hashlib;from pathlib import Path;entries=' + repr(entries) + ';out=[]\n'
        'for entry in entries:\n'
        ' path=Path(entry["publication"]["path"]);raw=path.read_bytes();doc=json.loads(raw)\n'
        ' assert str(path.parent)=='+repr(config['root'] + '/stream/inbox')+'\n'
        ' assert hashlib.sha256(raw).hexdigest()==entry["publication"]["sha256"]\n'
        ' assert doc["id"]==entry["publication"]["id"] and doc["speaker"]=="Astra" and doc["split"]=="TRAIN" and doc["text"]==entry["message"]\n'
        ' out.append(entry["publication"])\nprint(json.dumps(out))')
    return policy.parent.remote(source, config, script)


def serve(binding_path, digest):
    require(sha(binding_path) == digest, 'exact_owned_route_binding')
    binding = read(binding_path)
    require(binding['label'] in ('C1','C3','C4','C5','run1','pilot','repo_reader'), 'C2_excluded')
    for pin in binding['pins']:
        require(sha(pin['path']) == pin['sha256'], 'immutable_route_input')
    source, old, output = Path(binding['source']), Path(binding['old_output']), Path(binding['output'])
    require(not output.exists(), 'one_new_route_operator_not_consumed_retry')
    output.mkdir(mode=0o700)
    runtime, policy, provenance = load(source)
    owner = binding['owner']
    original = read(binding['config'])
    config = dict(read(binding['successor_config']), source_root=binding['remote_source'], cursor_store=binding['remote_cursor'])
    dead = binding.get('terminal_parent_recovery', False)
    if dead:
        require(not Path('/proc', str(owner['pid'])).exists(), 'exact_terminal_parent_no_child_recovery')
        terminal_parent_receipt(old)
        require(parent_census(config['root'], os.getpid()) == [], 'no_parent_for_terminal_recovery')
    else:
        runtime.validate_owner(owner, runtime.identity(owner['pid']))
        require(parent_census(config['root'], os.getpid()) == [owner['pid']], 'one_exact_parent')
    observed = runtime.snapshot_poll(policy, source, config, None, bootstrap=True)
    state, cursor = observed['snapshot'], observed['reference']
    seed, legacy = export_state(policy, old, state, original)
    receiver = verify_pending_receiver(policy, source, config, legacy)
    write(output / 'PREFLIGHT.json', dict(observed_unix=time.time(), snapshot=observed, owner=owner,
        pending_legacy_receivers=receiver, seed_sha256=policy._digest(seed), provenance=provenance,
        no_baseline=True, child_signals=0, authority='Rohin179/181 exact working route; parent-only repair'))
    deadline = time.monotonic() + 90
    while not dead and runtime.children(owner['pid']):
        require(time.monotonic() < deadline, 'inflight_transport_preserved')
        time.sleep(.2)

    def revalidate(watchdog):
        require(parent_census(config['root'], os.getpid(), watchdog) == [owner['pid']], 'exclusive_parent_at_pause')
        for pin in binding['pins']:
            require(sha(pin['path']) == pin['sha256'], 'unchanged_bound_source_at_pause')
        require(export_state(policy, old, state, original) == (seed, legacy), 'reserved_ledger_unchanged')

    if dead:
        lock = os.open(old / 'PARENT.lock', os.O_RDWR | os.O_NOFOLLOW)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write(output / 'TERMINAL_PARENT_RECOVERY.json', dict(prior=terminal_parent_receipt(old),
            same_existing_lock_inode=os.fstat(lock).st_ino, prior_pid_absent=True, signals=0))
    elif binding.get('legacy_without_lock'):
        legacy_source = read(binding['legacy_binding'])['source_copy']
        require(sha(legacy_source) == binding['legacy_source_sha256'] and
                'flock' not in Path(legacy_source).read_text(), 'bound_legacy_has_no_writer_lock')
        descriptor = os.pidfd_open(owner['pid'])
        import select
        import signal
        runtime.validate_owner(owner, runtime.identity(owner['pid']))
        read_end, cancel_end = os.pipe()
        watcher = os.fork()
        if watcher == 0:
            os.close(cancel_end)
            runtime.watchdog(descriptor, read_end, output)
        os.close(read_end)
        stopped = False
        retired = False
        try:
            write(output / 'PARENT_PAUSE_INTENT.json', dict(owner=owner, actual_legacy_lock_absent=True, child_signals=0))
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            stopped = True
            deadline = time.monotonic() + 2
            while runtime.identity(owner['pid'])['state'] not in ('T','t') and time.monotonic() < deadline:
                time.sleep(.01)
            require(runtime.identity(owner['pid'])['state'] in ('T','t') and not runtime.children(owner['pid']), 'quiet_legacy_parent')
            revalidate(runtime.identity(watcher))
            write(output / 'PARENT_RETIRE_INTENT.json', dict(owner=owner, actual_legacy_lock_absent=True, child_signals=0))
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            retired = True
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            stopped = False
            require(bool(select.select([descriptor], [], [], 20)[0]), 'legacy_parent_exit')
        finally:
            if stopped and not retired:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            os.write(cancel_end, b'C')
            os.close(cancel_end)
            os.waitpid(watcher, 0)
            os.close(descriptor)
        write(output / 'PARENT_EXITED.json', dict(owner=owner, observed_unix=time.time(), child_signals=0))
        lock = None
    else:
        lock = retire_exact(runtime, owner, old / 'PARENT.lock', output, revalidate)
    try:
        require(parent_census(config['root'], os.getpid()) == [], 'no_competing_parent_after_exit')
        write(output / 'SEED.json', seed)
        write(output / 'LEGACY_PENDING.json', legacy)
        config.update(predecessor_seed=ref(output / 'SEED.json'))
        write(output / 'CONFIG.json', config)
        policy.validate(config)
        with policy.community.parent_lock(output):
            write(output / 'ACTIVE_PARENT.json', dict(pid=os.getpid(), identity=runtime.identity(os.getpid()),
                label=binding['label'], arm=config['r175_arm'], config=ref(output / 'CONFIG.json'),
                binding=ref(binding_path), observed_unix=time.time(), provenance=provenance,
                legacy_pending_carried_not_republished=[entry['publication']['id'] for entry in legacy],
                tick_file=policy.tick.__code__.co_filename, child_signals=0))
            first = binding.get('first_exposure')
            sequence = 0
            while time.time() < config['hard_end_unix']:
                observed = runtime.snapshot_poll(policy, source, config, cursor, bootstrap=True)
                state, cursor = observed['snapshot'], observed['reference']
                poll = output / f'POLL_{sequence:08d}.json'
                write(poll, observed)
                new_attempts = policy.local_attempts(output)
                if provenance['effort'] is not None:
                    for attempt in new_attempts:
                        result = attempt['result']
                        if result['status'] != 'PUBLISHED':
                            continue
                        if not (output / 'R184_FIRST_PUBLICATION.json').exists():
                            from r184_parent_effort import publication_refs
                            write(output / 'R184_FIRST_PUBLICATION.json', dict(publication=result['publication'],
                                actual_attempt=publication_refs(output, result),
                                phase=provenance['effort'], observed_unix=time.time(), model=result.get('model')))
                        proof = runtime.exposure(result['publication'], result['message'], state)
                        examples = provenance['effort'].get('examples')
                        if examples is not None and not (output / 'R188_FIRST_PHASE_PUBLICATION.json').exists():
                            from r184_parent_effort import publication_refs
                            actual = publication_refs(output, result)
                            require(examples['marker'] in read(actual['prompt']['path'])['instruction'], 'actual_R188_outbound_prompt')
                            write(output / 'R188_FIRST_PHASE_PUBLICATION.json', dict(publication=result['publication'],
                                actual_attempt=actual, examples=examples, observed_unix=time.time(),
                                model=result.get('model'), worked_example_content_requires_read=True))
                        if examples is not None and proof is not None and not (output / 'R188_FIRST_RENDERED_REQUEST.json').exists():
                            write(output / 'R188_FIRST_RENDERED_REQUEST.json', dict(proof, snapshot=ref(poll),
                                examples=examples, observed_unix=time.time()))
                        if proof is not None and not (output / 'R184_FIRST_RENDERED_REQUEST.json').exists():
                            write(output / 'R184_FIRST_RENDERED_REQUEST.json', dict(proof, snapshot=ref(poll),
                                phase=provenance['effort'], observed_unix=time.time()))
                identifiers = set(binding['eligible_publication_ids']) | {
                    entry['result']['publication']['id'] for entry in new_attempts if entry['result']['status'] == 'PUBLISHED'}
                attempts = seed['attempts'] + new_attempts
                for attempt in attempts:
                    result = attempt['result']
                    if not eligible_exposure(attempt, identifiers):
                        continue
                    if not (output / 'FIRST_PUBLICATION.json').exists():
                        write(output / 'FIRST_PUBLICATION.json', dict(publication=result['publication'],
                            observed_unix=time.time(), inherited=attempt in seed['attempts'], model=result.get('model')))
                    proof = runtime.exposure(result['publication'], result['message'], state)
                    if proof is not None and first is None:
                        first = proof
                        write(output / 'FIRST_RENDERED_REQUEST.json', dict(proof, snapshot=ref(poll), observed_unix=time.time()))
                pending = pending_render(legacy, state)
                fable_waiting = [identifier for identifier in binding['fable_ids'] if identifier not in state['delivered']]
                if pending or fable_waiting:
                    status = dict(status='AWAITING_EXISTING_INBOX_RENDER_NO_DUPLICATE', legacy=pending, fable=fable_waiting)
                elif first is not None and state['sleep_count'] >= first['three_sleep_check_at']:
                    status = dict(status='WITHDRAWAL_NO_NEW_PARENT_OR_PEER', sleep_count=state['sleep_count'])
                    if state['sleep_count'] >= first['withdrawal_complete_at']:
                        write(output / 'WITHDRAWAL_COMPLETE.json', dict(status, observed_unix=time.time()))
                        return
                else:
                    from retry_prepublication import consumed_request, retry_once
                    status = retry_once(policy, source, config, output, seed, state)
                    if status is None:
                        if consumed_request(seed, policy.local_attempts(output), state):
                            status = dict(status='CONSUMED_SOURCE_WAITING_NEW_REQUEST_NO_REPLAY')
                        else:
                            status = policy.tick(source, config, output, seed, state)
                write(output / f'STATUS_{sequence:08d}.json', status)
                sequence += 1
                time.sleep(config.get('poll_interval_seconds', 5))
    finally:
        if lock is not None:
            os.close(lock)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    arguments = parser.parse_args()
    try:
        serve(arguments.binding, arguments.sha256)
    except BaseException as error:
        output = Path(read(arguments.binding)['output'])
        if output.exists():
            write(output / 'FAILED_CLOSED.json', dict(error_type=type(error).__name__, error=str(error)[:250],
                child_signals=0, retired=(output / 'PARENT_EXITED.json').exists(), observed_unix=time.time()))
        raise
