# Node1/node2 bounded operational inventory — 2026-09-12

## Scope and observation window

- Audit started **2026-09-12 18:53:07 UTC / 11:53:07 PDT**. Remote observations: node1 18:53:49–18:55:14 UTC; node2 18:53:50–18:55:16 UTC. Receipt metadata sampled at 18:55:03–04 UTC. This is a changing, non-atomic snapshot, not an allocation grant.
- Only node1 (`gpu/a40_ssh.sh`) and node2 (`gpu/ovx_ssh.sh`) were contacted. **Node3 was not contacted or audited.** Main's specified node3 GPU4/5/6 controllers 182565/182566/182567 remain wholly outside this audit.
- Read-only NVIDIA queries, process identities/ancestry, selected `/proc/*/environ` fields, queue receipts, bounded log tails, and file metadata. No model loading, packages, launches, kills, queue modifications, Git commands, or repository/remote file writes. SSH used existing wrappers with strict host-key checking and host-key updates disabled. The sole authored file is this report.
- Instructions consulted: supplied `AGENTS.md`; root `CLAUDE.md`; `gpu/V2_NODE_SETUP.md`; `gpu/codex/README.md`; current launch prompt §10/§15; current handoff and coordination entries; queue runner/status/seed scripts; VM filler script/lists; migration script (read, **not executed**). No nested AGENTS/CLAUDE files were found under gpu/research_loop/research_notes.

## Bottom line

**11 controller-owned GPUs; 5 provisional idle candidates across the two nodes.** Node1 candidates: **6,7**. Node2 candidates: **5,6,7**. These candidates have zero reported memory, no NVIDIA compute-app entry, no matching readable CUDA reservation, and no running queue assignment in the sampled evidence. They are **not certified free**: inaccessible process environments and unrecorded reservations remain unresolved.

Both node queues have **zero pending jobs**. All nine entries in each current filler list have already been submitted. The existing work therefore covers the 11 active reservations, **not** future backfill of the five candidates. The filler preserves two builder-headroom GPUs per node; its latest tick reports node1 room=0 and node2 room=1 with nothing left to add. Four idle slots are explained by that headroom policy; one additional node2 slot has no remaining filler job. Main may choose valid work for headroom, but this audit does not reserve or launch it.

## Concrete resource table

All devices are NVIDIA A40. Memory/utilization below are from **18:55:14 UTC node1** and **18:55:16 UTC node2**. Queue starts are September 12 UTC. Apparent task ownership is **Fable filler / builder-priority subsidiary work**, inferred from the live queue parent, job name, controller ancestry, and matching CUDA assignment; OS identity is the shared account `local-rohing`, not proof of an individual human's present ownership.

| Node | GPU | MiB / util % | Queue task (prefix `fable_fill_pretest_`) | Queue PID / CUDA shell PID | Queue start UTC | Observed worker or phase | Availability |
|---|---:|---:|---|---|---|---|---|
| 1 | 0 | 38449 / 0 | RP_B_seed402 | 2702628 / 2702633 | 08:29:39 | Engine 3998464; A_v3 disjoint probe | Owned, including reload gaps |
| 1 | 1 | 44543 / 100 | R4_B_seed606_AC | 3262676 / 3262681 | 16:44:53 | Trainer 3843239; C_tmem | Owned |
| 1 | 2 | 39337 / 79 | R4_B_seed605 | 2702733 / 2702738 | 08:29:40 | Engine 3939197; A disjoint probe | Owned |
| 1 | 3 | 39495 / 0 | R3_B_seed501 | 2767348 / 2767353 | 09:03:11 | Engine 3971244; A_v3 disjoint probe | Owned |
| 1 | 4 | 40991 / 0 | R3_B_seed502 | 2767453 / 2767458 | 09:03:11 | Engine 3931210; brief_mid disjoint probe | Owned |
| 1 | 5 | 39791 / 0 | R3_B_seed500 | 2703048 / 2703053 | 08:29:40 | Engine 3915268; B report probe | Owned |
| 1 | 6 | 0 / 0 | None observed | None observed | — | No compute entry or readable CUDA claimant | Provisional candidate; filler headroom |
| 1 | 7 | 0 / 0 | None observed | None observed | — | No compute entry or readable CUDA claimant | Provisional candidate; filler headroom |
| 2 | 0 | 40111 / 100 | R3_B_seed505 | 264738 / 264743 | 11:44:00 | Engine 1923104; OFF report probe | Owned |
| 2 | 1 | 37481 / 99 | R4_B_seed603_AC | 1439579 / 1439584 | 17:14:23 | Trainer 1909067; C_tmem | Owned |
| 2 | 2 | 34755 / 100 | R4_B_seed602_Brep | 1906961 / 1906966 | 18:34:49 | Trainer 1907935; B-only replication | Owned; recent added work already running |
| 2 | 3 | 39781 / 94 | R3_B_seed504 | 4180758 / 4180763 | 09:33:03 | Engine 1913176; A report probe | Owned |
| 2 | 4 | 0 / 0 | R4_B_seed600 | 3878323 / 3878328 | 08:30:00 | C_tmem disjoint probe at 18:54:28; engine 1965564 subsequently absent | **Retain reservation; not free on this evidence** |
| 2 | 5 | 0 / 0 | None observed | None observed | — | No compute entry or readable CUDA claimant | Provisional candidate; unused filler capacity |
| 2 | 6 | 0 / 0 | None observed | None observed | — | No compute entry or readable CUDA claimant | Provisional candidate; headroom accounting |
| 2 | 7 | 0 / 0 | None observed | None observed | — | No compute entry or readable CUDA claimant | Provisional candidate; headroom accounting |

Headroom is a count policy, not a pinning of specific GPU indices. The node2 5 versus 6/7 descriptions illustrate three candidate slots minus two headroom slots, not an exclusive reservation by index.

### Ownership evidence and limits

- Node1 queue runner **207904**, started September 11 20:10:14 UTC; node2 runner **1823897**, started September 11 20:10:17 UTC. Both remained live at the final sample. All 11 running receipt PIDs existed during receipt inspection; process ancestry connected their shell chains to the respective queue runner.
- Readable CUDA controller assignments: node1 `2702633→0, 3262681→1, 2702738→2, 2767353→3, 2767458→4, 2703053→5`; node2 `264743→0, 1439584→1, 1906966→2, 4180763→3, 3878328→4`. Worker identities and their PPIDs were checked independently with NVIDIA and `ps`.
- **Concrete zero-memory counterexample:** node1 GPU0 was 39725 MiB at 18:53:49, **0 MiB at 18:54:16**, and 38449 MiB at 18:55:14. Controller 2702633 retained `CUDA_VISIBLE_DEVICES=0`; the log advanced to the next probe. It was never available to another launcher. Node2 GPU4 similarly dropped from 40945 MiB at 18:54:28 to 0 at 18:55:16; no release was verified, so its reservation is retained.
- `/proc` environment reads encountered **2660 permission denials on node1** at 18:54:16 and **1466 on node2** at 18:54:28. These are counts of inaccessible environments, not counts of GPU claimants or independently established service processes. No privileged reads were attempted. A CVD-free process can also choose a device programmatically. The audit cannot exclude such claims or out-of-band reservations.
- No direct owner acknowledgement or atomic allocation lock was obtained. Before use, Main must freshly reconcile queue/controller identity, process start time, descendants, all-device compute inventory, CUDA reservations, and current coordination. An absent worker, idle utilization, or old log timestamp is insufficient. Existing work is preserved; the audit's explicit no-kill restriction supersedes broader runbook preemption language.

## Queue coverage and scheduler state

| Node | Pending | Running | Done | Failed | Rejected | Last queue event sampled |
|---|---:|---:|---:|---:|---:|---|
| 1 | 0 | 6 | 13 | 10 | 9 | 16:44:53 UTC: R4_B_seed606_AC launched; candidates 6,7 |
| 2 | 0 | 5 | 45 | 7 | 4 | 18:34:49 UTC: R4_B_seed602_Brep launched; candidates 5,6,7 |

Counts were inspected at 18:54:16 UTC node1 and approximately 18:53:50 UTC node2. Historical failed/rejected receipts are not ready work and were not retried. In particular, old node2 `neg64_b2`/dependent reports and A2 attempts remain historical failure records, not a justification to resubmit the September 11 seed scripts.

Local filler PID **1573630** was live at 18:54:52 UTC, running `fable_fill.sh 600 2`. At 18:54:32/33 UTC its log reported node1 `free=2 builder_pending=0 room=0`, node2 `free=3 builder_pending=0 room=1`, both with nothing added. Each checked-in list has **9 declared / 9 submitted / 0 unsubmitted** names. The node2 B-only replication was added at 18:34:29 and launched at 18:34:49; an earlier notebook snapshot saying four running / four free is superseded by this evidence.

The runner only logs events or changes in free count; an old last-event timestamp alone does not establish a dead runner. The filler consumes that event log, so its `free` value is not an independent real-time vacancy proof. No future GPU job or backup job is pending in either audited node queue.

## Selective receipt observations — operational, not scientific acceptance

- Node1 RP402: seven adapter `DONE` markers present, latest sampled C_tmem marker **17:36:00 UTC**; A/A_v3/B/B_match/Bs/C training metadata present. At **18:54:08 UTC** its queue log completed A_v3 report and began A_v3 disjoint. No `summary.json` at 18:55:03. Adapter-level completion is not whole-job completion.
- Node1 R4_606_AC: A/A_v3/C `DONE` markers present; C marker **18:35:51 UTC**. Queue log at 18:35:53 says **“WARNING train check failed for C”**; C_tmem trainer remains active. No summary at 18:55:03.
- Node2 R4_603_AC: A/A_v3/C `DONE` markers present; C marker **18:35:19 UTC**. Queue log at 18:35:20 has the same C training-check warning; C_tmem trainer remains active. No summary at 18:55:04.
- Node2 R4_602_Brep: current log starts B training at **18:34:59 UTC**; no sampled adapter DONE marker or summary at 18:55:04. This is the existing queued/runbook B-only seed-5252 follow-up, not missing work to duplicate.
- Local `write_ab.sh` checks training manifests for dropped target tokens and packing behavior. The two warnings require receipt-level diagnosis before treating cells as valid; this audit did **not** infer which condition failed, mark entire jobs failed, read sealed panels, load weights, or authorize automatic repair/retry. Existing partial artifacts must remain intact.

## Lease and backup horizon

These are **supplied/documented lease dates, not newly verified control-plane state**. Countdown reference: **September 12 18:54:52 UTC**. Leases are not assumed extendable.

| Node | Backup due | Finish cutoff (six-hour margin) | Lease expiry | Remaining to backup / finish / expiry |
|---|---|---|---|---|
| 1 | Sep 13 23:14 UTC / 16:14 PDT | Sep 14 17:14 UTC / 10:14 PDT | Sep 14 23:14 UTC / 16:14 PDT | 28.32 / 46.32 / 52.32 hours |
| 2 | Sep 20 08:43 UTC / 01:43 PDT | Sep 21 02:43 UTC / Sep 20 19:43 PDT | Sep 21 08:43 UTC / 01:43 PDT | 181.80 / 199.80 / 205.80 hours |

- Sources: `research_loop/COORDINATION.md:3125` and `research_notes/astra_memos/ASTRA_HANDOFF_2026-09-12.md:179`; launch prompt §15 requires copying needed adapters, ledgers, and receipts to surviving storage with hash verification before expiry. Current jobs have ample nominal lease margin, but this short audit provides no whole-job runtime guarantee.
- Node2 **does contain** `~/mirror/node1_adapters_2026-09-12`, `~/mirror/node1_receipts_2026-09-11`, `~/mirror/node1_receipts_2026-09-12`, and `~/node1_mirror/node1_v6_out_receipts_2026-09-10.tar.gz`. The adapter mirror root mtime is **September 12 02:04:15 UTC**; the latter archive mtime is **September 10 17:39:53 UTC**. Directory mtimes do not establish recursive freshness or completeness. No shallow mirror verification file matching the sampled manifest/hash name patterns was found; this is not proof none exists deeper.
- Historical Fable receipt at 06:50 UTC reported **698 of 702 adapters** mirrored and a planned final refresh. Coordination at line 2316 records a **07:04 UTC** node1 receipt archive on laptop storage, excluding model tensor files, with a reported matching checksum. The laptop copy, its full checksum, and current per-file mirror completeness were **not independently verified** here. Today's active write-pretest outputs postdate that evidence; no complete current backup claim is supported.
- A later notebook entry describes a fresh node1 lease after the current lease ends, with **CLEAN provisioning/reimaging**, not extension or data persistence. Do not let that future capacity erase the present off-node backup deadline. This audit did not verify or alter future leases/onboarding.
- No backup is represented in the inspected node pending queues, and no active backup/rsync was identified in the readable matching process inventory. External/laptop automation remains outside verification. The existing mirrors and historical receipts provide partial evidence, **not full coverage of the current backup horizon**.
- `gpu/migrate_node1_to_node2.sh` is a legacy reference, not a safe read-only next command: it includes hard-coded laptop paths and destructive process cleanup before transfer. It was not executed or recommended verbatim.

## Next safe choices for Main — recommendations only

1. **Preserve the 11 current reservations** and collect terminal queue/job receipts as they finish. Treat node1 GPU0 and node2 GPU4 reload/phase gaps as occupied until controller exit and release are verified. Do not duplicate the already-running R4_602_Brep or restart exhausted seed lists.
2. **Prioritize a bounded node1 backup-completeness audit now:** compare needed current adapters/ledgers/receipts against surviving node2/laptop evidence, then have the authorized owner arrange verified off-node copies before September 13 23:14 UTC. That copying is separate work, not performed or authorized by this audit. Preserve source data and hash-bound resume evidence; do not run the legacy destructive migration script blindly.
3. **Investigate the two existing C-training warnings with CPU-only manifest/log reads** in the AC follow-ups. Report the actual failed condition before any scientific interpretation, repair, or retry; do not change active scripts or score visibility.
4. **For additional GPU work, start from Main's current declared development prerequisites/controls, not historical backlog.** The latest coordination entry identifies native encoder/mask/readout-loading audit as the next diagnostic prerequisite. Its CPU/provenance audit can proceed without consuming an idle GPU; any separately approved native read-only/controlled diagnostic needs its own bounded plan, valid controls, fresh ownership check, immutable evidence root, and lease margin. This audit does not select new scientific arms.
5. **Capacity choices after that check:** node1 GPU6/7 or node2 GPU5/6/7 are candidate locations, with node2 offering more lease runway. The current filler has no unsubmitted task to cover them automatically. Filling the extra node2 slot requires a genuinely new, owner-declared ready item; keeping two slots of builder headroom per node is the documented filler behavior, not a scheduler failure. No action is needed on node3 from this audit.

## Uncertainties retained

Unverified lease control-plane state; shared-account human ownership; inaccessible `/proc` environments; non-atomic job transitions; final node2 GPU4 release status; warning causes; exact remaining job durations; recursive backup completeness; external watcher/backup execution. No result is promoted from operational liveness to scientific validity.
