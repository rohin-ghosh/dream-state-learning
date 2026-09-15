# Active grid successor contract for Herschel

2026-09-15. Herschel owns `gpu/orch_r118_grid_shared_run.py`,
`gpu/orch_r118_grid_shared_ready.py` and their tests. This worker will not duplicate
or edit those files. Main owns common CONFIG, allocation publication and Git.

## Actual F4 predecessor, not the retired original

- Wrapper: `gpu/ovx3_ssh.sh`, physical3, UUID `GPU-d23c9369-39cf-51fd-833e-13292f173006`.
- Root: `/localhome/local-rohing/orch_r115_grid_pair_20260915/F4`, life ID `F4_FABLE`.
- Active source: `/localhome/local-rohing/orch_r118_f4_wait600_source_20260915_v3`.
- Active native PID804107: `-m gpu.orch_r118_f4_wait600 resident`.
- Active guard PID804050: `-m gpu.orch_r118_f4_wait600 guard`.
- Both current working directories equal the active source path. Revalidate current
  PID/kernel identity, UID, UUID/CVD and command before any future handoff.
- Active metadata: root `R118_WAIT600_V2/{BOUNDARY,CPU_READY,LAUNCH,LOADED}.json`.
- Active terminal: root `R118_WAIT600_TERMINAL.json`.
- Root `TERMINAL.json` is **historical**: the first wait600 successor loaded but
  failed on missing `roster` before reserving any new calls. Source_v2 and its logs
  are retained. Native374237 and guard374023 are retired; never target them as live.

The successful transition used complete cycle5, preserved379native/25parent charges,
and exact CARRY SHA `d46bc7d4dcb31b0d78cf94edd21d9ccc58099550bc95f76b93ced528fc10a6e4`.
It resumed cycle6, not cycle1. First new native N00380 completed, and P0026 was
reserved at11:51:25.007UTC with actual600-second wait. This checkpoint is historical
once later work completes: refresh the latest complete cycle and carry at activation.

## Parent wait and broker handoff

F4 future requests use600seconds; provider cutoff is lane deadline minus30seconds,
also bounded by the original hard deadline. Effort remains max and head remains max.
A4 remains120seconds. This is an explicitly labelled F4 transport era, not a
parent-model-only matched comparison with the earlier A4 schedule.

`gpu.orch_r118_f4_wait600.WaitLife.ask` uses the original ask implementation with
only its pure queue constructor rebound. The wire retains exactly four keys and
unchanged payload bytes. `SharedLife.ask` by itself still inherits the old120-second
constructor: the new F4 runner must deliberately preserve WAIT600, e.g. assign the
existing `WaitLife.ask` to its own `SharedLife` subclass, rather than editing the
shared-client source or resetting F4's wait to120. Do not apply this override to A4.

Hubble owns the Fable broker. He is restoring it with exact config-bound terminal
filename `R118_WAIT600_TERMINAL.json`. At a later shared activation, coordinate an
explicit successor terminal filename (such as `SHARED_TERMINAL.json`) with Hubble;
do not broadly ignore terminals. Same root/claims/responses/caps; no old claim retry.

## Actual A4 predecessor

- Same pair root, suffix `/A4`, life ID `F4_ASTRA`, physical7.
- Native374239: original `gpu.orch_r115_grid_native resident --root .../A4`, cwd
  `/localhome/local-rohing/orch_r115_grid_source_20260915_v1`.
- Guard374024: `/localhome/local-rohing/orch_r115_grid_pair_20260915/launch_r116/orch_r116_grid_launch.py guard --root .../A4`, cwd `/localhome/local-rohing`.
- Astra HTTP broker976579 remains live; broker-only transport migration did not
  restart A4 native. Coordinate its terminal handling at shared activation.

## Safe common activation and client

Keep current fallback lives running until the shared successor and common CONFIG
are ready. For each branch, retire only at a completed TRAIN+DEV cycle with no
next-cycle reservations, all charged native files COMPLETE and all parent claims
PUBLISHED; MISSING remains valid and charged. Preserve CARRY, ledger, cursor,
readouts, original17:02hard/16:55TRAIN cutoff and1858native/298parent ceilings.
Never rerun final0, old DEV or completed calls. Old guard retirement must not publish
a false terminal that prematurely stops the owning broker. Fresh scoped admission
is required after actual release. `wait600.boundary(ROOT, CYCLE_COMPLETE_path)` is
the existing F4-only validator; do not call its `migrate()` for this handoff because
that entrypoint is pinned to the already-retired original PIDs.

The client remains unchanged:
- `gpu/orch_r116_grid_shared_client.py`: `ebb5a34315054db61af8f8edfdb7f9ccb70db3283ef0d096449c9a0beebf3577`.
- Test SHA: `961410ee77430d99c6e4f4aca04a49c5bef37ea221b1800f8b7ee1534fdca1fe`.
- Latest local client+Main coordinator52PASS. Earlier50nativePASS used an older
  coordinator; do not relabel that as validation of the newest coordinator.

Use `prepare`, `load_shared`, `SharedLife`, `run_cycle_and_submit`, `wait_for_next`,
and `reload_shared`. Bind actual common generation/checkpoint before every native
call; both collection and sealed readout must load the published shared adapter,
not the old BASE loader. Exactly two sequential TRAIN episodes and reflection;
exclude DEV/FINAL/readout-open. F1 alone owns optimizer/sleep. Existing BASE captures
cannot be rewritten into shared-checkpoint history. This worker's client is
CPU-ready but has not published actual SHARED_CLIENT_READY; Herschel's runnable
successor owns that readiness now. Extra A1004/node3_5/node3_6/node3_7 are not part
of the shared eight, and this worker will not touch Main's node3_7.
