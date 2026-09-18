# NODE1 second actual successor — September 17, 2026, 11:15 PDT

**teach_perception / lane3 is now actually LOADED.** This supersedes only the
lane3 dispatched-not-loaded status in `STATUS_20260917T1812Z.md`; that earlier
receipt remains unchanged. Current coverage is **two loaded, three armed, one
verified already-compliant no-op**. No fleet-wide count is inferred.

## Actual load and receiving custody

- Runtime load was observed at **2026-09-17T18:13:27.675430Z / 11:13:27 PDT**.
  Actor PID **1780287**, start ticks **38980819**.
- Actual source root:
  `/localhome/local-rohing/orch_r179_node1_20260917_attempt2/lanes/lane3/source`.
  Native SHA:
  `0744a34c62c2863cd3a960f2691588db3ffb105fea242f169285ae7badd47737`.
  Policy SHA:
  `b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b`.
- Resume is bound to saved sleep **42**, optimizer steps **4505**, adapter
  state SHA `7b52d9d4cbb554bb5325e8791497296477d40f46854b41f7e2c9194a08199af5`.
  Full saved stream SHA:
  `818cdee5749254f685727c965ba47a00f883a78c6d9aefd55bb1425a776f0baa`.
  Actual receiving CPU proof SHA:
  `2a213d394303db3631faa5c63cf6d2f6ac6231e657e8b53f035e5f1f2238b3b5`.
- Actual privileged admission is clear, scanner EUID0, no blockers; SHA:
  `b1185356e90ce9a634dfa47ff3b5303fccbc722718fc77a5578c06588a9c480c`.
- Remote `lanes/lane3/LOADED_RECEIPT.json` SHA:
  `40ebb03a0e13bf50bf83a14ad2c944559dadff30dff6260e9c026e729f48adaa`.
  Underlying LOADED journal record SHA:
  `6e7d918f4344ac595f3808d3566cb961b8fc0426e8971f201c6711c27cb5d5b4`.

The independent 18:15:02Z bounded observer freshly matches actor PID/ticks and
source, verifies both actual native/policy bytes against the guard, and verifies
the post-handoff journal prefix through5175. It observes LOADED and INBOX, **no
new COMMITTED, CONTEXT_RETAINED or post-R179 completed sleep yet**. Saved sleep42
was the original process's boundary; it is not a new R179 completed-sleep claim.

## teach_parenting and remaining waiters

- **Lane4 / teach_parenting:** still the first loaded successor, actor1418920
  with ticks/source freshly matched at18:07:34Z. Cycle42's actual retention
  marker and saved request remain proven: 2523/12288 visible/threshold tokens,
  333 raw events and unchanged history SHA
  `e6504d493e7cdbb9ea79d16aed5507cced0adb44c27658ea4893df8d45a1394a`.
  At **18:15:54Z** a small verified suffix through5071 contains only further
  UPDATEs, latest optimizer step4466. **No new completed sleep or post-sleep
  prompt-history custody yet.** The suffix read10555 bytes rather than another
  full22MB history observation.
- **Lanes2/5/6:** independent original90-minute waits remain live and have not
  retired, dispatched or loaded successors. Deadlines remain respectively
  **11:52:34, 11:52:46 and 11:52:52 PDT**. No failures or expiries are observed.
  The original actor/timer/supervisor metadata matches staged ownership.
  No live watcher was duplicated or shortened into a20-minute failure loop.
  Main's explicit clean-expiry, no-signal rearm authority is recorded in
  `STATUS_20260917T1812Z.md`; no expiry/rearm has occurred yet. A future rearm must
  preserve old attempts, immutable prepared sources, exact owner revalidation
  and the unchanged original wall, without native/readout replay.
- **Lane7:** already-compliant no-distillation source proof; no restart.

## Current evidence paths

- `EXECUTION_STATUS_1789668887885282065.json`, SHA
  `c8212bd75a6bd789c36f336ea5f0babfe412a23bc107ff99c9b511ac6b9afd67`.
- `CONTEXT_CUSTODY_LANE3_1789668902570180605.json`, SHA
  `628e86328b1bd4a0b08d923587bb03234d59accf4ac419f42817c93f123478bb`.
- `CONTEXT_CUSTODY_LANE4_1789668454690232956.json`, SHA
  `b2742287cb9298a766c536ac2240810065d50f86ece50341df19f6582c425b44`.
- `LANE4_SLEEP_SUFFIX_1789668954439578904.json`, SHA
  `a0967c71be39cbfd5499fe8c70e3c0f0536d3471eef14dbb4a5cd03f0999b2e5`.
- `WAITER_PROGRESS_1789668560910047151.json`, SHA
  `1c2f751b3ba4189f5caa06e7b9159136412ef5d0ed01b28a451cf060e02b23be`.

The observer uses the unchanged node1 code with11 prior passing CPU tests;
this report introduces no shared native/policy/test edits. Existing saved-state
machinery executed the lane3 handoff, with full stream/checkpoint preservation
and no new readmission/retry. Both R164 probe channels are untouched and remain
separate from Main's R176 authorization. No sealed output, evaluator scores,
maps, key files or parent messages were opened/sent; no COORDINATION edits.
