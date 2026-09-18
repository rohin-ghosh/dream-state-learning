from copy import deepcopy

import pytest

from gpu import orch_r108_guided_native as native
from organism_v6 import orch_r108_guided as policy


TASKS = [dict(id=f'R108_TRAIN_{index:03d}', split='TRAIN', question=f'What is {index} plus 5?',
    gold=str(index + 5)) for index in range(2)]


def test_sequential_cycle_records_actual_parent_and_previous_episode():
    events, saved = [], {}
    def generate(task, purpose, messages):
        events.append((task['id'], purpose))
        if task == TASKS[1] and purpose == 'experience':
            assert 'YOUR EARLIER TRAIN REFLECTIONS' in messages[0]['content']
        return dict(task_id=task['id'], path=f"{task['id']}_{purpose}.json", sha256='b' * 64,
            response=dict(raw='My own thought.\nFINAL: ' + task['gold'], token_ids=[9, 10],
                messages=messages, prompt_tokens=10, terminal=True, truncated=False, input_truncated=False))
    def parent(payload, task):
        events.append((task['id'], 'parent'))
        plan = dict(intervention_class='perception', guidance='What did you miss?', rationale='Notice relevant evidence.')
        return dict(plan=plan, actual_model=policy.STRONG, transcript_receipt=dict(node_only=True,
            all_verified=True, payload_sha256=policy.digest(payload), plan_sha256=policy.digest(plan)))
    result = native.collect_cycle(TASKS, 1, 'a' * 64, [], generate, parent, saved.__setitem__)
    assert events == [(task['id'], purpose) for task in TASKS
        for purpose in ('experience', 'parent', 'check', 'revision')]
    assert len(result['rows']) == 6 and result['parent_calls'] == 2
    assert len(saved['TRIPLES.json']) == 2 and saved['CARRY.json'][-1]['task_id'] == TASKS[1]['id']


def anchors():
    return {family: [dict(family=family, source_condition='PURE_BASE', split='TRAIN',
        verified_competent=True, source_call_sha256='c' * 64, encoded=family)]
        for family in ('code', 'math', 'simulated_tools', 'concise_answer')}


def test_every_accumulated_batch_has_all_anchors_and_rehearsal():
    rows = [dict(source_record_sha256='d' * 64)]
    selected = native.replay_batch(rows, ['new'], ['old1'], ['old2'], anchors(), 4)
    assert len(selected) == 7
    assert selected[:3] == [('NEW:' + 'd' * 64, 'new'), ('L1_REHEARSAL', 'old1'), ('L2_REHEARSAL', 'old2')]
    assert {label for label, _ in selected[3:]} == {'BASE_ANCHOR:' + name for name in anchors()}


@pytest.mark.parametrize('field,value', [('source_condition', 'LORA_ON'), ('split', 'HELD'),
    ('verified_competent', False)])
def test_inappropriate_anchor_rejected(field, value):
    changed = deepcopy(anchors())
    changed['code'][0][field] = value
    with pytest.raises(ValueError, match='base_train_competent_anchor_only'):
        native.validate_anchor_inventory(changed)


def test_no_missing_anchor_or_old_l1_rehearsal():
    changed = anchors()
    changed.pop('code')
    with pytest.raises(ValueError, match='competent_base_anchor_each_family_required'):
        native.validate_anchor_inventory(changed)
    with pytest.raises(ValueError, match='new_and_old_l1_required'):
        native.replay_batch([{}], [None], [], [], anchors(), 0)
