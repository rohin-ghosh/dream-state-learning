# R184 transition encoder handoff — September 17, 2026

**Confirmed integration limitation; not a deployment or integration-success claim.** The encoder remains undeployed by NODE1. Fleet recovery and the existing brain cache handoff take priority.

## Recorded-prefix extension is required

`gpu/orch_r184_transition_targets.py:144` constructs each earlier row's exact recorded prefix plus its actual target tokens. The next selected row must begin with that complete token sequence; otherwise line145 raises `ValueError('episode_requires_exact_recorded_continuation')`.

Consequently, a `complete_episode` spanning eviction, rewritten working-state consolidation, or another non-prefix-preserving context change can be rejected even when the actual child rows, history event IDs, and source hashes remain valid. Explicit dependencies and masked context do not remove this structural restriction. The implementation places earlier child targets at offsets within the final row's recorded prefix, so merely deleting the equality guard would risk training against incorrectly positioned or absent tokens.

The existing test `test_episode_rejects_evicted_or_rewritten_recorded_prefix` reproduces this rejection by changing the second row's recorded prefix. It does **not** test a real runtime consolidation event end to end. Working-state integration must explicitly account for this unsupported case; it cannot call every real episode compatible or claim successful deployment from this unit suite.

## Integration boundary

- Preserve actual recorded prefixes, child-source binding, declared dependencies, context masking, and the assigned16 exposures per row.
- Do not silently fabricate an append-only prefix, unmask consolidation/runtime text, drop a required dependency, omit failed rows, or add an episode exposure on top of the individual-row exposures.
- A caller may explicitly select a supported alternative view only if its actual dependency/source checks and exposure partition also pass; no automatic fallback or general compatibility is claimed here.
- Any support for complete episodes across changed prefixes needs a separately specified mapping and regression coverage against real consolidation shapes. No such change is implemented or authorized by this note.

## Exact source and test evidence

- Module SHA `92fe07d157f562db195e3deaba3b72bc746dafc376464b0fc120f651f49b3c8e`.
- Test source SHA `eeda07bcec8f327525f9585e16bddf2a43e1661c895dd68e138dcecc8dc1ee82`.
- Command rerun16:43 PDT: `CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_orch_r184_transition_targets.py -v`.
- Result:20 tests PASS in0.006s, including the explicit prefix-rejection test. This confirms the documented rejection and existing CPU behavior, not runtime integration or learning efficacy.

No shared native/history/journal/policy source edited, no encoder deployment, and no sealed content accessed.
