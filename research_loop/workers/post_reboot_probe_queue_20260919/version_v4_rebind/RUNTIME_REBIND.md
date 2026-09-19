# Immutable V3 to V4 scheduling rebind

Main authorized this CPU-only non-material repair on September19,2026. No
activation or GPU launch is authorized to this worker. No capture rebuild,
scientific source change, model/metric change, new job identity or lease extension.

The prepared sleep24 root and its original runtime are immutable predecessors.
New runtime/config/capsule/evidence live in its sibling `runtime_v4/` directory.
The old `inputs/capsules.json` stays unchanged; the replacement is the separately
created `inputs/capsules_v4.json`. Only this capsule's runtime pointers/hashes
change. All103 science files, input file hashes, source journal/cut/epoch, job ID,
adapter identity, scenes/seeds/6144-token battery, judge/control, fixed GPU2/7
UUIDs, parent blindness, policy and finite horizons are inherited without change.

The config carries exact predecessor config/capsule/registry pins. Every bundle
verification validates those pins, predecessor runtime bytes, and equality of
every config field except the explicitly changed scheduling runtime fields.
The old capsule/bundle evidence and captured exposure evidence remain authentic
and byte-identical; they are not relabelled as a new model or epoch.

CPU staging holds the existing original DISPATCH.lock via a read-only descriptor;
it writes no claims or launch markers. Any same-job/source attempt in any runtime,
scientific output, previous-attempt inventory, even an expired same-job claim,
or existing queue state blocks this one-time rebind. Existing/partial sibling
bindings are never overwritten or automatically retried. Stage does not run the
source-epoch observer. --verify checks completed immutable staging read-only.

The foreground observer uses the original durable queue state path and preserved
history. It warms its own process-local proof cache in bounded cycles before any
intent; no separate startup observer or standalone expensive source scan is
needed. Actual GPU occupancy, claims, protected processes and source/lease checks
remain required at admission. Registry/config pointers persist in durable intents
so reboot/crash reconciliation reads the selected runtime, not stale V3 files.
Unknown attempts stay no-retry; complete/scoring-shortfall policy is unchanged.

The dispatcher cold-validates within300 seconds and the original intent deadline.
It requires more than360 seconds remaining before role submission: at most300
for each concurrent role's independent cold validation plus60 remaining for
execution. Full completion is not predicted or guaranteed by this minimum.
Role START_INTENT (actual PID/start/argv and device confinement) is durable BEFORE
cold validation so reconciliation sees the pending CPU role. Each bounded batch
rechecks protected identities and the original deadline/lease. No proof or model
load after warmup may extend the original2400-second job deadline; original
transient units retain RuntimeMaxSec at that same absolute deadline. An overrun
or unknown outcome still fails/pauses/no-retries rather than resubmitting.

V3 and the preceding V4 epoch-cache release are preserved. The final release
has a new seal; Main's activation must bind that seal AND the exact new registry
hash. Activation remains a Main action through the original GPU-host confined
route; no VM service installation, platform-denial fallback, or fleet-ready claim.

Only after independent CPU rebind verification was the blocked shell stub
replaced. Main runs `activate_reviewed.py --reviewed-seal SHA --reviewed-registry
SHA` to write a review record once and exec the foreground shell. It validates
the concrete receipt/config/runtime pins without a duplicate source-epoch scan.
An identical existing review is reused without rewriting; conflicting reviews
are rejected. Existing durable state is never reset; singleton/reconciliation
still precede any new admission. This task never invokes that entrypoint.
