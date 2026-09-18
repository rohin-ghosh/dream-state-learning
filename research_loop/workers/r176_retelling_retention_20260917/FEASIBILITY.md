# R176 feasibility / first CPU candidate — September 17, 2026

**First candidate prepared at 16:09:36 UTC / 09:09:36 PDT. Eleven offline CPU tests pass.** This is a fixed-slot design/CPU candidate, not receiving CPU, complete source custody, independent approval, or execution GO.

## Fixed measurement

- Freeze **C2 sleeps 33–38 and C5 sleeps 29–34**: 12 checkpoint identities, 24 fresh condition processes, maximum **72 calls / 36,864 generated tokens**. `SLOTS.json` freezes the complete selection before any R176 responses or scores.
- Keep the existing frozen three-prompt generator byte-for-byte. **P0 is primary; P1/P2 remain separate secondary readouts.** No P0-only shortcut, decoder change, prompt-history injection, training write, or provider judge. Every prompt receives only the exact original system and birth context independently.
- Proposed execution: node2 physical0/1, unchanged strict privileged admission, ≤90 minutes from first admission and ≤10,800 GPU-slot-seconds, clipped to **September 17 19:30 UTC** and the verified lease minus six hours. A 24-process ceiling does not promise all processes finish within 90 minutes.
- No newly generated initial-baseline calls. Verified exact reuse count is currently **zero**. C2's prior initial completions are reuse candidates only; C5 has no bound reusable initial result. Missing baseline remains a limitation, not permission to generate one.

## Source and custody, explicitly timed

Both sources use `gpu/ovx3_ssh.sh`. No new R176 remote observation has occurred.

| Life | Original source | Existing evidence | Still required |
| --- | --- | --- | --- |
| C2 | `/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life` | R170 verifies own-row training included in sleep33, COMMIT created 10:08:06 UTC. R172 native custody at **15:22:57 UTC** verified frontier37. Its 15:46:03 UTC capture observation had initial only; it did not verify sleep38. | Exact immutable bytes/custody for each selected checkpoint, original birth, private preoutput witness/rubric, receiving copy/CPU and read-accounting proof. **Sleep38 completion is unverified**, not assumed retrospective. |
| C5 | `/localhome/local-rohing/orch_r153_community_C5_20260916_attempt1/life` | R170 verifies own-row training included in sleep29, COMMIT created 09:49:47 UTC. R172 custody preparation retained `C5_exact_recovery_release_witness_missing`. | Exact recovery-release/original-source custody, birth and all six checkpoint bindings. Retelling execution evidence alone does not satisfy saved-state custody. |

Known first-checkpoint metadata pins, not adapter validation:

- C2 sleep33 COMMIT: `38067e8619851f556e49b3e3c26f307fd1b4abfd700fcb64d4cdde18a91dc70f`.
- C5 sleep29 COMMIT: `1c8706984fb76c62a085268e12224a6a163098bf8d79e2d1e52b855770477f42`.
- R170 custody metadata: `../r170_replay_boundary_20260917/RETELLING_EXECUTION_METADATA.json`, SHA256 `ab98ea8cb6c646846ee0b3f25ebb7fa422f2b07b8cd496358e6dbe7633b64ac2`.
- R172 evidence: `../r172_forward_probes_20260917/preparation1/enrollment/C2.json`, `../r172_forward_probes_20260917/preparation1/enrollment/C5.json`, and `../r172_forward_probes_20260917/preparation1/capture_observations/ovx3_01.json`.

**C2 never waits for C5 custody.** The twelve identities/missingness rules are frozen together; each exact checkpoint source binding is attached once before that checkpoint's admission. Ready fixed C2 checkpoints can proceed after their own gates even if C5 or C2 sleep38 is held. A missing slot stays missing; no fourth/seventh/later or favorable checkpoint substitutes for it. No score is an input to scheduling.

## Finite source-read proposal, not authorization

`PROPOSAL.json` proposes a **new R176** pre-I/O ledger: 2 GiB metadata (32 MiB operational discovery included), 16 GiB adapter reads, 1 GiB metadata and 8 GiB adapter per life, 128 MiB hard adapter-size cap/checkpoint, 2 GiB receiver storage, and streaming with no local archive. Ten named adapter read passes/checkpoint reserve 15 GiB for all twelve slots; all failures, verification rereads, receiving hops and loader reads count. Additional reads cannot exceed the remaining envelope or silently retry a failed operation.

The earlier stat-only observations for C2 and C5 each report **80,798,775 initial-adapter bytes**. These support a size-feasibility estimate only: each selected checkpoint must independently pass the 128 MiB cap. No new adapter bytes were opened for this proposal.

**Earliest prerequisite:** Main binds the new R176 source/custody read envelope and exact proposal before new remote checkpoint I/O; then at least one fixed C2 slot must acquire complete source/receiving/private-evaluator bindings. Old R172 authorities cover different fixed future sleeps and are not borrowed. No elapsed completion estimate is supported.

## Shared code / review dependencies

- Existing generator pin: `gpu/orch_r167_fleet_eval.py`, SHA256 `383415b6b37f8ff237c95b053439f6919f7ee47c452b3ffd015e606ff1962011`.
- R172 B1–B4/B7 repairs remain required shared primitives: unchanged complete checkpoint verifier, actual host/device/lease schema, complete imported source closure, exact paired capture identity, and per-life oldest-ready scheduling. The existing R172 runner's fixed 24-life/root/GO contract **cannot run R176 unchanged**. A separately bound R176 admission/ledger adapter must use those repaired primitives; never monkeypatch R172 constants or reuse its GO.
- Ampere owns transfer/prep_common B5/B6. Their changed receiving API invalidates the older combined transfer fixtures; that failure is preserved in R172 `PREPARATION_CPU_07.txt`. Neither that run nor the eleven R176 offline tests is a full receiving pass.
- Fresh actual receiving CPU and a new independent bound review must follow the combined repaired source. Main's separate no-reset execution GO and fresh strict admission remain mandatory.

## Claim and visibility limits

This is a repeated checkpoint readout of selected retelling-period lives, not a randomized retelling treatment-effect experiment. ON/OFF controls separate adapter-dependent output from the frozen-base/birth-only control, but do not isolate retelling from other intervening training. Initial-reuse gaps, unfinished checkpoints, unpaired/failed cells and truncation remain explicit limitations under the unchanged private rubric. No success claim or retention outcome is released to Main.

Evidence: `PROPOSAL.json`, `SLOTS.json`, `SCOPE.md`, `candidate.py`, `test_candidate.py`, `CPU_CANDIDATE_01.txt`. R167/R172 proposals, evaluations and consumed budgets remain unchanged. R176 has made **zero remote, GPU, model or provider calls**.
