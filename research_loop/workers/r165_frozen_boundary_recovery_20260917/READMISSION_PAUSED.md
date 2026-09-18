# Separate readmission work preserved, not advanced

September 17, 2026. Main's B1–B3 priority interrupt occurred before any new
`gpu/orch_r165_frozen_readmission.py` or its tests were written. No readmission
source was staged, prepared, or dispatched. This note retains the inspected
constraints so the work can resume without repeating discovery after boundary
review is resolved.

- Keep exact original plan/cohort/root. Require the actual completed R165 boundary,
  selected orphan optimizer/RNG and NOT_STARTED sleep1 readout before any native
  admission. Do not accept candidate1's rejected boundary preparation.
- Candidate5 original guard SHA:
  `c1358b5b478b7be8fbfde1beab43f0b7ca60db6ee019b5a7085a81844977bc85`.
- Original R151 containment SHA:
  `cbef4a98de3f230c8a50f4ec2d54b02200e6f835477bb39e8b9b60f24691bf70`.
- Original R158 profile SHA:
  `4e21fe3b72f823b9b26ba2edd08e8442ac68c3ea0fe3cdfea1590a2a5cd085d7`.
- Original matched-native SHA:
  `f8919b47e63c759d2a15a89eaaa1e28b4c16a7c1d4dcf0fd5efa320227e3fed9`.
- Original R158 capsule SHA:
  `9eec437e5e6c759a5817a023bf0d1f7d3d9f77f81068a447945b47a8d09a1add`.
- Original GUARD config SHA:
  `c49fc41bf226d223a2ad8825da6141183f0f03f2c4a042bdb97e9804f70b2945`.

Potential narrow design, not implemented/approved: retain all those disk bytes
in a new closure; exact AST adapters may select a separately verified execution
source while preserving original plan.source_root/cohort and every remaining
guard predicate. New schema-specific completed-boundary admission replaces the
inapplicable R158 fresh-only wrapper, not its scanner or confinement checks.
Any adapter must have explicit derivation hashes/provenance, exact-site tests,
and independent approval; no module/source identity masquerade is acceptable.

R151 engine has five `plan['source_root']` references in validate/supervise/contained;
scan command currently targets original guard directly. R158's bounded transient
scan wrapper additionally checks that module string. These execution-source/CLI
seams require exact scoped treatment, not a permissive source-root bypass.
Original `verify_guard_derivation`, `check_admission`, capsule foreign-device FD
tests, service observation and cgroup-empty lifecycle proofs must remain active.
Existing device6 lock can be reused, but old consumed once markers/GOs cannot.
New helper still needs its own fixed once semantics, fresh Main GO, physical6-only
identity, immutable source inventory, unchanged 12:00 UTC wall and complete
native provenance. No code/GPU readiness is claimed by this design note.
