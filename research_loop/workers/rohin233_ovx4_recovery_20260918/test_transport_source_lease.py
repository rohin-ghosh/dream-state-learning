import datetime
import pytest

from research_loop.workers.rohin233_ovx4_recovery_20260918.cap_endpoint_transports import safe_end


def test_endpoint_horizons_follow_destination_not_shared_scorer():
    for group,day in [('node2',20),('node3',24)]:
        end=datetime.datetime.fromtimestamp(safe_end(group),datetime.timezone.utc)
        assert end==datetime.datetime(2026,9,day,17,59,20,tzinfo=datetime.timezone.utc)
        assert safe_end(group)+5<datetime.datetime(2026,9,day,18,tzinfo=datetime.timezone.utc).timestamp()
    assert safe_end('node2')<safe_end('node3')<1790791170
    with pytest.raises(KeyError):
        safe_end('ovx4')
