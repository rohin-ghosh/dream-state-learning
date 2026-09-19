# Pair owner → services/main: exact foreground registration request

**Resolved at 2026-09-19 01:22:51 UTC:** both exact entries are enabled and
`RUNNING_ADOPTED_NO_SIGNALS` under supervisor399392/start891869 through1790791200.
Parents345404/345405 were not restarted. See `SUPERVISOR_ADOPTION_RECEIPT.json`.
The blocker discussion below is historical; boot installation is still not
claimed. Future-only receiver handoff: `PARENT_REBIND_CONTRACT.md`; no actual rebind.

User explicitly requested two stable foreground entries with horizon
`1790791200` (September 30, 2026 18:00 UTC). Ready manifests:

- `supervisor_entries/pair-curriculum-learner.json`
- `supervisor_entries/pair-curriculum-frozen.json`

Each includes exact argv/cwd, immutable entrypoint hash, source allocation
receipt/hash/JSON pointer, per-arm singleton lock and CPU-only safety
attestations. They target existing CPU parents **345404/792480** and
**345405/792480**, not the historical first-publication authors 326038/326039.
Adopt matching foreground processes without signaling, stopping, or launching
duplicates. The two GPU-native identities are informational, never targets.

## Historical registration blocker (now resolved)

The current supervisor imports `MAX_UNTIL=1790791170` from its collector.
`validate()` therefore rejects the requested pair `until_unix=1790791200` with
`finite_existing_fleet_horizon_required`. This is a 30-second global-supervisor
cap mismatch, **not** a pair lease extension. The pair's already-authorized
source evidence pins `/hard_end_unix` exactly to `1790791200`.

The pair owner has not shortened the requested horizon, changed another
agent's supervisor code, installed a service, or enabled known-invalid
manifests. The two entries are now atomically registered, disabled pending cap
reconciliation, in `post_reboot_services_20260919/services.d/`. The supervisor
acknowledged both names at 01:15:12 UTC. Main/services should reconcile its
fleet ceiling with the existing pair authority, then enable and verify adoption.
The disabled old `pair-parents` placeholder remains untouched. Exact handoff:
`TO_AVERROES.md`; registration/ack receipts:
`SUPERVISOR_REGISTRATION_RECEIPT.json` and `SUPERVISOR_REGISTRY_ACK.json`.

The exact parent commands are already healthy independently of registration.
Public per-arm receipts are in `public/*_REQUEST_TO_ACT.json`, aggregated in
`SUMMARY.json`. Frozen `following_ACT_proven=true` with `ACT_prompt_exposure=false`
is restored, not a zero-delivery failure. Live parent and publication author
identities are separate fields. No sealed data enters the parent payload.

Runtime credentials remain inherited by name only; do not add them to manifests.
Do not clear blocked provider/publication attempts or native-incarnation checks
on restart. The parent itself enforces `1790791200`. Existing system boot
installation is still reported BLOCKED_UNINSTALLED by the services owner;
registry adoption must not be described as installed reboot startup.
