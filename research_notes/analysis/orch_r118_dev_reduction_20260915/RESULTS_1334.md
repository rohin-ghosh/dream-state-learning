# F1 pre-shared DEV: incomplete blind annotation, no retained-gain claim

Snapshot: September 15, 2026, 13:34:29 UTC. Scope is F1's completed
pre-shared readouts at sleeps 0–6: the same eight DEV tasks at each checkpoint,
56 trajectories and 110 native calls. No FINAL data or new model calls were used
by this reduction. The underlying bounded CPU judge is still running.

| Sleep | Complete annotations | Unresolved | Unattempted | Median native token IDs per task | Total native token IDs |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 3 | 0 | 5 | 23.5 | 183 |
| 1 | 2 | 0 | 6 | 50.5 | 638 |
| 2 | 2 | 2 | 4 | 122.5 | 1947 |
| 3 | 2 | 0 | 6 | 21 | 178 |
| 4 | 2 | 0 | 6 | 22 | 180 |
| 5 | 2 | 0 | 6 | 22 | 180 |
| 6 | 1 | 0 | 7 | 24 | 188 |

Token counts cover all eight tasks and include all calls in each task trajectory
and terminal EOS where present. They are not per-call medians. No native child
output was truncated in this inventory.

The 14 COMPLETE annotations report zero departure-and-return pairs and zero
shifts. **This is not an estimate of the whole inventory:** input-hash order is
not random, and only one or two completed task pairs per later checkpoint match
a completed sleep-0 judgment. Their observed deltas are zero; the other tasks
remain unknown. The two UNRESOLVED annotations are both from sleep 2 and hit the
judge's output-time bound; their child trajectories contain 426 and 833 native
token IDs. Neither failure is converted into zero behaviour.

There are 21 distinct blind inputs across 56 trajectories. No completed duplicate
input annotations disagree at this snapshot. No annotation is copied to an
unattempted row, and the reduction does not silently collapse repeated tasks.

An explicitly unblinded author spot-check of the two unresolved child traces
finds assumed route connections and, in one, revisions following child-visible
record feedback. This is a qualitative observation, not a completed fixed-judge
annotation or evidence of grounded, retained metacognition. The sleep-2 token
burst followed by terse later outputs does not establish durable improvement.

## Evidence and validation

- Node-only source: `/localhome/local-rohing/orch_r118_dev_reduction_source_20260915_v1`.
- Node-only full compact result: `/localhome/local-rohing/orch_r118_dev_reduction_20260915_attempt1/REDUCTION.json`.
- Repo compact copy: `REDUCTION_1334.json`, SHA256 `d5859e2ef30c413054ef33e900c11e29cb4949eec730238d0077bc30fbbae4ef`.
- Reducer source SHA256 `f1b25a4759db8ed6dcafe0b299185a63027df39a4742ce464fd3f7de28f2c5a2`.
- Test SHA256 `bd42d487b5b26c950641dfa8447bac944764bdcee3da1e1c0128433507610955`.
- Fourteen local and fourteen native standard-library CPU tests pass. They cover receipt/native-source tampering, request binding, recomputed metrics, unknown handling, paired-task intersections, and duplicate-input disagreement. No GPU/model/provider call is part of these tests.
- The reducer rehashes every referenced native capture and HELD cache, verifies the pinned plan/source/model manifest and EOS configuration, and recomputes each finished annotation from its saved judge output. Raw child/provider strings are not exported.

This is one branch's exploratory DEV measurement. It does not establish
parenting dependence, superiority to frozen/unparented twins, generalization to
FINAL, or learning by the pooled shared child. Those remain separate evidence
requirements.
