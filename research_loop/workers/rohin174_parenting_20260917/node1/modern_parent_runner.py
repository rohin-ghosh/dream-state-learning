"""Owner-admitted patched R166 tick/prompt/parser with exact legacy custody."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())


def load(spec):
    for path, expected in spec['pins'].items():
        require(sha(path) == expected, 'receiving_source_pin:' + path)
    sys.path.insert(0, spec['bundle'])
    from gpu import orch_r166_parent_policy as policy
    from gpu import orch_route_parent_campaign_providers as provider
    from gpu import orch_r175_parent_arms as arms
    for module, relative in ((policy, arms.POLICY_PATH), (provider, arms.PROVIDER_PATH),
                             (policy.parent, arms.PARENT_PATH)):
        require(Path(module.__file__).resolve() == Path(spec['bundle']) / relative, 'actual_patched_bundle_import')
    config = json.loads(Path(spec['config']).read_text())
    seed = json.loads(Path(spec['seed']).read_text())
    policy.validate(config)
    require(config['root'] == spec['root'] and config['r175_arm'] == spec['arm'], 'exact_assigned_life')
    return policy, provider, arms, config, seed


def poll(policy, spec, reference, bootstrap=False):
    script = ('import json,time; from gpu.orch_r166_parent_snapshot import stored_poll; '
              'root=' + repr(spec['root']) + '; store=' + repr(spec['cursor_store']) + '; '
              'reference=' + repr(reference) + '; used=0; started=time.monotonic()\n'
              'for ordinal in range(' + ('128' if bootstrap else '1') + '):\n'
              ' result=stored_poll(root,store,reference); reference=result["reference"]; '
              'used+=result["snapshot"]["source_bytes"]\n'
              ' if result["snapshot"]["caught_up"] or used >= 1879048192 or time.monotonic()-started>100: break\n'
              'result["read_bytes_this_call"]=used; print(json.dumps(result))')
    config = json.loads(Path(spec['config']).read_text())
    return policy.parent.remote(spec['repository'], config, script)


def pending_legacy(legacy, state):
    missing = []
    for entry in legacy:
        publication = entry['publication']
        delivered = state['delivered'].get(publication['id'])
        if delivered is None:
            missing.append(publication['id'])
            continue
        require(delivered['speaker'] == 'Astra' and delivered['inbox_sha256'] == publication['sha256']
                and delivered['text_sha256'] == entry['message_sha256'], 'actual_legacy_request_exposure')
    return missing


def record_milestones(policy, spec, state, directory):
    first = None
    for attempt in policy.local_attempts(spec['output']):
        result = attempt['result']
        if result['status'] != 'PUBLISHED':
            continue
        publication = result['publication']
        published_path = directory / ('PUBLISHED_' + publication['id'] + '.json')
        if not published_path.exists():
            write(published_path, dict(arm=spec['arm'], publication=publication,
                  message_sha256=hashlib.sha256(result['message'].encode()).hexdigest(),
                  word_count=len(result['message'].split()), source_request_count=attempt['source']['request_count'],
                  observed_unix=time.time(), policy_sha256=spec['policy_sha256'],
                  assignment_sha256=spec['assignment_sha256'], request_exposure_verified=False))
        delivered = state['delivered'].get(publication['id'])
        if delivered is None:
            continue
        require(delivered['speaker'] == 'Astra' and delivered['inbox_sha256'] == publication['sha256']
                and delivered['text_sha256'] == hashlib.sha256(result['message'].encode()).hexdigest(),
                'exact_new_arm_request_exposure')
        if first is None:
            first = delivered
        path = directory / ('EXPOSED_' + publication['id'] + '.json')
        if not path.exists():
            write(path, dict(arm=spec['arm'], publication=publication, delivered=delivered,
                  observed_unix=time.time(), first_arm_sleep_count=first['sleep_count'],
                  third_completed_sleep_count=first['sleep_count'] + 3,
                  fourth_completed_sleep_count=first['sleep_count'] + 4,
                  evaluation_status='UNKNOWN_NOT_YET_REVIEWED', request_exposure_verified=True))
    return first


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--preflight', action='store_true')
    arguments = parser.parse_args()
    spec = json.loads(arguments.spec.read_text())
    policy, provider, arms, config, seed = load(spec)
    if arguments.preflight:
        selected = arms.specification(spec['arm'])
        status = policy.tick(spec['repository'], config, spec['output'], seed,
                             dict(caught_up=False, source_bytes=0))
        require(status['status'] == 'VERIFIED_BOOTSTRAP_IN_PROGRESS', 'actual_patched_tick_invoked')
        bad = dict(config, cadence_responses=config['cadence_responses'] + 1)
        try:
            policy.tick(spec['repository'], bad, spec['output'], seed, dict(caught_up=False, source_bytes=0))
        except ValueError:
            pass
        else:
            raise ValueError('patched_tick_config_binding_not_active')
        state = json.loads(Path(spec['snapshot']).read_text())['snapshot']
        memory = policy.memory(seed, [], state)
        instruction, unused = policy.prompt(config, state, memory)
        require('ROHIN175_OBSERVATION_TO_ACTION_BASELINE_V1' in instruction, 'patched_prompt_baseline')
        response = dict(speak=True, message=' '.join(['word'] * selected['words']), rationale='fixture')
        provider.response_schema(json.dumps(response))
        for message in (' '.join(['word'] * (selected['words'] + 1)), 'x' * 4097):
            response['message'] = message
            try:
                provider.response_schema(json.dumps(response))
            except ValueError:
                pass
            else:
                raise ValueError('patched_parser_cap_not_active')
        print(json.dumps(dict(status='PASS', execution_kind='CPU_ONLY', actual_patched_tick=True,
              actual_patched_prompt=True, actual_patched_parser=True, word_cap=selected['words'],
              cadence=selected['cadence'], provider_calls=0, signals=0)))
        return
    directory = arguments.spec.parent
    require(sha(spec['admission']) == spec['admission_sha256'], 'own_cpu_and_main_authority_admission')
    admission = json.loads(Path(spec['admission']).read_text())
    require(admission['predecessor_terminal'] and admission['pending_reconciled'], 'preserved_parent_custody')
    reference = json.loads(Path(spec['snapshot']).read_text())['reference']
    with policy.community.parent_lock(spec['output']):
        write(directory / 'STARTED.json', dict(pid=os.getpid(), observed_unix=time.time(),
              spec_sha256=sha(arguments.spec), arm=spec['arm'], root=spec['root'],
              actual_entrypoint='gpu.orch_r166_parent_policy.tick', policy_sha256=spec['policy_sha256']))
        for sequence in range(100000):
            if time.time() >= config['hard_end_unix']:
                break
            observed = poll(policy, spec, reference)
            reference = observed['reference']
            write(directory / ('POLL_' + str(sequence).zfill(8) + '.json'), observed)
            state = observed['snapshot']
            if not state['caught_up']:
                continue
            first = record_milestones(policy, spec, state, directory)
            missing = pending_legacy(spec['legacy_publications'], state)
            if first is not None and state['sleep_count'] >= first['sleep_count'] + 3:
                path = directory / 'WITHDRAWAL_STARTED.json'
                if not path.exists():
                    write(path, dict(observed_unix=time.time(), first_exposure=first,
                          completed_sleep_count=state['sleep_count'], parent_and_peer_new_turns_stopped=True,
                          check_status='UNKNOWN_REQUIRES_REVIEW', old_invitations_may_remain_visible=True))
                if state['sleep_count'] >= first['sleep_count'] + 4:
                    write(directory / 'WITHDRAWAL_SLEEP_COMPLETE.json', dict(observed_unix=time.time(),
                          completed_sleep_count=state['sleep_count'], no_clean_context_claim=True))
                    break
                status = dict(status='ONE_SLEEP_PARENT_PEER_WITHDRAWAL')
            elif missing:
                status = dict(status='AWAITING_LEGACY_REQUEST_EXPOSURE', pending_publication_ids=missing)
            else:
                started = time.time()
                status = policy.tick(spec['repository'], config, spec['output'], seed, state)
                status.update(tick_started_unix=started, tick_finished_unix=time.time())
                record_milestones(policy, spec, state, directory)
            write(directory / ('STATUS_' + str(sequence).zfill(8) + '.json'), status)
            time.sleep(10)


if __name__ == '__main__':
    main()
