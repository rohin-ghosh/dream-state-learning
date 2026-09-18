"""CPU custody of completed CODE FINAL evidence, never an evaluator or timer."""

from gpu import orch_r119_code_continuation as custody


ROLE = 'COMPLETED_FINAL_CUSTODIAN_NO_EVALUATION'


def evidence(pointers, native_identity, custodian_identity, runtime_reference):
    complete = custody.checked(pointers['final_completed'])
    terminal = custody.checked(pointers['final_terminal'])
    custody.require(complete['native_calls'] == complete['completed_calls'] == 8,
        'original_eight_FINAL_calls_complete')
    custody.require(terminal['returncode'] == 0, 'original_FINAL_terminal_success')
    custody.require(pointers['final_repeat_allowed'] is False, 'no_FINAL_repeat_authority')
    return dict(role=ROLE, branch=pointers['branch'], root=pointers['root'],
        native_identity=native_identity, custodian_identity=custodian_identity,
        completed_final=dict(complete=pointers['final_completed'], terminal=pointers['final_terminal'],
            evaluator_identity=pointers['final_identity']),
        runtime=runtime_reference, evaluator_calls=0, model_calls=0, provider_calls=0,
        is_evaluator=False, is_timer=False, may_dispatch=False, quota_delta=0)


def binding(document_reference, native_identity, live_identity):
    document = custody.checked(document_reference)
    custody.require(document['role'] == ROLE and document['native_identity'] == native_identity,
        'truthful_completed_FINAL_custodian')
    custody.require(document['evaluator_calls'] == document['model_calls']
        == document['provider_calls'] == document['quota_delta'] == 0
        and document['is_evaluator'] is False and document['is_timer'] is False
        and document['may_dispatch'] is False, 'no_evaluation_or_quota_extension')
    complete = custody.checked(document['completed_final']['complete'])
    terminal = custody.checked(document['completed_final']['terminal'])
    custody.require(complete['native_calls'] == complete['completed_calls'] == 8
        and terminal['returncode'] == 0, 'original_FINAL_evidence_still_exact')
    live_identity(document['custodian_identity'])
    return dict(identity=document['custodian_identity'], evidence=document_reference)
