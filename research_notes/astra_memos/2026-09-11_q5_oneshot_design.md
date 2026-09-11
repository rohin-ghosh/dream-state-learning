# Astra memo 5 — one-shot consolidated design (write, read, loop/merge, scores, test, build order) for comparison with CHILD_MECHANISM_v7 (2026-09-11 01:05 UTC)

## 1. THE WRITE

**Build:** new `write_v7.py::{compile_windows,sample_write,audit_corpus}`, `train_adapter_v7.py::{train,grow_lora}`, and `write_manifest.py`. Leave the running v6 trainer unchanged.

**Test:** exact-context tests, a controlled “car” memory test, and a matched-token write A/B must pass before any adapter enters the lineage.

**Scope.** This is the design I would freeze for this sprint: one reasoning-gym lineage, one frozen 7B base, asynchronous Astra parenting, and compiler gym reserved for deployment. No Minesweeper, TextWorld, principle generator, or second memory mechanism. I have the supplied specification and code excerpts, but not memos 1–4; I therefore cannot verify compatibility with their exact wording. All changes below are explicit rather than presented as previously agreed.

### 1.1 Train the next thought in the situation that produced it

A state is **everything the child can currently read**, including the task, its clock, previous thoughts, observed outcomes, briefs, and carry-over. A transition is the child’s next generated turn followed by any resulting harness events.

Use one shared, appendable renderer for inference and training:

```text
Birth brief + own brief + parent brief                   CONTEXT
Current goal + labelled carry-over                      CONTEXT
[STATE] turn 1 of 16; best score ...; last outcome ...    CONTEXT
child turn 1                                            TARGET
actual outcome events                                   CONTEXT
[STATE] turn 2 of 16; best score ...; last outcome ...    CONTEXT
child turn 2                                            TARGET
...
```

These are roles in the dataset, not new markers the child must emit. Preserve the actual inference chat template and message delimiters.

**Replace:** move the changing clock, best score, and last outcome from a rewritten head into a harness state message immediately before each generation, because an appendable stream permits genuine multi-state training without giving an early thought a later state.

The fixed head still contains the briefs and current goal. At a new problem, rebuild it and include the labelled carry-over. At any context eviction, begin a new training window.

For each training window:

- Its prefix is an actual recorded inference context, token for token.
- Prefix tokens have loss mask 0, including earlier child thoughts.
- The next child turn has loss mask 1.
- Actual subsequent outcomes, nudges, and state messages have loss mask 0.
- Additional child turns have loss mask 1 **only while the accumulated prefix remains identical to what inference actually showed them**.
- Close the window before a head change, context eviction, adapter change, or problem boundary.
- Reflections use their actual reflection prompt and previous reflection as context; their generated turns are targets.

Do not synthesize missing states. Old ledgers lacking sufficient rendering information can support the old-write comparator, but are not silently promoted to exact-state data.

This preserves your important rule: **only the child’s generated thoughts and reflections are targets**. The `ACT:` line is part of its thought, not a separately rewritten action exemplar.

### 1.2 Two views, not two compulsory copies of every problem

Keep your two-scale intent, but replace action-centred windows with:

1. **Multi-state windows:** greedily cover successive child turns, in order, starting from an actual state. Close at the boundaries above or the length limit. Across this view, each eligible row has one target owner.
2. **State-to-state windows:** the actual context immediately before one child turn, followed by that turn. Include silent thinking turns, failed attempts, and reflections—not only action turns.

Allocate **70% of training token-passes to multi-state windows and 30% to state-to-state windows**. These are initial engineering settings, not measured optima.

Do not create a short window ending in an outcome and assume that this teaches adaptation to that outcome: the important target is the **next thought after seeing it**.

### 1.3 Length, boundaries, and packing

- Maximum training sequence: **8,192 tokenizer tokens**, including context and targets.
- Maximum generation: keep **400 new tokens per turn**.
- Runtime context cap: **7,792 tokens**, leaving room for one full turn. Retain your 14-turn tail limit; replace the 22,000-character cap with the token cap.
- Evict oldest complete tail turns first. Never silently truncate the current goal, newest outcome, or target turn.
- A long window can cover an entire problem if it fits; otherwise it closes before eviction or overflow and the next window starts from the next actual state.
- If a mandatory head alone cannot fit, stop with a render error rather than train a different situation.

**Ship without cross-example packing.** Use one sequence per microbatch, grouped by length for throughput. There is no attention between unrelated sequences. Add packed variable-length attention only if an existing implementation passes a test showing that changing example A cannot change example B’s logits or gradients.

**Replace:** family-neighbourhood packing is not a learning mechanism here, because unrelated examples must not attend to one another. Preserve family/time metadata for sampling and analysis.

### 1.4 Repetition and the token-pass budget

Keep every eligible occurrence in the immutable ledger. Two identical thoughts produced on different turns remain two occurrences.

Track separately:

- `occurrence_id`: clone, ledger index, problem, turn;
- `context_exposures`;
- `target_exposures`;
- target tokens presented at each write;
- cumulative target tokens presented across writes.

A thought appearing as carry-over is a context exposure, not another target occurrence.

Budget **all processed non-padding tokens**, not just supervised tokens:

\[
B=\min(5{,}000{,}000,\;v_{\text{measured}}\times3{,}600)
\]

where \(v_{\text{measured}}\) is sustained training throughput in tokens per second. Thus training gets at most **60 minutes per write**. Reserve the remaining approximately 60 minutes of a clone round for compilation, exams, confirmation, and reload.

Sampling:

- Divide the budget 70:30 between long and short views.
- Within each view, reserve half for rows not yet considered by a write and half for replay.
- If fresh data fits its reservation, include it all and give unused capacity to replay.
- Otherwise sample fresh problem instances uniformly without replacement.
- Sample older problem instances uniformly without replacement within the write; choose their windows using the recorded RNG seed.
- If a stratum is exhausted, transfer its remaining budget to the other stratum.
- Admit only complete windows. Record unused budget and every omitted fresh occurrence.
- One sampled pass; no hidden epoch multiplier.

This replaces your “about 10,000 tokens per problem” accounting: exact contexts can be expensive, and only tokenizer counts make the budget real.

### 1.5 Trainer configuration

| Setting | Shipped value |
|---|---|
| Base | Same pinned 7B checkpoint and tokenizer in every cell; frozen |
| LoRA rank / alpha | Start **8 / 16** |
| Targets | Keep `q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj` |
| Dropout | **0.0**, simplifying deterministic growth and comparison |
| Optimizer | AdamW; betas 0.9/0.999; epsilon \(10^{-8}\); weight decay 0 |
| Learning rate | **\(5\times10^{-5}\)** cumulative; **\(2\times10^{-5}\)** incremental |
| Schedule | 5% linear warm-up, then constant |
| Epochs | **1 sampled pass** |
| Precision | bf16; frozen base remains unquantized |
| Memory | Gradient checkpointing; `use_cache=False`; microbatch 1 |
| Accumulation | 4 sequences per optimizer update |
| Gradient clip | Global norm 1.0 |
| Seeds | Pretests **1101, 1102**; production `11000 + write_id` |
| Loss | Summed next-token CE on target tokens, divided by total target tokens in the accumulation group |

Do not average four sequence-mean losses equally: a 40-token target and a 1,000-token target should not have equal weight. Mask padding, all context, and harness text. Train a message terminator only when it actually terminated the model’s generated message; do not invent an end-of-thought token for a turn cut off at 400 tokens.

The supplied trainer truncates at **512 tokens**, trains every non-padding token, has no explicit seed, and updates on batches of four without checkpointing. Those are direct code reasons to replace it, rather than patch its corpus alone.

### 1.6 Rank growth: exact expansion first, not distillation

Write each adapted matrix as

\[
W'=W+sBA,\qquad s=\alpha/r.
\]

Grow **8 → 16 before write 4**, and **16 → 32 before write 8**, provided the measured writer cycle remains within one round. Otherwise keep the current rank and record `GROWTH_DEFERRED`. Gate outcomes do not determine growth.

For expansion from \(r\) to \(r'\):

```text
A'[:r, :] = A
B'[:, :r] = B
A'[r:, :] = seeded small random values
B'[:, r:] = 0
alpha' = 2*r'
```

Because \(s=s'=2\), the effective matrix is unchanged. The new zero columns of \(B\) receive gradients immediately.

**Do not zero-pad both new factors and call that trainable growth:** their product is zero and both new factors initially have zero gradients. Both-zero padding preserves the function but leaves the new capacity inactive under ordinary gradient descent.

If the scale changes, multiply the retained \(B\) by \(s/s'\).

An SVD-based alternative factors the existing update:

\[
\Delta W=U\Sigma V^\top,\quad
B'=U\Sigma^{1/2}/\sqrt{s'},\quad
A'=\Sigma^{1/2}V^\top/\sqrt{s'}.
\]

Keeping all nonzero singular components preserves the matrix up to numerical precision; truncating components does not. Add random-\(A\), zero-\(B\) capacity beyond those components. Use a thin QR/SVD calculation rather than materializing every full update matrix.

**Ship direct expansion.** SVD rotation changes optimization geometry without adding information, and distillation only approximately preserves behaviour. Reset optimizer state at a write boundary under either procedure. Verify function preservation in evaluation mode; training-time dropout would complicate that claim.

### 1.7 Cumulative versus incremental

Start with **three cumulative writes from the frozen base**. Keep that clean-reset baseline.

Starting at write 4, consider an irreversible switch to incremental training if either:

- fresh windows exceed half the token budget for two consecutive writes; or
- the available replay budget covers less than **25% of the older compiled windows** for two consecutive writes.

Before switching, run one matched-budget cumulative/incremental shadow comparison on the same ledger, using the reasoning development panel. Incremental must pass the brake, preserve old-family performance within the predeclared development tolerance, and complete within budget. If it fails, remain cumulative; do not search repeatedly during the lineage.

After switching:

- initialize from the **currently active adapter**, not the latest held or rejected candidate;
- use the same 50:50 fresh/replay allocation;
- keep all ledger rows, including rows produced under a subsequently rolled-back adapter;
- record the initialization adapter hash.

If still cumulative when rank increases, initialize a fresh adapter at the larger rank. That is **not** function-preserving growth of the preceding adapter; do not label it as such.

### 1.8 What must be demonstrated before launch

The supplied material does not define the car test. My operational version is a quarantined, controlled diagnostic—not lineage experience:

- A small simulated car has hidden faults and diagnostic observations.
- Matched situations require different next thoughts/actions depending on an earlier observation.
- Delayed cases insert several irrelevant turns; multi-state cases require “observe → revise → test again.”
- Use fixed verified traces, withheld paraphrases, and counterfactual cue swaps.
- No car data enters the reasoning lineage.

**Car acceptance:** across both training seeds, the adapter improves withheld cue-conditional accuracy by at least **20 percentage points** over base, reaches at least **80%**, and remains at most **10 percentage points worse** on delayed than immediate cases. Base, adapter-on, adapter-off, and wrong-cue controls must establish that weights—not a leaked answer or brief—cause the change. These thresholds are engineering acceptance criteria.

Then run the real write A/B on fresh, fixed reasoning-gym child ledgers:

- A: current v6 selection/restatement/principle compiler;
- B: the proposed state/multi-state compiler;
- same base, rank, optimizer, seeds, and processed-token budget;
- also evaluate the frozen base with the child’s own waking brief.

B must pass format/collapse checks, lower held-out conditional target loss relative to base, and improve birth-brief-only development behaviour beyond the measured paired-repeat noise band. It must not lose to A by more than that band. Compare adapter-only directly with brief-only: if the brief explains the whole gain, the weight-memory claim has not passed.

**Failing this test means no learned-lineage launch.** Continue the diagnostic; do not compensate by adding mechanisms.

---

## 2. THE READ

**Build:** `state.py::{render_event_context,truncate_tail}`, `reflection.py`, `write_v7.py::audit_corpus`, and `tests/test_render_equivalence.py`.

**Test:** every target prefix reproduces an actual inference prefix; forbidden sources never become targets; wake/reload tests show the expected brief versions and carry-over.

At a training wake the child sees, in your order:

1. **Fixed, hashed birth brief.**
2. **Own latest summary**, at most 8 lines.
3. **Latest accepted parent brief**, at most 10 lines, plus the existing one-line channel.
4. **Current problem and labelled last three turns from the previous problem**, followed by the current state and growing tail.

Briefs refresh at batch boundaries; none changes mid-problem. Keep neutral introductions, one `ACT:` interface, and no required notes, predictions, or rehearsal markers.

**The prompt head belongs inside training context.** Rohin is right on this point. If a parent cue caused a child response, stripping that cue teaches the response in the wrong situation.

**Replace:** remove the “no parent word in the corpus” rule and substitute “no parent token is a target,” because complete conditioning and zero direct supervision of parent prose are compatible, whereas removing the causal cue is not.

Be precise about the consequence: masked parent context can still influence gradients on child targets. This is not an information firewall. The firewall is that parents never see deployment material or sealed scores, and cannot supply training targets directly. Parent-free deployment measures whether anything useful survives without those cues.

### Automated invariant check on every write

The compiler emits token IDs, masks, and token-level source provenance. Before training, check:

- Every target token maps to an eligible child-generated row and exact byte/token span.
- Every masked source has the correct role: brief, goal, outcome, nudge, carry-over, or prior context.
- For each target turn, its visible token prefix equals the recorded inference prefix.
- No future outcome, later state, or later reflection is visible.
- No clone or problem is accidentally joined to another.
- No target is silently truncated.
- No report/gate item enters the training corpus.
- No sealed source is reachable through parent inputs.
- Target/context exposure totals reconcile with the sample manifest.
- A replay of the renderer from recorded structured events produces the same hashes.

A vocabulary scan is a useful alarm, not proof of split hygiene. Use source IDs and provenance for the hard assertion.

Keep private reflections as training data, but **remove parent access to their raw text**. The supplied six-word/four-content-word checker cannot guarantee that a parent has not paraphrased them. Parents receive ordinary training turns and outcomes instead.

---

## 3. THE LOOP AND MERGE

**Build:** `writer_daemon.py`, `clone_coordinator.py`, `model_backend.py::load_version`, `gate_v7.py::transition`, `parent_daemon.py`, and transactional publication/recovery tests.

**Test:** a two-clone soak survives a killed writer, duplicate slices, delayed parenting, and rollback without a blocked clone, duplicate pooled row, partial adapter load, or mid-problem weight change.

Keep your basic loop:

- 8 lanes per inference GPU;
- 16 turns maximum per problem;
- solved lanes idle until the batch boundary;
- nudge after 4 consecutive action-free turns;
- reflection after 32 problems;
- no child-issued stop token;
- raw-ledger pooling, **not adapter averaging**.

### Writer and publication

One writer pools all complete unseen slices available when it starts. It never waits for every clone. It compiles, trains, evaluates, and publishes while clones continue.

Publication is transactional:

1. Train into a temporary directory.
2. Save adapter, rank, base/tokenizer hashes, sample manifest, and gate record.
3. Validate loading and checksums.
4. Rename to an immutable version directory.
5. Atomically replace `ACTIVE.json` with version, path, monotonic load ID, and reason.

LoRA is enabled from engine birth, including for a base-only child. Use rank capacity 32 and unique IDs. Keep the current adapter until the new one has loaded successfully.

A clone finishes its entire batch—and any reflection already underway—under the old weights. It then refreshes adapter and briefs. Every generation records both versions.

Target lag is **one round**, not a guarantee. Record wall-clock lag and per-clone completed-round lag. If cycle time exceeds round time twice, reduce the next token budget; do not skip exams or make clones wait.

### Gate state machine

“Committed” is a durable record, not permission to govern the child.

| State | Meaning |
|---|---|
| `REJECTED` | Failed integrity, format, or confirmed collapse; never active or floor-eligible |
| `COMMITTED` | Immutable, loadable candidate that passed hard checks |
| `HELD` | Committed but awaiting confirmation, or withheld after a severe confirmed dip |
| `ELIGIBLE_AS_FLOOR` | Committed and independently confirmed; may anchor rollback |
| `ACTIVE` | Published for clones to adopt at boundaries |
| `ROLLBACK` | An event repointing `ACTIVE` to the best eligible committed version |

Initial gate: your **12 reasoning development items × 2 repetitions**, seeds 4242 and 5242, birth brief only.

Hold and confirm as follows:

- A candidate more than one tolerance below the floor is **held**, then rerun with independent confirmation seeds.
- If the four-repetition mean is no longer below the floor minus tolerance, activate and reset the dip counter.
- If it remains below, count **one confirmed below-floor candidate**, not two examinations.
- The first two ordinary confirmed dips may activate.
- A confirmed dip of at least **5 tolerances** stays held; the previous active adapter continues.
- On the third consecutive confirmed below-floor candidate, roll back and enter recovery mode.
- In recovery mode, later candidates remain held until one confirms within tolerance of the floor.

A candidate that appears to improve the floor also receives confirmation. Its fixed four-repetition mean becomes its recorded floor score. The floor is the largest such confirmed score among eligible committed adapters and never changes because of a later re-probe. First eligible adapter establishes the floor; the frozen base does not set a minimum floor.

**Replace:** do not let one noisy committed score set a permanent floor, and do not activate a severe dip before confirming it, because neither protects development from evaluation noise.

### Collapse brake: use the common-unsolved set

For candidate \(a\), base \(b\), and matched item/seed runs, define:

\[
U=\{i:\text{both }a\text{ and }b\text{ fail to solve }i\}.
\]

Compare their median generated tokens **on this same set**:

\[
C=\frac{\operatorname{median}_{i\in U}T_{a,i}}
        {\operatorname{median}_{i\in U}T_{b,i}}.
\]

Hold for confirmation if \(C<0.5\). Reject for collapse only if confirmation also has \(C<0.5\).

Require at least **6 paired runs** in \(U\). Otherwise use a preregistered reserve set of harder reasoning development items. If there are still too few, record the brake as inconclusive; do not compare different unsolved populations or reject an adapter for solving more problems.

Keep your format canary: at least **3 of 4 training-split problems** must yield a scoreable action within 6 turns. Actions and distinct actions remain instruments, not independent collapse vetoes.

Keep compiler tolerance **0.01** provisionally for deployment. For reasoning, freeze tolerance from repeated **paired panel differences**, with a minimum of one two-repetition score quantum, \(1/24\), rather than treating a four-repetition accuracy band as a precise noise estimate.

---

## 4. THE SCORES

**Build:** `score_access.py`, allow-listed views in `agentic_parent.py`, separate development/report storage, and parent-input manifests.

**Test:** capability tests attempt to retrieve every score class from child, parent, writer, and researcher identities; prohibited reads must fail at the storage/API boundary, not merely disappear from a prompt.

| Information | Child | Parents | Harness/researchers | Plain reason |
|---|---|---|---|---|
| **Training outcomes** | Own action outcomes and own scores | Yes: training scores, problem text, actions, ordinary thoughts, and aggregate trends | Yes | Parents need the same observable evidence of success and failure that makes teaching possible. |
| **Gate decisions** | No numerical exam results; knows only that inherited weights may change | Decision and reason code only | Full record | Parents need to know whether a write was held or rolled back without learning the exam. |
| **Development panel** | Only the task during an isolated evaluation, with its normal task feedback | No items, transcripts, or numerical scores | Available for preregistered tuning and gating | This keeps parenting aimed at classroom evidence rather than the examiner’s questions. |
| **Sealed report panel** | Tasks and normal feedback only inside report evaluations; no report memory carried out | Nothing | Evaluator writes sealed results; researchers open them after all adaptive choices finish | A final test cannot remain final if its results steer the lineage. |

**Answer to Rohin:** yes, parents should see the child’s training scores. Your current prohibition is appropriate for report scores, not for the ordinary evidence from which a parent teaches.

Report evaluation contexts are destroyed afterward. Their ledgers never enter training, summaries, carry-over, or parent tools. Do not publish intermediate sealed numbers to `COORDINATION.md`.

---

## 5. THE TEST

**Build:** `freeze_lineage.py`, `deploy_pair.py`, `sealed_eval.py`, and `analyse_primary.py`.

**Test:** a dry run proves snapshot immutability, empty deployment ledgers, matched twin schedules, no evaluation-row ingestion, and complete 512-problem score accounting.

### Two co-primary outcomes

**A. Frozen transfer.** Before either child learns from compiler experience:

- Taught: frozen lineage adapter, birth brief only.
- Untaught twin: same base, no adapter, same birth brief.
- Same compiler report programs, generation seeds, 16-turn budget, and scoring implementation.
- Four repetitions per condition.
- No writing, parents, summaries, or cross-program carry-over.
- Primary statistic: paired mean difference in final best compiler score per program, averaged across repetitions.

The 8 supplied report programs give a narrow fixed-panel conclusion. The disjoint panel used for gating is **development**, not additional sealed evidence.

**B. The 512-problem continual curve.**

Run **two paired deployment replicates**. Each pair has the same compiler problem order, generation-seed schedule, turn budget, write budget, update cadence, and parent policy: **no parents for either deployment life**.

Primary statistic:

\[
\Delta_{\mathrm{continual}}
=\frac{1}{512}\sum_{i=1}^{512}
\left(s_{\mathrm{taught},i}-s_{\mathrm{untaught},i}\right).
\]

Here \(s_i\) is the gym’s existing final best-score scalar for problem \(i\). Report eight 64-problem bins and the last-128-problem difference as secondary readings. A no-action problem remains zero.

### Empty ledger plus frozen snapshot

At deployment birth:

- Copy an immutable adapter directory and its full lineage provenance manifest.
- Mount the classroom ledger snapshot read-only for audit, **not for model retrieval or deployment replay**.
- Create a new writable deployment ledger with zero rows.
- Clear waking summary, parent brief, reflection history, tail, and writer cursors.
- Taught starts from the snapshot adapter.
- Untaught starts from the frozen base with a zero-update adapter of the same rank.
- Both use the same fixed incremental writer from their respective initial weights.

**Replace:** remove the extra **2.5 million lineage tokens per taught write**, because that creates a compute and lag asymmetry and makes inherited knowledge depend on repeatedly re-reading childhood data.

Both deployment lives replay only their own compiler experience. This deliberately tests whether the inherited adapter is a useful starting point and can survive continued learning.

Use matched logical publication timing in deployment: train after each 32-problem slice and make its candidate available at the next 32-problem boundary. If necessary, pause the faster twin at that boundary; never let hardware speed determine how many problems each condition experiences under an update. Report the resulting wall-clock cost.

Compiler gates may operate during continual deployment, identically in both conditions, using only the compiler development panel. Their exam rows stay out of the write. The taught adapter establishes its initial confirmed compiler floor; the untaught child establishes one after its first eligible write.

### Noise ruler and interpretation

The supplied record reports:

- **Between-life SD: 0.027 score units.**
- **Same-adapter replicate SD: approximately 0.0065 score units.**  
  [Supplied §3.4; SEQ-011/012 as quoted.]

Under independent repetitions, a four-repetition condition mean has SD about **0.00325**; a difference of two such means has SD about **0.0046** before any benefit from pairing. Thus **0.01** is a useful practical threshold for frozen-panel repeatability, not a universal significance threshold.

By contrast, **0.02 is less than one between-life SD**. Two deployment pairs cannot establish a general population effect. Report both pair differences, their mean, and the full curves; do not treat 512 successive problems as 512 independent lives.

For the frozen panel, report paired per-program differences and a program-level bootstrap interval, clearly labelled as conditional on this small panel. For continual learning, use block-bootstrap intervals only as within-run descriptive uncertainty, not as substitutes for independent lineages.

I would call the sprint’s downstream result positive only if:

- frozen transfer gains at least **0.01 score units** and its paired interval excludes zero; and
- continual AUC difference is positive in **both** deployment pairs, without an unresolved collapse.

Anything weaker is mixed or inconclusive, not a reason to retune against the sealed panel.

Do not reuse §3.4’s “false rollback essentially never happens” claim. It assumes an effectively fixed floor and independent Gaussian noise; the supplied record itself contains heavy tails, and selecting a maximum raises the floor by an amount that grows with the number of candidates.

---

## 6. THE MINIMAL BUILD LIST

**Build:** `SPRINT_MANIFEST.json`, a single launch command, and CI jobs for the acceptance tests below.

**Test:** launch refuses missing hashes, failed pretests, mismatched mechanisms, or an unmeasured throughput budget.

These are estimates in **engineer-hours**, excluding GPU runtime.

| Order | Work | Hours |
|---|---|---:|
| 1 | Pin base/tokenizer, splits, permissions, seeds, and manifest; preserve v6 | 2 |
| 2 | Parser, stopping, nudge, carry-over, token cap, shared appendable renderer | 6 |
| 3 | Exact-state compiler, masks, provenance, budget sampler, invariant suite | 8 |
| 4 | Seeded trainer, checkpointing, correct loss accumulation, rank expansion | 5 |
| 5 | Controlled car test and fixed-ledger write A/B scripts | 4 |
| 6 | Gate state machine, common-unsolved brake, confirmation, transactional publication | 6 |
| 7 | Background parent daemon and score-access enforcement | 3 |
| 8 | Nonblocking pooling, reload, crash recovery, two-clone soak | 5 |
| 9 | Snapshot/deployment twins, sealed evaluator, primary analysis | 5 |
| **Total** | | **44 engineer-hours** |

With three engineers this is approximately two working days, not one person’s overnight patch. Tomorrow’s build should have one owner for runtime, one for write/trainer, and one for gate/evaluation.

**Cut line:** ship after these acceptance-critical pieces work. Cut hot-swap optimization if necessary and use the measured engine-restart fallback. Cut packed attention, SVD refactoring, additional gyms, extra instruments, intermediate report probes, and repeated hyperparameter search. Do **not** cut exact conditioning, masks, access controls, hold/confirm, or the twin.

If the switch shadow test cannot be built or run, stay cumulative during classroom training and label it so. Deployment’s fixed incremental protocol must still be tested before deployment launches.

### GPU order: tonight, 09-11

I will label the eight surviving GPUs **S0–S7**. This assumes they can run node-local jobs with adequate storage; physical inventory must confirm that. Node 1’s temporary GPUs are **E0…**, used only for disposable tests.

1. **CPU first:** parser, render equivalence, mask/provenance, split and permission tests.
2. **S0:** longest-sequence memory/throughput smoke, then rank-growth equivalence test.
3. **S1:** base car controls and short reasoning ledger collection.
4. **S2:** inference reload/fallback and crash-recovery smoke.
5. **S3:** frozen reasoning development repetitions to establish paired noise and common-unsolved coverage.
6. **E0/E1, if available:** second car seed and old-write comparator. Otherwise queue them on S0/S1.
7. Remaining GPUs collect only the fixed reasoning pilot ledger or remain available for the A/B; no final-panel compiler runs tonight.

For rank growth, compare adapter-update matrices in float32 to relative error below **\(10^{-6}\)** and end-to-end logit differences against a same-adapter reload numerical baseline. Test that new factors actually receive nonzero gradients.

### Tomorrow, 09-12

- **S0/S1:** proposed-write A/B, two seeds.
- **S2/S3:** development inference for those candidates, adapter-off and brief-only controls.
- **S4/S5:** two-clone asynchronous soak with deliberate process kills.
- **S6:** gate fixtures: ordinary dip, severe dip, noisy apparent improvement, third-dip rollback, and recovery.
- **S7:** deployment-pair dry run on a **synthetic compiler-interface fixture**, not report programs.
- Temporary GPUs run only duplicate pretests and debugging.

Required green before lineage launch:

1. Exact inference/training prefix equivalence.
2. Zero forbidden target tokens and zero split contamination.
3. Car acceptance and real-write A/B acceptance.
4. Long-sequence fit and measured token budget.
5. Train/save/load/grow equivalence and nonzero new-rank learning.
6. Common-unsolved brake and complete hold/confirm/rollback tests.
7. Parent access-control tests.
8. Two-clone recovery soak with no mid-problem swap.

### Run schedule

- **09-12, after acceptance → 09-14:** one lineage on the surviving node: **S0 writer, S1–S6 clones, S7 development/confirmation and deployment preparation**. Parents are background API jobs, not clone dependencies.
- **Node 1:** disposable acceleration only. Checkpoint useful artifacts before its lease ends; nothing essential lives only there.
- **09-14:** freeze the classroom adapter and corpus manifest. Run frozen compiler transfer before any compiler write.
- **09-14 → 09-17:** two continual pairs, each using four GPUs: taught inference/writer and untaught inference/writer. Thus all **8 surviving GPUs** are occupied.
- At the supplied estimate of **16 problems per GPU-hour**, 512 problems require about **32 inference-hours per life**, plus controlled update waits and startup. Reserve **48 hours** for the deployment run and the remaining time for failures.
- **09-17 → 09-18:** complete all adaptive runs, seal manifests, then open and analyse report results.

Do not silently shorten one twin. If the measured schedule cannot finish 512 problems, report the co-primary as incomplete.

---

## 7. COMPARISON

**Build:** `DESIGN_DIFF.md`, linking every retained or replaced requirement to its implementation and acceptance test.

**Test:** the launch manifest has no unresolved mechanism choices.

I would keep your free-thinking loop, tolerant but colon-required `ACT:` parser, 16-turn budget, three-turn carry-over, private reflection write, all-occurrence ledger, asynchronous raw-experience merge, parent-free exams, and rollback without deleting experience [supplied §§1–3]. I would replace the v6 success-filtered/restated write with exact-state teacher forcing; replace stripped heads with masked, provenance-checked context; replace compulsory two-scale duplication with token-budgeted sampling; replace immediate rank 32 with tested 8→16→32 expansion; replace noisy maximum-score floors with confirmed eligibility; and remove asymmetric classroom replay from deployment. The three biggest risks in my design are **self-imitation reinforcing poor thought rather than useful learning**, **exact contexts consuming enough tokens that the writer sees too little fresh experience**, and **a small, repeatedly used development panel steering the lineage toward its own quirks**. The car test addresses whether the write works at all; the real-write A/B addresses whether it learns anything useful; only the frozen compiler test and matched 512-problem twins address whether that usefulness survives downstream.

[astra openai/openai/gpt-6-astra effort=high 208s tokens in=15385 out=8851 reasoning=1552]
