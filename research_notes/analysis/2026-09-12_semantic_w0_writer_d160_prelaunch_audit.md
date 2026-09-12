# Semantic W0 writer at `d160e0b2`: fresh prelaunch audit

Date: 2026-09-12 UTC

Scope: read-only scientific and implementation review of commit
`d160e0b26405a7e40eb7de0dca23cfcb94cdbf37`, especially
`organism_v6/semantic_writer_diagnostic.py` and
`tests/test_semantic_writer_diagnostic.py`, against the current end-to-end
synthesis, prospective semantic-writer specification, selective-writer audit,
and terminal semantic-carrier audit present at that commit. I did not inspect
or control a GPU, launch or kill a job, alter builder source, or edit the
coordination notebook.
This verdict is a watcher recommendation and does not alter the builder's
standing authority in `AGENTS.md`.

Audited byte identities:

| Artifact | SHA256 |
|---|---|
| `organism_v6/semantic_writer_diagnostic.py` | `d6ea45ac6bfb5cabe6cbd1224f4cf101e96cbd0e07c029e934c2aa3e03e1ddb0` |
| `tests/test_semantic_writer_diagnostic.py` | `daf0f95a30f5a6a6dedb020c97283ac39addb9648b588a85dfc5bee1ee38622b` |
| `research_notes/astra_memos/ASTRA_SEMANTIC_WRITER_COMPARISON_2026-09-12.md` | `027dc6528971022aef14fdeacca852cc7bb4d1e821813b447b8073d4e96fbf5f` |
| `research_notes/2026-09-12_end_to_end_goal_closure_synthesis.md` | `8040aae702512ac9beffe46775c9274ca1332b5341975d98756de0a0362c06f9` |
| `research_notes/analysis/2026-09-12_semantic_carrier_terminal_watcher_audit.md` | `7eb91d577202ee238f38c8f379f11813515dfef57d19396e2ea71b1ad8d3cfea` |

## Verdict

**REWORK BEFORE LAUNCH.**

The four-fit geometry is a legitimate bounded test of **supervised seen-key
binary conditional-policy carriage under held paraphrases**, and the source is
substantially stronger than the failed V10R1 execution. It does not leak the
map or target through primary prefixes, its marginals are balanced, its
native-action surface prerequisite is valid and narrowly interpreted, and its
four cells cannot be pooled or majority-rescued.

Two locality-reducer defects nevertheless allow a false selective-writer pass.
In addition, the present panel deliberately omits the train-form endpoint
needed to distinguish storage failure from held-form extraction failure, and
the preparation/execution receipts do not yet bind the known native-build risk
or the controller's complete wall-clock lifetime. These are cheaper to repair
before four fits than after a scientifically ambiguous result.

## What is already sound

1. **The estimand is real but narrow.** Training exhaustively crosses eight
   opaque tools, two modes, and eight training templates; held evaluation uses
   the same 16 tool-mode keys under four held templates. The target is
   `orientation(tool) XOR mode XOR map`, with the two map fits carrying exact
   complements (`semantic_writer_diagnostic.py` lines 150-167 and 219-235;
   inherited action equation in `multikey_writer_gateway_simple.py` lines
   152-155). The checks at writer lines 170-183 reject target-only, slot-only,
   mode-only, stratum-only, template-only, and template-by-mode shortcuts in
   both train and held panels. Audit metadata remains outside the rendered
   prompt (lines 207-217). Thus a pass cannot come from a tested marginal.
   It can come from direct lookup of the 16 already-seen tool-mode pairs; that
   is not leakage, but it is why the result is seen-key carriage rather than
   unseen-key compositional generalization.

2. **Freshness and replication boundaries are honest.** The new opaque keys
   and neighbours are disjoint from both inherited W0 and carrier keys (writer
   lines 153-175; tests lines 100-120). The two roots also use distinct key and
   grammar banks and distinct fit seeds. They are deterministic repeated cells,
   not random population draws: the manifest explicitly records
   `training_run_replication=False` and `root_seed_confounded=True` (writer
   lines 45-50), and the synthesis says roots/maps are not independent learners
   (`2026-09-12_end_to_end_goal_closure_synthesis.md` lines 355-361). No
   general reliability or seed-robustness claim is available.

3. **The action carrier is valid for eligibility.** Writer lines 98-119 bind a
   Main-verified proof, the exact terminal capsule/replay hashes, matching
   model/tokenizer inventories, all four `16/16` generation and scoring cells,
   `32/32` swaps per operation, `8/8` native-copy cells, zero truncation and
   zero multiple actions. The terminal audit independently limits that result
   to an inference-only surface (`2026-09-12_semantic_carrier_terminal_watcher_audit.md`
   lines 9-15 and 63-73). The registered native actions are `-mem2reg` and
   `-gvn`; no carrier answer row enters writer train, primary, or locality
   prompts. This is an appropriate positive surface control, not writer data.

4. **Training and request accounting are exact.** The four LoRAs each start
   from a fresh adapter-free base, use rank 8/alpha 16/dropout .05, all seven
   projection families, AdamW `3e-5`, fixed row order, two epochs, and exactly
   256 steps (writer lines 474-504 and 522-558). Evaluation reloads a fresh base
   and verifies the saved LoRA tensor digest (lines 507-519 and 565-585). The
   panel is exactly 1,712 requests: 880 generation, 832 two-candidate scoring,
   400 OFF, and 328 per adapter (lines 195-260). Full LF+EOS response tokens are
   masked/scored and the unequal candidate lengths are explicit (tests lines
   142-157). Fixed seeds, fresh processes, deterministic algorithms, eager
   attention, disabled TF32, and non-shuffled order make the computation
   reproducible on the pinned stack; the two seeds remain root-confounded, not
   replications.

5. **Several controls and failure paths are good.** OFF records are exact
   same-prompt baselines; W+/W- are complementary fits; wrong-root evaluation
   uses the other root's exact OFF primary prefix; missing-mode, unsupported-mode,
   neighbour-key, wrong-root, and native-copy panels are separate. All four
   root/map cells must pass (writer lines 363-422). Sixteen OFF native-copy
   requests run before the first fit and abort with zero fits on failure (lines
   614-621 and 718-726). Stage failures are no-retry, preserve `FAILED.json`,
   and do not seal a report (lines 591-611 and 741-744; tests lines 422-446).
   The inherited process-group limitations are explicitly disclosed rather
   than claimed away (writer lines 11-14).

6. **Thresholds are prospective, not outcome-tuned.** The writer result did
   not yet exist at `d160e0b2`. The specification fixes the inherited per-key,
   BA, map-contrast, interface, and locality thresholds before launch
   (`ASTRA_SEMANTIC_WRITER_COMPARISON_2026-09-12.md` lines 40-53), and writer
   lines 425-434 implement those stated numbers. I found no writer-result-based
   checkpoint choice, best-of-many seed rule, or post-hoc threshold.

## Launch-blocking findings

### 1. Binary-relative locality is blind to common-mode action-habit growth

Writer lines 397-404 reduce each locality item to

```text
abs(q_ON(a0 | {a0,a1}) - q_OFF(a0 | {a0,a1}))
```

where `q` is obtained by renormalizing only the two complete candidate
sequence log-probabilities. Adding the same constant to both ON candidate
log-probabilities leaves this quantity exactly unchanged, even if both native
action strings become vastly more likely in absolute model probability. Copy
generation does not detect this common-mode shift, and legal-ACT generation
detects it only after one of the two exact strings wins greedy decoding.

I exercised the exact reducer from `d160e0b2` with otherwise passing fixture
records. Changing one locality family's OFF candidate totals from
`[-2,-2]` to `[-100,-101]` and its fitted totals to `[-1,-2]` preserves the
binary odds but raises each exact sequence probability by a factor of `exp(99)`.
The report still returned `MULTIKEY_BINDING_PASS`; recorded mean binary TV was
`1.11e-16` and `spill_ok=True`.

This is not consistent with the motivating question, "without a global action
habit" (`2026-09-12_selective_writer_next_experiment_audit.md` lines 48-50),
or with an unqualified claim that locality is preserved. Before launch, either:

- add a prospectively thresholded common-mode endpoint, such as absolute change
  in the log-sum probability of the two exact action sequences and/or separate
  raw complete-sequence log-probability drift for both actions, on every
  locality family; or
- narrow the positive claim and label to conditional preference plus registered
  greedy-output stability, explicitly stating that global sub-greedy action
  propensity is unmeasured.

The first option is preferable for a diagnostic intended to rule out the
already-observed broad action habit.

### 2. The “absolute” legal-ACT-rate gate still has an item-cancellation loophole

Writer lines 401-404 compute one signed validity transition per item but then
gate `abs(mean(transitions))`. Four `OFF valid -> ON invalid` items and four
`OFF invalid -> ON valid` items therefore cancel to zero. This preserves the
marginal legal-ACT rate while every item's interface behavior changes.

I exercised exactly that adversarial case on all eight root-0 `missing` items
for both root-0 adapters, leaving all primary, score, and copy records passing.
Both cells reported `legal_ACT_rate_change=0`, `spill_ok=True`, and the terminal
label was still `MULTIKEY_BINDING_PASS`, despite 8/8 item-level validity flips.
The regression at test lines 184-194 covers only a one-directional `-1` change,
so it cannot catch cancellation.

Replace or supplement the net marginal difference with the mean absolute
itemwise transition (and preferably report the two directional transition
rates separately). Apply the predeclared `.05` ceiling to the non-cancelling
quantity, or explicitly predeclare a new threshold before any fit. Add a mixed
four-up/four-down regression that must fail `spill_ok`.

### 3. A negative Q0 cannot distinguish storage failure from extraction failure

The source records streaming training loss and then evaluates only held forms.
`optimization_ok` is itself based on held-form conditional-log-q gains (writer
lines 377-417 and 425-434). No exact-train row is scored after fitting, no
train-form OFF/ON endpoint exists, and no same-pipeline trained positive control
demonstrates that the fit stored its supervised rows. The prospective
specification deliberately excludes an extra train-form diagnostic
(`ASTRA_SEMANTIC_WRITER_COMPARISON_2026-09-12.md` lines 34-38).

Consequently `OPTIMIZATION_INCONCLUSIVE` conflates at least (a) no storage,
(b) stored but not extractable under held paraphrases, and (c) training-path
failure. The controlling selective-writer audit recommends canonical train-form
scoring (lines 102-109) and selects X0 specifically when exact-train storage is
present but fresh-held extraction fails (lines 116-133). The end-to-end
synthesis likewise asks later decisions to keep exact-train and fresh-held
scoring separate (`2026-09-12_end_to_end_goal_closure_synthesis.md` lines
363-372).

Add predeclared exact-train OFF/ON candidate scoring to the same four fits, at
least at the final checkpoint. If the step-128/256 comparison remains part of
the successor/simplicity plan, save and score both checkpoints prospectively.
The storage diagnostic must never rescue a failed held-form W0 pass. Refreeze
the physical-request/candidate-forward counts and measured time budget after
adding it. This also supplies the missing optimization positive control needed
to interpret a null.

### 4. The known native-build preflight and complete controller lifetime are not bound

The synthesis records that the prior W0's first attempt failed before training
because Triton's native build could not find `Python.h`, and that the repaired
attempt bound compiler/header/Triton evidence
(`2026-09-12_end_to_end_goal_closure_synthesis.md` lines 130-145). In the new
module, `prepare()` loads/pins the tokenizer and panel but never calls or stores
the inherited `native_build_preflight()` receipt; `builder_preflight_reference`
is only an arbitrary non-placeholder string (writer lines 78-96 and 268-291).
The carrier proof covers inference, not the fresh training path. The module also
does not execute and bind its CPU suite during preparation.

Bind the actual native-build receipt and exact CPU-test command/stdout/stderr
hashes into the prepared manifest, or bind an equivalent immutable external
preflight capsule. This is especially important because the exact failure has
already occurred once.

Each of the fourteen stage workers has a GNU-timeout/process-group envelope
(writer lines 437-471 and 591-611), but `execute` itself has no independently
supervised outer timeout. Validation, source/snapshot hashing, stage orchestration,
final sealing, and replay run in that controller. `RESOURCE.json` is written
before final replay and records `seconds`/`wall_finish` only through line 735;
the final deadline check occurs after replay at lines 738-740 and is not written
to a terminal receipt. A controller hang outside a stage can therefore exceed
the advertised three-hour lifetime, and a successful artifact under-records
the complete execute-through-replay wall time.

Before launch, bind an outer controller supervisor/command with the same
three-hour and lease deadline, and preserve a final completion/cleanup receipt
whose wall finish occurs after successful replay. If Main intentionally owns
that layer, its exact launcher and receipt must be part of the frozen prepared
evidence rather than an unbound operational assumption.

## Nonblocking limitations that must remain in the claim

- A pass is four supervised instances on 16 already-seen tool-mode keys under
  reused DEV grammar. It is not unseen-key generalization, independent-seed
  reliability, semantic understanding of compiler transformations, or a
  population result.
- The two roots change grammar bank, opaque IDs, orientation, and optimizer seed
  together. Root differences are not identifiable, and four cells are not four
  independent learners.
- Freshness is established relative to the inherited W0 and carrier namespaces,
  not as global pretraining novelty or clean-lineage provenance. Official model
  authentication remains explicitly unresolved (writer lines 45-50).
- Even after the two reducer repairs, mean-family TV without a maximum/itemwise
  tail rule permits a severe isolated spill item to be averaged away. At
  minimum, report maxima (already computed at writer line 403) and avoid claims
  of per-item locality unless a per-item ceiling is added prospectively.
- The action surface says the model can emit two valid registered compiler
  actions. The assay never observes a compiler outcome, so a pass is action-label
  carriage, not useful action selection or learned compiler semantics.

## CPU evidence from this audit

I exported the exact `d160e0b2` `organism_v6/` and `tests/` trees to a temporary
directory and made no source edits. The host is macOS, while the suite is
intentionally Linux-specific (`/usr/bin/timeout` and `/proc`). An unmodified
invocation therefore cannot be represented as a native pass here. With only
those two OS interfaces substituted at runtime (`/usr/bin/true` for the
nonexecuted timeout path and a deterministic fixture process identity), all 17
`test_semantic_writer_diagnostic` tests passed in 14.4 seconds with
`CUDA_VISIBLE_DEVICES` empty. The two adversarial reducer constructions above
then both reproduced false `MULTIKEY_BINDING_PASS` labels. No GPU API or model
was accessed.

## Minimum release checklist

1. Make locality sensitive to common-mode two-action probability growth, or
   narrow the positive label/claim so it does not purport to rule it out.
2. Replace the cancellable net legality statistic with a non-cancelling
   item-level endpoint; add the mixed-direction regression.
3. Add exact-train storage scoring (diagnostic only), refreeze request counts,
   and preserve the held-form gate as decisive.
4. Bind native-build and exact CPU-suite receipts in preparation.
5. Bind an outer controller lifetime and a post-replay terminal resource/cleanup
   receipt.
6. Rerun the full Linux CPU suite on the exact repaired bytes and perform a new
   prelaunch review. Do not cite this memo as approval of changed source.

Until those items are complete, do not spend the four semantic Q0 fits. The
terminal carrier remains a valid eligibility result; it is not invalidated by
this writer-side rework verdict.
