# R141 / R121 — independent interpretation A: four-condition Level-1 design

Source-hash snapshot: 2026-09-16 at approximately 04:07 UTC; key sources
revalidated at 04:13 UTC. Status: **proposal for
independent cross-critique, not consensus, ratification, implementation approval,
or launch authorization**. Only this document is owned by this analysis.
No runtime, source, ledger, Git, fleet, parent-provider, or intake state changes;
no model/provider calls. Main owns fleet coordination and the R141 interface
repair. I did not read another new interpretation or repeat the prior audits.

## 1. Directive and controlling evidence

Rohin's Message 121 is dated **September 15, 2026, approximately 20:50 UTC**;
the scope note is dated September 16 at 01:52 UTC. These are different records,
not evidence that the underlying directive occurred on September 16.

Verbatim, contiguous excerpt of Rohin's paragraph:

> Im scoping down my paper to only look at level 1, I dont have time for level 2-3 nor deployment and downstream improvements So basically doing some richness teaching and then comparing skill acquisition against SEAL of responsive teaching on a level 1 agent versus the same skill with SEALS acquisition loop and a baseline models md file acquisition

His capability concern, also verbatim:

> it’s all lora so they don’t get overwritten but the access could be lost

The forwarded assistant's four-arm suggestion is not independently human
ratification. The current `R121_LEVEL1_SCOPE_20260916.md` records it as the binding
scope: Level-1 + responsive teaching; original starting point + responsive
teaching; SEAL; original + Markdown. That same note explicitly says the new
benchmark is **not** ratified at implementation-byte level. Its reported R132
and R136 results are context, not observations independently re-audited here.

Read sources and SHA-256 at the snapshot:

| Source | SHA-256 |
| --- | --- |
| `AGENTS.md` | `7c9ee4b3050b72c31e933421e06a06a9fe167270dd804de97995d41bcf0a71f9` |
| `research_notes/analysis/R121_LEVEL1_SCOPE_20260916.md` | `1ed469475fc3fd8d5d74344f01d1611059d1de7cfe267c85357263d5e22db917` |
| `research_notes/THESIS_RAW_ROHIN_2026-09-11.md`, Message 121 | `75d5c4763eb39df30967004fa60d3c4bd5dfdf62e24649366e72ae85384bd388` |
| `research_notes/forwarded/GPT_SCOPE_LEVEL1_SEAL_2026-09-15.md` | `fa4f3b75d079bcaf92bf98cd60701c9388f5f94415e446242e40c24b66b4d3b8` |
| `research_notes/ASTRA_LAUNCH_PROMPT_2026-09-12.md`, §15 | `0509ee7e0148b0c08af75ce743f4a6f5e432ba536b6ca4def4612081ee8938c0` |
| `research_loop/architecture_intake.py` | `62d29dfa6f34b8093f686615c13dc192bb82c58bb789100be3ff78c91dc9fbea` |
| `research_loop/architecture_deliberation.py` | `f1d8e87cd7bd78b30755e986008936c154453c995c6e83abff70358b80165dcb` |

Existing-state check: the 85 conventional `intake.state.json`/`intake_state.json`
files inspected contained 5 `human_approved`, 67 `human_required`, 4
`awaiting_consensus`, and 9 `collecting_interpretations` phases. This was metadata
inspection, **not cryptographic validation of those approvals**. No R121/R141/
SEAL/four-condition-named workflow was found; targeted content searches did not
locate a bound R121 proposal. For example,
`chg_20260911_multikey_writer_gateway_v10r1_simple/intake_state.json` is
`human_required`, with implementation unauthorized, and its scope excludes
benchmark/model/GPU execution. Neither that state nor an unrelated historical
approval licenses this design. Absence is bounded to the inspected paths.

The deliberation runner supplies separate interpretation contexts, then both
interpretations to critique, and terminates at `human_required`. Intake verifies
proposal/context hashes, every visibility cell, all test/concern dispositions,
and separate evidence-bound human ratification. This Markdown is preliminary
input to that process, not a schema-valid, proposal-hash-bound interpretation.

## 2. Smallest experiment and what it can identify

**Propose one skill family, four acquisition conditions, three paired acquisition
seeds: 12 online runs.** Use read-only checkpoint forks, not restarts of existing
children. Add disposable evaluation processes and SEAL offline training, not
new developmental levels. All numerical limits below are proposed design bytes,
not previously approved budgets or evidence of feasibility.

Candidate skill: **counterexample-guided repair of short integer-list
transformations**. Each task supplies a specification, a buggy pure expression,
and a small set of input/output examples; the learner diagnoses and repairs it.
Use a restricted, deterministic expression grammar, not arbitrary program
execution. Include index/boundary, filter-predicate, and aggregation mistakes;
transfer combines familiar primitives in previously unused expression shapes.
Evaluate executable correctness rather than richness of prose. The skill is
repair/checking, not recalling a source table or a concealed label mapping.

This is a candidate, not a replacement for the R141 worker's interface decision.
Consume its frozen common-interface contract and regression receipts. First
establish that base and Level-1 can express known-correct answers and have
non-floor/non-ceiling semantic performance on disjoint calibration tasks. If
the worker's interface cannot support this family, return the choice to
adjudication; do not silently fix parsers or change skill after sealed results.

| Arm | Starting state | Acquisition intervention | Persistent state |
| --- | --- | --- | --- |
| A: L1 + RT | One provenance-clean, preselected Level-1 adapter on frozen base | Common responsive parent policy; learner attempts, receives feedback, writes its own consolidation material | Same single LoRA adapter, updated only at declared sleep boundaries |
| B: original + RT | Identical frozen base; newly initialized zero-effective-update LoRA | Exactly the same parent policy, opportunities, tasks, and update rule as A | Single LoRA adapter; no Level-1 history |
| C: SEAL | Same frozen base plus separately trained self-edit-policy LoRA | Self-edits, inner adaptation, and a genuine prior outer reward-learning loop; no online parent | Single live LoRA adapter; offline policy-training lineage disclosed |
| D: original + MD | Identical base, adapters disabled | Learner-written bounded Markdown memory using the same acquisition tasks/outcomes | Markdown only; zero parameter/optimizer updates |

“Original frozen-base starting point” in B does not mean prohibit LoRA learning:
that would remove the essential original-model learning control. D, in contrast,
has no parameter-learning channel. C's offline-trained policy is **not** an
untouched original starting point; measure its online step-zero performance.

Use one pinned L1 checkpoint and three acquisition seeds for the smallest
conditional test. Report that these do not constitute three independent
Level-1 developmental histories. A–B tests the effect of this initialization
package on subsequent acquisition, not richness as a uniquely isolated cause.
An equal-pretraining-budget sham/masked initialization would be required for a
strong richness-specific causal claim; it is not quietly added as a fifth arm.
Preserve existing FULL/masked evidence as exploratory, not matched substitutes.

## 3. Frozen weights, lineage, and actual update mechanism

- Pin model revision, tokenizer/chat template, inference precision, decoding,
  base-file hashes, adapter hashes, and lineage before acquisition. The base is
  **Qwen2.5-7B-Instruct**, never full-model SFT, merged/re-exported weight updates,
  another model, or an unreported provider-backed learner.
- Use rank-8 LoRA and one live adapter per child. Copy the selected L1 adapter's
  exact module list/scaling/dropout to B and C; do not invent compatibility or
  silently resize a historical checkpoint. If its config differs, resolve the
  mismatch before binding the protocol. All optimizer parameter IDs must be
  LoRA IDs; assert frozen base before and after every update.
- A continues its L1 adapter; B starts a no-op adapter. Reset acquisition
  optimizer, scheduler and replay state in both; retain historical artifacts
  but never inherit one arm's replay/optimizer into another. Proposed optimizer
  is AdamW, learning rate 1e-4, betas (0.9, 0.999), weight decay 0, gradient clip
  1; the common effective batch and exact masking/packing become manifest bytes.
- A/B sleep targets are the **learner's own event-grounded writes**. Parent
  lesson text is not directly packed, even as conditioning bytes, into sleep
  examples. Exact-byte provenance tests must distinguish legitimate child
  restatement from direct lesson ingestion. No seal-evaluation output is a row.
- C forks temporary copies for offline inner-loop trials, preserving receipts
  and restoring the parent policy state between candidates; these are not
  interacting developmental clones. Its online single adapter starts from the
  resulting policy checkpoint and receives only its own grounded self-edits.
- D's learner authors a complete replacement MD snapshot; no teacher-written
  oracle file, silent rolling transcript, optimizer state, or hidden retrieval.
  Base checksums must remain identical in all four arms.

The adapter/model revision, checkpoint path and module config are intentionally
not fabricated. Their absence is a concrete protocol-binding prerequisite.

## 4. Splits, visibility, and bounded loops

Before any scored online acquisition, bind IDs, generator/version hashes,
deduplication rules and semantic-template partitions:

- 16 interface/calibration tasks; never used for reported skill gain.
- 64 SEAL outer-training tasks, each with legal support and two private
  reward queries; separate from every online task and final template.
- 16 method-development tasks for fixed go/no-go feasibility checks, not
  unrestricted hyperparameter search.
- 64 online acquisition tasks, identical ordered stream within each paired
  seed and arm; each has two allowed attempt/verifier opportunities.
- 64 sealed skill tasks: 32 near-transfer/retention and 32 compositional
  transfer. Task IDs, solutions and expression templates are disjoint from
  online, development and outer-training tasks.
- A fixed sealed 128-item capability panel: 32 each for code, math, tool-use
  and concise answers. Preserve the older 32-item panel separately as historical
  diagnostic evidence; do not pretend its source-present scores were retention.

No clean ancestry includes deployment-gym-exposed weights, tasks, rows, parent
notes, rankings, or selection decisions. Semantic deduplication must cover
earlier L1 material as well as this experiment. Unknown ancestry blocks a clean
claim; synthetic task generation alone does not prove uncontamination.

### Visibility contract (deny unless explicitly permitted)

| Information | A/B learner and parent | C self-editor / trainer | D learner / file | Sealed evaluator / later analyst |
| --- | --- | --- | --- | --- |
| Current online task, own attempts, two legal verifier outcomes | Yes; parent sees only its paired learner | Yes online | Yes | Logged for later audit, never injected into retention |
| Another arm's attempts, lessons, MD or trained state | No | No | No | Analyst after protocol freeze |
| Online verifier's hidden cases/reference solution | No; outcome is pass/fail plus one bounded counterexample, no reference expression | Same | Same | Verifier only during acquisition |
| Parent response | Own arm only, current episode; never direct sleep bytes | No | No | Audit only |
| Offline reward task queries/answers | No | Isolated reward evaluator sees them; optimizer receives scalar post-adaptation reward, self-editor sees support only | No | Audit later |
| Method-development cases | Not in acquisition contexts; parent remains blind to report/gate scores | Isolated development evaluator; no final data | Isolated evaluator | Protocol designers may see development results before freezing |
| Sealed skill/capability prompts | No during acquisition | No during acquisition or policy training | No during acquisition | Disposable learner sees only its current legitimate task input |
| Sealed reference answers, verdicts, scores, evaluation generations | No | No reward, row selection, or fitting access | No | Scorer/analyst only after all acquisitions and selection are locked |
| Histories, MD, lesson/source files at retention | No | No | No; separate MD-present assay explicitly permits its pinned MD only | Evaluator cannot mount these for file-free runs |

Proposed online loop: eight blocks of eight tasks. Each task starts a fresh
episode. Attempt -> first legal outcome -> parent intervention (A/B) or local
review (C/D) -> revised attempt -> second legal outcome -> learner-authored
write/self-edit/MD replacement. Sleep/update after each block for A/B/C. No
cross-arm sharing and no cumulative prompt transcript between blocks. A/B's
parent may see this block's prior own-arm events within the common context cap,
not an unbounded private notebook. D may read only its current MD snapshot.

All arms get the same task information and verifier opportunities, **not identical
feedback text**: a responsive teacher legitimately reacts to different attempts.
Log prompt policy, actual interventions and consumption. Silence/missing slots
are outcomes, not secretly replaced calls; no safeguard-refused requests are
rerouted. Provider scheduling and any prospective Astra setup remain Main's work.

## 5. Proposed resource envelope, not “equal sleeps”

| Resource, per online seed/arm | Hard ceiling |
| --- | --- |
| Tasks / verified attempts | 64 / 128 |
| Generation | Four slots per task, each at most 512 generated tokens: initial attempt, intervention/local review, revised attempt, persistent write; at most 131,072 total output tokens |
| Input context | 4,096 tokenizer tokens per slot, including any MD and prior block events; no silent overflow retry |
| External parent contribution | A/B only: at most 64 responses, 32,768 output tokens, already inside the generation ceiling |
| Online loss-bearing token exposures, A/B/C | At most 16,384 per eight-task block; 131,072 total |
| Online optimizer steps, A/B/C | At most 8/block, 64 total; at most 2,048 loss-bearing tokens/step |
| D parameter updates / file | Zero / 1,024 tokens, versioned whole-file replacement after each task |

Loss-token caps include repetitions/epochs, not just unique rows. Log unique
tokens, exposures per row, admitted/rejected rows, actual steps, padding/forward
tokens, and underfilled blocks. No fabricated writes or extra epochs to fill a
budget; a no-valid-write block performs zero steps. Preserve the deficit and
report it. The budget matches opportunity ceilings, not guaranteed actual dose.

Count all parent and learner input/output tokens separately, verifier work,
latency, GPU-seconds, retry/timeout work, and available provider cost. Unreported
provider-internal reasoning compute is “unobserved,” not zero. D's zero optimizer
cost is intentional; report performance versus tokens and compute as well as
versus task opportunities. Equal token counts across a larger teacher and a
local learner are not equal FLOPs. No speed/cost superiority without measured
complete costs.

### C: what would actually fill the SEAL condition

Primary source [P1]: Zweiger et al., *Self-Adapting Language Models*,
arXiv:2506.10943v2, §§2, 4.1, 4.2 and Appendix A.3;
`https://arxiv.org/html/2506.10943v2` (read September 16, 2026).
The paper describes self-edit generation, inner weight adaptation, and outer
RL on post-adaptation performance. Its ReSTEM implementation trains on positively
rewarded self-edits; its few-shot experiment generates adaptation configurations
and updates LoRA. Published few-shot and knowledge-incorporation regimes differ.
Thus one reflection followed by SFT omits the defining outer learned policy.

My proposed **full-loop SEAL reimplementation constrained to frozen Qwen2.5-7B
and rank-8 LoRA**, not an exact published-result reproduction:

1. Two offline outer rounds, 64 outer-training tasks/round, two sampled
   self-edits/task: 256 candidate self-edits, each at most 512 tokens.
2. For each candidate, restore the round's policy adapter and empty optimizer;
   perform at most two inner steps, at most 2,048 loss tokens/step. The self-edit
   consists of grounded learner-generated examples for this restricted skill.
3. Measure post-adaptation performance on the task's two private reward queries;
   at most 512 query generations, each 256 tokens. Binary positive reward
   requires both queries correct; log failed and untrainable candidates too.
4. ReSTEM-style outer update on positive self-edits only: at most 64 steps per
   round, 2,048 loss tokens/step. No successful candidates means no outer update,
   not permission to call an untrained reflection system SEAL.
5. Freeze the two-round procedure, select the final policy by this fixed rule,
   and measure online step-zero performance. Continue inner self-edit adaptation
   at the same online block budgets as A/B; no online outer reward access.

Offline per-seed ceilings: 512 inner + 128 outer optimizer steps; 1,310,720
loss-token exposures; 131,072 self-edit output tokens plus 131,072 reward-query
output tokens. Charge these costs separately and include them in total-system
comparisons, alongside A's historical L1 development cost. Three independently
trained C policies support three paired online seeds. Development checks add
at most 16 × 256 generated tokens per seed/condition and no fitting.

This task, fixed update budget, generated-data action space and cumulative
online adaptation are modifications, not claims that the published ARC setup
used them. Before admitting C, pin official code commit/dependencies and map
the implementation against [P1], prove outer-update lineage, and decide whether
the constrained mapping satisfies the requested comparator. A rank/model/update
mechanism mismatch must remain in the method name. If only reflection+SFT is
feasible, report **three conditions plus an incomplete SEAL comparator**, not a
completed four-condition result. Do not launch a surrogate and rename it later.

## 6. Retention and capability evidence

At online task counts 0, 16, 32 and 64, fork read-only adapter snapshots into
fresh processes. Disable parent connection, MD mounting, history, caches,
retrieval and acquisition artifact access. Only generic fixed interface text
and the novel task's legitimate specification/inputs/examples may enter each
prompt. A buggy expression belonging to that new task is legitimate input;
an acquisition lesson explaining how to solve it is not. Use the same sealed
64 tasks across arms and checkpoints; evaluator outputs never flow back to
training or model/checkpoint selection. Score after acquisitions are locked.

One 512-token answer opportunity per sealed task, no verifier feedback or
reflection repair; report valid-format, executable, and semantically correct
rates independently. Repeat the final file-free assay after unload/reload with
identical bytes to test state persistence/reproducibility. Elapsed idle time
alone is not an interference/forgetting experiment. Skill retention through
later acquisition is measured by the earlier checkpoints' near-transfer
performance through task 64, not by pretending final evaluation writes memory.

D additionally gets the same tasks with its pinned MD present, no parent and
no edits. Paired MD-present versus absent estimates contextual assistance.
Removing its only mutable memory should leave the frozen system at its
file-free baseline distribution. This is a useful negative control: **MD
removal is not learning, forgetting of trained weights, or a scientific win**.
An unexplained D absent-versus-baseline change first triggers a state-leak test.

Primary skill estimand: paired A–B difference in acquisition change from their
own task-zero values on sealed near-transfer; accompany with absolute starts,
ends and area under the 0/16/32/64 curve. Report compositional transfer
separately and C/D contrasts as method comparisons, not equivalent mechanisms.
Show all three seeds and paired task cells; intervals must respect task and
seed dependence. Three seeds do not support fine-grained population certainty.
Training-set accuracy, vocabulary diversity and longer explanations cannot
substitute for this endpoint. Bounded behavioral diagnostics can count whether
an attempt uses the actual counterexample and successfully changes strategy;
they do not measure hidden cognition or establish a richness mediator.

Capability: at tasks 0 and 64, evaluate the fixed 128-item panel file-free under
both minimal-answer and fixed concise-task prompts, with identical token caps.
Report aggregate and each domain, before/after within each arm and against true
base. Proposed noninferiority criterion: one-sided 95% lower bound above -5
percentage points overall and above -10 points per domain on paired correctness;
failure to clear the bound is **inconclusive or impaired**, not preservation.
Calibrate uncertainty/power before ratification; 32 items/domain may be too weak.
Do not enlarge the panel after seeing a convenient result. Preservation relative
to an already-impaired L1 start is insufficient: show its true-base deficit too.

### Suppression versus destruction: explicit causal probes

Keep these read-only, separate from acquisition and checkpoint selection:

- Compare the same frozen base with adapter OFF, L1-at-start ON, and acquired
  adapter ON; B additionally has the zero-update start. Run identical prompts,
  precision and decoding. OFF restoring a lost base answer, with base hashes
  unchanged, supports adapter-induced interference/access suppression, not
  erased base parameters. It does not make the deployed ON system unimpaired.
- Compare minimal versus task-explicit prompting and a deterministic
  format-free semantic readout of the same stored answer where valid. Recovery
  supports elicitation/interface suppression. Do not give arm-specific repairs,
  re-score invalid answers as correct without a frozen rule, or train on these
  diagnostic prompts. The R141 worker owns that rule and its fixtures.
- If an ability present at L1-start ON disappears after acquisition, compare
  the preserved pre-acquisition adapter. Recovery only with that older adapter
  is evidence of **functional forgetting in the changed adapter**. Unlike the
  base, adapter parameters really are overwritten during training.
- Predeclared read-only adapter scales 0, 0.5 and 1 can probe interference on
  capability tasks; any scaled recovery is diagnostic, not a selected primary
  checkpoint or proof that all capabilities survive. Charge diagnostic compute.
- No finite prompt battery establishes irreversible representational
  “destruction.” Without recovery, report observed capability loss and unresolved
  mechanism. Unexpected OFF changes require precision/template/state-integrity
  investigation before any psychological interpretation.

## 7. Concrete deltas and acceptance tests for the later intake

| Delta | Proposed addition/change | Deliberately unchanged/excluded |
| --- | --- | --- |
| Graph G1 | Four isolated acquisition runners from pinned initial states -> immutable snapshots -> sealed evaluator -> analyst; separate SEAL support/inner/reward/outer subgraph and MD store | No Level-2/3 stages, shared learner, hippocampus, deployment clone graph or fleet intervention |
| Loop L1 | Shared task/attempt/outcome clock with responsive A/B interventions and bounded block LoRA writes; C learned self-edit loop; D file edits | No self-replay expansion, hidden retries, repeated-final reward, full-base updates |
| Claim C1 | Conditional L1-initialization effect on bounded skill acquisition, file-free retention/transfer, and separately measured capability preservation | No established H2 generality, richness causality, mature learning, complete developmental thesis, or SEAL reproduction by name alone |
| Visibility V1 | Explicit support/reward/dev/final partition and default-deny artifact access; two MD evaluation views | Parents remain blind to sealed scores; child-authored/provenance rules remain |
| Tests T1–T10 | New matched benchmark contracts and analysis acceptance criteria below | Existing tests/evidence are not relaxed or rewritten to manufacture a positive result |

| Test ID | Required evidence, failure disposition |
| --- | --- |
| A-T1 interface | R141 worker's common parser/readout fixtures; correct known outputs accepted for all arms; truncation, syntax and semantic failures separate. Stop benchmark admission if interface confounds skill. |
| A-T2 lineage | Exact clean adapter ancestry, split/template contamination checks, base hashes and LoRA-only optimizer IDs. Unknown ancestry or base mutation invalidates the affected arm. |
| A-T3 isolation | Canary artifacts and permission checks prove parents/editors cannot see finals, cross-arm states or report scores; evaluator has no lesson/MD/history mounts in absent mode. Any leak quarantines results. |
| A-T4 own-write packing | Byte provenance/masking fixture rejects direct parent lessons, reward queries and evaluation-generated rows. No replay/optimizer inheritance across arms. |
| A-T5 dose | Toy receipts reconcile opportunities, COMPLETE versus consumed replies, missing slots, token exposures, steps, MD versions and total costs. Empty-valid-row blocks cannot update. |
| A-T6 SEAL fidelity | Offline candidate/reset/reward/outer-update receipts, positive-edit admission and distinct final tasks; official-version mapping. Missing outer training leaves condition C unmet. |
| A-T7 retention | Fresh-process manifest, read-only snapshots, generic prompt allowlist, reload reproducibility, MD absent/present separation. No adaptation in any evaluation. |
| A-T8 preservation | Fixed paired capability panel, true-base and start/end adapter toggles, domain counts and predeclared noninferiority intervals. Insufficient precision forbids a preservation claim. |
| A-T9 claims/statistics | Paired seeds/tasks, explicit conditional initialization estimand, absolute starts, curves and missingness; no treating evaluation items as independent training seeds. |
| A-T10 authorization | Exact proposal/context hashes, both fresh interpretations, adversarial critique, every disputed choice/test disposed, ratified implementation scope and any required independent-review binding. This document does not pass that gate. |

## 8. Which next actions use which authority?

| Next action | Interpretation of authorization |
| --- | --- |
| Read sources and write this bounded design | Current direct instruction; no material implementation, no new intake record authored here |
| R141 response-interface bug repair restoring the already-frozen contract, preserving benchmark semantics | Non-material repair: builder scope, regression test and evidence preservation; Main/worker own it. A new accepted-answer definition or score rule instead changes the benchmark and needs material intake. |
| Existing invariant-preserving L1 experiments, state-preserving plumbing, resource scheduling, prospective logged parent use within allowed rules | Builder standing authorization with own CPU/provenance gate and dated Builder log; this analysis imposes no new independent-review veto on those runs |
| Introduce this four-arm benchmark: skill/splits, score semantics, capability panel/margins, visibility edges, analysis/claim boundaries | Material R121 intake and exact-scope human ratification before changing the benchmark/claim system, as the latest scope expressly requires. Raw scope direction is not approval of these proposed bytes. |
| Implement C's outer reward-policy loop and decide its frozen-base/LoRA/provenance mapping and comparator name | Include in the material benchmark/loop proposal. Request an explicit disposition of how parent score-blindness applies to the local self-editor's reward-trained policy and which sourced self-edit rows are legal. No silent invariant exception. |
| Implement D's MD edit/read policy and absent/present scoring as a new official comparison | Include in the same material proposal. Once bound, storage/transport code preserving that policy can be builder implementation detail. |
| Pick exact compatible checkpoint, seed order, packing/device details within a ratified protocol; run CPU/provenance checks | Builder implementation choice if it preserves approved scope; never select using final scores or move a registered endpoint to fit results |
| Change model, rank/adapter structure contrary to invariant, ingest direct teacher targets, expose sealed scores, pool contaminated ancestry | Reserved material invariant change, not standing authorization; do not use this design to request or imply those changes |
| Leases/extensions/onboarding, external sharing, deployment or Level-2/3 | Not authorized by this analysis; scope excludes developmental/deployment work and reserves the other actions for Rohin |

For the material benchmark change, later workflow execution must declare its
approved intake and requested scope, revalidate exact bindings, and satisfy
the change's explicit pre-GPU tests and review gate. Implementation followed
by fresh independent review plus author-side scientific advocate belongs to
that path; agreement cannot ratify. Do not misapply this to pause unrelated
builder-authorized experiments. This analysis performs neither path's launches.

## 9. Disputed choices requiring explicit cross-critique disposition

All remain **open**; these are recommendations, not resolutions:

1. **A-D1, skill/interface (A-T1/A-T9):** prefer constrained program repair for
   verifiable correction and transfer; reject if calibrated baseline is a parser
   floor. Is a simpler task more informative without reducing this to label
   lookup? Freeze the answer before scoring any sealed item.
2. **A-D2, initialization inference (A-T2/A-T9):** three acquisition seeds from
   one L1 checkpoint are the minimum conditional experiment, not three L1
   replications. Accept the narrower claim or explicitly expand developmental
   replication/sham control; do not claim richness-specific causation from A–B.
3. **A-D3, SEAL fidelity (A-T4/A-T6/A-T10):** does full-loop generated-data SEAL
   under rank-8/own-write constraints satisfy R121, or must an official task
   configuration be replicated? No reward-learning success is guaranteed within
   the proposed cap. The fourth acquisition requirement stays unmet if C fails.
4. **A-D4, dose fairness (A-T5/A-T9):** common online opportunities are the primary
   axis; offline costs and external-teacher compute are unequal and separately
   reported. Is a total-compute-matched secondary comparison required before
   any efficiency language? Do not compensate via secret extra episodes.
5. **A-D5, source-free construct (A-T3/A-T7):** legitimate new task examples remain
   visible, but learned strategy descriptions do not. Adjudicate the exact prompt
   allowlist so “file-free” cannot be misread as “without the task inputs.”
6. **A-D6, preservation (A-T8):** the 128-item panel and 5/10-point margins need
   pre-result power/uncertainty scrutiny. Retain “inconclusive” if the smallest
   panel cannot resolve the claim; do not default to no-significance = preserved.
7. **A-D7, MD strength (A-T5/A-T7):** prefer learner-written 1,024-token memory for
   transparent provenance. A teacher-authored file may be a stronger contextual
   comparator but adds teacher compute/information and must be named and budgeted.
8. **A-D8, governance boundary (A-T10):** distinguish the scope note's explicitly
   unratified benchmark/claims from routine invariant-preserving experiments.
   Require a new exact R121 binding, not blanket ratification of all builder work
   or reuse of an unrelated historical `human_approved` flag.

Bottom line: there is a bounded four-condition **design**, not presently a
verified four-condition experiment. Its smallest defensible claim concerns a
particular Level-1 initialization's subsequent learning under controlled
opportunities, with source-free readout and separately qualified capability
evidence. It neither treats removing Markdown as learning nor permits a
reflection+SFT surrogate to occupy the SEAL arm by relabeling.
