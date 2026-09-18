# NODE3 final source stop and receiving handoff

All six original native/timer/supervisor groups are actually absent. Old parents are settled/absent, and original inbox publication paths are frozen. This is not receiving LOADED.

| Life | Final COMPLETE | Source exit PDT | State discontinuity |
|---|---:|---|---|
| support_free | 46 | 16:46:47 | complete boundary;0 lost |
| creative_reread | 46 | 16:49:50 | 42 logged updates + UNKNOWN in-flight not resumed |
| brain_free | 44 | 16:49:49 | 48 logged updates + UNKNOWN in-flight not resumed |
| brain_guided | 42 | 16:47:43 | complete boundary;0 lost |
| creative_free | 43 | 16:47:27 | complete boundary;0 lost |
| creative_select | 44 | 16:49:49 | 41 logged updates + UNKNOWN in-flight not resumed |

Final archives: `physicalN.tar.gz`, each bound by `physicalN.VERIFIED.json` and this directory's `INDEX.json`. Each packet has a resumable COMPLETE-prefix root and `final_live_stream` containing the entire stopped raw journal/inbox/suffix; do not treat uncommitted suffix updates as resumed learning. Record/intent pairs and original hashes are preserved. Apply the separately verified `../FINAL_INBOXES_20260917t2350z.tar.gz` after this packet to preserve all final parent/Rohin messages. Per-life FROZEN.json records IDs/hashes and receiving inbox permissions. Parent ledgers/config/seed/pending IDs: `../final_parent_handoff/physicalN.json`.

Physical3/4 stopped at proven complete boundaries, but their waiter reported an exit-race while checking already exited timer/supervisor processes. Original failures and conservative packet flags are retained. `../FINAL_SOURCE_STOP_AUDIT.json` additively proves actors absent, exact saved-boundary head unchanged, and zero suffix/lost updates. This corrects uncertainty only; no original evidence is rewritten. Earlier R188 rollback losses remain separately recorded in packet control/STOPPED.json and RESTORED.json.

Allocation and sole receiving dispatch owners are in `../REHOME_ALLOCATIONS_V1_CORRECTED_METADATA.json`: Gauss node4:5 brain_free,6 brain_guided,7 support_free; Ampere node2:0 creative_reread,7 creative_free; creative_select waits for first naturally finished LR5/6 slot. Do not launch another copy or reuse stale admission. Bind actual receiving host/device/lease/deadline and original logical-root namespace. Frozen weights remain an external dependency.

Downtime starts at the source exit timestamps above and ends only at each actual receiving LOADED timestamp. Receiving owners must provide actual new wrapper/root/config and separate LOADED receipt before enabling Rohin-attributed console publication. Old NODE3 paths remain retired; do not send or resend baseline/unknown publication messages there.
