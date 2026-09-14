"""Fresh-process A2 teacher strategy over the unchanged v1 collector.

Only MASTER and GUIDANCE are configured, on explicit run, in this process.
The strict selector, scorer, 32-case shape, 900-second bound, native logging and
teacher-free draft prefixes remain v1's. No action is chosen by this wrapper.
This is exogenous prompted scaffold distillation until teacher removal, not
autonomous parenting. Main owns launch and provenance. Inherited episode labels
still say OUTCOME-TRAIN-A1; distinguish runs by output root and logged A2 master
and allocation digest, not that legacy label alone.
"""

from gpu import astra_stage2a_outcome_collect as collector


MASTER = b"ASTRA-OUTCOME-COLLECT-TRAIN-20260914-A2"
GUIDANCE = (
    "\n\nTeacher-only exogenous strategy for prompted scaffold distillation; "
    "remove this strategy for unguided student release:\n"
    "Use only the public conversation. First extract GOAL from the original TASK. "
    "Determine CURRENT from the latest WORLD, or from TASK if no WORLD has occurred. "
    "If CURRENT equals GOAL, immediately emit STOP: do not THINK or READ at GOAL. "
    "Never STOP before GOAL.\n"
    "At the start, and after THINK KEEP, emit READ INDEX using the latest CURRENT. "
    "After READ INDEX, choose the public ROUTE row with AT equal to CURRENT and FOR equal to GOAL. "
    "Emit READ RELATION with that row's QUERY field. Copy QUERY exactly; never derive it "
    "from the ROUTE row's identifier.\n"
    "After a relevant READ RELATION, choose the public EVENT row whose AT equals CURRENT "
    "and FOR equals GOAL. Emit STEP using that EVENT's DID port, not THINK. "
    "Remember from the public history that chosen EVENT's identifier, GOT and RECOVER "
    "for checking the actual outcome of this STEP.\n"
    "Immediately after STEP, read its actual WORLD outcome. If now at GOAL, immediately STOP. "
    "Otherwise emit exactly one check for this unchecked STEP: THINK KEEP using the chosen "
    "EVENT's identifier if WORLD CURRENT equals that EVENT's GOT, or THINK REVISE using "
    "that same EVENT's identifier if they differ. This check marks the STEP checked. "
    "Never THINK without a preceding unchecked STEP; never check one STEP twice.\n"
    "After KEEP, do NOT use RECOVER. Start the second hop with READ INDEX at the latest CURRENT, "
    "then the matching public QUERY, then STEP the relevant EVENT's DID. "
    "After REVISE, emit READ RELATION using the previous chosen EVENT's RECOVER exactly once; "
    "then STEP the observed relevant EVENT's DID, without another intervening THINK. "
    "RECOVER is only for an actual mismatch between a STEP's WORLD outcome and its chosen EVENT's GOT. "
    "Emit exactly one legal action per call and no explanation."
)


def run(options, **kwargs):
    collector.MASTER = MASTER
    collector.GUIDANCE = GUIDANCE
    return collector.run(options, **kwargs)


def parse_args(argv=None):
    return collector.parse_args(argv)


if __name__ == "__main__":
    run(parse_args())
