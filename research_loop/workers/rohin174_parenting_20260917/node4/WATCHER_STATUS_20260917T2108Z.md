# Main / watcher: verified NODE4 status after control withdrawal

Observed September 17, 2026 at 21:07:53 UTC. Main withdrawal receipt SHA:
`da4145a7f976d47f63c4af3ddc2ec72056a76706be79e7325f261eda442e7217`.
It supersedes the queued/PUBLISHED-pending classification of the sole H message.

| Physical / arm | Live parent PID | Current publications | Verified rendered deliveries |
| --- | --- | --- | --- |
| 0 / B walkthrough every2 | 489577 | 2 | 1 |
| 3 / D light steer every3 | 489578 | 0 | 0 |
| 4 / A strict dense every1 | 489576 | 0 | 0 |
| 1 / raw control, H OFF | None | 0 pending; 1 historical publication withdrawn before ingestion | 0 |

B's first delivery is publication `612cb544b9344a23b3d9a789333e3f23`,
TRAIN REQUEST4813 at **21:00:10.680862 UTC**, request ordinal122, sleep baseline40.
Its three/four completed-sleep targets are43/44; no completed sleep after first
exposure is yet observed. B's second publication
`60e48df47d544f9cad77e6b61b13d1d9` is not yet rendered. D/A continue awaiting
rendering of predecessor invitations; those are not new R175 deliveries.

## Raw control remains unparented

No H operator or in-flight H attempt remains. The only historical publication
ID is `11a39e52e43540f8839c312cf64e86ff`, verified withdrawn before ingestion by
Main. No replay, republish, or delivery recovery is permitted. Historical failed
attempts, publication receipts and the withdrawal receipt are preserved.

Raw1's root remains
`/localhome/local-rohing/orch_r136_raw_unparented_a40r1_20260916_attempt1/run1`.
Native294158/start24386173 is advancing in the unchanged R179 native guard:
the hash-linked journal extends Main's anchor5038 to5041 with three UPDATE
records; CPU ticks increase by120 across the 1.2-second sample at21:06:44–46 UTC.
No withdrawn-message INBOX ingestion appears in that verified suffix. This
worker reads no inbox files and sends no native signals during verification.

Exact raw progress and no-H census evidence:
`RAW_CONTROL_VERIFIED_1789679206164042548.json`.
Combined delivery, environment and child receipts:
`RECEIPTS_AFTER_WITHDRAWAL_20260917T2108Z/RECEIPT_000000.json`.

All four learner identities are alive with exact R179 loaded/subsequent-generation
receipts. Existing retained-sleep proof monitors remain alive, with zero completed
retained-sleep-plus-postsleep proofs yet recorded. No retention inference from
publication or rendering. No peer pair, executor connection, cap change, native
restart, recipe change or physical2/5/6/7 allocation change.
