from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from gpu import orch_math_feedback_uptake_r124_readout as readout
from gpu import orch_r125_a2_boundary_resume as recovery


@pytest.mark.parametrize('artifact', ['sealed', 'offloads'])
def test_repeated_final_is_noop_before_any_model_movement(tmp_path, artifact):
    key = 'R121_SEP16_0600_FINAL8'
    path = tmp_path/artifact/(key+'.json' if artifact == 'offloads' else key)
    path.parent.mkdir()
    path.write_text('preserved receipt')
    actor = Mock()
    before = path.read_bytes()
    result = readout.offloaded_readout(tmp_path, actor, {}, {}, key, 'FINAL')
    assert result['status'] == 'EXISTING_ATTEMPT_NEVER_RETRIED'
    assert actor.mock_calls == [] and path.read_bytes() == before


def test_unattempted_readout_still_executes_and_restores(tmp_path):
    actor = Mock()
    actor.loaded.optimizer.state = {}
    actor.torch.cuda.memory_allocated.return_value = 0
    actor.torch.cuda.memory_reserved.return_value = 0
    with patch.object(readout.old, 'fresh_readout', return_value={'status':'COMPLETE'}) as fresh, \
         patch.object(readout.native, 'observe_adapter', return_value=actor.loaded.observed):
        assert readout.offloaded_readout(tmp_path, actor, {}, {}, 'DEV_C000053')['status'] == 'COMPLETE'
    fresh.assert_called_once()
    assert actor.model.to.call_args_list[0].args == ('cpu',)
    assert actor.model.to.call_args_list[-1].args == ('cuda:0',)


def test_resume_plan_changes_only_saved_frontiers_and_carry():
    plan = dict(root='same_life', original_root='same_queue', bounds={'wall':123}, parent_models=['astra'],
        seed=0, initial_history='old', initial_carry='old', contract={'new_presentations':16,
        'episodes_per_sleep':2, 'anchor_loss_weight':.25})
    before = deepcopy(plan)
    counters = dict(optimizer_steps=21639, native=1274, parent=128)
    resumed = recovery.continuation_plan(plan, {'checkpoint':'C52'}, counters, 'history', 'carry', 52)
    assert plan == before
    for key in ('root','original_root','bounds','parent_models','seed'):
        assert resumed[key] == plan[key]
    assert resumed['contract']['next_cycle'] == 53
    assert resumed['contract']['initial_optimizer_steps'] == 21639
    assert resumed['contract']['inherited_counters'] == counters
    assert resumed['contract']['optimizer_reset'] is False


def test_startup_collision_redirect_does_not_redirect_new_cycle_evidence():
    with patch.object(recovery.run, 'write') as write:
        recovery.relocated_write(recovery.ROOT/'LOADED.json', {'new':True})
        assert write.call_args.args[0] == recovery.SERVICE/'LOADED.json'
        recovery.relocated_write(recovery.ROOT/'cycle000053/ROWS.json', {'new':True})
        assert write.call_args.args[0] == recovery.ROOT/'cycle000053/ROWS.json'
        recovery.relocated_write(recovery.ROOT/'TERMINAL.json', {'new':True})
        assert write.call_args.args[0] == recovery.SERVICE/'TERMINAL.json'
