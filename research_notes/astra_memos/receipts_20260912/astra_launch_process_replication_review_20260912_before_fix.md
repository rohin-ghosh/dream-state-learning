# Main process-replication launcher CPU review — September 12, 2026

**Result: API/receipt compatibility PASS; one reproduced timing regression FAIL (R1, medium severity).** No launcher edit. This is a bounded CPU fixture check, not a scientific approval gate or launch veto; Main retains all operator decisions.

## Exact tested bytes

- Main launcher `/tmp/astra_launch_process_replication_20260912.py`: `0539d5eb8ae6c0c71b14fc80ce461d08d78e37993b544af7b07ae119e34688ce` (rechecked unchanged after tests).
- Runner `/tmp/astra_rulegame_process_replication_20260912.py`: `96e27f5b8becaa59263f221206dc89a1b7d9a95eba8056810339556d8d9d11dd`.
- Collector `/tmp/astra_process_replication_collectors_20260912.py`: `fe80cfbbef70b2dc09b103d1de555eb7bdd359135be2bd9f59b9acc9d9bf39f8`.
- New owned tests `/tmp/test_astra_launch_process_replication_20260912.py`: `3f3593ace849cf5d2d183dcc051b413377cea98c43e3cbf424ea41b0c9889b31`.

**12 tests ran in33.177s:11 PASS,1 FAIL.** The failure is intentionally retained as a regression, not marked expected or weakened to make the suite green.

## R1 — recheck the full window after preflight, before spawning

At launcher`:54`, the1200/1800 controller plus300 collection margin is checked only before native-CPU-log reads/hashes, GPU vacancy preflight`:82`, and readout's prior-release archive/XML validation`:95`. There is no fresh time-window check before `Popen` at`:101`. Thus preflight can consume the spare time and the launcher still spawns without the promised full controller+collection window. The problem applies to either phase; the reproduced fixture uses write.

Regression `test_window_rechecked_after_slow_preflight_before_popen` at test`:236`: the first check has1501s remaining (write requires1500s). Mock vacancy preflight advances the clock2s. Only1499s remain, but `Popen` is still reached and a launch receipt is written. Expected refusal is not raised. This does **not** assert that an actual native launch exceeded a deadline; it demonstrates the missing final check at a boundary.

**Smallest correction for Main:** after all potentially slow preflight (including real `collector.write_release`) and immediately before spawning, resample the clock and repeat the same strict `now + cap + 300 < min(deadline, lease_cutoff)` requirement. Refuse without `Popen` when it fails. Refresh `started_utc` and `expected_custody_end_unix` from that launch-time sample rather than retaining a timestamp from before prior-release validation. No clipped controller, retuning, combined pipeline, new scientific gate or changed budget is needed. Keep any partial launch metadata rather than overwriting/retrying automatically. This worker did not apply the correction.

## Passing interface/custody checks

- Both phases and both FIT seeds exercise **real launcher `main()` argparse and branch dispatch**, with actual pinned runner `checked_plan` and actual collector `settings`, `bind`, `status`, and readout `write_release` validation. Complete CPU reference-write/capsule fixtures supply real schema-compatible prior-release receipts and archive hashes, not arbitrary fabricated success flags.
- Resulting `launch.json` passes collector binding for write seed0/1 and readout seed0/1. The emitted controller command is also passed through the runner's actual parser; it dispatches `write_pair` or `evaluate` with the expected root/hash/opt-in and correct seed. Native methods at that dispatch boundary are mocked, not executed. Prior runner tests cover emitted worker commands separately.
- **Main's root/launch_root fix is verified:** launcher`:95` supplies both exact keys plus seed/path/hash to actual `collector.write_release`. Its path, capsule hash, final-release XML/UUID, bounded/full-release/status/seed/write-plan checks execute in the CPU fixture. No missing-key or protocol mismatch occurs.
- Correct phase order and caps: P/A write, OFF/P_ON/A_ON readout;1200 versus1800 controller,140 cleanup,600 workers,300 external collection. `automatic_next_phase=false`. No automatic combined pipeline or implicit phase progression. Prospective aggregate remains1200+300+1800+300=3600s/60min per seed; R1 concerns preservation of that requested margin at launch, not a budget change.
- Missing opt-in/required CLI arguments, write carrying prior-release flags, absent readout release path/hash, wrong hash, wrong-seed/incomplete/unbounded release, wrong write-plan binding, initially insufficient controller+collection window, preexisting run or launch, missing/wrong-count/failed native logs, source/device mismatch, and GPU refusal all reject without spawning.
- Popen command/cwd/offline environment, exact unresolved interpreter spelling, new-session flag, fake PID/PGID and printed launch hash versus written receipt are checked. Native log paths/counts are exercised using synthetic27-test and19-test content; no live native log content is read.

## Reproduction and limits

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
CUDA_VISIBLE_DEVICES='' ASTRA_SOURCE_ROOT=/data/home/rohing/dream-state \
python3 -B -m unittest discover -s /tmp \
  -p test_astra_launch_process_replication_20260912.py -v
```

The test pins launcher bytes at import; Main's corrected launcher will require an explicit new tested hash before rerunning. No silent acceptance of changed launcher source. `check_free`, `Popen`, `getpgid`, native log reads, and the native home/source location are mocked. The exact native SOURCE_ID path components are checked while mapped to the CPU fixture's local source tree. Frozen dependency hashes are checked; module instances with existing CPU mocks are reused. Mock training/collection fixtures may create ephemeral temporary files, but no model/tokenizer-native calls, process launch, live GPU query, network/SSH/Git, repository/launcher/runner/collector edit or live sequential-run outcome inspection occurs.

I authored the replication runner and related driver/collector work. This is author-side API regression testing, not a fresh-author scientific outcome review. Only the assigned test and this review were authored. **EDITSTOP for these tested artifacts; R1 reported immediately to Main.**
