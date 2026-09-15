# R108 continual terminal readout — 2026-09-15 08:47 UTC

FULL8932 and separately trained new-labels-masked OFF8932:416/416 held calls
completed, no readout retries. OFF in this note is NOT adapter-disabled OFF in
the capability panel. The original controller release failure remains recorded;
a subsequent scoped release for A1002/3/6 is clear. The continual training run
has completed, not remained training after its declared bounded completion.

## Behavior before accuracy

| Held math,64 per arm | FULL | Masked-trained OFF |
|---|---:|---:|
| Generated tokens, median | 189 | 230.5 |
| Generated tokens, mean | 227.453125 | 258.46875 |
| Outputs at1536-token ceiling | 1 | 1 |
| Mean lexical repetition metric | 0.0693503831 | 0.0805210408 |
| Author-reviewed semantic sample | First4 | First4 |
| Departures-and-returns in those4 | 0 | 0 |
| Grounded rejected paths in those4 | 0 | 0 |

Lexical repetition is not semantic rumination. The author semantic audit covers
only four prospectively positioned responses per arm;60/64 remain semantically
unassessed in each arm. No whole-cohort branching, persistence or metacognition
conclusion follows. FULL is shorter on this held cohort, not demonstrated richer.
The first4 FULL coherence labels are3COHERENT/1MIXED; do not extrapolate that rate.

Secondary held-math accuracy: FULL54/64, masked-trained OFF40/64. This difference
does not establish parenting-dependent learning or a successful metacognitive
behavioral change. Historical117 extra physical OFF recovery updates remain a
disclosed asymmetry; matched terminal update indices do not erase it.

Evidence: `orch_combined_l1_continual_20260915_attempt1/R108_TERMINAL8932_FINAL_COMPACT.json`
binds each completion, adapter, optimizer, RNG, token reduction and author
annotation hash. The source/test allowlist is `STAGE_R108_TERMINAL_FINAL.json`
in the same directory. Raw calls and author annotations remain on-node.

R108 follow-up: genuine BASE and learned-child parenting in parallel; a NEW
two-episode guided lane uses inherited FULL8932 optimizer/RNG, actual causal
prompt replay with parent targets masked, ordinary competent BASE anchors and
fresh context-free held/capability readouts. At this entry its new native
integration is CPU-tested but NOT yet launched; reservations are not utilization.
