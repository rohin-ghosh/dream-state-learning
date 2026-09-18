# Explicit PRELOAD_PARENT_QUEUE authorization

Rohin/Main, September 18, 2026, exact directive:

> Need implement explicit bounded PRELOAD_PARENT_QUEUE mode, not fake LOAD or weaken live endpoint. User20:26 authorizes queuing parent turn now. Separate one-shot helper validates same original journal, exact retry PID699464/start33078516/source/guard, preserved COMPLETE+head, no inference LOAD, single publisher lock and unchanged original provider/policy/ledger; generates ONE xhigh parent turn from authenticated preserved child output and downtime context, publishes via existing console API as parent with queued-not-rendered receipt. Native retry inherits inbox. Keep normal live endpoint unchanged. CPU tests and attribution required; source exact actual/history distinction. No duplicate native/replay, no guards/security bypass, no presumption of delivery.

Non-material CPU parent transport mode, explicitly authorized. The earlier
blocker note incorrectly attributed a prohibition on application gate changes
to the user; only provenance/security invariants were prohibited from bypass.
The corrected mode does not forge a LOAD binding or modify the live endpoint.

One local original-ledger provider attempt, maximum600 seconds, original xhigh
provider/config/policy/seed/turn history and single-parent lock. Authenticated
snapshot is bound to preserved head and COMPLETE5243/sleep153. Provider input
explicitly labels the preserved failed-tail outputs historical and the recovery
gap as having no verified new inference, feedback or parenting cadence.

The new CPU endpoint retains host/user, exact PID/start/source/guard/source-pin,
same-journal, complete/recovery/head integrity, no-LOAD, isolation, word/byte,
lease and original publication-lock checks. One durable publication intent
prevents automatic duplicate publication. It uses the existing parent console
API and reports queued, never rendered. No native signal, restart or replay.

[Builder] 2026-09-18 20:38 UTC — Focused exact-identity, no-LOAD, changed-head,
immutability and dead-native regressions added to the retry CPU suite. The
normal post-LOAD parent waits only for this explicit one-shot parent writer to
finish; the learner is never held. Existing live endpoint remains unchanged.
