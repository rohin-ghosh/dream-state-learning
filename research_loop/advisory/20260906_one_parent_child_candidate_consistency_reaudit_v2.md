# One-parent/one-child candidate consistency reaudit v2

Date: 2026-09-06

Status: **fresh read-only hostile reaudit of repaired proposal bytes**. This
artifact authorizes no architecture change, implementation, target/task
generation, model or tokenizer call, adapter fit, external deliberation, GPU
use, or scientific claim. It does not overwrite the v1 audit.

Exact repaired bytes audited:

- plan: `research_loop/plans/one_parent_child_headline_v1.md`, SHA-256
  `540bfe55e2a152cd9a17f645209f685f2a009c1480900208792e35eb4fd4a434`;
- scope: `research_loop/changes/chg_20260906_one_parent_child_headline_v1/scope_proposal.json`,
  SHA-256 `c4eed6288d592a22a20f7b0bbcecf1992c521bc20e847dd1186ba2eb7184e614`;
- workflow: `research_loop/workflows/one_parent_child_headline_v1.deliberation.json`,
  SHA-256 `9abaa01e020cc59e2fda551485fcb67cbd9f174f85107fcee5c5370a61a5c39e`.

`AGENTS.md` and the v1 audit were reread. The workflow/scope parse as JSON,
all 15 workflow context paths exist, and `git diff --check` passes for the
three repaired sources.

## Verdict

**SUBSTANTIALLY REPAIRED, BUT STILL REWORK BEFORE EXTERNAL DELIBERATION.** Nine
of the eleven v1 repair items are fully or substantially closed. The new exact
call arithmetic is correct and the one-parent/one-child causal object remains
faithful. The central remaining defect is more important than the repaired
bookkeeping: the proposal specifies a bounded childhood writer but does not
specify the **deployment writer**, which is the intervention whose effect the
headline measures. The stated cumulative clean-base/cap contract cannot hold
if childhood and deployment rows are naively retained.

Blocking repairs before export:

1. define CompilerGym deployment row admission, quotas, retention, fading and
   cumulative clean-base reconstruction under exact fit caps;
2. make P/U optimizer/target-dose padding executable rather than relying on a
   32-position anchor packet that cannot fill all missing slots;
3. remove two residual exact-byte contradictions: deterministic training in
   the opening triad and per-row “independent semantic” review; and
4. bind the actual directive/context source bytes, not only the workflow path
   list, in the eventual export approval.

## 1. Reaudit of the eleven v1 repair items

| v1 repair | status | evidence / residual |
|---|---|---|
| 1. one dyad versus counterfactual child | **PASS** | Section 1 now says exactly one parent/parented child and an isolated U counterfactual with no communication/state exchange. |
| 2. common P/U admission plus P shadow | **PASS, wording polish** | Section 7 now binds one absolute offline process/outcome/application law for both branches and makes the neutral shadow a P attribution tag only. Replace “pre-feedback” with “pre-review” in the shared law because U receives no feedback. |
| 3. metric-qualified claims and pilot mean guard | **PASS** | Section 15 distinguishes terminal level, gAUC, and D; Section 12 requires 3/4 positive and `mean(D)>0`, while correctly rejecting a 0.05 pilot efficacy threshold. |
| 4. adjudicate J/opportunities/E/N conflicts | **PASS** | Section 6.1 gives both sources, selected bytes (`J=3`, 12 decisions, 24 tasks/branch, E=48, max N=32), and explicit scientific/resource reasons. |
| 5. use one calibrated exposure dose | **PASS** | All scientific childhood targets use four exposures and calibration races only LR at the same four exposures. Each fading row sums to four. |
| 6. prove target/anchor volume under every fit cap | **FAIL** | Childhood is proved; deployment is absent, and missing-row filler is not closed. See Sections 2–3 below. |
| 7. bind DREAM cadence/retry/usefulness | **PASS** | Exactly one opportunity/review and one/16-program era/service; early requests replace it; no retry; failure consumes it; emergency fallback is nontrainable; useful post-reset process/outcome support is required. |
| 8. deterministic or declared semantic firewall | **PARTIAL** | The new paragraph makes the live firewall deterministic and moves semantic attacks pre-science, but item 7.6 still says every row passes an “independent semantic” firewall. See Section 4. |
| 9. explicit call/shadow table | **PASS WITH IMPLEMENTATION DETAIL DUE** | The 4,811/757,504 table is arithmetically exact and says the P shadow is inside the P source aggregate. Exact source/corrected/shadow suballocations still need binding before implementation. |
| 10. exact export source binding and scope exception | **HALF PASS** | The scope now narrowly exempts exact-authorized deliberation Codex calls. No preapproval source-binding manifest/state exists, so workflow SHA alone still does not bind source bytes. |
| 11. include audit/dispositions | **PASS FOR v1** | Workflow now includes v1 audit and the plan disposes its main items. If v2 defects are repaired directly in the plan, include the revised plan hash; otherwise add this v2 artifact as context. |

## 2. Blocking defect: the deployment SLEEP writer is undefined

The proposal's scientific endpoint depends on the three deployment writes in
`P1/U1`, yet Sections 7–10 specify only nursery admission and childhood fits.
Section 11 specifies when deployment writes happen, not what they write.
Missing exact bytes include:

- the prospective CompilerGym support predicate for a `THINK_TO_ACT` row;
- whether a new-best action, a verified recovery, an informative failed action,
  or an entire thought/action pathway is eligible;
- the deployment-specific support rule for `DREAM_STATE` and its post-reset
  continuation;
- maximum targets of each type per program and per 16-program era;
- the deterministic selection key when more rows qualify than fit;
- whether deployment targets receive four ordinary-state exposures or another
  scaffold distribution;
- how much childhood corpus, earlier deployment corpus, and anchor/rehearsal
  corpus survives each clean-base rebuild; and
- exact cut-16/cut-32/cut-48 position, labeled-token, attended-token, and
  optimizer-step proofs.

This cannot be deferred to implementation. Different answers define different
learning algorithms and different causal treatments. In particular, “winner
only,” “recovery pathway,” and “first supported action” can change exploration
in opposite directions; prior exploratory evidence already observed this
failure surface.

### The current childhood cap cannot simply be extended

Childhood permits 24 targets, four exposures each, at most 256 target tokens:

```text
childhood: 24*4 = 96 positions; 24*4*256 = 24,576 labeled tokens
anchors:   32 positions;                 8,192 labeled tokens
total:    128 positions;                32,768 labeled tokens
```

Thus the 128-position ceiling is already exhausted before the first deployment
row if childhood rows and all anchors are retained. Even ignoring positions,
if deployment allowed one `THINK_TO_ACT` plus one `DREAM_STATE` per program,
the labeled-token maxima would be:

```text
cut 16: childhood 24,576 + deployment 32*4*256 + anchors 8,192 = 65,536
cut 32: childhood 24,576 + deployment 64*4*256 + anchors 8,192 = 98,304
cut 48: childhood 24,576 + deployment 96*4*256 + anchors 8,192 = 131,072
```

Cut 16 would still require 256 positions, twice the position ceiling. Even one
target per program exceeds 128 positions at cut 16. Therefore no implicit
reading of “cumulative clean-base rebuild” solves the problem.

### Required repair

Bind a deterministic bounded replay policy as architecture, not trainer
convenience. At minimum it must specify fixed slot/token quotas for:

1. childhood disposition rows;
2. recent deployment rows;
3. older deployment rows or distilled/replayed rows; and
4. treatment-neutral dialect/retention anchors.

Every cut must rebuild from the frozen base and the selected bounded corpus,
with a symbolic worst-case proof under all caps. Selection may use only frozen
public provenance/support/ledger-order keys, never arm identity, attribution
tag, later probe value, or downstream success. If old rows are evicted, report
backward retention; if childhood rows are reduced, retain a fixed quota and
measure whether parenting survives. A model-generated sleep curator would be a
new intelligence and is outside this deterministic SLEEP proposal.

## 3. Blocking defect: missing-target padding is not executable

The plan says the fixed anchor/rehearsal packet is capped at 32 positions and
8,192 target tokens, then says that when fewer treatment targets exist “only
the common presealed rehearsal packet fills the missing position/update
budget.” Those claims cannot both guarantee matched P/U optimizer exposure.
With zero admitted treatment rows, 96 of 128 positions are missing, but the
packet contributes only 32 positions unless it is repeated beyond its stated
cap. Variable repeats would also make anchor dose treatment-dependent.

Repair by deciding the estimand and binding it:

- If optimizer work must be matched, preseal a sufficiently large,
  target-blind rehearsal reservoir with response-length buckets and substitute
  one rehearsal position/target token for every unfilled treatment slot. Bind
  exact per-fit positions, labeled tokens, ordering, and loss weights.
- If admitted-target yield is intentionally allowed to change optimizer work
  as a mediator of parenting, remove the dose-matched language, do not call U
  optimizer-matched, and add a terminal matched-work diagnostic.

The first option is more consistent with Sections 2 and 6. Padding rows must
be reported as padding, never as supported child experience.

## 4. Residual exact-byte contradictions

### 4.1 Opening triad still calls training deterministic

Section 1 still defines SLEEP as a “deterministic selection/render/train/commit
boundary.” Section 9 correctly weakens this to deterministic compiler/gates
around a seeded optimization with measured reproducibility tolerance. Replace
the Section 1 phrase with the Section 9 contract. Otherwise the same document
both promises bitwise deterministic training and admits only tolerance-bounded
reproducibility.

### 4.2 Row criterion still names an independent semantic firewall

Section 7.6 says every parent/restatement/target passes “lexical plus
independent semantic” firewalls. The final Section 7 paragraph says no semantic
reviewer makes per-row decisions and the live firewall is deterministic. Drop
“independent semantic” from the row predicate or define it as a pre-science
policy audit rather than a live admission edge. The latter paragraph is the
architecture that preserves SLEEP as zero-inference writing.

### 4.3 Deployment support language points back to nursery families

Section 8 requires a DREAM continuation to pass “the same absolute task-family
support/non-inferiority guard.” That is executable for Codebreaker/RuleShift
but not yet for CompilerGym. Once the deployment writer is specified, name the
deployment guard separately rather than implying the nursery predicate applies
unchanged.

## 5. Arithmetic and resource reaudit

### Fits

The repaired 18-fit canary and headline totals are correct:

```text
canary = 3 LR fits + 1 duplicate + 2 technical roots*4 cells
         + 2 expansion roots*3 cells = 18

fits/root = 2*J + 2*K = 2*3 + 2*3 = 12
N20 total = 18 + 12*(2 development + 4 pilot + 20) = 330
N32 total = 18 + 12*(2 development + 4 pilot + 32) = 474
```

### Calls and output tokens

The new table sums exactly:

```text
calls  = 576 + 24 + 24 + 12 + 2,880 + 15 + 1,280 = 4,811
tokens = 73,728 + 4,608 + 9,216 + 3,072
         + 491,520 + 11,520 + 163,840 = 757,504

26 roots: 4,811*26 = 125,086; 757,504*26 = 19,695,104
38 roots: 4,811*38 = 182,818; 757,504*38 = 28,785,152
```

The P neutral shadow is now explicitly inside the 12-call/1,536-token P source
aggregate, and unused U diagnostic capacity is burned, not generated. Before
implementation, split that aggregate into exact pre-review, corrected/U-self,
and shadow turn/token limits so “same remaining budget” is testable rather than
aspirational. Development saturation/policy-audit costs are correctly labeled
outside scientific root cost, but they still need a separate maximum before a
calendar/lease closure can be called hard.

### DREAM

The fixed 24 nursery and 15 deployment DREAM opportunities reproduce the table.
Early requests replace scheduled calls; there is no retry; a failed dream does
not increase cost. The emergency reset is deterministic and nontrainable. This
closes the v1 unbounded-DREAM defect.

## 6. Workflow and scope reaudit

What now passes:

- all 15 context files exist and are unique;
- v1 audit is included;
- the workflow has the required advocate, two fresh independent
  interpretations, critique, and consensus stages;
- the runner will snapshot and continuously reverify source hashes after
  initialization;
- scope now permits only separately exact-authorized proposal deliberation
  provider calls before later ratification while continuing to forbid all
  scientific runtime/model/GPU access; and
- implementation remains gated behind later consensus ratification, static
  validation, fresh review, and separate pre-GPU authorization.

One formal blocker remains: there is no initialized source-binding state or
manifest. The workflow SHA `9abaa...` commits to paths and role configuration,
not the contents of the directive and 15 contexts. If export approval cites
only that SHA, a source could change before initialization without changing
the approved workflow hash. Generate a canonical source-binding manifest (or
initialize locally and expose its exact `source_bindings` aggregate), bind it
in the approval evidence, and fail closed on any later mismatch.

Because this reaudit identifies unresolved architecture bytes, either repair
them directly and include the new plan/scope hashes, or add this v2 audit to
the workflow. Any workflow/context edit invalidates SHA `9abaa...`; recompute
the exact workflow plus source-bundle authorization after the final edit.

## 7. Final disposition

The repaired candidate is now faithful, causally coherent, and arithmetically
auditable at the inference/root level. It is **not yet executable as the
headline experiment** because the deployment LoRA write—the mechanism under
test—has no exact admission/replay/cap specification. Close that writer and
the padding/source-binding contradictions before external deliberation. After
that, the bundle is suitable for the five-role architecture workflow, not for
implementation or GPU use.

