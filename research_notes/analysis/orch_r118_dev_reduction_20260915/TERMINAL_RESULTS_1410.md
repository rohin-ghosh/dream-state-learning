# Terminal blind DEV annotation: incomplete coverage, no retained-gain claim

The original CPU judge ended at **13:56:36 UTC on September 15, 2026**,
`WALL_BOUND`. Both its Python process and timeout wrapper were subsequently
verified absent. Main re-ran the pinned native reducer at 14:08:42 UTC without
model, provider, GPU or training calls.

- 56 expected trajectories across F1 pre-shared sleeps 0–6; 21 exact unique inputs.
- 29 attempted trajectories: **22 COMPLETE, 7 UNRESOLVED**; 27 unattempted.
- All 22 completed annotations report zero departures-and-returns and zero
  strategy shifts. This is not a whole-cohort zero: longer responses and other
  unfinished inputs remain unresolved or unattempted.
- Completed baseline-matched task intersections contain only 2–3 tasks in
  each later cycle, out of eight. None is a complete eight-task comparison.
- Whole-eight-task median generated IDs remain 23.5, 50.5, 122.5, 21, 22, 22,
  24 across sleeps 0–6. The transient sleep-2 expansion is not retained gain.
- Sampling order was input-hash order, not random. Completed-only means can
  be biased. No duplicate-input annotation disagreements were silently resolved.

The saved annotations are model judgments. The reducer rechecked native-call
and HELD-cache hashes, model/source/prompt binding, request/response joins, and
the interpretation of the saved judge output. No new semantic judgments were
substituted for incomplete attempts.

Terminal SHA256:
`6cd9dc928a7e0e38d9bc8bf81e69757771a1509ccbbb868852b0242eb69d1891`.
Detailed compact: `REDUCTION_TERMINAL_1409.json` in this directory.
Native source remains `orch_r118_dev_reduction_source_20260915_v1` on ovx3.

## Bounded successor, distinct computational contract

Hubble identified 10 exact inputs not previously attempted, representing 21
unattempted member trajectories. Six other unattempted trajectories duplicate
already charged inputs and are excluded from successor dispatch. Original
attempts, unresolved outputs and annotations remain preserved unchanged.

A CPU-batched successor is being prepared, not yet launched: at most ten new
input invocations, batch size at most four, 4096 generated-token cap, 300 seconds
per batch, absolute deadline September 15, 2026 at 15:10 UTC. It uses the same
frozen Qwen-14B judge prompt but explicitly labels batching as a changed
computational contract. Legacy annotations are not silently relabelled as
batched results. Actual preparation, publication and launch receipts are
separate requirements; these bounds alone are not evidence of a run.

Neither this single-branch analysis nor the prospective successor establishes
parenting dependence, matched-control superiority, pooled-child learning, or
reproduction on FINAL. Those remain open goal requirements.
