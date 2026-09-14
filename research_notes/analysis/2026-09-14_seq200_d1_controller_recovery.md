# SEQ-200: saved D1 controller readout

Date: September 14, 2026, 06:29 UTC. One DEV learner seed; no population claim.

## Observed result

The original 256-update run saved D1 but aborted on checkpoint loading before
its trained readout. The evaluation-only recovery loaded that exact artifact
with strict weights-only deserialization and zero further updates. It completed
84 physical calls in 280 reserved slots; the retained BASE had 56 physical calls.
Unused chain slots remain accounted for, not forced extra model calls.

| Metric | BASE | D1 ATOM_LOCAL |
|---|---:|---:|
| SEEK paired | 1/4 | 4/4 |
| PROSPECT paired | 0/4 | 4/4 |
| CHECK paired | 0/4 | 4/4 |
| CONTINUE paired | 0/4 | 2/4 |
| Typed interventions | 18/32 | 30/32 |
| Whole chains | 0/8 | 0/8 |
| Useful pre-STEP reads | 0/8 | 6/8 |
| Typed steps | 2/8 | 7/8 |
| Canaries | 16/16 | 15/16 |

Six of ten fixed criteria pass. CONTINUE, whole chains, useful reads and chain
gain miss their predeclared minima. D1 is not a qualified BIRTH controller.
Training losses are finite: first-32 mean 0.1244810372; last-32 mean
0.0002870215. These losses are training observations, not held efficacy.

In the eight trained chain traces, the first STEP is correct in six, the
first-outcome CHECK is correct in four, and the complete required READ evidence
is present in two. None arrives at the goal. Attempt counts are
5, 5, 7, 7, 5, 5, 1, 1. Thus the negative chain result is not just a strict
scorer rejecting otherwise successful arrivals.

## Mechanistic hypothesis, not an observed cause

`composition_birth_stage2a_targets._atom_turn_indices` returns no prior turns
for CONTINUE. Its renderer therefore puts the updated CURRENT directly in a
fresh TASK message. In an autonomous rollout, the initial TASK remains in the
history and CURRENT changes in subsequent WORLD observations. This is a
specific training/readout context mismatch to investigate, not evidence that
the learner cannot compose facts in principle.

The existing CLOSED partner keeps the preceding trajectory while supervising
the identical next assistant decision. It directly tests this context issue.
It does not add a search algorithm, an awareness variable, extra held facts, or
labels inferred from the failed evaluation. The hypothesis is that learning
how to use intervening observations helps continuation more than additional
repetitions of already-fit local examples.

## Prospective next comparisons

1. Complete the already-declared single ATOM D2 continuation, updates257–512,
   preserving optimizer/RNG/tape. It remains the original dose test; a miss
   closes that recipe. No changed thresholds or rank/prompt sweeps.
2. Run CLOSED-D1 as a separately labeled early exploratory comparison. Moving
   it ahead of the former conditional-salvage schedule is recorded before its
   outputs; it is not retroactively in the original primary. Same expert
   targets, seed, initial adapter, 256 updates and 14,000 target tokens. Input
   costs differ: ATOM has800,868 unpadded/1,266,764 padded sequence tokens;
   CLOSED has2,102,308/2,377,660. Do not call this FLOP-matched.
3. Keep P-CHAIN-2 independent: Stage2A reads an exact external text service,
   whereas that diagnostic asks about composition of facts written into LoRA.
   Neither result alone establishes the authentic two-sleep flywheel.

## Reproduction and preservation

Original source123f0ae2; recovery entry5195ecf0; result/decisionc87d7f89;
early CLOSED schedulingad3e5571. Checkpoint state:
dc380a749b12d5180b19615302b6ffa126ba1ae871a09b2ba561b00db172cced.
The original FAILED status is preserved. Recovery restores adapter tensors
for evaluation, not optimizer/RNG continuation. Full-state continuation is a
separate D2 test.

Local evidence root:
`gpu_artifacts_local/astra_stage2a_d1_result_preservation_20260914_attempt1/`.
It contains the original D1/BASE/observations, complete recovery, both replay
reports and the executed CPU replay script. 451files/359,632,251bytes verified;
archive SHA256:
96e4fcd439655c85aba7c58f0c704a8db8c87e1b889b1f3577a3b3375d4bf5c0.
`evidence/astra_stage2a_baseline_replay_code_20260914_attempt1/D1_COMBINED_REPLAY.json`
contains exact criteria, custody joins and source hashes. Replay uses captured
counts; it is not independent tokenizer authentication or a promotion flag.
