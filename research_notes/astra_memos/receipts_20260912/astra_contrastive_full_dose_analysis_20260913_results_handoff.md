# Contrastive full-dose: independent collected-output results — EDITSTOP

Date: 2026-09-13. Local CPU-only analysis of all three completed paired runs.
No native/model/tokenizer/GPU calls, collection, fitting, Git or repository edits.
The pre-outcome reducer, tests and implementation handoff remain unchanged.

## Results

Counts below are content-correct / original-strict-correct; these coincide for
every new arm. Exact-target-byte success counts also coincide for the new arms.
Original strict scoring accepts JSON whitespace/key order, not enclosing fences;
it is not defined as canonical-byte equality. No later Level1 parser was applied.

| Seed | PLAIN D1/D2 (each /12) | CONTRASTIVE D1/D2 | Held PLAIN/CONTRASTIVE (/24) | C minus P | Paired held wins/losses/both/neither | C-record P/C (/12) | C-general P/C (/12) | Original screen |
|---|---|---|---|---|---|---|---|---|
| 0 | 9 / 8 | 11 / 8 | 17 / 19 | +2 | 2 / 0 / 17 / 5 | 6 / 11 | 12 / 12 | FAIL |
| 1 | 7 / 7 | 12 / 8 | 14 / 20 | +6 | 6 / 0 / 14 / 4 | 7 / 11 | 12 / 12 | FAIL |
| 2 | 10 / 9 | 11 / 8 | 19 / 19 | 0 | 1 / 1 / 18 / 4 | 7 / 11 | 12 / 12 | FAIL |

Every contrastive arm fails the original D2 floor (8 < 9). Seed0 additionally
misses held minimum20 and minimum advantage4; seed2 likewise misses both.
Seed1 meets held minimum20 and advantage6 but is NOT an overall screen pass.
No seed selection or promotion follows. All288 new responses finish with stop;
there are no truncated/error completions.

Historical OFF is the same48 original responses imported across the three
reports, NOT three contemporaneous OFF controls and NOT incremental calls:
D1 0/12, D2 2/12, held2/24, exposed C-record0/12, C-general11/12.
Its two held successes do not match exact target bytes. Historical held failures
are22syntax errors, C-record12syntax errors, C-general1arithmetic-value error.
Contrastive minus OFF held gains are17/18/17, with zero itemwise losses.
Neither new arm loses any OFF-correct canary item at any seed. C-record had
zero OFF-correct items, so that panel's retention condition is vacuous, not
broad no-harm evidence. Both arms recover all12 C-general items.

## Error decomposition

| Seed | Arm | Held source-error rows | Held syntax-error rows | Incorrect try / observed / predicted / relation fields |
|---|---|---|---|---|
| 0 | PLAIN | 7 | 0 | 2 / 2 / 6 / 6 |
| 0 | CONTRASTIVE | 5 | 0 | 2 / 2 / 5 / 5 |
| 1 | PLAIN | 9 | 1 | 4 / 2 / 8 / 8 |
| 1 | CONTRASTIVE | 4 | 0 | 2 / 1 / 4 / 4 |
| 2 | PLAIN | 5 | 0 | 2 / 2 / 3 / 3 |
| 2 | CONTRASTIVE | 5 | 0 | 2 / 1 / 4 / 4 |

No held schema/completion errors occur. Field errors overlap; unavailable fields
are not counted as incorrect. Remaining failures are predominantly substantive,
not format-only. Every contrastive held failure includes predicted/relation
errors: an observation, not a causal explanation. All three contrastive arms
miss the same exposed C-record item on try/observed:
`C-record/perception:2841dc758324d33d4fc569d94ebf6ed97133a6d3241c2be792c7337372e0875b`.
The JSON retains paired item IDs, raw responses and error details.

## Budget and cost

- Exactly6new fits,2016updates,8064presentations,288new calls: per arm336updates,
  112epochs,1344presentations and48calls. Historical OFF adds zero calls/updates.
- Generation:61,794prompt tokens,7,609output tokens; summed reported generation
  time322.377963s. Training:3,305,136padded tokens,3,265,920unpadded tokens,
  249,984supervised tokens and3,015,936context/masked-tail tokens.
- Each arm has41,664supervised tokens. Each epoch has372target tokens in both
  arms; PLAIN4806total/4434context versus CONTRASTIVE4914total/4542context.
  Contrastive adds12,096padded tokens per seed,36,288 across the roster.
  This is matched output supervision, NOT matched compute/context length.
- Summed fit elapsed3082.234272s. Pair controller elapsed1291.181917,
  1301.871117,1294.470845s; each is below7200s. Duration sums are neither
  concurrent makespan nor measured GPU utilization. The180s collection cap and
  six-hour lease margin are protocol constraints, not fresh live attestations.
- Recorded final losses near5.1e-6 to6.0e-6 coexist with held source errors;
  they do not establish a dose cure or mechanism.

## Interpretation and scope

The descriptive material contrast is held gains+2,+6,0 and exposed C-record
gains+5,+4,+4, but zero of three original screens pass. All panels are exposed
exploratory DEV, not fresh confirmation. D1/D2 repeat12situations across skins,
not24independent situations. Negate-earlier is a perfect fixture shortcut;
success cannot identify source-attention or improved-process mechanisms.
Treatment combines grouping and instruction, with unequal context/padded costs.
Historical OFF is noncontemporaneous; this is not a new independent dose-control
replication. No child SLEEP, parent learning, freeze, H1/H2, general G3,
clean-ancestry or working-loop promotion claim follows.

## Custody and replay

The reducer verifies complete local roots, closed stage inventories, adapter
file hashes, source/plan/completion/collection joins and raw request/response
bindings. It replays frozen `material.score_row`, independently aggregates,
and requires exact equality with saved material scores, per-item canaries and
generation costs. The original scorer, pinned historical importer and pure
encoding/manifest/native-response validators are shared dependencies, not
independently reimplemented scientific definitions. Local consistency does not
reauthenticate native hardware or recompute model/tokenizer/tensor state.

Archive:
`/data/home/rohing/dream-state/gpu_artifacts_local/contrastive_full_dose_20260913_attempt2/evidence.tar`
SHA256 `32ee167d153812943c6942a095dafc1b5e2c7ccf2634eb77be5e95c03489fa4f`.
Local extraction checked776members with no duplicate/traversal/link/special
entries;720regular root files were copied into the fresh owned
`/tmp/astra_contrastive_full_dose_analysis_20260913_inputs/`.
Main reports native/VM archive validation,6adapters and493527040bytes.
Plan/completion/scores/collection pins also agree with Main's subsequently
supplied mirror `/tmp/astra_contrastive_full_dose_native_20260913_attempt2`.
Original native paths inside plans remain unchanged.

Historical archive:
`/data/home/rohing/dream-state/gpu_artifacts_local/contrastive_perception_20260913/contrastive_perception_20260913_attempt1_archive.tar`
SHA256 `c12c3ff8e7cd0a9261aa5118d85f5a93d5318245afd05d0d4ff3cacc96401f7d`.
Frozen source: `/tmp/astra_contrastive_source_20260913_attempt1`.
All exact per-file and per-seed bindings are retained in the manifest.

Main reports the incorrect seed0 collection plan-pin transcription was rejected
before claim/output existed, then the correct authoritative collection succeeded.
This is not a scientific retry. Earlier preparation/allocation failures and
original captures remain preserved. This analysis performed no recollection.

## Frozen artifacts and command

| Artifact | SHA256 |
|---|---|
| `/tmp/astra_contrastive_full_dose_analysis_20260913.py` | `ce020de47700c97b6208dbe2afea21f182ec85820b62b5f0aa5ea4208ca030f3` |
| `/tmp/test_astra_contrastive_full_dose_analysis_20260913.py` | `d6cfbdfc68260c71bd8e7b2aa2254ddd2f6badee6242be22717dbe564d487e81` |
| `/tmp/astra_contrastive_full_dose_analysis_20260913_handoff.md` (pre-outcome) | `a8185bbdbefb4be74a1b56aa2d1874e03d523f243fe40b5663847e54ba01e2ba` |
| `/tmp/astra_contrastive_full_dose_analysis_20260913_inputs.json` | `94463a9b5563ce2e1b10025d988b1c2ac8bb40d5a2d3bc0c086edad8fc8fdb9e` |
| `/tmp/astra_contrastive_full_dose_analysis_20260913_results.json` | `204fcb1e40041e3057d1fdd9300b924d6d1a9aa94b80d2a513f07b428f500c60` |
| `/tmp/astra_contrastive_full_dose_analysis_20260913_inputs/local_copy_receipt.json` | `d4a16890e42405b43391ceb3190c380e224189f075a3e044792c424f2c14bc74` |
| `/tmp/astra_contrastive_full_dose_run_20260913_v2.py` | `ddd36b16e188a2c2bfa11e61e8fbed66fed67d93f81b1d4fa6384c04dd43c025` |
| `/tmp/astra_contrastive_perception_material_20260913.py` | `b3c7fa549fdade0866da51131f64fe067ad7cd3ce36187f67e4c56ac7fbe5c1d` |
| Canonical dataset bytes | `7f9045242e98dc05b85f814574a1eb87cacebf463af88dcca60729c4aa5ebd66` |
| `research_notes/astra_memos/ASTRA_CONTRASTIVE_FULL_DOSE_2026-09-13.md` | `e777b5be15e2a1cab447de3e72fb013bfac2a20a3d12d81574f95880ca60b0e6` |

Fixture tests:25PASS before outcome reduction (final implementation10.617s;
pre-reduction rerun11.050s). Main independently reports25PASS11.878s.
CLI help, AST and whitespace checks passed. No outcome-driven code edits.

Executed successfully, exit0, approximately1.6s:

```sh
timeout 180s python3 -B /tmp/astra_contrastive_full_dose_analysis_20260913.py \
  --manifest /tmp/astra_contrastive_full_dose_analysis_20260913_inputs.json \
  --manifest-sha256 94463a9b5563ce2e1b10025d988b1c2ac8bb40d5a2d3bc0c086edad8fc8fdb9e \
  --out /tmp/astra_contrastive_full_dose_analysis_20260913_results.json
```

Status: `REDUCED_PINNED_RAW_COLLECTED_THREE_PAIRS`. Existing output is exclusive;
do not rerun this command against the same output pathname. Main owns archiving
and any scientific decisions. This handoff is a new artifact; the pre-outcome
handoff, implementation/tests, captures, manifest and results are unchanged.
