import pytest
from unittest.mock import patch

from gpu import orch_r158_kernel_nudge_observe as observer


def request(text='Astra: approved text', split='TRAIN', role='user'):
    return dict(kind='REQUEST', index=50, sha256='a' * 64,
                document=dict(split=split, started_unix=123, messages=[dict(role=role, content=text)]))


def test_exact_attributed_rendering_after_registration():
    result = observer.match_record(request(), {}, 'approved text', True)
    assert result['rendered_request']['index'] == 50
    assert result['rendered_request']['exact_attributed_text_in_messages'] is True
    assert 'executed' not in result


@pytest.mark.parametrize('registered,text,role', [
    (False, 'Astra: approved text', 'user'),
    (True, 'approved text', 'user'),
    (True, 'Astra: different text', 'user'),
    (True, 'Astra: approved text', 'assistant'),
])
def test_not_publication_or_unattributed_or_child_echo(registered, text, role):
    assert observer.match_record(request(text=text, role=role), {}, 'approved text', registered) == {}


def test_nontrain_request_stops_before_message_match():
    with pytest.raises(ValueError, match='TRAIN_only_observer'):
        observer.match_record(request(split='HELD'), {}, 'approved text', True)


def test_inbox_requires_identity_text_and_publication_hash():
    publication = dict(id='one', sha256='b' * 64)
    record = dict(kind='INBOX', index=49, sha256='c' * 64, document=dict(
        source_sha256=publication['sha256'], message=dict(id='one', speaker='Astra',
        actor='parent', text='approved text', split='TRAIN')))
    assert observer.match_record(record, publication, 'approved text', False)['registration']['index'] == 49
    record['document']['source_sha256'] = 'd' * 64
    with pytest.raises(ValueError, match='exact_Astra_registration'):
        observer.match_record(record, publication, 'approved text', False)


def test_other_inbox_identity_is_not_delivery():
    record = dict(kind='INBOX', index=49, sha256='c' * 64, document=dict(message=dict(id='other')))
    assert observer.match_record(record, dict(id='one'), 'approved text', False) == {}


def test_phase_initialization_is_not_terminal(tmp_path):
    (tmp_path / 'lane0/phase_02').mkdir(parents=True)
    snapshot = observer.snapshot_service(tmp_path)
    assert snapshot['0']['phase_02'] == dict(initialization_pending=True)


@pytest.mark.parametrize('launched', [False, True])
def test_result_reports_actual_launch_flag_separately(tmp_path, launched):
    phase = tmp_path / 'lane0/phase_01'
    (phase / 'service/call').mkdir(parents=True)
    (phase / 'spool/request').mkdir(parents=True)
    result_path = phase / 'spool/request/RESULT.json'
    observer.service.store(phase / 'service/STATE.json', observer.service.encoded(dict(phase='READY')))
    observer.service.store(result_path, observer.service.encoded(dict(status='REQUEST_REJECTED' if not launched else 'KERNEL_ERROR',
        launch_attempted=launched, origin=dict(child_generated=True), request_id='identity')))
    observer.service.store(phase / 'service/call/BRIDGE_RECEIPT.json', observer.service.encoded(dict(result_path=str(result_path))))
    result = observer.snapshot_service(tmp_path)['0']['phase_01']['results'][0]
    assert result['launch_attempted'] is launched
    assert result['child_generated'] is True
    assert result['request_id'] == 'identity'


def test_mutable_state_atomic_replacement_retries_bounded():
    with patch.object(observer, 'document', side_effect=[ValueError('file_changed_during_read'), dict(phase='READY')]) as read:
        with patch.object(observer.time, 'sleep'):
            assert observer.mutable_state('STATE.json') == dict(phase='READY')
    assert read.call_count == 2


def test_mutable_state_persistent_race_stops_after_three():
    with patch.object(observer, 'document', side_effect=ValueError('file_changed_during_read')) as read:
        with patch.object(observer.time, 'sleep'), pytest.raises(ValueError, match='file_changed_during_read'):
            observer.mutable_state('STATE.json')
    assert read.call_count == 3


def test_other_integrity_error_never_retried():
    with patch.object(observer, 'document', side_effect=ValueError('journal_record_hash')) as read:
        with pytest.raises(ValueError, match='journal_record_hash'):
            observer.mutable_state('STATE.json')
    assert read.call_count == 1


def test_immutable_reads_still_fail_on_race():
    with patch.object(observer.service, 'read', side_effect=ValueError('file_changed_during_read')) as read:
        with pytest.raises(ValueError, match='file_changed_during_read'):
            observer.document('RECEIPT.json')
    assert read.call_count == 1


def test_no_terminal_means_no_lock_probe(tmp_path):
    with patch.object(observer, 'existing_lock_available') as probe:
        assert observer.campaign_closure(tmp_path) is None
    probe.assert_not_called()


def test_lock_probe_never_creates_missing_file(tmp_path):
    missing = tmp_path / 'missing.lock'
    with pytest.raises(FileNotFoundError):
        observer.existing_lock_available(missing)
    assert not missing.exists()


def test_existing_lock_probe_preserves_bytes_and_releases(tmp_path):
    lock = tmp_path / 'existing.lock'
    lock.write_bytes(b'original owner receipt')
    assert observer.existing_lock_available(lock)
    assert observer.existing_lock_available(lock)
    assert lock.read_bytes() == b'original owner receipt'
