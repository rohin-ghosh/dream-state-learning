# Independent post-training audit: PCFL vertical DEV v2.1 writer

**Date:** 2026-09-13 UTC  
**Scope:** prospective writer/data/readout audit only. I changed no PCFL source,
fixture, model, tokenizer, adapter, job, or GPU state.  
**Evidence cut:** current repository through `cf5308c0`, including the completed
Q0 full-dose, memory-dose/replay, Level-1, contrastive-perception, and L2
public-record results; contrastive keyed-discrimination v2 is design evidence
only because it has not run.

## Verdict: the PCFL experiment is right; the exact writer is not yet qualified

The PCFL world, child-authorship boundary, two-SLEEP chronology, local-memory
API, source controls, and content-versus-format endpoints are the strongest
integrated experiment currently specified. Do **not** replace it with another
authored proxy.

However, the exact v2.1 SLEEP fit should not yet be described as a likely
working writer. It combines four individually reasonable choices in a
combination that no completed result supports:

1. fresh clean-base rank-8 LoRA;
2. full-response EVENT/LINK causal-LM targets;
3. only `3e-5` for 200 updates; and
4. memory-only batches padded with **loss-active synthetic PAD targets**.

The closest positive writer evidence used `3e-4`, explicit preservation
replay, and distinct-source interleaving. The closest objective-matched
negative evidence says that `3e-5`--`1e-4` on a few dozen child records can
lower loss without changing greedy keyed behavior. Q0 further shows that a
balanced conditional corpus at `3e-5` can converge toward a global output bias
instead of the requested keying. These do not prove PCFL will fail—its
high-entropy exact rows and explicit local addresses are a better surface than
Q0's binary actions—but they make the current recipe an unsupported gamble.

There is also one actual causal incompatibility: loss-active PAD is not a
neutral dose equalizer. `S1_AUTH` has three PAD sources while `S1_ATOMS` has
six; `S2_FULL` has one while `S2_OLD_REPLAY` has three. Parser-disjointness and
a generic canary cannot prove that gradients from `padvoid x y ...` are inert
on the learned memory or route surface. Therefore an AUTH advantage can bundle
LINK information with *less synthetic PAD training*, and a FULL advantage can
bundle NEW information with the same difference. This is the same class of
arm-visible training nuisance that the independently passed keyed-contrastive
v2 protocol correctly removed.

My disposition is **small prospective rework before implementation**, not a
new architecture or a delay behind more proxy experiments.

## What the completed writer evidence actually transfers

| Evidence | Exact result | What it licenses for PCFL | What it does not license |
|---|---|---|---|
| High-dose 16-binding continuation | Rank 8, `3e-4`, 20 optimizer encounters/binding: exact and held `14/16`, `16/16`, `16/16`; inherited action interface destroyed in `2/3` seeds without replay | Rank 8 has enough capacity for this small keyed load; repeated optimizer encounters can make arbitrary bindings extractable | Memory-only high heat is safe; `3e-5` is enough; long EVENT/LINK responses behave like one-token colors |
| Distinct-source interleaving / FOUR_VIEW | At rank 8, `3e-4`, 40 presentations/source, memory `15--16/16`, held lexical `45--48/48`, old action `32/32` in `3/3`; grouped same-source batches previously gave `4/16` | Four varied views, repeated source exposure, source-diverse batches, and replay are the best current engineering default | Random shuffling is equivalent to enforced source interleaving; fresh-base memory-only PCFL is qualified |
| Sequential replay | At the second 320-update cycle, replay retained `64/64` old decisions while no-replay retained `25/64`; both acquired the newest `32/32` | Cumulative old/new replay is necessary to keep in the PCFL S2 construction | Current result is dose-matched or proves all replay schedules |
| Q0 full dose | Rank 8, `3e-5`, 128 updates: loss fell about `1.2 -> .7`, but complete roots failed conditional acquisition/locality; opposite-map adapter deltas had cosine `.9961/.9973` and learned the same broad action motion | Every writer needs a keyed-content and spill assay, not loss alone | More repetitions of a shared response surface necessarily produce conditional memory |
| L2 child public records | Original root and all six low/high cells (`3e-5` and `1e-4`, seeds 0--2), 100 updates across three fits: every report stayed old `4/8`, new `4/8`, legal `16/16`; all records admitted | Child-authored rows can flow through two physical fits, but current small-dose writes can be behaviorally silent | Admitted records plus falling aggregate loss imply extractable memory |
| Level-1 320-update rosters | Rank 8, `3e-4`, 96 authored rows: all four explicitly stated policies reached `47--48/48` over three optimizer seeds | The high-plasticity recipe can install same-distribution authored procedures and exact output schemas | Those procedures transfer reliably to live action/outcome/record interaction |
| Level-1 real-record bridge | With a literal motor example, OFF admitted `7/16`; perception seeds admitted `14/16`, `8/16`, `8/16`, despite all three being near-perfect on the authored exam | Native-dialect formation and source binding must be measured directly; optimizer seed matters | An easy authored exam predicts authentic record quality |
| First contrastive-perception screen | Strict improved mainly by removing fences; permissive content was OFF `23/24`, PLAIN `17/24`, CONTRASTIVE `19/24`; targets had a perfect negate-earlier shortcut | Strict format and semantic content must remain separate | Low training loss or canonical formatting is semantic learning |
| Keyed-contrastive v2 | Independently audit-passed **protocol**, unrun | Its answer-hidden candidate/content/native split, distinct-source batches, and fully masked tensor padding are good patterns | Any efficacy result, or permission to assume contrast wording solves PCFL |

## Audit of the exact PCFL fit

### Rank 8: supported; keep it fixed

Rank 8 is not the current bottleneck. It has already carried 16 arbitrary
bindings and three replayed 16-fact banks. PCFL S1 contains eight EVENT and
four LINK child rows behind 17 query blocks. There is no evidence-based reason
to spend DEV roots on rank 16 or a rank sweep. If v2.1 fails after a qualified
rank-8 dose, the failure should first be localized to acquisition, extraction,
scope, or native use—not relabeled as capacity.

### `3e-5` and 200 updates: unsupported as a sufficient dose

PCFL presents each query-response block under eight wrappers for five epochs,
so each block is targeted **40 times** and each fit executes **200 updates**.
That repetition count is sensible. The unsupported part is the ten-fold lower
learning rate relative to the only robust keyed-extraction recipe.

The completed comparisons bracket the risk:

- `3e-4` with 20--40 encounters/source can extract small supplied maps;
- `1e-4` with 100 updates on the L2 child-record surface stayed greedily flat
  in all three seeds; and
- `3e-5` with 128 conditional Q0 updates learned a broad common response
  direction rather than the map.

Because the objectives and target lengths differ, none of those numbers can
simply be copied into PCFL. The correct answer is one objective-matched
calibration on the already-required disposable PCFL formation root, not a
broad rank/LR/dose sweep and not blind faith in `3e-5`.

### Full-response CE: scientifically allowed, but easy to misread

EVENT/LINK targets contain many shared grammar tokens and relatively few
opaque content fields. Full-response CE can lower aggregate loss by learning
`EVENT ... AT ... DID ...` or a frequent row while still missing the address
binding. Q0's global action motion and the contrastive screen's fence removal
show both versions of this failure.

The primary PCFL semantic-exact generation score protects the final claim:
format alone cannot pass it. But the fit receipt currently reports only total
loss, so a failure cannot be localized. The writer needs content-sensitive
diagnostics described below; it does not yet need a new loss.

### The wrapper/read interface is a local API, not held-surface extraction

All eight readout wrappers `W0..W7` are also training wrappers, and the READ
addresses are the trained addresses. A local-service pass therefore proves
exact addressed carriage through the system's frozen API. That is legitimate
and useful, but it is not unseen-wrapper transfer. State it that way.

One ninth, never-trained wrapper is a cheap diagnostic. It must not replace
candidate-free success through the actual frozen API, but it distinguishes a
row bound to exact request prose from a more robust address binding.

### Native route use is a second, currently unsupported transfer

The adapter is trained to answer goal-blind `READ ...` requests with exact
memory blocks. The mandatory native endpoint instead asks the same mounted
model to solve a ROUTE task without issuing the trained local read. Nothing in
the corpus teaches that cross-interface use. Allen-Zhu--Li's main relevant
warning is exactly that source-text fit can coexist with failure on a new QA
use surface. This repo's Level-1 result supplies the closer analogue: a policy
at `48/48` in its authored JSON exam did not reliably survive the live
PREDICT/ACT/record interface.

Keep the native endpoint—it is the stronger architectural result—but report
it as a separate **native-use gate**, not evidence that the local writer did or
did not store the rows. At minimum, preserve the S1 service-carriage result
and its failure label even if native reachout stops S2. Do not repair native
failure by putting ROUTE answers, future goals, or authored action traces into
SLEEP; that would cross the thinker/compiler line.

## Minimal changes to freeze before source authoring

### 1. Delete loss-active synthetic PAD; use truthful replay fillers

Keep 20 slots, eight wrapper views, batch 4, and the same update count. Replace
every loss-active `PAD_S*` response with an output-blind, predeclared replay of
an already admitted child block available to that arm:

- S1 AUTH/TWIN/PERMUTE: 17 original blocks plus three balanced EVENT replays;
- S1 ATOMS: 14 original EVENT-bearing blocks plus six balanced EVENT replays;
- S2 FULL: 19 original blocks plus one balanced OLD replay;
- S2 OLD_REPLAY: 17 OLD blocks plus three balanced OLD replays.

Choose filler addresses before model output from structural slot indices, and
balance how often each underlying child row appears. ATOMS then becomes the
stronger scientific baseline: equal slots/updates spent on more atom rehearsal
rather than on links. OLD_REPLAY likewise spends its absent-NEW capacity on
more truthful OLD rehearsal. The compiler only exact-copies accepted child
bytes, so this does not originate meaning or cross the boundary.

If exact target-token equality cannot be achieved with truthful replays, do
not synthesize a trainable placebo. Match slots, views, batches, and updates;
report active semantic-token totals and treat the residual token difference as
part of the bounded link/new-data intervention. Post-EOS tensor padding may be
used only with `attention_mask=0` and label `-100`, with the same invariance
test already specified by keyed-contrastive v2.

### 2. Make source diversity an invariant, not a hoped-for shuffle outcome

Preseal a batch schedule such that:

- no batch contains two wrapper views of the same query slot;
- no batch repeats the same underlying child span where a disjoint assignment
  is feasible;
- S1 LINK requests are distributed among EVENT/replay requests rather than
  clustered; and
- each S2 NEW request is placed in a different batch with OLD/replay requests.

Use the same structural batch positions and RNG streams across paired arms.
This is the smallest faithful transplant from SEQ-113: its causal change was
distinct-source interleaving, not merely lexical variety.

### 3. Qualify the dose on the disposable authentic formation root

Turn the already-required disposable formation root into a writer-calibration
root after its grammar is frozen. Use only its own exact child-authored rows
and the final replay-filler/batch construction above. It never enters DEV.

Run this predeclared sequential rule:

1. `CAL_LOW`: rank 8, current `3e-5`, 200 updates.
2. If and only if CAL_LOW misses final semantic carriage while integrity is
   valid, run `CAL_HIGH`: identical tensors, rows, order, dropout streams,
   clipping, and 200 updates, changing only LR to the supported `3e-4`.
3. Select LOW if it passes. Otherwise select HIGH only if it passes. If both
   fail, stop with a writer barrier; do not add rank, more epochs, checkpoint
   selection, or a third recipe.

A calibration pass requires the existing candidate-free S1 EVENT/LINK
semantic thresholds, zero usable wrong-root/unseen rows, and the generic
canary/no-collapse gate. Native ROUTE success must be logged but must not
select the writer rate: it is a separate use-interface property. This costs at
most two objective-matched fits and validates the exact thing the 14-fit DEV
assumes.

The final checkpoint remains the only selectable checkpoint. Saving
`0/40/80/120/160/200` diagnostics is allowed, but no intermediate result may
be promoted.

### 4. Add four no-training diagnostics

For C0 and every final fitted state, save:

1. **Grammar versus content NLL:** target-token NLL separately for fixed
   grammar/separators/EOS and for child-authored opaque field tokens.
2. **Same-shape semantic margin:** conditional log probability of the correct
   complete block minus the best type/row-count-matched wrong registered block,
   including EOS. Candidates are scorer-side only and never enter a prompt.
3. **Candidate-free confusion table:** for each READ address, which registered
   row/block—if any—the raw generation actually emitted, plus unique-output
   count. One repeated legal block is then visibly a global-memory habit.
4. **Unseen-wrapper sidecar:** one frozen ninth wrapper over every supported
   address, scored semantic and strict, diagnostic only.

These are cheap localizers. They cannot rescue failed candidate-free semantic,
locality, canary, route, or formation gates.

## Recommended frozen writer statement

After the four repairs above, the most defensible prospective statement is:

> Rank 8 is fixed. Exact accepted child EVENT/LINK spans are trained through
> varied addressed views, truthful balanced replay, and source-diverse batches.
> A disposable authentic PCFL root selects between only the current low heat
> and one predeclared evidence-backed high heat using final candidate-free
> carriage, scope, and interface gates. The two untouched DEV roots then use
> that recipe unchanged. Aggregate loss and strict syntax are diagnostics;
> semantic addressed retrieval and later action are required outcomes.

This does not make success certain. It removes the unsupported scalar gamble,
the PAD confound, and the two easiest false wins while preserving the core
experiment: the child acts, observes, authors EVENT/LINK rows, SLEEP copies no
meaning the child did not supply, and later behavior must use what was written.

## Decision summary

- **Keep:** PCFL v2.1 world, exact child spans, rank 8, all-layer LoRA,
  cumulative clean-base S2 refit, eight varied requests, response-only loss,
  semantic/strict split, candidate-free service/native routes, TWIN/PERMUTE,
  wrong-root/cuts, canary and rollback.
- **Change before implementation:** loss-active PAD -> authentic replay;
  random shuffle -> explicit source-diverse/OLD--NEW interleaving; disposable
  root -> bounded LOW-then-HIGH writer qualification.
- **Add diagnostics, not gates:** grammar/content NLL, correct-vs-wrong block
  margin, raw confusion/entropy, unseen wrapper.
- **Do not add:** rank sweep, authored easier substitute, parent text, oracle
  route targets, compiler-generated EVENT/LINK meaning, best-checkpoint search,
  or an interpretation that formatting/loss alone is memory.

## Evidence consulted

- `2026-09-13_pcfl_vertical_dev_v2_synthesis.md`
- `2026-09-13_pcfl_vertical_dev_v2_exact_build_ledger.md`
- `2026-09-13_pcfl_vertical_dev_v2_prospective_binding_register.md`
- `2026-09-13_pcfl_vertical_dev_v2_prospective_binding_final_skeptic.md`
- `2026-09-13_q0_fulldose_v2_terminal_independent_raw_reduction.md`
- `2026-09-13_q0_attempt2_corpus_and_canary_forensic.md`
- `2026-09-13_l2_public_record_independent_terminal_reduction.md`
- `2026-09-12_high_dose_memory_continuation_terminal_audit.md`
- `2026-09-12_interleaved_replay_three_seed_terminal_postaudit.md`
- `2026-09-12_sequential_old_new_fixed_budget_*` and the independently
  recounted SEQ-118 summary
- `2026-09-13_level1_second_roster_result_blind_claim_audit.md`
- `2026-09-13_level1_skill_to_real_record_terminal_reduction.md`
- `2026-09-13_contrastive_perception_independent_terminal_reduction.md`
- `2026-09-13_contrastive_keyed_discrimination_followup_protocol.md`
- `2026-09-13_contrastive_keyed_discrimination_v2_reaudit.md`
- `2026-09-13_allen_zhu_li_birth_sleep_recipe_translation.md`
