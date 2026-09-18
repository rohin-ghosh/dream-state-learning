from gpu import orch_r108_guided_supervisor as supervisor


def test_train_held_disjoint_and_all_registry_hashes_excluded():
    registry = dict(excluded_ids=['older_TRAIN_000'], excluded_question_sha256=['a' * 64])
    cohort = supervisor.cohort(registry)
    tasks = [task for group in cohort['train'] + cohort['held'] for task in group]
    assert len(tasks) == 20
    assert len({task['id'] for task in tasks}) == 20
    assert len({task['question_sha256'] for task in tasks}) == 20
    assert {task['split'] for group in cohort['train'] for task in group} == {'TRAIN'}
    assert {task['split'] for group in cohort['held'] for task in group} == {'HELD'}
    enlarged = dict(excluded_ids=registry['excluded_ids'] + [task['id'] for task in tasks],
        excluded_question_sha256=registry['excluded_question_sha256'] + [task['question_sha256'] for task in tasks])
    fresh = supervisor.cohort(enlarged)
    new = [task for group in fresh['train'] + fresh['held'] for task in group]
    assert not {task['id'] for task in new} & {task['id'] for task in tasks}
    assert not {task['question_sha256'] for task in new} & {task['question_sha256'] for task in tasks}
