"""Offline continuation gates; no launch, signals, epoch creation or migration."""

from pathlib import Path

from .contract import byte_digest, canonical, decode, digest, is_sha, require


FROZEN = ('deadline_unix', 'judge_epoch_sha256', 'epoch_binding_sha256', 'weights',
    'reference_panels', 'judge_configuration', 'ledger_files', 'custody_files', 'queued_requests')


def gate(previous, candidate):
    from research_loop.workers.rohin233_ovx4_recovery_20260918.recovery_contract import restore_contract
    require(previous['admission_closed'] is True and previous['inflight'] == 0, 'explicit_drain_not_process_silence')
    require(candidate['admission_closed'] is True and candidate['inflight'] == 0, 'candidate_not_serving_during_restore')
    require(set(previous['sessions']) == set(candidate['sessions']), 'same_complete_session_set')
    for field in FROZEN:
        require(canonical(previous[field]) == canonical(candidate[field]), 'unchanged_' + field)
    evidence = {identifier:restore_contract(state, candidate['sessions'][identifier])
        for identifier,state in previous['sessions'].items()}
    require(is_sha(previous['transport_epoch']) and is_sha(candidate['transport_epoch'])
        and previous['transport_epoch'] != candidate['transport_epoch'], 'explicit_new_transport_epoch')
    require(is_sha(candidate['source_manifest_sha256']) and is_sha(previous['source_manifest_sha256'])
        and candidate['source_manifest_sha256'] != previous['source_manifest_sha256'], 'explicit_source_changing_continuation')
    require(all(item['disposition'] in ('PREPARED_NEVER_DISPATCHED', 'COMPLETE', 'UNKNOWN_NO_REPLAY', 'NO_JUDGMENT_EXPIRED')
        for item in candidate['queued_requests']), 'every_pending_request_explicitly_disposed')
    return dict(status='OFFLINE_CONTINUATION_GATE_ONLY_NOT_DEPLOYED', sessions=evidence,
        previous_sha256=digest(previous), candidate_sha256=digest(candidate), replay_authorized=False)


def reattach_existing_epoch(session, root, expected_files, expected_epoch):
    from research_loop.workers.rohin233_ovx4_recovery_20260918.judge_epoch import EpochLedger
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), 'existing_original_epoch_directory')
    actual = {path.name:byte_digest(path.read_bytes()) for path in root.iterdir() if path.is_file() and not path.is_symlink()}
    require(actual == expected_files and all(path.is_file() and not path.is_symlink() for path in root.iterdir()),
        'complete_original_epoch_file_set')
    binding = decode((root/'BINDING.json').read_bytes())
    require(digest(binding) == expected_epoch, 'original_epoch_binding_not_new_handoff_hash')
    session.epoch_ledger = EpochLedger(root, binding)
    require(session.epoch_ledger.epoch_sha256 == expected_epoch, 'same_original_epoch')
    return session.epoch_ledger
