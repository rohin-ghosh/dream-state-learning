# F1/A1 shared route activation — actual 2026-09-15

Both strict-admission launches succeeded at **12:25:26UTC**. Main initialized the common state at12:23:54; no initialization or roster changes by the route owner. No additional acknowledgment is required or awaited.

| Branch | Physical | Supervisor | Native actor | Native loaded | First completed shared response |
|---|---:|---:|---:|---|---|
| F1 |0|1035111|1035149|12:26:20.791880Z|12:26:24.674459Z,80tokens including EOS |
| A1 |4|1035107|1035110|12:26:21.570195Z|12:26:22.914821Z,11tokens including EOS |

These are native response counts, not semantic quality or functional-change claims. Both first calls have actual pre-generation `shared_generation=0` and checkpoint SHA256 `084f62110ca5e42fb55145675538f6f88e10ce684a9c8847c49d1c858df7d264`; full prompt prefix verified, `input_truncated=false`. First F1 prompt200tokens/A1prompt351tokens. No raw text or token arrays are copied to the repository.

## Actual PLAN and terminal bindings for Hubble/Main

- F1 root `/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1`, actual `PLAN.json` SHA256 `7d84a94eecce66c38dd2e52c2df4bf1b5eae48e3265c810f684cdb1f091d89fb`.
- A1 root `/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_4_attempt1`, actual `PLAN.json` SHA256 `88eb7ec06bfac5149e9fa201c2ab1068c500baf1d7fb0e81bb9e2e16d30cf0b4`.
- Frozen source root `/localhome/local-rohing/orch_r111_route_shared_source_20260915_v2r1`, executable `gpu.orch_r111_route_pair_shared`, SHA256 `c385db4fe1920ba645af8816327ddcbaebe10da3d1f42f3318330fa052ecb7ae`.
- Both real terminal paths remain **ROOT/TERMINAL.json**, absent before launch and at the12:27:54Z startup observation. Actual writer line763, supervisor reader line1018. No shared-terminal marker is invented; no historical terminal ignored/deleted.
- Existing A1 broker941768 remains live, unchanged root/queue/claims/config/HTTPslots4/120-second parent wait. Its frozen transport reads `ROOT/TERMINAL.json` at line735. Native `A1 ROOT/R118_SHARED_BROKER_BINDING.json` SHA256 `9e944f4e59b57360c7afeb5d4aeabccfafa2ad09471c8259ab66e74568047dfc` explicitly binds current PLAN, actual successor writer and live broker identity/config/reader hashes. No broker restart or claim reset.
- Hubble owns F1 broker migration and received actual PLAN/source/terminal-absence notification at12:25Z. Do not infer that migration completed merely from native residency. At12:27:54, F1's first postdispatch parent response was MISSING, not COMPLETE; no refusal retry/reroute or wait/effort change is authorized here.

## Preserved progress and proof

F1 resumed cycle7 with the latest cycle6 checkpoint and optimizer restored; A1 resumed cycle4 and reloaded that same shared adapter **without an optimizer**. Adopted lifetime totals1125steps/68231child-token exposures/20351anchor-token exposures remain; observed shared-only optimizer steps0, so no new joint sleep completion is claimed. Shared collection advances original counters, not a new baseline allocation.

- F1 `cycle_0007/CALL_000380.json` SHA256 `591a8cb48ef56146a2a63b77fd83769dbda3da16189e479511c263339ca128f8`; response-text SHA256 `c09e43bf3fde6fa0041ce4d8c0a2beb7668bce736c252ee12a8ed795b91ea5c8`.
- A1 `cycle_0004/CALL_000195.json` SHA256 `f8c8b385b8f251564622261f535906d6a30652e667e813e27952a803fdc23022`; response-text SHA256 `6b82b76fb7be09edd8c16e19a2a214276d2109be4bd3e991e8f93dfcb7f2f996`.
- F1 `R118_SHARED_DISPATCH.json` SHA256 `33bcbee5d17846d0a55eee357a9e020728ded6d735f1fe017b1059481541753c`; A1 same filename SHA256 `277fd667036ba982a9a42d1af6c2007842381eb97fac62b52c2ab4ef91b80b03`.
- Original PLAN/PUBLICATION/F1GO remain byte-exact hardlinks under each root's `R118_SHARED_PREDECESSOR_FILES`; root PLAN now intentionally names the activated shared source. Release certificates/ledgers/carry/checkpoints/uncharged teardown diagnostic archives remain preserved. No frozen source hotpatch, old raw deletion, foreign signal, or quota reset.
- Compact node receipt `/localhome/local-rohing/orch_r111_shared_route_receipts_20260915/STARTUP_COMPACT_1227.json` SHA256 `4dfacb5746a9c81ea0bbfa3c1ae304a2e26ca1b027fbc4a77c94fd4fba4b022a`; repository counterpart `SHARED_STARTUP_COMPACT_1227.json` contains only metadata/reductions/hashes. In-progress capture hashes are explicitly distinguished from completed calls.

## Tests and one-shot commands

Local handoff+activation14tests PASS; native handoff8 and activation6 PASS. The initial five activation tests passed before launch; the extra historical-terminal refusal regression passed locally before launch and natively afterward without blocking or mutating either live runtime. Frozen206-case native closure receipt remains unchanged.

Activation helper `/localhome/local-rohing/orch_r111_shared_activate_control_20260915_v1/gpu/orch_r111_route_shared_activate.py` SHA256 `87daa353bb0360e3cafcdc517a8d8134606ee030e4c640af494f7f0f4c59a56f`; native six-test receipt `/localhome/local-rohing/orch_r111_shared_activate_control_20260915_v2/CPU.json` SHA256 `dfb0a3929d8bb7342386fd239518bcbf18913fd094c879b97c20a7afc012a0e9`.

Executed through `gpu/ovx3_ssh.sh`, CUDA hidden for control/admission, interpreter `/localhome/local-rohing/v2/venv/bin/python -B`, PYTHONPATH frozenv2r1:

```text
orch_r111_route_shared_activate.py stage --root ROOT --binding COMMON/INITIALIZED.json --binding-sha256 d4e2c87e97bcfccb639d332d996f9f239023bbaa19f9312ce95d30f3f0aecff6
orch_r111_route_shared_activate.py launch --root ROOT --binding ROOT/R118_SHARED_BOUND_METADATA.json --binding-sha256 BRANCH_BOUND_METADATA_SHA
```

F1 bound-metadata SHA256 `b1718d21da4a8556a264e84e539ceb3c5090d5a7b7769585cd19c0d4f91bef56`; A1 `20bc4987b3c4c2633b461f0c87c2f81041a3908d6d53822fad614e924f0a9132`. **These commands already succeeded; do not rerun them.** Dispatch-attempt markers prevent duplicate activation. Normal supervisor lifecycle now owns the resident actors.

Common cutoff/watchdog remains the separate nonblocking operational plan in `R118_COMMON_COMPLETION_WATCHDOG_PLAN.md`, not an active controller or changed source. Main supervises the common run; FINAL17:00 and each original budget remain explicit, including the documented math16:59 native/17:00FINAL incompatibility.
