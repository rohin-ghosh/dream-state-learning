# Writer/SLEEP evidence-chain audit

Date: 2026-09-12 UTC
Scope: fresh-context, read-only scientific audit of checked-in artifacts,
current writer source, and Astra A1/A2/B0 remote outputs. No remote job was
started, stopped, resumed, or changed. Builder-owned source was not edited.

## Bottom line

The evidence supports **parametric carriage**, but not yet a qualified SLEEP
writer:

- A LoRA can make supplied routines and canonical continuations persist after
  their source text is removed.
- What is extractable depends strongly on the rendering and on the optimizer
  seed. Current canonical-frame memory is either broad spill or nearly null,
  not selective memory.
- Some writers preserve the action interface; others destroy it. Interface
  preservation is therefore a noncompensatory gate, not an implementation
  detail.
- The life runner repeatedly rebuilds an adapter from the frozen base over a
  cumulative corpus, but no completed experiment isolates OLD knowledge,
  writes an identity-disjoint NEW bank, and then shows both survive. Repeated
  execution is not a retention result.

The highest-value next writer experiment remains the reviewed **V10R1
multi-key conditional native-action gateway (W0)**. It directly asks whether
the writer can store several opposing, situation-conditioned actions without
turning them into one global habit. Only after a W0 pass should the
identity-disjoint **OLD+NEW cumulative replay test (W1)** run.

## What is actually supported

| Property | Strongest terminal evidence | Verdict |
|---|---|---|
| Fitting supplied text | Legacy writers lower training loss; current A1 bank-0 fits completed 9,693 updates / 749,985 processed tokens with finite terminal losses. | **Supported as optimization**, not by itself memory. |
| Parametric carriage | Legacy A carried the bootstrap-supplied routine on both panels in 3/3 source lives (mean ON-OFF `+0.0386` report, `+0.0161` disjoint). Canonical frame prompts also change after fresh-base LoRA fits with the source rows absent. | **Supported narrowly:** routines and cue-conditioned continuations can live in the adapter. |
| Extractability | The original car QA route did not yield clean owner binding, while canonical completion frames produced large changes. Child-rendered/repaired CF-b reached pooled completion `0.822` versus synthetic F `0.913` over three banks in the earlier screen. | **Cue- and rendering-dependent.** There is no qualified free-action relay from stored fact to decision. |
| Locality / specificity | F seed-0 and seed-1 pooled completion was `0.451` and `0.830`, but spill was `0.264` and `0.392` against the registered `0.03` ceiling. Equal-exposure K1/K4/K16 bank-0 spill was `0.4389/0.3446/0.3326`; higher repetition did not fix it. | **Failed.** Owner signal exists inside a broad completion habit. |
| Fit stability | Identical effective F examples reproduced exactly across machines at the same configured seed, but seed 0 versus 1 changed pooled completion `0.451 -> 0.830`. The new A1 bank-0 seed-2 versus seed-3 outputs diverge again (below). | **Failed as a stable recipe.** Variance is primarily optimizer-seed/run variance, not a demonstrated machine effect. |
| Native interface | Legacy A did not show a collapsed replicate, but strict native action validity was not fully measured. Legacy C scored `0.000` on both panels and C-TMEM was harmful; their targets did not begin in the child's native marker dialect. One R5 first-sleep candidate passed a 1.00 parseable-ACT canary, but the score delta was inside noise. | **Possible but not qualified.** Every writer needs strict fixed-denominator action and unrelated-interface gates. |
| Retention through later learning | Historical lives contain many accepted sleeps, and one recovery-contaminated seed ended ON `0.4878` versus OFF `0.4672`. No result separates OLD content from a later unrelated NEW write. | **Not demonstrated.** |
| Cumulative replay | `compile_sleep()` carries the prior corpus forward and deduplicates it with newly rendered rows; `run_life_v2` then trains a fresh adapter from the frozen base. | **Implemented as replay/reconstruction, not experimentally qualified.** |

### Important implementation qualification

The current comments call the cumulative corpus "interleaved," but the
checked-in legacy path forms `prior_corpus + new_texts`, deduplicates in that
order, and the v1 trainer iterates that list without an explicit shuffle.
Thus the present life path is **old-then-new concatenated replay**, not the
deterministically interleaved OLD+NEW union required by W1. Also, every sleep
starts from the frozen base: continuity exists only through replayed corpus
bytes; it is not sequential parameter retention.

## Current Astra runs: terminal versus live

Read-only polls were made at 06:56--07:06 UTC.

### A1 — synthetic F writer, new optimizer seeds

The complete A1 jobs are still live, but their individual bank-0 fit and eval
artifacts are terminal.

Both bank-0 fits used the same effective corpus:

```text
corpus_sha = 15adaeff18a685c0
items_sha  = 55e5bca9dadd19ea
items      = 12,924
steps      = 9,693
tokens     = 749,985
rank       = 8
```

| Train seed | Final loss | Target frame, OFF -> ON | Similar-owner, OFF -> ON | Wrong-relation/bicycle, OFF -> ON | Reading |
|---:|---:|---:|---:|---:|---|
| 2 | `1.093895` | `.260 -> .685` | `.250 -> .401` | `.258 -> .669` | Strong write, but nearly as strong on the wrong relation: broad frame habit. |
| 3 | `1.162619` | `.260 -> .258` | `.250 -> .253` | `.258 -> .258` | Essentially no extracted effect despite the same corpus/dose. |

ON candidate mass was approximately `.998` for seed 2 and `.973--.980` for
seed 3, so these numbers are not explained by an empty candidate
distribution. Together with prior bank-0 seed-0/1 completion `.379/.874`, the
four observed optimizer seeds span `.258--.874`. This is already useful
partial evidence of high writer-fit variance; it does not become a completed
three-bank A1 result until the remaining fits/evals and final summary exist.

### A2 — repaired child-rendered CF-b writer

- Attempt 1 for seeds 0/1/2 is terminal as **profile-cap refusal**, not a
  scientific result (`25.2/27.8/26.8` projected minutes versus a 25-minute
  cap).
- Fresh attempt-2 seed-0 and seed-1 bank-0 fits and evaluations are terminal.
  The identical corpus (`18ff624e6732643e`, item hash
  `cf73d4d9442e524b`) produced finite losses `1.311253` and `1.341968` after
  10,614 updates / 749,994 processed tokens. Canonical target completion was
  `.230 -> .790` at seed 0 and `.230 -> .736` at seed 1. But bicycle-frame
  completion also rose `.239 -> .720/.627`, and similar-owner completion
  `.238 -> .473/.503`: both writes are broad habits, not selective bindings.
- Their bank-1 fits were live and seed 2 remained queued at the cutoff. No
  attempt-2 multi-bank report or final `summary.json` existed.

A2 can estimate whether the earlier constrained child-frame result is stable
to writer seed. It cannot prove parenting or autonomous record formation:
the corpus used an explicit canonical-ending instruction, the harness
repaired missed endpoints, and the whole child row was loss-bearing.

### B0 — fresh post-outcome slot plumbing

The matched A/B attempt-2 processes were live on node 1. B had completed its
initial probe (`0.4872`) and first eight wake episodes; A was still in its
initial probe at the last detailed poll. Neither arm had reached sleep 32.
Therefore there was no articulation-gate receipt, fitted adapter, reload,
neutral pre/post comparison, or terminal result.

B0 is deliberately `QUARANTINE_TASK_EXPOSED`. It tests whether the missing
post-outcome slot produces enough grounded child records for the writer
plumbing. It is not a clean child, parenting, H1/H2, retention, or outcome-
learning experiment.

The B0 implementation threshold is not a paper acceptance gate:

- a record is `admit_hi` when it is grounded (`G`), its number check is not
  false (`N != false`), and it is not a duplicate;
- first-person form `F` is measured for `artic_hi` but is **not required** by
  `admit_hi`;
- the enforce path trains B only after at least **64 cumulative deduplicated
  admitted records**, not 64 new first-person records;
- the current run predates the later immutable gate-to-label-to-adapter
  trainer-receipt code and cannot inherit that stronger custody after launch.

The strongest admissible positive B0 statement remains: in one uninterrupted
task-exposed scout, N grounded records joined earlier ACT receipts; a finite
child-body-only fit reloaded; and descriptive fresh-context Scratchpad ON/OFF
differences were observed. Anything stronger requires a successor.

## Exact next gates

### W0: V10R1 `MULTIKEY_BINDING_PASS`

The experiment is not implemented in the current checkout. Its effective
V9+V10+V10R1 contract requires:

- two disjoint roots, two complementary maps per root, hence **four
  clean-base rank-8 fits**;
- exactly 128 rows per fit, batch 1, two epochs, **256 optimizer updates**,
  `3e-5` learning rate, context-masked loss, and only exact native
  `ACT: a0\n` / `ACT: a1\n` plus EOS targets;
- all four adapters and both roots to pass every applicable gate below.

Per root:

1. **Assay:** explicit-map OFF oracle BA `>= .90` for both maps.
2. **Optimization:** every one of 16 keys in both adapters has median
   action-choice NLL gain `>= .50 nat`; map mean-gain asymmetry `<= .25 nat`.
3. **Binding:** for each adapter, own-map generated BA `>= .80`; accuracy
   `>= .75` in each stratum; directional margin `>= .50` on at least `12/16`
   keys and `6/8` in each stratum; gain over OFF `>= .20`; own-minus-opposite
   BA `>= .50`.
4. **Interface:** overall validity `>= .95`, per-stratum validity `>= .875`,
   zero adapter multiple-ACT outputs, and exact `8/8` unrelated native-action
   outputs for OFF and every adapter.
5. **Spill:** in each of four fixed spill families, binary candidate TV from
   OFF `<= .05` and absolute legal-ACT-rate change `<= .05`.

Both roots passing all five yields `MULTIKEY_BINDING_PASS`. The ordered failure
labels distinguish invalid assay, inadequate optimization, interface damage,
binding with spill, and a valid negative. A pass establishes supervised
seen-key conditional action carriage only.

### W1: `TWO_BANK_CUMULATIVE_REPLAY_PASS`

Run only after W0 passes, using identity-disjoint NEW keys and an explicitly
interleaved OLD+NEW clean-base rebuild. Required independently for OLD and NEW:

- every cumulative key still clears the absolute W0 `.50 nat` per-key gate;
- mean per-key-median gain `KMG_CUM >= .8 * KMG_SINGLE`;
- at least `12/16` keys and `6/8` per stratum individually retain at least
  80% of their single-bank per-key gain;
- cumulative generated BA gain is at least 80% of the matching single-bank
  BA gain, and each bank still passes the full absolute W0 gates;
- OLD-only is neutral on NEW, NEW-only neutral on OLD, and every adapter
  neutral on the other root's banks;
- per-key candidate TV and absolute legal-ACT-rate change from OFF are each
  within `.05`.

This qualifies two-bank cumulative-replay **coexistence/reconstruction**. It
still does not imply unrehearsed retention or sequential weight continuity.

## Highest-value next action

1. Let A1/A2/B0 finish unchanged and use only their terminal artifacts for
   their narrow diagnostics.
2. Implement and execute W0 V10R1 with its dedicated module/test/launcher;
   do not reuse generic trainer/prober defaults that violate its exact dose,
   token-boundary, raw-output, or precision contract.
3. If and only if W0 passes, immediately run W1. If W0 fails, its ordered
   label identifies whether to repair optimization, action-interface
   preservation, locality, or conditional binding before spending on long
   children.

More F/CF repetition is lower value. It can refine the variance estimate, but
cannot answer the actual blocking question: whether several conditional
native actions coexist in one writer without becoming a global habit.

## Evidence basis

- `research_notes/2026-09-11_legacy_writer_seed0_7_8_terminal_closure.md`
- `research_notes/2026-09-11_cross_node_effect_adversarial_audit.md`
- `research_notes/2026-09-11_cell_f_next_action_advisory.md`
- `research_notes/2026-09-11_decisive_evidence_path.md`
- `research_notes/2026-09-12_end_to_end_goal_closure_synthesis.md`
- `research_loop/changes/chg_20260911_multikey_writer_gateway_v9_simple/exact_scope.md`
- `research_loop/changes/chg_20260911_multikey_writer_gateway_v10_simple/exact_scope.md`
- `research_loop/changes/chg_20260911_multikey_writer_gateway_v10r1_simple/exact_scope.md`
- current `organism_v6/sleep_compile.py`, `train_adapter.py`,
  `run_life_v2.py`, and `preschool.py`
- read-only node-1/node-2 process, run-tree, log, train-metadata, and
  evaluation-JSON inspections at 06:56--07:06 UTC.
