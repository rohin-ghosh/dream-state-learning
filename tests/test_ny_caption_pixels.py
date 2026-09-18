"""Synthetic CPU contract checks, not pretrained embedding or humor validation."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import FrozenInstanceError, asdict, replace
import json
import math

import pytest

from gpu.ny_caption_pixels import (
    ArchiveFullError, LabeledPair, PixelArchive, PixelConfig, SnapshotError, calibrate_pairs,
    embedding_key, embedding_text, main, normalized_vector,
)


@pytest.fixture
def config():
    return PixelConfig('synthetic-test-encoder', 'fixture-v1', 0.7, 0.8, 0.9)


def encoder(vectors, calls=None):
    def embed(text):
        payload = json.loads(text)
        assert set(payload) == {'scene', 'caption'}
        if calls is not None:
            calls.append(payload)
        return vectors[payload['caption']]
    return embed


def test_config_requires_explicit_ordered_finite_thresholds(config):
    with pytest.raises(TypeError):
        PixelConfig('model', 'revision')
    for field, value in [('rho_primary', float('nan')), ('rho_coarse', 0.95),
                         ('rho_fine', 2), ('rho_primary', True),
                         ('resolution', 'FINAL'), ('embedding_revision', ''),
                         ('input_format', 'caption_only')]:
        with pytest.raises(ValueError):
            replace(config, **{field: value})
    with pytest.raises(FrozenInstanceError):
        config.rho_primary = 0.4


@pytest.mark.parametrize('vector', [[], [0, 0], [float('nan'), 1], [float('inf'), 1],
                                   '123', {'dimension': 1}, [object()], None])
def test_rejects_invalid_embeddings(vector):
    with pytest.raises(ValueError):
        normalized_vector(vector)


def test_normalization_handles_large_and_tiny_finite_vectors():
    assert normalized_vector([3, 4]) == pytest.approx((0.6, 0.8))
    assert normalized_vector([1e308, 1e308]) == pytest.approx((2 ** -0.5,) * 2)
    assert normalized_vector([1e-300, 0]) == (1.0, 0.0)


def test_embedding_input_has_unambiguous_frozen_scene_caption_boundaries():
    scene, caption = 'A scene with "quotes".\nCaption: not a caption', 'Line one\nLine two'
    assert json.loads(embedding_text(scene, caption)) == dict(scene=scene, caption=caption)
    assert embedding_key(scene, caption) != embedding_key(caption, scene)


def test_rejected_captions_are_history_only_and_idempotent(config):
    def forbidden_embed(text):
        pytest.fail('rejected captions must never be embedded')
    archive = PixelArchive('child-a', 'cartoon-a', 'Facts', config, forbidden_embed)
    first = archive.submit('rejected data', accepted=False, q=0.1)
    second = archive.submit('rejected data', accepted=False, q=0.1)
    assert first is second
    assert first.status == 'rejected' and first.vector is None
    assert archive.pixel_count == 0 and len(archive.history) == 1
    assert archive.pixels == ()
    assert archive.snapshot()['history'][0]['caption'] == 'rejected data'


def test_representatives_never_replaced_or_chained_through_members(config):
    vectors = {'first': (1, 0), 'better delivery': (math.cos(math.pi / 6), 0.5),
               'third idea': (0.5, math.sin(math.pi / 3))}
    archive = PixelArchive('child', 'cartoon', 'Facts', config, encoder(vectors))
    first = archive.submit('first', accepted=True, q=0.8)
    repeat = archive.submit('better delivery', accepted=True, q=0.99)
    third = archive.submit('third idea', accepted=True, q=0.85)
    assert first.status == third.status == 'new_pixel'
    assert repeat.status == 'repeat' and repeat.pixel_id == first.pixel_id
    assert archive.pixel_count == 2
    assert archive.pixels[0].representative_caption == 'first'
    assert archive.pixels[0].representative_vector == (1, 0)
    assert len(archive.pixels[0].members) == 2
    assert third.nearest_similarity == pytest.approx(0.5)
    with pytest.raises(FrozenInstanceError):
        archive.pixels[0].representative_caption = 'replacement'


def test_matches_nearest_representative_not_first_threshold_hit(config):
    config = replace(config, rho_coarse=0.3, rho_primary=0.3, rho_fine=0.9)
    archive = PixelArchive('child', 'cartoon', 'Facts', config,
                           encoder({'old': (1, 0), 'new': (0, 1), 'candidate': (0.4, 0.9)}))
    archive.submit('old', accepted=True, q=0.9)
    second = archive.submit('new', accepted=True, q=0.9)
    match = archive.submit('candidate', accepted=True, q=0.9)
    assert match.pixel_id == second.pixel_id and match.matching_caption == 'new'
    assert match.similarities == ((second.pixel_id, match.nearest_similarity),)
    assert archive.snapshot()['similarity_trace'] == 'nearest_only_all_immutable_representatives_searched'


def test_equal_cosine_tie_matches_oldest_and_threshold_is_inclusive(config):
    config = replace(config, rho_coarse=0.5, rho_primary=0.5, rho_fine=0.9)
    archive = PixelArchive('child', 'cartoon', 'Facts', config,
                           encoder({'old': (1, 0), 'new': (0, 1), 'tie': (1, 1)}))
    first = archive.submit('old', accepted=True, q=0.9)
    archive.submit('new', accepted=True, q=0.9)
    assert archive.submit('tie', accepted=True, q=0.9).pixel_id == first.pixel_id
    exact = PixelArchive('child', 'other', 'Facts', replace(config, rho_primary=1, rho_fine=1),
                         encoder({'one': (2, 0), 'two': (200, 0)}))
    exact.submit('one', accepted=True, q=0.9)
    assert exact.submit('two', accepted=True, q=0.9).status == 'repeat'


def test_agent_and_contest_archives_are_isolated(config):
    archives = [PixelArchive(agent, contest, 'Facts', config, lambda text: (1, 0))
                for agent, contest in [('FROZEN-life', 'one'), ('LEARNER-life', 'one'), ('FROZEN-life', 'two')]]
    traces = [archive.submit('same text', accepted=True, q=0.9) for archive in archives]
    assert all(trace.status == 'new_pixel' and trace.matching_caption is None for trace in traces)
    assert len({trace.submission_id for trace in traces}) == 3


def test_exact_submissions_are_atomic_and_conflicts_do_not_rescore(config):
    calls = []
    archive = PixelArchive('child', 'cartoon', 'Facts', config, encoder({'caption': (1, 0)}, calls))
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda index: archive.submit('caption', accepted=True, q=0.9), range(30)))
    assert all(result is results[0] for result in results)
    assert len(calls) == len(archive.history) == archive.pixel_count == 1
    before = archive.snapshot()
    with pytest.raises(ValueError, match='conflicting'):
        archive.submit('caption', accepted=True, q=0.95)
    assert archive.snapshot() == before


def test_exact_bytes_not_case_or_whitespace_are_idempotency_key(config):
    archive = PixelArchive('child', 'cartoon', 'Facts', config, lambda text: (1, 0))
    first = archive.submit('Caption', accepted=True, q=0.9)
    second = archive.submit('caption ', accepted=True, q=0.9)
    assert first.submission_id != second.submission_id
    assert second.status == 'repeat' and len(archive.history) == 2


def test_capacity_preserves_existing_records_and_allows_exact_replay(config):
    archive = PixelArchive('child', 'cartoon', 'Facts', config, lambda text: (1, 0), max_submissions=1)
    original = archive.submit('first', accepted=True, q=0.9)
    with pytest.raises(ArchiveFullError):
        archive.submit('second', accepted=True, q=0.9)
    assert archive.submit('first', accepted=True, q=0.9) is original
    assert len(archive.history) == 1


def test_dimension_or_verifier_failure_has_no_partial_commit(config):
    vectors = {'first': (1, 0), 'bad': (1, 0, 0)}
    archive = PixelArchive('child', 'cartoon', 'Facts', config, encoder(vectors))
    archive.submit('first', accepted=True, q=0.9)
    before = archive.snapshot()
    with pytest.raises(ValueError, match='dimensions'):
        archive.submit('bad', accepted=True, q=0.9)
    assert archive.snapshot() == before
    archive = PixelArchive('child', 'cartoon', 'Facts', config, lambda text: (1, 0),
                           same_joke_verifier=lambda *args: 'yes')
    archive.submit('first', accepted=True, q=0.9)
    with pytest.raises(ValueError, match='bool'):
        archive.submit('second', accepted=True, q=0.9)
    assert len(archive.history) == 1


def test_optional_contextual_verifier_sees_only_scene_and_caption_pair(config):
    calls = []
    def verifier(scene, caption, representative):
        calls.append((scene, caption, representative))
        return False
    archive = PixelArchive('private-child', 'cartoon', 'Visible facts', config, lambda text: (1, 0),
                           same_joke_verifier=verifier)
    archive.submit('same topic one', accepted=True, q=0.9)
    result = archive.submit('same topic two', accepted=True, q=0.9)
    assert result.status == 'new_pixel' and result.verifier_same_joke is False
    assert calls == [('Visible facts', 'same topic two', 'same topic one')]
    assert archive.snapshot()['implementation'] == 'embedding_plus_verifier'


def test_sequential_order_sensitivity_remains_visible_for_later_audits(config):
    vectors = {'left': (1, 0), 'middle': (math.cos(math.pi / 6), 0.5),
               'right': (0.5, math.sin(math.pi / 3))}
    counts = []
    for captions in (('left', 'middle', 'right'), ('middle', 'left', 'right')):
        archive = PixelArchive('child', 'cartoon', 'Facts', config, encoder(vectors))
        for caption in captions:
            archive.submit(caption, accepted=True, q=0.9)
        assert tuple(trace.caption for trace in archive.history) == captions
        counts.append(archive.pixel_count)
    assert counts == [2, 1]


def test_archive_stop_json_reload_continue_never_reembeds_or_reverifies(config):
    vectors = {'first': (1, 0), 'repeat': (1, 0), 'new': (0, 1)}
    original = PixelArchive('child', 'cartoon', 'Facts', config, encoder(vectors), max_submissions=5,
                            same_joke_verifier=lambda *args: True)
    first = original.submit('first', accepted=True, q=0.9)
    original.submit('repeat', accepted=True, q=0.95)
    original.submit('rejected', accepted=False, q=0.1)
    state = json.loads(json.dumps(original.snapshot()))
    calls = []
    def only_new(text):
        calls.append(text)
        assert json.loads(text)['caption'] == 'new'
        return (0, 1)
    def forbidden_verifier(*args):
        pytest.fail('restore and exact replay must not reverify')
    restored = PixelArchive.from_snapshot(state, 'child', 'cartoon', 'Facts', config, only_new,
                                          max_submissions=5, same_joke_verifier=forbidden_verifier)
    assert json.loads(json.dumps(restored.snapshot())) == state
    assert restored.submit('first', accepted=True, q=0.9) == first
    assert restored.submit('rejected', accepted=False, q=0.1).status == 'rejected'
    assert calls == []
    assert restored.submit('new', accepted=True, q=0.9).status == 'new_pixel'
    assert len(calls) == 1 and restored.pixel_count == 2
    assert restored.pixels[0].representative_caption == 'first'
    assert len(restored.pixels[0].members) == 2
    assert original.pixel_count == 1


@pytest.mark.parametrize('binding,value', [('agent_id', 'other-child'), ('contest_id', 'other-cartoon'),
                                         ('scene', 'Other facts'), ('max_submissions', 1)])
def test_archive_restore_requires_exact_explicit_bindings(config, binding, value):
    original = PixelArchive('child', 'cartoon', 'Facts', config, lambda text: (1, 0))
    original.submit('Caption', accepted=True, q=0.9)
    arguments = dict(agent_id='child', contest_id='cartoon', scene='Facts', config=config,
                     embed=lambda text: pytest.fail('restore must not call encoder'))
    arguments[binding] = value
    with pytest.raises(SnapshotError, match='binding'):
        PixelArchive.from_snapshot(original.snapshot(), **arguments)


def test_archive_restore_config_and_optional_verifier_binding_are_exact(config):
    original = PixelArchive('child', 'cartoon', 'Facts', config, lambda text: (1, 0))
    original.submit('Caption', accepted=True, q=0.9)
    with pytest.raises(SnapshotError, match='config'):
        PixelArchive.from_snapshot(original.snapshot(), 'child', 'cartoon', 'Facts',
                                   replace(config, embedding_revision='new-revision'), lambda text: (1, 0))
    with pytest.raises(SnapshotError, match='implementation'):
        PixelArchive.from_snapshot(original.snapshot(), 'child', 'cartoon', 'Facts', config,
                                   lambda text: (1, 0), same_joke_verifier=lambda *args: True)


@pytest.mark.parametrize('change', ['representative', 'vector', 'member', 'identity', 'nearest', 'sequence', 'rejection', 'nonfinite'])
def test_archive_restore_rejects_broken_closure_atomically(config, change):
    original = PixelArchive('child', 'cartoon', 'Facts', config, lambda text: (1, 0))
    original.submit('first', accepted=True, q=0.9)
    original.submit('repeat', accepted=True, q=0.9)
    original.submit('rejected', accepted=False, q=0.1)
    state = json.loads(json.dumps(original.snapshot()))
    if change == 'representative':
        state['pixels'][0]['representative_caption'] = 'repeat'
    elif change == 'vector':
        state['history'][0]['vector'] = [2, 0]
    elif change == 'member':
        state['pixels'][0]['members'].pop()
    elif change == 'identity':
        state['history'][0]['submission_id'] = 'foreign-life'
    elif change == 'nearest':
        state['history'][1]['nearest_pixel_id'] = 'pixel-000009'
    elif change == 'sequence':
        state['history'][1]['sequence'] = 10
    elif change == 'rejection':
        state['history'][2]['vector'] = [1, 0]
    else:
        state['history'][0]['vector'] = [float('nan'), 0]
    target = PixelArchive('child', 'cartoon', 'Facts', config, lambda text: pytest.fail('restore must not embed'))
    before = target.snapshot()
    with pytest.raises(SnapshotError):
        target.restore(state)
    assert target.snapshot() == before
    target.restore(original.snapshot())
    with pytest.raises(SnapshotError, match='empty'):
        target.restore(original.snapshot())


def test_legacy_full_distance_snapshot_preserves_trace_format_across_restart(config):
    vectors = {'first': (1, 0), 'second': (0, 1), 'repeat': (0, 1), 'later': (0, 1)}
    original = PixelArchive('child', 'cartoon', 'Facts', config, encoder(vectors))
    for caption in ('first', 'second', 'repeat'):
        original.submit(caption, accepted=True, q=0.9)
    state = json.loads(json.dumps(original.snapshot()))
    state.pop('similarity_trace')
    distances = [['pixel-000001', 0.0], ['pixel-000002', 1.0]]
    state['history'][2]['similarities'] = distances
    state['pixels'][1]['members'][1]['similarities'] = deepcopy(distances)
    restored = PixelArchive.from_snapshot(state, 'child', 'cartoon', 'Facts', config, encoder(vectors))
    assert json.loads(json.dumps(restored.snapshot())) == state
    restored.submit('later', accepted=True, q=0.9)
    again = PixelArchive.from_snapshot(restored.snapshot(), 'child', 'cartoon', 'Facts', config, encoder(vectors))
    assert again.snapshot() == restored.snapshot()


def make_pairs(pair_count=300, source='synthetic'):
    pairs, vectors = [], {}
    for index in range(pair_count):
        same = (index // 6) % 2 == 0
        similarity = 0.95 if same else 0.2
        scene = f'Synthetic scene {index % 6}.'
        caption_a, caption_b = f'Fixture left {index}', f'Fixture right {index}'
        pairs.append(LabeledPair(f'pair-{index}', f'dev-{index % 6}', scene, caption_a, caption_b,
                                 {resolution: same for resolution in ('coarse', 'primary', 'fine')}, source))
        vectors[embedding_text(scene, caption_a)] = (1, 0)
        vectors[embedding_text(scene, caption_b)] = (similarity, math.sqrt(1 - similarity ** 2))
    return pairs, vectors


def test_calibration_reports_fpmerge_fnsplit_and_missing_human_labels(config):
    pairs, vectors = make_pairs()
    report = calibrate_pairs(pairs, config, vectors.__getitem__)
    assert report['pair_count'] == 300 and report['validation_status'] == 'provisional'
    assert report['validated_scoring'] is False
    assert report['human_labeled_pair_count'] == 0
    assert 'missing_human_labels' in report['warnings']
    assert set(report['training_pair_ids']).isdisjoint(report['heldout_pair_ids'])
    for resolution in ('coarse', 'primary', 'fine'):
        metrics = report['resolutions'][resolution]['heldout']
        assert metrics['fp_merge'] == metrics['fn_split'] == 0
        assert metrics['false_merge_rate'] == metrics['false_split_rate'] == 0
    selected = PixelConfig(**report['pixel_config'])
    assert selected.rho_coarse <= selected.rho_primary <= selected.rho_fine


def test_heldout_labels_and_initial_thresholds_do_not_select_rho(config):
    pairs, vectors = make_pairs()
    original = calibrate_pairs(pairs, config, vectors.__getitem__)
    heldout = set(original['heldout_pair_ids'])
    changed = [replace(pair, labels={name: not value for name, value in pair.labels.items()})
               if pair.pair_id in heldout else pair for pair in pairs]
    alternate = calibrate_pairs(changed, replace(config, rho_coarse=-1, rho_primary=-1, rho_fine=1),
                                 vectors.__getitem__)
    assert alternate['pixel_config'] == original['pixel_config']
    metrics = alternate['resolutions']['primary']['heldout']
    assert metrics['fp_merge'] > 0 and metrics['fn_split'] > 0
    assert {error['error'] for error in metrics['errors']} == {'FPmerge', 'FNsplit'}


def test_sparse_or_missing_labels_never_manufacture_all_three_thresholds(config):
    pairs, vectors = make_pairs(30)
    sparse = [replace(pair, labels={'primary': pair.labels['primary']}) for pair in pairs]
    report = calibrate_pairs(sparse, config, vectors.__getitem__)
    assert report['pixel_config'] is None
    assert report['resolutions']['coarse']['rho'] is None
    assert report['resolutions']['primary']['rho'] is not None
    unlabeled = [replace(pair, labels={}, label_source='missing') for pair in pairs]
    report = calibrate_pairs(unlabeled, config, vectors.__getitem__)
    assert report['pixel_config'] is None and report['human_labeled_pair_count'] == 0
    assert all(entry['rho'] is None for entry in report['resolutions'].values())


def test_scene_groups_stay_disjoint_and_insufficient_groups_are_provisional(config):
    pairs, vectors = make_pairs(30)
    pairs = [replace(pair, group_id='same-scene-family') for pair in pairs]
    report = calibrate_pairs(pairs, config, vectors.__getitem__)
    assert report['heldout_pair_ids'] == []
    assert 'insufficient_independent_groups_for_holdout' in report['warnings']
    with pytest.raises(ValueError, match='straddle'):
        calibrate_pairs([replace(pairs[0], group_id='one'), replace(pairs[6], group_id='two')],
                        config, vectors.__getitem__)


def test_calibration_rejects_invalid_labels_and_duplicate_identifiers(config):
    pairs, vectors = make_pairs(30)
    with pytest.raises(ValueError, match='duplicate'):
        calibrate_pairs([pairs[0], pairs[0]], config, vectors.__getitem__)
    with pytest.raises(ValueError, match='bool'):
        calibrate_pairs([replace(pairs[0], labels={'primary': 'false'})], config, vectors.__getitem__)
    with pytest.raises(ValueError, match='strictly'):
        calibrate_pairs(pairs, config, vectors.__getitem__, heldout_fraction=0)


def test_llm_labels_plus_small_spotcheck_are_not_a_stage1_human_panel_gate(config):
    pairs, vectors = make_pairs(source='llm')
    initial = calibrate_pairs(pairs, config, vectors.__getitem__)
    assert initial['label_selection_source'] == 'automatic_only'
    assert initial['pixel_config'] is not None and initial['stage1_human_panel_required'] is False
    training_id = initial['training_pair_ids'][0]
    pairs = [replace(pair, spotcheck_labels=dict(pair.labels), labeler_id='fixture-labeler',
                     labeler_revision='fixture-revision') if pair.pair_id == training_id else pair for pair in pairs]
    checked = calibrate_pairs(pairs, config, vectors.__getitem__)
    assert checked['label_selection_source'] == 'human_and_automatic'
    assert checked['human_spotchecked_pair_count'] == 1 and checked['human_labeled_pair_count'] == 1
    assert checked['pixel_config'] == initial['pixel_config']
    assert checked['stage1_human_panel_required'] is False and checked['validated_scoring'] is False


def test_human_spotcheck_overrides_only_its_pair_not_all_automatic_labels(config):
    pairs, vectors = make_pairs(source='automatic')
    original = calibrate_pairs(pairs, config, vectors.__getitem__)
    heldout_id = original['heldout_pair_ids'][0]
    changed = [replace(pair, spotcheck_labels={name: not value for name, value in pair.labels.items()})
               if pair.pair_id == heldout_id else pair for pair in pairs]
    report = calibrate_pairs(changed, config, vectors.__getitem__)
    assert report['pixel_config'] == original['pixel_config']
    metrics = report['resolutions']['primary']['heldout']
    assert metrics['fp_merge'] + metrics['fn_split'] == 1
    assert report['resolutions']['primary']['heldout_human_spotcheck']['n'] == 1


def test_calibration_cli_local_vectors_outputs_provisional_report_without_overwrite(config, tmp_path):
    pairs, vectors = make_pairs()
    pair_file, vector_file, config_file = (tmp_path / filename for filename in ('pairs.json', 'vectors.json', 'config.json'))
    pair_file.write_text(json.dumps([asdict(pair) for pair in pairs]))
    vector_file.write_text(json.dumps(dict(
        embedding_model_id=config.embedding_model_id, embedding_revision=config.embedding_revision,
        input_format=config.input_format, source_kind='synthetic_fixture',
        vectors={embedding_key(pair.scene, caption): vectors[embedding_text(pair.scene, caption)]
                 for pair in pairs for caption in (pair.caption_a, pair.caption_b)})))
    config_file.write_text(json.dumps(asdict(config)))
    output = tmp_path / 'calibration'
    args = ['calibrate', '--pairs', str(pair_file), '--vectors', str(vector_file),
            '--config', str(config_file), '--output-dir', str(output)]
    assert main(args) == 0
    report = json.loads((output / 'pixel_calibration_report.json').read_text())
    assert report['encoder']['source_kind'] == 'synthetic_fixture'
    assert report['encoder']['model_execution_verified'] is False
    assert set(report['input_sha256']) == {'pairs', 'vectors', 'config'}
    assert (output / 'pixel_config.json').exists()
    before = (output / 'pixel_calibration_report.json').read_bytes()
    with pytest.raises(SystemExit):
        main(args)
    assert (output / 'pixel_calibration_report.json').read_bytes() == before


def test_calibration_cli_rejects_vector_provenance_mismatch(config, tmp_path):
    (tmp_path / 'config.json').write_text(json.dumps(asdict(config)))
    (tmp_path / 'pairs.json').write_text('[]')
    (tmp_path / 'vectors.json').write_text(json.dumps(dict(embedding_model_id='other-model')))
    with pytest.raises(SystemExit):
        main(['calibrate', '--pairs', str(tmp_path / 'pairs.json'), '--vectors', str(tmp_path / 'vectors.json'),
              '--config', str(tmp_path / 'config.json'), '--output-dir', str(tmp_path / 'output')])
    assert not (tmp_path / 'output').exists()
