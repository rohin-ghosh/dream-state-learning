# Canonical three-arm coverage — observed September 15, 2026, 13:39:15 UTC

Read-only verification through `gpu/ovx2_ssh.sh`; no new inference, signals, restart, or control creation. Raw remains node-local.

Canonical root: `/tmp/orch_route_parent_campaign_20260915_canonical102`.

| Arm / exact root suffix | Initial child | Latest completed sleep / parent-free readout | Saved updates, lifetime | Terminal |
|---|---|---|---:|---|
| `GUIDED` | Shared initial adapter | C6 / C6 | 424 | C7 experience FAILED; guardian FAILED |
| `UNPARENTED` | Same initial adapter | C8 / C8 | 752 | Guardian COMPLETE |
| `NO_LORA` | Frozen Qwen BASE, no adapter/PEFT; parented | C6 / C6 | 0 | C7 experience FAILED; guardian FAILED |

All three original actor PIDs are absent. This does not imply their historical physical slots are currently free.

## Identity and readout coverage

GUIDED and UNPARENTED both start from `initial_adapter` under the canonical root, verified state SHA `d13fabd566e04926f45aa66ee0a30ff7dc88d411430ab3e1fe15dfffeb2fd27f`. All arms bind base SHA `a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`. NO_LORA uses that bare BASE, **not a frozen initial-adapter twin**.

C0–C6 task hashes match across arms. All 18 post-sleep C1–C6 joins verify a fresh readout process, no parent, exact saved child, and loaded identity equality. These are the canonical campaign's parent-free readouts (`cycleN/readout`), not the later R118 DEV8 protocol. Each readout has only two episodes / one world. Tasks change between cycles, with no adjacent overlap. Source hashes are historical PREPARE bindings, not claims about the current mutable checkout.

At the matched C1–C6 horizon, saved updates are GUIDED424 / UNPARENTED536 / NO_LORA0. GUIDED C6 makes zero updates (`NO_VALID_REFLECTIONS`) and retains C5. Parent charges are 55 / 0 / 50; charges are not proof of delivered interventions. Matched ancillary outcomes remain 10/12 / 8/12 / 6/12, identical to Main's 12:11 audit; these are not a newly computed thinking score or a causal effect estimate.

## Claims covered and missing

- Covered: actual saved adapter lineage, parented/unparented initial-adapter match, genuine zero-update BASE arm, and parent-free fresh-process transfer-readout availability.
- Limited descriptive comparison: the three realized systems on shared per-cycle tasks through C6. UNPARENTED C7–C8 are unmatched and excluded from this comparison.
- Not isolated: the effect of parenting on learning at equal realized exposure (424 vs 536 updates); freezing the same seeded child (NO_LORA instead starts from bare BASE); intervention delivery/dose effects (only charges verified here).
- Not established: same-task retention, retained thinking/metacognition, population-level gains, or superiority of the later shared pooled learner. This historical triple is not a matched control for R118's pooled lineage.
- Failures are preserved, not repaired or replayed. Both C7 experience failures are ValueError; exact error hashes and terminal refs are in the compact. No failure cause beyond those receipts is inferred.

## Evidence and reproducibility

`CANONICAL_CONTROL_COMPACT_1343.json` contains exact roots, receipts/hashes, identities, matched task hashes and limitations. Full metadata audit stays at `/tmp/orch_r111_control_audit_20260915_1342_v2/AUDIT.json`, SHA `4514c01ae1b13dd5eedc80de1efe9f712112e3393b4e38517469482c2937699a`.

Reducer `gpu/orch_r111_control_audit.py`; six focused tests pass. Prior v1 audit remains untouched; v2 changes task-hash serialization to match Main's default JSON encoding, not task bytes or outcomes. No GPU/provider/judge calls, no hidden task contents copied.
