# Node-1 long-life integrity snapshot

Date: 2026-09-11 16:54 UTC

Status: read-only simple-hygiene audit. This is not a terminal scientific
receipt, does not alter any live run, and does not finish or enforce the C11
guard.

## Classification

- `R4_B_seed604` was genuinely progressing. Its ledger changed during the
  audit; it had reached nominal wake 1016/1024 and 31 terminal sleep states.
- `R4_B_seed605` was genuinely progressing. It had reached nominal wake
  832/1024, 26 terminal sleep states, and fresh probe/reload activity.
- `R4_B_seed606` was cleanly terminal: `LIFE_DONE`, 128 wake files,
  reconstructed episode count 1024, 32 terminal adapter states, final ON/OFF
  probes, and no live process. It was already included in the terminal-union
  audit and bound selection receipt.
- `R5_B_seed701` was genuinely progressing. It advanced from wake 168 to 176
  during the audit and had five committed sleeps. It remains an exploratory
  R5-loose mechanism life under its disclosed tolerance and report-contact
  canary.
- `RP_B_seed402` was stale/wedged, not cleanly terminal. A parent PID remained
  with only a resource-tracker child, but no artifact had changed since
  2026-09-10 03:55 UTC and there was no `LIFE_DONE`. Although it had 128 wake
  files, a sleep-1024 state, and final ON/OFF probes, its reconstructed episode
  count was 1048 rather than the nominal 1024. Sleep 832 recorded training
  `rc=-9` without an adapter terminal marker, and the post-final model reload
  failed for insufficient available GPU memory.

## Evidence rule

`RP_B_seed402` must not be promoted to the clean terminal parenting pool. It
may be retained only as legacy exploratory/failure evidence with the episode
count mismatch, missing sleep-832 state, reload traceback, stale timestamp,
and absent `LIFE_DONE` disclosed. Restarting it or adding a marker later would
not repair the historical lineage.

The remaining active lives continue unchanged. Terminal closure requires
matching nominal and reconstructed episode counts, every sleep in a terminal
state, final ON/OFF probes, `LIFE_DONE`, process exit, and a refreshed receipt
binding the relevant gates, canaries, adapters, and parent briefs.
