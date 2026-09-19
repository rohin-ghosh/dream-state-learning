"""Pure prospective policy composition; no I/O, provider calls, or life control."""

import hashlib


POLICY_ID = 'R233_PAIR_MIXED_PERSISTENT_CANDIDATE_V1'


def policy_binding(brief):
    if not isinstance(brief, str) or not brief.strip():
        raise ValueError('nonempty_parent_policy_required')
    return dict(policy_id=POLICY_ID, brief_sha256=hashlib.sha256(brief.encode()).hexdigest(),
        prospective=True, cadence_changed=False, learning_changed=False,
        sealed_visibility_changed=False, provider_changed=False)


def extend_instruction(original, stage, brief):
    if type(stage) is not int or not 0 <= stage <= 5:
        raise ValueError('existing_stage_required')
    binding = policy_binding(brief)
    return (original + '\n\nProspective paired-parent TRAIN policy; existing response metrics schema stays:\n'
        + brief + '\nPolicy epoch: ' + binding['policy_id'] + '; brief SHA256: ' + binding['brief_sha256']
        + '\nCurrent scheduler stage: ' + str(stage) + '. Keep proposed_stage at ' + str(stage)
        + '; do not change cadence to mix subjects. Assess only the actual supplied child evidence.')


def bind_payload(payload, brief):
    if 'parent_policy_epoch' in payload:
        raise ValueError('new_turn_policy_binding_must_not_overwrite_a_prior_epoch')
    return dict(payload, parent_policy_epoch=policy_binding(brief))
