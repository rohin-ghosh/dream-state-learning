import hashlib
import json
from pathlib import Path
import time

import pytest

from gpu import orch_r136_node4_parent as adapter


@pytest.fixture
def config(tmp_path):
    programme = tmp_path/'programme.md'
    programme.write_text('Kernel experimental coach, only committed TRAIN.')
    prefix = '/localhome/local-rohing/orch_r136_kernel_parented_a40r4_20260916_attempt1'
    return dict(schema='R133_PROGRAMME_PARENT_V1', node='a40r', physical=4,
        programme='kernel', branch='kernel4', root=prefix+'/run1', source_root=prefix+'/source1',
        cadence_responses=2, cadence_label='SPARSE', parent_style='experimental-coach',
        programme_path=str(programme), principles_path=str(programme),
        programme_sha256=hashlib.sha256(programme.read_bytes()).hexdigest(),
        principles_sha256=hashlib.sha256(programme.read_bytes()).hexdigest(),
        parent_module_sha256=hashlib.sha256(Path(adapter.parent.__file__).read_bytes()).hexdigest(),
        hard_end_unix=time.time()+600)


def test_exact_kernel4_adapter_does_not_edit_shared_parent_file(config):
    before = Path(adapter.parent.__file__).read_bytes()
    assert adapter.validate(config) == config
    assert Path(adapter.parent.__file__).read_bytes() == before


@pytest.mark.parametrize('physical', [0,1,2,5,6,7,True,'4'])
def test_protected_unparented_and_wrong_slots_rejected(config, physical):
    with pytest.raises(ValueError, match='only_owned'):
        adapter.validate(dict(config, physical=physical))


@pytest.mark.parametrize('patch', [{'cadence_responses':1}, {'cadence_label':'PERSISTENT'},
    {'parent_style':'corrective'}, {'root':'/localhome/local-rohing/other/run1'}])
def test_mismatched_style_or_branch_rejected(config, patch):
    with pytest.raises(ValueError, match='exact_R137'):
        adapter.validate(dict(config, **patch))


def test_parent_module_drift_rejected(config):
    with pytest.raises(ValueError, match='pinned_parent_module'):
        adapter.validate(dict(config, parent_module_sha256='0'*64))


def test_raw3_contained_source_relocation_preserves_programme(config):
    prefix = '/localhome/local-rohing/orch_r136_raw_parented_seed1_a40r3_20260916_attempt1'
    candidate = dict(config, physical=3, programme='raw_parented', cadence_responses=3,
                     parent_style='Socratic', root=prefix+'/run1', source_root=prefix+'/source2')
    assert adapter.validate(candidate) == candidate
    with pytest.raises(ValueError, match='exact_R137'):
        adapter.validate(dict(candidate, source_root=prefix+'/source3'))


def test_kernel4_source_is_not_relocated(config):
    with pytest.raises(ValueError, match='exact_R137'):
        adapter.validate(dict(config, source_root=config['source_root'].replace('/source1', '/source2')))


@pytest.mark.parametrize('message', ['What evidence changed?', 'Compare “first” with “second”.', 'A naïve explanation is not evidence.'])
def test_English_prose_and_punctuation_are_accepted(message):
    adapter.require_english_message(message)


@pytest.mark.parametrize('message', ['你有什么证据？', 'English with 中文 quoted.', 'Какие доказательства?', ''])
def test_nonLatin_or_empty_parent_message_is_rejected(message):
    with pytest.raises(ValueError):
        adapter.require_english_message(message)


def test_English_policy_is_raw3_only(config):
    with pytest.raises(ValueError, match='exact_raw3_English'):
        adapter.validate(dict(config, parent_language='English', language_phase='R140_RAW3_ENGLISH_PARENT_V1'))


def test_rejected_parent_message_never_publishes_and_raw_result_is_preserved(config, tmp_path, monkeypatch):
    prefix = '/localhome/local-rohing/orch_r136_raw_parented_seed1_a40r3_20260916_attempt1'
    programme = Path(config['programme_path'])
    programme.write_text(adapter.ENGLISH_POLICY)
    digest = hashlib.sha256(programme.read_bytes()).hexdigest()
    config.update(physical=3, programme='raw_parented', cadence_responses=3, parent_style='Socratic',
        root=prefix+'/run1', source_root=prefix+'/source2', programme_sha256=digest, principles_sha256=digest,
        parent_language='English', language_phase='R140_RAW3_ENGLISH_PARENT_V1')
    path = tmp_path/'config.json'
    path.write_text(json.dumps(config))
    state = dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', response_count=3, request_count=3,
        record_count=9, head_sha256='a'*64, events=[], consumed_inbox={})
    response = dict(speak=True, message='你有什么证据？', rationale='Evidence check.')
    monkeypatch.setattr(adapter.parent, 'snapshot', lambda *args: state)
    if hasattr(adapter.parent, 'transport_preflight'):
        monkeypatch.setattr(adapter.parent, 'transport_preflight', lambda *args: {'passed': True})
    monkeypatch.setattr(adapter.parent, 'strong', lambda *args, **kwargs: (response, 'test-model', {}))
    calls = []
    publish = lambda *args: calls.append(args)
    monkeypatch.setattr(adapter.parent, 'publish', publish)
    adapter.serve(path, tmp_path, tmp_path/'output', once=True)
    result = json.loads((tmp_path/'output/parent_000000/RESULT.json').read_text())
    assert result['status'] == 'MISSING' and result['response'] == response and result['retry'] is False
    assert not calls and adapter.parent.publish is publish


def test_Latin_script_guard_does_not_claim_language_classification():
    adapter.require_english_message('Bonjour tout le monde.')
    assert 'not a complete English-language classifier' in adapter.ENGLISH_POLICY
