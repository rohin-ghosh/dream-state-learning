# Main / Averroes: bounded-error repair readiness after01:48 resume

## Offline implementation ready September19 02:33UTC

Main accepted endpoint ownership; `projected_wire/` now contains the runnable,
owner-authenticated projected receiver and continuation gate.69 CPU tests pass
(26 new); a synthetic71,305,512-byte original window projects to4,089bytes without
changing the64MiB transfer cap or original parser/seen/epoch behavior. This is
offline only: no live deployment, restart, signal or new natural scorer receipt.
Exact sealed manifest, security assumption and queue/state continuity handoff:
`OFFLINE_PROJECTION_READY.md`.

## Updated September19 02:09UTC

All five now have fresh post01:48 natural failure -> Tool INBOX -> masked REQUEST
chains, including revision. Oversized-window scoring remains blocked: the live
receiver requires original full-byte mirrored ancestry and exposes no supported
authenticated projection route. Existing chunk staging already sends only the
last stage to its socket; the64MiB failure happens before staging/dispatch.
43 CPU tests pass, including14 new source-parity/tamper/receiver-contract tests.
No live mutations or signals. Full blocker/action-needed and exact fresh tables
are in `PROJECTION_BLOCKER.md`; machine-readable evidence is
`PROJECTION_READINESS.json`. Smaller windows have32 real scorer-service receipts,
but zero caption feedback results; do not call those successful judgments.

## Preserved01:51 audit (superseded by the update)

**Operational-error feedback is deployed and adopted; oversized export recovery remains blocked.**
No byte-bound, native, scorer, epoch, source-ancestry or training-target change. No historical ACT replay or synthetic request.

Read-only chain audit cut: September19 01:51:13.449592UTC.
Freshness is measured from reporter startup01:38:29.395381UTC. These are natural new source responses, not reissued old ACTs.
No source response after Main's01:48 resume is yet verified in this cut; do not present these as post-01:48 chains.

| Fork | RESPONSE → ACT → Tool INBOX → masked REQUEST | Failure UTC | Tool publication UTC | State |
|---|---|---|---|---|
| observation | 7936 → 7939 → 7959 → 7961 | 01:46:18.826398 | 01:46:37.852113 | Post-repair natural chain verified |
| perspective | 8314 → 8317 → 8326 → 8328 | 01:46:58.974026 | 01:47:07.370516 | Post-repair natural chain verified |
| revision | 7518 → 7521 → 7551 → pending | 01:38:30.111250 | 01:39:17.048210 | Older source; INBOX only; not a new complete chain |
| selfderive | 7080 → 7083 → 7092 → 7096 | 01:44:22.386437 | 01:44:35.069893 | Post-repair natural chain verified |
| unparented | 7635 → 7638 → 7659 → 7661 | 01:42:05.754618 | 01:42:26.853949 | Post-repair natural chain verified |

All notices explicitly say No judgment, scorer not contacted, and no rank/acceptance/zero score. The four complete chains have exact Tool text and `all_history_tokens_masked=true`.
The historical unparented name remains an R233 parented treatment, not a control.

The same-provenance minimum windows still exceed67,108,864bytes; the newest observation window is107,759,432bytes. No compatible shorter window was found, and the cap has not been raised or bypassed.

Reporter459421/start1006370, transport425470/start939654 and model provider330973/start764197 are unchanged in the real-host check. Node-local native incarnations, scorer499900, bridges448173/502015, Tool relay1970178 and all five epoch bindings reverified unchanged.

Supervisor399392 confirms reporter adoption at2026-09-19T01:52:35.678380+00:00: RUNNING_ADOPTED_NO_SIGNALS. Exact candidate installed as services.d/node3-operational-errors.json; held singleton preserved. No duplicate launch or signal. OS boot_enabled remains false.

**29 worker CPU tests pass**, including prevention of older verified receipts masking a newer pending failure. Inherited pytest remains unavailable; no package installation was performed.

Authoritative proofs: FRESH_OPERATIONAL_CHAINS_LATEST.json (plus immutable timestamped cuts), FRESH_REAL_HOST_VERIFIED.json, FRESH_SCORER_NATIVE_IDENTITIES.json, OPERATIONAL_ERRORS_ADOPTION_VERIFIED.json, FRESH_AUDIT_TESTS.txt.

Restart contract remains the single foreground report_transport_errors.py command and locks/OPERATIONAL_ERRORS.lock, with unchanged September24 17:59:20UTC deadline. This shared-repository note is not a claim of direct agent-message acknowledgment.
