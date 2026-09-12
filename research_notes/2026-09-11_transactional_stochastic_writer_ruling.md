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
   prior candidate result. `K` remains undecided until the running fit-repeat
   diagnostics finish.
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
