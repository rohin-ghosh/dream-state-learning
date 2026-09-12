# EDITSTOP — trained-record acquisition check, September 12, 2026

Implemented only the owned acquisition sidecar, its tests and this note. **22 CPU-only tests PASS in25.454 seconds.** No SSH/network/Git, GPU query, native tokenizer/model execution, scoring outcome inspection, fit, source/material/readout edit, or dose change. Main alone prepares and launches natively. The adopted null-branch design and both subsequent interpretation clarifications are preserved prospectively.

## Exact tested hashes

| File | SHA256 |
|---|---|
| `/tmp/astra_rulegame_record_acquisition_20260912.py` | `ae3bbad045a7ec205ed2d711e03fcdcd08aa3b2bde8b529decda597d6e9888ea` |
| `/tmp/test_astra_rulegame_record_acquisition_20260912.py` | `20ebc85d127ab9c449e3746c746a7e2c83f8bf508b6453f45c8da92e34507426` |
| Frozen readout helper, unchanged | `120e260a76395586736d47e4f8a55c425b090f9f8654208dcfbef7eac5cccbde` |
| Main's frozen write-v2 driver, unchanged | `183b48be6193da953f699d718575f9227fd946d9f8111d2d1647ae5dd431ec7c` |
| `organism_v6/semantic_carrier_diagnostic.py`, unchanged | `a05da09e8f2720907eb277f928e84ec095a754119144a6b2ecbd38360a969f98` |
| `organism_v6/conditional_behavior_readout.py`, unchanged | `b4cd06137e3743186b885a809e1f2d3316fffd420a75c8c24838d6df72fa80df` |
| `organism_v6/rulegame_record_material.py`, unchanged | `7eb7bbd04068a34be4932f11a0eab0109ddabcceb03210a07b657d57a0c621c1` |

Source label supplied by Main: `610c6edd05ce9c85720ee6e992889badecc2c158`; no Git verification performed. The native plan pins actual source/dependency bytes in addition to the inherited write pins. Only write-attempt2 plan `48effd1ba154f497e5946d308f990624ada63bd905c198e0abfdf668131a8ee4` is accepted. No readout outcomes are used to choose records or requests.

## Frozen requests and raw-byte contract

Three cells **OFF → P → A**, each a fresh supervised HF scoring process. OFF loads the pinned frozen base; P/A load their verified saved12-update adapters, inference-only. All cells score all four originally selected records in fixed P0, P1, A0, A1 order, each under:
1. **FULL**: exact actual rendered training-record context.
2. **MAPPING_SENTENCE_REMOVED**: exactly that context with one occurrence of `"\n" + diagnostic.RELATION_DEFINITION` deleted. The raw user prompt receives the same one deletion; native re-rendering must equal the byte-edited actual context. No other string surgery, shortened history, extra instruction, length-matched control or regenerated context.

Each request has two complete continuations in order: original **raw record+EOS** and an evaluation-only foil changing only the unique literal JSON `relation` value, matched↔mismatched. Preserve whitespace and every other character/UTF-8 byte. Exact schema, duplicate-key rejection, nonnull Boolean predicted/observed values, truth relation and one unescaped literal span are required. No reserialization of the raw target, appended newline or foil training. Any record/context/offset failure rejects the whole preparation before creating output; never substitute a later record.

This is **8 requests/cell,24 total; two candidate forwards/request,48 total; zero generations**. It adds no task, gym, curriculum, dose, adapter update or outcome-based filter. All cross-arm targets remain visible. Each per-candidate output includes full-target **sum logprob, mean logprob, scored-token count and complete token-logprob vector**, including EOS. Truth–foil margin uses full-target sums, not length-normalized margins. Per-cell costs include requests, candidate forwards, scored target tokens, native input tokens, padded-forward tokens and call seconds.

## Native mechanism and audits

`NativeScorer` at line277 reuses **`conditional_behavior_readout.HFScorer` for local HF/PEFT loading and cleanup**, but calls **`semantic_carrier_diagnostic.score` directly**. It never invokes conditional scoring_groups, conditional operations/assay versions, compiler candidate selection, conditional CLI or generation. New namespace: `rulegame-trained-record-acquisition-v1`; old conditional request versions fail.

The minimal generic JSON encoder at line110 adapts the carrier's offset/prefix/mask checks, not its compiler-only whitelist/24-token cap. It requires exact native complete-text and raw-target roundtrips, contiguous character/UTF-8 offset coverage, no context/target token join or boundary straddle, no truncation, max4096 tokens including EOS, exactly one terminal target EOS, complete target labels and shifted predictor indices. It records relation spans, relation-overlapping token positions and zero-width terminal-EOS offsets. FULL truth input IDs/labels must **equal the actual V3 training receipt**, and ablation may not change truth target tokenization. Native prepare can fail on unsupported offset behavior or a token join; no fallback normalization is implemented.

The request's common input-only prefix contains **only actual rendered context tokens**, never an added gold relation or a shared beginning of the target. The full raw JSON remains scored. Within ordinary autoregressive scoring, earlier correct target fields are nevertheless given conditional prefixes for later relation tokens: this is **not cognition, causal discovery or pre-TRY information selection**.

The existing carrier scorer executes two forward passes with equal future-only padding/positions, no cache, and its shared-prefix likelihood consistency checks. A forward pre-hook records/verifies actual native input IDs, attention masks, position IDs and use_cache=False for both passes. Store byte-hashed request/response receipts, full input/label/offset arrays and raw selected logprobs. All parameters must be frozen, model eval/no-cache and adapter count0/1; runtime count/dtypes are logged. Load recipe remains local-only HF bf16/eager and PEFT is_trainable=False. This is a teacher-forced HF score identity, **not vLLM logit parity or model-origin authentication**.

## Prospective interpretation — distinct criteria

Reported separately for each context condition:
- **Each adapter's own-record acquisition versus OFF:** for P, both P-owned records individually improve summed truth logprob **and** truth–foil margin versus OFF; analogously A on its own two records. This is the adopted narrow trained-record criterion, not a universal necessary condition for learning.
- **Stronger P-specific selective carriage:** both P-owned records individually improve summed truth logprob **and** margin versus **both OFF and A**. This remains reported, but is **not required for parameter acquisition**.
- Every P−OFF, A−OFF and P−A delta for every record/context remains visible, including mean logprob deltas. No averaging away a failed own-record condition, dropping an A/cross-arm record or selecting a favorable context.
- If P/A both meet own-record criteria and both improve on the P records without the stronger P-specific result, the report explicitly permits **shared/nonselective acquisition**; equal P/A gains are not labeled “no acquisition.” Context-pattern fields show both, FULL_only, MAPPING_SENTENCE_REMOVED_only or neither_demonstrated for the own-record criterion.

MAPPING_SENTENCE_REMOVED is **not scaffold-free**: all other record-schema instructions and public action/outcome remain. Any FULL/removed difference indicates sensitivity to this ablation; prompt shortening and position changes are not isolated, so no unique semantic mechanism is identified. No length-matched control is added. Failure to meet a criterion is acquisition **not demonstrated by that criterion at this fixed dose**, not a claim of inability to learn. This is on trained records, not heldout learning, general parenting, P1, autonomous adult updates, H1/H2 or longitudinal G5. No new gate, tuning or automatic escalation.

## Custody, isolation and bounds

`prepare` at line198 replays original formation, reruns `build_record_pair` with the actual local tokenizer, compares exact corpora/source receipts/training IDs against unchanged accepted material, and binds `accepted_writes` saved-adapter identity. Main's original audit and fixed first-two selection are inherited unchanged. The scorer workers receive the eight exact evaluation requests plus model/adapter/source pins, not parent lesson/restatement/Main-audit prose or prior-cell outcomes. Process isolation reuses the frozen owning-process/PID/PGID/session checks and parent-death/deadline watcher. It is not OS filesystem sandboxing or an automatic semantic nonleakage certificate.

Run rechecks original fit/material/base/adapter/source pins before cells and at completion. Workers independently check native rendered context, offset/token/mask/EOS preparation and immutable model/adapter inventories before and after scoring. Raw replay verifies every request, response, timestamp, native forward/mask receipt and score vector; complete prior captures are rechecked before reduction.

Use the existing diagnostic supervisor: **controller1800s inclusive, worker≤600s,140s nested cleanup reserve**, existing load180s/call120s guards and10s supervisor lease guard. Three full600s worker windows plus extra cleanup are not promised. Hard end is min(start+1800, supplied deadline, supplied real lease expiry−6hours). Native preparation is a separate CPU phase and must leave a full1800s at its end. These clocks are nested/nonadditive; the real lease expiry is Main-supplied, not provider-verified. Fresh sibling output and exclusive run directory prevent retries/overwrites. Any failure preserves prior/partial captures, stops later cells and writes aggregate=null; no partial scientific conclusion or automatic rerun. Main separately performs full resource-release collection/reconciliation.

## Tests / Main-only commands

Tests cover raw whitespace and both foil directions; absent/repeated mapping, null/duplicate/escaped/wrong relation rejection; whole-pair atomicity; FULL V3 token equality; offsets/joins/EOS/overflow; custody tamper; exact24/48/0 mock workload; all cross-arm rows; own-record versus stronger/shared acquisition; FULL/removed patterns; no old protocol routing; worker offsets/spec; partial failure/no retry; cleanup. They execute the **actual carrier.score Python mechanism with mocked tensor/model interfaces**, verifying two forwarded sequences and every shifted scored token/EOS. No actual torch package/model/tokenizer or native/GPU operation is needed for these tests.

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES='' \
python3 -B -m unittest discover -s /tmp -p test_astra_rulegame_record_acquisition_20260912.py -v
```

Main: keep frozen helper/readout/write-v2 paths and source/model paths unchanged. Set the actual timezone-aware deadline and lease expiry. Use the native venv interpreter's **absolute spelling, not its resolved system-Python symlink target**:

```bash
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
WRITE_ROOT="$HOME/astra_diagnostics/astra_rulegame_interaction_v3_record_write_20260912_attempt2"
ACQUISITION_ROOT="$HOME/astra_diagnostics/astra_rulegame_record_acquisition_20260912_attempt1"
"${NATIVE_PYTHON:?exact write-plan venv interpreter}" -B \
  /tmp/astra_rulegame_record_acquisition_20260912.py prepare \
  --write-root "$WRITE_ROOT" \
  --write-plan-sha256 48effd1ba154f497e5946d308f990624ada63bd905c198e0abfdf668131a8ee4 \
  --write-driver /tmp/astra_rulegame_record_write_v2_20260912.py \
  --out "$ACQUISITION_ROOT" --deadline "${DEADLINE_UTC:?set deadline}" \
  --lease-end "${LEASE_END_UTC:?set real lease expiry}"

"${NATIVE_PYTHON:?exact write-plan venv interpreter}" -B \
  /tmp/astra_rulegame_record_acquisition_20260912.py run \
  --root "$ACQUISITION_ROOT" --plan-sha256 "${ACQUISITION_PLAN_SHA256:?exact prepare return}" --allow-gpu
```

**Pending decisive native checks:** original four-record byte/non-null/offset preparation and immutable plan pin; three fresh correct HF base/adapter loads; native forward/mask/logprob receipts for all24 requests/48 forwards; complete reductions under both contexts; owned and full resource release. None was executed or observed here. Do not interpret mock completion as native feasibility or acquisition. EDITSTOP.
