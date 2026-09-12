# Sequential authored OLD/NEW fixed-budget allocation: prospective outcome matrix

**Frozen:** 2026-09-12 23:45 UTC, before inspecting any live or terminal
outcome from the launched sequential run.

**Evidence boundary:** design and interface contracts plus the launch receipt
only. The receipt said `LAUNCHED_NOT_COMPLETED`. I did not inspect run markers,
raw responses, reductions, post-launch notebook entries, processes, or GPU
state. This memo changes no code, job, adapter, model, claim, or launch state.

## Verdict before outcomes

This is a valid **fixed-total-budget allocation comparison** between replaying
old authored facts and spending the same row slots on more current facts. It
is not a new-dose-matched causal test of replay:

| quantity per cycle | `R` replay | `C` / `NEW_ONLY` |
|---|---:|---:|
| current-new presentations per fact | `20` | `40` |
| cycle-1 replacement slot | `M0`, `20`/fact | extra `B1`, `20`/fact |
| cycle-2 replacement slot | `M0`, `10`/fact + `B1`, `10`/fact | extra `B2`, `20`/fact |
| arithmetic sources | same `64`, four presentations/source | same |
| updates | `320` | `320` |

Both trajectories start from the same seed-0 FOUR_VIEW 400-update state `S0`.
Cycle 1 yields `R1` and `C1`; cycle 2 continues those separate weights to
`R2` and `C2`, with a fresh optimizer at each cycle. The five states receive
the same 128-request panel: `M0`, `B1`, and `B2`, each on exact and development
wording, plus 32 arithmetic cases.

Consequently:

- an `R` advantage can show that this **allocation policy** better balances
  old and new content at fixed total updates;
- it cannot isolate replay from lower new-content dose, different within-batch
  content, or their interaction;
- a `C` advantage rejects the practical value of this replay allocation at
  this load, not replay in general; and
- no outcome qualifies conditional Q0 locality, child-authored SLEEP,
  parenting, H1/H2, or the Dream--LoRA--Think thesis.

## Outcome reduction fixed before inspection

All decisions are itemwise and surface-specific. Never pool the exact and
development surfaces or treat the 16 repeated facts as 32 independent items.

For bank `b`, state `x`, define:

```text
Q(b,x) = exact_correct(b,x) >= 15/16
         AND dev_correct(b,x) >= 15/16

H(x)   = arithmetic_adherence(x) >= 30/32
         AND correct_ACT(x) >= 31/32
```

Report validity, cap hits, raw output identity, per-fact transitions, and
colour/tag spill separately. `H` is a usability floor, not proof that latent
arithmetic competence survived.

For B1, retention is meaningful only relative to the same arm's cycle-1
state. Preserve:

```text
retained_X(B1) = facts correct on both surfaces at X1
                 that remain correct on both surfaces at X2
                 / facts correct on both surfaces at X1
```

If `Q(B1,X1)` is false, label B1 `NOT_ESTABLISHED_AT_ENTRY`; a low B1 score at
cycle 2 is not a forgetting result. Absolute `R2-C2` B1 differences cannot
repair unequal cycle-1 acquisition.

### Precedence

1. Missing, wrong-parent, nonfinite, incomplete-panel, reload, timing, or
   cleanup evidence is `TECHNICAL_PARTIAL`; do not enter the scientific
   matrix or score missing calls as wrong.
2. If S0 does not reproduce the bound parent inventory and its recorded M0
   and arithmetic behavior, use `S0_PRECONDITION_FAIL`. Do not reinterpret
   descendant differences.
3. If S0 is already near-perfect on B1 or B2, use
   `NEW_BANK_HEADROOM_INVALID`; the affected acquisition contrast is invalid.
4. Any `H` failure makes that state `X` (unsafe interface) regardless of its
   memory scores.
5. Otherwise classify cycle 1, then the terminal state matrix below. Surface
   discordance and B1 entry failure are mandatory suffixes, never averaged
   away.

## Cycle-1 interpretation matrix

Cycle 1 asks whether B1 can be learned while M0 and arithmetic remain usable.
It is diagnostic; execution was prospectively required to continue through
both cycles regardless of scientific cycle-1 scores.

| pattern after `R1` / `C1` | narrow inference | next interpretation action |
|---|---|---|
| Both satisfy `Q(M0)`, `Q(B1)`, and `H` | Both policies integrate one new bank at this load; replay is not yet needed. | Use cycle 2 to test a second bank; do not claim replay from equal ceilings. |
| R satisfies both banks; C learns B1 but loses M0 | Early practical advantage for replay allocation, despite C's double B1 dose. | Preserve as allocation evidence; cycle 2 must show whether it persists. |
| R keeps M0 but fails B1; C satisfies both | R traded acquisition for preservation; C is already the better integrator. | Mark R B1 retention at cycle 2 unassessable unless B1 later qualifies. |
| R keeps M0 but fails B1; C learns B1 but loses M0 | Canonical stability--plasticity tradeoff; neither integrates both. | Cycle 2 may describe persistence, but cannot convert this into a replay success. |
| R satisfies both; C fails B1 despite twice the new dose | Mixed old/new content or schedule regularized acquisition, but the effect is not attributable to replay alone. | Require cycle-2 replication of the same dominance before any follow-up. |
| Both learn B1 but both lose M0 | The registered replay allocation did not protect old content at cycle 1. | Do not call B1 acquisition coexistence; inspect cycle 2 only under the frozen plan. |
| Both retain M0 but neither learns B1 | Apparent retention is trivial because no new content was installed. | Classify the writer/dose as inadequate for B1; B1 forgetting is later undefined. |
| Neither learns B1 nor retains M0 | Scientifically destructive/no-acquisition under both policies. | Stop this recipe after terminal custody; no outcome-driven rescue. |
| Either arm fails `H` | That arm is unsafe even if its memory scores rise. | Raw outputs may localize format versus wrong action only after terminal; they cannot rescue usability. |

## Complete terminal cross-matrix

After cycle 2, assign each technically valid arm exactly one state:

- `I` (**integrates**): `Q(M0)`, `Q(B1)`, `Q(B2)`, and `H` all pass, with B1
  established at cycle 1;
- `P` (**preserves/underlearns**): both old banks and `H` pass, but B2 fails;
- `F` (**forgets**): B2 and `H` pass, but either old bank fails;
- `N` (**neither**): B2 fails and either old bank fails, while `H` passes;
- `X` (**unsafe**): `H` fails, regardless of memory.

This partition covers every technically valid pass/fail pattern. Within `F`
or `N`, always name whether M0, B1, or both failed. If B1 was not established
at cycle 1, append `B1_NOT_ESTABLISHED_AT_ENTRY` and replace “forgot B1” with
“B1 never qualified.”

Rows are replay `R2`; columns are comparator `C2`.

| R \ C | `I` | `P` | `F` | `N` | `X` |
|---|---|---|---|---|---|
| **`I`** | **Both saturate/integrate.** No demonstrated need for replay at this load; ceiling can hide differences. Stop the colour allocation line and return to Q0. | R integrates while C underlearns B2 despite twice its new dose. R is the better practical policy; mixed-content regularization is plausible, not replay necessity. | **Strongest practical replay-allocation pattern:** R integrates; C learns B2 but forgets old. Preserve as fixed-budget evidence; only an equal-new-dose successor could isolate replay. | R integrates while C installs neither old+new conjunction. R dominates this comparator, but the mechanism remains composite. | R is the only safe integrator. Prefer R operationally; do not infer that absence of replay alone caused C's interface failure. |
| **`P`** | C integrates while R underlearns B2. Comparator wins; reject this replay allocation at the registered budget. | Both preserve old but fail B2. No integration and no forgetting test with successful new learning; current-new dose/format is inadequate. | **Replay preserves but underlearns new; C learns new but forgets old.** This is the canonical Pareto tradeoff, not a winner or coexistence result. | R preserves old but fails new; C achieves neither. R has a retention advantage only, not useful integration. | Neither supplies a safe integrated state; R's old preservation cannot compensate for absent B2. |
| **`F`** | C safely integrates and R forgets. Comparator wins strongly; the replay allocation is harmful or insufficient here. | R learns B2 but forgets old; C preserves old but underlearns B2. Reverse Pareto tradeoff; neither integrates. | **Both learn B2 and both forget old.** The registered replay allocation is insufficient; no replay-preservation claim. | R shows new acquisition only; C shows neither. This is an acquisition advantage without coexistence. | R learns new but forgets old while C is unsafe. Neither is a usable integrator. |
| **`N`** | C dominates with safe integration. Stop the replay-allocation branch. | C preserves old but neither policy installs B2. Comparator is safer for old content; no integration. | C learns B2 but forgets old; R achieves neither. C has acquisition only, not coexistence. | **Both forget/fail new.** No usable evidence beyond failure of both registered allocations. | R is safe but achieves neither; C is unsafe. No integration. |
| **`X`** | C is the only safe integrator and wins. | C safely preserves old but underlearns new; R is unsafe. No integration. | C safely learns new but forgets old; R is unsafe. No integration. | Neither integrates; R is additionally unsafe. | **Both unsafe.** Memory counts are descriptive only; stop this writer recipe. |

## Mandatory modifiers to the matrix

### 1. Both saturate

`I/I` supports only “both policies carried three authored banks at this load.”
It does not prove replay is useless; a 16-fact ceiling may be too easy. The
next scientific capacity test would prospectively increase identity count or
horizon, not mine logits for a post-hoc difference. For the active program,
the next action is still conditional Q0, because task-level colour memory does
not qualify selective native-action writing.

### 2. Useful replay-allocation signal

Apply the design's stricter descriptive rule in addition to `I/F` or related
cells. R must retain at least `15/16` on both surfaces of every learned old
bank, acquire B2 at least `15/16` on both, keep `H`, and exceed C by at least
two retained facts on the same old bank on both surfaces without harming the
other old bank by more than one. Passing this licenses “useful fixed-budget
replay allocation at one authored seed,” not a causal replay effect.

### 3. Replay preserves but underlearns new

If R old retention passes but B2 fails while C acquires B2, the result is an
allocation tradeoff even when C forgets. Do not call R successful because it
remembered content it continued to see. The smallest clean successor, only if
the causal question remains valuable after Q0, is two fits with identical new
rows/dose/RNG:

```text
CONTROL: L_new
REPLAY:  L_new + L_old
```

with separately normalized losses and unchanged new coefficient. This changes
compute but isolates adding the old gradient; it must not be retrofitted into
the running comparison.

### 4. Comparator wins or ties

- If C is `I` and R is not, reject R at this budget.
- If both are `I`, there is no supported replay need.
- If C retains old as well as R and learns at least as much B2, there is no
  positive replay-allocation evidence even if small logits differ.
- A C win does not show that rehearsal is generally harmful; it shows that
  spending fixed slots on the registered old mixture was not useful here.

### 5. Old-bank asymmetry

M0 and B1 must remain separate. M0 began in S0 and is replayed in both R
cycles; B1 is acquired in cycle 1 at unequal dose and replayed only in R cycle
2. `M0 pass / B1 fail` can indicate recency or inadequate B1 entry/dose;
`B1 pass / M0 fail` can indicate age/strength asymmetry. Neither supports a
general old-memory claim. Report per-fact loss, recovery, and cross-surface
transitions without selecting the more favorable bank.

### 6. Surface disagreement

Exact-pass/dev-fail is `STORED_NOT_ROBUSTLY_EXTRACTED`; dev-pass/exact-fail is
`SURFACE_INSTABILITY`. Both fail `Q`. Never let a `16/16` surface compensate
for the other surface, and never count a wording transition as an independent
fact.

### 7. Apparent recovery

R receives old rows, so an old fact wrong at R1 and correct at R2 is
**reacquisition/refresh under replay**, not retention. C receives no old rows;
an analogous recovery is a parameter-drift or generalization observation.
Report recoveries separately from continuously correct facts.

## Next-action funnel fixed before outcomes

1. Complete immutable custody and apply technical/precondition precedence.
2. Publish all five-state, bank-by-surface counts and per-fact transitions,
   not only the terminal winner.
3. If R is the sole `I`, retain it as an authored practical scaffold; do not
   replicate or tune this colour task ahead of the unqualified Q0 writer.
4. If C is `I` or both are `I`, stop this replay-allocation line at the
   current load and advance Q0.
5. If neither is `I`, preserve the exact failure subtype and stop. No best
   checkpoint, extra epoch, bank replacement, coefficient, or seed rescue.
6. Only after selective Q0, and only if causal replay remains blocking, run
   the two-fit equal-new-dose loss-separated test above. For claim-bearing
   conditional W1, retain the already reviewed full two-root/two-map design;
   this colour scout cannot replace it.

The running experiment already contains four fits. This matrix authorizes
**zero additional fits** from its outcomes. A later equal-new-dose causal
pair would be two new development fits; a complete conditional W1 remains the
separately budgeted eight-fit program after qualified W0.

## Prospective source custody

- `research_notes/astra_memos/receipts_20260912/astra_sequential_memory_design_20260912.md`
- `research_notes/astra_memos/receipts_20260912/astra_sequential_memory_corpus_handoff_20260912.md`
- `research_notes/astra_memos/receipts_20260912/astra_sequential_memory_pair_handoff_20260912.md`
- `research_notes/astra_memos/receipts_20260912/astra_sequential_memory_launch_20260912.json`

No outcome-bearing source was opened before this matrix was frozen.
