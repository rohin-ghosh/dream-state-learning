# PCFL-Active-Stream final audit

Date: 2026-09-02

Status: **read-only advisory only**. This audit does not ratify the proposal,
initialize or run deliberation, authorize implementation or any scientific,
model, CPU, or GPU execution, release a claim, or create successor authority.

## Verdict

**APPROVE** for the configured non-authorizing architecture-deliberation path,
subject to the existing human-required boundary. The three exact repair targets
from re-audit 2 are now coherent and machine-readable, and the repair preserved
the frozen primary design, visibility boundary, and authority limits.

## Integrity verification

I independently recomputed every current recorded hash. All **18/18**
`bundle_manifest.json.files` entries and all **34/34**
`change.json.context_files` entries match their current bytes. Current SHA-256
digests are:

- bundle manifest: `611982e10a59df48d0b5d19922ec1c213f64c3402b657bfc0cc1361a59c278c1`
- change proposal: `593c45668322cfef6c48c2bdbb145c25f4756434b69fc05c846906ecfca5d8d2`
- deliberation workflow: `b717ccaa3ee79a458c07ab37482ab38725c7a3b731faba3a6733a6fab3f1b23a`
- claim-to-test map: `9f008afcee87abf04341e3572a28e5caecefbf39ac483e028fc0f3d0c1e331c9`

The bundle remains `proposal_only_unratified`; it records no deliberation run,
interpretations, critique, consensus, human ratification, or execution
authorization (`research_loop/changes/chg_20260902_pcfl_active_stream_paper_target_v1/bundle_manifest.json:5,80-87`). The configured workflow is an
architecture-deliberation workflow only
(`research_loop/workflows/pcfl_active_stream_paper_target_v1.deliberation.json:1-7`),
and the requested scope expressly forbids implementation, execution, science,
and ratification (`research_loop/changes/chg_20260902_pcfl_active_stream_paper_target_v1/scope_proposal.json:4-20`). No run or intake state was present at the
configured paths during this audit.

## Final-gate findings

1. **P1 compiler CRN — pass.** `P1_COMPILER_SEED` contains only the protocol,
   fixed version tag, root, recipient/evaluation side, checkpoint, presealed
   pair group, and sample index; its pair group is explicitly neither lane,
   method, branch, treatment, nor opaque label
   (`research_loop/changes/chg_20260902_pcfl_active_stream_paper_target_v1/mediation_contract.md:86-110`). AUTH/TWIN/NULL, intact SELF/twin-outcome,
   and stochastic common-history P1 comparisons share draws index-by-index;
   cut/sham makes no compiler draw. Independent descriptive draws are separately
   namespaced, assignment-independent, labeled descriptive, and barred from P1
   (`mediation_contract.md:112-120`). The contract binds treatment/label/lane
   mutations and index-wise equality at A1, then freezes assertion code,
   vectors, RNG implementation, pair groups, and numbering at A2
   (`visibility_taint_reset_contract.md:123-135`); the A1/A2 gate repeats those
   required checks (`stage_gate_and_test_manifest.md:75-123`). This is also
   consistent with the delta compiler's allowed inputs and post-unmount
   exclusion of assignment-derived seeds (`visibility_taint_reset_contract.md:49-56`).

2. **A4 value and gate scope — pass.** Primary A4 `V` is solely a legal
   world/action trajectory plus terminal world return for every arm; contradiction,
   revision, recovery, and retention are separate descriptive diagnostics
   (`research_loop/changes/chg_20260902_pcfl_active_stream_paper_target_v1/experiment_contract.md:148-160`). The normative machine-readable map limits
   T09 for C1--C3 to roster completeness, representation-neutral scoring,
   failure inclusion, and sterility; it explicitly excludes all A4 efficacy
   and mechanism results (`claim_test_applicability.json:52-67`). The acceptance
   object confirms that even zero A4 efficacy passes the current text integrity
   test when those structural conditions conform, and cannot alter P1--P4
   (`change.json:475-481`). The statistics contract independently keeps A4 out
   of P1--P4 and makes its mechanism efficacy descriptive
   (`statistics_and_claim_contract.md:260-280`).

3. **T10 / LoRA applicability — pass.** The machine-readable map marks T10
   `not_applicable` to C1--C3, defines `NOT_REQUESTED_STAGE_D` as a passing
   disposition with no evidence artifact, and confines mandatory T10 to a future
   separately ratified LoRA proposal (`claim_test_applicability.json:6-16,70-75`).
   The human-readable acceptance object mirrors those exact semantics
   (`change.json:484-490`), as does the Stage-D gate
   (`stage_gate_and_test_manifest.md:200-231`). Thus its coarse
   `required_before=scientific_claim` timing field cannot block a current text
   claim; the map is declared normative for claim applicability.

4. **No collateral change to primary design, visibility, or authority — pass.**
   The independent unit remains the twin-pair root; exactly 26 fresh roots and
   exactly four P1--P4 root aggregates comprise the alpha-.05 IUT
   (`statistics_and_claim_contract.md:5-38,97-120`). The intact roster remains
   768 ordinary + 36 lagged NEW + 12 first-acquisition OLD + 36 intact-clone
   integrative + 24 additional delta lanes + 32 common-history rows = **908 per
   root** and 23,608 total (`baseline_and_resource_manifest.md:82-94`). The
   claim ceiling remains finite, synthetic, and text-first, with LoRA only a
   future conditional sentinel (`statistics_and_claim_contract.md:298-321`; `compiler_memory_contract.md:267-284`). The component-level visibility matrix
   still bars assignment metadata from Dream-2 and the delta compiler, requires
   the latter to use only the common prior, Dream-1, public event, and pre-fork
   assignment-independent seed manifest, and preserves sterile evaluation
   (`visibility_taint_reset_contract.md:45-61,100-151`).

No proposal or workflow bytes were edited in this review; this advisory is the
only newly created artifact.
