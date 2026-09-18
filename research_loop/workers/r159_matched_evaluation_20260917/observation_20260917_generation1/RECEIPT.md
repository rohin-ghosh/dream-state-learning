# Candidate5 source observation — 2026-09-16 22:57:36 PDT / September17 05:57:36 UTC

Metadata-only authority SHA256 `7ee28a6b3d8297f3bd057bf552a1f653da3254f76d2b8e5848fecafc85eaf84a`; exact a40r host `[REDACTED_HOST]` and candidate5 cohort SHA256 `da04b4cd814f6f695ca49a1ace66f9378039f6166d04e26bbd27ed7692ad0b4b` verified. Observation interval 05:57:36.087130–05:57:36.298135 UTC. Reader scanned 6,658,530 bytes/871 files; transport returned 379,210 bytes, within 256MiB/16MiB authority. Ten CPU and actual-receipt tests PASS. Helper SHA256 `8aa6e968b811e6ddce355dce16c80ba0f7b7d62e691e16c3f68ee10cb760ffa8`.

All three original initial COMMIT byte strings are archived locally with mode0600; no adapter/checkpoint payload copied. Their metadata agrees with the preserved initializer: zero optimizer updates, unchanged original creation time, identical adapter file inventory/state and optimizer/RNG **hashes only**. Original freeze/runtime2/plan and all source bytes are unchanged.

| Arm | Initial COMMIT SHA256 | Retained journal records |
| --- | --- | --- |
| parented_learning | `1aa2785d58eb0ac98f7af799360f2334226977a8a3648ed61a6ccfffe6ccfc55` | 211 |
| parented_frozen | `68580b9e6f4db25d0bc8b5a2107eec7507863d617065ff8b3f6d7c352a97417c` | 14 |
| unparented_learning | `101dcf3bfdc327d664ee394374733d18f748800966b32e67925bf587e2d5628a` | 192 |

Each retained journal is contiguous, digest-chain/intent verified, with unchanged directory listing during its scan. All three contain BIRTH and LOADED. Frozen INITIAL_STATE_VERIFIED hash agrees with Main's `dc4ed41c887b15e6642ff17b571d0a38d24ea7c915fc80725258f4b063505b9e`.

## Exposure evidence, not fabricated exact timestamps

All times below are September17 UTC. Birth is bracketed by native INITIAL_STATE_VERIFIED and LOADED timestamps. BIRTH itself has no native event timestamp; its file mtime is preserved separately, explicitly **not** promoted to an exact event time.

| Arm | Birth bracket | First TRAIN request → response | Initial readout dispatch → clean custody close |
| --- | --- | --- | --- |
| parented_learning | 05:36:42.005839–05:36:42.358459 | 05:38:56.822934–05:39:22.143886 | 05:36:42.363386–05:38:56.815955 |
| parented_frozen | 05:52:48.064033–05:52:48.419945 | 05:55:03.205339–05:55:28.505539 | 05:52:48.424675–05:55:03.198719 |
| unparented_learning | 05:36:44.425602–05:36:44.793791 | 05:38:59.754536–05:39:24.794920 | 05:36:44.799191–05:38:59.744497 |

First TRAIN segment0 has both response and commit in every arm; a service start/publication is not used as delivered-exposure evidence. The frozen arm's first native TRAIN generation therefore precedes the later gym service start Main reported around05:56. This does not assert when its first gym task was rendered.

All three initial readouts have hash-bound OPEN/DISPATCH/CLOSED metadata, completion-marker-present=true, failure-marker-present=false. No held output directory/file/log was opened. Dispatch/open is an intent timestamp, not the first evaluated item's execution timestamp; clean closure bounds completion but does not provide that exact first-item time. These are original native readouts, not R159 enrollment/evaluation.

## Necessary source-owner disposition

The retained prefixes are complete and stable **as enumerated**, not proof against external history deletion or activity outside the recorded namespace; snapshots are sequential across live arms. Global `coverage_complete` stays false and first-exposure attestation stays UNKNOWN, never NOT_OCCURRED. Main/source owner must attest complete history through a specified common observation cutoff, bind original unused-saved-initial custody, and supply or explicitly adjudicate event-time evidence for BIRTH and first evaluation. Do not place file mtimes, publication/start times or guessed first-item times into exact `first_unix` fields. Current R159 has no interval-valued timestamp schema; no evaluator rule was changed here.

Parent-safe detailed receipt `OBSERVATION.json` SHA256 `acff2dfecb88fbcb1839c91ee3da825cc0696b257d28bd03ac2926cd222bfea5`; concise `SUMMARY.json` SHA256 `adb88207bf922463e52ab053c7b247d2ddd2f4cb371e384b8e4b87ac477d8cce`. Raw original COMMIT archives/transport remain private local metadata artifacts; do not dump them into parent messages. No source writes, adapter or optimizer/RNG payload reads, held contents, source/input installation, enrollment, GPU calls, child/parent/service changes.
