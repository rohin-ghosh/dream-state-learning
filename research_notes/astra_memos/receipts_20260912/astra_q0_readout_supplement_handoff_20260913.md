# R1 final-readout supplement — implementation EDITSTOP

Date: 2026-09-13. Implements accepted design `bdbd7af0652526f2abfcfab90b9957624189e7f7e35da65fad1d04ed0f7d3ade`. Main owns admission approval, native tests, immutable staging, launch and collection. Only the two new files and this handoff were authored; no old executor/helper/test/root edits, Git, network, GPU/native/model/tokenizer execution or launch. CPU tests use fixture tokenization and a small frozen CPU model, not native Qwen inference. I authored the full-dose executor and this supplement; this is not an independent scientific review.

## Frozen files

- `gpu/astra_q0_readout_supplement.py`: SHA256 `6c0e40d242f6903fab53b303112c4f2e25afde62c696be02ee80a5c8ebd4ad08`.
- `tests/test_astra_q0_readout_supplement.py`: SHA256 `109d9fb67004b4b8bdabe319acf4b7c54d625f36a31c1947e8a430fe2738dccc`.
- Version: **`astra-q0-final-readout-supplement-v1`**.
- Runtime hard-pins original v2 executor `f63c77f9c371433442a204d6bd7bb10e3769a3bb709ae1d728648d765ee8ceca`; unchanged v2 test SHA `ea5ea21c8b508e8621a673b61fa324c4303b3ec25160d666a7431dfb7459ea72` also confirmed locally.
- Unchanged gateway/supervisor/interface hashes: `b9fd33c7c11b2f57395f08d609bb1df004d9663eeefd143060bb1a24a34f10c8`, `dd4f0a72cddc8226fa48ce50ab0faa6dd4e75f9db510aa89cfb5224898ee7496`, `9ab582ebc935ae36b88bd412fd06d799044661612f89a0770e46b92ab1b066c7`.

## Acceptance log

```bash
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/tmp/astra_preservation_cpu_20260912/bin/python -B -m unittest \
  tests.test_astra_q0_readout_supplement -q
```

```text
Ran 21 tests in 41.816s
OK
PASS: no original worker/reducer/replay, fitting, backward, or optimizer-step calls
PASS: one-query helper declares timeout=30
```

Zero failures/errors/skips in the final suite. Existing missing-NumPy warning from Torch2.8.0+cpu persists; no packages installed. Initial fixtures needed native-style binary tensor-store representations to exercise read-only canary receipt verification; corrected only the new fixture code. CLI `--help` also checked. This is CPU implementation acceptance, not a native receipt or throughput guarantee. No actual R1/Noether admission artifact was consumed during implementation.

## Admission interface — does not assume Noether JSON field names

Main supplies a JSON-object custody receipt and its exact SHA256, plus **external hashes of the original `SEAL.json` and `FINALIZED.json`**. Those separate witness pins bind actual original bytes without interpreting an evolving custody-receipt schema. Receipt contents are retained as opaque Main-approved provenance, not automatically adjudicated approval. Main must approve the receipt's meaning; the module independently validates the sealed artifact chain.

Admission checks the full closed original inventory, finalization, R1=(identifier502, learner2), original abort label, nine successful stages, ordered job/load/receipt/event/counter/release joins, both128 fit receipts using existing read-only canary validation, and the failed final job's exact DERANGED128 adapter binding. Stage09 must have no LOAD/DONE/readout artifacts, a15s identity-query timeout trace, and verified failed-worker cleanup. The saved adapter tree is hashed and later its actual loaded LoRA tensor digest checked. Unknown/changed failure chronology fails closed; Main should report a concrete fixture/interface mismatch rather than bypass it.

**Requires the complete closed original root including its tensor store and saved adapter**, not metadata-only extraction. No old worker, fit, optimizer, original reducer or original replay is invoked. Canary replay here reads saved numbers on CPU; it does not rerun a fit. Critical admission repeats after capture and on supplementary replay; original bytes must remain unchanged.

Prepare a new config by copying the original R1 config. Permitted differences are GPU UUID, current lease end/cutoff, builder preflight reference and approved intake reference. Node, driver, original public receipt, resolved model/tokenizer paths, environment, learner allocation and other fields must remain identical. Same-node recovery is the deliberately bounded interface; machine migration needs a separately authorized extension. Existing v2 config validation and local public file binding remain enforced.

## Commands for Main (not executed natively here)

Stage an immutable copy of the original source/support with both new files. `source_pins()` includes v2's20 source inputs plus the new module/test. Keep the historical fixture/public-reference files already required by v2. Run from that source root with matching `PYTHONPATH`, native dependencies installed, and offline flags. No separate launcher was created.

```bash
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python -B -m gpu.astra_q0_readout_supplement prepare \
  --out /ABS/NEW_SUPPLEMENT_ROOT --original-root /ABS/CLOSED_R1_ROOT \
  --custody /ABS/MAIN_APPROVED_CUSTODY.json --custody-sha256 EXACT_CUSTODY_SHA256 \
  --original-seal-sha256 EXACT_ORIGINAL_SEAL_SHA256 \
  --original-finalized-sha256 EXACT_ORIGINAL_FINALIZED_SHA256 \
  --config /ABS/RECOVERY_CONFIG.json
# Optional, prospective flag: --joined-diagnostic (default is capture only).

# Main's owned launcher supplies reserved CUDA UUID, :4096:8 CUBLAS config, offline flags,
# external stdout, exact source/manifest pins and its refreshed allocation check:
python -B -m gpu.astra_q0_readout_supplement execute \
  --out /ABS/NEW_SUPPLEMENT_ROOT --allow-gpu

CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python -B -m gpu.astra_q0_readout_supplement replay --out /ABS/CLOSED_SUPPLEMENT_ROOT
```

`worker --out ROOT --allow-gpu` is internal only; it requires the newly registered live controller parent and job/start/manifest hashes. `manifest.json` and `PREPARED.json` are new-root-only artifacts; this module does not copy the old launcher ABI beyond the `execute --out ... --allow-gpu` entry. Main should pin the new manifest before execution. Never invoke the old v2 worker on the sealed root.

## Execution, outputs and limits

- One fresh frozen base+saved DERANGED128 load, seed2, existing `q0.evaluate` and `q0.native_generate`, unchanged greedy32-token/EOS behavior and original request IDs/order. Exactly584 raw records:288 prefix readouts and296 generations; zero updates/training forwards. Actual decoder counter must equal288 natural forwards and288+actual generated tokens, at most9,760 model forwards. No optimizer or snapshot writing.
- New-module identity query is one exact UUID/name/driver call with **30s timeout**, unchanged node/A40/driver checks and no retry. Old15s `gpu_identity` is never called on this path. The separate inherited idle query remains15s and may still fail closed; supervisor release query already uses30s.
- Controller cap3,600s; worker receives remaining time minus45s cleanup; reserve180s separately for Main's collection/replay and retain the six-hour lease cutoff. Actual process identity/exit/group/GPU release gates completion. A second failure produces a sealed supplemental abort, never a retry.
- Raw events, LOAD/DONE, process/cleanup/resource receipts, REPORT, seal and finalization live only in the new root. `REPORT.json` is a candidate until sealed/finalized. Durable or post-fsync publication overrun yields effective `SUPPLEMENT_ABORT`; late-publication witness is replayed. CLI execute returns the effective report; replay reconstructs it without writing. The180s external collection limit is Main's supervision responsibility, not a new daemon.
- Output always retains original `NONREPORTABLE_RUNTIME_ABORT`, `original_primary_changed=false`, `primary_three_root_complete=false`, and `scientific_claim=false`. Complete readout status is distinct from any endpoint pass/fail. No silent promotion of the original primary experiment.
- Optional joined scoring uses only original R1 OFF and AUTH128 plus the new DERANGED128 capture, checks unchanged endpoint/locality/copy/complementarity gates, and labels the result `POST_ABORT_JOINED_DIAGNOSTIC_ENDPOINT_NOT_ORIGINAL_PRIMARY`, with per-cell artifact hashes. No other root, new control, new fit or parent context can substitute.

**EDITSTOP. Ready for Main's actual custody admission, staged native-environment CPU tests and integration—not a launch or efficacy guarantee.**
