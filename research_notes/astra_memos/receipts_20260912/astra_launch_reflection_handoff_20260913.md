# Reflection launcher — September 13, 2026 UTC

**EDITSTOP. CPU mocks only; no launch or native/GPU/network/Git operations.**
Only the three newly assigned launcher/test/handoff files were created. Existing
runtime, corpus, source snapshots, helpers, historical files and runs were not
modified. No WebFetch, curl or wget was used.

## Final hashes

```text
56fef18cf9102721548e769100e8368c3432d484fade1e564ad074743165841b  /tmp/astra_launch_reflection_fit_20260913.py
97c97ed753638a33b1b5117d166f8ad789bf26ac1087f7e57c91a83ad82ade18  /tmp/test_astra_launch_reflection_fit_20260913.py
```

The handoff's own hash is returned separately, not recursively embedded.

## Validation

```bash
python3 -B /tmp/test_astra_launch_reflection_fit_20260913.py -v
```

**21 tests pass** (final run: 0.228 seconds). `--help` also succeeds. All helper
and controller subprocess calls are mocked; the fixture scripts deliberately
raise if executed. `/proc` identity parsing is tested with mocked bytes, not a
real detached controller. Tests write disposable fixtures only under `/tmp`.
These are launcher tests, not Noether's runtime acceptance or native evidence.

## Corrected lease invariant

Main's pre-EDITSTOP correction is implemented exactly:

```text
now + 3600 controller + 180 collection + 40 additional cleanup reserve
    + 21600 six-hour post-finish margin <= lease_end

required remaining lease = 25420 seconds
reserved finish offset = 3820 seconds
minimum margin AFTER that reserved finish = 21600 seconds
```

The gate runs before precheck, again after precheck, and immediately before
spawn. Precheck duration therefore consumes the available lease window rather
than silently consuming the six-hour finish margin. The exact 25,420-second
boundary passes with a fixed fixture clock; 0.001 seconds below fails. A further
test advances the clock during precheck and requires rejection before spawn.

The extra40-second lease reserve is conservative and intentional per Main:
the controller itself still has a3600-second ceiling including its40-second
cleanup reserve. Collection remains a separate180-second command. No runtime
budget was edited and the launcher never starts collection.

## Launch contract

- Explicit `--allow-gpu` is required before even validating files or invoking
  precheck. There is no implicit launch, retry, network operation, or lease change.
- Requires full final SHA256 pins for runtime, prepared plan, and allocation
  precheck. Rechecks all three after precheck and validates bound root/runtime,
  exact prepared interpreter, reflection scope, eight stages,144 calls and
  the3600/180/30/600/300-second plan limits.
- Refuses started, failed, completed, pending, symlink-containing or already
  claimed roots, including an existing empty `run/`. A successful preparation's
  `prepare_started.json` is allowed. An exclusive `launcher_started.json` prevents
  concurrent launchers from both proceeding. The controller still has its own
  exclusive start marker. Failed launch attempts remain terminal; retain evidence.
- Stdout must be a nonexistent file with an existing nonsymlink parent chain.
  Existing files, dangling symlinks and symlink parents are rejected. Stdout must
  be disjoint from the prepared root, runtime, precheck, launcher, source, model,
  worker-log directory and bound public helper. Exclusive `O_NOFOLLOW` creation
  prevents replacing another writer's evidence; the new file has mode0600.
- Runs the explicitly pinned allocation/vacancy precheck afresh with
  `CUDA_VISIBLE_DEVICES=''`, offline environment flags and a60-second timeout.
  Preserves helper stdout/stderr/return code; nonzero or timeout prevents spawn.
  No stale receipt is accepted instead of a new helper invocation.
- Detaches the exact prepared Python interpreter and final runtime's `controller`
  command using `start_new_session=True`, stdin `/dev/null`, and merged output
  to the exclusive log. The controller receives the planned GPU UUID and
  unchanged offline/deterministic environment settings adapted from perception.
- Success requires a live isolated PID/PGID/session and exact Linux `start_ticks`.
  Returns and saves command, pins, PID, PGID, start ticks, GPU identity, stdout,
  launch time, lease/finish reserves, and structured controller/collection/cleanup
  ceilings in `launcher_detached.json`. It never reports a scientific result.
- The ceiling is the approved pinned runtime's internal controller budget,
  measured from runtime controller entry, not an invented absolute wall-clock
  deadline measured before Python startup/precheck. This launcher adds no second
  supervisor or timeout wrapper.
- If detachment occurs but identity/receipt capture fails, `launcher_failure.json`
  records the known PID/command/pins and `controller_may_be_running=true`.
  Main must reconcile it; do not retry, infer GPU release, or kill an unverified
  process. This launcher does not signal potentially foreign processes.

## Main's final prepared inputs

Main reports native preparation succeeded at final identifier `098d023a` and
selects helper `59874c` from the frozen perception snapshot, not the stale `/tmp`
native helper. These are Main-reported abbreviated identifiers, not invented
full hashes or independently repeated acceptance. Preserve Main's final runtime,
plan and helper selection; Noether owns runtime acceptance.

There is no helper default or fallback in this launcher. The plan's public
helper path remains unchanged. Independently, `--precheck` must point to Main's
final allocation-check CLI accepting `--gpu-index` and `--gpu-uuid`, with its
full final SHA256. Do not substitute an unpinned or stale `/tmp` helper.

## Main-only invocation — not executed here

Use the exact interpreter recorded in the successful prepared plan. Supply
full64-character pins, a fresh exclusive stdout pathname, and the final frozen
allocation-check path. The prepared root must not already be launched or failed.

```bash
"$PYTHON" -B /tmp/astra_launch_reflection_fit_20260913.py \
  --root "$ROOT" \
  --driver "$FINAL_REFLECTION_RUNTIME" \
  --driver-sha256 "$FINAL_RUNTIME_SHA256" \
  --plan-sha256 "$FINAL_PLAN_SHA256" \
  --precheck "$FINAL_ALLOCATION_PRECHECK" \
  --precheck-sha256 "$FINAL_PRECHECK_SHA256" \
  --stdout "$FRESH_CONTROLLER_STDOUT" \
  --allow-gpu
```

Retain returned JSON plus `launcher_started.json`, `launcher_precheck.json`,
`launcher_detached.json` or `launcher_failure.json`, and controller stdout.
Only the runtime's complete unscored capture receipt can enable its separate
collection command. Launcher success alone is not runtime completion.

**EDITSTOP — final corrected finish-margin gate tested; no launch performed.**
