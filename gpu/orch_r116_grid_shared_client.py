"""Next-source grid client for F1-owned consolidation; no optimizer or launcher."""

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import time

from gpu import orch_guided_native as native
from gpu import orch_r115_grid_native as grid
from gpu import orch_r116_shared_learner as shared


TRAIN_PHASES = frozenset(('episode', 'continuation', 'open_turn', 'presleep', 'reflection'))
require = shared.require


def prepare(shared_root, branch, *, config_sha256):
    require(branch in ('F4', 'A4'), 'grid_branch_only')
    with shared.locked(shared_root) as root:
        config, state = shared.read(root / 'CONFIG.json'), shared.read(root / 'STATE.json')
        require(state['config_sha256'] == shared.sha(root / 'CONFIG.json') == config_sha256,
                'shared_config_hash')
        checkpoint = shared.checked_checkpoint(state['checkpoint'])
        document = shared.read(checkpoint['path'])
        require(document['complete'] is True, 'complete_checkpoint_required')
        require(document['optimizer_rng_sha256'] == checkpoint['optimizer_path_sha256'],
                'same_owner_optimizer_provenance')
        identity = native.bridge.AdapterIdentity.from_document(document['adapter'])
        require(identity.base_sha256 == grid.policy.game.BASE_SHA, 'original_frozen_base')
        return dict(schema='R116_GRID_SHARED_COLLECTION_V1', shared_root=str(root.resolve()),
                    branch=branch, branch_root=str(Path(config['branches'][branch]['root']).resolve()),
                    generation=state['generation'], checkpoint_sha256=checkpoint['path_sha256'],
                    checkpoint=checkpoint, adapter=identity.document(),
                    config_sha256=state['config_sha256'],
                    predecessor_processes=[document['source_process']], optimizer_owner='F1')


def current(session):
    root = Path(session['shared_root'])
    state = shared.read(root / 'STATE.json')
    require(shared.sha(root / 'CONFIG.json') == session['config_sha256'] == state['config_sha256'],
            'shared_config_changed')
    require(state['generation'] == session['generation'] and
            state['checkpoint']['path_sha256'] == session['checkpoint_sha256'] and
            state['checkpoint'] == session['checkpoint'], 'shared_generation_changed')
    return state


class SharedDecoder:
    def __init__(self, loaded):
        require(loaded.optimizer is None, 'no_branch_optimizer')
        self.loaded = loaded
        self.no_adapter = False

    def __getattr__(self, name):
        return getattr(self.loaded.engine, name)

    def batch(self, messages, cap):
        require(self.loaded.optimizer is None and not any(parameter.requires_grad
                for parameter in self.model.parameters()), 'readonly_shared_actor')
        return grid.Decoder.batch(self, messages, cap)

    def verify_base(self):
        require(self.loaded.optimizer is None, 'no_branch_optimizer')
        return self.loaded.verify_unchanged()


def load_shared(session, *, model_dir, gpu_uuid, check, readout=False,
                predecessor_processes=()):
    current(session)
    checkpoint = shared.checked_checkpoint(session['checkpoint'])
    document = shared.read(checkpoint['path'])
    require(document['adapter'] == session['adapter'], 'checkpoint_adapter_binding')
    identity = native.bridge.AdapterIdentity.from_document(session['adapter'])
    require(identity.base_sha256 == grid.policy.game.BASE_SHA, 'original_frozen_base')
    binding = native.bridge.StageBinding(session['branch'], native.bridge.ARMS[0],
        session['generation'], 'sealed_readout' if readout else 'collection', identity,
        not readout, readout, session['config_sha256'])
    predecessors = predecessor_processes or tuple(tuple(item) for item in session['predecessor_processes'])
    loaded = native.load_stage(binding, model_dir=model_dir, device='cuda:0', gpu_uuid=gpu_uuid,
        context=native.StageContext(private_guidance=() if readout else ('R116_PRIVATE_PARENT',)),
        check=check, predecessor_processes=predecessors)
    current(session)
    require(loaded.optimizer is None, 'no_branch_optimizer')
    loaded.verify_unchanged()
    return SharedDecoder(loaded)


def call_binding(session):
    return {name: deepcopy(session[name]) for name in
            ('branch', 'generation', 'checkpoint_sha256', 'config_sha256', 'adapter')}


class SharedLife(grid.Life):
    def __init__(self, root, engine, config, cycle, session):
        require(Path(root).resolve() == Path(session['branch_root']), 'bound_branch_root')
        require(isinstance(engine, SharedDecoder) and engine.loaded.optimizer is None
                and engine.loaded.binding.adapter.document() == session['adapter'],
                'actually_loaded_shared_adapter_required')
        super().__init__(Path(root), engine, config, cycle)
        self.session = deepcopy(session)

    def calls(self, tasks, purpose, messages, cap, *, attached_readout=False):
        current(self.session)
        require(len(tasks) == len(messages) and tasks, 'one_prompt_per_task')
        training = not attached_readout and any(task['split'] == 'TRAIN' for task in tasks)
        if training:
            require(len(tasks) == 1 and purpose in TRAIN_PHASES, 'sequential_known_grid_train_phase')
            if time.time() >= grid.TRAIN_END:
                raise grid.TrainWindowClosed('reserve_morning_FINAL_after_completed_response')
        reservations = []
        for task, prompt in zip(tasks, messages):
            number = grid.reserve(self.root, 'NATIVE', dict(cycle=self.cycle, task_id=task['id'],
                split=task['split'], purpose=purpose, attached_readout=attached_readout))
            folder = 'sealed_readout_calls' if task['split'] == 'FINAL' else (
                'readout_calls' if attached_readout or task['split'] != 'TRAIN' else 'calls')
            path = self.root / folder / f'N{number:05d}.json'
            record = dict(status='STARTED', number=number, cycle=self.cycle, task_id=task['id'],
                split=task['split'], purpose=purpose, attached_readout=attached_readout,
                messages=deepcopy(prompt), cap=cap, base_sha256=grid.policy.game.BASE_SHA,
                adapter=deepcopy(self.session['adapter']), shared_child=call_binding(self.session),
                shared_generation=self.session['generation'],
                shared_checkpoint_sha256=self.session['checkpoint_sha256'],
                started_unix=time.time())
            grid.write(path, record)
            reservations.append((path, record))
        responses = self.engine.batch(messages, cap)
        require(len(responses) == len(reservations), 'exact_native_response_count')
        for (path, record), response in zip(reservations, responses):
            require('messages' not in response or response['messages'] == record['messages'],
                    'native_messages_mismatch')
            response['messages'] = deepcopy(record['messages'])
            record.update(status='COMPLETE', response=deepcopy(response), finished_unix=time.time())
            grid.write(path, record, replace=True)
            response['reference'] = grid.ref(path)
            if record['split'] == 'TRAIN' and not attached_readout:
                self.event('child', response['raw'], response['reference']['sha256'])
        current(self.session)
        return responses


def canonical_row(path, session, cycle, episode_ids):
    path = Path(path).resolve()
    require(path.parent == Path(session['branch_root']) / 'calls', 'only_native_train_directory')
    call = shared.read(path)
    require(call['status'] == 'COMPLETE' and call['cycle'] == cycle, 'complete_same_cycle_capture')
    require(call['split'] == 'TRAIN' and call['purpose'] in TRAIN_PHASES and
            not any(call.get(key) for key in ('attached_readout', 'attached_evaluation', 'evaluation_origin')),
            'train_only_no_readout_open')
    require(call['shared_child'] == call_binding(session) and call['adapter'] == session['adapter']
            and call['shared_generation'] == session['generation']
            and call['shared_checkpoint_sha256'] == session['checkpoint_sha256']
            and call['base_sha256'] == grid.policy.game.BASE_SHA, 'actual_shared_child_binding')
    require(call['task_id'] in episode_ids, 'outside_two_episode_cycle')
    response = call['response']
    require(response['messages'] == call['messages'] and response['messages'] and
            all(set(message) == {'role', 'content'} and message['role'] in ('system', 'user', 'assistant')
                and isinstance(message['content'], str) for message in response['messages']) and
            response['messages'][-1]['role'] == 'user', 'actual_causal_messages_required')
    require(type(response['terminal']) is bool and type(response['truncated']) is bool and
            not (response['terminal'] and response['truncated']), 'native_completion_flags')
    require(type(response['prompt_tokens']) is int and response['prompt_tokens'] > 0 and
            isinstance(response['raw'], str) and response['token_ids'] and
            all(type(token) is int and token >= 0 for token in response['token_ids']), 'native_token_evidence')
    row = dict(replay_mode=shared.replay.MODE, student_prefix=deepcopy(response['messages']),
        source_prompt_sha256=shared.replay.history_policy.digest(response['messages']),
        source_prompt_tokens=response['prompt_tokens'], target=response['raw'],
        target_sha256=shared.replay.history_policy.text_sha(response['raw']),
        source_generated_token_ids=list(response['token_ids']), append_eos=response['terminal'],
        continuation_only=not response['terminal'], source_call_path=str(path),
        source_call_sha256=shared.sha(path), episode_id=call['task_id'],
        source_outcome_is_metadata_only=True, observed_fact_endorsement=False)
    shared.replay.verify_source(row, call)
    return row


def export_cycle(session, cycle):
    current(session)
    root = Path(session['branch_root'])
    complete_path = root / 'cycles' / f'{cycle:04d}' / 'TRAIN_COMPLETE.json'
    complete = shared.read(complete_path)
    episode_ids = [outcome['task_id'] for outcome in complete['outcomes']]
    require(len(episode_ids) == 2 and len(set(episode_ids)) == 2 and
            all(outcome['split'] == 'TRAIN' for outcome in complete['outcomes']), 'exact_two_completed_episodes')
    ledger = [json.loads(line) for line in (root / 'LEDGER.jsonl').read_text().splitlines() if line.strip()]
    selected = [entry for entry in ledger if entry['kind'] == 'NATIVE' and entry['cycle'] == cycle
                and entry['split'] == 'TRAIN' and not entry.get('attached_readout')]
    numbers = [entry['number'] for entry in selected]
    require(numbers and len(numbers) == len(set(numbers)), 'unique_reserved_native_calls')
    paths = [root / 'calls' / f'N{number:05d}.json' for number in numbers]
    captured = [path for path in (root / 'calls').glob('N*.json') if shared.read(path)['cycle'] == cycle]
    require(set(paths) == set(captured), 'all_cycle_captures_accounted')
    rows = [canonical_row(path, session, cycle, episode_ids) for path in paths]
    calls = [shared.read(path) for path in paths]
    for entry, call in zip(selected, calls):
        require(all(entry[name] == call[name] for name in
                    ('number', 'cycle', 'task_id', 'split', 'purpose', 'attached_readout')), 'ledger_capture_binding')
    require({call['task_id'] for call in calls if call['purpose'] == 'episode'} == set(episode_ids),
            'both_actual_episode_streams_required')
    require(sum(call['purpose'] == 'reflection' for call in calls) == 1 and
            any(call['purpose'] == 'presleep' for call in calls) and calls[-1]['purpose'] == 'reflection',
            'complete_presleep_reflection_required')
    require(complete['reflection'] == grid.ref(paths[-1]), 'completed_reflection_source_binding')
    missing = {call['purpose'] for call in calls} - shared.PHASES
    require(not missing, 'coordinator_phase_alias_required:' + ','.join(sorted(missing)))
    packet = dict(schema='R116_GRID_SHARED_PACKET_V1', session=call_binding(session), cycle=cycle,
        episode_ids=episode_ids, rows=rows, completion=grid.ref(complete_path),
        actual_presentations=0, child_source_tokens=sum(len(row['source_generated_token_ids']) for row in rows))
    packet_path = root / 'shared_cycles' / f'{cycle:04d}' / 'PACKET.json'
    if packet_path.exists():
        require(shared.read(packet_path) == packet, 'immutable_cycle_packet')
    else:
        shared.write(packet_path, packet)
    receipt = shared.submit(session['shared_root'], session['branch'], session['generation'],
                            session['checkpoint_sha256'], episode_ids, rows)
    return dict(packet=grid.ref(packet_path), submission=receipt, optimizer_owner='F1',
                branch_optimizer_steps=0, status='SUBMITTED_WAITING_SHARED_GENERATION')


def run_cycle_and_submit(life, tasks, memory):
    require(isinstance(life, SharedLife) and len(tasks) == 2 and
            len({task['id'] for task in tasks}) == 2 and
            all(task['split'] == 'TRAIN' for task in tasks), 'two_sequential_train_episodes')
    current(life.session)
    arrived = Path(life.session['shared_root']) / f"generation_{life.session['generation']:06d}" / (life.session['branch'] + '.json')
    require(not arrived.exists(), 'already_at_shared_barrier')
    shared.write(life.root / 'shared_cycles' / f'{life.cycle:04d}' / 'COLLECTION.json', life.session)
    grid.train_cycle(life, tasks, memory)
    life.engine.verify_base()
    return export_cycle(life.session, life.cycle)


def wait_for_next(session, *, deadline, check, poll_seconds=2):
    require(poll_seconds > 0 and deadline <= grid.END, 'bounded_shared_barrier')
    root = Path(session['shared_root'])
    receipt = root / f"generation_{session['generation']:06d}" / (session['branch'] + '.json')
    require(receipt.exists(), 'submit_before_wait')
    while time.time() < deadline:
        check('shared_checkpoint_barrier')
        state = shared.read(root / 'STATE.json')
        if state['generation'] != session['generation']:
            require(state['generation'] == session['generation'] + 1, 'no_skipped_shared_generation')
            complete = shared.read(root / f"generation_{session['generation']:06d}" / 'sleep' / 'COMPLETE.json')
            require(complete['state'] == state, 'completed_shared_sleep_state_binding')
            return prepare(root, session['branch'], config_sha256=session['config_sha256'])
        current(session)
        time.sleep(min(poll_seconds, max(0, deadline - time.time())))
    return dict(status='DEADLINE_WAITING_SHARED_CHECKPOINT', generation=session['generation'],
                optimizer_steps=0, no_branch_fallback_update=True)


def reload_shared(decoder, session, next_session):
    from gpu.orch_r111_route_shared import reload_adapter

    require(isinstance(decoder, SharedDecoder) and decoder.loaded.optimizer is None, 'no_branch_optimizer')
    require(all(session[name] == next_session[name] for name in
                ('branch', 'branch_root', 'shared_root', 'config_sha256')) and
            next_session['generation'] == session['generation'] + 1, 'same_branch_exact_next_generation')
    require(decoder.loaded.binding.adapter.document() == session['adapter'], 'loaded_previous_shared_child')
    current(next_session)
    complete = shared.read(Path(session['shared_root']) /
        f"generation_{session['generation']:06d}" / 'sleep' / 'COMPLETE.json')
    require(complete['state'] == current(next_session), 'completed_shared_sleep_state_binding')
    decoder.verify_base()
    document = reload_adapter(decoder.loaded.engine, next_session['checkpoint'])
    require(document['adapter'] == next_session['adapter'], 'reloaded_published_adapter')
    identity = native.bridge.AdapterIdentity.from_document(next_session['adapter'])
    decoder.loaded.binding = replace(decoder.loaded.binding, adapter=identity, cycle=next_session['generation'])
    decoder.loaded.observed = native.observe_adapter(decoder.loaded.engine, identity)
    decoder.verify_base()
    return dict(generation=next_session['generation'], checkpoint_sha256=next_session['checkpoint_sha256'],
                optimizer_owner='F1', local_optimizer_steps=0, resident_reload=True)
