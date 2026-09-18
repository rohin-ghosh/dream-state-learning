"""Public deterministic scene assignment, bound to the actual generation request."""


POLICY = 'R226_ROUND_ROBIN_ONE_ACTIVE_SCENE_V1'


def assignment(scenes, opportunity):
    if type(opportunity) is not int or opportunity < 1 or not scenes:
        raise ValueError('positive_opportunity_and_scene_roster')
    number = (opportunity - 1) % len(scenes) + 1
    scene = scenes[number - 1]
    return dict(policy=POLICY, opportunity=opportunity, number=number,
                contest_id=scene['contest_id'], canonical_scene=scene['canonical_scene'])


def prompt(scenes, opportunity):
    active = assignment(scenes, opportunity)
    return (f"This opportunity is for Scene {active['number']}: {active['canonical_scene']}\n"
            'Write the captions themselves for this scene. Bare caption lines or a numbered list '
            'will refer to this assigned scene, not to different scene numbers. No fields, fixed '
            'count, or special output format are required. Questions receive clarification.')


def verified_active_scene(request, scenes):
    policy = request['binding']['plan'].get('scene_schedule')
    if policy is None:
        return None
    if policy != POLICY:
        raise ValueError('unknown_scene_schedule')
    expected = dict(role='user', content=prompt(scenes, request['opportunity']))
    if expected not in request['messages']:
        raise ValueError('assigned_scene_must_have_been_in_actual_model_input')
    return assignment(scenes, request['opportunity'])['contest_id']
