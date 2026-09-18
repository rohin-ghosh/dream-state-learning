# R233 node1-only retirement

Scope: `creative_b1`, `r203_creative_structured_a4`,
`r203_math_comm_b2`, `r203_math_self_derive_c5`, on logical node1 only.
Rohin explicitly authorizes retirement with state preserved. No refill,
kept-life signal, other-node action, original-file deletion, or learning change.

This is a non-material fleet retirement under the builder's standing scope.
The original cohort aliases resolve through `ACTIVE_CONTROL.json` to R210/R213
controls. Old root-level `RETIRED.json` files concern predecessor replacement,
not the selected descendant's exit. At the initial R233 scan, all four selected
descendants had already exited normally with final `R184_SCREEN_STOP` records.
The archival helper fails if any selected native or helper is still running;
it contains no signalling implementation and never starts a learner.

`preserve_ended.py` binds the active guard, plan, physical slot and raw root,
requires the actual final control's successful exit, and verifies final sleep,
working-state and terminal record hashes. It copies every stream file and
every checkpoint, the active control and runtime source into a separate
node-local archive. All copied file bytes are checked against their originals.
Original roots, earlier phases, service artifacts and readouts stay in place.
No claim is made to have copied inaccessible ephemeral executor root files.
Raw transcripts and binaries remain private on node1; publish metadata only.

Final checkpoint payloads are loaded on CPU and verified for adapter file hashes,
optimizer steps/state, CPU/Python RNG restoration and stored CUDA RNG tensors.
CUDA initialization and a GPU resume are not performed. Original private-namespace
paths in COMMIT files are preserved, with an explicit physical-root mapping.
The existing runtime's journal validator validates the original full stream;
the independently hash-equal copied stream preserves those exact bytes.

Native start ticks cannot be read after an exit. The final LAUNCH PID and
command hash are bound; recorded launcher-parent ticks must never be presented
as native ticks. No process is signalled based on those historical identifiers.

CPU regression command: `python3 -m unittest -v test_preserve_ended.py`
(run in this directory). Nine tests cover scope, exact-boundary integrity,
pending operations, old retirement markers and safe archival enumeration.
The journal validator reuses R144's logical-inbox projection for copied private
namespaces, without rewriting source paths or any journal bytes. The first
unprojected audit's failure receipts remain preserved; `--finish-existing`
revalidates every archived/original byte before finalizing these archives.
