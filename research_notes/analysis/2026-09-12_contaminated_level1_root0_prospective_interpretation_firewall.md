# Prospective interpretation firewall for the public-ID-contaminated Level-1 root-0 run

**Date:** 2026-09-12  
**Status:** prospective outcome-interpretation memo, written before any
conditional generation or likelihood outcome was available in the laptop
worktree. No model/GPU process, run artifact, builder source, or result was
inspected or changed.  
**Bound inputs:** source commit `5f6e1f1d`; native candidate
`5d1644b90ff7621ee121aba65be7dd7cae7f15168f5a3c3a09a1bc9aa9a7af8c`;
fit acceptance `fb4aa19a`; launch receipt `a1afd430`; fit plan
`680e5239cd90c15b72de998d22c09cf5aa451d2e71111d99e940532e43510f11`;
fresh shortcut audit `cd881932`. The committed readout interface is a
proposal, and its implementation was still uncommitted at this cutoff.

## Decision in one paragraph

Preserve the already-launched AUTH/DERANGED pair as a disposable exploratory
diagnostic. Split every result by operation. **PROSPECT remains interpretable
as a finite, supplied, public-card conditional-control diagnostic. REVISE does
not test use of the literal expected outcome:** on every train and dev row,
the visible numeric case suffix plus `OBSERVED` and the prior action predicts
the complete target perfectly. AUTH/DERANGED reversal does not remove that
shortcut; it merely reverses which shortcut-defined target is fitted. No
aggregate over PROSPECT+REVISE, no REVISE score, and no overall Level-1 gate is
valid. Narrow control/interface results can still diagnose damage. Nothing in
this run can pass, select, replace, or tune Q0.

## 1. Exact contamination and unaffected subset

The material has 64 PROSPECT and 64 REVISE training rows per arm, plus 32
PROSPECT and 32 REVISE dev rows. Train and dev wording and full instance
strings differ, but both reuse public square suffixes `00..07`.

For REVISE, construction fixes

```text
expected = local_outcomes[0]
local_outcomes rotation = floor(square_suffix / 2) mod 2
```

Therefore, for both AUTH and DERANGED:

| REVISE projection | train joint target | dev joint target |
|---|---:|---:|
| public suffix/instance, alone | 16/64 | 8/32 |
| public suffix/instance + `OBSERVED` | 32/64 | 16/32 |
| public suffix/instance + prior action | 32/64 | 16/32 |
| public suffix/instance + `OBSERVED` + prior action | **64/64** | **32/32** |

The last policy reconstructs `(COMPARE, POLICY, NEXT)` without reading the
literal `expected` token in `PRIOR: PREDICT ... -> expected`. The train/dev
split does not break it because the informative numeric suffix repeats.

No REVISE row or post-hoc REVISE subgroup escapes this defect. In particular:

- an outcome twin can flip perfectly by reading suffix plus `OBSERVED`;
- a prior-action twin can flip `NEXT` perfectly by additionally reading the
  prior action;
- component, joint, strict, own-map, held-template and likelihood metrics all
  admit the same shortcut; and
- dropping a favorable suffix after outcomes would only add selection bias.

PROSPECT does not have this defect. Within every public instance, belief and
goal are fully crossed. On both maps, `instance + goal` and `instance + belief`
each top out at `.50` joint accuracy (32/64 train; 16/32 dev), whereas the
literal public `goal + belief` is sufficient. Thus its 16 goal twins and 16
belief twins on dev remain meaningful tests of using both public inputs. A
PROSPECT pass is still only a supplied two-action truth-table procedure under
held wording and identifiers, not stored world knowledge, novel reasoning, or
broad generalization.

## 2. Meaningful measurements, with fixed boundaries

### Training versus development

Report four cells, never one aggregate:

| operation/split | What a high score can mean | What it cannot mean |
|---|---|---|
| PROSPECT train, 64 rows | exact-form acquisition and surface carriage | transfer or general reasoning |
| PROSPECT dev, 32 rows | held-template/identifier expression of the same supplied goal+belief procedure | new Boolean structure, experiential memory, or Level 1 |
| REVISE train, 64 rows | exact-form fit, syntax, and possibly input-dependent routing | use of explicit expected-versus-observed comparison |
| REVISE dev, 32 rows | held-wording transfer of the contaminated suffix/observed/prior function | held semantic revision or prediction-error use |

The pre-existing whole-corpus `116/128` own-map threshold is unusable here:
the 64 contaminated REVISE rows can carry half the aggregate. Do not invent a
new PROSPECT-only pass threshold after seeing outcomes. Preserve raw exact
counts and the already named operation-level diagnostics (`32`-row semantics,
surface, strata and twins) as descriptive evidence only. The repaired
successor must bind its own noncompensatory gate prospectively.

### AUTH/DERANGED map reversal

For PROSPECT, paired map reversal remains informative. The two arms have
identical prompts, complete target-sequence multisets, dose and fresh-base
initialization. If both learn their own maps on train and dev, with itemwise
complementary outputs and opposite fixed-orientation likelihood margins, the
writer has directionally controlled a finite public-card conditional policy.
If only AUTH succeeds, the result is compatible with the base model's natural
semantics or asymmetric optimization and is not conditional-writer evidence.

For REVISE, map reversal is only a matched contaminated control. If both maps
succeed, it rules out a single constant output and shows that supervision can
redirect an ID/observation/prior-conditioned response. It **does not** show
that the model compared the stated expectation with the observation. AUTH
success with DERANGED failure is especially compatible with a base semantic
prior. No AUTH-minus-DERANGED average may rescue either case.

The shared OFF state is one state, not two independent controls. Score its
same responses against both maps for orientation, but never count them as
replicate evidence.

### Teacher-forced likelihood

Only common-input-prefix, complete-continuation likelihood is admissible; no
gold `PREDICT`, `COMPARE` or `POLICY` field may enter the scoring prefix. Keep
the predeclared AUTH orientation fixed:

```text
I = [log P(A|x0) - log P(B|x0)]
  - [log P(A|x1) - log P(B|x1)]
```

- PROSPECT's 16 belief-pair interactions are meaningful sub-greedy evidence.
  AUTH should be positive in AUTH orientation and DERANGED negative (or
  positive only after explicitly reporting its own reversed orientation).
- REVISE's 16 outcome-pair interactions remain contaminated. A large signed
  interaction shows observation-sensitive preference under a stable public
  cue; that cue can be the suffix. It cannot demonstrate comparison with the
  literal expected outcome.
- Likelihood movement without strict generation is latent preference, not
  behavioral carriage. Strict generation without the corresponding fixed-sign
  likelihood movement is a discrepancy to audit, not a pass.

An additional, pre-readout `expected`-token intervention holding public ID,
`OBSERVED` and prior action fixed could diagnose whether the fitted model is
sensitive to the literal expected token. It would be out of the training
support and cannot repair or retroactively qualify this material: success
would rule out *exclusive* shortcut use; failure would remain ambiguous
between shortcut reliance and ordinary off-support failure.

### Controls and interface

The shortcut does not contaminate prompts that contain no conditional case ID.
The proposed controls therefore remain useful **if their exact bytes and
denominators are frozen before the first readout call**:

- 16 addition/ACT-only inputs can measure narrow legal-action correctness,
  invalidity and unwanted conditional-tag spill relative to shared OFF;
- the native-action copy set has eight unique prompts executed twice. Report
  eight independent items and 16 executions, never `n=16` independent tasks;
  it measures literal interface copying and tag spill, not CompilerGym skill;
- a loss of even one item exceeds the proposed `.05` absolute tolerance on a
  16-item family. Report each control family separately; do not average one
  preserved interface over another damaged one.

Control preservation is only narrow no-harm evidence for this authored
rank-8/LR-`1e-4` write. It cannot cure REVISE contamination, establish broad
interface preservation, or turn this into DREAM/SLEEP/parenting evidence.
Control failure remains meaningful: it shows this exact writer/dose damages
an out-of-scope behavior, even if PROSPECT succeeds.

Fit loss, exact token accounting, adapter hashes, absence of skips and release
receipts remain technical evidence. A low loss is not semantic acquisition.
Because the arm token schedules are matched, gross AUTH/DERANGED optimization
asymmetry is diagnosable, but it does not identify a cognitive mechanism.

## 3. Outcome-contingent interpretations fixed before readout

| Observed pattern | Allowed interpretation | Required next action / forbidden reading |
|---|---|---|
| PROSPECT AUTH and DERANGED each acquire their own train map, redirect on dev, show correct belief/goal twins and opposite likelihood signs; controls hold | finite complementary public-card conditional carriage at root 0 under full-response CE | retain as exploratory mechanism evidence; still run adjudicated Q0 and rebuild Level 1 |
| PROSPECT train passes but dev fails | exact-form fit without held-surface extraction | repair views/extraction only after Q0; do not call conditional transfer |
| PROSPECT likelihood moves correctly but generation fails | sub-greedy directional acquisition | no behavioral or Level-1 pass |
| PROSPECT generation appears correct but DERANGED or fixed-sign likelihood fails | base prior, parser/generation boundary, or asymmetric fit remains viable | no writer qualification |
| REVISE alone passes, including all twins and held templates | contaminated ID/observation/prior routing plus surface carriage | no expected-versus-observed, revision, intertwining, or Level-1 claim |
| Both REVISE maps reverse perfectly | complementary control of the contaminated function; not a constant ritual | map reversal does not neutralize leakage |
| AUTH REVISE passes but DERANGED does not | natural semantic prior/asymmetric optimization | not writer evidence |
| PROSPECT and REVISE both look excellent, but any control family degrades | acquisition with unsafe scope/interface at this recipe | fail no-harm; do not average the control away |
| Controls hold but conditional panels fail | narrow interface preservation only | no acquisition claim |
| All panels look excellent | at most root-0 authored PROSPECT carriage + contaminated REVISE routing + narrow no-harm | cannot pass Level 1, Q0, W-H1, H1, parenting, or whole-organism claims |

No composition/intertwining conclusion is available: the launched fit contains
only isolated rows, and the committed composition interface has no cases. A
later zero-training chain using this contaminated REVISE operator would inherit
the shortcut and therefore cannot rescue the run.

## 4. Relationship to Q0

**No scientific score from this run may inform Q0's implementation choices.**
Q0 is already prospectively adjudicated on a different and harder object:
opaque tool x mode XOR, a natural common `ACT: -` decision prefix, a pairwise
objective at fixed rate, quartet-gradient canary, complementary maps, exact
and held gates, and itemwise locality. This Level-1 scout instead uses
semantically transparent public cards, full-response target CE, LR `1e-4`,
and a contaminated multi-field REVISE target. Outcome-based selection of Q0's
objective, rate, dose, rank, or canary from these scores would be post hoc.

Two implementation-only lessons may transfer without changing Q0's science
bytes:

1. the fresh AUTH/DERANGED fit wrapper, immutable adapter receipts, complete
   denominators and shared-OFF accounting can be reused as engineering
   patterns; and
2. if PROSPECT produces the expected opposite-sign complete-continuation
   margins, that validates the common-prefix scorer's orientation on this
   surface. It validates instrumentation, not the Q0 writer.

Conversely, a PROSPECT failure can trigger a generic loader/scorer/fit audit
before spending on Q0, but it cannot falsify Q0's pairwise objective. REVISE
outcomes supply no Q0 mechanism evidence at all. The claim-bearing sequence
therefore remains:

```text
adjudicated Q0 -> repaired Level-1 material -> W-H1 -> H1
```

## Final label

Use exactly:

```text
EXPLORATORY_ROOT0_AUTHORED_CONDITIONAL_DIAGNOSTIC_WITH_REVISE_PUBLIC_ID_LEAK
```

The run is worth preserving because PROSPECT, control damage, map asymmetry and
readout plumbing can still teach us something. It is not a failed or passed
Level-1 experiment; that experiment was never validly instantiated.
