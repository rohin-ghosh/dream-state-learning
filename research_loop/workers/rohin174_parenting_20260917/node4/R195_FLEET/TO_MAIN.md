# Node4 operator: inventory complete, awaiting tested READY

**MSG201 SUPERSEDES THE ROLLOUT PLAN:** Uniform rollout preparation stopped.
No operator was armed or deployed. Current work is read-only, bounded degraded
candidate selection; retirement requires Main naming an exact slot/life.

Snapshot 2026-09-18 02:05:57 UTC /2026-09-17 19:05:57 PDT;
receipt `INVENTORY_20260918T0207Z.json` uses the observed timestamp inside it,
not the nominal filename. Seven actual learner natives; no missing life.

| GPU / device minor | Life | Native PID / start ticks | Latest COMPLETE |
| --- | --- | --- | --- |
| 0 /3 | kernel0 | 1742549 /25551049 | 56 |
| 1 /2 | raw_unparented | 1734752 /25543112 | 57 |
| 3 /0 | raw_parented | 1565205 /25377833 | 61 |
| 4 /7 | kernel_parented | 1643508 /25450832 | 56 |
| 5 /6 | relocated brain_free | 1995652 /25800024 | 55 |
| 6 /5 | relocated brain_guided | 2001674 /25805852 | 52 |
| 7 /4 | relocated support_free | 1995650 /25800021 | 58 |

All seven actual plans and saved states retain hard wall1789754400
(September18 18:00 UTC /11:00 PDT). Lease end1789776000 is September19
00:00 UTC /September18 17:00 PDT; the existing six-hour safety margin remains.
All seven have actual recent `R181_NEW_ONLY_V1`,16 new presentations,0 old
selected rows; none currently has `think_act_learn` in its plan. Current
source lacks R184, R193, the glyph-filter module and code-block module.
No R184 successor has been staged, dispatched, or observed by this operator.

## Concrete Main integration findings

1. **Need the final tested dependency closure, not a native-only copy.** All
   seven are pre-R184 sources. Final R184 also imports R189/R191/history/state
   interfaces. Receiving imports and existing focused tests must run on the
   actual final source after READY. No shared source files were copied early.
2. **NFKC propagation is not uniformly complete in the shared tree inspected.**
   `gpu/orch_r132_kernel_bridge.py:24` accepts only LEGACY/POLICY; its extraction
   at line31 also omits an explicit policy. `gpu/orch_r153_community_transport.py`
   accepts NFKC in direct `cpu_once`, but its remote request schema at line304
   does not allow `code_policy`. These are route-specific integration findings,
   not a request to add unrelated features; fix/bind whichever route final
   receiving plans actually use. This worker does not edit runtime.
3. **CPU availability is not proved by native-venv imports.** Node4's existing
   R153 gate directory is present. Native venv has SymPy/NumPy but not SciPy or
   pytest. No separate bridge/service Python process was found in the bounded
   process inventory. Actual confined CPU interpreter/profile and tool
   availability still need final receiving tests; no tool execution was sent.
4. **Reuse R181/R179 primitives with current identities.** Existing
   `r181_journal_release_20260917T2220Z/node4_rollout.py` provides `saved_evidence`
   (adapter/AdamW/Python/CPU/CUDA RNG/history/wall checks) and its bounded
   handoff mechanism. The `r144_helpers.py` `regular` check rejects logical
   symlink roots used by all three R188 rehomes. The read-only observer resolves
   backing paths without changing the logical plan; do not mistakenly treat
   that observer repair as authorizing a weaker handoff check. Preserve the
   current R188 rehome guard/containment and original checkpoint path semantics.
   The historical selector is limited to old PIDs/0,1,3,4 and cannot be invoked
   blindly for this fleet.

## Finite handoff / blockers

Only blocking external dependency now is **Main's tested READY with final
source/config/dependency bindings**; the four items above must be resolved by
the receiving integration, not by new permission/custody scaffolding. After
READY: receiver CPU checks, finite wall-clamped COMPLETE/readout-drained
handoff, then actual first LOADED and R184_STAGE per life. Other ready lanes
need not wait for a slower lane. No in-flight sleep interruption or old-row
rehearsal; original logical roots and all inboxes remain unchanged.

**Zero signals, source deployments, GPU launches, parent publications, or
background waiters.** No node5/C2 or expired node3 connection; no credential,
sealed, or final-data reads. Runtime/tests/COORDINATION unchanged by this worker.
All output is in `node4/R195_FLEET`.

The first inventory receipt is preserved: it had observer-only duplicate timer
identities and `no_symlinks` errors for relocated logical roots. The second
receipt has exactly seven learners and zero errors. This is a non-material
observer repair, not a learner failure; owned regression tests cover both.

Validation: `PYTHONDONTWRITEBYTECODE=1 python3 -B
research_loop/workers/rohin174_parenting_20260917/node4/R195_FLEET/test_inspect_node4.py`
passed2 tests in0.022s. These are observer-only regressions, **not receiving
runtime approval**. Final finite READY check at02:08:00 UTC still found Main's
implementation-in-progress entry and no READY in this worker's path. No waiter
is left running; the next action is Main's explicit tested READY.
