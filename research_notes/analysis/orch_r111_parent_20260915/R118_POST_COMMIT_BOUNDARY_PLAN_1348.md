# Prospective post-commit shared successor seam — R118

Status: **plan only, no runnable new controller, no arming, signals, source mutation, backend installation, or quota extension**. Main owns common state/adoption and FINAL selector; Herschel owns the new parallel consolidation backend. This document owns route hooks and cross-family handoff requirements, not backend implementation.

## Actual state, not readiness by allocation

Native observation September 15, 2026, 13:45:23 UTC through `gpu/ovx3_ssh.sh`: first serial generation0 sleep is at **830/1884 in-memory updates**, 144908 child / 15653 anchor token exposures. `sleep/COMPLETE.json` is absent. STATE remains generation0, shared steps0, prior lifetime steps1125. No F1/A1 `SHARED_SLEEP.json` exists; latest local COMPLETE remains F1C6/A1C3. No first pooled checkpoint, reload, or fresh DEV claim is justified yet. The existing serial process is preserved.

`SHARED_SEAM_OBSERVATION_1348.json` binds observed STATE/START, exact eight readiness refs, roots/bounds, and native source hashes. Readiness refs there describe the **already activated serial successor**, not readiness for the new parallel backend. No actual parallel-client readiness certificate exists from this work.

## Required common event

First eligible generation is1, only after:
1. `common/generation_000000/sleep/COMPLETE.json` exists and its committed state equals the verified canonical STATE/checkpoint/optimizer; do not treat UPDATES or an uncommitted save as publication.
2. Each branch has actually mounted that checkpoint (F1 retains and saves the sole trained owner state; seven nonowners reload), and its fresh parent-free DEV process completes against that same hash. All eight must attest, not merely one family.
3. Each family certifies a settled safe cursor with no lost native/parent reservations, carry, or partial episode. Generation numbers and local cycle/sleep numbers are different; bind both explicitly.

Existing CONFIG, INITIALIZED/ADOPTION history, prior counters, and FINAL selector remain immutable. A future backend-era sidecar must explicitly name the committed generation and inherited F1 checkpoint/optimizer without reinitializing the learner. No independently trained adapter is merged.

## Actual family seams and owners

| Family / branches | Current executable and owner | Post-sleep evidence to require | Next-work race / seam constraint |
|---|---|---|---|
| Route F1/A1 | `gpu/orch_r111_route_pair_shared.py`; Poincare | `cycle_N/SHARED_SLEEP.json`, `cycle_N/checkpoint/CHECKPOINT.json` containing `shared_checkpoint`, `SLEEP.json`, `OWN_CARRY.json`; fresh `readout_S/COMPLETE.json` and loaded identity; settled `open_readouts/readout_S`; finally `cycle_N/COMPLETE.json` | Next iteration immediately writes START and reserves calls. A new controller must lock original `RESERVATIONS.jsonl`, verify no next-cycle charges, exact pidfd-bind actor/supervisor, and preserve at most a truly empty START cursor. No live STOP_AFTER_CYCLE polling exists. |
| Math F2/A2 | `gpu/orch_math_feedback_uptake_r118_shared_run.py`; Anscombe | `cycleNNN/SHARED_SLEEP.json` after `reload_at_boundary`; `readouts/cycle_NNN/BEFORE.json`, `AFTER.json`, `COMPLETE.json`; then `cycleNNN/COMPLETE.json` and PROGRESS | `dispatch_readout` waits synchronously; next loop immediately collects. Owner must rebind the reservation/counter-lock boundary controller to the shared actor/source and preserve COUNTERS, all reservations and carry. Legacy pre-shared release is not a current release. |
| Code F3/A3 | `gpu/orch_r108_code_parent_r116_shared_run.py`; Cicero | `cycles/CNNN_COMPLETE.json` identifies shared generation/sleep; `shared_readout_bindings/CNNN_DEV.json`; **actual** `readouts/CNNN_DEV/COMPLETE.json` with matching checkpoint/freshness | Important: cycle COMPLETE is written **before** DEV is spawned. DEV is asynchronous and the next cycle can already collect TRAIN while it runs. COMPLETE alone is unsafe; owner must settle/isolate resident next-work separately from readout, or explicitly preserve/resume already charged partial next-cycle work. |
| Grid F4/A4 | `gpu/orch_r118_grid_shared_run.py` under actual `orch_r118_grid_shared_repair.py`; Herschel runtime / Laplace client | `shared_cycles/NNNN/RELOADED.json`, fresh `readouts/NNNN/dev/COMPLETE.json`, then `cycles/NNNN/CYCLE_COMPLETE.json`; TRAIN_COMPLETE and CARRY | Use the active repair source and `shared_repair_v1/READY.json`, not the failed original runtime. Actual terminal is `R118_SHARED_REPAIR_TERMINAL.json`. Snapshot of settled ledger/carry is not itself a stop controller; family owner must bind the active guard/actor. |

All table source hashes were verified against native immutable files. Exact root/source/serial-readiness references are in the observation compact. These are source-derived seams; the future parallel readiness and release certificates are deliberately absent.

## Route-specific legacy blockers

Do **not** rearm `gpu/orch_r111_route_boundary.py` unchanged:
- Its process suffix is `gpu.orch_r111_route_pair`, not the running `gpu.orch_r111_route_pair_shared`.
- It only accepts SHARED_ADOPTION / WAIT600_TRANSPORT purposes; old authorization is not authorization for this new transition. F1 wait remains120.
- It assumes a local `cycle_N/checkpoint/optimizer_rng.pt`. Shared route writes a local checkpoint wrapper pointing at the canonical shared checkpoint; the actual optimizer belongs to that common checkpoint. Verify that reference and bytes, not a guessed local optimizer path.
- Existing candidate logic accepts terminal readout PROCESS_RESULT; the requested new seam needs **actual fresh DEV COMPLETE**. Failed readout is not fabricated as success or silently replayed.
- Reusing the empty-START cursor helpers is only valid after revalidation that no native/parent reservation or capture exists there. Preserve original START and write a new resume receipt, never erase history.

A new immutable, explicitly authorized route boundary controller must use the exact current PLAN/source closure, root, UUID, process UID/boot/start ticks, actor/supervisor pidfds and reservation lock. Hold the lock only after current readout work is settled; verify no parent request is pending, capture the canonical checkpoint+optimizer and local carry, and recheck ledgers before an authorized release. If validation races or fails before release, release the lock and resume only the exact processes this controller paused. This is a required future implementation/test contract, not an executed command.

## Prevent lost next-generation calls

There is no atomic all-eight barrier between the existing DEV readers and the next collection. Especially code can already be collecting generation1 while slower DEV runs finish. Therefore **do not promise a guaranteed all-eight stop immediately after the first sleep** from these frozen loops alone.

Future family controllers must either prove no later reservations at their settled boundary, or provide tested replay-free continuation of the exact already-charged partial cycle. All completed/failed/MISSING calls and pending parent dispositions remain charged and node-local; never regenerate or retrospectively relabel captures. If a safe first seam is missed and exact continuation is unavailable, leave that life intact and use a later common settled boundary under original caps (possibly another serial sleep). Do not freeze seven peers indefinitely while the eighth needs the shared owner to finish its already-collected generation.

## Proposed readiness / release contract (not a current file)

Each owner should prepare a **new** hash-bound `PARALLEL_CLIENT_READY` reference with:
- branch/root/current PLAN or activation + immutable source closure; active repair binding where applicable;
- proposed executable and CPU-test receipt; no claims from the old serial readiness alone;
- committed generation/checkpoint/optimizer reference, exact local completed cycle/sleep and next cursor;
- required actual DEV COMPLETE/loaded/checkpoint refs, OPEN completion where applicable;
- original caps/deadlines and current charged counts; remaining quota is derived, never reset;
- preservation hashes for ledger, carry, current plan/control, pending triples/parents, failures and any partial next cycle;
- exact owner identities, current terminal writer, boundary controller request/expiry, and replay-free cursor behavior;
- inherited lifetime metrics plus separate future backend logical-step/sample/token-exposure accounting.

Main coordinates all-eight readiness and authorization; each family emits a RELEASED certificate only after actual safe release. A release cert must not stand in for a future boundary prediction. F1 is the sole optimizer owner; seven workers never initialize independent AdamW states. Average-gradient multi-rank steps are **not equivalent to eight serial AdamW steps**. Herschel/Main own the new schedule, RNG/error/commit protocol, and explicit accounting; this route plan does not claim speedup.

## Existing guards and FINAL remain binding

A future process/source change must also explicitly rebind the separate identity-bound cutoff monitor/fuse and route FINAL scheduler predecessor/release bindings. Do not leave old-only identities protecting a new actor, or silently ignore mismatches. Preserve old control/evaluation configs and receipts; use prospective immutable versions and prevent duplicate FINAL schedulers. Main's canonical selector and CONFIG stay unchanged.

Drain review16:45UTC; common TRAIN cutoff16:55UTC. Original math native16:59/hard17:02 and all branch call/cycle caps remain effective. The separate FINAL allocation remains17:00–17:20UTC, only the canonical selected committed checkpoint, zero parent/training/optimizer, no early or duplicate FINAL. No future backend change may extend those clocks. Insufficient time means no transition, not a quota extension.

## Minimal future regression requirements

Before an authorized route controller is usable: test shared-wrapper optimizer reference, wrong module/PLAN/PID reuse/foreign sentinel rejection, pending native and parent settlement, failed DEV exclusion, empty-START preservation, raced next-call rejection, partial-work no-replay disposition, cancellation before release, original quota/clock preservation, and explicit watchdog/FINAL lifecycle rebinding. Family-specific async code readout handling is Cicero's scope, not a route-source patch.

No current backend or scientific code was changed to implement this plan. Control audit source/tests are a separate read-only reduction; six tests pass. The exact publication manifest contains only owned source, tests, compact receipts, docs and journal.
