# Actual learning behavior and prospective R227 completion

September 18, 2026, 18:46 UTC. Own P7 and original C2 only; no P3 action.

## Observed, not inferred from source names

- P7 resumed with actual WALL6740 and LOAD6741 at 18:40:31.323 UTC,
  optimizer8076, same journal and complete6734/sleep157. Its first new sleep
  has RECIPE6779, ELIGIBILITY6780: 3/3 new rows retained, zero exclusions,
  but three content and three prose checks actually executed. UPDATE6804
  records optimizer8100. That sleep was still incomplete at this cut.
- P7 completed sleeps153–157 each retained 3/3 rows and made48 updates.
  All15 checked rows contained CJK and had CJK exclusion explicitly disabled;
  normal Chinese punctuation was admitted. This proves actual Chinese training
  in this window, not that every semantic filter is disabled.
- C2 completed sleeps113–114 retained4/4 and made64 updates each. Sleeps110–112
  retained3/4 and made48 updates each. Actual reasons were script quarantine
  in110–111 and `meta_only_target` in112. The quarantine evidence had one
  fullwidth character in110 and three CJK characters in111. These are receipt
  dispositions, not our semantic correctness judgments.
- C2 was still replaying its authorized same-state continuation at18:46:18;
  no new C2 LOAD or post-resume sleep is claimed. Full hashes and bounded
  coverage are in `P7_ACTUAL_ELIGIBILITY.json` and `C2_ACTUAL_ELIGIBILITY.json`.
- Neither current continuation satisfies the requested all-semantic-exclusions
  disabled policy. A zero-exclusion batch is not a disabled-filter receipt.

## 19:19UTC: copied runtime ports now receiving-tested, not live

The receiving merge is implemented in disjoint copied source closures;
`r227_port/README.md` describes exact seams and remaining adoption work.
`r227_port/MANIFEST.json` binds both four-file deltas and before/after hashes.
No resident source or replay was changed. The receiving tests now validate
the actual copied plan and driver, semantic bypass including authentic
Chinese and normal Chinese punctuation, historical-annotation non-veto,
technical/provenance checks, CPU code/root forwarding, and synthetic AdamW
checkpoint/history/RNG restoration followed by a new-only sleep.

P7:8 receiving +5 compatibility tests pass. C2:8 receiving +10 compatibility
tests pass, including5 deep-work cases with R227 enabled.40 local operator
tests pass separately. The two receiving closures preserve every other
pinned file and all untouched function ASTs. These are CPU/synthetic tests,
not live adoption or an actual new GPU/CPU-tool execution claim.

The initial receiving attempt identified and fixed startup-context rebasing
and a missing test-fixture boundary policy. Earlier failure logs are retained.
The extra broad deep-work invocation imported legacy semantic-filter tests;
those two expectations intentionally conflict with R227. No shared tests were
rewritten; the focused deep-work class and seam runner pass.

Main can reuse `r227_plan.py:proposed_plan` and the exact delta hunks for P3,
not overwrite whole files. P3's `r212_prose_replay` and R233 recovered-boundary
guard must remain intact. No P3 receiving pass or source adoption is claimed.
Current resident policy mismatch remains as observed above. C2's existing
replay must finish; parent restoration and a later fresh COMPLETE precede
any coordinated runtime policy adoption.

## Earlier 18:46UTC diagnosis (superseded receiving-work status)

The authoritative R227 implementation is commit
`bb1e9a9033979d50ed97072675515f7290de1237`. It changes only the native trainer,
THINK driver, plain-context eligibility helper and new R227 policy module.
Main's existing191-tests/372-subtests evidence does not prove compatibility
with these older receiving source closures.

The scoped prospective transformation sets
`learn_row_policy=R227_ALL_AUTHENTIC_CHILD_ROWS_V1` in both plan and THINK;
removes semantic selectors, including the superseded P7 language exception;
preserves execution NFKC/code policy, CPU gate, judgment, identity, masking,
dose, optimizer and long wall; and drops the already-used wall-extension
authorization before a future same-long-wall resume. It never edits the input
plan or accepts the resident source directory as its destination.

35 focused operator/audit tests pass. These are NOT receiving runtime tests.
Read-only patch checks against exact source copies found concrete conflicts:
both native trainers lack the newer candidate-filter recipe metadata seam;
P7 also has a different driver optional-config set with its scoped language
hook. Therefore wholesale replacement or a config-only toggle is unsafe.
`R227_RECEIVING_PLAN.json` records source hashes and the failed dry-run checks.

Remaining bounded work:
1. Port only those four R227 deltas to separate copies of each actual source
   closure, preserving custom CPU bridge/root policy and C2 deep-work seams.
2. Run focused receiving config/driver/trainer tests: authentic Chinese,
   normal/fullwidth prose, code glyphs, repetition/meta and historical veto
   annotations must not be semantically excluded; parent/Tool masking,
   provenance and technical encoding checks remain enforced. Verify identical
   optimizer/RNG continuation, CPU dispatch policy and source manifests.
3. Only after the current continuation, at a later fresh coherent COMPLETE,
   perform supported same-current-state adoption; no stale checkpoint reuse,
   historical replay, mid-replay source mutation or current replay interrupt.
4. Report actual new LOAD plus actual recipe, eligibility, UPDATE/COMPLETE,
   with `active_semantic_filters=[]`; config/source staging alone is not live.

No additional native signals, exclusion changes, policy adoption or shared
source edits were performed during this audit. English remains a parent
request, not an eligibility rule. Existing sole overseer and bridge continue.
