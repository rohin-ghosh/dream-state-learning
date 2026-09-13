# Main process-replication launcher CPU review — R1 recheck, September 12, 2026

**PASS — same12 tests pass in34.512s, including the unchanged R1 regression. EDITSTOP.** No remaining required fix identified in this bounded launcher API/window test scope.

**Priority/status: process-replication prepared plans remain UNLAUNCHED regardless of this result. Rohin steered birth-first.** This is verification of Main's known routine timing repair, not resumption of the former scientific priority, launch authority, scientific promotion or a new approval/C11 gate. Main retains all scheduling/operator decisions.

## Exact current tested bytes

| Artifact | SHA256 |
|---|---|
| Main launcher `/tmp/astra_launch_process_replication_20260912.py` | `3d03f4867bcfb2a6f2d152ea5f0f29d11d9e3cb7de2187df6240f48d7e2e9aac` |
| Owned tests `/tmp/test_astra_launch_process_replication_20260912.py` | `e303f811911c510c9bd6437beecb03555ac0170df3567486e62c3383c80fd936` |
| Unchanged runner `/tmp/astra_rulegame_process_replication_20260912.py` | `96e27f5b8becaa59263f221206dc89a1b7d9a95eba8056810339556d8d9d11dd` |
| Unchanged collector `/tmp/astra_process_replication_collectors_20260912.py` | `fe80cfbbef70b2dc09b103d1de555eb7bdd359135be2bd9f59b9acc9d9bf39f8` |

## R1 disposition

The only launcher source difference inspected is Main's five-line insertion immediately before Popen: sample fresh `now`, require `now + cap + 300 < min(deadline, lease_cutoff)`, then refresh `started_utc` and `expected_custody_end_unix`. This occurs after native-log reads/hashes, GPU preflight and readout prior-release validation. Original stage caps1200/1800,300s external collection and separate phase operation are unchanged.

The **unchanged** `test_window_rechecked_after_slow_preflight_before_popen` at test`:236` now passes: initial1501s remaining, simulated2s preflight, only1499s left for the required1500s write+collection window; launcher raises ValueError and Popen is not called. Main's code inspection additionally confirms the launch/custody timestamp refresh. No native timing or deployment behavior is claimed from this CPU fixture.

The tests differ from the pre-fix version **only in the single LAUNCHER_SHA constant**. No assertion, fixture, regression or test count was relaxed. The exact12-test discovery pattern excludes the preserved historical `_before_fix.py` file, whose old import-time pin intentionally does not match the current launcher path.

## Preserved failure evidence

Exclusive `_before_fix` copies were created and verified byte-identical before rebinding the test hash:

- `/tmp/test_astra_launch_process_replication_20260912_before_fix.py`: `3f3593ace849cf5d2d183dcc051b413377cea98c43e3cbf424ea41b0c9889b31`.
- `/tmp/astra_launch_process_replication_review_20260912_before_fix.md`: `c2d5b7c1ed112ffe0c7d574489488329dd57b4e4e3e168c9a0ca38ab1f783010`.
- Main-preserved old launcher `/tmp/astra_launch_process_replication_pre_window_fix_20260912.py`: `0539d5eb8ae6c0c71b14fc80ce461d08d78e37993b544af7b07ae119e34688ce`.

Historical result remains11/12 passing in33.177s with R1 failing; it is not rewritten as a pass. Main authored the launcher correction. This worker edited only the owned tests/review and the explicitly authorized `_before_fix` copies.

## Passing coverage retained

- Real Main launcher argparse/dispatch for **write/readout × FIT seeds0/1**, actual frozen runner checked_plan and collector settings/bind/status. Generated launch.json matches collector phase, seed, plan, source, interpreter, command, caps, member order and UUID contracts. Emitted controller commands additionally enter the real runner parser and select the correct phase handler/root/hash/seed/opt-in.
- Readout prior-release validation executes actual collector logic against bounded mock-written and mock-collected capsules; root/launch_root config keys are present and correct. Missing/wrong release path/hash, wrong seed/plan and incomplete/unbounded release reject without spawning.
- Required CLI arguments/opt-in, prior-release flags on write, initial insufficient full window, preexisting run/launch, missing/wrong-count/failed native logs, source/device mismatch and GPU refusal reject without spawning. Post-preflight window regression now also passes.
- Popen argv/cwd/offline environment/new-session flag, unresolved interpreter spelling, fake PID/PGID and printed-versus-written launch hash agree. Separate1200+300 write and1800+300 readout budgets remain <=60 aggregate minutes/seed; no implicit next phase or combined coordinator.

## Reproduction and scope

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
CUDA_VISIBLE_DEVICES='' ASTRA_SOURCE_ROOT=/data/home/rohing/dream-state \
python3 -B -m unittest discover -s /tmp \
  -p test_astra_launch_process_replication_20260912.py -v
```

`check_free`, Popen, getpgid, native acceptance-log reads and native home/source location are mocked. Exact SOURCE_ID path components are checked while mapped to the CPU fixture source tree. Dependency hashes are verified and existing CPU fixture module instances reused. Native handler work at emitted-command parser dispatch is mocked, while the parser/dispatch itself is real. No actual native/model/tokenizer call, process launch, live GPU/resource query, network/SSH/Git, repository/launcher/runner/collector edit, live native-log read or sequential-run outcome inspection occurred. Ephemeral mock training/collection files are test fixtures only.

I authored the replication runner and related driver/collector work; this is author-side API regression testing, not fresh-author independent science review. **EDITSTOP. Plans remain UNLAUNCHED; birth-first priority unchanged.**
