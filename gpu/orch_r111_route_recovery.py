"""Versioned recovery of exited R109 route owners; original bytes stay intact."""

import argparse
from dataclasses import replace
import inspect
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace

from gpu import orch_r109_route_run as old
from gpu import orch_r109_route_broker as old_broker
from gpu import orch_r109_route_seed as seed
from gpu import orch_r111_route_sleep as pair


VERSION = 'recovery_r113_v1'
LANES = ('a100_1', 'a100_2', 'a100_3', 'a100_5', 'a100_6')


def directory(root, lane):
    return root/VERSION/('campaign_'+lane)


def prepare(root, lane):
    old.verify(root, lane)
    old.policy.require(lane in LANES, 'only_released_owned_a100_route')
    prior = root/('campaign_'+lane)
    launch = old.read(prior/'LAUNCH.json')
    old.policy.require(not Path('/proc', str(launch['pid'])).exists(), 'original_native_absent')
    old.policy.require(launch['uuid'] == old.policy.allocation(lane), 'original_uuid_join')
    failed = old.read(prior/'FAILED.json')
    old.policy.require(failed['error']['message'] == 'parent_timeout_no_replay', 'exact_recovery_failure')
    reservations = [json.loads(line) for line in (root/'RESERVATIONS.jsonl').read_text().splitlines()]
    first_cycle = max(row.get('cycle', 0) for row in reservations)+1
    checkpoints = sorted(prior.glob('CHECKPOINT_C*.json'), key=lambda path: int(path.stem.split('C')[-1]))
    checkpoint = old.read(checkpoints[-1]) if checkpoints else None
    counters = {key: failed[key] for key in ('native_completed', 'parent_completed', 'train_segments',
                'train_episodes', 'held_episodes', 'sleeps', 'optimizer_updates', 'triples', 'semantic_verified_changes')}
    document = checkpoint['adapter'] if checkpoint and checkpoint.get('adapter') else old.read(root/'SEED.json') if (root/'SEED.json').exists() else None
    if document:
        seed.validate(document)
    old_rows = []
    last_sleep_cycle = int(checkpoints[-1].stem.split('C')[-1]) if checkpoints else 0
    for path in sorted((prior/'native').glob('CALL_*.json')):
        call = old.read(path)
        if call.get('status') == 'COMPLETE' and call.get('cycle', 0) <= last_sleep_cycle and not call.get('purpose', '').startswith('held'):
            old_rows.append(old.native_engine.replay_row(call, path, old.sha(path)))
    output = directory(root, lane)
    output.mkdir(parents=True, exist_ok=False)
    (output/'parent_queue').mkdir()
    for name in ('READY.json', 'PUBLICATION.json'):
        old.write(output/name, old.read(prior/name))
    recipe = dict(first_cycle=first_cycle, counters=counters, own_memory=checkpoint['own_memory'] if checkpoint else '',
        document=document, old_rows=old_rows, prior_root=str(prior), original_pid=launch['pid'],
        uuid=launch['uuid'], prior_failed_sha256=old.sha(prior/'FAILED.json'),
        old_reservations_sha256=old.sha(root/'RESERVATIONS.jsonl'), old_reservation_count=len(reservations),
        original_partial_cycle_preserved_not_regenerated=True, anchor_lambda=.25,
        new_row_presentations=16, later_rehearsal_presentations=1,
        unchanged_deadline=old.read(prior/'READY.json')['hard_deadline_unix'],
        source_files={str(path): old.sha(path) for path in (Path(__file__).resolve(), Path(pair.__file__).resolve())})
    old.write(output/'RECOVERY.json', recipe)
    return dict(lane=lane, first_cycle=first_cycle, counters=counters, uuid=launch['uuid'],
                recovery_path=str(output), recovery_sha256=old.sha(output/'RECOVERY.json'),
                seed_binding_sha256=document['binding_sha256'] if document else None)


def verify(root, lane):
    old.verify(root, lane)
    document = old.read(directory(root, lane)/'RECOVERY.json')
    for path, expected in document['source_files'].items():
        old.policy.require(old.sha(path) == expected, 'recovery_source_binding')
    return document


def state(root, lane, counters, native_state):
    recovered = verify(root, lane)
    counters.update(recovered['counters'])
    counters['parent_missing'] = 0
    native_state.update(memory=recovered['own_memory'], old_rows=recovered['old_rows'])


def parent(root, lane, cycle, episode, segments, messages, response, stage, check, mode='BEHAVIOR', turn=0):
    output = directory(root, lane)
    principles = (root/'source'/old.policy.PRINCIPLES_PATH).read_text()
    payload = old.policy.parent_payload(lane, cycle, episode, segments, messages, response, stage, principles, mode, turn)
    old.policy.require(not old.policy.identifiers(payload).intersection(old.policy.identifiers(old.read(root/'COHORT.json')['held'])), 'held_blind')
    intent = old.reserve(root, lane, 'PARENT', dict(cycle=cycle, mode=mode, turn=turn))
    identity = f"GUIDED_SLEEP_C{cycle}_P{intent['number']}"
    path = output/'parent_queue'/(identity+'.request.json')
    old.write(path, dict(id=identity, payload=payload, payload_sha256=old.policy.digest(payload),
                         ready_sha256=old.sha(output/'READY.json')))
    response_path = path.with_name(identity+'.response.json')
    deadline = min(time.time()+180, old.read(output/'READY.json')['native_deadline_unix'])
    while time.time() < deadline and not response_path.exists():
        check('bounded_parent_wait')
        time.sleep(.25)
    receipt = dict(intent, status='MISSING', observed_unix=time.time(), request_sha256=old.sha(path),
                   no_retry=True, behavior_change=None, held_exposed=False)
    advice = ''
    if response_path.exists() and time.time() < deadline:
        try:
            result = old.read(response_path)
            old.policy.require(result['status']=='COMPLETE' and result['request_sha256']==old.sha(path)
                and result['principles_sha256']==old.policy.PRINCIPLES_SHA, 'actual_parent_response_join')
            archive = Path(result['archive']['remote_root'])
            old.policy.require(archive.is_relative_to(root/'parent_transcripts'/output.name), 'own_archive')
            for name, expected in result['archive']['files'].items():
                old.policy.require(not Path(name).is_absolute() and '..' not in Path(name).parts
                                   and old.sha(archive/name)==expected, 'archive_hash')
            plan = old.parse_parent(old.read(archive/'RAW_RESPONSE.json'), [payload['episodes'][0]['task_id']])
            old.policy.require(old.policy.validate_plan(plan)==result['plan']==old.read(archive/'PLAN.json'), 'actual_plan')
            advice = plan['guidance']+'\n'+plan['episode_guidance'][payload['episodes'][0]['task_id']]
            receipt.update(status='COMPLETE', response_sha256=old.sha(response_path), archive=result['archive'])
        except (ValueError, KeyError, OSError):
            receipt['reason'] = 'failed_or_invalid_parent_continue'
    old.write(output/f"PARENT_{intent['number']:05d}.json", receipt)
    return advice, receipt


def sleep(loaded, document, rows, old_rows, anchors, output, deadline, check, write, sha):
    output.mkdir(parents=True, exist_ok=False)
    flattened = [row for family in sorted(anchors) for row in anchors[family]]
    result = pair.train_sleep(loaded.engine, loaded.optimizer, rows, old_rows, flattened, output, check,
                              context_limit=old.policy.CONTEXT)
    engine = loaded.engine
    destination = output/'adapter'
    engine.model.save_pretrained(destination, safe_serialization=True, save_embedding_layers=False)
    parameters = {name: value for name, value in engine.model.named_parameters() if old.native_engine.native.is_lora(name)}
    identity = old.native_engine.native.bridge.AdapterIdentity(str(destination), old.native_engine.native.state_hash(parameters),
        seed.BASE_SHA, tuple((path.name, sha(path)) for path in sorted(destination.iterdir()) if path.is_file())).verify()
    carried = seed.save_carry(loaded, document, identity, output/'carry')
    loaded.binding = replace(loaded.binding, adapter=identity)
    loaded.observed = identity
    loaded.r108_seed_provenance['binding_sha256'] = carried['binding_sha256']
    result.update(optimizer_updates=result['updates'], inherited_step=document['optimizer_summary']['step'],
                  final_step=carried['optimizer_summary']['step'], no_optimizer_reset=True)
    write(output/'COMPLETE.json', result)
    return carried, result


def replace_once(source, before, after):
    old.policy.require(source.count(before) == 1, 'exact_recovery_transform:'+before)
    return source.replace(before, after, 1)


def native_function():
    source = inspect.getsource(old.native)
    source = replace_once(source, "campaign=root/('campaign_'+lane)", "campaign=recovery_directory(root,lane)")
    source = replace_once(source, '    def status(phase):', '    recovery_state(root,lane,counters,state)\n    def status(phase):')
    source = replace_once(source, "document=read(root/'SEED.json')", "document=recovery_verify(root,lane)['document']")
    source = replace_once(source, 'for cycle in range(1,policy.CYCLES+1):',
                           "for cycle in range(recovery_verify(root,lane)['first_cycle'],policy.CYCLES+1):")
    source = replace_once(source, "counters['parent_completed']+=1", "counters['parent_completed' if receipt['status']=='COMPLETE' else 'parent_missing']+=1")
    engine = SimpleNamespace(**vars(old.native_engine))
    engine.sleep = sleep
    namespace = dict(old.native.__globals__, parent=parent, verify=verify, native_engine=engine,
                     recovery_directory=directory, recovery_verify=verify, recovery_state=state)
    exec(compile(source, __file__+':native_clone', 'exec'), namespace)
    return namespace['native']


def guard(root, lane):
    source = inspect.getsource(old.guard)
    source = replace_once(source, "campaign=root/('campaign_'+lane)", "campaign=recovery_directory(root,lane)")
    source = replace_once(source, "'gpu.orch_r109_route_run'", "'gpu.orch_r111_route_recovery'")
    source = source.replace("root/'source'", "recovery_source")
    namespace = dict(old.guard.__globals__, verify=verify, recovery_directory=directory,
                     recovery_source=Path(__file__).resolve().parents[1])
    exec(compile(source, __file__+':guard_clone', 'exec'), namespace)
    return namespace['guard'](root, lane)


def broker(repository, root, lane, buffer, receipts):
    source = inspect.getsource(old_broker.serve)
    source = replace_once(source, "campaign = root/('campaign_'+lane)", "campaign = recovery_directory(root,lane)")
    source = source.replace('repository/policy.PRINCIPLES_PATH', 'frozen_repository/policy.PRINCIPLES_PATH')
    source = source.replace('repository/relative', 'frozen_repository/relative')
    namespace = dict(old_broker.serve.__globals__, recovery_directory=directory,
                     frozen_repository=Path(__file__).resolve().parents[1])
    exec(compile(source, __file__+':broker_clone', 'exec'), namespace)
    return namespace['serve'](repository, root, lane, buffer, receipts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'native', 'guard', 'broker'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--lane', choices=LANES, required=True)
    for name in ('repository', 'buffer', 'receipts'):
        parser.add_argument('--'+name, type=Path)
    arguments = parser.parse_args()
    if arguments.phase == 'broker':
        broker(arguments.repository, arguments.root, arguments.lane, arguments.buffer, arguments.receipts)
    elif arguments.phase == 'native':
        native_function()(arguments.root, arguments.lane)
    elif arguments.phase == 'guard':
        guard(arguments.root, arguments.lane)
    else:
        print(json.dumps(prepare(arguments.root, arguments.lane), sort_keys=True))
