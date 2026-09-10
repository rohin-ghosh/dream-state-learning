# Extractable SLEEP compiler v1 — initial deltas for independent review

Date: 2026-09-08

Status: proposal preparation only. No implementation or scientific execution
is authorized.

## Architecture delta

No new cognitive organ. The architecture remains:

```text
THINK -> grounded lived evidence
DREAM -> finite-context reconstruction, no weight write
SLEEP -> compile grounded evidence into training views, then write child LoRA
```

Parenting remains upstream of SLEEP: it helps the child produce better
thinking and action experience. Parent text may condition child behavior but
is not itself evidence of learning and is not a response-loss target.

## Loop delta

Separate two meanings previously mixed under “sleep frequency”:

1. **Writer scheduling effect:** how splitting a fixed immutable evidence set
   into one or several writes changes the final adapter when total target
   tokens, optimizer updates, seed, initialization, rank, LR schedule, and
   replay exposure are matched.
2. **Closed-loop cadence effect:** how earlier committed adapters change later
   thoughts/actions/outcomes, hence the future evidence distribution. This is
   the system-level reason cadence may matter.

Do not infer either effect from an experiment that changes row count, epochs,
optimizer tokens, evidence, or policy-generated experience at the same time.

## Compiler delta

For each immutable public action/outcome evidence identity, candidate compiler
views may include:

- the child-native committed context -> thought/action/outcome continuation;
- a revision that makes the prediction/error/credit assignment explicit;
- diverse re-expression or order while preserving every fact and source ID;
- a scoped contrast against a related success/failure;
- a future-cue -> recalled lesson -> thought/action continuation showing use.

Compiler views change training dose, never independent evidence count. They
must preserve source identity, truth conditions, scope, and native action
dialect. Any unsupported connection is ineligible.

## Claim delta

Keep four outcomes separate:

- **storage:** lower held-out target NLL or exact continuation recovery for
  evidence excluded from compiler-view generation;
- **extraction:** correct recovery from a new cue/order/wording without the
  source text in context;
- **behavioral use:** improved thought/action on fresh homologous tasks after
  context reset and adapter reload;
- **interface/no-harm:** marker/action validity and generic behavior preserved
  relative to the previous committed child.

No storage metric alone supports an extraction or learning claim.

## Visibility delta

- Static writer assay: compiler sees only a development evidence deck. Its
  extraction questions, behavioral probe instances, and expected answers are
  hidden until compiler and trainer source freeze.
- Closed-loop cadence assay: every arm sees the same task generator and
  budget, but later evidence is intentionally policy-dependent. Final sealed
  evaluation remains invisible to every development component.
- Audit reviewers see complete source identities, seeds, evidence/view/dose
  receipts, and results only after execution.

## Test delta

Minimum static matched assay:

1. native grounded continuation only;
2. diverse re-expression/order with the same unique evidence;
3. diverse re-expression/order plus future-cue use continuations;
4. a dose-matched sham-repetition control if budget permits.

Match total response-target tokens or optimizer-token exposure, not epochs.
Use multiple explicit training seeds. Score storage, extraction, use, and
interface separately.

Minimum cadence decomposition:

- **fixed-data dose split:** one final write versus multiple scheduled writes
  over the same frozen evidence, with matched total exposure;
- **closed-loop cadence:** delayed versus periodic writes over the same total
  episode budget, allowing policy-dependent experience to differ by design.

The static test licenses a compiler choice. The closed-loop test estimates
whether that compiler creates a useful experiential feedback loop.

## Existing evidence correction

The R2 long-life runner currently executes `compile_sleep` and
`train_adapter` (`v1_frozen`, bare text, `lr=1e-4`, three epochs), not
`compile_native` and `train_adapter_v21`. The earlier write-swarm changes row
count and optimizer exposure across arms. Both result families remain
exploratory; neither certifies this proposal.
