import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('r204_audit', HERE / 'audit.py')
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def remote_namespace():
    bundle = json.loads((HERE / 'R195_HELPERS.json').read_text())
    namespace = {'__name__': 'r204_test'}
    exec(bundle['journal_helpers'], namespace)
    exec((HERE / 'remote.py').read_text(), namespace)
    return namespace


def test_only_authorized_nodes():
    assert set(audit.WRAPPERS) == {'node1', 'node2', 'node4', 'node5'}


def test_request_metadata_does_not_depend_on_checkpoint_size(tmp_path):
    namespace = remote_namespace()
    path = tmp_path / '00000000000000000002.json'
    document = dict(prompt_tokens=12280, messages=[], resume_state={'state': 'x' * 400000},
        schema='R125_TEST', split='TRAIN', segment=4, started_unix=3)
    path.write_text(json.dumps(dict(document=document, index=2, journal_id='test', kind='REQUEST', sha256='a' * 64),
        sort_keys=True, separators=(',', ':')))
    selected = namespace['request_fields'](path)
    assert selected['split'] == 'TRAIN' and selected['prompt_tokens'] == 12280
    assert 'messages' not in selected and 'resume_state' not in selected


def test_large_prompt_metadata_remains_available(tmp_path):
    namespace = remote_namespace()
    path = tmp_path / 'request.json'
    document = dict(messages=[dict(content='word ' * 20000)], prompt_tokens=15000,
        resume_state={'state': 'x' * 400000}, schema='R125_TEST', split='TRAIN', segment=4, started_unix=3)
    path.write_text(json.dumps(dict(document=document, index=2, journal_id='test', kind='REQUEST', sha256='a' * 64),
        sort_keys=True, separators=(',', ':')))
    assert namespace['request_fields'](path)['prompt_tokens'] == 15000


def test_loaded_requires_current_pid_and_incarnation_time():
    namespace = remote_namespace()
    assert namespace['loaded_matches'](dict(pid=44, loaded_unix=101), 44, 100)
    assert not namespace['loaded_matches'](dict(pid=43, loaded_unix=101), 44, 100)
    assert not namespace['loaded_matches'](dict(pid=44, loaded_unix=50), 44, 100)
    assert not namespace['loaded_matches'](dict(pid=44), 44, 100)


def test_no_current_request_or_raw_before_matching_loaded():
    namespace = remote_namespace()
    paths = [Path(f'{index:020d}.json') for index in (5825, 5847, 5848, 5850)]
    assert namespace['incarnation_paths'](paths, None) == []
    assert namespace['incarnation_paths'](paths, dict(reference=dict(index=5848))) == paths[2:]


def test_zero_mtime_cannot_be_a_staleness_measurement():
    namespace = remote_namespace()
    assert namespace['timestamp']({}, dict(mtime_unix=0), 1789702049) == (None, 'UNVERIFIED')
    assert namespace['timestamp'](dict(started_unix=1789702000), dict(mtime_unix=0), 1789702049) == (
        1789702000, 'document.started_unix')


def test_overflow_reason_preserves_counts_not_arbitrary_text():
    namespace = remote_namespace()
    assert namespace['state_reason']('working_state_overflow:2300>2048; explicit_child_revision_or_deletion_required; prior_state_unchanged') == dict(
        consolidation_reason='working_state_overflow', working_state_bytes=2300, working_state_byte_budget=2048)
    assert namespace['state_reason']('untrusted\nprivate=content') == dict(consolidation_reason='UNCLASSIFIED_REASON')


def test_public_raw_hash_verification(tmp_path):
    namespace = remote_namespace()
    record = dict(document={'response': {'raw': 'raw Ａ text'}}, index=3, kind='RESPONSE', journal_id='test')
    record['sha256'] = namespace['digest'](record)
    path = tmp_path / 'record.json'
    path.write_text(json.dumps(record))
    assert namespace['full_record'](path)['document']['response']['raw'] == 'raw Ａ text'
    record['document']['response']['raw'] = 'changed'
    path.write_text(json.dumps(record))
    with pytest.raises(RuntimeError, match='HASH_MISMATCH'):
        namespace['full_record'](path)


def test_scanner_preserves_raw_and_reports_opportunities():
    raw = 'One and The other. Ａ aа 漢字\u3000word  word aWord\u200b'
    metrics = audit.glyphs(raw)
    assert metrics['fullwidth'] == 1
    assert metrics['cjk'] == 2
    assert metrics['mixed_script_words'] == 1
    assert metrics['non_ascii_whitespace'] == 1 and metrics['zero_width'] == 1
    assert metrics['internal_multispace_runs'] == 1
    assert metrics['lowercase_uppercase_joins'] == 1
    assert metrics['capitalization'] == audit.scan_target(raw)
    assert raw.endswith('aWord\u200b')


def test_expired_nodes_make_no_ssh_call():
    with patch.object(audit.subprocess, 'run') as run:
        result = audit.collect_node('node4', {}, {'lives': [{'node': 'node4', 'wall': {'lease_end_unix': 1}}]})
    assert result['native_count'] is None
    run.assert_not_called()


def test_no_evidence_is_not_zero_health():
    result = audit.table({'node1': {'status': 'READOUT_UNVERIFIED', 'lives': []}})
    assert 'READOUT_UNVERIFIED' in result and '| ? |' in result
