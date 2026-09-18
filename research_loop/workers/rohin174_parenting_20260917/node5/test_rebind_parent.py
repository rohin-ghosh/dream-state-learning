import hashlib
import types

import pytest

from rebind_parent import eligible_exposure, export_state, pending_render, terminal_parent_receipt
from console_baseline import write


def test_consumed_CPU_failure_is_not_a_withdrawal_or_learner_failure(tmp_path):
    path = tmp_path / 'FAILED_CLOSED.json'
    write(path, dict(error_type='FileExistsError', child_signals=0,
                    error=str(tmp_path / 'parent_000000000148')))
    assert terminal_parent_receipt(tmp_path)['path'] == str(path)


def test_other_failures_are_not_silently_restarted(tmp_path):
    write(tmp_path / 'FAILED_CLOSED.json', dict(error_type='ValueError', child_signals=0, error='different'))
    with pytest.raises(ValueError, match='only_consumed_CPU_parent_failure'):
        terminal_parent_receipt(tmp_path)


def state():
    return dict(journal_id='same-life', response_count=20, request_count=20, delivered={})


def legacy(tmp_path, status='PUBLISHED'):
    directory = tmp_path / 'parent_000001'
    directory.mkdir()
    write(directory / 'SOURCE.json', dict(head_sha256='head', response_count=20, request_count=20))
    publication = dict(id='old-id', sha256='inbox-sha', path='/existing/inbox/old-id.json')
    write(directory / 'RESULT.json', dict(status=status, source_head_sha256='head', source_response_count=20,
        inbox_publication=publication, response=dict(message='Keep the existing turn.')))
    return directory


def test_legacy_pending_transfers_without_claiming_delivery(tmp_path):
    legacy(tmp_path)
    seed, pending = export_state(types.SimpleNamespace(SCHEMA='R166'), tmp_path, state(), {})
    assert seed['attempts'] == []
    assert seed['last_response_count'] == seed['last_request_count'] == 20
    assert pending_render(pending, state()) == ['old-id']


def test_legacy_requires_exact_rendered_bytes(tmp_path):
    legacy(tmp_path)
    unused, pending = export_state(types.SimpleNamespace(SCHEMA='R166'), tmp_path, state(), {})
    current = state()
    current['delivered']['old-id'] = dict(speaker='Astra', inbox_sha256='inbox-sha',
        text_sha256=hashlib.sha256(b'Keep the existing turn.').hexdigest())
    assert pending_render(pending, current) == []
    current['delivered']['old-id']['speaker'] = 'Rohin'
    with pytest.raises(ValueError, match='exact_legacy_render'):
        pending_render(pending, current)


def test_unknown_never_replayed_or_transferred(tmp_path):
    legacy(tmp_path, 'PUBLICATION_UNKNOWN')
    with pytest.raises(ValueError, match='uncertain_legacy_no_replay'):
        export_state(types.SimpleNamespace(SCHEMA='R166'), tmp_path, state(), {})


def test_existing_r175_seed_and_pending_preserved(tmp_path):
    seed = dict(attempts=[dict(old='original')], cursor=27)
    write(tmp_path / 'SEED.json', seed)
    observed = []
    policy = types.SimpleNamespace(export_predecessor=lambda old, current: dict(attempts=[dict(new='pending')]),
        memory=lambda merged, attempts, current: observed.append(merged))
    merged, pending = export_state(policy, tmp_path, state(), {})
    assert merged['attempts'] == [dict(old='original'), dict(new='pending')]
    assert seed == dict(attempts=[dict(old='original')], cursor=27)
    assert merged['cursor'] == 27 and not pending and observed == [merged]


def test_no_legacy_cursor_rewind(tmp_path):
    legacy(tmp_path)
    current = dict(state(), response_count=19)
    with pytest.raises(ValueError, match='no_cursor_rewind'):
        export_state(types.SimpleNamespace(SCHEMA='R166'), tmp_path, current, {})


def test_old_seed_publication_never_starts_new_arm_clock():
    attempt = dict(result=dict(status='PUBLISHED', publication=dict(id='historical')))
    assert not eligible_exposure(attempt, {'new-arm'})
    assert eligible_exposure(attempt, {'historical'})
