from research_loop.workers.rohin233_ovx4_recovery_20260918 import support_census as subject


def test_timeout_seconds_are_not_kill_grace():
    assert subject.duration(['timeout','--signal=TERM','--kill-after=5','123','ssh']) == 123
    assert subject.duration(['timeout','--kill-after=5','2h','ssh']) == 7200
    assert subject.duration(['python3','123']) is None


def test_live_census_does_not_disclose_command_arguments():
    row = subject.observe('self',subject.os.getpid(),'operator_vm')
    assert row['alive'] and row['start_ticks'] > 0
    assert 'args' not in row
    assert len(row['command_sha256']) == 64


def test_systemd_deadline_units():
    assert subject.systemd_duration('1w 5d 16min 14s') == 1037774
    assert subject.systemd_duration('infinity') is None
