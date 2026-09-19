# V4 bounded source-epoch validation — September 19, 2026

Non-material performance/integrity repair. The original evaluator, source cuts,
scenes, token budget, judging, parent blindness, no-retry identities, fixed UUID
lane and lease horizon are unchanged. The original V3 worker and seal remain
untouched. This directory is a new release, not an in-place V3 replacement.

## Proof and bounds

Each process owns an in-memory proof keyed by its PID, exact policy and source.
No persisted cursor or caller-supplied high-water mark authorizes skipping work.
Cold start still authenticates every required record from current_loaded through
the observed head, and both pinned LOADED anchors. It uses the original canonical
JSON SHA256 definition, exact journal/index and previous-hash chain, LOADED/base
checks, and rejects any new LOADED epoch. No original journal writes occur.

One verification call parses at most 256 records or 64 MiB, with a 2-second
cooperative time budget per source. One atomic record up to the inherited32 MiB
limit can exceed the byte/time target. Directory enumeration and metadata checks
are O(number of retained suffix records), not constant-time or hard real-time.
Every incomplete batch raises SOURCE_EPOCH_VALIDATION_PENDING_NO_ADMISSION;
it is never success and never records a dispatch intent. The foreground queue
continues warming without turning known incomplete validation into a permanent
fault. Real integrity, identity, lease and platform failures still pause.
Pending warmup cycles yield0.1 seconds rather than imposing the normal10-second
idle poll delay on every64 MiB chunk. Warmup remains serialized and CPU-only.

Warm calls inspect every verified file's device/inode/type/ownership/link count,
size, mtime_ns and ctime_ns, plus source directory identities. Replacement,
mutation, deletion, truncation, symlink and chain changes fail closed. Files
within a conservative2-second timestamp granularity window are raw-SHA rechecked
without JSON decoding, including a final check after that window, before relying
on metadata alone. This detects same-size/mtime-restored rapid writes that share
a filesystem timestamp tick. Cached decoded documents are not retained. Like
the original journal writer's identity cache, this assumes truthful local kernel
metadata, not a hostile filesystem/root capable of forging old ctimes.

observe, verify_capsule and verify_live_source share the same process cache.
Host/boot/UID, protected PID start/argv and lease checks remain fresh even while
validation is pending. GPU occupancy, original claims and prior attempts are
not cached; admission refreshes them after expensive bundle checking. A new
process intentionally cold-validates rather than trusting a disk proof. The
one-shot preflight can drain bounded batches for at most300 seconds with fresh
protected checks; its caller has a420-second transport ceiling. The finite
scientific job deadline is never extended. A pending/failed launch still gets
the inherited ambiguity/no-retry handling, never automatic resubmission.

## CPU-only preflight

```
python3 -B source_preflight.py --policy policy.json --max-seconds 300
```

Run on the pinned receiving host. This does NOT inspect GPU occupancy, verify
the capsule runtime binding, activate a daemon, claim devices or execute probes.
It reports cold and warm costs, authenticated heads, or an explicit blocker.
There is no trusted disk cache: do not repeatedly spawn this command and expect
unfinished cold work to survive process exit. For a deployed foreground daemon,
bounded cycles warm its own long-lived cache before any admission.

## Deployment remains blocked

The existing sleep24 capsule/config is frozen to V3's four-module runtime. V4
adds epoch_cache.py and changes runtime bytes, so its exact runtime-binding check
MUST reject that old binding. Do not overwrite the existing config/capsule, reuse
its old config SHA for V4, rebuild the source capture, change its job ID, or erase
attempt markers. Main must review a separately versioned immutable runtime/config
binding for that same captured source and no-retry identity before activation.
No such rebind is performed by this repair. ACTIVATE_FOREGROUND.sh deliberately
exits2; V3's existing activation instructions do not activate V4.

Boot installation stays BLOCKED_UNINSTALLED. Secure automatic credential
bootstrap stays UNVERIFIED. No VM service-management attempts or alternate routes.
