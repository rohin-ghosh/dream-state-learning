# Q0-FULLDOSE-v2 implementation handoff — EDITSTOP

2026-09-13. Main owns native validation, immutable staging, launcher, resource selection and execution. Only the two new source/test files and this handoff were authored. No historical source/helper/test edit, Git, network, native/model/tokenizer execution or GPU launch. The implementation is an isolated faithful version of the existing executor, reusing its pinned low-level helpers without mutating another module's globals; it is not a new supervision framework.

## Final files and acceptance

| File | SHA256 |
| --- | --- |
| `gpu/astra_pairwise_q0_fulldose.py` | `f63c77f9c371433442a204d6bd7bb10e3769a3bb709ae1d728648d765ee8ceca` |
| `tests/test_astra_pairwise_q0_fulldose.py` | `ea5ea21c8b508e8621a673b61fa324c4303b3ec25160d666a7431dfb7459ea72` |

Version: **`astra-pairwise-q0-fulldose-v2`**. Native evidence kind: `Q0_FULLDOSE_V2_NATIVE_RAW`. New material campaign SHA256: **`1f29967875bb7e84fd479c25a1a54aed59405675c9bccc74305be8449d7884df`**. This seals source-only alpha-renaming and allocations, not fitted outcomes or tokenizer preparation. Prepare all three roots before any launch; compare their campaign hashes. Each native prepared hash also binds that root's actual native tokens/order/receipt.

Final CPU logs (captured tool stdout/stderr; summary retained here to avoid writing an unowned log file):

```text
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
/tmp/astra_preservation_cpu_20260912/bin/python -B -m unittest \
  tests.test_astra_pairwise_q0_fulldose -v
Ran 65 tests in 118.343s
OK

CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
/tmp/astra_preservation_cpu_20260912/bin/python -B -m unittest \
  tests.test_astra_pairwise_q0.MaterialTests \
  tests.test_astra_pairwise_q0.NumericalTests \
  tests.test_astra_pairwise_q0.AuditAndBudgetTests \
  tests.test_astra_pairwise_q0.LifecycleTests \
  tests.test_astra_pairwise_q0.ForwardCounterPlumbingTests -q
Ran 42 tests in 9.944s
OK

PASS: 18 numerical/counter/endpoint definitions AST-identical to v1
PASS: no hidden 2700 constant or setattr global monkeypatch
```

Both final suites had zero failures/errors/skips. Local Torch2.8.0+cpu emitted the existing missing-NumPy warning. Transformers/PEFT are absent locally; no dependencies were installed. This is not the complete seven-suite native-environment acceptance receipt: Main must run the built-in `cpu-tests` on the staged source/environment, where `prepare` still requires successful **zero-skips** acceptance. Earlier copied-fixture mismatches (endpoint fixture missing update count; comparing pointers between separate toy models) were corrected; final tests above passed.

Protected v1 hashes remain `1459c037cccf2f043bc02f40fb9957f38c5620a4d0bcfc8cbb4ebf30fd31182a` (executor) and `bc08064301721157fa353247559105a31b11ee3e0c3b14d5dbbbfa255b9d42e3` (tests). The new executor explicitly checks them. AST comparison confirms unchanged losses, finite gradients, FP64 dot, gradient comparison/audit classification, diagnostic neutrality, optimizer audit, objective/raw audit, canary calculation/replay, decoder counter, record validation, acquisition/locality/cell gates and curves.

## Implemented contract

- Allocations: R0=(identifier501, learner1), R1=(502,2), R2=(503,3). Config/prepared/LOAD/resource bind the allocation. Actual `configure_torch` receives the selected learner seed; both arms restart it independently. Tests check real CPU RNG agreement within allocations and differences across learner seeds. `RECIPE` is not mutated globally.
- Original source material only, with deterministic opaque-ID alpha-renaming of trained and wrong-root tools/neighbours. Original row hashes and substitution tables retained;96 new tool/neighbour identifiers are disjoint across the campaign. No old labels/adapters/fits consumed, no request/replica/seed metadata inserted in prompts. Template-role root coordinates stay1/0; logical replica is the separate allocation. Scope is **`EXCLUDED_DIAGNOSTIC_DEV_ONLY_NOT_CLEAN_NOT_PARENTING`**.
- Same rank8/alpha16/dropout0.05/LR3e-5/pairwise objective/128 quartet updates. Both finite canary misses remain raw diagnostics and do not veto either full fit. No conditional third V/unary fit, no retry, no checkpoint restart/selection. Preserved pre-fit zero-tangent/OFF-copy exclusions and all numerical/integrity/release stops.
- Ten fresh stages: audit, OFF, AUTH fit, AUTH32/64/128, DERANGED fit, DERANGED32/64/128. Both fit steps and snapshot inventory are mandatory. The full mock native controller reaches both128 endpoints with **both canaries failing**, preserves raw misses, matches decoder/token counters and exactly replays its CPU fixture capsule.
- Unchanged128 endpoint gates. New labels are `Q0_V2_FULL_DOSE_ENDPOINT_PASS/FAIL`; unchanged explicit incomplete/precheck/runtime branches remain distinct. v1 prepared/native capsules cannot be promoted. Diagnostic DEV results are not parenting, clean-lineage, H1/H2, P1/G5, generalG3, retention or mechanism-freeze evidence. Root/seed allocations are confounded and exploratory.

Full completion per root: two fits,256 updates,1,024 training-row forwards, six snapshots,1,632 evaluation prefix readouts,888 greedy generations,3,072 natural-prefix forwards; model forwards=3,072+actual generated tokens (32-token/request ceiling, at most31,488). Three roots multiply these totals by three. Missing endpoints are not zero accuracy.

Runtime/root is10,800s, two attempts,256 updates; worker timeouts derive from remaining root/lease time minus existing45s cleanup reserve. Resource fields use these constants, not old2700 literals. Before GPU work, the controller requires room for the whole10,800s plus Main's separate **180s collection reserve**, with unchanged six-hour lease cutoff. The180s is a reserved margin, not a new collection daemon/timer. The existing executor performs read-only post-terminal replay after durable finalization; Main owns external collection supervision. No throughput guarantee or actual native timing was measured here.

## Staging and model binding — important additional input

Start with Main's frozen support source, add **only the two new files**, and also stage this historical reference file at its repository-relative location if absent:

`research_notes/astra_memos/receipts_20260912/astra_qwen_public_binding_receipt_20260913_attempt1.json`

SHA256 `e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019`. It is a **CPU fixture reference for the immutable official14-file identities**, not accepted as another machine's native receipt. The new `native_source_pins()` includes20 files, including both v1 files, both v2 files, the original material archive, unchanged helpers/contracts/tests and this reference. Preserve all historical regression-support files alongside them.

Use the explicit historical support manifest `/tmp/astra_q0_counter_test_support_20260913_attempt1.json`, SHA256 `3e587a113051c7ba5bf143c853b343b391b87a0ee51aa903bde61c91e1d22517`, with its actual archived files. The built-in receipt validates the support before and after all seven suites and binds its inventory/hash; nothing is silently skipped. The current live workspace's documentation may differ from those historical pins: use Main's frozen staged support, not changes to old files here.

Per-node public binding:

1. Retain the original receipt schema's official `repository`, `revision`, `metadata_sha256`, `status`, `file_count=14`, exact `files` entries (sha256/size/public_match), `checked_utc`, and false `clean_lineage_certified`/`historical_receipts_changed`.
2. Main's **new local receipt** must additionally contain `node`=SHA256(hostname UTF-8), `environment` equal to config's existing environment identity, `model` and `tokenizer` equal to the actual resolved absolute snapshot paths. Do not merely reuse node3's receipt or timestamp as new-node verification. Main reports node2's14 payloads have already been rehashed; this implementation did not perform that native readiness work.
3. Set config `public_binding_path` to its absolute path and `public_binding_sha256` to the exact bytes hash. The module validates that pin and the immutable official file-map digest, checks current node/environment/paths, and rehashes both local inventories using existing helpers. Wrong node, wrong environment/path, altered official identities/bytes, relative paths, inherited old receipt and clean-origin claims have CPU negative tests.
4. Null binding can produce only an unready preparation; execute refuses it. No HTTP/download or receipt-authoring tool was added. Existing hardware helper still requires the registered A40/driver identity; this is not a hardware-portability expansion.

## Main command interfaces (not run natively here)

Run from the immutable source root with that root on `PYTHONPATH`; use the native environment interpreter as `python`. Keep offline flags and `PYTHONDONTWRITEBYTECODE=1`. The execute CLI and manifest/config/PREPARED shape match Main's launcher.

```bash
python -B -m gpu.astra_pairwise_q0_fulldose config-template --replica R0
python -B -m gpu.astra_pairwise_q0_fulldose material --replica R0
# Repeat config generation for R1/R2; Main fills node/path/environment/lease/intake fields.

CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python -B -m gpu.astra_pairwise_q0_fulldose cpu-tests \
  --out /ABS/NEW_CPU_RECEIPT.json --test-support /ABS/HISTORICAL_TEST_SUPPORT.json

CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python -B -m gpu.astra_pairwise_q0_fulldose prepare \
  --out /ABS/FRESH_R0_ROOT --config /ABS/R0_CONFIG.json --test-receipt /ABS/NEW_CPU_RECEIPT.json
# Prepare R1/R2 separately; allocation is taken from each config, not the output-directory name.

# Main's owned launcher supplies reserved CUDA UUID, CUBLAS_WORKSPACE_CONFIG=:4096:8 and supervision:
python -B -m gpu.astra_pairwise_q0_fulldose execute --out /ABS/FRESH_R0_ROOT --allow-gpu

CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python -B -m gpu.astra_pairwise_q0_fulldose replay --out /ABS/CLOSED_R0_ROOT
```

Optional `--expected-version astra-pairwise-q0-fulldose-v2` rejects mismatches before command dispatch. `worker` remains internal and requires registered live controller parent, ticket/prior receipts and `--allow-gpu`; do not invoke it independently. No new launcher was created or Main's launcher edited.

Source seams: allocation/renaming at181–219; preparation352; fit915; release1209; endpoint1337; native config1508; preparation1619; verification1664; actual seed binding1780; worker1787; controller1904; native reduction2064; replay2146; CLI2190. These are source navigation hints, not a scientific claim.

**Ready for Main's staged native-environment CPU acceptance and review, not a launch authorization or success guarantee. EDITSTOP.**
