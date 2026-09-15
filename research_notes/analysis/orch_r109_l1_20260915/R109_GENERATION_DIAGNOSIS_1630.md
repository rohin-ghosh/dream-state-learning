# R109 generation/feed diagnosis — 2026-09-15

Status: CPU-only diagnosis and PROPOSED NEXT ARM; no allocation, dispatch,
live source change, new admission, FINAL access, or successful-learning claim.
The existing paired run, source history and failed shared sessions are untouched.

## What was actually inspected

- Eight native LOADED receipts and 96 completed TRAIN calls per lane, captured
  at 16:28:15–16:28:16 UTC: 768 calls total. This is a bounded recent window,
  not a random population estimate and not 768 independent tasks.
- Every sampled row matched its node's original/supplement archives, prompt
  policy, TASKS hash, exact seed, TRAIN label and zero parent calls.
- Six frozen source files on node2 were individually hash-compared with the
  inspected repository files; all matched. No model/tar transport or current
  GPU weight rehash. Loaded model identity is supported by native receipts
  and the verified load implementation, not a fresh tensor inspection.
- Full text of six native node2 family/stage exemplars and four node1 code/math
  exemplars was inspected from the first bounded audit, at 16:26:25. Those raw
  examples remain in each node's audit/NATIVE_TRAIN_SAMPLES.json. The later
  audit_v2 window is the sole quantitative denominator; do not add the overlapping
  windows. Two additional node2 TRAIN route episode receipts were reduced.
- All raw captures, prompts, samples and checkpoint data remain on-node.
  R109_GENERATION_DIAGNOSIS_1630.json contains hashes, counts and references only.

## Root diagnosis, ordered by causal relevance

### 1. The sampler is not the continually trained child

All eight LOADED receipts pin the intended FULL8932 state
121655d491bc55ba6bbd8eb732bc4f7a65215a07d3b6b2492f4fa623026f80f1,
on the expected frozen Qwen2.5-7B-Instruct base
a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992.
This is NOT an accidental wrong checkpoint or a BASE generator. V3 explicitly
sets generation_seed_unchanged, loads input/checkpoint once, and has no adoption
of the advancing C2 checkpoint. Generation is greedy (do_sample=False), with
finite repeated TRAIN pools (1024 math, 64 code, 256 route). Continuing to train
C2 therefore cannot alter these generators' behavior. This is an open-loop
experience supply, not evidence of evolving self-generated experience.

Source: gpu/orch_r109_l1_generation_v3.py generate/prepare;
gpu/orch_rich_hot_node2_exhaustion_v3.py Engine.generate.

### 2. Zero reported persistence is partly a measurement mismatch

The descriptive V3 metric requires >=64 child tokens AFTER the first answer
marker, >=0.8 four-gram novelty, and a final answer before the cap. It is per
response, not a before/after episode comparison, and always sets
functional_admission=False. It is not the C2 admission predicate.

- 649/768 calls are route microcalls (256 scheduled exposure, 393 goal actions).
  Exposure explicitly asks for only the offered ROUTE command. READ actions do
  not match the ROUTE answer marker. Most of this denominator is not an
  opportunity for post-answer thought or autonomous exploration.
- All 61 math responses contain work before a last-line FINAL. There is no
  post-FINAL text; 60 align to the marker and one has an alignment miss. The
  metric cannot count their pre-answer reasoning as post-answer persistence.
- 52/58 code responses have no fenced marker; all 52 are nevertheless in a
  window where JSON expression outputs are common (52 total JSON last lines).
  The actual task requests expression JSON, while first_answer_end expects a
  fenced block. This is an observation-format mismatch, not permission to
  relabel JSON/length as functional thought.
- 768/768 terminate, no cap hits, no truncation. None exceed C2's 2048-token
  encoded prefix+target limit. The present sample does not implicate exhaustion
  or the encoding-length gate as the bottleneck.

Therefore zero on this metric does NOT prove absence of reasoning, perception,
or useful multistep behavior. Preserve it as the frozen descriptive result.
Source: organism_v6/orch_r109_l1_generation_policy.py first_answer_end/measure.

### 3. There is also a real experience-design deficit, not only bad counting

In 50 complete paired draft/opportunity samples, all 26 math pairs are already
correct -> correct. Code has 21 false -> false, one false -> unparsed, and two
unparsed -> unparsed; no observed corrected pair. Nine pairs repeat identical
text. The second prompt explicitly says no feedback/new observation was supplied.
Code verification is recorded but its error is NOT delivered to the child.

Of 58 code outputs, 46 record unknown-identifier errors, five helper-arity errors,
one syntax error and six no recorded verifier error. A fully inspected pair
(node2 gpu4 CALL_014876/014877) uses xs despite the task permitting the variable
values. The child then affirms the same invalid expression. Actual stored
verifier error: unknown identifier. Helper signatures themselves use xs as
formal-argument notation; schema copying is a plausible mechanism, not a proven
causal attribution to previous LoRA training. No contemporary BASE comparison
was run, so base suppression/protocol-training causation is unproven.

Useful native actions do exist: two sampled route EPISODE receipts contain
three correct episodes out of four. One inspected transcript uses supplied
memory receipts to take the next real port. This is not a persistence or
metacognitive-allocation success rate; the episode selection is tiny and
descriptive. It does show why response-marker zeros cannot stand in for the
functional trajectory audit requested by R107/R108.

### 4. Admission starvation is a separate, structural plumbing limit

C2 does not consume all V3 output. Its frozen reviewer accepts only math rows
with manually authored PASS grounding and one of TASK_CONSTRAINT_USED or
ARITHMETIC_ERROR_CORRECTED. The native gate checks sources, correctness, held
exclusion, exact student tokens and prefix masking. Code/route are excluded
before admission; there is no general persistence/hops admission implementation.
feed.prepare also builds its lookup solely from the math task pool. Its corrected
arithmetic branch is not currently wired with a draft argument by feed.prepare.

The append tool publishes a finite reviewed batch, not an ongoing review worker.
With no reviewed batch after B002, the same 19 eligible rows keep cycling:
original four plus 15 new. Native decisions show 15 admissions and three explicit
ambiguous-grounding rejects across the reviewed C2 batches. Zero new admissions
is not a measured 97k-row rejection rate; almost all calls have never been reviewed.

Task/target dedup is real and should remain. It is NOT the demonstrated immediate
cause: the node2 audit window contains five distinct math source tasks, none
already among the 19 eligible IDs. There are remaining candidates, but ordinary
correct math candidates would not answer the functional-persistence question.

Sources: gpu/orch_r109_l1_experience.py review_gate;
gpu/orch_r109_l1_feed.py prepare/source_gate;
gpu/orch_r109_l1_feed_append.py validate_extension/publish.

## One concrete next arm: feedback-grounded repair -> sleep -> transfer

Proposed name: R109_NEXT_FUNCTIONAL_REPAIR_V1. Separate experiment; NOT a C2
hotpatch or relabeling of current data. Main must explicitly allocate before any
GPU work. Preserve original deadlines; no lease extension or renewed eight-hour
counter. If no bounded allocation remains, retain as unlaunched next campaign.

### Hypothesis and unit

Actual TRAIN execution feedback can teach the child to use a consequential
observation to repair its own action and retain that operation after sleep.
Primary unit is a complete failed-attempt -> received evidence -> child repair
episode, followed by parent-free transfer, NOT response length, branch counts,
marker frequency, or raw calls. This targets R107/R108 functional perception,
metacognitive allocation and persistence without forced exhaustion/templates.

### Minimum prospective pilot

1. Freeze 16 distinct TRAIN bounded-code problems before any outcomes, balanced
   over identifier/arity/operation-order constraints; hold out a separate transfer
   set by task family/normalized specification. Use no FINAL or fixed32 inputs
   for teachers, task construction, selection, or targets. Do not cherry-pick
   the completed run's successful or failed outcomes into a new benchmark.
2. At an explicitly authorized safe new-arm boundary, snapshot the actual latest
   C2 FULL adapter + AdamW steps/momenta + RNG, preserving their exact hashes and
   history. Use this SAME checkpoint for learner collection and fit, frozen
   within each cohort. Never silently substitute8932 or reset the optimizer.
   Existing C2 remains untouched. The next cohort adopts only a committed new
   arm checkpoint with a source-labelled adoption receipt.
3. One source task receives one child draft and at most one optional continuation.
   Treatment receives the actual public TRAIN interpreter result/error for its
   submitted expression; control receives the existing no-new-feedback opportunity.
   No provider/teacher, gold expression, AST rewrite, semantic compiler, fake
   test, forced length or forced correction. A correct first answer may stop.
   Keep the present8192 output cap/context rules, and an exact prelaunch total
   call/time bound. Never trim a target to fit2048: log context rejection.
4. Include a frozen-BASE, adapter-OFF reference on the same preselected TRAIN
   task/prompts before attributing failures to the learned seed. It is a source
   diagnostic, never silently pooled into child-generated targets. In line with
   R107, retain all42 independently verified BASE anchors in the learner recipe.
5. Admit only exact child continuations whose real feedback changes a consequential
   action/representation and whose correction is independently verified on TRAIN
   examples. Require a full native draft/evidence/continuation hash chain and
   a short semantic review of what changed and why it mattered. Output success
   alone is insufficient. Label R109_SELF_PUBLIC_FEEDBACK_REPAIR separately;
   preserve source-family IDs, rejected rows/reasons and exact prefix-masked
   child tokens. No parented/L2 mixing and no conversion of unparsed -> unparsed
   into a success. Permit no synthetic repair of the target.
6. Publish at most eight independently eligible repairs in one immutable batch.
   Empty batch is an honest null: no fit launch just to consume the allocation.
   A queued review/publish worker must account for every pilot episode, including
   ineligible ones, before declaring feed readiness; the status observer alone
   is not that worker. Subsequent cohort publication occurs only at checkpoint
   and fixed-readout boundaries.
7. For the small write test, clone the same saved optimizer state into a separately
   labelled treatment/control pair; each arm advances its own continuous optimizer,
   not a shared cross-control object. Keep the C2 native recipe unchanged except
   for this new labelled eligible bucket: one eligible selection every8 updates,
   existing prior/legacy rehearsal and an anchor every update, token-normalized
   loss. CONTROL masks eligible labels. This is NOT shared16-new/1-old or a fixed
   .25 anchor lambda. Bound to128 updates per arm for the pilot, with exact dose
   and target-loss receipts. Do not combine its history with current C2.
8. Each checkpoint requires the exact fixed32 ON/OFF suite plus held behavior
   in fresh processes, separate from selection and invisible to parents. Assess
   frozen pre/post transfer using the preregistered functional repair/constraint
   use rubric and actual verifier receipts. Compare matched updates and report
   cell counts; distinguish immediate feedback benefit from retained learning.
   Repeated tasks, correct first answers and ordinary syntax compliance are not
   automatically persistence successes. No H1/H2 gain claim from this pilot;
   broader claims still need matched controls/seeds and unseen-environment slopes.

### Earliest decision and budget request

Do not reserve GPUs from the current lanes. Request only a bounded collection
pilot first: at most96 native responses (16tasks x 2opportunities x treatment,
no-feedback control and BASE reference), fewer when a first response finishes.
No fit allocation is implied. Record actual raw/eligible yield and stop collecting
when the fixed bound expires. Request the separate128-update paired write test
only if grounded repairs exist and Main grants capacity. If feedback merely fixes
the xs/values convention but fails held-out transfer, report that narrow result;
do not promote it into metacognition, retained thinking, or continuous improvement.

## Validation and stage status

The new diagnostic source runs stdlib-only, opens only explicit native TRAIN
paths, verifies per-row provenance, writes only a new external audit directory,
and has no model loader, subprocess, signal, optimizer or admission capability.
Three CPU assertion tests pass via direct Python execution; local pytest is
unavailable, so no pytest-suite pass is claimed. Both native node reductions
completed successfully (768 calls total). Earlier audit artifacts are retained.
Exact changed-file allowlist: STAGE_READY_L1_DIAGNOSIS_1630.json.
This receipt is not a pre-GPU approval or an implemented successor trainer.
