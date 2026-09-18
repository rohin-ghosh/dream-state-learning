"""CPU budget, attribution, isolation and unchanged PixelArchive contract regressions."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import ny_caption_similarity as similarity
from gpu.ny_caption_pixels import PixelArchive, PixelConfig


@pytest.fixture
def budget(tmp_path):
    scope = dict(schema='NY_SIMILARITY_BOUNDED_SCOPE_V1', label_call_cap=360,
        verification_call_cap=32, pair_label_cap=360, active_seconds_max=3600,
        absolute_end_unix=similarity.time.time() + 600, retries=0,
        provider_model=similarity.LABEL_MODEL, allowed_pool='judge_train',
        locked_validation_reads=0, FINAL_reads=0, lane_id='smoke')
    reference = similarity.private_write(tmp_path / 'scope.json', scope)
    return similarity.CallBudget(tmp_path / 'budget', reference)


def response(items, **extra):
    return dict(choices=[dict(finish_reason='stop', message=dict(content=json.dumps(dict(items=items))))],
        model=similarity.LABEL_MODEL, usage=dict(prompt_tokens=10, completion_tokens=10), **extra)


def correct(body, timeout):
    pairs = json.loads(body['messages'][1]['content'])['items']
    return response([dict(pair_id=pair['pair_id'], coarse=True, primary=True, fine=True) for pair in pairs])


def pair(identity='opaque'):
    return dict(pair_id=identity, scene='Synthetic scene.', caption_a='First synthetic caption.', caption_b='Second synthetic caption.')


def test_pinned_sentence_encoder_not_MLM():
    assert similarity.MODEL_ID == 'sentence-transformers/all-MiniLM-L6-v2'
    assert len(similarity.MODEL_REVISION) == 40
    assert similarity.LABEL_MODEL == 'openai/openai/gpt-6-astra'


def test_private_files_are_exclusive_and_private(tmp_path):
    reference = similarity.private_write(tmp_path / 'private.json', {'private': 'fixture'})
    assert Path(reference['path']).stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        similarity.private_write(tmp_path / 'private.json', {})


def test_changed_reference_refused(tmp_path):
    reference = similarity.private_write(tmp_path / 'bound.json', {'value': 1})
    with pytest.raises(ValueError, match='reference_hash_changed'):
        similarity.bound(dict(reference, sha256='0' * 64))


def test_missing_credentials_no_dispatch_or_charge(budget):
    annotator = similarity.AstraAnnotator(budget, key='')
    with pytest.raises(ValueError, match='credential_missing_no_dispatch'):
        annotator.labels('missing', [pair()])
    assert budget.summary()['label_calls_charged'] == 0


def test_success_attribution_and_private_labels(budget):
    annotator = similarity.AstraAnnotator(budget, transport=correct)
    labels, reference = annotator.labels('one', [pair()])
    receipt = similarity.bound(reference)
    assert labels['opaque']['primary'] is True
    assert receipt['attribution']['provisional'] is True
    assert receipt['attribution']['human_truth'] is False
    assert budget.summary()['pair_labels_charged'] == 1


def test_after_dispatch_failure_charged_and_no_retry(budget):
    def fail(body, timeout):
        raise TimeoutError('private text must not escape')
    annotator = similarity.AstraAnnotator(budget, transport=fail)
    with pytest.raises(similarity.AnnotationUnavailable, match='annotation_failed_preserved_no_retry'):
        annotator.labels('failed', [pair()])
    assert budget.summary()['label_calls_charged'] == 1
    assert budget.summary()['failed_or_invalid_calls'] == 1
    with pytest.raises(ValueError, match='operation_already_consumed_no_retry'):
        annotator.labels('failed', [pair()])


@pytest.mark.parametrize('items', [[], [dict(pair_id='wrong', coarse=True, primary=True, fine=True)],
    [dict(pair_id='opaque', coarse=False, primary=True, fine=True)],
    [dict(pair_id='opaque', coarse=True, primary=1, fine=True)],
    [dict(pair_id='opaque', coarse=True, primary=True, fine=True, rationale='not allowed')]])
def test_invalid_labels_are_missing_and_charged(budget, items):
    annotator = similarity.AstraAnnotator(budget, transport=lambda body, timeout: response(items))
    with pytest.raises(similarity.AnnotationUnavailable, match='invalid_labels_preserved_no_retry'):
        annotator.labels('invalid', [pair()])
    assert budget.summary()['pair_labels_charged'] == 1
    assert not (budget.root / 'invalid/LABELS.private.json').exists()


def test_truncated_annotation_not_complete(budget):
    def truncated(body, timeout):
        document = correct(body, timeout)
        document['choices'][0]['finish_reason'] = 'length'
        return document
    with pytest.raises(similarity.AnnotationUnavailable):
        similarity.AstraAnnotator(budget, transport=truncated).labels('truncated', [pair()])
    assert budget.summary()['failed_or_invalid_calls'] == 1


def test_echoed_secret_is_redacted_in_receipt(budget):
    secret = 'unit-test-secret-never-logged'
    def echoed(body, timeout):
        document = correct(body, timeout)
        document['unused_echo'] = secret
        return document
    similarity.AstraAnnotator(budget, key=secret, transport=echoed).labels('echo', [pair()])
    assert secret.encode() not in (budget.root / 'echo/RESPONSE.private.json').read_bytes()


def test_concurrent_duplicate_admission_exactly_once(budget):
    def reserve():
        try:
            budget.reserve('same', 'label', 1, 100)
            return True
        except ValueError:
            return False
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert sum(pool.map(lambda value: reserve(), range(8))) == 1
    assert budget.summary()['label_calls_charged'] == 1


def test_pair_budget_and_verification_budget_separate(budget):
    for index in range(30):
        budget.reserve('batch_' + str(index), 'label', 12, 10)
    with pytest.raises(ValueError, match='pair_budget_exhausted'):
        budget.reserve('overflow', 'label', 1, 10)
    for index in range(32):
        budget.reserve('verify_' + str(index), 'verification', 1, 10)
    with pytest.raises(ValueError, match='call_budget_exhausted'):
        budget.reserve('verify_overflow', 'verification', 1, 10)


def test_no_moving_wall_or_budget_rebind(budget, monkeypatch):
    budget.reserve('first', 'label', 1, 10)
    monkeypatch.setattr(similarity.time, 'time', lambda: budget.scope['absolute_end_unix'] + 1)
    with pytest.raises(ValueError, match='fixed_active_or_admitted_wall_ended'):
        budget.reserve('late', 'label', 1, 10)
    changed = dict(budget.scope, label_call_cap=359)
    reference = similarity.private_write(budget.root.parent / 'other_scope.json', changed)
    with pytest.raises(ValueError, match='no_budget_rebinding'):
        similarity.CallBudget(budget.root, reference)


def test_ambiguous_verification_never_becomes_novelty(budget):
    def ambiguous(body, timeout):
        items = json.loads(body['messages'][1]['content'])['items']
        return response([dict(pair_id=items[0]['pair_id'], coarse=True, primary=None, fine=None)])
    verifier = similarity.SameJokeVerifier(similarity.AstraAnnotator(budget, transport=ambiguous), lane_id='smoke')
    with pytest.raises(similarity.AnnotationUnavailable, match='ambiguous_model_annotation'):
        verifier('Synthetic scene.', 'Candidate.', 'Representative.')
    assert budget.summary()['verification_calls_charged'] == 1


def test_no_cross_lane_verifier_state(budget):
    with pytest.raises(ValueError, match='no_cross_lane'):
        similarity.SameJokeVerifier(similarity.AstraAnnotator(budget, transport=correct), lane_id='other')


def test_actual_callable_contract_and_exact_replay(budget):
    verifier = similarity.SameJokeVerifier(similarity.AstraAnnotator(budget, transport=correct), lane_id='smoke')
    config = PixelConfig(similarity.MODEL_ID, similarity.MODEL_REVISION, .5, .6, .7)
    archive = PixelArchive('smoke', 'synthetic', 'Synthetic scene.', config, lambda text: [1., 0.], same_joke_verifier=verifier)
    archive.submit('First synthetic caption.', accepted=True, q=.8)
    result = archive.submit('Second synthetic caption.', accepted=True, q=.8)
    assert result.status == 'repeat'
    assert archive.submit('Second synthetic caption.', accepted=True, q=.8) == result
    assert budget.summary()['verification_calls_charged'] == 1


def test_public_summary_excludes_ids_labels_and_errors():
    result = dict(rho=.8, training={'n': 2, 'fp_merge': 1, 'errors': [{'private_caption': 'secret'}]},
        heldout={'n': 2, 'false_merge_rate': .5})
    report = dict(resolutions={name: result for name in similarity.RESOLUTIONS}, pair_count=4,
        training_pair_ids=['private1'], heldout_pair_ids=['private2'], label_source_counts={'llm': 4},
        human_labeled_pair_count=0, warnings=[], pixel_config={'rho': .8})
    public = similarity.safe_calibration_summary(report)
    assert 'private' not in json.dumps(public).replace('private_label_or_caption_contents', '')
    assert public['metrics']['primary']['training']['n'] == 2
    assert public['encoder_execution_verified'] is False


def test_unresolved_records_do_not_count_as_sufficient_labels():
    report = dict(resolutions={name: dict(heldout=dict(balanced_error=.1)) for name in similarity.RESOLUTIONS})
    pairs = [SimpleNamespace(group_id=str(index % 30), contest_id=str(index % 30),
        labels={name: (True if index < 239 else None) for name in similarity.RESOLUTIONS}) for index in range(300)]
    assert similarity.sufficient_labels(pairs, report) is False
    pairs[239].labels = {name: False for name in similarity.RESOLUTIONS}
    assert similarity.sufficient_labels(pairs, report) is True


def test_missing_holdout_classes_cannot_emit_threshold():
    pairs = [SimpleNamespace(group_id=str(index % 30), contest_id=str(index % 30),
        labels={name: True for name in similarity.RESOLUTIONS}) for index in range(300)]
    report = dict(resolutions={name: dict(heldout=dict(balanced_error=None)) for name in similarity.RESOLUTIONS})
    assert similarity.sufficient_labels(pairs, report) is False


def test_development_factory_requires_explicit_Main_bound_lane_budget(tmp_path):
    scope = dict(schema='NY_SIMILARITY_DEVELOPMENT_VERIFIER_SCOPE_V1', issuer='Main/Astra', no_reset=True,
        label_call_cap=0, pair_label_cap=0, verification_call_cap=2, active_seconds_max=600,
        absolute_end_unix=similarity.time.time() + 500, retries=0, provider_model=similarity.LABEL_MODEL,
        allowed_pool='agent_development', locked_validation_reads=0, FINAL_reads=0, lane_id='lane_one')
    reference = similarity.private_write(tmp_path / 'development.json', scope)
    verifier = similarity.make_same_joke_verifier(lane_id='lane_one', budget_root=tmp_path / 'budget',
        scope_ref=reference, api_key='')
    assert callable(verifier)
    assert verifier.annotator.budget.summary()['verification_calls_charged'] == 0
    with pytest.raises(ValueError, match='exact_lane_budget_binding'):
        similarity.make_same_joke_verifier(lane_id='lane_two', budget_root=tmp_path / 'budget', scope_ref=reference)


@pytest.mark.parametrize('change', [{'issuer': 'self'}, {'label_call_cap': 1}, {'pair_label_cap': 1},
    {'verification_call_cap': 33}, {'allowed_pool': 'final'}, {'no_reset': False}])
def test_development_factory_does_not_expand_scope(tmp_path, change):
    scope = dict(schema='NY_SIMILARITY_DEVELOPMENT_VERIFIER_SCOPE_V1', issuer='Main/Astra', no_reset=True,
        label_call_cap=0, pair_label_cap=0, verification_call_cap=2, active_seconds_max=600,
        absolute_end_unix=similarity.time.time() + 500, retries=0, provider_model=similarity.LABEL_MODEL,
        allowed_pool='agent_development', locked_validation_reads=0, FINAL_reads=0, lane_id='lane_one')
    scope.update(change)
    reference = similarity.private_write(tmp_path / 'invalid.json', scope)
    with pytest.raises(ValueError):
        similarity.make_same_joke_verifier(lane_id='lane_one', budget_root=tmp_path / 'budget', scope_ref=reference)


@pytest.mark.parametrize('purpose,pair_units', [('label', 1), ('label', 0), ('verification', 0), ('verification', 2)])
def test_development_scope_cannot_dispatch_labels_generation_or_batches(tmp_path, purpose, pair_units):
    scope = dict(schema='NY_SIMILARITY_DEVELOPMENT_VERIFIER_SCOPE_V1', issuer='Main/Astra', no_reset=True,
        label_call_cap=0, pair_label_cap=0, verification_call_cap=2, active_seconds_max=600,
        absolute_end_unix=similarity.time.time() + 500, retries=0, provider_model=similarity.LABEL_MODEL,
        allowed_pool='agent_development', locked_validation_reads=0, FINAL_reads=0, lane_id='lane_one')
    reference = similarity.private_write(tmp_path / 'development.json', scope)
    budget = similarity.CallBudget(tmp_path / 'budget', reference)
    with pytest.raises(ValueError, match='development_verifier_one_pair_only'):
        budget.reserve('refused', purpose, pair_units, 4096)
    assert budget.summary()['verification_calls_charged'] == 0
    assert budget.summary()['label_calls_charged'] == 0


def test_development_factory_preserves_spend_across_instances(tmp_path):
    scope = dict(schema='NY_SIMILARITY_DEVELOPMENT_VERIFIER_SCOPE_V1', issuer='Main/Astra', no_reset=True,
        label_call_cap=0, pair_label_cap=0, verification_call_cap=1, active_seconds_max=600,
        absolute_end_unix=similarity.time.time() + 500, retries=0, provider_model=similarity.LABEL_MODEL,
        allowed_pool='agent_development', locked_validation_reads=0, FINAL_reads=0, lane_id='lane_one')
    reference = similarity.private_write(tmp_path / 'development.json', scope)
    verifier = similarity.make_same_joke_verifier(lane_id='lane_one', budget_root=tmp_path / 'budget',
        scope_ref=reference, api_key='')
    verifier.annotator._transport = correct
    assert verifier('Synthetic scene.', 'Synthetic first.', 'Synthetic second.') is True
    successor = similarity.make_same_joke_verifier(lane_id='lane_one', budget_root=tmp_path / 'budget',
        scope_ref=reference, api_key='')
    successor.annotator._transport = correct
    with pytest.raises(ValueError, match='operation_already_consumed_no_retry'):
        successor('Synthetic scene.', 'Synthetic first.', 'Synthetic second.')
    with pytest.raises(ValueError, match='call_budget_exhausted'):
        successor('Synthetic scene.', 'Synthetic third.', 'Synthetic fourth.')
    assert successor.annotator.budget.summary()['verification_calls_charged'] == 1
    assert successor.annotator.budget.summary()['label_calls_charged'] == 0
