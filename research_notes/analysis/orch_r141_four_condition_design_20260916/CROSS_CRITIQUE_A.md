# R141 / R121 — adversarial cross-critique A of interpretation B

2026-09-16 UTC. **Recommendations and open objections for eventual consensus;
not adjudicated dispositions, ratification, or implementation/launch authority.**
Only this new document is owned. A and B remain unchanged. No code, experiment,
enumeration, provider call, launch, Git operation, ledger edit or fleet action
is performed. Main owns the enumeration and R141 interface repair; neither is
duplicated here. No other cross-critique was read.

## Evidence bound to this critique

| Read artifact | SHA-256 |
| --- | --- |
| `INTERPRETATION_A.md` | `9e23c518743b45ccf5805181b0ac9ec262d6e9f5570547fba18cf216c4e9a307` |
| `INTERPRETATION_B.md` | `bdaca00f60df3ff095d5eee82a0f1daf1ba733044188be603bf5cd2d0815650b` |
| `../R121_LEVEL1_SCOPE_20260916.md` | `1ed469475fc3fd8d5d74344f01d1611059d1de7cfe267c85357263d5e22db917` |

Also re-read root `AGENTS.md` and launch-prompt §15 invariants. A's earlier
source bindings and governance reading remain context, not approvals.

New evidence supplied by Main through the current user message, verbatim:

> CPU enumeration by Main of B six primitives, values0–3 lengths3–5 length1–3 programs:1344 inputs,258 syntactic programs,97 semantic classes(6/20/71 by maximal length). B's32+8+48 consumes88 classes leaving9 for offline SEAL/L1/dev.

This is a **reported CPU result**, not independently reproduced or bound here
to an enumerator/output hash. Consensus needs Main's exact semantics, command,
code/version and output receipts, including what the length bins mean. The
arithmetic is consistent: 64 + 256 + 1,024 inputs; 6 + 36 + 216 programs;
32 + 8 + 48 = 88, and 97 - 88 = 9. No new primary-source SEAL check is made:
method-fidelity obligations below come from the scope and the two proposals,
not a fresh certification of the paper or implementation.

## Overall recommendation

**Return B's numeric task specification for revision before binding a benchmark
proposal; retain its four-arm and isolation principles.** The enumeration
confirms B's own B-D07 feasibility concern rather than defeating its general
design. Nine remaining classes do not mathematically prove that every offline
SEAL design is impossible. They do prove that offline training, validation,
development and any target-family L1 preparation cannot remain unspecified.
Nor does A supply an automatically valid replacement: its task grammar was not
enumerated, and its budgets and capability panel conflict with B's.

The strongest common conclusion is a conditional **initialization-package
comparison under responsive teaching**, not richness-specific causality or H2.
A four-condition result must retain original-model **LoRA learning**, genuine
SEAL method accounting, and both MD-present and MD-absent readouts. All proposed
resolutions below remain open until the adjudicator explicitly disposes them.

## CA-01 — Semantic capacity is an explicit allocation constraint

**Severity: blocking for B's present benchmark specification.** B §4 consumes
88 of 97 classes before supplying any offline SEAL allocation or development
count. Every class excluded because three demonstrations cannot identify it,
or because of prior exposure, further reduces the usable pool. Therefore nine
is an upper bound on the remainder under the proposed exclusions, not a usable
offline budget already demonstrated. Related: B-D07, B-T02/B-T05/B-T09;
A-D1/A-D3/A-D4, A-T2/A-T5/A-T6.

**Recommended disposition:** accept Main's enumeration as a reason to require
a revised allocation; reject simply changing task IDs, shuffling examples,
renaming programs, or adding seeds to create supposedly new semantic classes.
Three seeds may reuse the same declared partition as independent training
realizations; they do not triple the number of independent functions. Rotation
of class assignments between seeds needs a separate fold-isolation design,
especially if an offline policy or L1 checkpoint is reused across folds.

L1 preparation is not automatically another fixed number of these 97 classes:
an existing checkpoint may have no target-grammar exposure. Its ancestry still
needs evidence; a different dataset label does not prove absence of overlap.
Generic L1 preparation must not be retroactively assigned nine convenient
classes or retrained to make this budget work.

**Questions for consensus:** retain this grammar and shrink partitions, or
enlarge/change the grammar/domain before sealing? How many usable classes remain
after identifiability and ancestry exclusions? What are the separate outer-train,
outer-validation and development counts? A possible bookkeeping reallocation
is 24 acquisition + 6 interference + 24 sealed + 24 outer-train + 6
outer-validation + 12 development + 1 reserve = 97. This is **only an arithmetic
example**, not a recommendation, feasibility proof or revised authorization;
it has no slack for exclusions and requires its own power/method review.

## CA-02 — Length balancing and semantic equivalence are not interchangeable

**Severity: blocking if “balanced” means 16 distinct classes at each length.**
B's 48 sealed tasks cannot include 16 distinct one-primitive functions when
only six exist, even before other partitions take any. Identity padding means
syntactic length is not a disjoint semantic complexity stratum. A program's
equivalent longer spelling cannot create a new held-out function. Related:
B-D07, B-T02/B-T10; A-T2/A-T9.

**Recommended disposition:** define one semantic key as the output vector on
Main's complete, ordered 1,344-input domain. Bind empty-list/intermediate-list
semantics, composition order and canonical input ordering. Confirm whether
6/20/71 denotes new classes first realizable at lengths 1/2/3 or a different
enumerator labeling; do not silently reinterpret “maximal length.” Use a declared
canonical complexity statistic, then choose feasible, non-overlapping strata
and report their counts rather than claiming equal length balance.

Equivalence on this domain is not automatically equivalence on longer lists or
other values. If those are added as transfer, define the reference domain used
for deduplication and the new claim. A larger alphabet/longer domain may split
some equivalences but does not guarantee enough new functions; re-enumeration
is necessary. Shared primitive semantics are legal vocabulary, not contamination.
Class fingerprints and whole-domain output tables remain evaluator artifacts,
not learner aids.

**Question:** what exact class/complexity partition will replace the infeasible
reading of “balanced,” and how many final classes remain after all exclusions?

## CA-03 — Three demonstrations, additional counterexamples, and shortcut solving

**Severity: high; potential construct failure.** B requires three demonstrations
that uniquely identify each semantic class, while teaching counterexample-guided
synthesis. If those examples uniquely identify the answer, a counterexample is
not information-theoretically necessary; it diagnoses a learner's search or
reasoning failure. That is a legitimate skill, but different from active
information gathering needed to resolve an ambiguous task. An exhaustive
258-program search could solve identifiable tasks without richness. This is a
methodological observation, not a claim about observed model performance.

**Recommended disposition:** require Main's proof/receipt that each selected
class has an identifying triple under the frozen demonstration rule; distinct
whole-domain vectors alone do not imply three examples suffice. Record how many
classes are excluded. Freeze a deterministic demonstration-selection policy
without encoding a class index in ordering or input choices. Use a fixed
symbolic enumeration diagnostic as an upper-bound/shortcut check if later
authorized; do not implement it here or add it as a replacement acquisition arm.

**Questions:** is the target strategy search/error correction or information
acquisition? Does B really require three individually distinguishing examples
for every class? If fewer/more examples or ambiguous support sets are chosen,
what changes in the verifier contract and final success criterion? Do not change
these after a floor/ceiling is discovered on sealed data. Related: B-T02/B-T03/
B-T10/B-T12; A-T1/A-T7/A-T9.

## CA-04 — Agree on narrow causality; reject either memo's shorthand as stronger proof

**Severity: high for claims; principle accepted.** B correctly distinguishes
L1+R minus O+R from both parenting-versus-no-parent and richness-specific
effects. One selected L1 adapter plus three online seeds estimates variation
conditional on that adapter; it does not replicate L1 construction. Matching
teacher policy does not make actual interventions or optimization trajectories
identical. Starting competence and pretrained adapter geometry are part of the
initialization package, not controlled-away explanations.

**Recommended disposition:** retain B's stronger baseline/ceiling cautions and
post-trajectory embargo. Treat A's “smallest defensible claim” as conditional,
not general. A common-start-miss subset is exploratory and selected using noisy
outcomes; it does not identify mediation. Neither difference-in-gains nor an
AUC subtracting starts removes every ceiling/regression issue. Preserve absolute
performance and declared difficulty strata alongside the gain contrast.

**Questions:** select endpoint gain contrast (A's primary) or normalized gain
AUC (B's primary), not whichever wins. If B's five-percentage-point margin is
retained, define mean AUC as the trapezoidal gain integral divided by the task
budget; an unnormalized integral has accuracy-times-task units. Freeze practical
margin, uncertainty, seed/task clustering and multiplicity. Additional sham or
independent L1 histories require a scope decision, not rhetorical substitution
of historical FULL/masked evidence. Related: B-D01/B-D04, B-T10/B-T12;
A-D2/A-D4, A-T9. H2 and richness mediation remain untested.

## CA-05 — Original-model LoRA control is indispensable, but “neutral” needs proof

**Severity: blocking if implemented as frozen or historical trained control.**
Accept B-D02 without qualification: O+R must start at the same original frozen
base function, then receive online LoRA learning and the same responsive policy
as L1+R. D, adapter-OFF diagnostics and historical unparented/masked lives are
not substitutes. Neither memo permits full-base updates.

**Recommended disposition:** bind exact Qwen2.5-7B-Instruct revision, rank-8
adapter targets/scaling, trainable parameter IDs, initialization and reset rules.
Require functional no-op at O+R start **and** a nondegenerate trainable
initialization; naming an adapter “neutral” is not evidence. Reset optimizer,
scheduler and replay symmetrically; preserve the intentional difference in
adapter values. Use the learner's event-grounded writes, not teacher lesson
bytes as sleep targets or conditioning. A/B hyperparameters must be matched or
their mismatch explicitly adjudicated, not tuned separately on finals.

**Question:** which actual compatible checkpoint/configuration supplies these
bytes, and what does the R141 worker's existing repair contract guarantee?
Accept B's parent-label blinding and add it to the final visibility contract:
do not disclose arm names/provenance, while acknowledging that behavior can
reveal treatment. Related: B-T01/B-T04, A-T2/A-T4/A-T5.

## CA-06 — SEAL: policy-state conflict and unspecified offline budget remain blocking

**Severity: blocking for admitting the comparator, not evidence SEAL cannot work.**
B says hold the offline self-edit policy fixed online, but leaves open whether
it is the learner's adapter or a separate policy adapter. A continues a single
adapter online, changing the same parameters used to generate edits. These
cannot both mean fixed **policy parameters** and online updates to that same
adapter. Freezing the outer optimization *procedure* is a different statement.
A separate frozen policy state may alter the one-adapter mechanism and costs;
it must not enter as an unexamined implementation detail.

**Recommended disposition:** enumerate the actual parameter stores, ownership,
initialization, reads, writes, candidate resets and checkpoint lineage for C.
Select the applicable primary-source regime and map it component by component.
Decide whether R121 accepts a named constrained SEAL implementation under the
existing base/LoRA rules. Do not label reflection+SFT as SEAL, use sealed scores
as reward, or silently add a second learning adapter/external learner.

A's particular two-round/64-task offline schedule and fixed online block updates
are proposals, not fidelity evidence; B's flexible budgets are not executable
limits. Importing A's 64 offline classes into B would require 152 classes before
development, exceeding 97. Offline support/reward queries may be distinct inputs
within an outer-training class, but the entire class must stay outside sealed
evaluation. Repeated edits/epochs increase dose, not semantic diversity.

One correction to A's wording: **a faithfully executed outer procedure yielding
zero accepted edits is different from omitting that procedure**. Preserve it as
a documented failed-training/zero-update outcome with actual lineage; do not
convert negative evidence into an omitted arm or falsely advertise a successfully
learned policy. The adjudicator must specify its inclusion/failure rule before
results. Whether it fills R121's requested trained-policy comparison remains an
explicit question, not a post-hoc label change.

**Questions:** freeze outer updates only or freeze an independent policy? Which
official method mapping is acceptable? What exact offline class/dose budget,
validation/selection rule and failure disposition can fit? Related: B-D03/B-D07,
B-T02/B-T05/B-T09; A-D3, A-T4/A-T6/A-T10.

## CA-07 — Markdown asymmetry is required, not a matched-mechanism victory

**Severity: high for interpretation; common proposal accepted conditionally.**
A and B correctly require frozen original+MD with no optimizer and separately
report file-present application and file-free retention. Removing D's only
persistent writable state makes it a state-isolation/no-weight-learning control,
not a competitive equal-mechanism retention baseline. A win over D-absent alone
says nothing about richness, SEAL superiority or better weight learning.

**Recommended disposition:** same MD snapshot and base across present/absent
readouts; identical legitimate task inputs and generic instructions; no parent,
edits, history or caches. Charge file reads, rewrites and prior context. For
deterministic decoding, check unchanged file-free outputs under fixed inference
state; with stochastic/nondeterministic inference use paired seeds/distributions,
not exact identity as a universal requirement. A discrepant absent result is
initially an isolation issue, not evidence MD was consolidated into weights.

**Questions:** A proposes 1,024 tokens, B 2,048; which cap, read frequency, author,
rewrite/truncation policy and charged context will be bound? A's 512-token
persistent-write slot can underfill its nominal 1,024-token full-replacement
file; reconcile the effective editable size rather than advertising a larger
usable memory. Related: B-D04, B-T06/B-T09/B-T12; A-D7, A-T5/A-T7/A-T9.

## CA-08 — Actor-level visibility still needs separation inside the evaluator

**Severity: blocking until a complete information-flow contract is bound.**
B's evaluator actor may read private references, while a model executes inside
that evaluator. The trusted scoring process may read answers; the evaluated
learner's prompt must not. Similarly, “offline optimizer sees feedback/reward”
must distinguish scalar reward for selection from private query/answer text
entering self-edit generation or training examples. These are separate actors,
not permissions inherited by everything in one process group.

**Recommended disposition:** retain B's scheduler/side-channel protections and
default to post-trajectory scoring. Bind exhaustive stage × information cells,
including support examples, counterexample-selection data, full truth tables,
semantic fingerprints, reward queries, answers, verdicts, evaluation generations,
MD and parent responses. Training-time verifier feedback is allowed according
to contract; sealed verdicts are not. A's proposal to show a bounded
counterexample after each of two attempts differs from B's single optional
learner-requested counterexample; choose exact timing/content before parity is
claimed. A stop/pass flag can leak a sealed verdict even without a numeric score.

**Questions:** who can inspect unsealed ancestry/development reports, and what
may the L1 constructor see? B's broad “development diagnostics” permission must
not override parents' report-panel/gate-exam score blindness. Which acquisition
histories survive between tasks for each arm, and within what input cap? What
may the model see during tool-capability evaluation? Related: B-D05, B-T04/B-T07/
B-T08; A-D5, A-T3/A-T4/A-T7.

## CA-09 — Numeric scope is unresolved, not an average of A and B

**Severity: blocking for exact-byte protocol binding.** Both call numbers
proposals, but a hybrid must settle the following explicitly. Related:
B-T02/B-T09/B-T10/B-T11 and A-T2/A-T5/A-T8/A-T9/A-T10.

| Contract | A | B | Required disposition |
| --- | --- | --- | --- |
| Task construct | Repair buggy integer-list expressions | Synthesize compositions of six primitives | Choose one; B's enumeration does not establish A's feasibility |
| Online dose | 64 tasks; eight blocks | 32 tasks; checkpoints at 0/8/16/32 | Freeze tasks, update boundaries and actual generation/exposure caps |
| Interference | No separate challenge block | Eight further acquisition tasks | Bind total budget 40 if B retained; score at 32 and 40 separately |
| Sealed skill set | 64; 32 near + 32 compositional | 48, “balanced” by length | Resolve capacity, strata, and what retention versus transfer measures |
| Offline/development | 64 outer tasks, 16 development, 16 calibration | No numerical allocation | Allocate disjoint classes before adopting any online count |
| Generation/training | Explicit 512-token slots and step/exposure caps | Finite ceilings requested but unnamed | Bind maxima, unique rows, exposures, repeats, exceptions and failures |
| MD size | 1,024 tokens | 2,048 tokens | Bind effective writable/readable size and rewrite costs |
| Capability panel | New 128-item panel, older 32 preserved separately | Bind existing fixed panel | No silent substitution; exact identities and any enlargement need disposition |
| Capability tolerance | 5 pp pooled, 10 pp/domain | 5 pp/domain against start and original | Choose estimand/margins/power, not an easier test after loss |
| Primary skill metric | Endpoint gain contrast | Gain-AUC contrast; proposed 5 pp meaningful margin | One primary or preregistered multiplicity; specify normalized units |
| Seeds | Three online seeds, one L1 start; three C policy seeds | At least three online seeds, offline replication unresolved | Bind what is independently trained versus shared |

Matching acquisition-task opportunities does not imply matched teacher compute,
gradient exposures or lifecycle cost. Missing offline costs remain unknown.
Freezing method-specific budgets is necessary but must not remove defining SEAL
behavior merely to match sleeps. Prebind delivery failure versus algorithm
failure and paired rerun rules; no successful-only denominator or selective retry.

## CA-10 — Retention and preservation claims need narrower, separable evidence

**Severity: high for claims.** B's eight-task interference block is a stronger
test of robustness to further updates than A's reload alone, but is also eight
more acquisition opportunities. Same-family tasks can improve performance;
the block must not be called destructive interference by assumption. All methods
receive the same declared opportunity stream, with D changing its file only.
Same-family forgetting robustness does not establish long-horizon developmental
retention or H2. Preserve endpoint and post-block scores separately.

Both memos' sealed fresh-class tasks test retained **procedural transfer**, not
direct recall of acquisition examples. Define whether near-transfer and
composition strata are sufficiently distinct; do not count the same class as
two independent endpoints. Read-only evaluations add no rehearsal.

For capability, adopt B's explicit start **and original-base** comparisons and
A's separation of base suppression from adapter forgetting. An unchanged base
hash with adapter-OFF recovery localizes adapter-associated interference/access
loss, not preserved usable capability ON. Loss of previously learned LoRA
behavior may be functional forgetting in overwritten adapter weights; restoring
an older adapter is different from eliciting the current one. No finite probe
battery proves irreversible representational destruction.

**Recommended disposition:** capability correctness, interface validity and
elicitation diagnostics are distinct outputs. Do not replace the fixed panel
with the easier grammar. A 5-pp domain tolerance is much finer than an eight-item
domain's 12.5-pp score increment; three runs on the same items do not create 24
independent task classes. This does not prevent exact reporting on a finite
panel, but broad noninferiority requires a specified sampling/uncertainty model
and adequate power. A's larger panel and looser domain margin are no automatic
solution. Unknown precision means unknown preservation, not demonstrated safety
of acquisition. Related: B-D06, B-T08/B-T11/B-T12; A-D6, A-T7/A-T8/A-T9.

## CA-11 — Governance disposition: new benchmark, not a global runtime veto

**Severity: blocking only for promotion of this new material benchmark/claim
contract.** Accept B §10's durable binding requirement and preserve A's standing-
authorization distinction. No R121 proposal/consensus/ratification IDs are
invented here. The latest scope explicitly leaves new benchmark bytes unratified.
This critique neither authorizes them nor pauses unrelated invariant-preserving
builder work. Main's non-material R141 interface repair remains Main's scope;
altering accepted answer semantics instead would require a benchmark disposition.

**Recommended disposition:** exact class allocation, feedback/visibility,
method state, budgets, endpoints and fidelity names become graph/loop/claim/
visibility/test deltas in the subsequent proposal. All CA objections, A-D1–A-D8,
B-D01–B-D07, A-T1–A-T10 and B-T01–B-T12 need explicit mapped dispositions; merged
tests need a crosswalk, not dropped concerns. Any later schema-bound derivative
must preserve source identities and bind the revised proposal, not suggest
these pre-proposal independent memos reviewed unseen exact bytes. Rohin's
separate exact-scope ratification and the applicable implementation/review gate
remain later actions. Related: A-D8, A-T10, B §10.

## Proposed consensus sequence — no decisions taken here

1. Bind Main's enumeration and usable-class/identifiability receipts; settle
   CA-01–CA-03 before declaring the task regime feasible.
2. Choose the narrow claim and one numeric contract; settle CA-04/CA-09/CA-10,
   including what would count as a negative or inconclusive finding.
3. Bind original+LoRA, SEAL parameter ownership/method mapping, MD semantics and
   actor-level visibility; settle CA-05–CA-08. An unresolved SEAL comparator
   stays unresolved rather than being filled with reflection+SFT.
4. Dispose every original disagreement/test plus CA-01–CA-11 in a new exact
   proposal/consensus chain. Seek the required human ratification later; no
   statement in this critique supplies it.

Bottom line: **B's scientific control logic is largely sound; its proposed
semantic partition and numeric method contract are not yet executable.** A's
more explicit budgets do not cure those defects and introduce conflicts of
their own. Preserve both originals, revise the shared proposal transparently,
and keep all four acquisition mechanisms and the qualified claim boundary.
