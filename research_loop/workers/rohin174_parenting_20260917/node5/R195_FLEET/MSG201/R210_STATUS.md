# Original C2 R210 — finite intermediate status

## Ownership check — September18,2026 05:22UTC

Reported GPU4 PID3376586 is legacy C4/native2606742's readout child;
GPU6 PID3374391 is legacy pilot/native2757295's readout child. Exact PPIDs,
resident-dispatch IDs, plan hashes and GPU UUIDs match. Both children have
exited; original natives still reserve their slots. These are not newly
launched clones. Metadata-only audit, no diagnostic content/scores read,
no signals sent. Proof: `R210_GPU4_GPU6_OWNERSHIP.json`.
Original C2 at05:21:03: native3371337 running, head6765, all169 source pins
match; no waiting genuine Rohin IDs since R209. Actual first resumed LEARN
is REQUEST6748, not pending model load.

## LIVE AGAIN — September18,2026 05:20:20UTC

Recovery LOADED6743 at05:19:42.312UTC, native3371337, receiver
`/localhome/local-rohing/orch_r210_C2_20260918_resume2`. Exact current6739
history/three pending rows and complete61/AdamW5404 retained. Receipt6744
discloses saved checkpoint RNG use, not exact resident sampling continuation.
First action LEARN REQUEST6748 at05:19:43.510,8900 masked tokens, with the
same-parent corrective source `854bedce11f54d18a4cad0af84d6c650` rendered.
No human reply replay. Same parent3148600 continues.

Review6752 and native TARGET_ELIGIBILITY6758 exclude Chinese-drift
THINK6731/segment188 (26CJK+2fullwidth), raw unchanged. Three of four NEW
rows retained,16 presentations each,0 old;48 updates scheduled for sleep62.
Head6760 shows training started, not a completed-sleep claim. Homework/story
content is still incomplete: the actual reply and LEARN mistake two paragraphs
for two complete drafts. The parent has called out that mismatch, not answered
for the child. Proof: `R210_REPAIR_LIVE_RECEIPT.json`.

## Recovery update — September18,2026 05:17UTC

The human reply DID commit at RESPONSE6738/05:13:35.296UTC and receipt6741
at05:13:36.336. It is English but mistakenly supplies two paragraphs rather
than two complete drafts and claims completion. No replay is authorized.
Native3356655 then exited before LEARN because my helper used the wrong
phase marker. Latest committed state6739/head6742 and three pending rows
remain unchanged; no cycle62 updates happened in this failed incarnation.

Six regression tests now PASS including prepare_sleep and target exclusion.
Receiver `/localhome/local-rohing/orch_r210_C2_20260918_resume2` preserves
complete61/model+AdamW5404+saved RNG and the exact CURRENT conversation,
inboxes and three pending rows. Exact real state round-trip passed. Its
one-state native recovery exception is hash-bound to committed6739; it does
not relax other boundaries. Wrappers launched; actual LOAD pending.
Next action is LEARN review, not another human reply. Post-generation
resident RNG was lost on exit and is NOT claimed exact; saved61 RNG is used.
Same Astra remains active. Actual status supersedes the older live cut below.

## LIVE update — September18,2026 05:13:20UTC

LOADED6716 at05:12:51.137UTC, native3356655, same original root and
COMPLETE61/AdamW5404. Actual original question + same-Astra guidance render
REQUEST6722 at05:12:53.062/6932 masked tokens; first THINK RESPONSE6723
at05:12:59.173. Actual Astra feedback `8d8eb9ed14984a0cbf35a34b7f5e0852`
rendered REQUEST6730 at05:13:09.026/7937 tokens, then second THINK
RESPONSE6731 at05:13:16.590. Direct human ACT REQUEST6737 started only
afterwards,05:13:18.638/8374 tokens, console-only policy/tools off. No completed
reply at this cut. First THINK mostly stated intention; second gave an initial
long-horizon idea but drifted into Chinese. No homework-success claim; verify
actual R209 exclusion at LEARN. Raw sources and responses remain unchanged.

## Earlier finite cut

September18,2026 05:12:07UTC observation, original life unchanged.

- Genuine homework inbox `e540198699ee4ddb9fbfd8b34b72ced3`, file time
  04:56:24.638UTC, SHA256
  `e20cf2a83b24f02382c3fc2329015934e343a6a5e7a7ce80bb6ac283ebe7563b`:
  not consumed/replied at this cut. Watcher05:37 was not the source time.
- Safe pause05:04:21.087UTC at sleep61 COMPLETE6714/head6715;
  AdamW5404 (32 updates in61). Full checkpoint, history, journal and inbox
  copied and verified under old control `R210_HOMEWORK_BOUNDARY/`.
- Same Astra parent PID3148600, same programme/branch/provider. Actual
  homework guidance published05:06:40.898UTC, inbox
  `cb9708bceba74cf691fe1031eb1a327d`; not yet rendered at this cut.
- Original-only R210 receiving root
  `/localhome/local-rohing/orch_r210_C2_20260918_resume1`;
  wrappers started05:10:13.432UTC; native3356655 is loading, not yet LOADED.
- Tested route: exact genuine source, two actual child THINKs with genuine
  parent feedback between them, then one source-bound tool-off reply. No
  parent answer/completion claim. Four narrow CPU tests PASS. English target
  quarantine/pins/recipe/wall remain R209 unchanged. No human inbox writes.
- No history/weight rollback. Earlier16 corrupt updates remain. Saved
  checkpoint RNG is preserved; earlier R202 resident post-console sampling
  RNG was not separately captured, so no full-live-RNG continuation claim.

Machine-readable finite observations: `R210_CURRENT_RECEIPT.json`.
Same-parent publication: `R210_PARENT/run/parent_000000/RESULT.json`.

## Transfer to other operators

`R209_FLEET_BUNDLE/READY.json`, `runtime_overlay.tar.gz`, `README.md`.
Archive SHA256
`ccd62dbb0483240c23ac5caddc23cf5e7ee4a54b45e6896e49267f5f2efd60ec`.
42-file R206 frame, two runtime changes,62 shared tests PASS, zero skips.
READY status is `CPU_TESTED`. Preserve per-arm P4/P16/P32, plasticity/LR,
optimizer groups, anchor, wall and treatment; merge feature maps only.
Rebind existing source/bridge pins, reload at exact COMPLETE, report actual
LOADED/REQUEST/review. R210 original-only exception is NOT in fleet bundle.

## Node5 actual inventory

05:11:31UTC: original1 receiving3356655; legacy C1/0=2707975,
run1/2=2495635, C3/3=2668022, C4/4=2606742, C5/5=2761060,
pilot/6=2757295. No native GPU7 observed by this native-entrypoint scan;
repo_reader remains untouched. Six staged clone roots still have no
STARTED/ARMED/RETIRE/READY receipts and no matching native processes.
Do not call these six legacy lives new clones or claim withdrawn controls
were newly parented. Descartes now owns node5 enrichment; no competing clone
launch or retirement is armed by this operator.
