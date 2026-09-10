# Source-drift incident and provenance refreeze — 2026-09-02

## Incident

The Active proposal was initialized while its formal context bound the live
`research_notes/IDEAS.md` at SHA-256
`1495966ec85df37c278c14625668aa0d1e4916924582e72882f49398500ec51b`.
The same live path was subsequently observed at SHA-256
`0b2aa2eebdb16a9099e81005b9c0cac4055e93218ffec2d28fd0ab5c4c7a7fdc`.
Because a mutable path changed after initialization, the attempt is invalid.
No interpretation from that attempt is canonical and none is scientific
evidence.

## Immutable replacement

The current live source was read between two identical SHA-256 observations:
`0b2aa2eebdb16a9099e81005b9c0cac4055e93218ffec2d28fd0ab5c4c7a7fdc`.
Its exact byte payload is preserved beneath the provenance header in
`ideas_context_snapshot_20260902.md`. The snapshot file SHA-256 is
`7c781851717af66122706b410c8f249a20546f64357b9e40731c4752cbdae75e`;
extracting the payload beginning on line 9 reproduces the observed live-source
SHA-256 exactly.

All formal context bindings for this proposal now name the immutable snapshot,
not `research_notes/IDEAS.md`. The live path is recorded here only as incident
provenance and is not a formal source.

## Invalidated artifacts and state cleanup

The two invalidated interpretation artifacts are preserved only under
`invalidated_source_drift_20260902/`:

- `interpretation_systems.json` — SHA-256
  `ecb1ce137e1b274d1546abdf4abfc6f317ecc8008dd73f00bf9b4b2bc91dccb2`.
- `interpretation_benchmark.json` — SHA-256
  `f40d7783eb7da75c1a3cac05062dd28f736683842e60f1686bddd92910aa04ca`.

They are noncanonical, non-evidence incident records. Their canonical
bundle-root paths were removed.

Only state owned by this invalidated Active attempt was removed:

- `research_loop/changes/chg_20260902_pcfl_active_stream_paper_target_v1/intake.state.json`
  (former SHA-256
  `a6a08ab4ca692a5afb5a157811830bcc1ec3b8546d4d2f8309c5a6a36281a995`).
- `.research_loop/intake/chg_20260902_pcfl_active_stream_paper_target_v1.deliberation.state.json`
  (former SHA-256
  `aa661132d5c375ab7bcbcc954863f04fe2196592d7803c54484499b33c6bab8a`).

No Active lock was present when the cleanup inventory was taken. No other
change, run, or state was touched.

## Authority and scientific-content boundary

This is provenance repair only. It changes no scientific contract, target,
estimand, power design, roster, resource budget, implementation authority, or
claim. It does not constitute deliberation, ratification, model/science
execution, or permission to run any such work.

