import pytest

from research_loop.workers.rohin233_ovx4_recovery_20260918.contrast_receiving import TYPES, evaluate, validate_cases


def test_exact_all_case_counts_and_unique_scoring_inputs():
    class Judge:
        max_length=32
        def __init__(self):
            self.inputs=[]
        def token_count(self,scene,caption):
            return 3
        def score(self,rows):
            self.inputs.extend(rows)
            return [2.0 if row['caption']=='synthetic good' else 1.0 for row in rows]
    judge=Judge()
    cases=[dict(scene='synthetic scene',good='synthetic good',contrast='synthetic contrast',
        kind=kind,case_id=kind) for kind in TYPES]
    summary,records=evaluate(judge,cases)
    assert len(judge.inputs)==2
    assert len(records)==6
    assert all(value==dict(scored=1,wins=1,ties=0,losses=0) for value in summary.values())
    with pytest.raises(ValueError):
        validate_cases(cases)
