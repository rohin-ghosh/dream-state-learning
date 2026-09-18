"""Training-only A4 collection: frozen D2, existing V2 public teacher strategy.

No new fitting or automatic release. Tests whether successful normal/KEEP paths
can be elicited before a prospective branch-balanced outcome corpus is built.
The unchanged selector retains all 32 attempts and only whole-route successes.
"""

from gpu import astra_stage2a_d2_collect as source
from gpu import astra_stage2a_outcome_collect_v2 as strategy


MASTER = b"ASTRA-OUTCOME-COLLECT-TRAIN-20260914-A4"


def main(argv=None):
    source.MASTER = MASTER
    source.collector.GUIDANCE = strategy.GUIDANCE
    return source.main(argv)


if __name__ == "__main__":
    main()
