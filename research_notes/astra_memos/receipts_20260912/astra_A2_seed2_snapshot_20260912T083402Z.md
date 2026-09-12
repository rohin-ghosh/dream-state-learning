# A2 seed2: still running; one new evaluated bank

**Node2 snapshot 2026-09-12 08:34:02 UTC:** queue0052 PID3560937 is running on GPU1, PPID1823897; started07:41:12 UTC per queue receipt. No stage-completion marker. Bank0 and bank1 have fit DONE; only bank0 has completed evaluation. Bank0 TRAIN_DONE08:05:22/EVAL_DONE08:08:43; bank1 TRAIN_DONE08:32:58. Bank1 eval and bank2 fit/eval remain outstanding/unconfirmed as of this snapshot. No terminal state, final RC or campaign completion is asserted. No repeated status polling/waiting.

Run: `/localhome/local-rohing/v6_out/astra_A2_memory_dose_D32_CF_r16_b_ts2_20260912_attempt2`. Fixed-scope raw capture08:35:05 UTC; archive verified08:36:38 UTC. Compared with08:04:18, this adds two completed-fit receipts and one completed fit/eval, not two new optimizer seeds.

## Unchanged G9, bank0 only

Cell CF_r16_b, optimizer seed2, source bank seed0. **Source-compatible;1313 cues;16 paired dose16 owners; no missing controls.** Mean I_d_frame **1.184902794133669**; within-fit/bank95% percentile interval **[0.736801601373312,1.8112251421790742]**; frame spill **0.3231037216369375**. **G9 FAIL**: positive lower bound, but spill exceeds unchanged0.03 limit. Bootstrap seed0,2000 owner-paired resamples. No pooling/causal inference or threshold changes.

New evidence comprises **one evaluated artifact from one family/optimizer-seed configuration**, plus bank1's fit-only receipt. Bank1 has no evaluated G9 result and is not counted as pass/failure. Adding this artifact to main's previously reviewed12 gives a historical-plus-new bookkeeping count of **13 evaluated artifacts/13 G9 failures**, not13 independent seeds or a pooled failure-rate estimate. Family/seed configurations represented: A1{2,3}, A2{0,1,2}; five family/seed configurations, with6 A1 and7 A2 evaluated bank artifacts. Prior12 outcomes were not re-inspected or reanalyzed.

Bank0's complete source-input hash map exactly matches prior A2 bank0 seeds0/1, checked using only previous analyzer JSON identity references. The isolated one-entry analyzer's reference-seed-unavailable fields mean absent from this new invocation, not globally missing. Frozen experiment source `f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d`; captured definitions hash `ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3`; unchanged analyzer hash `e1327b3d2fdc060e33aad3d088beada167226437a9b1e6f28b819c6b5959eea9`. Analyzer exit0/empty stderr; output SHA256 `dcdb2d9c18264586d08111f69204b8ad7613199bdbdf7520121865da173d2f3f`.

Label remains **SYNTHETIC_DIAGNOSTIC_NOT_CLEAN_LINEAGE**. Fit-DONE is not eval-DONE, G9 failure is not runtime failure, and none establishes H1/H2 or parenting. No original failed attempts were altered. No notebook, Git, source edits, reruns, experiment launches/stops, remote writes or external fetches.

## Frozen raw custody

- Capsule/report: `/tmp/astra_A2_seed2_terminal_20260912/README.md`. Capsule write bits removed; the requested directory name does not imply terminal status.
- Archive: `research_notes/astra_memos/receipts_20260912/astra_A2_seed2_snapshot_20260912T083402Z_raw.tgz`, **2108802 bytes**.
- Archive SHA256: **80a30ec80cfb53e856be00e7ae82f4a4a5aa6bdc3c56156ca264e32dd97536d8**.
- Capsule SHA256SUMS SHA256: **99c25498e2e6b617f32a83061651f17552bbc730914d4fbce9b04bac9da202f9**.
- **25 remote file identities verified**, all stable; **43 archive payload hashes plus SHA256SUMS verified**. Full new bank0 eval, training metadata/DONE, required inputs, bank1 fit receipts, runbooks, frozen analyzer, queue/launch/log receipts, commands/results, and manifests included. No prior completed-bank evals recopied.
- Adapter binaries omitted but original node2 paths/hashes recorded in CAPTURE_MANIFEST.json; both confirmed present at capture, each80792096 bytes. Bank0 SHA256 `2a638bb476071bc21127d94735718cfc4e3936d49eb961100606e3eef19fd18d`; bank1 `f3f8a3755ee4578670bf91f5bab6dfd47eb599dec50c097d2efba9e8bba8fed5`. No future retention guarantee. Base/runtime binaries likewise not bundled; this archive is self-contained for the reported bank0 CPU analysis, not model inference.

```bash
(cd /tmp/astra_A2_seed2_terminal_20260912 && sha256sum -c SHA256SUMS)
(cd research_notes/astra_memos/receipts_20260912 && sha256sum -c astra_A2_seed2_snapshot_20260912T083402Z_raw.tgz.sha256)
```

Keep the raw archive with any owner-performed custody commit; adjacent checksum/validation JSON alone does not preserve raw evidence. No further remote inspection in this task.
