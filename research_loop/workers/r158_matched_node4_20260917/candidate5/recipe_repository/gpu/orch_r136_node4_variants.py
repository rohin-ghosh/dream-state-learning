"""Truthful new-life startup/plan variants for node4 slots3/6/7 only."""

from copy import deepcopy

from gpu.orch_r136_node4_launch import bind_startup, life_spec, require
from organism_v6.orch_r125_continual_stream import PRESLEEP_INVITATIONS


def variant_plan(template, physical):
    require(type(physical) is int and physical in (3,6,7), 'only_seed_or_replay_variant_slots')
    spec = life_spec(physical, variants_ready=True)
    result = deepcopy(template)
    result.update(seed=spec['seed'], presleep_variant=spec['replay'],
                  compaction_invitation=PRESLEEP_INVITATIONS[spec['replay']])
    return result


def variant_startup(original, physical, branch, source):
    require(type(physical) is int and physical in (3,6,7), 'only_seed_or_replay_variant_slots')
    text = bind_startup(original, life_spec(physical, variants_ready=True), branch, source)
    original_sleep = 'After two generated segments, the runtime invites you to distill what you want to retain in a third segment, then sleeps.'
    original_compaction = 'At sleep your nonempty distillation replaces the earlier visible history with your own summary.'
    if physical == 6:
        sleep = ('After two generated segments, the runtime invites you to re-read your visible history '
                 'and copy the passages you want to retain in a third segment, then sleeps. '
                 'This is a prompt-guided selection, not a machine-verified verbatim extraction.')
        compaction = 'At sleep your nonempty selection replaces the earlier visible history with that selected text.'
    elif physical == 7:
        sleep = ('After two generated segments, the runtime sleeps directly. This branch has no '
                 'pre-sleep distillation generation and does not compact the history at sleep.')
        compaction = ('At sleep the existing visible history is retained subject to the usual '
                      'bounded-context eviction; there is no new summary replacing it.')
    else:
        return text
    for before, after in ((original_sleep,sleep),(original_compaction,compaction)):
        require(text.count(before) == 1, 'exact_default_learning_description')
        text = text.replace(before,after,1)
    return text
