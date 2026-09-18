"""R108 sequential collection and masked replay seams, with injectable native IO."""

from copy import deepcopy
from dataclasses import asdict
import time

from gpu import orch_guided_native as native
from organism_v6 import orch_math_feedback_uptake as history
from organism_v6 import orch_r107_parented_replay as replay
from organism_v6 import orch_r108_guided as policy


def collect_cycle(tasks, cycle, adapter_sha256, previous, generate, parent, save):
    policy.require(type(cycle) is int and 1 <= cycle <= policy.CYCLES, 'cycle_bound')
    policy.require(len(tasks) == policy.EPISODES and len({task['id'] for task in tasks}) == policy.EPISODES,
        'two_distinct_sequential_episodes')
    rows, triples = [], []
    memory = deepcopy(list(previous))[-policy.EPISODES:]
    for episode, task in enumerate(tasks, 1):
        records = []
        source_calls = []
        original_messages = policy.messages(task, 'experience', previous=memory)
        original = generate(task, 'experience', original_messages)
        source_calls.append(original)
        records.append(history.record(task, 'experience', original['response']))
        payload = policy.parent_payload(task, records[0], adapter_sha256, cycle, episode, memory)
        result = parent(payload, task)
        policy.validate_plan(result['plan'], [task])
        receipt = result['transcript_receipt']
        policy.require(result['actual_model'] == policy.STRONG and receipt['node_only'] is True
            and receipt['all_verified'] is True, 'verified_strong_parent_required')
        policy.require(receipt['payload_sha256'] == policy.digest(payload)
            and receipt['plan_sha256'] == policy.digest(result['plan']), 'actual_parent_join')
        for purpose in ('check', 'revision'):
            messages = policy.messages(task, purpose, records, result['plan'], memory)
            call = generate(task, purpose, messages)
            source_calls.append(call)
            records.append(history.record(task, purpose, call['response']))
        episode_rows = policy.replay_rows(task, records, result['plan'])
        for row, call in zip(episode_rows, source_calls):
            policy.require(call['task_id'] == task['id'], 'source_task_join')
            replay.verify_source(row, call)
            row.update(source_call_path=call['path'], source_call_sha256=call['sha256'])
        triple = policy.intervention_triple(task, records, result['plan'], adapter_sha256, receipt)
        save(f'episode{episode}/RECORDS.json', records)
        save(f'episode{episode}/TRIPLE.json', triple)
        rows.extend(episode_rows)
        triples.append(triple)
        memory.append(dict(task_id=task['id'], trace=records[-1]['response']['raw'],
            source_record_sha256=policy.digest(records[-1])))
        memory = memory[-policy.EPISODES:]
        save('ROWS_PARTIAL.json', rows)
    save('ROWS.json', rows)
    save('CARRY.json', memory)
    save('TRIPLES.json', triples)
    return dict(rows=rows, memory=memory, triples=triples, sequential_episodes=2,
        native_experience_calls=6, parent_calls=2)


def validate_anchor_inventory(anchors):
    families = {'code', 'math', 'simulated_tools', 'concise_answer'}
    policy.require(set(anchors) == families and all(anchors[family] for family in families),
        'competent_base_anchor_each_family_required')
    for family, records in anchors.items():
        for record in records:
            policy.require(record['family'] == family and record['source_condition'] == 'PURE_BASE'
                and record['split'] == 'TRAIN' and record['verified_competent'] is True,
                'base_train_competent_anchor_only')
            policy.require(record['source_call_sha256'] and record['encoded'] is not None,
                'bound_encoded_anchor')


def replay_batch(rows, encoded, old_l1, old_l2, anchors, step):
    policy.require(len(rows) == len(encoded) and rows and old_l1, 'new_and_old_l1_required')
    validate_anchor_inventory(anchors)
    policy.require(type(step) is int and step >= 0, 'schedule_step')
    position = step % len(rows)
    selected = [('NEW:' + rows[position]['source_record_sha256'], encoded[position])]
    selected.append(('L1_REHEARSAL', old_l1[step % len(old_l1)]))
    if old_l2:
        selected.append(('L2_REHEARSAL', old_l2[step % len(old_l2)]))
    for family in sorted(anchors):
        anchor = anchors[family][step % len(anchors[family])]
        selected.append(('BASE_ANCHOR:' + family, anchor['encoded']))
    return selected


def train_batch(engine, optimizer, batch, check):
    parameters = {name: parameter for name, parameter in engine.model.named_parameters() if native.is_lora(name)}
    policy.require(parameters and all(parameter.requires_grad for parameter in parameters.values()),
        'existing_lora_trainable')
    policy.require(not any(parameter.requires_grad for name, parameter in engine.model.named_parameters()
        if not native.is_lora(name)), 'base_frozen')
    engine.model.train()
    optimizer.zero_grad(set_to_none=True)
    losses = []
    rehearsal_count = sum(label.endswith('REHEARSAL') for label, unused in batch)
    policy.require(rehearsal_count in (1, 2), 'one_or_two_rehearsal_sources')
    for label, encoded in batch:
        check('gradient_accumulation')
        inputs = engine.torch.tensor([encoded.input_ids], dtype=engine.torch.long, device=engine.device)
        targets = engine.torch.tensor([encoded.labels], dtype=engine.torch.long, device=engine.device)
        with engine.torch.autocast(device_type='cuda', dtype=engine.torch.bfloat16):
            loss = engine.model(input_ids=inputs, labels=targets,
                attention_mask=engine.torch.ones_like(inputs), use_cache=False).loss
        policy.require(bool(engine.torch.isfinite(loss)), 'finite_loss')
        weight = 0.7 if label.startswith('NEW:') else (
            0.025 if label.startswith('BASE_ANCHOR:') else 0.2 / rehearsal_count)
        (loss * weight).backward()
        losses.append(dict(label=label, loss=loss.item(), objective_weight=weight))
    policy.require(all(parameter.grad is not None and bool(engine.torch.isfinite(parameter.grad).all())
        for parameter in parameters.values()), 'finite_lora_gradients')
    optimizer.step()
    return losses


def sleep_cycle(engine, optimizer, rows, old_l1, old_l2, anchors, deadline, check, save, clock=time.time):
    encoded = [replay.encode_row(row, engine.tokenizer, policy.CONTEXT) for row in rows]
    validate_anchor_inventory(anchors)
    for index, value in enumerate(encoded):
        save(f'MASK_{index:02d}.json', asdict(value))
    started = clock()
    policy.require(deadline > started, 'positive_sleep_time')
    presentations = {row['source_record_sha256']: 0 for row in rows}
    step = 0
    while clock() < deadline:
        batch = replay_batch(rows, encoded, old_l1, old_l2, anchors, step)
        losses = train_batch(engine, optimizer, batch, check)
        presentations[rows[step % len(rows)]['source_record_sha256']] += 1
        step += 1
        save(f'UPDATES/{step:06d}.json', dict(update=step, losses=losses, finished_unix=clock()))
    result = dict(started_unix=started, finished_unix=clock(), optimizer_updates=step,
        presentations=presentations, every_own_row_presented=all(presentations.values()),
        base_anchor_families_per_update=4, old_l1_rows_per_update=1,
        old_l2_rows_per_update=int(bool(old_l2)), gradient_accumulation=True,
        objective='weighted_SFT_not_unlikelihood',
        objective_weights=dict(new_own=0.7, old_rehearsal=0.2, broad_base_anchors=0.1),
        deadline_is_not_an_epoch_target=True)
    save('SLEEP.json', result)
    policy.require(result['every_own_row_presented'], 'sleep_window_incomplete_preserve_partial_no_promotion')
    return result
