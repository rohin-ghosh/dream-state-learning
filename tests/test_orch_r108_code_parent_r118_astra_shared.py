from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r108_code_parent_r118_astra_shared as broker


def test_only_own_old_terminal_redirected_all_queue_paths_unchanged():
    assert broker.terminal_path(broker.ROOT/'TERMINAL.json')==broker.ROOT/'SHARED_TERMINAL.json'
    for path in [broker.ROOT/'parent_queue/OLD.response.json',broker.ROOT/'SHARED_TERMINAL.json',
        Path('/foreign/TERMINAL.json')]:
        assert broker.terminal_path(path)==path


def test_actual_main_adoption_gate_before_any_serving():
    class Store:
        def hash(self,path):return 'a'*64
        def shell(self,script):return SimpleNamespace(stdout='BOUND_MAIN_ADOPTION\n')

    config=dict(remote_root=str(broker.ROOT))
    launch=dict(shared_activation=dict(path=str(broker.ROOT/'SHARED_ACTIVATION.json'),sha256='a'*64))
    broker.verify_gate(Store(),config,launch)
    launch['shared_activation']['sha256']='b'*64
    with pytest.raises(ValueError,match='actual_shared_activation'):
        broker.verify_gate(Store(),config,launch)


def test_foreign_lane_and_missing_adoption_never_gain_terminal_override():
    with pytest.raises(ValueError,match='own_A3'):
        broker.verify_gate(None,dict(remote_root='/foreign'),{})
    with pytest.raises(KeyError):
        broker.verify_gate(None,dict(remote_root=str(broker.ROOT)),{})
