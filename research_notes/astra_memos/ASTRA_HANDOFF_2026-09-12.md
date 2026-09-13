# Astra restart handoff — September 13, 2026, 20:01 UTC

## Current override: prospective warmfix4, no live Main GPU job

Reconciled node2 at19:52UTC: controllers233271,248098/99/100,252471 absent;
`nvidia-smi` reported no compute processes. Recheck both GPU process and CVD
ownership before launching. Acquisition SEQ-194 is complete and unchanged.

Attempt3 failed after200B updates on each seed, before worker completion.
Attempt4 seed0 completed its worker but FAILED outer collection after187.831s
with `warm start: output must be fresh`. Seeds1/2 attempt4 never launched.
Every failed root remains excluded: no recovery certificate, readout, promotion,
or reuse of attempt4. The local unexecuted recovery proposal is archived at
`/tmp/astra_pcfl_unexecuted_recovery_proposal_20260913.py`, not deployed.
Prospective successful full assay would charge19physical fits,6200updates,
24800presentations,288readout calls, including4failed fits separately.

Fresh audit e66edeac and Peirce found freshness checks in BOTH validate_stage
and the controller's final input revalidation. Main now separates read-only
predecessor/input validation from explicit pre-fit helpers. Scientific writer,
material, doses, seeds, four arms and measured A200 parents are unchanged.
Main fit suite:22tests PASS184.480s,2dependency-based class skips; actual native
tiny-model tests and full warm outer/controller regression remain required.

Current ownership (uncommitted work; preserve gpu/codex/dream_state.rules):
- Main: fit module/test, outer module, integration, archives and notebook.
- Russell01a09c54: followup operator, warm overlay, their tests; exact attempt4
  failure chain and explicit two-file repair boundary. Fresh attempt5 only.
- Franklin01a09c56-75c3: outer tests, full warm controller regression.
- Hubble01a09c2d: raw reducer and its tests; terminal stable-source suite pending.
- Peirce01a09c56-a66c: independent read-only code review; re-review pending.
No new native overlay or experiment has been deployed in this continuation.

Attempt4 evidence, including unlaunched seed1/2 plans, is now preserved onVM:
`gpu_artifacts_local/pcfl_v2_attempt4_20260913_attempt1/evidence.tar`,74members,
SHA256e4a7e7c76b27567dda9a9101b87930a1c319b813e6a1ef14b9120e7d80d05b9d.
Native archive `/tmp/astra_pcfl_v2_attempt4_evidence_20260913_attempt1.tar`.
Both SHA256checks agree. Earlier acquisition and attempt2/3 archives remain.

Next: finish full controller tests and independent review, commit/pin repaired
fit+outer+operator+reducer, build fresh warmfix4, native CPU validation, prepare
attempt5 with all failed-work costs, then launch complete matched followups.
Do not repeat acquisition. TSJ-v1 binding and M-COMBINE remain separate future
work; no parenting, H1/H2, mechanism-freeze or completion claims follow here.

## Historical snapshot at19:26UTC — superseded by current override

Mission ACTIVE and incomplete. Reconcile live state before any new launch.
Earlier full handoff is preserved in Git at16842885; the append-only notebook
contains intermediate failures, repairs and launch receipts. Do not restart
completed acquisition, prediction transfer, or historical component tests.

## Standing scope

Rohin: simple hygiene now; formal guard only for final paper-grade C11.
Frozen Qwen2.5-7B-Instruct, LoRA-only learning, provenance/contamination,
parent blindness, matched controls, immutable evidence, owned-process cleanup,
and six-hour lease finish margins remain. No mechanism freeze, general G3,
P1/H1/H2, clean-lineage or full-campaign qualification. Preserve unrelated
`gpu/codex/dream_state.rules`. Pull before writing; append notebook; push logs.
No approval requests made and no curl/wget used in this continuation.

## Current native work: fixed retention-v2 followups

Node2 through `bash gpu/ovx_ssh.sh`. Launched19:26:09UTC:
- Seed0/GPU1 controller248098.
- Seed1/GPU2 controller248099.
- Seed2/GPU3 controller248100.

All roots under `/localhome/local-rohing/astra_diagnostics`:
`pcfl_sequence_v2_followup_seed{0,1,2}_20260913_attempt3`.
Each has `launch.json`, `manifest.json`, `controller.stdout.log`,
`controller.stderr.log`; terminal `completed.json` or `stopped.json`.
Stage outputs are `runs/{PHASE}_{fit,readout}_outer/collection.json`.

Manifest FILE SHA256 by seed:
0 fe342fcaf55488f92a2765649eee95a6676e2d5da0a9ae0ec930612b59c9a76a
1 1ea5884b50582e366de6ab84dd6aaf101e58409c6757a982d129a336b0a4781c
2 1da3e9444b2a132a8456ebfa5158b7621255e82495c2d184a4fce8887974801d

Standalone operator `/tmp/astra_pcfl_v2_followup_operator_20260913_attempt3.py`
is repo implementation at7ee0be92. Launcher
`/tmp/astra_pcfl_followup_launch3_20260913.py` FILE SHA256
4ececc68862847833e763ada34b909bc0087f950f9359bd3c0f3778d0258b357.
Startup delays10/20/30s allow SSH session closure. Actual worker creation and
stage completion must be checked; launch does not establish either.

Each seed runs all four fixed fit/readout pairs, regardless of B200 scores:
1. B200_NEW_DOSE: independent fork of measured A200,200B updates.
2. B400_FIXED_WORK: independent fork of same A200,400B updates.
3. REPLAY400: independent fork of same A200,400updates,800A+800B presentations.
4. CLEAN_CUM600: fresh C0, literal ordered A200+REPLAY400 items.

Additional12fits/4800updates/19200presentations/192calls. Full assay totals
15fits/5400updates/21600presentations/288calls. Perseed2h includes acquisition
and recorded failed-preflight costs;30min stage caps; no automatic retry.
No original checkpoint mutation. Same exposed A4/B4 bank for all optimizer
seeds; not independent worlds. Retention/replay contrasts are still pending.

## Acquisition complete: SEQ-194

Original controller233271 completed at19:15:20UTC, all9stages released.
Root `pcfl_sequence_v2_acquisition_20260913_attempt5` on node2; manifest FILE
SHA2564e41adf04873a5f119f2f372dcb6ab27c561134c8ff7f407e72ec6b242d89731.
All seeds0/1/2 at W0 and W8: C0 A0/4 B0/4; A200 A4/4 B0/4. No truncations.
Raw reducer verified96calls plus full joins.3fits/600updates/2400presentations.
W8 is exposed wrapper transfer only; this is not retention or generalization.

Native reduction roots:
`pcfl_sequence_v2_acquisition_reduction_seed{0,1,2}_20260913_attempt1`.
Receipt FILE SHA256 by seed:
0 045aaf1b99cf714752ccc4ce015f570bb0fc803539a61af7eabc5436ad42c0ea
1 3b0efc7272d83d41e8bc238d35df1f32e151bf90ff055e9f7a84820321ef0cf5
2 a2e14c6d68e7e3fe2de8d8e5093aa5dd9d2f7e50263dc35a7c755f8ce03fb6bd

Verified native/VM archive:
`gpu_artifacts_local/pcfl_v2_acquisition_20260913_attempt1/evidence.tar`
SHA256fdc22c730206c5c9e6486099fc908b5daaaad78916c106eeb4f738fa86446879.
Includes originals, all3fits/raw readouts, reductions, input prerequisites and
source tar. Native `/tmp/astra_pcfl_v2_acquisition_evidence_20260913_attempt1.tar`.

## Validation-only compatibility repair

Original immutable source commit71adf462cfdc17d94f95298e76949e08da38e410
at `/tmp/astra_pcfl_sequence_v2_source_20260913_attempt2`; tar SHA256
21936c7acdd2fe846fb4ce78de2b5b2f86f13df8cdbf4c0be3211b887c28fc1b.
Never hot-edit it. Acquisition uses this original source.

Followups use `/tmp/astra_pcfl_sequence_v2_source_20260913_warmfix2`:
only `validate_warm_tensors` code changed; outer is byte-identical regular copy;
other files symlink to original sources so resolved material pins remain exact.
Repair commitfad676bb272e8deffaf87aa651b14ce0c3536ce0.
Repair receipt FILE SHA256
ba1ed31aff1021d6e4ea02c90eb935c0ae433bb0c4ea30922e56f5229b0888e8.
Old material/spec and measured A200 receipt/checkpoint remain identical;
no re-export or changed training/data/scoring rule. Sparse actual-conversion
maps now match the real writer receipt, with complete tensor verification.

Native real CPU Qwen2/PEFT warm initialization4testsPASS3.908s. First direct
script invocation ran zero tests; attempt2 unittest is the counted receipt.
Main29operator/overlay testsPASS0.444s. Latest native preflight validated exact
material reconstitution and all12outer inputs plus node/environment checks;
receipt FILE SHA256d9aab696b459901aac13c49f181237784a0c1296aa7ea38addf5f5dee24a2b7d.
Logs/receipts in `research_notes/astra_memos/receipts_20260912/astra_pcfl_v2_validation_20260913/`.

Preserve failures: acquisition prep1–4 and batch4 had zero workers;
warmfix1/seed0 followup prep1 failed CPU outer aliased-path check;
all3followup attempt2 controllers failed pre-node missing explicit empty CVD,
worker_identity=null,returncode=null,stage_inventory={}. Zero model calls or
updates there. Attempt3 operator sets CPU-controller environment and charges
those7.809/7.742/7.856seconds respectively. No retries after worker execution
are currently supported; diagnose and version rather than overwriting.

## Agent ownership / next actions

Hubble `01a09c2d-1140-7493-82ef-d72b5fa7e178` owns ONLY new
`gpu/astra_pcfl_event_sequence_v2_reduce_followup.py` and corresponding test.
Await EDITSTOP. Task: final all-four raw reducer with A/B vectors, proper warm
ancestry, releases/inventories, and dose/work/cumulative contrasts. No remote
or launch permission. Raman EDITSTOP/closed; Main owns all integration.

1. Reconcile current followup worker identities/stages; no blind re-launch.
2. Finish raw reducer/tests while GPUs run; inspect raw outcomes only after
   complete controlled collections, then archive with checksum verification.
3. Report all arms, failed costs and limits. Update manuscript/claim map only
   with verified evidence; no automatic H1/H2 promotion.
4. Continue parenting/composition work from message43 and binding successor,
   without treating partial source fixtures as qualified model experiments.

## Other completed work / research gaps

SEQ192 prediction transfer branch STOPPED: three-seed continuation FALSE.
Primary288calls, failed192calls retained=480actual; zero new fits. FULL OFF16
perseed/post24,23,19; MINIMAL OFF14/post24,1,18, all/24. No rescue. Result note
`research_notes/analysis/2026-09-13_level1_prediction_transfer_result.md`;
paper/TeX/claimmapC105/UNSENT collaborator draft updated; abstract unchanged.
No TeX build claim. All primary/failed archives already verified onVM.

Composition fixture at e28df7f3 is only partial Stage0 source:32 authored tiny
tasks, grammar/exact memory/oracle,11CPUtestsPASS. Fixed-READ/STOP32/32 are
memory-using ceilings, NOT task-blind shortcuts. Rich domains, cross-domain
motifs, C/S coupling and36pairwise null definitions missing. NO_GO_PARTIAL.
Read message43 adjudication and newer M-COMBINE4 staged/binding successor
before extending. Stage2A design bound CLOSED vs ATOM-LOCAL, not executed.

Node2 lease September21 08:43UTC; all runs finish≥6h before expiry. Node1
expiry September14 23:14UTC; preservation deadline September13 23:14UTC.
Relevant prior prediction adapters/evidence already onVM. Latest acquisition
also preserved. Followup evidence not yet transferred. No guarantee that
other agents' node1 data is mirrored; verify if needed, do not assume.
