import pytest

from gpu import orch_r118_code_final_transfer_completion as completion
from test_orch_r118_code_final_failed_release import fixture


def test_disappeared_pid_completes_same_transaction_without_signal(fixture, tmp_path):
    root, original, old, live = fixture
    final = completion.final
    final.io.write(root / 'TRANSFER_INTENT.json', dict(old_timer={'pid': 2},
        replacement=final.handoff.ref(root / 'REPLACEMENT_ARMED.json')))
    live.remove(2)
    completion.complete(root, clock=lambda: 100, proc=tmp_path / 'proc')
    assert final.io.read(root / 'TRANSFER_COMMITTED.json')['stopped']['additional_signals'] == 0
    assert final.validate_release(root)['fabricated_clean_release'] is False


def test_present_pid_never_waived(fixture, tmp_path):
    root, original, old, live = fixture
    final = completion.final
    final.io.write(root / 'TRANSFER_INTENT.json', dict(old_timer={'pid': 2},
        replacement=final.handoff.ref(root / 'REPLACEMENT_ARMED.json')))
    (tmp_path / 'proc/2').mkdir(parents=True)
    with pytest.raises(ValueError, match='old_pid_fully_absent'):
        completion.complete(root, clock=lambda: 100, proc=tmp_path / 'proc')
    assert not (root / 'TRANSFER_COMMITTED.json').exists()
