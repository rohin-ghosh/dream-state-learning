# PCFL-Active-Stream fresh area-chair re-audit 2

Date: 2026-09-02

Status: **read-only advisory only**. This review does not edit or ratify the
proposal, initialize deliberation, authorize implementation or CPU/GPU/model
science, release a claim, or create successor authority. Bare proposal
filenames below are rooted at
`research_loop/changes/chg_20260902_pcfl_active_stream_paper_target_v1/`.

## Verdict

**REWORK**

The repaired design now resolves the previously central construct, comparator,
retention, power, roster, MECH-scope, deadline, and authority issues. It is not
yet safe to send to formal deliberation, however, because the exact post-fork
compiler RNG violates the proposal's own unmount/taint boundary and confounds a
claim-bearing P1 intervention. The A4 and LoRA acceptance entries also contradict
the declared four-endpoint text-only decision boundary.

## Integrity and workflow verification

- I independently recomputed every hash. All 16 entries in
  `bundle_manifest.json.files` match their current bytes. The manifest itself is
  SHA-256
  `2450466ff1239dce31fb423f040de1912913bc4ab65a15f59342e1aec8896bc1`.
- All 32 `change.json.context_files` hashes match their current source bytes.
  The workflow's directive plus context list is exactly the same 32-path set.
- The current proposal hash is
  `562218efe4c5cb149f1aec671e01b2682acd32796fc4bf658e135759bbe8a507`;
  the workflow hash is
  `6da496d00a86a002d150567422805a36e2a5f0183005cd357651590f6e538bca`.
  The repository's read-only workflow/stage validator accepts this exact
  workflow and adopted advocate artifact.
- No deliberation runner state, intake state, interpretation, critique, or
  consensus exists for this change. This agrees with the proposal-only authority
  record (`bundle_manifest.json:72-79`) and the scope that permits only the
  configured non-scientific deliberation calls through `human_required` while
  forbidding ratification, implementation, and science
  (`scope_proposal.json:4-20`). Validation did not create state.

## Blocking issues

### 1. The post-fork compiler RNG is an assignment descendant and the paired outcome contrast does not have a common seed

The causal design requires the assigned AUTH/TWIN/NULL object and every
assignment descendant to disappear before Dream-2. The delta compiler must not
read assigned fork metadata (`visibility_taint_reset_contract.md:25-33,54-56`),
and the unmount invariant expressly forbids an assignment label, hash, or seed
from surviving (`visibility_taint_reset_contract.md:100-126`).

The exact compiler RNG rule nevertheless hashes `branch_label` into every
post-fork compiler sample:

```text
SHA256(protocol_hash || root_id || side || checkpoint ||
       branch_label || lane || "COMPILER" || sample_index)
```

(`mediation_contract.md:81-85`). `branch_label` is the randomized opaque
`B0/B1/B2` exploration-assignment identity defined immediately above
(`mediation_contract.md:57-71`). It therefore survives unmount as a
cognition-affecting seed even if it is not printed in the prompt. That directly
contradicts both the visibility matrix and the claim that later differences are
descended only from the public `(A_z,O_z)` event.

The same formula also conflicts with the matched-action outcome intervention.
`SELF-DELTA` and `SELF-TWIN-OUTCOME` are distinct registered lanes
(`baseline_and_resource_manifest.md:63-66`), so including `lane` gives them
different compiler draws. Yet the intervention requires the seed, as well as
all non-outcome Dream-2 inputs and their order, to be common
(`mediation_contract.md:157-165`). Consequently `r_5,w` can reflect model
sampling rather than the changed public outcome packet, defeating its stated
outcome-necessity interpretation (`mediation_contract.md:300-311`).

Required repair: define a pre-fork, assignment-independent paired compiler RNG
key that excludes opaque branch/treatment identity and excludes the intervention
lane for every paired stochastic comparison. Bind exact seed-equality and
seed-independence assertions at A1/A2. If independent compiler draws are desired
for any descriptive lane, keep them out of P1 causal contrasts and label them
accordingly. Re-run the roster/power specification check after the RNG repair;
do not leave this to implementation interpretation.

### 2. A4 is simultaneously a representation-dependent target, a secondary sentinel, and a mandatory pre-claim success gate

The proposal summary says every target succeeds only by a world action,
independent of memory representation (`change.json:6`). The six confirmation
arms all receive four A4 target rows per side, and those rows are part of the 768
ordinary rows and hence the exact 908-row roster
(`baseline_and_resource_manifest.md:46-54,76-85`). But the A4 contract defines
target success as requiring a **model-owned revision**, in addition to action and
recovery (`experiment_contract.md:148-153`). AS-NONE, AS-CTX, AS-RAG, AS-EXT,
and AS-MECH cannot satisfy that internal-representation condition by definition.
This is not the world/action-only scoring used for D4 and integrative targets
(`experiment_contract.md:117-146`; `statistics_and_claim_contract.md:136-142`).

The inferential status is also contradictory. A4 is declared secondary/sentinel
(`statistics_and_claim_contract.md:260-276`), and Stage C says a positive text
result requires **only** the P1--P4 intersection, with no other confirmatory sign
gate (`statistics_and_claim_contract.md:26-31`;
`stage_gate_and_test_manifest.md:173-185`). Nevertheless
`PAS_T09_A4_REVISION_SENTINEL` requires successful revision/recovery and is
globally marked `required_before: scientific_claim` (`change.json:465-471`;
`stage_gate_and_test_manifest.md:220`). Under the literal acceptance registry,
A4 is a fifth unpowered efficacy gate; under the prose, T09 is not binding. Both
cannot be true.

Required repair: score each A4 target's primary `V` solely from its legal
world/action trajectory and terminal return for every arm. Record contradiction
detection, revision status, and unrelated-memory preservation as separate
mechanism diagnostics. Make T09 a completeness/leakage/failure-inclusion check
whose efficacy result is descriptive, or explicitly restrict it to a separately
powered A4-specific claim. It must not gate C1--C3 unless A4 is folded into the
four primary summaries and the complete decision is repowered. Preserve the
908-row arithmetic after separating action value from mechanism labels.

### 3. The optional post-text LoRA sentinel is globally marked as a prerequisite for the text scientific claim

The design says no LoRA work occurs until the powered text confirmation and its
independent review establish causal text value; Stage D is later, separately
authorized, DEV-only, and cannot add a Paper-1 parametric claim
(`experiment_contract.md:260-290`;
`stage_gate_and_test_manifest.md:192-206`). The prose acceptance table correctly
narrows T10 to "any LoRA claim" (`stage_gate_and_test_manifest.md:221`).

In the authoritative `change.json` acceptance object, however, T10's setup is
post-text but its stage is the generic `required_before: scientific_claim`
(`change.json:474-480`). Read literally, the optional, separately authorized
future sentinel must run before even the text C1--C3 claim; if its new authority
is not granted, the already completed text result cannot clear its own acceptance
registry. This conflicts with the nonautomatic successor boundary and with the
claim ladder that makes no parametric Paper-1 claim.

Required repair: make the machine-readable acceptance semantics unambiguous.
T10 must be nonapplicable to C1--C3 and mandatory only before a future LoRA
claim, ideally in the future separately ratified LoRA proposal. If it remains in
this proposal because of the coarse schema enum, its expected/pass condition and
an exact claim-to-test map must state that a not-requested Stage D does not block
the text claim. Do not rely on prose to silently override a generic
`required_before` field.

## Findings that pass this fresh audit

1. **Representation-neutral D4/integrative construct.** Integrative success is
   defined by latent world state, a legal executed trajectory, the action cap,
   and terminal return, with no SELF record or backend in correctness. The
   target has a certified read-dependent DAG; recurrent KV, raw, linked,
   rolling, MECH, or SELF may honestly solve it
   (`experiment_contract.md:117-146`). A0 stops only on direct, independent, or
   nonadaptive sufficiency (`stage_gate_and_test_manifest.md:50-73`). This part
   is scientifically coherent; blocker 2 is limited to A4.
2. **Honest competitors and SELF's narrow earned claim.** The common-history
   sentinel includes raw RAG, equal-atom nonadaptive and recurrent KV, MECH,
   linked, rolling, generic SELF, and a separately labeled class-informed
   ceiling (`experiment_contract.md:228-248`). P1's `r_1`--`r_6` require SELF to
   beat raw/action-only/witness controls, lose value under outcome/semantic
   interventions, and beat the root-wise strongest non-SELF common-history
   condition (`mediation_contract.md:292-337`). Offline work may differ but all
   preprocessing, calls, bytes, latency, storage, indexing, candidate work, and
   online work are charged and reported; no fixed-total-compute or efficiency
   claim is made (`compiler_memory_contract.md:112-131`;
   `baseline_and_resource_manifest.md:216-238`).
3. **A2 and human authorization.** The gate now freezes all cognition, model,
   parser, reader, candidate, cut, budget, failure, diagnostic, and joint-power
   bytes before B0; a fresh independent hash review and Rohin Ghosh's exact
   model/provider/token/cost/root/stage authorization are both required. Missing
   authority is `NOT_RUN`, and any cognition change restarts DEV
   (`stage_gate_and_test_manifest.md:93-116`). The current proposal grants none
   of that execution authority.
4. **Acquisition and retention.** P2 is the root-wise minimum of all three
   current-minus-lagged NEW contrasts. P3 uses the same preassigned 6L OLD rows
   at the first acquisition snapshot and 6L, with
   `min(A-tau, L-tau, L-A+.05)`; acquisition failure, endpoint failure, and
   `0 -> 0` cannot earn retention (`statistics_and_claim_contract.md:186-226`).
5. **Four-endpoint IUT and prospective power.** The IUT logic is correct: each
   P1--P4 component is tested one-sided at `.05`, and the complete intersection
   has global size at most `.05` provided each component test has its stated
   size (`statistics_and_claim_contract.md:26-38,97-102`). I independently
   recomputed `t_(.95,25)=1.708141`, marginal noncentral-t power `.951579`, the
   arbitrary-endpoint-dependence union lower bound `.806317`, and independent
   joint power `.819936`. At `n=25`, the corresponding lower bound is `.777372`,
   so 26 is the smallest integer meeting both registered `.80` calculations.
6. **Variance and simulation gates.** The simultaneous normal-theory SD formula
   is numerically correct:
   `chi2_.0125,7=1.334270`, multiplier `2.290483`, and the observed eight-root
   requirement `s<=.130977`. The exact-version diagnostic, at-least-100,000-run
   nested scenario grid, joint-power lower bound, null-size upper bound, and
   calibration-only failure disposition are all prospectively located before
   Stage C (`statistics_and_claim_contract.md:58-95`). The proposal correctly
   acknowledges that eight-root diagnostics do not establish normality.
7. **P1 chain completeness, apart from blocker 1.** Six cumulative products
   force each earlier failed link to zero all later credit; six compiler/
   intervention contrasts and three directional binding scores join them in the
   root minimum, with no separate claim-bearing point-sign gate
   (`mediation_contract.md:217-241,280-337`). This supports the deliberately
   narrow randomized causal-cascade wording, not a natural indirect effect.
8. **MECH gate scope.** The `.90` Stage-B MECH threshold is explicitly limited
   to deterministic extraction/read fidelity over every assigned fully
   supported ordinary witness atom, failures included; it does not apply to
   ordinary or common-history integrative action value
   (`stage_gate_and_test_manifest.md:133-140`). MECH remains an alternative, not
   a ceiling without a separate upper-bound proof.
9. **Exact roster.** The arithmetic independently reconciles:
   `768 ordinary + 36 lagged NEW + 12 first-acquisition OLD + 36 intact clone
   integrative + 24 additional 3L lanes + 32 common-history = 908` rows/root;
   `26 * 908 = 23,608`. The 18 exploration clones, same-probe outcome actions,
   and six binding diagnostic actions are nested operations, not extra roots or
   target rows (`baseline_and_resource_manifest.md:59-88`).
10. **September 25 and authority honesty.** The September evidence target is
    only the deterministic construct/protocol plus failure-inclusive eight-root
    DEV labeled nonconfirmatory. P1--P4 population, superiority,
    noninferiority, plateau, and continual-learning claims are expressly barred;
    full confirmation is after September 25 under new exact authority
    (`baseline_and_resource_manifest.md:153-182`;
    `stage_gate_and_test_manifest.md:173-190`).

## Re-review threshold

A new review can be narrow. It should verify exact repaired bytes for (1) the
assignment-independent paired compiler RNG and its A1/A2 mutation tests, (2) the
split between A4 world/action value and descriptive mechanism diagnostics, and
(3) claim-specific T09/T10 acceptance applicability. It should then recompute
all source/bundle hashes and confirm that the 908-row roster and P1--P4 power
objects did not change unintentionally. Until those contradictions are removed,
formal deliberation should not be initialized.
