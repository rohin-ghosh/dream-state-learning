# R205 reported lease update — 2026-09-18 03:42:01 UTC

The user confirms node5's extension and cancels the earlier emergency interpretation. This is **user-reported provenance, not CLI/provider verification by this audit**.

| Node | Reported local expiry | UTC equivalent | Verification / audit action |
| --- | --- | --- | --- |
| node5 | September 21, 2026, 21:04 PDT | September 22, 2026, 04:04 UTC | User extension confirmation. Emergency interpretation cancelled. Existing read-only audit continues; Descartes remains sole operator. |
| node3 | September 25, 2026, 20:03 PDT | September 26, 2026, 03:03 UTC | User reports active; Copernicus verifies the authoritative host-bound receipt. Not yet added to audit or contacted. |

PID2656637 remains identity-verified at the timestamp above: UID158984/start ticks180945900 and command hash match; cadence1,200 seconds. Nodes1/2/4/5 remain enabled. No hardwall was updated from an unverified expiry report, no lease was created or extended, and no process was killed, signaled, restarted, or reconfigured. Main's off-node copies remain insurance, not evidence of a continuing emergency. Machine-readable provenance is in `LEASE_PROVENANCE.json`.
