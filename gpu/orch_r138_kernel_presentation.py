"""Permit pending-sleep recovery only when presentation remains identical."""

from organism_v6.orch_r125_continual_stream import require


def verify_recovery_presentation(stream, plan, recovering):
    if not recovering:
        return
    expected = dict(version=plan['presentation_version'], system_prompt=plan['system_prompt'],
                    birth_prompt=plan['birth_prompt'])
    require(stream.presentation == expected and stream.context_limit == plan['context_limit'],
            'recovery_must_preserve_existing_presentation')
