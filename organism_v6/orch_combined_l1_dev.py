"""Prospective adaptive-DEV panels and bounded checkpoint diagnostics."""


PHASES = ('INTERMEDIATE', 'TERMINAL')
FAMILIES = ('math', 'route', 'legacy')
ROUTE_WORLDS = {'INTERMEDIATE': 16, 'TERMINAL': 4}
ORIGINAL_MATH_READOUT_CALLS = 224
DEFAULT_P64_CALLS = 128
TOTAL_READOUT_CAP = 1760
DEFAULT_MATH_SYSTEM = 'Solve the problem. Finish with a separate line FINAL: followed by just the numeric answer.'


def default_math_messages(task):
    return [dict(role='system', content=DEFAULT_MATH_SYSTEM), dict(role='user', content=task['question'])]


def call_cap(phase, family):
    assert phase in PHASES and family in FAMILIES
    return {'math': 64, 'route': ROUTE_WORLDS[phase] * 4 * 6, 'legacy': 48}[family]


def total_bound():
    return ORIGINAL_MATH_READOUT_CALLS + DEFAULT_P64_CALLS + sum(2 * call_cap(phase, family)
        for phase in PHASES for family in FAMILIES)


def first_boundary(new_rows):
    assert type(new_rows) is int and new_rows >= 2394
    return (new_rows + 12 + 1) // 2


def next_window(update, boundary, completed):
    assert update >= 0 and boundary > 0
    assert completed or update < boundary, 'missed_registered_dev_boundary'
    return update + 128 if completed else min(update + 128, boundary)


def jobs(phase):
    assert phase in PHASES
    return tuple((arm, family) for family in FAMILIES for arm in ('FULL', 'OFF'))


def validate_plan(plan):
    assert plan['schema'] == 'COMBINED_CONTINUAL_ADAPTIVE_DEV_V1'
    assert plan['claim'] == 'ADAPTIVE_DEV_NOT_CONFIRMATORY_H1'
    assert plan['parent_access'] is False and plan['training_ingestion'] is False
    assert plan['readout_total_cap'] == TOTAL_READOUT_CAP
    assert plan['reserved_all_calls'] == total_bound() == 1760
    assert plan['first_boundary_update'] == first_boundary(plan['registered_corpus_rows'])
    assert plan['route_condition'] == 'OWN_TEXT'
    assert plan['math_tokens'] == plan['route_tokens'] == 1536 and plan['other_tokens'] == 160
    assert plan['math_system'] == DEFAULT_MATH_SYSTEM
    assert plan['report_order'] == ['richness', 'accuracy']
    assert plan['temporary_devices'] == [2, 3, 6]
    assert plan['new_batches_during_registered_traversal'] == 'QUEUE_UNTIL_INTERMEDIATE_THEN_APPEND'
    assert plan['promote_automatically'] is False and plan['resume_after_readout_failure'] is True
    return plan
