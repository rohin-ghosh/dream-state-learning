"""In-memory execution of the full bound null roster, not scientific admission.

Callers supply held fixtures, counters and seed master. Outputs retain every
null action and schedule trace without reseeding, selection or repair. Passing
these thresholds on synthetic inputs does not validate a canonical material
root, tokenizer, model or learned behavior.
"""

from dataclasses import dataclass
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_nulls as nulls
from organism_v6 import composition_birth_stage2a_rollout as rollout
from organism_v6 import composition_birth_stage2a_scoring as scoring


STATUS = "PARTIAL_SOURCE_ONLY"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(nulls.SCIENCE_GATES, False))


@dataclass(frozen=True)
class NullPairResult:
    world: str
    actions: tuple[bytes, bytes]
    score: scoring.InterventionPairScore


@dataclass(frozen=True)
class OneTurnAudit:
    names: tuple[str, ...]
    pairs: tuple[NullPairResult, ...]
    pair_both_counts: tuple[tuple[str, int], ...]
    within_bound: bool


@dataclass(frozen=True)
class ScheduleWorldResult:
    world: str
    runs: tuple[rollout.ChainRun, rollout.ChainRun]
    score: scoring.ChainPairScore


@dataclass(frozen=True)
class ScheduleAudit:
    name: str
    worlds: tuple[ScheduleWorldResult, ...]
    whole_chain_count: int
    twin_both_count: int
    within_bound: bool


@dataclass(frozen=True)
class NullAudit:
    one_turn: tuple[OneTurnAudit, ...]
    schedules: tuple[ScheduleAudit, ...]
    thresholds_passed: bool
    counter_provenance: str
    status: str = STATUS


def _interventions(panel):
    names = tuple(f"{transition}_k{index}" for transition in held.TRANSITIONS for index in range(8))
    if (type(panel) is not tuple or len(panel) != 32
            or any(type(pair) is not held.InterventionPair for pair in panel)
            or tuple(pair.world for pair in panel) != names):
        raise ValueError("complete_ordered_intervention_panel_required")
    for pair in panel:
        if (type(pair.members) is not tuple or len(pair.members) != 2
                or tuple(member.member for member in pair.members) != ("m0", "m1")
                or any(member.transition_name + "_k" + str(member.pair_index) != pair.world
                       for member in pair.members)):
            raise ValueError("inconsistent_intervention_members")
    return panel


def _chains(panel):
    if (type(panel) is not tuple or len(panel) != 16
            or any(type(world) is not held.ChainWorld for world in panel)
            or tuple(world.world for world in panel) != tuple(f"h{index:02d}" for index in range(16))):
        raise ValueError("complete_ordered_chain_panel_required")
    return panel


def audit_one_turn(panel):
    """All nine singletons and all36 unordered pairs on all64 members."""
    panel = _interventions(panel)
    results = []
    for names in tuple((name,) for name in nulls.NULL_NAMES) + nulls.NULL_PAIRS:
        pairs = []
        counts = dict.fromkeys(held.TRANSITIONS, 0)
        for pair in panel:
            actions = []
            for member in pair.members:
                prefix = tuple(nulls.PublicMessage(message.role, message.content.encode("ascii"))
                               for message in member.public_view().prefix)
                options = dict(phase=member.transition_name.upper(), skin=member.construction.skin)
                ranking = (nulls.rank_null(names[0], prefix, **options) if len(names) == 1
                           else nulls.rank_pair(names[0], names[1], prefix, **options))
                actions.append(ranking[0])
            score = scoring.score_intervention_pair(tuple(action.decode("ascii") for action in actions), pair)
            pairs.append(NullPairResult(pair.world, tuple(actions), score))
            counts[pair.members[0].transition_name] += int(score.pair_both_correct)
        results.append(OneTurnAudit(names, tuple(pairs), tuple(counts.items()),
                                    all(count <= 4 for count in counts.values())))
    return tuple(results)


def audit_schedules(panel, *, count_context, count_action, counter_provenance, master):
    """All six public-only actors over32 chains; all generated traces retained."""
    panel = _chains(panel)
    results = []
    for name in nulls.SCHEDULE_NAMES:
        worlds = []
        for world in panel:
            runs = tuple(rollout.run_schedule(
                world, member.member, name=name, count_context=count_context,
                count_action=count_action, counter_provenance=counter_provenance, master=master,
            ) for member in world.members)
            score = scoring.score_chain_pair(tuple(run.attempts for run in runs), world.members)
            worlds.append(ScheduleWorldResult(world.world, runs, score))
        chain_count = sum(member.whole_chain_success for world in worlds for member in world.score.members)
        twins = sum(world.score.pair_both_correct for world in worlds)
        results.append(ScheduleAudit(name, tuple(worlds), chain_count, twins,
                                     chain_count <= 16 and twins <= 8))
    return tuple(results)


def audit_nulls(interventions, chains, *, count_context, count_action, counter_provenance, master):
    one_turn = audit_one_turn(interventions)
    schedules = audit_schedules(chains, count_context=count_context, count_action=count_action,
                                counter_provenance=counter_provenance, master=master)
    return NullAudit(one_turn, schedules,
                     all(result.within_bound for result in one_turn + schedules), counter_provenance)
