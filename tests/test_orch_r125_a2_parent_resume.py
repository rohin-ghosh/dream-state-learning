from gpu import orch_r125_a2_parent_resume as repair
from gpu import orch_r137_math_request_repair as previous


def test_current_runtime_liveness_replaces_only_historical_terminal_test():
    source = repair.remote_source(previous.REMOTE)
    compile(source, '<snapshot>', 'exec')
    assert "terminal=not live" in source
    assert "runtime_recovery7" in source
    assert "sha(process/'cmdline')==identity['command_sha256']" in source
    assert "assert sha(root/'PLAN.json')==PLAN_VALUE" in source
    assert "unfinished_claims=unfinished" in source


def test_epoch_accepts_only_unserved_requests_after_exact_C52_resume():
    document = dict(resumed_unix=100, resumed_pid=42, host_sha256='node', requests=[
        dict(id='old', reservation={'first':128}), dict(id='unreserved', reservation=None),
        dict(id='new', reservation={'first':129})])
    boundary = repair.epoch(document)
    row = dict(id='R121_C000053_E0_experience', response=False, partial=False, claim=False, delivered=False,
        reservation=dict(first=129,count=1,reserved_unix=101))
    assert previous.eligible(row, boundary)
    for key in ('response','partial','claim','delivered'):
        assert not previous.eligible(dict(row, **{key:True}), boundary)
    assert not previous.eligible(dict(row, reservation=dict(first=128,count=1,reserved_unix=101)), boundary)
    assert not previous.eligible(dict(row, reservation=dict(first=129,count=1,reserved_unix=99)), boundary)
