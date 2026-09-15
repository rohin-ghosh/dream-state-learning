from gpu.orch_r109_l1_bounded_diagnosis import response_shape


def row(text, family):
    return dict(family=family, stage='draft', response=dict(raw=text, token_ids=[1, 2],
                terminal=True, truncated=False), outcome=dict(correct=True),
                descriptive_response_metrics=dict(marker_found=False,
                post_first_answer_child_tokens=0, persistence=False, cap_hit=False,
                native_marker_alignment_verified=False))


def test_json_expression_is_not_fenced_marker_evidence():
    result = response_shape(row('{"expression":"values[0]"}', 'code'))
    assert result['expression_json'] and not result['marker_found']
    assert not result['persistence']


def test_reasoning_before_final_does_not_become_post_final_persistence():
    result = response_shape(row('Use the given difference: 5 - 2 = 3.\nFINAL: 3', 'math'))
    assert result['math_pre_final_nonempty'] and result['math_first_final_is_last']
    assert not result['persistence']


def test_work_after_answer_is_distinguished():
    result = response_shape(row('FINAL: 3\nCheck another supplied relation.\nFINAL: 3', 'math'))
    assert not result['math_first_final_is_last']
