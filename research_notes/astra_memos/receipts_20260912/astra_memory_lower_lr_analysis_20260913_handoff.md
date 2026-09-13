# Lower-LR stored-result reducer — EDITSTOP

September 13, 2026. CPU-only analysis implementation, prepared without reading
new candidate outcomes. The subsequently authorized result reduction is appended
below; reducer/test bytes are unchanged. Main owns native lifecycle/collection.
No model/native/network/Git actions, old-file edits or repository changes.

## Owned files and pins

- `/tmp/astra_memory_lower_lr_analysis_20260913.py`
  SHA256 `123e2088804d0c9f7ac548330816884e495a2ec83f79b446e182ea13010b18f4`
- `/tmp/test_astra_memory_lower_lr_analysis_20260913.py`
  SHA256 `72c2b947ba5c05a2a578e6048bcd451f2253f46f572e27f1c9f5a99bf9cb6222`
- This handoff's SHA256 is supplied externally.

Output schema: `astra_memory_lower_lr_analysis_20260913_v1`.
Protocol pin remains
`122965224f6a72d1fb852a40dd24c02b78c733751337f37513712f0f3b45bbce`.

## Stable API

```text
reduce_seed(candidate_scores_dict, historical_scores_dict) -> seed_report
load_collected(collection_binding, plan_sha256, completion_sha256)
    -> (scores_dict, resolved_file_provenance)
reduce_manifest(manifest_path, manifest_sha256) -> analysis_report
```

Use the manifest API/CLI for collected evidence. `reduce_seed` is the
in-memory arithmetic interface and requires its caller to authenticate input
objects separately. Neither API reparses model raw answers, recomputes semantic
scores, invokes a collector, nor accesses native model/adapter directories.
The only imported old functions used are the unchanged pure `paired_counts`
and `repair_screen`, plus fixed scope/history pins. Standard-library-only
imports of those frozen files perform no native work:

- `/tmp/astra_memory_lower_lr_run_20260913.py`, SHA256
  `80467204aa7ccb4a1cbf4f8d85c7be4e7347263f98f4f7b8fef5739980fcf413`
- `/tmp/astra_real_record_memory_run_20260913.py`, SHA256
  `7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e`

These exact source files must remain available locally. Their hashes are
checked on each helper load. Old worker/verify/fit/readout/score/collect
functions are never called. The independent reduction derives panel totals,
formats, field counts, paired changes and retention item classifications from
stored score booleans. It checks its totals and paired counts against the
collector's summaries and its frozen screen against the collector's screen;
disagreement fails rather than silently overwriting or repairing a report.

## CLI and closed manifest

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 60s python3 -B \
  /tmp/astra_memory_lower_lr_analysis_20260913.py \
  --manifest /tmp/MAIN_OWNED_lower_lr_analysis_inputs.json \
  --manifest-sha256 ACTUAL_MANIFEST_SHA256 \
  --out /tmp/MAIN_OWNED_lower_lr_analysis_results.json
```

No candidate bindings have been guessed. Main provides completed collection,
plan and completion hashes after collection. Paths may point to local archive
copies; source collection paths in the original report need not be relocated.
Content hashes, not rewritten provenance paths, bind the imported evidence.

Manifest has exactly `protocol` and `runs`. Each run has exactly the five
fields shown. One to three distinct seeds0/1/2 are accepted; partial results
explicitly leave the all-three screen unknown, never silently pass missing
seeds. Failed/missing collections are errors, not zero-score observations.

```json
{
  "protocol": {
    "path": "/ABSOLUTE/LOCAL/COPY/ASTRA_ACTUAL_MEMORY_RETENTION_REPAIR_2026-09-13.md",
    "sha256": "122965224f6a72d1fb852a40dd24c02b78c733751337f37513712f0f3b45bbce"
  },
  "runs": [
    {
      "seed": 0,
      "candidate_collection": {
        "path": "/ABSOLUTE/LOCAL/seed0_lower_lr_collected/collection.json",
        "sha256": "MAIN_SUPPLIED_CANDIDATE_COLLECTION_SHA256"
      },
      "candidate_plan_sha256": "MAIN_SUPPLIED_CANDIDATE_PLAN_SHA256",
      "candidate_completion_sha256": "MAIN_SUPPLIED_CANDIDATE_COMPLETION_SHA256",
      "historical_collection": {
        "path": "/tmp/astra_memory_collected_20260913_attempt1/real_record_memory_seed0_20260913_attempt1_collected/collection.json",
        "sha256": "fbbc8ddf580e2141c01a3b73477605e7e5a77bc8e638126475950ea1f105dfab"
      }
    }
  ]
}
```

The placeholder candidate values deliberately make this non-executable until
Main binds actual completed artifacts. Each adjacent `scores.json` hash is
read from its pinned `collection.json`; plan/completion joins are checked.
The three historical plan/completion/collection/score pins come unchanged
from `runner.HISTORY_PINS[seed]`. Candidate imported historical cells must
exactly match the independently loaded historical file, and the historical
binding embedded in the candidate must agree with those pins.

Output uses exclusive creation and refuses an existing file or output
symlink. No input is written, no collection claim is consumed, and rerunning
analysis against identical inputs is deterministic. Use a new output path
for a subsequent partial/full roster analysis. JSON duplicate keys and NaN/
Infinity are rejected; each input JSON file is bounded to64MiB. The supplied
60second command timeout is for CPU analysis, not a native run lifecycle.

## Output and unchanged interpretation

For each `seeds[]` entry:

- `panels.LOWER_LR`, `.HIGH`, `.LR0`: exact/paraphrase/held/canary totals.
  Memory metrics remain `production_eligible`, `content_correct`,
  `strict_canonical`, `exact_target_bytes`; retention metrics remain
  `passed`, `content_correct`, `strict`. Format counts and four memory-field
  agreement counts remain separate. No content/format endpoint is promoted
  into source-faithful production eligibility.
- Fixed exact/paraphrase denominators14/8/8 by seed, possible denominator16;
  held48, canary12. No pooled memory/retention pass.
- `paired_lower_lr_vs.LR0` and `.HIGH`: metric-by-metric pair counts, with
  first=LOWER_LR, second=the explicitly named historical endpoint. No LR0
  internal-slot ambiguity in this reducer's output.
- `retention.held` and `.canary`: one entry per source row with LR0/HIGH/
  LOWER_LR correctness, plus explicit ID lists and counts for LR0-correct,
  LR0-correct retained, restored from a HIGH regression, still missing
  LR0-correct, and newly lost versus HIGH among LR0-correct items.
  Restored means LR0=true, HIGH=false, LOWER_LR=true; retained/restored
  are not conflated. A higher overall score cannot cancel an item loss.
- `strict_exploratory_repair_screen`: the same exact source-faithful floor
 8/7/5 AND zero missing LR0-correct held/canary items. Paraphrase improvement,
  content-only correctness or gains on formerly wrong items cannot rescue
  this screen. Partial tradeoff is not full repair.
- `costs.new`: actual new calls/updates, prompt/output token counts,
  generation seconds, fit train/wall seconds, training token exposure.
  Calls88/76/76 and updates112/64/64; same original training accounting.
- `costs.historical.HIGH` and `.LR0`: stored observed expenditure separately
  labeled reused/noncontemporaneous with zero incremental calls/updates.
  Never included in `total_new_cost`, never additional learner replications.
- `fit_diagnostics`: stored final/epoch losses and parameter diagnostics,
  not remeasured tensors. Original parent, LR-only config delta, fit seed,
  training accounting and stored source/initialized inventories must agree.

Top-level `roster` shows present/missing seeds and completion. Only a complete
three-seed roster has a boolean `all_three_strict_screens_met`; partial input
gives null. `total_new_cost` sums only newly observed costs across present
seeds (full roster240calls/240updates), never the reused controls.
Fit/generation seconds are summed observed durations, not concurrent makespan
or controller/collection wall time. Parent/raw/source/target/prompt-count
joins, duplicate IDs, wrong seeds, malformed metrics, non-stop pass flags and
bad input hashes fail closed; no repairs are made.

Every report remains `automatic_pass=false`, `scientific_pass=null`.
`native_identity_verified_by_reducer=false` and
`raw_reparsed_or_rescored=false` are explicit. This authenticates local
collected-file bytes and checks their internal joins/arithmetic, not the
original native process identity, all prompt token values, teacher-free
formation, or world outcomes independently. Those remain the frozen
collector's responsibility. Equal prompt-token counts are not proof of equal
prompt-token sequences. Stored content agreement is not reasoning correctness.
Memory targets derive from earlier child experience; held retention remains
the authored, now-inspected Level1 repair panel, not new experience or fresh
confirmation. No H1/H2, autonomy or general-learning promotion follows.

## Verification performed

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 60s python3 -B -m unittest discover \
  -s /tmp -p 'test_astra_memory_lower_lr_analysis_20260913.py' -v
```

**18 tests PASS,0.637s.** Synthetic fixtures only for new candidate results:
three-seed denominators/budgets, item restoration vs loss, canary-only failure,
exact-eligibility vs content/paraphrase, gain/loss non-offset, bool/int and
non-stop rejection, missing/duplicate/foreign IDs, source/target/raw/prompt
joins, parent/seed/LR/init mismatches, aggregate/screen disagreement, unchanged
historical imports, malformed costs/JSON, collection hashes, partial/complete
rosters, duplicate seeds/bad imported pins, exclusive output/no overwrite.

Additional compatibility check on the existing three historical collections:
**all24stored panel summaries match independent row reductions; all six
endpoint cost structures validate.** No raw outputs were regenerated or
rescored and no new lower-LR outcomes were read. CLI `--help` passes. Frozen
runner hashes remain unchanged. Native/model/network/Git/repository actions:
none. Main can bind new collections and run this reducer entirely locally.

## Authorized actual-result reduction — complete

After Main supplied the completed, once-collected lower-LR files, ran the
unchanged reducer locally. All three supplied score SHA256 values match:

```text
seed0 03288439ddb4d31db5bdc49bec0e64dd4de3fa22fa1dd8cf18315ab5707234e3
seed1 25fbfafced9e00799efeb16cd7f90d97d35837f3ae44bb90c3c8b37fc01d0ce9
seed2 511acb2c3a48d21887a2b81cd52d7f2136ca2b7459b79759a901571ebcb145ea
```

Also verified the supplied archive
`gpu_artifacts_local/memory_lower_lr_20260913_attempt1/evidence.tar`:
SHA256 `675f3598855c581da85caea154724004a9d2adb446091cca184e0f67072b0b02`,
627members. This is file integrity, not a fresh native execution audit.

New owned analysis artifacts:

- `/tmp/astra_memory_lower_lr_analysis_20260913_inputs.json`
  SHA256 `2642ab0571082579fbc02b35aad6602a6abfa6b8d2b3e8d82b7d7a308dd6da32`
- `/tmp/astra_memory_lower_lr_analysis_20260913_results.json`
  SHA256 `9fc8b149f78fafebb860be35db9adfb0b2114179e0f9a3075f776d43bba98bfd`

Exact command executed:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 60s python3 -B \
  /tmp/astra_memory_lower_lr_analysis_20260913.py \
  --manifest /tmp/astra_memory_lower_lr_analysis_20260913_inputs.json \
  --manifest-sha256 2642ab0571082579fbc02b35aad6602a6abfa6b8d2b3e8d82b7d7a308dd6da32 \
  --out /tmp/astra_memory_lower_lr_analysis_20260913_results.json
```

Exit0, `REDUCED_STORED_SCORES`, complete roster0/1/2. All independently
recomputed panel totals, paired counts and frozen screens agree with their
collected summaries. Existing result file is exclusive; a reproduction must
use a new output path. No new scorer/model/native/collector execution.

### Primary endpoints and strict screen

Exact/paraphrase columns use source-faithful `production_eligible`, not
canonical formatting or target-byte matching. HIGH/LR0 are reused historical
observations, not fresh controls.

| Seed | Endpoint | Exact | Paraphrase | Held | Canary |
|---|---|---|---|---|---|
|0|LOWER_LR|10/14|10/14|47/48|12/12|
|0|HIGH|8/14|6/14|44/48|12/12|
|0|LR0|0/14|0/14|47/48|12/12|
|1|LOWER_LR|4/8|5/8|46/48|12/12|
|1|HIGH|7/8|5/8|37/48|12/12|
|1|LR0|0/8|0/8|48/48|12/12|
|2|LOWER_LR|4/8|3/8|47/48|12/12|
|2|HIGH|5/8|5/8|17/48|12/12|
|2|LR0|0/8|0/8|48/48|12/12|

| Seed | Required exact count | LR0-correct held retained | HIGH-regressed held restored | Still missing LR0-correct held | Strict screen |
|---|---|---|---|---|---|
|0|>=8|47/47|3/3|0|MET|
|1|>=7|46/48|9/11|2|NOT MET|
|2|>=5|47/48|30/31|1|NOT MET|

All LR0-correct canaries retained for all seeds. No newly lost versus HIGH
among LR0-correct held items. Seed0's one held error was also wrong under
LR0, so47/48 is compatible with full restoration of its47LR0-correct items.
Seed1 and seed2 each fail both the exact-recall floor and itemwise restoration
requirement. Complete three-seed screen is false; partial retention recovery
is not full repair and does not authorize another dose or promotion.

Remaining LR0-correct held item IDs (full per-item tables and all restored
IDs are in the results JSON):

```text
seed1 perception:3168de3a2773da0af3a9c7a43586a1838565eb04d29b6add6ce43cab4e29cb65
seed1 perception:a3487a82a4eba508a231505ebda20e8d3b8b26a2ef4bafeea5c404f8596a32ac
seed2 perception:7a60a5144c25523d53a4b484937897020d9639c96cbad37c44601f15b36b5ca4
```

### Content/format separation remains intact

For LOWER_LR, exact source-faithful/content counts are10/4/4; exact canonical
counts8/0/0; exact target-byte counts8/4/4. Paraphrase source-faithful/content
counts10/5/3; paraphrase canonical counts2/0/0; paraphrase target-byte counts
8/5/3. The denominators are14/8/8, with possible-record denominator16 per
variant kept separately. Noncanonical but source-faithful outputs are not
silently rejected as semantic failures, and formatting alone is not recall.

### Costs and measured fit diagnostics

New work:112/64/64updates and88/76/76calls,240each total. New generation
prompt tokens55,799, output tokens5,052; summed generation time211.4060s.
Summed fit training time85.3s, fit wall time115.7s. These are observed
duration sums, not concurrent makespan/controller elapsed time.
Training exposure41,608padded/total tokens, including6,776supervised tokens
and34,832context tokens. Historical HIGH+LR0 contributed480previous calls
and480previous updates across the three seeds; incremental historical work
in this analysis/candidate experiment is zero. Per-arm observed historical
token/time costs remain separate in the JSON.

| Seed | LOWER_LR final loss | HIGH final loss | LOWER_LR tensor delta L2 | HIGH tensor delta L2 |
|---|---|---|---|---|
|0|0.044026|0.056623|1.811951|3.920665|
|1|0.131284|0.137973|1.573681|3.589591|
|2|0.028906|0.018383|1.419358|3.179680|

These are stored fit diagnostics, not independently remeasured weights or
proof that parameter displacement causes retention changes. In particular,
seed1's lower recorded final loss does not preserve the high-rate exact
recall count. No assumption that more steps or a further LR change repairs
this tradeoff follows. Historical comparisons remain noncontemporaneous;
the held panel remains inspected/exploratory, not fresh confirmation.

Final status: analysis delivered, reducer and tests unchanged, thresholds and
materials unchanged, no native work or recollection. **EDITSTOP.**
