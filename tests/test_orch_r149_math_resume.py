from copy import deepcopy
from pathlib import Path

import pytest

from gpu import orch_r149_math_resume as recovery


def documents():
    checkpoint = dict(path='adapter.json', path_sha256=recovery.CHECKPOINT_SHA,
                      optimizer_path='optimizer.pt', optimizer_path_sha256=recovery.OPTIMIZER_SHA)
    counters = dict(optimizer_steps=48021, native=2494, parent=232,
                    child_token_exposures=6989367, anchor_token_exposures=903890)
    return dict(terminal=dict(status='FAILED', error='prospective_cohort_extension_required_before_dispatch',
                              last_committed_checkpoint=deepcopy(checkpoint), counters=deepcopy(counters)),
                counters=counters, committed=dict(cycle=96, checkpoint=deepcopy(checkpoint)),
                complete=dict(cycle=96, next_cycle=97, checkpoint=deepcopy(checkpoint)),
                sleep=dict(cumulative_optimizer_steps=48021, checkpoint=deepcopy(checkpoint)), next_exists=False)


def test_exact_boundary_returns_independent_checkpoint():
    values = documents()
    result = recovery.boundary(**values)
    assert result == values['committed']['checkpoint']
    result['path'] = 'changed'
    assert values['committed']['checkpoint']['path'] == 'adapter.json'


@pytest.mark.parametrize('document,key,value', [
    ('terminal', 'status', 'COMPLETE'),
    ('terminal', 'error', 'CUDA out of memory'),
    ('committed', 'cycle', 95),
    ('complete', 'cycle', 95),
    ('complete', 'next_cycle', 96),
    ('sleep', 'cumulative_optimizer_steps', 0),
    ('counters', 'native', 2495),
    ('counters', 'parent', 233),
    ('counters', 'optimizer_steps', 48022),
    ('counters', 'child_token_exposures', 0),
])
def test_boundary_rejects_other_failure_or_unsaved_work(document, key, value):
    values = documents()
    values[document][key] = value
    with pytest.raises(ValueError):
        recovery.boundary(**values)


def test_boundary_rejects_next_cycle_even_when_empty():
    values = documents()
    values['next_exists'] = True
    with pytest.raises(ValueError, match='no_unsaved'):
        recovery.boundary(**values)


@pytest.mark.parametrize('key', ['path_sha256', 'optimizer_path_sha256'])
def test_boundary_rejects_wrong_checkpoint_even_if_agreement(key):
    values = documents()
    for document in ('committed', 'complete', 'sleep'):
        values[document]['checkpoint'][key] = '0'*64
    values['terminal']['last_committed_checkpoint'][key] = '0'*64
    with pytest.raises(ValueError, match='exact_C96_checkpoint_hashes'):
        recovery.boundary(**values)


def test_plan_preserves_all_but_frontier_carry_history_cohort():
    prior = dict(root='same', original_root='same_queue', source_root='same_source',
                 parent_models=['astra'], bounds={'wall': 1}, dev='private_dev_ref', final='private_final_ref',
                 seed=0, initial_history='old', initial_carry='old', train='old',
                 contract={'episodes_per_sleep': 2, 'anchor_loss_weight': .25, 'parent_wait_seconds': 0})
    saved = deepcopy(prior)
    values = documents()
    plan = recovery.continuation_plan(prior, values['committed']['checkpoint'], values['counters'],
                                      'history', 'carry', 'new_train')
    assert saved == prior
    for key in prior.keys()-{'initial_history', 'initial_carry', 'contract', 'train'}:
        assert plan[key] == prior[key]
    assert plan['contract']['next_cycle'] == 97
    assert plan['contract']['initial_optimizer_steps'] == 48021
    assert plan['contract']['inherited_counters'] == values['counters']
    for key in prior['contract']:
        assert plan['contract'][key] == prior['contract'][key]


@pytest.mark.parametrize('name', sorted(recovery.STARTUP))
def test_startup_receipts_are_new_not_overwrites(tmp_path, name):
    root, service = tmp_path, tmp_path/'runtime'
    observed = []
    emit = recovery.redirected_writer(lambda path, data: observed.append((path, data)), root, service)
    emit(root/name, {'status': 'new'})
    assert observed == [(service/name, {'status': 'new'})]


@pytest.mark.parametrize('name', ['cycle000097/ROWS.json', 'readouts/DEV_C000097/BINDING.json',
                                  'sealed/key/BINDING.json', 'COUNTERS.json'])
def test_nonstartup_artifacts_keep_original_life_namespace(tmp_path, name):
    observed = []
    emit = recovery.redirected_writer(lambda path, data: observed.append(path), tmp_path, tmp_path/'runtime')
    emit(tmp_path/name, {})
    assert observed == [tmp_path/name]


def test_parent_config_redirect_is_exact_not_global():
    observed = []
    old = Path('/queue/parent_claude/CONFIG.json')
    new = Path('/life/runtime/BROKER_CONFIG.json')
    reader = recovery.config_reader(lambda path: observed.append(path), old, new)
    reader(str(old))
    reader('/other/CONFIG.json')
    reader('/life/COUNTERS.json')
    assert observed == [new, '/other/CONFIG.json', '/life/COUNTERS.json']


def test_writes_never_replace_evidence(tmp_path):
    target = tmp_path/'receipt.json'
    recovery.write(target, {'old': True})
    before = target.read_bytes()
    with pytest.raises(FileExistsError):
        recovery.write(target, {'old': False})
    assert target.read_bytes() == before


def clearance():
    return dict(passed=True, complete_exclusion_coverage=True, exact_prefix=True,
                train_sha256='train', original_train_sha256='old', manifest_sha256='manifest',
                task_id_collisions=0, question_hash_collisions=0, checked_new_task_count=192,
                excluded_id_count=5846, excluded_question_hash_count=5838,
                exclusion_sources_sha256={name: 'digest' for name in
                    ('original_train', 'dev', 'final', 'inherited_registry')})


def test_clearance_requires_complete_actual_bound_coverage():
    recovery.collision_clearance(clearance(), 'train', 'old', 'manifest')


@pytest.mark.parametrize('key,value', [
    ('passed', False), ('complete_exclusion_coverage', False), ('exact_prefix', False),
    ('train_sha256', 'wrong'), ('original_train_sha256', 'wrong'), ('manifest_sha256', 'wrong'),
    ('task_id_collisions', 1), ('question_hash_collisions', 1), ('checked_new_task_count', 0),
    ('excluded_id_count', 0), ('excluded_question_hash_count', 0),
    ('exclusion_sources_sha256', {'original_train': 'digest'}),
])
def test_clearance_rejects_incomplete_or_different_candidate(key, value):
    receipt = clearance()
    receipt[key] = value
    with pytest.raises(ValueError):
        recovery.collision_clearance(receipt, 'train', 'old', 'manifest')
