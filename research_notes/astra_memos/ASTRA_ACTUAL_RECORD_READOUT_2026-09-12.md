# Actual-record write and parent-free readout — September 12, 2026

## Status and interpretation

**SEQ111 writes verified; SEQ112 readout technically complete. No parenting
advantage observed in this exploratory comparison. Independent raw recount
is pending.** The table below comes from hash-verified terminal results and
native collector replay/token audits, not a new independent analysis.

| State | Quiz correct / fixed 24 items | Mean quiz accuracy | Valid quizzes / 4 | Faithful records / allotted 12 | Faithful / emitted records |
|---|---:|---:|---:|---:|---:|
| OFF | 7/24 | 0.291667 | 4/4 | 9/12 | 9/12 |
| P_ON | 6/24 | 0.250000 | 3/4 | 10/12 | 10/11 |
| A_ON | 6/24 | 0.250000 | 3/4 | 10/12 | 10/11 |

P minus A is zero; each adapter minus OFF is -1/24. The two adapter states
have identical *aggregate and per-task scores*, not necessarily identical raw
outputs. On rules 2/3/4, each cell scores 2/6, 1/6, 3/6. On rule 5, OFF scores
1/6 while both adapter cells terminate `protocol_invalid` after two TRYs;
their missing quizzes correctly retain zero under the frozen denominator.
The raw cause and pre-TRY prediction choices require the pending recount.

These are four shared rule tasks, one generation-seed protocol and one
paired write seed, not 24 independent learner observations. A one-record
faithfulness increase cannot establish learned experience selection,
amortized parenting, downstream utility or a robust treatment effect.
Rule families were excluded from this formation, not globally untouched
confirmation data. All original 64 confirmation cases remain unrequested.

## What executed

- Formation `interaction_v3` used process guidance P versus active neutral
  recap A. Main accepted the first two eligible raw child records in each
  arm; provenance, control rules and excluded parent/restatement prose are
  recorded under SEQ110. Earlier SEQ095 remains declined.
- Two independent fresh-base rank-8 LoRA writes, seed 2, LR 1e-4, batch 2,
  12 updates each. Each corpus has 74 target tokens including EOS, or 888
  target-token presentations. No packing, splitting, dropped targets or
  nonfinite batches. Native source/token/config/trainability/seal checks pass.
- Both saved adapters have 392 finite tensors. Every saved B entry is
  nonzero; B L2 is 1.587822886866 for P and 1.600173037602 for A. Given declared
  zero-B initialization, this corroborates a parameter write, not usefulness
  or a complete parameter-delta measurement.
- OFF, P_ON and A_ON run in separate fresh processes, with only current-task
  history. No parent, restatement, formation transcript, previous-task history
  or readout-time parameter update is supplied. Diagnostic record calls are
  not fed back into wake prompts or trained. The full relation-definition
  prompt remains an explicit scaffold.
- The controller executes 90 calls: OFF 32, P_ON 29, A_ON 29; 96 is the
  ceiling, not the executed count. Raw usage is 31,510 input and 1,945 output
  tokens. Interrupted/invalid tasks are not replaced.

This closes a sourced-record-to-saved-adapter-to-parent-free-output path.
It does not qualify general G3/P1/G5/H1/H2, a clean lineage, a mechanism freeze
or the evolving adult learning-policy loop. Model origin remains
`UNRESOLVED_LOCAL_HASHES_ONLY`; formal C11 guard enforcement remains deferred.

## Custody and cost

Frozen source: `610c6edd05ce9c85720ee6e992889badecc2c158`.

Write root: `~/astra_diagnostics/astra_rulegame_interaction_v3_record_write_20260912_attempt2`.
Plan: `48effd1ba154f497e5946d308f990624ada63bd905c198e0abfdf668131a8ee4`.
Capsule: `26243e9a6436a859f7ed7a6ec1250a9e3a06496ec61c8eb3f85afe4d1ea308b4`,
47 metadata files. Attempt 1 was never GPU-launched; its virtualenv-symlink
preparation bug and unchanged scientific material were preserved before the
tested v2 driver prepared attempt 2.

Readout root: `~/astra_diagnostics/astra_rulegame_interaction_v3_record_readout_20260912_attempt1`.
Plan: `cdb71865359498ca0f75db57566e638b667d2e849cc11c9cbd45dd6bfbb97375`.
Capsule: `f8f2bb688da189ebb8f70c67725f1c008db49d6c5b2800abdc58a0dd4fcb7458`,
232 metadata files. Both capsules are locally hash-validated and safely
extracted; weight bytes remain native with verified inventories. Full
GPU UUID/process/reservation/queue release is verified, not inferred from
zero memory usage. Former controller PIDs are 233174 and 234660 on node3 GPU2.

| Phase | Controller seconds | Worker seconds | Launch to observed full release seconds | Collection seconds |
|---|---:|---:|---:|---:|
| Paired writes | 230.665586 | 153.654476 | 361.167984 | 22.495086 |
| Parent-free readout | 595.137126 | 493.982361 | 642.893684 | 53.982670 |

Within each row these clocks overlap; do not add them. Full release includes
time awaiting collection. The separate model-free tensor audit takes
12.852530 CPU seconds, not a new GPU reservation. Native collection reruns
exact call/world replay and actual-tokenizer audit; it does not independently
recompute model logits or establish statistical significance.

## Next decision

Inspect raw rule-5 failures and distinguish record faithfulness from
spontaneous pre-TRY prediction. Do not repeat this same tiny comparison as
proof of parenting or retune on its readout. A bounded independent design
review is considering the smallest acquisition/selection/retention diagnostic
before further actual-record development. The separate interleaved authored
memory pair tests a mechanism question, not a prerequisite that recasts this
null parenting contrast as success.
