# P3 explicit pre-LOAD parent queue — September 18, 2026

Actual publication: **20:50:18.992 UTC**. A separate one-shot CPU helper generated
one original-policy xhigh Astra turn from authenticated preserved child history
with explicit recovery-downtime context, then used the existing parent console
API. Remote inbox-byte verification completed at **20:51:03.884 UTC**.

| Evidence | Actual result |
| --- | --- |
| Original ledger | `parent_000000000315`, PUBLISHED; prior attempts preserved |
| Provider request | Original provider/model; `reasoning.effort=xhigh`; API request SHA `0a762332863eff393c879e34330792d1e22d003e3276a0f919e3a0627a4f9268` |
| Inbox | `d8b1416558c04cb085107592e3408ec6`, attributed Astra/parent |
| Exact inbox bytes | SHA `657d7e830346e1f4e8098314c8c057394b4d5dab3486f5b98035c8b37a890585` |
| Preserved child source | RESPONSE5310, record SHA `83dbdfe4c2c966130fe777fa7b7f19a61206e240d8c248fe1fc7b0ef8f7ebe50` |
| Recovery authority | Same original journal, COMPLETE5243/sleep153; recovery head5315; native699464/start33078516 |
| LOAD/render/ACT | No retry LOAD at publication; inbox queued, **not rendered**; no new ACT claimed |
| Single owners | Native699464, controller658049, existing waiter3671383 untouched; no new replay |

The native was dispatched at **20:16:52.819966 UTC**. At **20:49:28 UTC** the
same native and controller were alive and the journal still ended at recovery
record5315. Native699464 was absent from the GPU compute-process query. It had
read15,789,776,053 process bytes over20,068 read calls; these are cumulative I/O
counters, **not an exact journal replay position or percentage**. No current
inference residency, parent cadence or successful learning is inferred.

## Historical publication reconciliation

The original ledger's turn312 had PUBLICATION_UNKNOWN. Its exact preserved
error is a rejection in the old endpoint's host validation, before its console
publication branch. The original RESULT, SOURCE and PUBLISH_INTENT were pinned
and retained unchanged. Under the same authenticated host/native/head and
publisher lock, a bounded audit of162 existing inbox files found no matching
message hash. Endpoint source hashes matched. An append-only resolution receipt
records **NOT_PUBLISHED_PREPUBLICATION_HOST_REJECTION**.

Only this exact historical result is projected as a failed validation for policy
memory; the historical UNKNOWN status is retained in the projection and on disk.
Other unknown publications, changed receipt bytes, duplicate resolution, or an
inbox match still block. The normal live endpoint and its LOAD gate were not
modified. This reconciliation also prevents the same historical blockage after
the existing waiter authenticates a real retry LOAD.

Two earlier CPU snapshot attempts made zero provider calls/publications: the
first exhausted its bounded read, and the second caught up but hit turn312's
uncertainty guard. A separately logged source-resume reused the authenticated
cursor and generated once. There is no automatic publication retry.

## Authorization and checks

The user prohibited bypassing provenance/security, **not modifying an application
LOAD gate**. The explicit instruction authorizes a separate bounded preload
mode. Prior attribution to a user ban on application-gate changes was incorrect
and is corrected in the historical blocker document.

[Builder] 2026-09-18 20:52 UTC — Non-material, CPU-only parent transport repair
and explicitly authorized one-turn preload queue. Same journal, exact PID/start,
source/guard/COMPLETE/head, source pins, original provider/policy/ledger and
single-publisher lock verified. Original ledger files unchanged; no native
signals, restarts, source changes or GPU dispatch. **54 focused local tests and
44 receiving CPU tests PASS**. Tests cover wrong/reused identity, LOAD/head
changes, duplicate publication, in-lock identity change, exact uncertainty
reconciliation and preservation of original bytes. Test outputs are retained.

Post-LOAD parent REQUEST/committed ACT, retained Tool notice rendering and actual
R227 recipe/eligibility/COMPLETE remain pending. The existing waiter owns normal
attachment; this queue is not a second continuous parent.
