"""CPU-only synthetic TRAIN fixtures; never construct or read held tasks."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from gpu import orch_r149_math_cohort as cohort


@pytest.fixture
def training():
    groups, identifiers, questions = [], set(), set()
    for cycle in range(1, 97):
        group = []
        for episode in range(2):
            for nonce in range(10000):
                task = cohort.recipe.source.make_task('R111_F2_TRAIN', cycle, episode + nonce * 1001)
                task['split'] = 'TRAIN'
                if task['id'] not in identifiers and task['question_sha256'] not in questions:
                    identifiers.add(task['id'])
                    questions.add(task['question_sha256'])
                    group.append(task)
                    break
            else:
                raise AssertionError('synthetic_train_fixture_exhausted')
        groups.append(group)
    return groups


def test_default_extension_exact_prefix_schema_determinism_and_disjointness(training):
    original = deepcopy(training)
    extended = cohort.extend_train(training)
    assert training == original == extended[:96]
    assert len(extended) == 192
    assert all(len(group) == 2 for group in extended)
    assert extended == cohort.extend_train(training)
    identifiers, questions = cohort.validate_train(extended)
    assert len(identifiers) == len(questions) == 384
    assert {task['split'] for group in extended for task in group} == {'TRAIN'}
    assert extended[96][0] == cohort.make_train_task(97, 0)
    assert extended[96][1] == cohort.make_train_task(97, 1)
    assert [task['family'] for task in extended[96]] == ['affine_balance', 'inventory_balance']
    extended[0][0]['gold'] = 'changed copy only'
    assert training == original


def test_incremental_continuation_matches_single_extension(training):
    partial = cohort.extend_train(training, additional_cycles=17)
    assert cohort.extend_train(partial, additional_cycles=79) == cohort.extend_train(training)


@pytest.mark.parametrize('field,keyword', [('id', 'excluded_ids'),
    ('question_sha256', 'excluded_question_sha256')])
def test_opaque_exclusions_use_original_retry_recipe(training, field, keyword):
    candidate = cohort.make_train_task(97, 0)
    exclusions = {candidate[field]}
    extended = cohort.extend_train(training, additional_cycles=1, **{keyword: exclusions})
    assert extended[:96] == training
    assert extended[96][0] == cohort.make_train_task(97, 1001)
    assert not exclusions.intersection(task[field] for task in extended[96])
    assert exclusions == {candidate[field]}


def test_old_train_question_collision_is_skipped(training, monkeypatch):
    original = cohort.make_train_task

    def collide(cycle, position):
        task = original(cycle, position)
        if cycle == 97 and position == 0:
            task['question_sha256'] = training[0][0]['question_sha256']
        return task

    monkeypatch.setattr(cohort, 'make_train_task', collide)
    assert cohort.extend_train(training, additional_cycles=1)[96][0] == original(97, 1001)


def test_exhaustion_fails_without_mutation(training, monkeypatch):
    original = deepcopy(training)
    candidate = cohort.make_train_task(97, 0)
    monkeypatch.setattr(cohort, 'MAX_NONCES', 1)
    with pytest.raises(ValueError, match='fresh_candidates_exhausted_before_dispatch'):
        cohort.extend_train(training, excluded_ids={candidate['id']})
    assert training == original


@pytest.mark.parametrize('count', [0, -1, True, 1.5, '96'])
def test_invalid_extension_size(training, count):
    with pytest.raises(ValueError, match='positive_additional_cycles'):
        cohort.extend_train(training, additional_cycles=count)


@pytest.mark.parametrize('field,value,error', [
    ('split', 'DEV', 'train_only'),
    ('split', 'FINAL', 'train_only'),
    ('cycle', 0, 'original_generator_schema_required'),
    ('question_sha256', '0' * 64, 'original_generator_schema_required'),
    ('gold', 'tampered', 'original_generator_schema_required'),
    ('id', 'other_namespace', 'original_train_namespace_and_cycle_required'),
])
def test_rejects_visibility_or_recipe_changes(training, field, value, error):
    training[0][0][field] = value
    with pytest.raises(ValueError, match=error):
        cohort.extend_train(training)


def test_rejects_incomplete_prefix_and_wrong_cycle_width(training):
    with pytest.raises(ValueError, match='complete_96_cycle_train_prefix_required'):
        cohort.extend_train(training[:95])
    training[0].pop()
    with pytest.raises(ValueError, match='two_tasks_per_cycle_required'):
        cohort.extend_train(training)


def test_cli_creates_new_candidate_and_reads_no_held_files(training, tmp_path, monkeypatch, capsys):
    train = tmp_path / 'TRAIN.json'
    raw = json.dumps(training, separators=(',', ':')).encode()
    train.write_bytes(raw)
    expected = hashlib.sha256(raw).hexdigest()
    output = tmp_path / 'TRAIN_R149.json'
    original_read = Path.read_bytes
    allowed = {train, Path(cohort.recipe.__file__), Path(cohort.recipe.source.__file__)}
    reads = []

    def guarded_read(path):
        assert path in allowed
        reads.append(path)
        return original_read(path)

    monkeypatch.setattr(Path, 'read_bytes', guarded_read)
    cohort.main(['--train', str(train), '--output', str(output), '--expected-train-sha256', expected])
    receipt = json.loads(capsys.readouterr().out)
    result = json.loads(original_read(output))
    assert result[:96] == training
    assert original_read(train) == raw
    assert receipt['output_sha256'] == hashlib.sha256(original_read(output)).hexdigest()
    assert receipt['preserved_cycles'] == receipt['added_cycles'] == 96
    assert receipt['preserved_tasks'] == receipt['added_tasks'] == 192
    assert (receipt['first_new_cycle'], receipt['last_cycle']) == (97, 192)
    assert receipt['held_and_inherited_pool_collision_check'] == 'NOT_PERFORMED'
    assert receipt['dispatch_authorized'] is False
    assert set(reads) == allowed
    assert not {'question', 'gold', 'excluded_ids'}.intersection(receipt)
    with pytest.raises(FileExistsError):
        cohort.prepare(train, output, expected_train_sha256=expected)
    with pytest.raises(FileExistsError):
        cohort.prepare(train, train, expected_train_sha256=expected)
    with pytest.raises(ValueError, match='exact_train_file_binding_required'):
        cohort.prepare(train, tmp_path / 'wrong.json', expected_train_sha256='0' * 64)
    assert not (tmp_path / 'wrong.json').exists()
    assert original_read(train) == raw


def test_service_cli_immutable_cohort_manifest_and_broker_map(training, tmp_path, capsys):
    train = tmp_path / 'TRAIN.json'
    raw = json.dumps(training).encode()
    train.write_bytes(raw)
    expected = hashlib.sha256(raw).hexdigest()
    service = tmp_path / 'runtime_r149_cohort96_20260916t1920z'
    cohort.main(['--train', str(train), '--service', str(service),
        '--expected-train-sha256', expected])
    summary = json.loads(capsys.readouterr().out)
    manifest_path, candidate_path = service / 'COHORT.json', service / 'TRAIN.json'
    manifest = json.loads(manifest_path.read_bytes())
    candidate = json.loads(candidate_path.read_bytes())
    assert candidate[:96] == training
    assert train.read_bytes() == raw
    assert manifest['original_train_sha256'] == expected
    assert manifest['train_sha256'] == hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    assert summary['manifest_sha256'] == hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    assert (manifest['cycles_before'], manifest['cycles_after']) == (96, 192)
    assert manifest['task_id_collisions'] == manifest['question_hash_collisions'] == 0
    assert manifest['collision_scope'] == 'ORIGINAL_TRAIN_AND_NEW_TRAIN_ONLY'
    assert manifest['train_tasks'] == {
        task['id']: task['question_sha256'] for group in candidate for task in group}
    assert len(manifest['train_tasks']) == 384
    assert 'train_tasks' not in summary
    assert manifest['held_and_inherited_pool_collision_check'] == 'NOT_PERFORMED'
    assert manifest['dispatch_authorized'] is False
    assert len(manifest['source_sha256']) == 4
    assert all(len(value) == 64 for value in manifest['source_sha256'].values())
    assert candidate_path.stat().st_mode & 0o777 == 0o444
    assert manifest_path.stat().st_mode & 0o777 == 0o444
    with pytest.raises(ValueError, match='new_service_artifacts_required'):
        cohort.prepare_service(train, service, expected_train_sha256=expected)


def test_service_refuses_existing_manifest_before_writing_train(training, tmp_path):
    train = tmp_path / 'TRAIN.json'
    raw = json.dumps(training).encode()
    train.write_bytes(raw)
    service = tmp_path / 'service'
    service.mkdir()
    manifest = service / 'COHORT.json'
    manifest.write_bytes(b'existing owner artifact')
    with pytest.raises(ValueError, match='new_service_artifacts_required'):
        cohort.prepare_service(train, service, expected_train_sha256=hashlib.sha256(raw).hexdigest())
    assert manifest.read_bytes() == b'existing owner artifact'
    assert not (service / 'TRAIN.json').exists()
