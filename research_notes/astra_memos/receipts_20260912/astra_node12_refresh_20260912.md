# Node 1–2 read-only resource/evidence refresh — 2026-09-12

Inspection began 2026-09-12T16:32:04Z. Hardware/process/queue receipts below are from 16:33:40–16:33:42Z; selective terminal-content reads ended 16:34:07Z. Report prepared after 16:34:14Z. These are point-in-time observations, not continuing monitoring.

## Decision for Main

**No newly completed independent evidence was found that changes the next mechanism comparison.** All 12 existing fill pretests remain running (six per node), with live queue-controller PIDs, no terminal RC files, and no top-level summaries for these run IDs in the inspected roots. Do not treat individual finished training/probe stages as completed pretests.

Older completed pretests were positively verified using summary contents, literal `WRITE_AB_DONE` log lines and RC=0, not filenames. The newest inspected pretest is node 2 `R2_B_seed3`, terminal at 11:38 UTC; it predates the latest 16:02 UTC watcher baseline. The newest inspected Astra memory-dose fit/eval stage is already covered by COORDINATION SEQ-067 at 09:13 UTC. Neither is a new result since that baseline. No independent re-scoring, causal review, or RuleGame recommendation change is claimed.

For the upcoming comparison, retain the existing no-write/control and complete-record utility distinctions. These older pretest aggregates do not establish learned parenting, a clean lineage, or that a completed record is useful merely because training finishes. This is a narrow evidence-refresh conclusion, not an architecture decision or launch approval.

## Scope and routing confirmation

- Confirmed the real files with `ls -l gpu/a40_ssh.sh gpu/ovx_ssh.sh`, exit 0; both are executable. Read wrapper routing with credential-related directives redacted. `a40_ssh.sh` selects `A40_NODE`; `ovx_ssh.sh` selects `OVX_NODE`. No host variables, credentials, or credential files were inspected or copied; normal wrapper-managed authentication was used.
- Actual wrapper-returned hostnames: node 1 `a4u8g-0105`; node 2 `ipp2-ovx-p2-08`. Paths below were discovered in remote listings, process arguments, job metadata and COORDINATION, not invented. Remote home is `/localhome/local-rohing` on both.
- Read latest available `research_loop/COORDINATION.md`: latest initial entry 16:30 UTC, latest watcher fill baseline 16:02 UTC (line 4299 at inspection), A2 terminal SEQ-067 around lines 2713–2715. Historical coordination entries are not globally chronological.
- No Main/node 3 connection or inspection. No launches, queue mutations, kills, leases, source edits, external communications, checkpoint transfers, or Fable contact. Read-only SSH commands did spawn ordinary inspection shells. Only local `/tmp` scripts, text receipts, and this report were written.
- Initial local `git status --short` showed a pre-existing modification to `gpu/codex/dream_state.rules`; it was not touched. No nested AGENTS.md was found under `gpu/` or `research_loop/`; `/tmp/AGENTS.md` was absent.

## Current hardware / process / queue snapshot

All 16 enumerated devices are NVIDIA A40, 46,068 MiB each. Device memory below is the GPU-query value, not per-process allocation. Queue ownership is taken from existing `.job` contents and checked live PIDs. Stage names are selective tail observations, not progress percentages.

| Node | GPU | Used MiB | Util % | Compute PID | Existing run / latest observed stage |
|---|---:|---:|---:|---:|---|
| 1 | 0 | 33607 | 100 | 2983222 | RP_B_seed402 — train_C_tmem |
| 1 | 1 | 38639 | 100 | 3235364 | R4_B_seed604_AC — probe_brief_mid_disjoint |
| 1 | 2 | 25861 | 100 | 3021184 | R4_B_seed605 — train_C_tmem |
| 1 | 3 | 36917 | 100 | 2958228 | R3_B_seed501 — train_C_tmem |
| 1 | 4 | 40319 | 78 | 3218973 | R3_B_seed502 — probe_A_v3_report |
| 1 | 5 | 43771 | 100 | 2956364 | R3_B_seed500 — train_C_tmem |
| 1 | 6 | 0 | 0 | none listed | No compute process observed |
| 1 | 7 | 0 | 0 | none listed | No compute process observed |
| 2 | 0 | 40235 | 0 | 1065387 | R3_B_seed505 — probe_A_disjoint |
| 2 | 1 | 39635 | 100 | 1050452 | R3_B_seed503 — probe_OFF_disjoint |
| 2 | 2 | 40533 | 86 | 1047282 | RP_B_seed401 — probe_Bs_disjoint |
| 2 | 3 | 38161 | 100 | 713390 | R3_B_seed504 — train_C_tmem |
| 2 | 4 | 39851 | 91 | 1088686 | R4_B_seed600 — probe_A_disjoint |
| 2 | 5 | 40095 | 86 | 1083068 | R4_B_seed602 — probe_B_match_report |
| 2 | 6 | 0 | 0 | none listed | No compute process observed |
| 2 | 7 | 0 | 0 | none listed | No compute process observed |

Node 1 GPU1 was momentarily 0 MiB at 16:32:44Z while its queue job remained live. By 16:33:40Z it had a new vLLM engine and 38,639 MiB allocated. This was an inter-stage gap, **not a free slot**. Node 2 GPU0's zero sampled utilization also does not make it available. GPUs 6/7 are observationally empty on both nodes, not certified for reassignment.

| Node | Queue runner PID | Running | Pending | Hold | Done | Failed | Rejected |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 207904 | 6 | 0 | 0 | 12 | 10 | 9 |
| 2 | 1823897 | 6 | 0 | directory absent | 42 | 7 | 4 |

Counts enumerate `.job` files directly in `/localhome/local-rohing/queue/<state>`; done/failed/rejected are historical counts, not newly classified outcomes. Both runner PIDs were visible in the process snapshot. No pending jobs were added or modified.

| Node | Queue job prefix | Run suffix | Controller PID | GPU |
|---|---|---|---:|---:|
| 1 | 0030 | RP_B_seed402 | 2702628 | 0 |
| 1 | 0031 | R4_B_seed605 | 2702733 | 2 |
| 1 | 0034 | R3_B_seed500 | 2703048 | 5 |
| 1 | 0035 | R3_B_seed501 | 2767348 | 3 |
| 1 | 0036 | R3_B_seed502 | 2767453 | 4 |
| 1 | 0037 | R4_B_seed604_AC | 2854044 | 1 |
| 2 | 0053 | RP_B_seed401 | 3878196 | 2 |
| 2 | 0054 | R4_B_seed600 | 3878323 | 4 |
| 2 | 0055 | R4_B_seed602 | 4046022 | 5 |
| 2 | 0057 | R3_B_seed503 | 4138954 | 1 |
| 2 | 0058 | R3_B_seed504 | 4180758 | 3 |
| 2 | 0059 | R3_B_seed505 | 264738 | 0 |

Full queue names are `fable_fill_pretest_<run suffix>`; each job file is `<prefix>_<full queue name>.job`. All twelve `ps -p <controller> -o pid,ppid,etime,args` checks exited 0; all twelve `test -f /localhome/local-rohing/queue/logs/<full queue name>.rc` checks exited 1 (absent, not a job failure).

Observed output roots are `/localhome/local-rohing/v6_out/pretest_write_ab/<run suffix>/`, except node 1's AC run uses `/localhome/local-rohing/v6_out/pretest_write_ab_AC/R4_B_seed604/`. `R4_B_seed604_AC` is the queue-name suffix; the actual life directory is `R4_B_seed604`.

## Completed evidence and precise boundaries

### Pretests — verified older terminals, no newly completed fill

| Node | Run ID | Summary path | Summary mtime UTC | Literal terminal evidence | Reported measured GPU-hours |
|---|---|---|---|---|---:|
| 1 | R2_B_seed1 | `/localhome/local-rohing/v6_out/pretest_write_ab/R2_B_seed1/summary.json` | 2026-09-12 09:49:17.840493575 | `seed1_pretest.rc` contains 0; `.out` ends `WRITE_AB_DONE /localhome/local-rohing/v6_out/pretest_write_ab/R2_B_seed1` | 12.851 |
| 2 | R2_B_seed3 | `/localhome/local-rohing/v6_out/pretest_write_ab/R2_B_seed3/summary.json` | 2026-09-12 11:38:11.654462267 | `seed3_pretest.rc` contains 0; `.out` ends `WRITE_AB_DONE /localhome/local-rohing/v6_out/pretest_write_ab/R2_B_seed3` | 15.109 |

Receipt files above are under `/localhome/local-rohing/queue/logs/`. JSON `life` fields matched each run ID, and all ten cell entries were present. Selective aggregate values (8-panel / disjoint means, not recomputed from raw trajectories):

| Run | OFF | A | B | C | B_match | C_tmem |
|---|---|---|---|---|---|---|
| R2_B_seed1 | .483981 / .255430 | .529087 / .273097 | .529087 / .273097 | 0 / 0 | .426789 / .217421 | .122389 / .097243 |
| R2_B_seed3 | .501116 / .250356 | .529089 / .273217 | .520996 / .273097 | 0 / 0 | .468562 / .234006 | .388802 / .144732 |

Both summaries mark both C repetitions collapsed on both panels. Node 2 seed3 B_match has one collapsed repetition on each panel; C_tmem has two on the report panel and one disjoint. Thus terminal completion is explicitly not general success. These aggregate patterns do not supply a contrary positive result for Main's next mechanism question. No cross-life pooling or independence claim is made.

The node2 seed3 summary reports 15.109 GPU-hours, so the older watcher shorthand “finished ones 10.6–13.5” is not a comprehensive bound. Do not turn these fields into a new completion-time forecast. Node1 AC is on a late brief probe but still has no terminal receipt.

Other discovered pretest summaries (metadata only): node1 R2 seeds0/5/6 and cross-node seed0; node2 R2 seeds2/4/7/8, RP_B_seed400 and R4_B_seed601. None has an mtime later than the two latest per-node terminals above. Compile-summary files were excluded from the terminal-summary conclusion.

### Memory-dose — older report terminals and an already-recorded fits-stage terminal

- Node1 run `memory_dose_conf_rep_same`: `/localhome/local-rohing/v6_out/memory_dose_conf_rep_same/report/summary.md`, mtime 2026-09-12 03:53:48.522476893 UTC; sibling `report.json` discovered. `n1rep_same_report.rc` = 0 and log ends `MEMORY_DOSE_FRAMES_DONE step=report`. Read the summary header and first cell, not all underlying evaluations: frame OFF→ON .252→.451, I_d_frame .760 [.395,1.191], spill .264. Summary explicitly labels this synthetic researcher-planted memory, not autonomous consolidation.
- Node2 run `memory_dose_S1_rep_seed1`: `/localhome/local-rohing/v6_out/memory_dose_S1_rep_seed1/report/summary.md`, mtime 2026-09-12 04:27:59.298256512 UTC; sibling `report.json` discovered. `s1rep_seed1_report.rc` = 0 and log ends `MEMORY_DOSE_FRAMES_DONE step=report`. First-cell frame OFF→ON .252→.830, I_d_frame 2.013 [1.365,2.748], spill .392. This is an existing seed/control contrast, not a new selective-memory pass.
- Node2 run `astra_A2_memory_dose_D32_CF_r16_b_ts2_20260912_attempt2`: root `/localhome/local-rohing/v6_out/astra_A2_memory_dose_D32_CF_r16_b_ts2_20260912_attempt2/`; queue job `0052_astra_A2_memory_dose_D32_CF_r16_b_ts2_20260912_attempt2.job`. Queue RC contains 0. Last nine log lines explicitly show TRAIN_DONE/EVAL_DONE for banks0/1/2, 1313 cues per evaluation, and end `[2026-09-12 09:04:30] MEMORY_DOSE_CHILDFRAMES_DONE step=fits`. **Fits/evals-stage terminal only, not report/campaign completion.** Discovered bank2 evaluation path: `eval/bank2__CF_r16_b__across__sleep4__r8__lam1.json`; raw evaluation content was not read. COORDINATION SEQ-067 already records all three bank spills .323104/.294377/.356472 exceeding the unchanged .03 ceiling; those gate numbers are attributed to that existing entry, not independently recomputed here.

Other memory-dose report locations discovered by metadata: node1 `memory_dose/report/`, `memory_dose_conf/report/`; node2 `memory_dose_S1_rep_same/report/`, `memory_dose_S2/report/`, `memory_dose_S1/report/`, `memory_dose_D32/report/`. All are older than the report terminals listed above. Astra A1/A2 roots are separate from these reports and were checked separately to avoid mistaking missing reports for incomplete fits.

## Supplied lease timing — not independently verified

- Node1 expiry: **2026-09-14 23:14 UTC**.
- Node1 backup-by: **2026-09-13 23:14 UTC**.
- COORDINATION additionally supplies node1 finish cutoff **2026-09-14 17:14 UTC**; this is distinct from expiry and backup-by.
- No lease/control-plane lookup, extension, onboarding, backup action or checkpoint transfer was performed.

## Exact command / exit evidence

Primary reproducible inspection bodies were written with `apply_patch` as local files and piped directly into the confirmed wrappers; no script was stored remotely. Exact invocations, all wrapper exits **0**:

```bash
gpu/a40_ssh.sh 'bash -s' < /tmp/astra_node12_selective_read_20260912.sh > /tmp/astra_node1_selective_20260912.txt 2>&1
gpu/ovx_ssh.sh 'bash -s' < /tmp/astra_node12_selective_read_20260912.sh > /tmp/astra_node2_selective_20260912.txt 2>&1
gpu/a40_ssh.sh 'bash -s' < /tmp/astra_node12_terminal_read_20260912.sh > /tmp/astra_node1_terminal_20260912.txt 2>&1
gpu/ovx_ssh.sh 'bash -s' < /tmp/astra_node12_terminal_read_20260912.sh > /tmp/astra_node2_terminal_20260912.txt 2>&1
```

Each transcript emits the exact shell-escaped `COMMAND:` and its individual `EXIT=` alongside returned evidence. Wrapper exit alone is not used as evidence that all checks passed. Principal commands include:

```bash
date -u +%Y-%m-%dT%H:%M:%SZ
hostname
nvidia-smi --query-gpu=index,name,uuid,memory.used,memory.total,utilization.gpu --format=csv
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv
find /localhome/local-rohing/v6_out -maxdepth 3 -type f -path '*pretest*/summary.json' -printf '%T+ %s %p\n'
```

These exited 0 on both nodes. All logged `head`, `tail`, `stat`, `jq`, queue listings and controller `ps` checks exited 0; the twelve logged RC-existence tests exited 1 as expected. No shell executed the CMD strings read from queue metadata. Preliminary exploratory output was sometimes display-truncated; final conclusions use the bounded, saved primary transcripts rather than unseen truncated output. One local documentation search hit an absent `gpu/README*` glob (rg error 2, pipeline masked it); it was not routing evidence. No SSH failure or retry/escalation occurred.

Additional exploratory snapshots are `/tmp/astra_node1_snapshot_20260912.txt`, `/tmp/astra_node2_snapshot_20260912.txt`, `/tmp/astra_node12_metadata_20260912.txt`. The primary transcripts supersede the earlier instantaneous GPU reading.

SHA-256 bindings (local evidence bytes, not remote checkpoint verification):

```text
c3f2d4eea3f5c189afafd83f1f1c47c046d2551af1f8d81138df8254e241c2df  /tmp/astra_node12_selective_read_20260912.sh
b846775b59df38accf0148acb3a1a4e3f5e6b2ef6767e0fa6a11892c995c9b4a  /tmp/astra_node12_terminal_read_20260912.sh
d486db79a100c28f14d26604b31240e012c03aee7149a47aaf627d6c142d3644  /tmp/astra_node1_selective_20260912.txt
cc2f7b086d5396552723b6d3710cecc64016d7714f285d3acb924a55e1b0543a  /tmp/astra_node2_selective_20260912.txt
66905ca3224f07d7c9d4c8f32c053a5a84c62773b7b627bc53027992741fc455  /tmp/astra_node1_terminal_20260912.txt
13045d8aef9b4f9243d944b9d4b4f3e40a15ecfdccf90c9c874f4cdccb993976  /tmp/astra_node2_terminal_20260912.txt
```

## Uninspected scopes / limits

- Main/node3, RuleGame files/processes/results, all other machines, Fable/laptop state and direct messaging.
- Checkpoint/model tensor bytes, credentials, source deployment verification, full provenance hashes, raw probe trajectories, detailed optimizer logs, contamination re-audits and independent recomputation of published metrics.
- Full filesystem outside discovered roots, arbitrary alternative queue locations, inaccessible process environments, cgroups/system services, non-compute GPU clients, scheduler reservation policy, utilization history, host CPU/RAM/disk metrics and sustained throughput.
- Historical failed/rejected job contents and remote hold directories beyond their observed presence/count. No assertion of no crashes anywhere; only no newly completed fill was observed in this bounded scope.
- This refresh ends here: no poll-until-done, queue intervention, broad review, new comparison proposal or launch authorization.
