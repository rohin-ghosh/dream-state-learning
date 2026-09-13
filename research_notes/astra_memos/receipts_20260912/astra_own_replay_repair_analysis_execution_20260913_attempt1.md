# Own-source replay repair: local independent result

September 13, 2026. Authorized completed-mirror reveal. No lifecycle API,
native command, recollection, GPU/model/tokenizer loading, network, Git or
repository edit. All raw source/scored evidence remains unchanged.

## Reduction status and non-material ordering repair

The pre-outcome reducer was verified at its frozen SHA256
`ba039742485f8292e7caf9d728f0b5c9b1c3a0ca03a52ff39b8d4b14814a84cb`.
Its first local reduction rejected the best-constant diagnostic because its
candidate/tie arrays used admission order while the frozen native collector
sorts candidate SHA256 keys. Every candidate score and optimum agreed; only
array order differed. No result directory was created by the failed reduction.

The original reducer, tests and pre-outcome handoff remain byte-identical.
Initial failed argv, exit1, empty stdout and traceback are preserved in
`/tmp/astra_own_replay_repair_analysis_initial_failure_20260913_attempt1.json`
SHA256 `2b49616325394d4f9bdabc1ec7745ba933d037174a7e5e2ef4f14edddfb34ab5`.
This receipt explicitly identifies its origin as a later transcription of the
preserved shell tool output, not a contemporaneous redirected stderr file.
Main independently reports the original14-test suite PASS3.032s.

A separately named copy changes exactly one line, `candidates.items()` to
`sorted(candidates.items())`, matching the already frozen collector. No scorer,
floor, count, candidate set, eligibility or scientific rule changed. A regression
extracts the frozen native `constant_diagnostic` and compares intentionally
unsorted synthetic candidates/ties. Another checks the entire source differs
by only that one line. Original14 fixtures plus2 regressions: **16 PASS,2.946s**.
The corrected reducer then passed all three complete local mirrors, ~3 seconds.

```diff
-        for checksum, raw in candidates.items():
+        for checksum, raw in sorted(candidates.items()):
```

Corrected reducer:
`/tmp/astra_own_replay_repair_analysis_20260913_orderfix.py`
SHA256 `4c06d8ded8ab58814a94f0aab40780a54fa2cf76ca0c7d858d1ab639483b03ab`.

Regression suite:
`/tmp/test_astra_own_replay_repair_analysis_20260913_orderfix.py`
SHA256 `2aef15b05fdcb434640dd3f6ef12318308451873c8ef36c4f7cbb0b4b2f315f2`.

## Per-learner findings

All24 replay responses per seed admitted; original memory banks14/8/8.
Eligibility equals source-correct content for these readbacks. Canary content
and strict are12/12 in every fresh arm. Held correct outputs are canonical;
memory content success does not require canonical serialization.

| Seed | Arm | Exact eligible | Paraphrase eligible | Held content /48 | LR0-correct held losses | Frozen exploratory screen |
|---|---|---|---|---|---|---|
|0|REPLAY|10/14|10/14|47|0|meets|
|0|EXTRA_MEMORY|13/14|10/14|47|0|meets|
|1|REPLAY|6/8|6/8|48|0|misses recall floor7|
|1|EXTRA_MEMORY|7/8|6/8|46|2|fails retention|
|2|REPLAY|5/8|3/8|48|0|meets|
|2|EXTRA_MEMORY|7/8|7/8|42|6|fails retention|

REPLAY preserves every originally LR0-correct held/canary item in all3 learners;
EXTRA_MEMORY preserves them only in seed0. This is a recall/retention tradeoff,
not an all-seed repair: REPLAY meets2/3 screens, EXTRA_MEMORY1/3. Seed1 REPLAY
still misses the predeclared recall floor. No gains offset losses.

Paired REPLAY-only/EXTRA_MEMORY-only success counts, retaining row identities
in JSON:
- Exact: seed0 **1/4**, seed1 **0/1**, seed2 **0/2**.
- Paraphrase: **0/0,0/0,0/4**.
- Held: **0/0,2/0,6/0**.

Raw retention failures, independently rescored with the frozen source scorer:
- Seed0's one held failure in both arms is also wrong under LR0; it is not a
  newly introduced loss (`try:integer_triple_required`).
- Seed1 EXTRA_MEMORY's2 new losses have canonical JSON, correct action/outcome,
  but replace absent prior with observed false and relation `matched` instead
  of null/unavailable. These are prior/source errors, not formatting errors.
- Seed2 EXTRA_MEMORY's6 losses emit records when source requires abstention:
  five missing-outcome cases and one outcome/action-mismatch case. No syntax
  or schema failure explains them; the wrong output variant is selected.
- REPLAY has no newly lost retention items. No fresh-arm memory or held
  length terminations were reported in the rescored panels.

Exact strict-canonical counts REPLAY/EXTRA_MEMORY: **4/5,0/0,0/0**;
exact original-target-byte matches: **8/13,6/7,5/7**.
Paraphrase strict-canonical counts are0 throughout; exact-target-byte matches
REPLAY/EXTRA_MEMORY: **8/8,6/6,3/7**. Valid noncanonical content is not silently
reclassified as failure. Full formats/error breakdowns are in JSON.

## Constant-record diagnostic

For each seed, emit each distinct original admitted raw target as the same
response to every memory cue, assuming stop; report the best same-panel score.
This is evaluator-only, not an executed model/control or a new training source.
Best constant exact/paraphrase is **6/14,4/8,4/8**, respectively. The frozen
candidate universe and all candidate/tie arrays were independently reproduced.

Both fresh arms exceed this limited constant optimum on exact cues. For
paraphrase, seed2 REPLAY is **3/8, below the constant4/8**, while EXTRA_MEMORY
is7/8. Thus meeting seed2's exact/retention screen does not establish robust
paraphrase retrieval or general key binding. Exceeding this diagnostic only
rules out matching these particular constant-target baselines on these panels;
it is not a general anti-shortcut proof.

## Noncontemporaneous references

Historical exact eligible / paraphrase eligible / held correct:

| Seed | HIGH | LOWER | LR0 |
|---|---|---|---|
|0|8 /6 /44|10 /10 /47|0 /0 /47|
|1|7 /5 /37|4 /5 /46|0 /0 /48|
|2|5 /5 /17|4 /3 /47|0 /0 /48|

These are pinned historical snapshots, rescored from their stored raw cells,
not rerun or contemporaneous controls. REPLAY matches LOWER aggregate endpoints
for seed0, improves seed1 exact by2/paraphrase by1/held by2, and seed2 exact
by1/held by1 with unchanged paraphrase. This remains descriptive; replay adds
192 steps per seed relative to LOWER while preserving its112/64/64 memory
presentations. Both new arms start from original perception parents, not LOWER
or HIGH descendants.

## Dose and cost

Both arms:38/32/32 items,304/256/256 updates. REPLAY memory presentations
112/64/64 plus192 observation-replay presentations per seed. EXTRA_MEMORY
memory presentations304/256/256, of which192 are repeated presentations—not
new records. Equal steps do not mean equal memory exposure or token compute.

| Seed | REPLAY supervised/context tokens | EXTRA_MEMORY supervised/context tokens | REPLAY/EXTRA_MEMORY fit seconds | Controller seconds |
|---|---|---|---|---|
|0|8936 /76736|8776 /44112|109.175 /88.525|539.210|
|1|7280 /69792|6368 /37184|97.273 /77.308|477.818|
|2|7624 /69792|7744 /37184|99.271 /80.677|495.145|

Totals: **6fits,1632updates,480generations**, no new source/teacher calls.
Training46728 supervised plus334800 context tokens; generation111598 prompt
plus10297 output tokens. Summed fit552.229s and generation435.597s are nested
within summed controller1512.173s, not additional sequential wall time.
Recorded tensor inventories/norms show finite changes and original-parent
initialization; reducer did not load or recompute tensor payloads.

## Evidence and reproduction

Main archive receipt `/tmp/astra_own_replay_repair_archive_receipt_20260913.json`
SHA256 `1951b264b32491289734c4973b165690b524578d2b641d906dccf50fc72cbe37`
reports archive SHA256
`86c2aadc7b35a50ccb58ad81e4c4733200423d121db75b25afde1112538d8936`,
1248members,507965440bytes,six adapters, all extracted bytes verified by Main.
This sidecar independently pinned the explicit local manifests, snapshots and
JSON stage receipts; it did not repeat Main's full tar/tensor verification.

Input manifest `/tmp/astra_own_replay_repair_analysis_inputs_20260913_attempt1.json`
SHA256 `05c8d1638a48f43d54f1a6bbccd49bf1d7b7e5ae9686ad20971e1cef32ee970f`.
Contains exact plan/completion/score/collection pins for every seed.

Result `/tmp/astra_own_replay_repair_analysis_result_20260913_attempt1/analysis.json`
SHA256 `03ac63e35c3e912533b62474ba4590dee21bbac02ca790511491d3305022bc6a`.

Result `/tmp/astra_own_replay_repair_analysis_result_20260913_attempt1/analysis.md`
SHA256 `2dcd00d35aef27ca9a3c97883c0324b97c732d58858043870fdd32eb76c884a6`.

Commands executed (output is write-once; reproduction needs another fresh out):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp python3 -m unittest -v test_astra_own_replay_repair_analysis_20260913_orderfix

PYTHONDONTWRITEBYTECODE=1 python3 /tmp/astra_own_replay_repair_analysis_20260913_orderfix.py \
  --manifest /tmp/astra_own_replay_repair_analysis_inputs_20260913_attempt1.json \
  --manifest-sha256 05c8d1638a48f43d54f1a6bbccd49bf1d7b7e5ae9686ad20971e1cef32ee970f \
  --source-root /tmp/astra_level1_real_record_source_20260913_attempt1 \
  --protocol-path /data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_OWN_SOURCE_REPLAY_REPAIR_2026-09-13.md \
  --module-dir /tmp \
  --out /tmp/astra_own_replay_repair_analysis_result_20260913_attempt1
```

Three learner pairs, exposed exploratory DEV, not independent episodes or a
pooled causal estimate. No all-seed substrate certification, fresh confirmation,
adaptive parenting, clean ancestry, H1/H2 claim or automatic promotion.

EDITSTOP
