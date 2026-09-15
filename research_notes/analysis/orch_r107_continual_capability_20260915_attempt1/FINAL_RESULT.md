# Continual FULL8932 capability panel — final, 2026-09-15 08:28 UTC

Native run 08:07:42.601631–08:10:13.042239 UTC on gpu/a100_ssh.sh physical0.
All64 calls are fresh, one process, zero retained cells, truncations, parents or
optimizer updates. OFF means this FULL adapter DISABLED, not separately trained
new-labels-masked OFF. BASE is the pre-existing fixed-panel reference, not rerun.

## Behavior first, capability second

Generated tokens including EOS: ON346, disabled-OFF381, BASE381. Content tokens
ON314/OFF349. These constrained short-output tasks do not measure persistence,
metacognitive movement or semantic novelty; those remain unassessed here.

| Family | BASE | Disabled OFF | ON |
|---|---:|---:|---:|
| Code | 2/8 | 2/8 | 1/8 |
| Math | 7/8 | 7/8 | 7/8 |
| Mock tools | 8/8 | 8/8 | 7/8 |
| Concise instruction following | 7/8 | 7/8 | 6/8 |
| Total | 24/32 | 24/32 | 21/32 |

Pairs:20 both-pass,7 both-fail,4 OFF-only,1 ON-only. ON-only CODE01 packages a
valid JSON expression; OFF-only CODE02/CODE05 are JSON packaging losses,
TOOLCALL07 uses a string instead of the requested integer, and concise03 emits
the wrong first-three-letter sequence. Not all regressions are formatting.
CODE00 in both arms uses valid Python exponentiation outside the bounded
interpreter: this panel does not measure general Python competence.

BASE and disabled-OFF match31/32 raw and generated-token sequences, not32/32.
The mismatch is R107_CODE_03 (hashes in the two digest manifests); equal total
scores/tokens do not establish identical outputs. Adapter disablement restores
aggregate baseline performance on this panel; no universal suppression,
destruction, retained-learning or thinking-success conclusion follows.

## Evidence and execution/publication distinction

Native raw root: /localhome/local-rohing/orch_r107_continual_capability_20260915_attempt1.
Compact result: PAIRED_REDUCTION.json, verified against hash-bound CALL/LOADED,
plan, complete and adapter receipts. OFF_OUTPUT_DIGESTS.json and
BASE_REFERENCE_DIGESTS.json bind the reference comparison without raw text.

FULL8932 adapter SHA256:
121655d491bc55ba6bbd8eb732bc4f7a65215a07d3b6b2492f4fa623026f80f1.
Base tensor SHA256:
a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992.
Fixed32 suite SHA256:
32a1d71ff23e168f42366ec4c96777aceb59247020e7a3ae98b6f64b4b9b602c.

The native runner contained a private host literal. It remains immutable on-node;
the repository candidate replaces it with hashed identity. The sanitized source
is NOT the exact native execution source. SANITIZATION.md and the sanitized
publication manifest preserve that distinction; no native rerun is implied.
The earlier REPORT.md is an initial launch snapshot, superseded for results by
this file. Reducer process-disclosure repair derives boundaries from receipts
rather than assuming an earlier run's retained cells.
