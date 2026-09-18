"""Reduction records exact native tokens without pretending semantics were read."""

import json
from gpu.orch_combined_l1_richness_report import reduce


def test_reduction_keeps_missing_semantics_and_accuracy_separate(tmp_path):
    (tmp_path / 'LOADED.json').write_text(json.dumps(dict(parent_present=False)))
    response = dict(raw='One operation.', token_ids=[1, 2], terminal=True, truncated=False)
    call = dict(position=0, metadata=dict(purpose='math_held', task_id='one'), status='COMPLETE',
        response=response, max_new_tokens=1536, prompt_condition='MINIMAL_DEFAULT')
    (tmp_path / 'CALL_000.json').write_text(json.dumps(call))
    (tmp_path / 'MATH_ROWS.json').write_text(json.dumps([dict(task_id='one', outcome_pass=True)]))
    result = reduce(tmp_path)
    assert result['generated_tokens']['mean'] == 2 and result['eos'] == 1 and result['ceiling'] == 0
    assert result['semantic_unassessed'] == 1 and result['semantic_reviewed'] == 0
    assert result['accuracy_secondary'] == dict(correct=1, completed_denominator=1)
    assert not result['raw_text_included'] and 'One operation.' not in json.dumps(result)
