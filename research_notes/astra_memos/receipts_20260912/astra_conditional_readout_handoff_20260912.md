# Conditional root0 readout — EDIT-STOP, 2026-09-12

**CPU implementation complete with Main's accepted dual-map likelihood amendment. Generation API remains unchanged. No native readout/model/GPU call was performed.**

## Exact owned files

- `organism_v6/conditional_behavior_readout.py` — SHA256 `b4cd06137e3743186b885a809e1f2d3316fffd420a75c8c24838d6df72fa80df`
- `tests/test_conditional_behavior_readout.py` — SHA256 `ba6b6951113cf36f0cde154041bd983fd4ded34762a71b037faa62a0e30c332d`
- This `/tmp` handoff only. No existing source, material, fit files, repository logs, Git, network, GPU or model operations. Main's live fit source is untouched.

## Accepted dual-map likelihood amendment

The immutable prepared AUTH/DERANGED strings **do not swap across PROSPECT belief twins**. Example from the actual attempt2 candidate construction, goal=fep:

| Belief | AUTH | DERANGED |
|---|---|---|
| dax→fep, wug→nup | PREDICT dax→fep; ACT dax | PREDICT wug→nup; ACT wug |
| dax→nup, wug→fep | PREDICT wug→fep; ACT wug | PREDICT dax→nup; ACT dax |

The selected action exchanges, but comparing the two prepared full maps also exchanges the predicted outcome. My earlier proposal incorrectly assumed their entire strings swapped. Tests exposed this; it is not hidden or treated as equivalent.

Main's accepted amendment replaces the earlier AUTH-only proposal: PROSPECT scores **two real fixed-endpoint pairs**, `AUTH(x0), AUTH(x1)` and `DERANGED(x0), DERANGED(x1)`, at BOTH inputs and in ALL states including OFF. Four distinct complete strings/case are retained as `AUTH_X0`, `AUTH_X1`, `DERANGED_X0`, `DERANGED_X1`, with their actual source map and endpoint ID. REVISE scores only its two genuine swapped strings; both map orientations are derived by matching each map's actual endpoint targets to those strings, not by attaching an assumed negative sign.

Score plans and requests name assay version **`conditional-dual-map-fixed-endpoints-v2-20260912`**. Select the accepted assay when preparing score plans with:

`--prospect-contrast dual-map-belief-endpoints-v2`

There is **no obsolete-assay fallback**. Omission or the old `auth-belief-endpoints` option rejects score preparation. The API has the same named choice. AUTH-oriented and DERANGED-oriented pair values/means are reported separately for every state/OFF under `operations[operation].map_oriented` and per-pair `oriented_nats`. Neither PROSPECT likelihood is substituted for the other or converted by a static sign. Both can be positive; a regression test requires that independent result. DERANGED-own/opposite strict generation tests remain unchanged. Prepared corpora, recipe and `teacher_forcing_interface.json` are immutable and untouched; new likelihood requests live only in the new versioned readout plan. No outstanding approval question remains for this amendment.

## Implemented interface

All functions are in `organism_v6/conditional_behavior_readout.py`:

- `controls()` (line56): exact16 source addition rows `eval-addition-000..015`, and all16 existing `native_action_copy` executions from `semantic_carrier_diagnostic.build_items()`. Full source records are retained. Copy has **16 executions /8 unique prompts**, never16 independent tasks. Copy scoring is literal interface preservation, not compiler execution.
- `read_material()` (line73): immutable attempt2 three-file pins, inventory, native source/recipe/corpora/teacher-interface bindings, source hashes and11248/1888 per-epoch token totals.
- `fit_contract()` (line123): saved fresh adapter, no warmstart, exact recipe,128 rows/steps/microbatches,4 epochs, zero skipped/nonfinite/truncated/split rows, correct arm corpus SHA and44992 processed tokens; actual rank8 saved configuration and one safetensors adapter.
- `prepare()` (line243): CPU tokenizer-only preparation, no fit or GPU allocation. Stores a frozen state/phase plan, requests, native encodings, control bytes, source/model/adapter pins and named likelihood assay. `verify()` repeats these checks before use.
- `run()` (line431): explicit `allow_gpu=True` only after Main allocation. Launches a fresh process with the existing `rulegame_parenting_diagnostic.supervise`; no new guard framework.
- `reduce()` (line567): replay all complete raw pairs, token/text/likelihood/mask bindings, usage and existing supervision/release receipts. Returns `INCOMPLETE` without manufactured zeros if evidence is missing, invalid or source/native pins changed. It returns JSON data, not an automatic continuation decision.
- `summarize()` (line587): requires all six unique state/phase reductions, same material/base/source/likelihood assay, same serialized state adapter for generation and likelihood, and shared OFF. Reports comparisons, literal thresholds, native costs and reserved seconds; **never a full L1/Q0/H1 verdict**.

Generic reuse is direct: `fundamental_teaching_readout.capture` (not any fixed48-case prepare/worker/reduce wrapper), `semantic_carrier_diagnostic.score` (not its fixed compiler-action preparation), and existing supervisor/backend cleanup. HF scoring loads the pinned base and saved adapter, one adapter only, `is_trainable=False`, all gradients disabled, eval/inference mode. No optimizer or fitting code was added.

## Runnable Main commands

Use the newly integrated readout source installation, with unchanged corpus/trainer bytes. The interpreter can be Main's native `/localhome/local-rohing/v2/venv/bin/python`. `--model-pins` expects a **plain filename→SHA256 JSON object**, such as the `model_files` member of Main's existing fit plan, not the whole plan.

```bash
PY=/localhome/local-rohing/v2/venv/bin/python
MATERIAL="$HOME/astra_diagnostics/astra_conditional_behavior_20260912_attempt2/material"
FIT_ROOT="$HOME/astra_diagnostics/astra_conditional_behavior_20260912_attempt2/fits_root0_attempt1"
READOUTS="$HOME/astra_diagnostics/astra_conditional_behavior_20260912_attempt2/readouts_root0_attempt1"
MODEL="$HOME/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28"
# Main supplies PINS (plain model-files JSON), DEVICE and actual Unix LEASE_END.

# Dry CPU preparation can happen before fit outputs exist; OFF has no adapter.
"$PY" -B -m organism_v6.conditional_behavior_readout prepare \
  --material "$MATERIAL" --out "$READOUTS/OFF_generate" \
  --model "$MODEL" --model-pins "$PINS" --state OFF --phase generate \
  --device "$DEVICE" --lease-end "$LEASE_END"

# After the relevant fit completes and Main verifies release:
"$PY" -B -m organism_v6.conditional_behavior_readout prepare \
  --material "$MATERIAL" --out "$READOUTS/AUTH_generate" \
  --model "$MODEL" --model-pins "$PINS" --state AUTH --phase generate \
  --adapter "$FIT_ROOT/run/AUTH/adapter" --device "$DEVICE" --lease-end "$LEASE_END"

# Main's accepted dual-map fixed-endpoint likelihood amendment:
"$PY" -B -m organism_v6.conditional_behavior_readout prepare \
  --material "$MATERIAL" --out "$READOUTS/AUTH_score" \
  --model "$MODEL" --model-pins "$PINS" --state AUTH --phase score \
  --adapter "$FIT_ROOT/run/AUTH/adapter" --device "$DEVICE" --lease-end "$LEASE_END" \
  --prospect-contrast dual-map-belief-endpoints-v2

# An explicit, separately allocated worker; no automatic chaining follows.
"$PY" -B -m organism_v6.conditional_behavior_readout run \
  --root "$READOUTS/AUTH_generate" --allow-gpu
"$PY" -B -m organism_v6.conditional_behavior_readout reduce \
  --root "$READOUTS/AUTH_generate"
```

Prepare/run analogous DERANGED generation/score roots with `run/DERANGED/adapter`; OFF_score omits `--adapter`. Each root is exclusive/fresh; do not rerun or overwrite a failed root. Main, not this module, waits for live fit completion and confirms device availability. Fit wrapper `fit-result.json` /terminal/full-release decisions remain Main's responsibility; this module validates the saved adapter's trainer artifacts and its own readout supervision.

After all phases:

```bash
"$PY" -B -m organism_v6.conditional_behavior_readout summarize --roots \
  "$READOUTS/OFF_generate" "$READOUTS/OFF_score" \
  "$READOUTS/AUTH_generate" "$READOUTS/AUTH_score" \
  "$READOUTS/DERANGED_generate" "$READOUTS/DERANGED_score"
```

Commands emit JSON to stdout; Main may save it outside `run/data` (the capture manifest covers that directory). Inspect the `complete`/`status` fields; a reduction returning `INCOMPLETE` is not usable evidence or an authorization.

## Counts, interpretations and costs

- Per state:128 train+64 dev+32 controls =224 generation calls; temperature0, seed20260912, cap64. Three states =672 actual generations. One contemporary OFF panel is used for both comparisons, never double-counted.
- Per state:32 PROSPECT×4 candidates +32 REVISE×2 =192 candidate forwards across64 dev likelihood requests. Three states =192 scoring requests/**576 forwards**, +192 versus the earlier assay. Each PROSPECT request reuses the generic two-candidate kernel twice; REVISE once. Thus96 kernel invocations/state, with no duplicate REVISE forwards for its second map orientation. OFF receives exactly the same candidate bytes and prefixes as trained states. Input-only chat prefix plus complete continuation+real EOS; never gold prior output fields. Candidate sums are not length-normalized. Exact per-token logprobs/IDs/masks remain in raw receipts.
- Registered interaction **for each real map separately**: fix that map's endpoint0-correct candidate A and endpoint1-correct candidate B, then `[logP(A|x0)-logP(B|x0)] - [logP(A|x1)-logP(B|x1)]`. Report all16 pairs and arithmetic mean per operation/map in EVERY state including OFF. Positive DERANGED-own interaction uses its own real targets. REVISE's two orientations are opposite because its verified target strings genuinely swap, not because of a static state-dependent sign rule.
- Scorer reports both full maps on generation, strict syntax vs components/joint semantics, all goal/belief/outcome/prior-action twin families and strata, invalid calls retained, addition/copy exactness and spill. Eight unique copy prompts require both registered executions correct for the unique-all-correct endpoint.
- Training costs expected per arm44992 total input/7552 supervised target; two fits89984/15104. These include EOS and are **not** a readout estimate. Generation costs use actual returned prompt/output IDs separately from14336 output-token ceiling/state. Likelihood costs separately count unpadded input, padded forward tokens, scored target tokens and forwards; scored tokens are not generated output tokens. Timings distinguish call time from supervised window including cleanup. No billing/throughput estimate was invented.

## Resource limits, gaps and claims

Main's root0 cap is recorded as5400 A40-seconds including fits+readouts+cleanup:1200s fit pair, six nominal600s workers,600s margin. **Main enforces the aggregate**, since fits are owned by the other orchestrator. Existing worker600/load180/call120 and supervisor cleanup behavior remain unchanged. There is no automatic split, retry, cap extension, partial denominator or next launch. A224-call generation state or amended192-forward HF state that times out stays INCOMPLETE, and raw partial receipts are preserved. The extra forwards do not increase the600s HF worker allowance or90 A40-minute total cap. Existing cleanup grace is not a new grant beyond Main's total cap.

No native HF/vLLM readout profile has been observed here. Native tokenizer preparation/HF eager shared-prefix tolerance/actual engine loading still require Main's successful phases; mocks are not calibration. No full-logit backend parity is claimed. Preparation may report a concrete failure rather than changing the frozen protocol.

This is one root0 authored diagnostic, not independent root replication, child's own experience, confirmation, general learning, a Q0 gate, or H1. Completion of these readouts is not full L1: composition is absent and all-root requirements remain outside scope. Main has prospectively accepted the named dual-map amendment; no empirical outcome or new scientific claim was inferred from it.

## CPU validation

**191 tests passed +48 subtests passed, no skips (24.77s).** Includes52 readout tests, all41 conditional corpus tests and neighboring fundamental corpus/readout regressions. Tests mock tokenizer/backend/scorer/HF loader and explicitly test all four literal PROSPECT target strings, both real map endpoint orientations, independently positive AUTH/DERANGED PROSPECT contrasts in every state/OFF, genuine REVISE swaps, identical candidate bytes across states, generic kernel reuse once/twice, exact576-forward and per-pair padding accounting, missing DERANGED score rejection and assay-version drift. Generation own/opposite strict checks, controls, pin/fit checks and supervisor bounds remain covered. Fixture “native” receipts are synthetic test inputs, not native evidence.

```bash
PYTHONPATH="/data/home/rohing/dream-state:/home/rohing/.cache/uv/archive-v0/x1HSjiSiIHWXFVFO:/home/rohing/.cache/uv/archive-v0/otX-mnihYO-Z_5I0:/home/rohing/.cache/uv/archive-v0/40CHA3uYuGrxepLQ:/home/rohing/.cache/uv/archive-v0/WhvpL9vEtag5Xx96:/home/rohing/.cache/uv/archive-v0/_og-n3yIa91AcMqC" \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
python3 -m pytest -q -p no:cacheprovider \
tests/test_conditional_behavior_readout.py tests/test_conditional_behavior_corpus.py \
tests/test_fundamental_teaching_readout.py tests/test_fundamental_teaching_corpus.py \
tests/test_fundamental_two_habit_corpus.py
```

**EDIT-STOP. Exact owned bytes are frozen for Main's review/integration.**
