# PCFL-Active-Stream formal rework round-1 audit

Date: 2026-09-02  
Scope: fresh, read-only audit of only the two blockers recorded in
`invalidated_formal_rework_round1/critique.json`, plus the requested collateral
invariants. This memo neither ratifies the proposal nor grants execution,
scientific, GPU, or claim authority.

## Verdict: APPROVE for the two rework blockers

The current proposal resolves both specified formal defects. This is an
approval of the repair only, not evidence that the prospective gates have been
implemented or passed.

### 1. Mandatory, executable A2/T12 treatment-policy freeze

**Resolved.** The former underspecification is now mandatory and sufficiently
executable as a future hash-bound contract:

- A2 names and requires the exact `SELF_AGGREGATION_V1`
  multi-sample-to-canonical-SELF reducer/admission policy, including duplicate,
  disagreement, malformed, abstained, failed, capacity, and
  no-correctness-selection behavior. It requires fixed treatment-policy
  assertions and golden bytes for disagreement/admission.
- It separately requires `ORDINARY_SLEEP_CADENCE_V1` for every Dream-1,
  Dream-2, block, and snapshot schedule/trigger; the proposal additionally
  forbids target, truth, result, model-output, contradiction, failure, latency,
  and DEV-dependent triggers.
- It requires checkpoint-specific `SELF_LIFECYCLE_READER_V1`: readable status,
  active version, fixed slots, tombstone/padding, candidate and return policy
  for provisional, superseded, contradicted, abstained, malformed, and failed
  records. Thus status and omission cannot remain an undeclared reader or
  candidate-count channel.
- A1/A2 and T12 require all-mixture/disagreement, cadence/snapshot,
  lifecycle-transition, and constant-shape-return golden/mutation fixtures
  under independent target, truth, scorer, comparator, downstream-result, and
  DEV-result mutations. T12 expressly turns a missing policy byte, fixture,
  review, or human model-call authority into `NOT_RUN`.
- Before B0, a fresh independent reviewer must reproduce the frozen hashes and
  verify blindness, no deterministic correctness selection, reducer handling,
  cadence completeness, lifecycle/constant-shape behavior, and all required
  fixtures; Rohin Ghosh must then explicitly authorize the reviewed hashes and
  exact model/provider call, token, cost, root, and stage scope. Any cognition
  change restarts DEV and requires new review and authorization.

The detail is consistent in `change.json` (including PAS_T12),
`stage_gate_and_test_manifest.md`, `compiler_memory_contract.md`,
`experiment_contract.md`, `statistics_and_claim_contract.md`,
`baseline_and_resource_manifest.md`, and the visibility contract. Because the
proposal remains unimplemented, these are prospective executable acceptance
requirements, not completed implementation evidence; that distinction is
maintained correctly.

### 2. One Stage-C Monte Carlo gate, with no marginal simulation gate

**Resolved.** The current formal contracts consistently state one and only one
prospective Monte Carlo gate, in every admissible scenario with at least
100,000 frozen replicates:

```
one-sided 99% LCB(all-four joint rejection) > .80
and
one-sided 99% UCB(global-null rejection size) <= .0525
```

`statistics_and_claim_contract.md` explicitly calls this the sole prospective
Monte Carlo go/no-go rule and explicitly excludes a per-endpoint or simulated
marginal lower-bound gate. `change.json` PAS_T06/T08/T12, the stage-gate
manifest, the baseline/resource manifest, and the concern disposition repeat
the same joint/global-null rule and identify `.951579` marginal power and
`.806317` arbitrary-dependence joint lower bound as analytical planning
arithmetic only. I found no orphan marginal simulation threshold or conflicting
Stage-C simulation criterion in the current proposal contracts.

The four simultaneous SD-UCB checks and deterministic distribution diagnostic
remain separate preconditions, not additional Monte Carlo gates. Failure
correctly yields calibration-only/stopped status rather than threshold repair.

## Collateral invariant check

No collateral departure was found from the requested frozen boundaries:

- **Inference/roster:** exactly four failure-inclusive root summaries
  `P1_w`--`P4_w`, four one-sided alpha-.05 component tests, and their complete
  intersection as the 26-root global IUT; 908 target-evaluation rows/root and
  23,608 rows total remain explicit.
- **Claim boundary:** the result remains a narrow finite, synthetic,
  action-conditioned text-memory proposal; DEV is nonconfirmatory and A4
  efficacy / Stage-D LoRA do not gate C1--C3.
- **Authority:** status remains proposal-only and `human_required`; no current
  artifact authorizes implementation, CPU/GPU science, model execution, DEV,
  confirmation, publication, or claim release. The required later independent
  review and exact human authorization are preserved.
- **Immutable context:** `AGENTS.md`, `00_THESIS.md`, the owner directive, the
  IDEAS snapshot, source-drift incident, archive critique, and all 37
  SHA-bound entries referenced by `change.json` match their recorded hashes.
  All 27 entries in the current bundle manifest also match.

## Hashes audited

- Bundle manifest: `2208cc57c000257f6f1f517c21a350ae153e5d2d108de0d4165b781dafe2f025`
- Change proposal: `50bd326ed57031b40715649da16bea3e1b28ac061181935ae564f72b9ba06ae2`
- Stage-gate/test manifest: `829003174f5d2512b913e386124bb0c29b3158daf514add93b5fa05f25c65fac`
- Statistics/claim contract: `1e5784f906eb0c4648f4e23df7536cebeb81a5b2090f8a329bc0f9279bcc439b`
- Baseline/resource manifest: `55e0d557abb804885c5589b332e1ef5db6f749fcdced254b7d0d1b15d617d143`
- Archived round-1 critique: `0791d6b41026b5ec1870c3caca8cb58884b3fd897f8f5cafc3a32d02bcc15552`
- Bound workflow: `0bf81b45e6380841a4dbfccedbc2bff874fd1ef06ecd7cd6454ae7a258351fc3`

No proposal, workflow, deliberation state, implementation, model/science, or
GPU action was changed or run for this audit.
