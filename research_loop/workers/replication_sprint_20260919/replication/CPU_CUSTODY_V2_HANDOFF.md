# V2 CPU custody repair and dead-claim disposition

**READY FOR MAIN REVIEW/RECEIVING EXECUTION. No worker-side release, staging,
proof submission or model dispatch.** Source is sealed and held.

Seal `CPU_CUSTODY_SOURCE_FREEZE_V2.json`:
`050587019d9f0a53e3c52ea6ac1af61635db20683ba40ac69809c47e90b099df`.
**66 CPU tests pass**, `CPU_CUSTODY_REPAIR_V2_TESTS_FINAL.log`.
The science candidate, captured checkpoints, judge/panels, seed choice,
contract and token budgets have not changed. All previous seals remain.

## Main's exact commands

Copy the current seven runtime Python files listed in the seal, the command
script, `CPU_CUSTODY_REPAIR_V2.json`, the seal, `ORIGINALS_RECEIPT.json`,
`C2_SAMPLING_CANDIDATE_V2.json`, and Main's exact
`C2_SAMPLING_PREREGISTRATION.md` into a **new immutable receiving package**.
Do not overwrite either prior source package or the failed diagnostic root.
From that receiving package, execute separately, reviewing each result:

```bash
bash CPU_CUSTODY_V2_COMMANDS.sh release-check
bash CPU_CUSTODY_V2_COMMANDS.sh release
bash CPU_CUSTODY_V2_COMMANDS.sh stage
bash CPU_CUSTODY_V2_COMMANDS.sh check
bash CPU_CUSTODY_V2_COMMANDS.sh prove
```

Only Main executes these. `release-check` and `check` are read-only checks.
`release` is the explicitly authorized dead-ownership archival operation.
`stage` writes a disjoint CPU diagnostic; `prove` submits six new CPU-only
units after fresh original admission. There is **no `run` action**. Both the
dispatcher and role command reject a model run for this new incarnation.
Do not submit `prove` again after any failure. An admission-not-granted
receipt before submission is not a platform denial and does not auto-retry.

New root:
`/localhome/local-rohing/post_sampling_custody_diagnostics_20260919/d0f368fbcb0ac74ba908a008d7b4daac0bf3f3cd19d5a3fc171902e7419adaad`

Registry: `CPU_CUSTODY_REGISTRY_V2.json`, SHA-256
`e77f7d10b2e7732b7603ed471e3874408d8c3099ee62f2921e2ade118489c7b4`.
Fresh block:
`a465f7195077b4820d36e81d257ca36c30db991793467f7805430ff3090725e3`.
Fresh jobs begin `aa9a113bf5e2ded3`, `925189dbc0808930`, `f4d46c2ebf1d247f`;
the registry contains the full IDs. No old unit/root/guard is reused.

## What changes, and what must be measured

1. The original hash-bound `FrozenCPUEncoder` imports `torch` and
   `transformers.AutoModel/AutoTokenizer`; it does **not** import the
   `sentence_transformers` Python package. Read-only receiver inspection
   confirms that package is absent in the original `/v2/venv`. The proof's
   invented import is removed; no dependency installation, model substitution
   or scoring change is made. Original recorded library versions are checked.
2. All nine private player-facing file paths were zero-byte bind-mount
   targets in the shared host view. This explains a possible visibility
   failure, but the old proof did not record its individual path results.
   V2 adds actual `InaccessiblePaths` protection over the player's `judge`,
   `epoch` and `assets` directories. The existing denial check is unchanged.
3. Each new CPU role records `*_CUSTODY_PATH_DIAGNOSTIC.json` **before** the
   denial assertion. This contains path/boolean checks, identity and timestamps,
   never file bytes. Main can identify the exact failed path if confinement
   still fails. Successful proofs must also open only their assigned GPU
   device and deny the other seven, without loading a model.
4. The new CPU-only identity explicitly binds Main's repair instruction and
   the previous failed registry, source seal, preparation, launch and failure
   hashes. The old block remains terminal. This is not a sampling rerun or
   permission to reuse its scientific execution guard.

## Safe ownership disposition

`release_failed_claims.py` holds the **original shared `DISPATCH.lock`** while:

- Verifying all prior failure/source/config hashes and the six old transient
  unit names, exact original proof argv, UID/GID, unique invocation identities,
  and joins to the preserved role-start markers/PIDs.
- Requiring each unit terminal, MainPID/ControlPID zero, recorded PID absent,
  cgroup empty/absent, no model/dispatch receipts, and protected-host identity
  intact. The original GPU admission check requires GPUs2/7 at zero memory
  with no compute owners; nothing is evicted or signalled.
- Requiring both current claims byte-identical to the observed SHA-256,
  matching the failed block, original UUIDs, creation time and hold deadline.
- Writing a separate durable disposition intent, renaming each claim to
  `GPU-<uuid>.failed.<old-block-id>.json`, fsyncing the namespace, rechecking
  archived claim hashes and old guards, and writing a completion receipt.

The old `BLOCK_FAILED`, `BLOCK_LAUNCH`, six unit records and all source/results
are untouched. Claim contents are preserved, not shortened or overwritten.
Any mismatch prevents release; a partial filesystem failure remains recorded
in the disposition intent and is **not automatically retried**. No existing
queue helper performing these checks was found. The queue continues to read
only canonical UUID claim filenames; archival files are evidence, not active
ownership. Without this explicit release, the old claims remain effective
through **2026-09-19 14:19:47 UTC**, and new admission refuses them.

This release permits legitimate queue admission or Main's separately sealed
CPU proof. It does not authorize science in either failed or proof-only roots.
Model inference still needs Main's subsequent reviewed execution decision.

## Additional bounded reporting fix

Curie's reproduced accounting case is repaired: an existing
`INCOMPLETE_ZERO_TOKEN_GENERATION` cell retains its status, observed tokens,
hash and partial evidence while all six source/seed rows remain visible.
It is excluded from completed-cell rates; a full-budget result stays unknown.
Epoch/scene/seed mismatches still fail integrity checks. This changes reporting
only, not generations, extraction, judgments or the no-retry rule.
