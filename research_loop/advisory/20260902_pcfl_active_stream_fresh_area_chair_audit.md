# PCFL-Active-Stream fresh area-chair audit

Date: 2026-09-02

Status: **read-only advisory only**. This document provides no implementation,
deliberation, ratification, model/provider/network, CPU/GPU execution, training,
confirmation, publication, promotion, scientific-claim, or successor authority.
It does not modify, approve, or authorize the proposal bundle.

## Verdict

**REWORK**

I audited the current bytes read-only. No deliberation state or downstream
artifacts exist, and no model/network/GPU work was run.

## Fatal scientific blockers, in priority order

### 1. The pre-native target contract is impossible

`experiment_contract.md` section 4 says every checkpoint has `OLD_D4` whose
last support is more than `L_native` tokens old, while section 5 includes a
checkpoint at `0.75 L_native` (`experiment_contract.md:83-91,113-120`; repeated
in `statistics_and_claim_contract.md:42-47`). No event in a 0.75L prefix can be
more than 1L old.

Minimal repair: apply the greater-than-`L_native` age rule only to post-native
checkpoints and define a separate pre-native reference cohort with no
old-retention eligibility. Update PAS_T01 and target counts accordingly.

### 2. The experiment does not identify model-owned reconsolidation rather than action-conditioned KV/witness replay

The mediation delta may directly include deterministic witness atoms
(`mediation_contract.md` section 3, lines 88-92), and SELF memory explicitly
contains those atoms (`compiler_memory_contract.md` section 5, lines 92-96).
P1 contrasts AUTH against TWIN but never SELF reconsolidation against raw
`(A,O)`, witness-only, or mechanical deltas
(`statistics_and_claim_contract.md` section 3/P1). Confirmation mediation is
only attached to SELF (`baseline_and_resource_manifest.md:47-49`). Thus the
entire chain can be realized by probe selection plus keyed storage/retrieval;
model-owned Dream-2 need not contribute.

This is especially acute because the world consists of independent
label-to-transform/predicate/precondition mappings
(`experiment_contract.md:28-44`), the reader returns one local relation, and
the frozen resolver composes four such reads. The proposal's own KV falsifier
is likely to fire by construction.

Minimal repair: either:

- narrow the headline to “action-conditioned public-event memory” and remove
  causal credit for model-owned reconsolidation; or
- add, on the same branch event and common prior, raw-event, action-only,
  witness-only/MECH, and SELF-delta conditions; add an
  outcome-drop/twin-outcome intervention holding probe identity fixed; cut
  model-owned SELF semantic records while holding witness
  atoms/reader/resources fixed; and require directional incremental
  later-action value from the model-owned portion. If the intended claim is
  explicitly beyond KV, add a primary target whose decisive relation requires
  integration across multiple public events and is not a direct witnessed
  keyed atom.

### 3. The AUTH/TWIN/NULL fork and corresponding independent unit are operationally ambiguous

`mediation_contract.md:41-48` says every root contains one fork but that
assignment is randomized “within root” over three treatments using a Latin
rotation. Other passages assume all branch deltas exist, and the statistics
treat branches as nested paired measurements
(`statistics_and_claim_contract.md:7-10,69-84`). If one treatment is observed
per root, 24 roots yield roughly eight observations per treatment and the
paired power calculation is invalid. If all three clones run, “assignment” and
Latin rotation need to refer to opaque labels/execution order, not treatment
inclusion.

Minimal repair: state exact clone count per twin side/checkpoint, install each
treatment exactly once if the design is within-root, randomize opaque branch
labels and execution order, specify common versus independent RNG namespaces,
define the root-level MED summary across sides/checkpoints/targets, and count
every branch/failure in the resource manifest. Otherwise rederive an
unpaired/clustered estimator and sample size.

### 4. The 24-root study is not powered for its declared four-family intersection

The sole calculation (`statistics_and_claim_contract.md:23-40`) powers a paired
superiority difference of 0.15 at SD 0.22. It does not power:

- three separate acquisition lower bounds (`statistics_and_claim_contract.md:86-95`);
- retention noninferiority at margin -0.05 (`statistics_and_claim_contract.md:97-107`);
- the full multiplicity family; or
- the DEV-selectable superiority-versus-resource-frontier alternative
  (`statistics_and_claim_contract.md:109-128`).

Using its own critical value and SD, retention at true difference 0 requires
approximately
`ceil(((2.24+0.84)*0.22/0.05)^2) = 184` roots, not 24. The exact
max-T/closed-testing method is deferred until later, so 2.24 is not yet
justified for all required intervals. A point SD estimate from eight heavily
tuned DEV roots also cannot certify a true SD ceiling without an uncertainty
bound. P2/P3 additionally require cross-snapshot evaluation cells not
explicitly counted in Stage C.

Minimal repair: freeze an estimand-by-estimand power table using the exact root
summary, covariance/multiplicity procedure, finite-sample critical values,
expected effect or NI distance, and a conservative upper confidence bound for
each contrast SD. Prospectively increase roots or label 24 as
calibration/underpowered evidence. Add all lagged/current snapshot cells to the
roster and cost ledger.

### 5. Visibility/taint is still internally contradictory and does not dispose the prior full-component concern

The canonical `change.json` matrix combines assigner+actor and
resetter+compiler (`change.json:74-76`). It then forbids fork
assignment/capacity information to the combined reset/compiler stage
(`change.json:105-112,159-166`), while the resetter must inspect the
assigned-capability object registry to prove removal
(`visibility_taint_reset_contract.md:47,77-97`). The prose also says
`EVAL_GOAL` can never become a retrieval key or prompt hint
(`visibility_taint_reset_contract.md:23-26`), while the target reader
necessarily accepts model query bytes derived from that goal
(`visibility_taint_reset_contract.md:44,49-50`). Finally, no trusted DEV
selector is modeled even though DEV results/resources select AS-EXT, prompts,
caps, the variance disposition, and Stage C
(`baseline_and_resource_manifest.md:64-76,111-116`).

Minimal repair: make the schema matrix component-level; split assigner from
actor and resetter from delta compiler; allow the resetter read-only
assignment-registry metadata but no semantic content; permit ephemeral
evaluation-goal-derived queries only in sterile target-time cognition while
forbidding persistence/upstream flow; and add a trusted DEV gate/selector with
exact allowed metrics and one-way frozen outputs.

## Fatal workflow and feasibility blockers

### 6. The ICLR September 25 path is not credible as written

Stage A allows seven days, Stage B four, and Stage C ten
(`baseline_and_resource_manifest.md:89-94`): 21 days after implementation
exists, excluding deliberation, human ratification, implementation, Stage-A
review, independent evidence review, failure recovery, and paper writing. From
September 2 to September 25 there are 23 calendar days, and the abstract is
September 18. The bound compute audit explicitly said powered confirmation was
not credible in the same two weeks
(`research_loop/advisory/20260902_pcfl_compute_feasibility.md:9-15`). Current
480-H100-hour/6-TB values are unmeasured planning caps; exact model-call/cost
conversion is deferred (`baseline_and_resource_manifest.md:86-99`).

Minimal repair: remove “submission-feasible” and make ICLR's honest target
Stage A/B or a design/DEV paper, with confirmation for a later venue; or bind an
evidence-backed dated critical path including completed implementation date,
measured per-root branch costs, available fleet/concurrency, storage/transfer,
reviews, and writing slack.

### 7. The proposal forbids the very model calls required by its deliberation workflow

`scope_proposal.json:7-8` requests model-based independent interpretations, but
`scope_proposal.json:12,18` blanket-forbids model/provider/network calls.
`change.json:195-198` repeats that prohibition before approval, while the
workflow configures Codex executors for every deliberation role
(`pcfl_active_stream_paper_target_v1.deliberation.json:41-106`). Human approval
is supposed to occur only after those roles, creating a deadlock.

Minimal repair: explicitly permit only the configured non-scientific
architecture-deliberation calls through `human_required`, while continuing to
forbid implementation, scientific/model execution, GPU, training, and claims.

### 8. Acceptance-test timing is semantically impossible despite structural schema validity

PAS_T01/T07 require generated construct/mutation evidence “before
implementation,” although that evidence needs an implementation. PAS_T04/T05/
T08 are labeled before any GPU/model run even though they require DEV
model/compiler/baseline outputs and measured DEV projections
(`change.json:179-186`; `stage_gate_and_test_manifest.md:108-121`). Meanwhile
exact compiler prompts/DSL are intentionally frozen during later DEV
(`compiler_memory_contract.md:18-22`).

Minimal repair: replace the coarse timing labels with explicit gates such as
`specified_before_implementation`, `executed_before_stage_b`,
`executed_before_stage_c`, and `before_claim`; split structural preflight from
DEV empirical checks.

## Nonblocking improvements

- Keep AS-MECH labeled an alternative/control unless a true ceiling property
  is proved.
- Add a fixed-experience or cross-system experience-swap sentinel to decompose
  experience acquisition from representation/use; the randomized pulse is
  otherwise only within SELF.
- Add a generator-nuisance sentinel or keep every conclusion explicitly
  confined to the one frozen generator/model.
- If the work is marketed as a benchmark, bind release of the deterministic
  generator, certifier, scorer, manifests, and harness.

## What passes

- Claim boundaries are substantially improved: finite, synthetic, text-first,
  no compression/unbounded/generic-SOTA/learned-controller claim, and LoRA is
  correctly deferred.
- Baseline breadth and native-interface/resource accounting are directionally
  strong.
- Failure inclusion, root-as-independent-unit language, plateau equivalence
  logic, reset/canary intent, and nonautomatic stage transitions are good.
- Human provenance is now clean: `human_directive.txt` contains exact owner
  quotes, while broad permission is not inferred as ratification.
- Structural validation passes for both `change.json` and the workflow; all
  `change.json` context hashes match current bytes; workflow and change context
  sets match exactly; no intake/deliberation state was initialized.

## Exact audited hashes

- `change.json`:
  `eccb3c0f20401c9a35e048fef6263f7efca235b49ad0b02ef97d5425543aa9b7`
- `bundle_manifest.json`:
  `450f91b48d484a11b8d593bc2f659e8a2b2e84edd91992fd2f641ab4331df832`
- `research_loop/workflows/pcfl_active_stream_paper_target_v1.deliberation.json`:
  `9a793b4b1ecb32102d50d400dc7b071f9e191e9b59906ab11c463c1a184ef887`
