# Node4 owned status — September18 17:38UTC

| Life/component | Actual liveness/delivery | Loaded deadline / pending renewal |
| --- | --- | --- |
| P7 native | PID1100592/start28670738 alive17:32:30; uninterrupted, no signal | Native18:00UTC today; outer timeout about17:59:49UTC. New September25 18UTC native bound NOT loaded. |
| P7 sole overseer | PID2805259 live17:38:33. Parent58 INBOX b20a4620d6cb445f96d78dfcaeb28e3d rendered REQUEST6510 SHA430c15f6ee9e63649f8a54b1b04c07f2037c715b94a05eef4cbc5797e8af54c1. Parent59 published17:32:54.302318UTC, render pending. | Existing CPU18:00UTC. Successor2996247 waits for exact predecessor185812216 start-ticks to exit naturally; configured September25 18UTC. Not active parenting yet. |
| Astra7 native, Jason owner | Actual renewed receiver checks PID762967/start98059264, LOADED3128/17:26:46.873724UTC, SHA1454621c60943dea4399858b30ee195418f4406e2201c19e5a891965621e28f1 | Actual native September18 22:59:36.105072UTC. Untouched. |
| P7/Astra7 CPU bridge | PID2996246 live17:38:33, same old coordinator lock, prospective P7 frontier6555. Receiver imported/hash verified; no new roundtrip yet. | Minimum of own new CPU lease bound and actual child native budget: September18 22:59:36.105072UTC. Every call still verifies current native identity; P7 native expiry remains a blocker after18UTC. |
| C2 read-only | Native3624513/start25171256 alive17:32:58, source orch_r222_C2_20260918_discussion2/source | Actual September19 00:00UTC, not user-authorized September20 18UTC. No writes/signals. |

Thirteen focused CPU regressions pass. Existing parent ledgers, old bridge
queues/cursors, child journals and training policies preserved. Forward ACT-only
restriction remains explicit; THINK/LEARN are not relabelled or endlessly retried.
Returned replies must match a new-epoch P7 publication in the actual masked child
REQUEST, not merely historical P7 context. No P3 actions or retirement action.

Recommendation is published in notebook commit181f9eab9; deadline/source receipt
in a221e2627. Prefer preserved retirement over indefinite reminders for the
current purpose, or one bounded genuinely renewed-child trial; awaiting Rohin's
choice without action. Language alone is not the failure and no exclusions change.
