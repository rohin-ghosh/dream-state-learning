"""Synthetic TRAIN files only; no real verifier, provider, GPU or held content."""

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from gpu import orch_r159_train_capture as capture
from tests.test_orch_r159_train_eligibility import BINDING, make_case, make_reflection_case


def response_index(evidence):
    return json.loads(evidence['records'][1]['raw'])['index']


def assemble(case, **changes):
    options = dict(target_kind=case.packet['target_kind'], label=case.packet['label'],
                   generator_binding=deepcopy(BINDING), excluded_task_ids=[])
    if 'anchor_attempt' in case.packet:
        options['anchor_response_index'] = response_index(case.packet['anchor_attempt'])
    if 'feedback' in case.packet:
        options['feedback_response_index'] = response_index(case.packet['feedback'])
    options.update(changes)
    return capture.assemble(case.root, 0, response_index(case.packet), **options)


@pytest.fixture
def case(tmp_path, monkeypatch):
    return make_case(tmp_path, monkeypatch)


def test_answer_capture_preserves_bytes_and_requires_later_reviews(case, tmp_path, monkeypatch):
    monkeypatch.setattr(capture.eligibility, 'compile_candidate', Mock(side_effect=AssertionError('no premature compile')))
    bundle = assemble(case)
    assert bundle['status'] == 'CAPTURED_UNREVIEWED_NOT_ELIGIBLE'
    assert bundle['packet']['reviews'] == []
    assert bundle['review_template']['sources']['target']['text'] == case.row['target']
    for path, artifact in bundle['artifacts'].items():
        assert artifact['raw'] == Path(path).read_bytes()
        assert bundle['observed_path_hashes'][path] == capture.sha(Path(path).read_bytes())
    assert bundle['budgets']['reads'] == 2 * bundle['budgets']['files']
    written = capture.write_capture(bundle, tmp_path / 'captured')
    loaded = capture.load_packet(tmp_path / 'captured', expected_manifest_sha256=written['sha256'])
    assert loaded == bundle['packet']
    template = json.loads((tmp_path / 'captured/REVIEW_TEMPLATE.json').read_bytes())
    assert template['review_envelope_template']['status'] is None
    assert all(axis['status'] is None and axis['evidence'] == []
               for axis in template['review_envelope_template']['axes'].values())
    assert not template['judgments_generated']


@pytest.mark.parametrize('reflection,feedback', [(False, False), (False, True), (True, False), (True, True)])
def test_exact_compiler_bindings_and_reviewed_integration(tmp_path, monkeypatch, reflection, feedback):
    case = (make_reflection_case(tmp_path, monkeypatch, failed_chain=feedback) if reflection
            else make_case(tmp_path, monkeypatch, feedback=feedback))
    bundle = assemble(case)
    expected = json.loads(case.packet['reviews'][0]['raw'])['binding']
    assert bundle['review_template']['review_envelope_template']['binding'] == expected
    for name, source in bundle['review_template']['sources'].items():
        span = source['full_source_span']
        assert source['text'][span['start']:span['end']] == span['quote']
        assert span['source'] == name
    trusted = dict(bundle['observed_path_hashes'], **case.trusted)
    result = capture.compile_reviewed(bundle['packet'], case.packet['reviews'], trusted_artifacts=trusted,
        reviewer_provenance=case.reviewers, generator_binding=BINDING, excluded_task_ids=[])
    assert result['status'] == 'PASS', result['reasons']
    assert result['row'] == case.row
    if reflection:
        assert 'result' not in bundle['packet'] and 'intent' not in bundle['packet']
        assert result['reflection_truth_verified'] is False


def test_compilation_never_defaults_to_observed_trust(case):
    bundle = assemble(case)
    result = capture.compile_reviewed(bundle['packet'], case.packet['reviews'], trusted_artifacts={},
        reviewer_provenance=case.reviewers, generator_binding=BINDING, excluded_task_ids=[])
    assert not result['eligible']
    assert any('external_pin_missing' in item['code'] for item in result['reasons'])
    with pytest.raises(ValueError, match='supplied_review_envelopes'):
        capture.compile_reviewed(bundle['packet'], [], trusted_artifacts=bundle['observed_path_hashes'],
            reviewer_provenance={}, generator_binding=BINDING, excluded_task_ids=[])


def test_capture_does_not_open_writer_or_invoke_collection(case, monkeypatch):
    before = {str(path): path.read_bytes() for path in case.root.rglob('*') if path.is_file()}
    actual = capture.Reader.read
    paths = []
    def tracked(reader, path):
        paths.append(str(path))
        return actual(reader, path)
    monkeypatch.setattr(capture.Reader, 'read', tracked)
    assemble(case)
    assert all(count == 2 for count in Counter(paths).values())
    assert not any('WRITER.lock' in path for path in paths)
    assert before == {str(path): path.read_bytes() for path in case.root.rglob('*') if path.is_file()}


@pytest.mark.parametrize('options', [dict(terminal=False), dict(terminal=False, truncated=True)])
def test_incomplete_candidate_refused(tmp_path, monkeypatch, options):
    case = make_case(tmp_path, monkeypatch, target='Answer: 4\n', **options)
    with pytest.raises(ValueError, match='complete_nontruncated'):
        assemble(case)


def test_capped_earlier_attempt_is_not_silently_admitted(tmp_path, monkeypatch):
    case = make_case(tmp_path, monkeypatch, feedback=True, earlier_capped=True)
    with pytest.raises(ValueError, match='complete_nontruncated'):
        assemble(case)


def test_missing_commit_is_not_captured(case):
    Path(case.packet['records'][2]['path']).unlink()
    with pytest.raises(FileNotFoundError):
        assemble(case)


def replace_json(path, change):
    path = Path(path)
    value = json.loads(path.read_bytes())
    change(value)
    path.chmod(0o600)
    path.write_bytes(capture.encoded(value))


def test_tampered_response_refused(case):
    replace_json(case.packet['records'][1]['path'], lambda value: value['document']['response'].update(raw='Answer: 9'))
    with pytest.raises(ValueError):
        assemble(case)


def test_task_exposure_requires_real_rendering(case):
    replace_json(case.packet['records'][0]['path'], lambda value: value['document'].update(messages=[]))
    with pytest.raises(ValueError):
        assemble(case)


def test_publication_cannot_redirect_reader(case, monkeypatch):
    path = Path(case.packet['task_publication']['path'])
    replace_json(path, lambda value: value.update(path='/forbidden/private.json'))
    with pytest.raises(ValueError, match='publication_path_outside_exact_inbox'):
        assemble(case)


def test_symlink_file_refused(case, tmp_path):
    path = Path(case.packet['task']['path'])
    other = tmp_path / 'original.json'
    path.rename(other)
    path.symlink_to(other)
    with pytest.raises(OSError):
        assemble(case)


def test_symlink_parent_refused(case, tmp_path):
    directory = case.root / 'train_environment'
    directory.rename(tmp_path / 'environment')
    directory.symlink_to(tmp_path / 'environment', target_is_directory=True)
    with pytest.raises(OSError):
        assemble(case)


@pytest.mark.parametrize('component', ['held', 'heldout', 'readout32', 'sealed-data', 'eval', 'evaluation', 'final'])
def test_forbidden_paths_rejected_before_open(component, monkeypatch):
    monkeypatch.setattr(capture.gym.console, '_directory', Mock(side_effect=AssertionError('must reject before open')))
    path = f'/tmp/{component}/orch_r158_test/parented_learning'
    with pytest.raises(ValueError, match='held_or_evaluation_path'):
        capture.assemble(path, 0, 2, target_kind='ANSWER', label='grounded_reasoning',
                         generator_binding=BINDING, excluded_task_ids=[])


def test_nontrain_request_refused_before_response_read(case, monkeypatch):
    request_path = case.packet['records'][0]['path']
    replace_json(request_path, lambda value: value['document'].update(split='OTHER'))
    actual = capture.Reader.read
    def restricted(reader, path):
        assert str(path) != case.packet['records'][1]['path']
        return actual(reader, path)
    monkeypatch.setattr(capture.Reader, 'read', restricted)
    with pytest.raises(ValueError, match='TRAIN_request_required'):
        assemble(case)


def test_external_generator_and_exclusions_required(case):
    with pytest.raises(ValueError, match='caller_generator_authority_mismatch'):
        assemble(case, generator_binding=dict(BINDING, package_source_sha256='c' * 64))
    with pytest.raises(ValueError, match='caller_excluded_task'):
        assemble(case, excluded_task_ids=[capture.gym.task_id(0)])


def test_no_implicit_anchor_or_feedback_discovery(case):
    with pytest.raises(ValueError, match='explicit_reflection_anchor_only'):
        assemble(case, target_kind='POST_FEEDBACK_REFLECTION')
    with pytest.raises(ValueError, match='explicit_feedback_chain_only'):
        assemble(case, label='feedback_use')
    with pytest.raises(ValueError, match='explicit_reflection_anchor_only'):
        assemble(case, anchor_response_index=1)


@pytest.mark.parametrize('limits,reason', [
    (capture.Limits(max_files=1), 'capture_file_budget'),
    (capture.Limits(max_file_bytes=1), 'capture_file_byte_budget'),
    (capture.Limits(max_read_bytes=1), 'capture_total_read_budget'),
])
def test_read_budgets_fail_closed(case, limits, reason):
    with pytest.raises(ValueError, match=reason):
        assemble(case, limits=limits)


def test_output_budget_checked_before_creation(case, tmp_path):
    bundle = assemble(case, limits=capture.Limits(max_output_bytes=1))
    destination = tmp_path / 'capture'
    with pytest.raises(ValueError, match='capture_output_byte_budget'):
        capture.write_capture(bundle, destination)
    assert not destination.exists()


def test_original_live_life_is_never_output(case):
    with pytest.raises(ValueError, match='capture_output_outside_live_life'):
        capture.write_capture(assemble(case), case.root / 'new_capture')


def test_output_create_only_and_external_manifest_pin(case, tmp_path):
    bundle = assemble(case)
    destination = tmp_path / 'capture'
    receipt = capture.write_capture(bundle, destination)
    with pytest.raises(FileExistsError):
        capture.write_capture(bundle, destination)
    with pytest.raises(ValueError, match='externally_pinned'):
        capture.load_packet(destination, expected_manifest_sha256='0' * 64)
    blob = destination / (bundle['packet']['task']['sha256'] + '.bin')
    blob.chmod(0o600)
    blob.write_bytes(b'{}')
    with pytest.raises(ValueError, match='captured_bundle_file_hash'):
        capture.load_packet(destination, expected_manifest_sha256=receipt['sha256'])


def test_independent_second_pass_detects_replacement(case, monkeypatch):
    actual = capture.Reader.read
    counts = Counter()
    task_path = case.packet['task']['path']
    def changed(reader, path):
        raw, identity = actual(reader, path)
        counts[str(path)] += 1
        if str(path) == task_path and counts[str(path)] == 2:
            return raw + b' ', identity
        return raw, identity
    monkeypatch.setattr(capture.Reader, 'read', changed)
    with pytest.raises(ValueError, match='capture_changed_between_passes'):
        assemble(case)


@pytest.mark.parametrize('raw', [b'{"a":1,"a":2}', b'{"a":NaN}', b'[]'])
def test_ambiguous_json_refused(raw):
    with pytest.raises(ValueError):
        capture.decode(raw)


def test_loaded_helper_schema_metadata_is_cpu_only():
    metadata = capture.integration()
    assert metadata['compiler_schema'] == capture.eligibility.SCHEMA
    assert metadata['review_schema'] == capture.eligibility.REVIEW_SCHEMA
    assert not metadata['dataset_loaded']
    for module in metadata['modules'].values():
        assert module['sha256'] == capture.sha(Path(module['path']).read_bytes())


def test_template_is_not_accepted_as_a_completed_review(case, monkeypatch):
    bundle = assemble(case)
    blank = capture.eligibility.capture('/tmp/blank_review.json',
        capture.encoded(bundle['review_template']['review_envelope_template']))
    monkeypatch.setattr(capture.eligibility, 'compile_candidate', Mock(side_effect=AssertionError('no template compilation')))
    with pytest.raises(ValueError, match='completed_review_not_blank_template'):
        capture.compile_reviewed(bundle['packet'], [blank, blank], trusted_artifacts={},
            reviewer_provenance=case.reviewers, generator_binding=BINDING, excluded_task_ids=[])


def test_missing_result_publication_is_not_synthesized(case):
    Path(case.result_publication['path']).unlink()
    with pytest.raises(FileNotFoundError):
        assemble(case)


def test_publication_intent_is_required_and_bound(case):
    path = Path(case.result_publication['path']).parent / 'PUBLICATION_INTENT.json'
    replace_json(path, lambda value: value.update(replay_allowed=True))
    with pytest.raises(ValueError, match='publication_intent_join'):
        assemble(case)


def test_nonregular_capture_file_is_rejected_without_waiting(tmp_path):
    path = tmp_path / 'pipe'
    capture.os.mkfifo(path)
    with pytest.raises(ValueError, match='regular_capture_file'):
        capture.Reader(capture.Limits()).read(path)


def test_invalid_limits_are_not_a_budget_bypass():
    for options in (dict(max_files=True), dict(max_read_bytes=0), dict(max_file_bytes=2**40)):
        with pytest.raises(ValueError):
            capture.Limits(**options)


def test_unjudged_capture_retains_rejected_answer_without_claiming_eligibility(tmp_path, monkeypatch):
    case = make_case(tmp_path, monkeypatch, target='I counted one pair.\nAnswer: 2')
    bundle = assemble(case)
    assert json.loads(bundle['packet']['result']['raw'])['accepted'] is False
    assert bundle['status'] == 'CAPTURED_UNREVIEWED_NOT_ELIGIBLE'
    assert bundle['review_template']['sources']['target']['text'] == case.row['target']


def test_capture_cli_roundtrip_without_collection(case, tmp_path, monkeypatch, capsys):
    authority = tmp_path / 'authority.json'
    authority.write_bytes(capture.encoded(dict(generator_binding=BINDING, excluded_task_ids=[])))
    destination = tmp_path / 'captured_cli'
    monkeypatch.setattr(capture, 'compile_reviewed', Mock(side_effect=AssertionError('capture cannot compile')))
    monkeypatch.setattr('sys.argv', ['capture', 'capture', '--root', str(case.root), '--task-index', '0',
        '--response-index', str(response_index(case.packet)), '--target-kind', 'ANSWER',
        '--label', 'grounded_reasoning', '--authority', str(authority), '--output', str(destination)])
    capture.main()
    receipt = json.loads(capsys.readouterr().out)
    packet = capture.load_packet(destination, expected_manifest_sha256=receipt['sha256'])
    assert packet['records'] == case.packet['records']


def test_kernel_service_root_is_not_a_matched_gym_life():
    with pytest.raises(ValueError, match='exact_R158_matched_life'):
        capture.assemble('/tmp/orch_r158_kernel_execution/run1', 0, 2, target_kind='ANSWER',
                         label='grounded_reasoning', generator_binding=BINDING, excluded_task_ids=[])


def test_unicode_span_units_preserve_original_target(tmp_path, monkeypatch):
    from tests.test_orch_r159_train_eligibility import TARGET
    case = make_case(tmp_path, monkeypatch, target='β 🌱\n' + TARGET)
    source = assemble(case)['review_template']['sources']['target']
    assert source['text'] == 'β 🌱\n' + TARGET
    assert source['full_source_span']['end'] == len(source['text'])
    assert source['full_source_span']['end'] < len(source['text'].encode('utf-8'))
