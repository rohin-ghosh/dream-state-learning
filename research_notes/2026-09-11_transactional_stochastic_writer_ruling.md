# Transactional stochastic writer: fit-seed and commit ruling

Date: 2026-09-11 PDT (written 2026-09-12 UTC)

Status: architecture/scientific-hygiene ruling for the future longitudinal
Dream--LoRA--Think writer. It does not authorize implementation or execution.

## Why this is necessary

The apparent cross-node writer discrepancy was traced to a training-seed
difference, not hardware. On identical corpus bytes, fitting is reproducible
for a fixed training seed, but different training seeds can produce materially
different bindings. In the seed-1 synthetic frame banks, train seed 1 bound
all three banks while train seed 0 failed on two. The terminal same-corpus
repetitions will estimate this basin more directly.

Therefore a sleep write is not merely `corpus -> adapter`. It is a stochastic
transaction whose yield and selection rule are part of the mechanism. A
retry-until-good rule chosen after inspecting a deployment or report score
would be hidden post-selection and could make an ineffective writer look
reliable.

## Frozen transaction

Before the paper-grade longitudinal run, freeze all of the following:

1. **Candidate count and seed schedule.** Each sleep has exactly `K` candidate
   fits, or stops early at the first qualifying fit. Candidate seeds are
   deterministically derived from the sealed run identity, sleep index, and
   candidate index. They cannot depend on any model output, score, report, or
   prior candidate result. Within a matched experimental block, paired arms
   use the same candidate-seed schedule; an arm-specific seed derivation would
   confound treatment with optimizer luck. `K` remains undecided until a
   separate development calibration exists.
2. **One writer recipe.** Every candidate starts from the same frozen base and
   the same complete committed corpus using the same rank, target modules,
   masks, dose, learning rate, and optimizer. No within-life switch to another
   recipe, rank, or corpus renderer is allowed after a candidate fails.
3. **Source-local qualification only.** Candidate qualification may inspect
   predeclared source-derived bind/locality checks, old-memory retention
   checks, and generic native-interface/non-harm canaries. These checks are
   constructed and frozen before fitting and are disjoint from deployment,
   report, final-test, and parenting-comparison panels.
4. **First pass, not best score.** Examine candidates in scheduled order and
   commit the first candidate satisfying every hard gate. Do not choose the
   highest-scoring passing candidate. This limits winner's-curse selection.
5. **Atomic commit or no write.** Adapter, corpus head, source cursor,
   qualification receipt, and ancestry move together. If no candidate passes,
   retain the previous committed child and advance no active-writer ancestry.
   The raw experiences remain in the lossless ledger for later replay.
6. **Nothing disappears.** Preserve every candidate adapter, fit receipt,
   evaluation record, rejection reason, and seed. A rejected candidate is an
   observed writer failure, not an infrastructure omission.
7. **No repeated lottery on unchanged evidence.** Exhausting `K` produces
   `NO_COMMIT`, not a rollback: the previous adapter remains mounted and the
   uncommitted raw experiences remain in the lossless ledger. The system may
   not reopen the identical corpus digest later under a fresh `K`. A later
   transaction requires a new corpus digest and still pays its full writer
   cost. Rejected adapters and their compiled derivatives are quarantined and
   never become later DREAM or SLEEP inputs.

The writer must never use the same benchmark outcome that will later measure
learning to decide which adapter is mounted. Parent and child likewise never
see the qualification scores.

## Required measurements

Report, over sleeps and independent lives:

- first-candidate qualification rate;
- qualification rate within `K` candidates;
- distribution of candidate index at commit;
- no-commit/rollback rate;
- failures split by binding, locality, retention, and interface gate;
- GPU-hours per attempted and committed write; and
- final conclusions both including the full mechanism and stratified by
  whether a sleep committed.

These quantities are part of writer reliability. A system that succeeds only
after many discarded seeds may still be a usable transactional learner, but
it is not a reliable one-shot writer and must pay and disclose that selection
cost.

The qualification panels are part of training-time selection and therefore
are not independent scientific evidence. The untouched longitudinal analysis
must be intention-to-treat: every assigned life and every `NO_COMMIT` remains
in the headline denominator. Results stratified by whether a sleep committed
are descriptive only, because commitment is post-treatment selection. The
scientific object is explicitly the complete frozen `K`-attempt
compile--fit--qualify--commit policy; first-candidate qualification measures
one-shot yield, while qualification within `K` measures transactional yield.

## Calibrating `K` without contaminating the final run

Do not infer `K` from the current child-frame cells: all six child
root-by-variant cells fail locality, and selecting among systematically broad
habits cannot repair the representation. V10R1 remains the unchanged one-shot
feasibility gate.

Only after V10R1 passes, calibrate on identity-disjoint development roots:

1. Fit every scheduled candidate through a frozen `K_max`, even after the
   first one passes, so the candidate-yield distribution is observable.
2. Include wrong-root, shuffled and null-source transactions to measure false
   qualification, not only true-writer yield.
3. Estimate pass-within-`K` directly across independent transactions. Do not
   substitute `1-(1-p)^K`: candidates sharing a corpus are not independent.
4. Select the smallest `K` satisfying a predeclared operational-yield target,
   false-accept bound and GPU budget. If development support is too small,
   choose `K` from the compute budget alone and make no calibrated-reliability
   claim.
5. Freeze `K`, seed schedule, gates, thresholds and writer recipe before any
   new confirmation lineage begins.

Integrity, dose or tokenization failure invalidates a transaction rather than
consuming another scientific candidate. A valid fit that fails binding,
locality, retention or interface consumes its candidate ordinal. Retention is
checked contemporaneously against the immediately previous committed child on
the same still-valid old memories: absolute old gates must remain satisfied,
at least 80% of prior measured gain must remain, the new memories must be
acquired, and spill/interface gates must still pass. Explicitly contradicted
memories use a separately defined revision gate rather than forced retention.
A later miss on an untouched report panel is an outcome, never grounds for
retroactive rollback.

## Relationship to the current evidence path

V10R1 first asks whether the fixed rank-8 recipe has any conditional-policy
carriage basin at all. Its four paper-scored adapters use the predeclared fit
recipe; it is not converted into a best-of-seeds test. If V10R1 passes, a
separate retention/transaction qualification stage may calibrate `K` and the
source-local gates on development roots before the longitudinal mechanism is
frozen.

This ruling does not claim that fitting stochasticity is biological sleep,
useful exploration, or learned self-repair. It is an engineering and
scientific-control response to measured optimizer sensitivity.
