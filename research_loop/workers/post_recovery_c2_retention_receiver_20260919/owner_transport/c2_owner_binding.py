"""Read-only C2 delivery/rebind validation; no signal, dispatch or model imports."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from common import DEADLINE, IDENTITY, JOURNAL, ROOT, digest, file_bytes, literal, pinned, pins_match, process_identity, read, require, sha


def record(index, expected=None):
    require(type(index) is int and index >= 0, 'explicit_nonnegative_record_index')
    path = Path(ROOT) / 'stream/records' / f'{index:020d}.json'
    value = read(path)
    require(value['schema'] == 'R125_STREAM_JOURNAL_V1' and value['journal_id'] == JOURNAL
        and value['index'] == index and value['sha256'] == digest({key: item for key, item in value.items() if key != 'sha256'}),
        'authentic_original_record')
    require(expected is None or value['sha256'] == expected, 'exact_record_reference')
    intent = read(path.with_name(f'{index:020d}.intent.json'))
    require(intent == dict(schema=value['schema'], journal_id=JOURNAL, index=index,
        previous_sha256=value['previous_sha256'], record_sha256=value['sha256']), 'record_intent_integrity')
    return value


def native(expected, guard_path):
    actual = process_identity(expected['pid'])
    require(all(actual[key] == expected[key] for key in IDENTITY) and actual['uid'] == 2524
        and actual['state'] not in ('T', 't', 'Z', 'X')
        and actual['argv'][-3:] == ['native', '--config', guard_path], 'exact_actual_C2_native_not_launcher')
    return actual


def drain(plan, inventory):
    life = plan['old_life']
    require(life['journal_root'] == ROOT + '/stream' and life['journal_id'] == JOURNAL
        and life['hard_end_unix'] == DEADLINE and time.time() < DEADLINE, 'original_unexpired_C2_drain')
    actual = process_identity(life['pid'])
    require(all(actual[key] == life[key] for key in ('pid', 'uid', 'start_ticks', 'boot_id'))
        and actual['argv'] == life['command'] and actual['state'] not in ('T', 't', 'Z', 'X')
        and sha(life['guard_path']) == life['guard_sha256'], 'same_original_native_during_owner_drain')
    manifest = read(Path(ROOT) / 'stream/JOURNAL.json')
    require(manifest['journal_id'] == JOURNAL, 'same_original_journal')
    verified = []
    for item in inventory['publications']:
        consumption = item['consumption']
        observed = record(consumption['record_index'], consumption['record_sha256'])
        require(observed['kind'] == 'INBOX', 'actual_consumed_publication')
        document = observed['document']
        source = literal(document['source_id'])
        require(source.parent == Path(ROOT) / 'stream/inbox' and sha(source) == document['source_sha256']
            and read(source) == document['message'] and document['message']['id'] == item['publication']['id']
            and document['message']['actor'] == 'parent', 'same_original_published_parent_mailbox_bytes')
        verified.append(observed['sha256'])
    current = process_identity(life['pid'])
    require(all(current[key] == actual[key] for key in IDENTITY)
        and current['state'] not in ('T', 't', 'Z', 'X'), 'native_unchanged_during_drain_read')
    return dict(schema='C2_DRAIN_REMOTE_VERIFIED_V1', life_binding_sha256=digest(life),
        inventory_sha256=digest(inventory), consumed_publication_records=verified,
        native_signals=0, journal_writes=0, observed_unix=time.time())


def verify(binding_path, expected_sha256):
    binding = pinned(dict(path=binding_path, sha256=expected_sha256))
    require(binding['schema'] == 'C2_POST_LOADED_OWNER_BINDING_V1' and binding['deadline_unix'] == DEADLINE
        and time.time() < DEADLINE, 'explicit_unexpired_post_LOADED_C2_binding')
    token = pinned(binding['handoff'])
    require(token['schema'] == 'RETENTION_HANDOFF_TOKEN_V1'
        and token['sha256'] == digest({key: value for key, value in token.items() if key != 'sha256'})
        and token['old_native_exited'] is True and token['deadline_unix'] == DEADLINE
        and token['epoch_id'] == binding['source_epoch']
        and token['life_binding_sha256'] == binding['life_binding_sha256'], 'actual_exact_handoff_not_owner_permission')
    receiver = token['receiver']
    require(receiver['dispatcher_module'] == 'gpu.r188_node5_confinement'
        and receiver['same_journal_root'] == ROOT + '/stream', 'original_r188_and_journal_only')
    pins_match(receiver['artifact_pins'])
    guard = read(receiver['guard_path'])
    require(sha(guard['plan_path']) == guard['plan_sha256'], 'same_original_guard_plan')
    plan = read(guard['plan_path'])
    require(plan == receiver['plan'] and digest(plan) == receiver['plan_sha256']
        and plan['root'] == guard['copy_raw'] == ROOT and plan['hard_end_unix'] == DEADLINE
        and guard['source_pins'] == token['new_source_pins'] and guard['resume'] is True,
        'same_admitted_source_plan_root_wall')
    require(plan['physical'] == 1 and plan['gpu_uuid'] == 'GPU-7fc4e5b2-060c-ada8-8f91-3fe262c3573c'
        and plan['think_act_learn']['trial_id'] == 'C2_R216_current_conversation_maintenance'
        and token['new_source_pins']['gpu/r188_node5_confinement.py'] ==
            '75eed0e5e57cd7463e46fa10adeeebdb80b9ef1ce5e76a9b527c034d1e8e6481', 'original_learned_C2_r188')
    require('authorized_wall_extension' not in plan, 'no_old_wall_authorization_reapplied')
    actual_pins = {str(path.relative_to(plan['source_root'])): sha(path) for path in Path(plan['source_root']).rglob('*.py')}
    require(actual_pins == token['new_source_pins'], 'actual_exact_new_native_source')
    if plan.get('startup_context'):
        context = plan['startup_context']
        require(literal(context['path']).is_relative_to(Path(plan['source_root']))
            and sha(context['path']) == context['sha256'], 'same_pinned_startup_context_asset')
    actual = native(binding['native'], receiver['guard_path'])
    require(actual['cwd'] == plan['source_root'] and actual['pid'] != token['old_pid'], 'actual_successor_not_old_native')
    candidate = token['exact_complete']
    first = candidate['complete_index']
    last = binding['loaded']['index']
    require(type(last) is int and first < last <= first + 256, 'bounded_COMPLETE_to_LOADED_only')
    chain = []
    total = 0
    for index in range(first, last + 1):
        total += (Path(ROOT) / 'stream/records' / f'{index:020d}.json').stat().st_size
        require(total <= 512 * 1024**2, 'bounded_owner_binding_tail_bytes')
        item = record(index)
        if chain:
            require(item['previous_sha256'] == chain[-1]['sha256'], 'contiguous_complete_adoption_LOAD_chain')
        chain.append(item)
    require(chain[0]['kind'] == 'SLEEP_COMPLETE' and chain[0]['sha256'] == candidate['complete_sha256']
        and chain[0]['document']['resume_state'] == candidate['resume_state']
        and chain[0]['document']['checkpoint'] == candidate['checkpoint']
        and len(candidate['records']) >= 2 and chain[1]['kind'] == 'R184_LEARN_COMPLETE'
        and candidate['resume_state']['state']['deadline_unix'] == DEADLINE, 'actual_saved_COMPLETE_same_wall')
    for prior in candidate['records']:
        require(chain[prior['index'] - first] == prior, 'same_exact_COMPLETE_LEARN_candidate_bytes')
    adopted = [item for item in chain if item['kind'] == 'RETENTION_SOURCE_ADOPTED']
    require(len(adopted) == 1 and adopted[0]['document']['handoff_sha256'] == token['sha256']
        and adopted[0]['document']['source_pins_sha256'] == digest(token['new_source_pins'])
        and adopted[0]['document']['epoch_id'] == token['epoch_id']
        and adopted[0]['document']['deadline_unix'] == DEADLINE
        and adopted[0]['document']['wall_extended'] is False, 'durable_exact_source_adoption_before_LOAD')
    loaded = chain[-1]
    require(loaded['kind'] == 'LOADED' and loaded['sha256'] == binding['loaded']['sha256']
        and loaded['document']['pid'] == actual['pid'] and loaded['document']['resume'] is True
        and loaded['document']['optimizer_steps'] == candidate['checkpoint']['optimizer_steps']
        and adopted[0]['index'] < loaded['index'], 'actual_LOADED_not_dispatch_PID_or_frozen_state')
    require(all(item['kind'] in ('INBOX', 'R184_LEARN_COMPLETE', 'RETENTION_SOURCE_ADOPTED', 'LOADED')
        for item in chain[1:]), 'no_unresolved_work_or_wall_reapplication_before_LOAD')
    current = native(binding['native'], receiver['guard_path'])
    require(all(current[key] == actual[key] for key in IDENTITY), 'unchanged_successor_during_binding_read')
    return dict(schema='C2_ACTUAL_POST_LOADED_REBIND_VERIFIED_V1', binding_sha256=expected_sha256,
        native=actual, loaded= binding['loaded'], source_epoch=token['epoch_id'],
        life_binding_sha256=token['life_binding_sha256'], source_pins_sha256=digest(token['new_source_pins']),
        original_journal_root=ROOT + '/stream', deadline_unix=DEADLINE, native_signals=0, journal_writes=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding', required=True)
    parser.add_argument('--binding-sha256', required=True)
    arguments = parser.parse_args()
    print(json.dumps(verify(arguments.binding, arguments.binding_sha256), sort_keys=True))
