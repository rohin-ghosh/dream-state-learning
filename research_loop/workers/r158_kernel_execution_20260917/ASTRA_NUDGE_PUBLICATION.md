# One authorized Astra nudge per existing kernel child

**FINAL05:03UTC:** both services closed cleanly05:02:39UTC; observers also ended.
Kernel4 nudge and subsequent Tool rejection actually rendered; no kernel GPU
launch. Kernel0 publication not rendered through closure. See `FINAL_CLOSURE.md`.

**Follow-up04:52UTC:** old observer failed04:26:53UTC on a mutable STATE read
race. Its earlier status below is historical, not current liveness. Repaired
observer159584 is live with current phase2/calls0; no rendering yet.
See `FOLLOWUP_20260917T0447Z.md`. No second publication is authorized or made.

## Publication — September 17, 2026, 04:21:32 UTC

Published exactly once to kernel0 and kernel4 via the sanctioned
`gpu/a40r_ssh.sh` wrapper and existing `publish_parent(root, 'Astra', text)`.
The complete Main-authored text was passed verbatim, without a solution body.
UTF-8 text SHA256:
`448aa2c8dd3ea9ac1125e08ba552662c4f9a8792ca9ff7786fb7a49438ea5901`.

Immediately before each publication: both original child identities matched
the R158 activation; supervisor4042560 and sidecars4048159/4048160 matched live
PID/startticks; both scanners were READY with no pending fields; phase1 and
the new confinement gate remained valid; immutable source pins matched.
No expired gate, old request replay, child restart or retired5 change.

| Life | Inbox ID | Exact publication SHA256 |
|---|---|---|
|kernel0|`045934b6bbd2453897fde7f298a57018`|`b69fcbaea4b83dd680a9bd4617063be39acb80ea7eb799719471348656cda029`|
|kernel4|`bc96acee94154bfc85c678b21f124b5f`|`d44f3056f4d18628a72c6a4ccd49bbbe6a63a7570a1e561f9ece348ee7ddd055`|

Original-byte local receipts:
`astra_publication_receipts/astra_main_nudge_20260917t0422z/`.
The directory label is rounded; actual publication timestamps are
1789618892.5035708 and1789618892.511736 (04:21:32 UTC).
Create-only intent and per-life attempt markers prohibit automatic retries
after uncertain publication. **Do not send either message again.**

## Rendering — not yet observed at 04:23:23 UTC

Neither inbox ID has yet appeared as a matching INBOX registration followed
by exact attributed text in a committed TRAIN journal REQUEST's rendered
`messages`. Inbox publication alone is not rendered exposure. Native generation
completion is also distinct from the REQUEST being written.

## Child execution — none at 04:23:23 UTC

Both scanners remain READY/calls0, with no bridge results. This is not a GPU
submission or execution receipt and no correctness/speedup is claimed.

## Bounded observation is running

CPU-only observer4134329 starts04:23:23UTC. It reads only subsequent TRAIN
journal records and owned service/result metadata, checks the hash chain and
same child identities, and writes observation receipts. It cannot publish,
dispatch, restart a child, alter a cursor or change the immutable service.
It stops on campaign completion/failure or after180 polls at15seconds
(at most~45minutes); errors produce FAILED_NO_RETRY. No held artifacts opened.

Remote status:
`/localhome/local-rohing/orch_r158_kernel_execution_20260917t0402z/astra_nudge_observation/STATUS.json`.
Initial downloaded status: `NUDGE_OBSERVATION_INITIAL.json`.
Observer script is staged separately in `nudge_observer_source/`, outside
the pinned runtime source. Its CPU regression tests: **11 passed**.

- Helper SHA256: `ae6dc50084f63b7ee345f41e5a78b9a709a408a132f85d5d8f52df8bbc6781b3`.
- Tests SHA256: `fc9806bf4283ace0c8cd79b9b95ac71be8415877f5421e0948890298e1248cc0`.

The observer separately reports registration, actual rendered REQUEST index/hash,
bridge result status, real `launch_attempted` and `child_generated` flags. A
rejected child request is not described as an executed kernel. The already-live
R158 service alone retains admission, execution, publication and bounded renewal.
