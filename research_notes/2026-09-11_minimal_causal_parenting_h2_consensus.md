# Minimal causal parenting / H2 consensus candidate

Date: 2026-09-11

Status: **unratified design candidate; do not implement or launch from this
document.** Two independent reviewers cross-critiqued the design and converged
on the staged protocol below. Current mechanism and parenting scouts continue
under the simple-hygiene ruling. The full C11 guard remains parked until the
final paper-grade run.

## Decision in plain language

The historical saved adults cannot answer whether parenting made subsequent
sleep-based learning better. They were raised under different conditions and
the present runner cannot preserve a childhood adapter while isolating later
adapter promotion.

The smallest honest next step is therefore:

1. raise one child with one narrow lesson and one otherwise identical child
   with content-neutral support;
2. remove the parent and every wake-visible memory;
3. fork each adult into a learning branch and a shadow-sleep branch;
4. let all four branches experience the same 128-episode task tape;
5. run sleep in every branch, but only mount accepted candidates in the two
   learning branches.

This one-root experiment is an executor and directional canary, not evidence
that parenting works in general. A confirmatory result needs new independent
childhood roots.

## Immediate canary

### Childhood

- Start from one byte-identical clean birth checkpoint.
- Fork it into `P` (targeted adaptive parent) and `S` (active sham).
- Match parent model, timing, turns, tools, context occupancy, and
  tokenizer-counted parent dose. Only the lesson's targeted distinction may
  differ.
- Freeze the parent policies before launch and reset parent state between
  roots.
- Teach one bounded disposition: after informative, verifiable feedback,
  create a grounded first-person condition--action--outcome record; use it
  when its trigger recurs; omit it on matched non-informative cases.
- Use 32 fixed childhood episodes with balanced trigger/non-trigger
  opportunities, followed by one qualified sleep. Do not extend childhood in
  response to observed uptake.
- Parent text stays outside the loss target. Only grounded committed child
  continuations may enter sleep.
- Seal and hash both adult checkpoints. Then remove the parent, lesson,
  conversations, childhood/waking briefs, retrieval state, caches, and all
  other persistent wake-visible text.

### H1 diagnostic before deployment

Use disposable ON/OFF clones on fresh balanced trigger and contraindication
cases. Score correct use and correct non-use separately.

The within-root diagnostic is:

`h1 = (P_ON - P_OFF) - (S_ON - S_OFF)`.

With one root this is directional feasibility only. Restatement or lexical
matching is not uptake.

### Four-cell deployment

Fork the sealed adults into:

- `P-running`
- `P-shadow`
- `S-running`
- `S-shadow`

Keep all four forks from the root on one node and randomize GPU/launch
positions. Run 128 episodes: 16 balanced visits over eight fresh acquisition
tasks. Sleep after episodes 32, 64, 96, and 128. Use entry, episode-64, and
episode-128 fixed-K report probes plus a small untouched terminal transfer
family.

Every sleep opportunity uses the same compiler, trainer, validation,
budgets, and RNG policy. Shadow branches train and preserve candidate
artifacts but never mount them. Later histories and corpora may legitimately
diverge after promotion; forcing byte-identical post-treatment corpora would
block the proposed mediator and test a different question.

Primary score keeps invalid or missing actions in the denominator as zero.
For each branch, average each task's late visits 13--16 minus early visits
1--4. Report three directional canary quantities:

- absolute improvement of the parented running child;
- parented running minus parented shadow improvement;
- `(P-running - P-shadow) - (S-running - S-shadow)`.

All three must point in the favorable direction before scaling. They are not
significance claims and cannot justify endpoint switching after inspection.

Estimated canary cost: roughly 50--80 A40-hours, dominated by 36 A40-hours of
adult waking plus childhood, shadowed sleeps, and probes.

## Hard blockers before a GPU canary

CPU and transactional fixtures must first demonstrate all of the following:

1. both descendants hash-load the same sealed childhood adapter;
2. later sleep extends or cumulatively reconstructs that adapter instead of
   fitting a replacement LoRA from the clean base;
3. zero-new-data cumulative reconstruction reproduces the sealed childhood
   adapter if reconstruction is used;
4. shadow mode executes the complete compiler/trainer/canary path while the
   mounted adapter hash remains unchanged;
5. running mode differs only by promotion of a technically accepted
   candidate;
6. deployment cannot call or expose the parent, lesson, conversations,
   childhood or waking briefs, retrieval state, or caches;
7. no persistent cross-episode text enters wake in any primary arm;
8. task and decode RNG include occurrence/visit index;
9. fixed-K scoring retains invalid and missing actions as zero;
10. before the first sleep, running and shadow descendants produce identical
    results under the common tape;
11. the selected compiler/trainer, not legacy interfaces, is bound into the
    runner;
12. source/provenance validation checks factual support, not merely verbatim
    parent-text leakage;
13. output roots are fresh, transactional, ancestry-hashed, and never resumed
    by path/marker coincidence;
14. failed candidates are retained, the previous adapter remains mounted,
    and analysis is intention-to-treat;
15. all four forks are same-node blocked with randomized execution positions.

If these do not pass, the correct outcome is `NOT_RUN`, not a historical or
partially shadowed substitute.

## Later paper-grade confirmation

Exclude the canary root. Freeze the resulting protocol, then raise new
independent roots. Eight roots are only a structural floor: 32 deployment
forks still give `n = 8`, not `n = 32`. If the root-interaction standard
deviation is about 0.027 and the target interaction is 0.020, approximately
16 roots are needed for about 80% power.

The confirmation therefore targets 16 fresh root blocks, or uses a fixed N
chosen before unblinding from external/blinded variance. Run the same P/S
childhood, sealed H1 assay, and four-cell 128-episode deployment for every
root. Analyze root-block contrasts; programs, visits, checkpoints, and
decoding repeats are nested measurements rather than independent samples.

H1 is tested first. H2 is confirmatory only if H1 passes. H2 additionally
requires positive absolute parented-running improvement, positive
parented-running versus parented-shadow benefit, positive parenting-by-
promotion interaction, terminal retention/no-harm, and a prebound practical
interaction margin. A 252-episode extension may be authorized from feasibility
or blinded precision only, never observed treatment direction.

The full confirmation is approximately 800--1,200 A40-hours at the current
throughput. Enforce the complete paper-grade guard only for that final run.

## Claim boundary

The immediate canary may support only:

> The four-cell executor isolated candidate-adapter promotion, and one
> excluded randomized root showed the reported directional contrasts over
> 128 episodes.

If a multi-root H1 later passes, the bounded claim is that one targeted lesson
caused an adapter-carried skill after parent/context removal. If H2 also
passes, the bounded claim is that targeted parenting increased the early
performance benefit of continued weight consolidation relative to matched
neutral interaction.

This design does not establish superiority to text memory, general learning
on unseen tasks, indefinite continual improvement, or the full experiential
intelligence flywheel.
