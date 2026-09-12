# SEQ-071 — lower-rate memory writes still fail selectivity

September 12, 2026, 10:40 UTC. Both new fits/evaluations/report commands
completed; independent CPU re-reduction agrees with unchanged native G9.
This closes the predeclared two-rate follow-up, not the mechanism campaign.

| Learning rate | Dose16 I_d_frame | Paired-owner bootstrap interval | Frame spill | G9 |
| --- | ---: | --- | ---: | --- |
| 1e-4 inherited | 1.921470 | [1.202608, 2.682503] | .415537 | FAIL |
| 3e-5 new | 3.077589 | [1.990598, 4.163140] | .393606 | FAIL |
| 1e-5 new | 1.140233 | [.520100, 1.815956] | .296436 | FAIL |

Native G9 requires interval lower bound>0 AND frame spill<=.03. All three
clear the acquisition interval test and all fail spill. Native G11abstention
also fails for all. These intervals resample16owners within one fitted adapter,
not optimizer seeds. No new pass threshold, pooling or p-value was introduced.

Dose16 mean conditional correct-color probability is OFF .259650, ON .685323
at1e-4, .919509 at3e-5 and .617202 at1e-5. These are candidate-normalized
probabilities, NOT generated-answer accuracy. At3e-5acquisition strengthens
while average spill falls slightly, but bicycle spill rises from.508725to.609463.
At1e-5lower spill comes with weaker acquisition. Neither is a selective writer
or a reason to lower the gate. Do not continue an unbounded LR search or
claim that reduced spill alone demonstrates improved memory.

## Binding and actual execution

Same source-bank seed1/bank0oracle F_r16k16 corpus, identical bytes
f2388eaf9c2285d6c5fe109445a599a4fefb5d9b1ca0ce6223ef78bede01c37d.
Rank8, adapter initialization seed2,3epochs,12924items,9693actual steps,
749985input/711213supervised tokens, zero training straddles/truncations.
All1313cue IDs, ordering, non-score fields, candidate order, tokenization and
evaluation metadata match. Every OFF score matches across all three pairwise
comparisons at saved JSON precision; max serialized drift0. This is not a
claim of tensor-bit identity or official model authentication.

New fits ran node3source52e0e4db0d67d54defa4151cb091ccc925cd9e8c;
memory_dose.py and preparation helper byte-identical to baseline sourcef2e5b65e.
Historical baseline ran node2. Node/runtime placement remains a limitation;
observed OFF equality supports this descriptive comparison but is not an
independent node-causal test. Official origin stays UNRESOLVED_LOCAL_HASHES_ONLY.

3e-5controller53249/GPU0:10:13:57.390967→10:39:08.447186UTC;
fit1245.0s, evaluation225.6s.1e-5controller53265/GPU2:
10:14:01.151320→10:39:04.611381UTC; fit1232.3s, evaluation236.3s.
Combined launch-to-terminal reservation time is about50.24A40minutes,
including startup/checks; core fit/evaluation48.99minutes. Both controllers
and workers53250/53266are absent, both original cleanup receipts actually
verify empty owned groups/GPUprocesses. The earlier slow-query concern did
not invalidate their cleanup. No manual kill or unrelated process intervention.

## Reproduction and preservation

Original runs stay on node3:
`~/astra_diagnostics/astra_A1_lowerlr_bank0_ts2_{3e5,1e5}_20260912_attempt1`.
Adapters remain there; terminal capsule excludes only adapter weights, not
configurations, DONE, training metadata, raw cue scores, inputs or logs.
Capsule `receipts_20260912/astra_lowerlr_terminal_20260912.tgz`, SHA256
f40c504ea67497bf64412f74195131dbf8701c7a8645f84ff0b92571ca121547,
matches node/VM copies. Reproducer `astra_lowerlr_reduce_20260912.py` accepts
baseline,low3,low1capture roots and prints JSON without changing any input.
It verifies frozen native-source hashes and reduces unchanged native gates;
the old campaign analyzer hardcoding1e-4was neither used nor patched.
Full JSON `astra_lowerlr_reduction_20260912.json` records errors=[], all three
valid artifacts and exact OFFmatch. Separate reviewer check is pending.

## Decision

Park further LR-only sweeps: the requested two comparisons have answered their
question and still do not solve spill. Preserve stronger3e-5acquisition as a
diagnostic observation, not an accepted substrate. Behavioral useful/wrong-
board fits have separately completed and parent-free evaluation is underway.
Interpret those before selecting joint/repeated-write and child-material work;
the minimum memory-selectivity interface remains unresolved. No clean lineage,
H1/H2, mechanism freeze, or sprint completion claim.
