# Replication execution preparation — September 19, 2026

**Latest (after Main's terminal CPU proof): `CPU_CUSTODY_V2_HANDOFF.md`.**
V2 is a distinct CPU-only isolation/dependency diagnostic and audited dead-claim
disposition, with 66 tests. The failed scientific block remains terminal; no
model execution is enabled by V2. Use its sealed commands, not the older
restaging/model-dispatch instructions below.

**Current execution handoff: `EXECUTABLE_HANDOFF.md`.** The seed-aware runner,
original shared admission integration, immutable release and guarded repair
of Main's unlaunched CPU-staging failure are implemented; **52 CPU tests pass**.
Receiving role proofs and any dispatch remain Main's responsibility. The
earlier missing-runner/admission blockers below are retained as historical
preparation notes, not the current implementation status. The original source
seal remains preserved; use `EXECUTABLE_SOURCE_FREEZE_REPAIR_V1.json`.

**Historical preparation report follows.**
Workstream 2 did not launch, stop, signal, register, or modify any native,
scorer, daemon, original bundle, queue policy, or capsule registry. Main owns
all launch decisions. No commits or pushes. Everything written is in this
`replication/` directory; remote work was bounded read-only metadata/source
verification through `gpu/ovx4_ssh.sh`. No private caption/panel text or model
weights were transferred to the VM or delivered to a parent.

## The missing age24 comparison is already available

The activated V4-rebind job is the frozen sibling's completed sleep24 job,
not the stale V3 construction handoff. Its registry still has exactly that
one capsule. Its original no-retry identity must not be relaunched.

`history.json` already marks **FRESH_R231_s24 PRIOR_COMPLETE_NO_RETRY**.
The old learner and the newly completed sibling use the same original
103-file scientific closure, original judge adapter, reference panel, scenes,
decoder, and two seeds. Their checkpoint ages and source compute match the
requested age24 comparison. No additional learner24 run is needed to fill it.

Fresh read-only receipt: `ORIGINALS_RECEIPT.json`, observed
**2026-09-19 13:08:13 UTC**. Counts deduplicate scene/caption pairs **within
each seed**; replayed returned new-pixel statuses are not counted again.

| Original-judge source | Seed | Tokens | Distinct scored | Accepted | New pixels | ACTs without scored strings |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Learner sleep24, 1,152 updates | 23201 | 3,072 | 35 | 0 | 0 | 6 |
| Learner sleep24, 1,152 updates | 23202 | 3,072 | 82 | 23 | 11 | 1 |
| Frozen sibling sleep24, 0 updates | 23201 | 3,072 | 53 | 28 | 14 | 0 |
| Frozen sibling sleep24, 0 updates | 23202 | 3,072 | 38 | 17 | 14 | 0 |

One learner outcome has no rank because the existing scorer rejected it as
`injection_detected` (`ok=true`, `scoring_status=relative_rank_development`),
not a provider outage. `unscored_outcomes` in the inspection receipt means
rankless unique outcomes; it must not be automatically interpreted as a
scoring failure. Its text was not exported.

The learner's operational pixel count is lower in both seeds. This is one
existing training lineage pair, not a replicated training experiment, and
judge acceptance is not certified humor. The observations occurred at
different wall times; no claim is made of identical historical parenting.

### Do not mix this with the adopted-judge block

The September 18 adopted rank8/step15625 block already completed **both**
age24 arms: learner pixels **6/19**, sibling **15/24**. Its independent
judge epoch is
`216f34224e27a2ced6671026c482041c3e6024aecbabd105341a365d2935268a`.

The V4 sibling's **14/14** is under the **original judge**, not this adopted
epoch. These are separate game trajectories because feedback affects later
generation. Pairing 6/19 with 14/14 would silently change the evaluator.

## Shortest next replication

**Recommended: a separately preregistered sampling diagnostic of base /
C2 sleep51 / C2 sleep117 using new seeds 23301 and 23302.** All three
preserved sources are present and source-verified on ovx4. This directly
tests sampling robustness of the promising historical comparison, without
changing a live learner or producing new checkpoint weights.

An alternative two-arm sampling diagnostic repeats the adopted-judge
learner24/sibling24 comparison at those same new seeds. It is cheaper, but
neither diagnostic supplies independently trained lineages. Three development
scenes remain the same; this is not a fresh-scene generalization experiment.

No unattempted runnable capsule was found in the active V4 registry. The
inspected preserved pair-source directories contain learner12/24 and
sibling1/24; learner12/24 and sibling24 already have recorded attempts.
Sibling1 is historical and not eligible under the unchanged prospective
frontier. A genuinely new age requires capture, exposure audit and binding
of a new completed source; it cannot be supplied by renaming a consumed
capsule or lowering the frontier.

### Candidate artifacts

- `C2_SAMPLING_CANDIDATE_V2.json`: three source templates, 18,432 generated
  tokens total; diagnostic epoch
  `4df129caf0a0377ba91feec83923bc972e00b10dab13b5b198594db567689d95`.
- `PAIR24_SAMPLING_CANDIDATE_V2.json`: two source templates, 12,288 tokens;
  diagnostic epoch
  `e7494c233e14c97307c5606937cbf0fb871b55dbdf2c02d3e92ae54ed45bb222`.
- `construct_candidate.py`: pure CPU config construction. Validates existing
  completed-source, exposure, parameter, judge, scene, source-closure, decoder,
  cell-budget and lease identities. It only writes a new local artifact.
- `sampling_cells.py`: CPU-testable seed-loop adapter. It hash-loads the
  **unchanged original `contract.run_cell`** and supplies the new seeds;
  THINK/ACT prompts, feedback flow, per-call limits and actual-token accounting
  are unchanged. It does not instantiate a model, implement a scorer, claim
  GPU admission, or launch anything.
- `RECEIVING_SOURCE_CHECK.json`: at **13:11:54 UTC**, all **111 original
  source files per adopted arm** matched the frozen manifest, and all four
  captured checkpoint files matched for each of the four adapter arms.
  This is not a replacement for fresh receiving admission at launch.

V1 candidate artifacts are preserved. **Use V2**, which additionally retains
the C2 preparation's stricter September 30 00:00 UTC bound. Neither version
contains a dispatchable `root`, deadline, capsule, launch intent, or guard.

## Exact implementation blockers

1. **Seed-aware receiving runner.**
   `post_recovery_age_queue_20260918/epoch.py:require_config` and the original
   adopted `runner.py` hardcode seeds 23201/23202. Changing config alone will
   fail; monkeypatching these validators would invalidate the protocol receipt.
   Integrate `sampling_cells.run_cells` with the original backend and scorer
   in a separate, sealed diagnostic runner. Bind the new sampling-epoch hash
   in config, REQUEST, scoring reply, LOADED, COMPLETE and report receipts.
   Preserve the existing judge/panel epoch as a reference, not as a claim that
   the old seed-containing experiment epoch has been rerun unchanged.

2. **Original shared admission/claims integration.**
   The active V4 queue supports only the two pair journals, original judge,
   and original battery. It also disallows reuse of any attempted source key.
   C2 and new-seed diagnostics are therefore not valid V4 capsule submissions.
   Main must bind a separate finite diagnostic lane to the **existing shared
   claim namespace**, with new attempt identity and no automatic retry. Do
   not call the old unclaimed `post_recovery_age_queue/dispatch.py` while
   the queue daemon may use GPUs2/7. Do not use another namespace to bypass it.

3. **Fresh custody and receiving proof.**
   Re-verify the captured checkpoint/exposure, exact scientific files, source
   closure, current host/lease/UUID/protected-handle state and role isolation.
   Private reference panels/cached panel scores remain scorer-only. Only the
   original model-facing scene and tool feedback may reach the player, and
   no evaluation scores reach a live parent. Same-UID permissions alone do
   not establish private-panel isolation. A fresh unconsumed launch intent
   is required; no consumed guard is included or reused by this workstream.

These are implementation gaps, not a request for additional scientific
permission. Main can execute after integrating and testing them under the
existing authorized scope. No claim of GPU readiness is made here.

## Resources, costs and existing bounds

- ovx4 / `ipp2-ovx-p3-02`, player physical2
  `GPU-ac7e4165-630c-eafe-4ba5-2b2fc4a4e5d1`, judge physical7
  `GPU-b7ec9035-3ba3-464f-6c2f-7588a3e328c1`; no fallback devices.
- Main's 13:06:43 UTC free-device observation is historical, not reusable
  launch admission. Protected devices0/1/3/4/5/6 remain untouched; the live
  queue daemon may claim2/7 at any time.
- Shared claims namespace:
  `/localhome/local-rohing/post_reboot_probe_dispatch_20260919/dispatch_locks`.
- V4 policy: one two-GPU job at once; 2,400s per-job maximum; 30s teardown
  margin; hard end **September 30, 2026 17:59:30 UTC**; lease boundary
  **October 1, 2026 00:00 UTC**. These values are read from the existing policy,
  not a lease extension. C2 preparation's existing stricter bound is
  **September 30, 2026 00:00 UTC**; V2 uses the earlier applicable limit.
- Actual measured historical player+feedback wall time: C2 base325.0s,
  sleep51 383.0s, sleep117 473.3s; serial total **19.7min**, excluding
  separate judge startup/admission/staging. Budget roughly **25–35min**
  for the three-arm block after integration, not an operational ETA.
- Adopted learner24 385.5s + sibling24 364.4s = **12.5min** measured;
  budget roughly **18–25min** for the two-arm alternative. Current novel
  outputs may change call counts. Do not report these wall times as measured
  GPU compute; training compute is separate, and evaluation updates are zero.
- Per source: two seeds × three scenes ×1,024 actual generated tokens;
  3,072 tokens/seed, 6,144/source. Zero parent tokens and training updates;
  no historical working context, optimizer or RNG loaded.

## Exact CPU-only commands

From repository root:

```bash
WORK=research_loop/workers/replication_sprint_20260919/replication
python3 -B -m unittest discover -s "$WORK" -p 'test_*.py' -v
RECEIPT_SHA=$(sha256sum "$WORK/ORIGINALS_RECEIPT.json" | cut -d ' ' -f 1)
python3 -B "$WORK/construct_candidate.py" \
  --receipt "$WORK/ORIGINALS_RECEIPT.json" --receipt-sha256 "$RECEIPT_SHA" \
  --seeds 23301 23302 --block c2 --output "$WORK/C2_REVIEW_COPY.json"
```

The output name must be new. Use `--block pair24` with a different output for
the paired diagnostic. These commands cannot launch; attempting to feed the
result to the original dispatcher is an error, not the next command.

Optional fresh **read-only** receiving verification through the original route:

```bash
bash gpu/ovx4_ssh.sh 'python3 -B -' < "$WORK/verify_receiving_sources.py"
```

No GPU command is represented as executable before the three blockers above
are resolved. Main owns source staging, new capsule/intents and actual launch.

## Validation and dependency closure

**21 CPU tests pass** in `CPU_TESTS_BOUND_CHECK.log`. They exercise original
pair alignment, cross-judge rejection, original-budget/source/decoder
validation, new-seed identity, immutable receipt inputs, no forged guard or
deadline, stricter C2 bound, per-seed deduplication, exact six-cell sequence,
unchanged THINK→ACT feedback, private-context rejection, and incomplete
generation handling without retry. The initial test-only repository-root
index error and its log are preserved; it was fixed before the green runs.

Real receiving dependencies, already available and source-checked:

- Original adopted closure `bcdd5adbcd03bc52e0ae20ca400cd6b328bc9d89aeb19a3f1d9fbae20b3e5c7b`:
  `post_recovery_age_queue_20260918/{runner,epoch,observe}.py`,
  `rohin232_age_probe_20260918/{contract,runtime}.py`,
  `rohin233_kept_age_probe_20260918/probe.py`,
  `rohin221_continuous_caption_20260918/freeform.py`, and the caption
  data/game/pixel/relevance/scalar/similarity modules. Per-file pins are
  copied from the original manifest into each candidate.
- C2 immutable receiving roots:
  `/localhome/local-rohing/orch_post_recovery_c2_age_eval_20260918/{base,c2sleep51,c2sleep117}`.
- Paired adopted roots:
  `/localhome/local-rohing/orch_post_recovery_age_20260918_attempt3/{learner24,frozen24}`.
- Adopted scalar config:
  `/localhome/local-rohing/orch_r233_judge15625_20260918/judge15625-base-v1/primary_scalar.json`.
- Existing reference epoch and private calibration remain on ovx4 at each
  block's `epoch/`; they are identified by hashes, not exported as text.
- Original V4 source freeze
  `d77089e8d7eb3ff06e709fb8f16c9555a2c620a614fe9c335a516c54475061e0`
  and capsule registry
  `2e04590f6265e4759222283c1d9843c13d81eb3ded6878c6e7eaf086136f2b37`
  were read and preserved. **Do not execute `CONSTRUCT_NEXT_CAPSULE.sh`; it
  still addresses the already-completed job and stale V3 construction.**

No copied multi-GB journals, new training lineages, model loads, parent
messages, forced process actions, registry edits, or platform-denial retries
occurred. These artifacts support a controlled next run, not a new outcome.
