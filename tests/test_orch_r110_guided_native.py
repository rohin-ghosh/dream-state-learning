from gpu import orch_r110_guided_native as native
from organism_v6 import orch_r110_guided as policy


def test_two_sequential_episodes_then_parented_presleep_raw_tokens():
    tasks = [dict(id=f'R110_TRAIN_{index:03d}', split='TRAIN',
        question=f'What is {index} plus 5?', gold=str(index + 5)) for index in range(2)]
    events, saved = [], {}

    def generate(task, purpose, messages):
        events.append((task['id'], purpose))
        return dict(task_id=task['id'], path=f"{task['id']}_{purpose}.json", sha256='b' * 64,
            response=dict(raw='My own thought.\nFINAL: ' + task['gold'], token_ids=[9, 10],
                messages=messages, prompt_tokens=10, terminal=True, truncated=False, input_truncated=False))

    def parent(payload, task):
        policy.validate_parent_payload(payload)
        events.append((task['id'], 'parent_' + str(payload['episode'])))
        plan = dict(intervention_class='perception', guidance='Notice your allocation of effort.',
            rationale='Consider adding a different allocation behavior.')
        return dict(plan=plan, actual_model=policy.STRONG, transcript_receipt=dict(node_only=True,
            all_verified=True, payload_sha256=policy.digest(payload), plan_sha256=policy.digest(plan)))

    result = native.collect_cycle(tasks, 1, 'a' * 64, [], generate, parent, saved.__setitem__)
    expected = [(task['id'], purpose) for index, task in enumerate(tasks, 1)
        for purpose in ('experience', f'parent_{index}', 'check', 'revision')]
    expected += [(tasks[-1]['id'], purpose) for purpose in ('presleep_initial', 'parent_presleep', 'presleep')]
    assert events == expected
    assert len(result['rows']) == 8 and result['parent_calls'] == 3
    assert len(saved['TRIPLES.json']) == 3
    assert saved['ROWS.json'][-1]['kind'] == 'presleep'
    assert saved['ROWS.json'][-1]['source_generated_token_ids'] == [9, 10]
    assert saved['CARRY.json'][-1]['source_record_sha256'] == policy.digest(saved['presleep/RECORD.json'])
