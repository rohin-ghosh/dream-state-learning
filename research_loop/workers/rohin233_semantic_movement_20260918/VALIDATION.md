# Builder CPU/provenance receipt

Validated on 2026-09-18; publication preflight at 12:15:43Z.

- Sidecar parser/privacy/observer-arithmetic tests: **13 passed**.
- Existing R232 canonical audit regression tests: **13 passed**.
- Immutable input validation: **16/16 evidence SHA256s match the frozen cut**.
- Canonical frame source SHA256:
  `e5b97a72e1566fd347f68792cac0dd7770fdaa8ee3a9790a7e9c073081af93dc`.
- Private cut SHA256:
  `6aee5711e161061a70255f0cd2b81a431cad944c096670b22b6712212af47d28`.
- Deterministic report regeneration matches the written JSON and Markdown.
- Publication base contains identical canonical parser bytes.
- Explicit UTF-8 file allowlist screened for addresses, host identifiers,
  credential patterns and large files. Raw-turn containment check passes.
- No providers, model inference, GPU work, new evidence collection, signals,
  runtime changes, child-code execution or new experiment launches.

The first observer-arithmetic test caught an incorrect reviewer expectation:
ordered pairs on 0 through 9 with sum divisible by 4 number **25**, not 24
(residue sizes 3,3,2,2 give 9+6+4+6). Both the annotation and test were corrected
before the final passing runs. This CPU enumeration is reviewer verification,
not evidence that any child performed the check.

## Published artifact hashes

- `REPORT.json`:
  `aaff7bf540678d5ca9e5ca77e0e239f361aa1915f2ed6223d1e31991f1244b4b`
- `REPORT.md`:
  `93a85c4cfc6ec2128e8ec07a206b8f310fed1c2a54479c401f8afa0f3870d9c6`

## Exact publication allowlist

Within `research_loop/workers/rohin233_semantic_movement_20260918/`:

- `.gitignore`
- `prepare.py`
- `view_events.py`
- `annotations.py`
- `report.py`
- `test_report.py`
- `README.md`
- `REPORT.json`
- `REPORT.md`
- `VALIDATION.md`

Additionally, one append-only dated Builder entry in
`research_loop/COORDINATION.md`, in a separate clean publication worktree.
Private evidence, raw turns and worktree contents are not on the allowlist.
