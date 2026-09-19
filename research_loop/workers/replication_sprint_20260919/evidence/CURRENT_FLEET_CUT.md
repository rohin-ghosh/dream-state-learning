# Current fleet capabilities — bounded operational cut

## Refresh — 2026-09-19 13:33:10 UTC

**No additional bound native went down. C0 and Astra7 are still down; C2, P3 and P7 retain their exact native identities and GPU residency.** The full 13:25 baseline remains below. New timestamped metadata is in `CURRENT_FLEET_CUT.json` under `refreshes[-1]`; `latest_refresh_utc` identifies this refresh.

| Life | Current head | Change since baseline | Most recent parent registration matched in this refresh |
|---|---|---|---|
| C2 | UPDATE 15474, 13:33:07 UTC | +32 records; native active | INBOX 15449 matches the latest local delivery receipt |
| C0 | UPDATE 6710, 02:43:34 UTC | No change; bound native absent | No new registration; old INBOX 6633 only |
| P3 | UPDATE 11023, 13:33:02 UTC | +56 records; native active | INBOX 10965, unchanged from baseline |
| P7 | UPDATE 14994, 13:33:07 UTC | +48 records; native active; new SLEEP_COMPLETE 14954 | INBOX 14973 matches a recent overseer publication |
| Astra7 | UPDATE 7807, 02:44:24 UTC | No change; bound native absent on node2 | None in the bounded window |

- **Urgent:** node2 still reports **100% used**; available space is now **5,284,925,440 bytes (~4.92 GiB)**, down 275,251,200 bytes since the baseline. No disk cleanup or recovery was attempted.
- **Bridge:** the same live bridge PID continues to record `FileNotFoundError`, most recently at 13:33:01 UTC. No current Astra7 roundtrip is established.
- **P3 parent:** process identity remains valid, but the newest provider receipt is still the 13:25:12 response and its result is SILENT. No newer publication is established by the selected metadata; this is not evidence the parent process is dead.
- **Limits:** journal advance is not a semantic-progress measure; parent registrations still do not establish REQUEST/ACT rendering or uptake. Refresh read approximately 1.02 MiB of remote metadata plus 17,451 bytes of selected local parent metadata. No node3/ovx4 read, launch, publication, signal or bulk extraction.

## Baseline — 13:25 UTC

**Native observation:** 2026-09-19 13:25:17–13:25:20 UTC (06:25 PDT). **Local parent metadata:** through 13:29:57 UTC. These are separate, non-atomic observations; this is not a live dashboard.

**Headline: 3/5 requested source-bound natives are active; C0 and Astra7 are down at their recorded bindings.** C2, P3 and P7 have matching PID/start identities, GPU residency and fresh journal metadata. They also have recent, hash-matched parent **INBOX registrations**. This cut does **not** prove that those messages were rendered into ACT, acted upon, learned, or transferred. The historical evidence findings remain unchanged.

## Native status

| Life | Verified node | Native PID / start ticks | GPU residency at cut | Latest record | Latest observed COMPLETE / checkpoint | Operational finding |
|---|---|---|---|---|---|---|
| C2 | node5, `ovx3_ssh.sh` | 1139778 / 30025875 | 20,818 MiB | CONTEXT_INPUT 15442, 13:24:25 UTC | SLEEP_COMPLETE 15412 / sleep150; optimizer 10,060 | Active, source-bound identity stable during read |
| C0 | node2, `ovx_ssh.sh` | Bound PID 745118 absent; current start unknown | None attributable to C0 | UPDATE 6710, approximately 02:43:34 UTC | SLEEP_COMPLETE 6631 / sleep145; optimizer 8,412 | Bound native down; no replacement established; sleep146 has no COMMIT |
| P3 | node4, `a40r_ssh.sh` | 699464 / 33078516 | 20,834 MiB | REQUEST 10967, 13:24:56 UTC | SLEEP_COMPLETE 10945 / sleep223; optimizer 10,108 | Active, source-bound identity stable during read |
| P7 | node4, `a40r_ssh.sh` | 563796 / 32330897 | 25,232 MiB | UPDATE 14946, 13:25:18 UTC | SLEEP_COMPLETE 14872 / sleep275; optimizer 12,332 | Active, source-bound identity stable during read |
| Astra7 | **node2**, `ovx_ssh.sh` | Bound PID 762967 absent; current start unknown | None attributable to Astra7 | UPDATE 7807, 02:44:24 UTC | SLEEP_COMPLETE 7750 / sleep146; optimizer 9,644 | Bound native down; no replacement established |

Record times above are file modification times, not independently established generation times. Start ticks identify a process within its boot; boot IDs, GPU UUIDs, working directories, bindings and full record hashes are in `CURRENT_FLEET_CUT.json`. Checkpoint entries are COMMIT metadata only, **not restore verification**. C0 and Astra7 have approximately 10 h 42 min and 10 h 41 min of journal silence at this cut; their exact failure times are not inferred from that silence.

Astra7's node differs from the requested grouping: the existing `rohin233_recovery_node4_20260918/bridge.py` routes Astra7 to `ovx_ssh.sh`, and its receiver binds `/localhome/local-rohing/orch_r229_Astra7_20260918/raw`. No node3 or ovx4 access was made.

## Parenting: publication is not delivery

| Life / component | Actual process evidence | Most recent registration verified against the native cut | Current bounded finding |
|---|---|---|---|
| C2 parent | Provider PID 325487 / start 753205; supervisor PID 361010 / start 822432 | Astra INBOX 15433 at 13:21:11 UTC; ID `b2d74256bf704ecf937da536ef969f39`; matches parent_000102 receipt | Later local receipt also exists, but is not cross-verified against this earlier native cut. `DELIVERED` names an INBOX record, not an ACT render. No current provider failure established. |
| P3 parent | PID 346649 / start 795156; exact runner argument and process hash match | Astra INBOX 10965 at 13:24:30 UTC; ID `1ce95f138f964ec9a5ed78f5209c279e`; matches parent_526 publication | Latest provider receipt at 13:25:12 reports a successful xhigh response; attempt528 is **SILENT**, not a new publication. `awaiting_render=false` is publisher state, not independently verified rendering. |
| P7 overseer | PID 378291 / start 854895 | Astra INBOX 14893 at 13:19:16 UTC; ID `dfc9c9a9948d4ec6af3bdab4c1204d01`; matches publication sequence258 | Sequence259 is published locally; its registration is not established in the selected native window. Latest sampled error is an older HTTP_429 followed by successful publications, not evidence of a current auth outage. |
| C0 parent | Current parent process not established in this read | Astra INBOX 6633 at 02:34:51 UTC; ID `34a70aeb1bce46e98239b5f730a59159` | Native is down. No current successful interaction claimed. |
| P7 ↔ Astra7 bridge | PID 325634 / start 753612 is running | No new roundtrip established | Latest two sampled failures are **FileNotFoundError**. Latest receipts in this bridge ledger for both directions are from September 18, not current interaction. An active bridge cannot substitute for the absent Astra7 native. |

All current REQUEST/ACT rendering and uptake remain **unknown** in this metadata-only cut. No parent credential was read or changed; error text is not exported. Main's learner/sibling `HTTP_401` / `AUTH_ERROR` report is external context only: those arms were expressly not re-audited and their failure is not attributed to these parents.

## Recovery-relevant blockers, without taking action

- **C0:** control `EXIT.json` reports exit code1, `no_retry=true`, finished at approximately 02:44:27 UTC. Sleep145 COMMIT exists; sleep146 COMMIT does not. The preserved-state recovery decision belongs to Main, not this read-only workstream.
- **Astra7:** missing bound PID plus stale journal establishes its recorded incarnation is down. Current EXIT/OUTER_EXIT metadata was unavailable within the small-file bound; exact exit class remains unknown.
- **Bridge:** current repeated FileNotFoundError is established; the exact missing object and causal relationship to Astra7's outage were not diagnosed.
- **Disk:** node2 reports **100% used**, despite 5,560,176,640 available bytes (about 5.18 GiB). VM `/data` is **95% used**, with about 12.48 GiB available. Node4 is 24% used; node5 is 74% used. Disk pressure and stopped natives are observations, not a newly established causal explanation.

## Evidence and limits

- Machine-readable companion: `research_loop/workers/replication_sprint_20260919/evidence/CURRENT_FLEET_CUT.json`. It includes exact paths, stored record IDs/hashes, recomputed small-file hashes, process identities, per-node timestamps, and publisher-to-registration matches.
- C2 binding: `research_loop/workers/rohin233_recovery_node4_20260918/C2_CHECKPOINT_TAIL_LOADED.json`; P3 binding: `research_loop/workers/post_reboot_p3_parent_20260919/P3_RETRY_BINDING.json`; P7 binding: `research_loop/workers/post_reboot_c2_p7_20260919/P7_DELIVERY.json`. C0 journal identity matches the existing historical C0 projection; no incarnation mismatch is asserted.
- Parent evidence uses the existing `post_reboot_c2_p7_20260919`, `post_reboot_p3_parent_20260919`, `rohin174_parenting_20260917/node4/R195_FLEET/r210_parent3`, and `rohin233_recovery_node4_20260918/private/bridge` metadata. Only allowlisted fields and error classes are copied into the companion, not prompts, answers, or raw errors.
- Native read: at most **128 record headers per life**, 4 KiB tails and 64 KiB small-JSON caps; approximately **1.14 MiB** read across three nodes. Parent metadata capture for this report: **60,994 bytes**. Large record hashes are stored header claims, not recomputed full-body hashes; small INBOX canonical hashes were verified.
- No multi-GB journal scans/copies, REQUEST/COMPLETE payload extraction, weights, sealed panels, answer keys, launches, publications, signals, commits, or pushes. There was no exhaustive replacement-process search. Only the evidence directory is written.

**Front-page claim supported now:** three verified natives are producing records with recent parent registrations; two retained lives need recovery and the Astra7 bridge is failing. **Not supported by this cut:** that all five are operational, that a running parent delivers usable guidance, or that current self-reflection improves ACT or independent performance.
