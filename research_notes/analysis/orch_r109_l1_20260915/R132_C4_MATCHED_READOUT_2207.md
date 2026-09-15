# R132 C4 matched readout — 19428

Observed 2026-09-15 22:07:22 UTC. Both arms' segment056 ON/OFF capability and held readouts completed, with exit0 and complete post-run base/adapter integrity receipts. No new model/provider calls, source edits, process changes, training ingestion, or Git/shared-ledger edits.

## Matched case results

| Panel | FULL ON | FULL OFF | CONTROL ON | CONTROL OFF |
|---|---:|---:|---:|---:|
| Capability | 22/32 | 24/32 | 22/32 | 24/32 |
| Code | 0/8 | 2/8 | 0/8 | 2/8 |
| Math | 7/8 | 7/8 | 7/8 | 7/8 |
| Tool calls | 8/8 | 8/8 | 8/8 | 8/8 |
| Concise instruction | 7/8 | 7/8 | 7/8 | 7/8 |
| Held overall | 16/16 | 6/16 | 16/16 | 6/16 |
| Held true | 8/8 | 6/8 | 8/8 | 6/8 |
| Held fault | 8/8 | 0/8 | 8/8 | 0/8 |

**No new scored gain.** Against matched18404, earlier17764/17892, and immediate pre-C4 matched19300, every condition's individual capability and held pass/fail vectors remain identical: zero newly passing and zero newly failing cases. ON held advantage over OFF (+10/16), and ON code deficit (-2/8), predate C4 in both arms. This does not attribute either to the three newly registered math targets.

At19428 only the first new target was presented (update19421; FULL287active tokens, CONTROL0). Later FULL checkpoints or its additional target exposures are not used as matched outcome evidence.

## Output shape, not richness

Capability FULL ON:31/32single-line,1multiline,345tokens total; CONTROL ON:32/32single-line,330tokens. Both OFF:25/32single-line,7multiline,381tokens. All responses terminal, no truncations or token-cap hits. Held responses:16/16single-line in every condition;102tokens ON,63tokens OFF. These are descriptive shapes, not evidence of persistence or metacognition.

Compared with18404, FULL ON changes6/32raw capability outputs and CONTROL ON changes2/32, but no case changes correctness. All OFF capability outputs and all held outputs are byte-identical to18404. At19428 FULL vs CONTROL ON differs in6/32raw capability outputs and zero correctness outcomes; all16held outputs match. Against immediate19300, FULL ON changes2raw outputs, CONTROL ON changes0; no case changes correctness.

Code ON failure categories now5invalid_json+1invalid_expression_schema+2unsafe_or_invalid_expression. Earlier18404 had6invalid_json+2unsafe/invalid, but the new category split is already present in BOTH arms at19300 before C4. This is neither a passing correction nor a C4-specific change.

## Exact checkpoint and fresh-process proof

Native root: `/localhome/local-rohing/orch_r132_gen7_consumer_20260915_attempt1`.
- FULL checkpoint: `FULL/segment056/fit/FULL/checkpoints/000019428`; COMMIT `09e4d8c449cc93783ab998d6433cc955d8949abf29f60125642e444dcd48e506`; adapter-state `61e463b37e15f445a39ac45187a0cc7e73ce8227bf3741ac8ddbe81663990467`.
- CONTROL checkpoint: `CONTROL/segment056/fit/CONTROL/checkpoints/000019428`; COMMIT `f0279b5c848e3e5b801c1620aac1d6d7400d4ecaec237004e06a55f7d2d086c7`; adapter-state `e4e618f00ea06aa02c99a841055d561fd33e2c255f53ae67629fd3eb958334c2`.
- FULL ON/OFF native PIDs161223/176852; CONTROL ON/OFF323861/337838. Four distinct kernel-identity receipts, distinct from training, exact checkpoint-bound launches, all exit0.
- Both checkpoints' complete file manifests rehashed, including adapter, optimizer and saved rank/RNG files; actual metadata world_size1. Readout condition/capture fields reconstruct exactly as ON/LoRA-enabled versus OFF/disabled under the existing frozen evaluator. COMPLETE is emitted only after unchanged-base/adapter verification; no optimizer is run during readout.

## Provenance and visibility limitation

CPU-only rederivation used unchanged pinned capability/held scorers and original messages.960native captures across20panels were reduced:640capability reconstructions and320held rescorings. All reconstructed records/held summaries match originals;1002read receipt/capture files unchanged across audit. Baseline18404 and earlier17764/17892 COMPLETE hashes match R119_BOUNDED_LIVE_AUDIT_2106. Fixed32suite `32a1d71ff23e168f42366ec4c96777aceb59247020e7a3ae98b6f64b4b9b602c`; heldsuite `4528215d24a80aff62e27b834e58305f492a2b0fa640bd0b89382e5266bd69e4`.

Held prompts explicitly include the source table in16/16cases in every panel, with0parent-guidance/assistant-history/tool messages. This is **fresh-process, parent-free, source-present in-context discrimination**, NOT source/file-free retention. No held text, responses or examples are exported or mixed into training. Historical CONTROL17508 failed-postcheck caveat remains; this audit excludes it and does not retroactively certify it.

Remaining measured bottleneck:0/8code ON and no code targets added by this math-only C4 feed. The fixed held/capability failures are not collection prompts or teacher feedback. No new scientific scope is started here.
