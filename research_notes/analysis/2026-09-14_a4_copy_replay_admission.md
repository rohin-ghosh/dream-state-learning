# A4 + SOURCE_ACTION_COPY: native CPU admission

**PASS — `A4_COPY_REPLAY_NATIVE_CPU_ADMISSION_PASSED`.** Native A100 command
exited **0**, with no stderr/errors, at **2026-09-14 08:47:00 UTC**;
Python elapsed **22.370 seconds**. No source/tokenization/mask/schedule blocker
observed. This admits these deterministic preparation checks only, not a claim
of downstream success, causal isolation, or birth qualification.

## Bound inputs and scope

- Main-declared synced source: `2bb752f273cda66e96b05414caac8e97eaeb40e9`;
  A100 overlay **S** = `/tmp/astra_outcome_a4_replay_source_20260914_attempt1`.
  Compiler, runner and tokenizer-helper file hashes matched the local source
  and were asserted again inside the CPU process before replay.
- Collection **R** = `/tmp/astra_a4_collection_20260914_attempt1/run`.
  Existing `source.load_collection` replay passed all 32 episodes/100 calls,
  returning the exact previous **30 A4 selected rows** (four strict successes,
  two KEEP and two REVISE). All five input hashes match the prior node2 audit.
- Only this new note was written. No remote artifacts, model loads, optimizer
  construction, fitting, GPU activity, launch/process control, or EVAL execution.
  `CUDA_VISIBLE_DEVICES=''` was asserted; CUDA remained uninitialized.

## Compiler and origin checks

Called `compile_copy_rows(rows)` from `organism_v6.outcome_action_replay` and
received **12 rows**, two per family. Metadata kind is
`ACTUAL_TRAINING_ACTION_AUTHORED_COPY_PROMPT`: these are authored copy prompts
using experienced training-action bytes, **not 12 new experienced trajectories**.
The original 30 rows were unchanged byte-for-byte; recompilation was deterministic.

Independently checked each metadata origin against its complete source row hash,
assistant-byte hash, episode, call index and original row index. All 12 call
indices are distinct; selection is the two lowest source call indices per
declared family, not an outcome/evaluation-based choice. Each target/EOT/loss
policy equals its original. Each new prefix is exactly the existing system
message plus:

```text
Return the following text verbatim, without explanation:
{actual source action}
```

All original and copy prefixes exclude the recorded teacher guidance. Exact
prefix equality also excludes additional guide text from copy prompts. No held
rows, identifiers, target construction, or evaluation results were consumed by
the pure copy compiler. Original outcomes retain their replay-validated prefixes.

Indices below are zero-based; source calls refer to R/CALLS.jsonl (line = call+1).

| Copy index | Family | Source row / call | World-member | Exact assistant target | Presentations |
|---:|---|---|---|---|---:|
| 0 | READ INDEX | 0 / 15 | h01-m1 | `READ INDEX M2AN_IDZBKDEYPTXR` | 22 |
| 1 | READ INDEX | 4 / 19 | h01-m1 | `READ INDEX M2AN_2BVRIFVFLTII` | 22 |
| 2 | READ RELATION | 1 / 16 | h01-m1 | `READ RELATION M2AQ_VTF4BXOM2RT6` | 22 |
| 3 | READ RELATION | 5 / 20 | h01-m1 | `READ RELATION M2AQ_AV6I5VVOU5HJ` | 22 |
| 4 | STEP | 2 / 17 | h01-m1 | `STEP M2AP_Q2MMULOO6TOW` | 21 |
| 5 | STEP | 6 / 21 | h01-m1 | `STEP M2AP_7BK7AMFGIYBT` | 21 |
| 6 | THINK KEEP | 3 / 18 | h01-m1 | `THINK KEEP M2AE_E2QOXYG4HMP5` | 21 |
| 7 | THINK KEEP | 11 / 34 | h02-m1 | `THINK KEEP M2AE_NNNUJBVQ2R4T` | 21 |
| 8 | THINK REVISE | 19 / 85 | h13-m0 | `THINK REVISE M2AE_XPUFCO5OI5P2` | 21 |
| 9 | THINK REVISE | 26 / 92 | h13-m1 | `THINK REVISE M2AE_F6P5ACALQCG2` | 21 |
| 10 | STOP | 7 / 22 | h01-m1 | `STOP` | 21 |
| 11 | STOP | 15 / 38 | h02-m1 | `STOP` | 21 |

## Native tokenizer, targets and masks

Used the collection request's official local Qwen snapshot:
`/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28`.
Loaded **only AutoTokenizer**, local-only/no remote code. Verified the official
receipt SHA and tokenizer.json size/SHA, restored the native backend **in memory**
using `tokens.official_native_backend(raw)`, checked wrapper/special-ID preservation
and backend equality with A4's retained reference, and bound chat-template
`return_dict=False`. The artifact-writing restoration wrapper was not called.

`source.tokenize_rows(tuple(rows)+tuple(copy_rows), tokenizer, guidance=...)`
passed **all 42 rows**. Asserted all prefix labels and trailing newline labels
are -100; assistant/EOT labels equal their input-token slice and decode exactly
to the original action plus EOT. Every copy target's token IDs equal those of
its specific original outcome row. All 30 original token/mask receipts retain
the previous canonical hash. Existing helper checks exact full-template token
composition and nontruncation; no target was repaired or substituted.

| Row kind | Rows | Sequence token range | Corpus assistant/EOT tokens |
|---|---:|---|---:|
| OUTCOME | 30 | 306–3754 | 389 |
| SOURCE_ACTION_COPY | 12 | 268–298 | 158 |

Context limit **16384**. Runtime: torch **2.13.0+cu130**, transformers **5.5.3**,
tokenizers **0.22.2**; intra/inter-op threads **1/1**. No PEFT/model load.

## Exact 256-batch replay

Called `source.cyclic_batch(combined_tokenized, update, pad,
outcome_row_count=30)` for **updates 1–256**. Every batch has four rows;
the first three indices equal the unchanged outcome-only scheduler's first
three slots. Fourth index is exactly `30 + (update-1) % 12`. Checked selected
row identity, padding token values, zero padding attention, and -100 padding
labels across all batches.

- **768 OUTCOME + 256 SOURCE_ACTION_COPY = 1024 row presentations**.
- Calculated target-token presentations: **10054 OUTCOME + 3377 COPY = 13431**.
  These are schedule calculations, not executed training cost.
- Copy indices 0–3 occur 22 times; 4–11 occur 21 times: READ INDEX/RELATION
  get 44 presentations each; STEP/KEEP/REVISE/STOP get 42 each.
- Outcome row exposure is intentionally not uniform: row 0 and row 2 occur
  35 times, row 1 occurs 18 times, remaining even indices 34 times, remaining
  odd indices 17 times. This is the specified fourth-slot replacement on the
  original stride-four cycle, **not a scheduler error or an added rebalance**.
- Compared with unchanged A4-only scheduling (1024 outcome presentations,
  13284 target-token presentations), this preserves updates/batch size, not
  outcome dose, supervised-token count, or compute. The earlier skin/branch
  confound remains; this preflight establishes no causal isolation.

## Command and hashes

Exact execution wrapper, with the CPU assertion script supplied on standard input:

```bash
bash gpu/a100_ssh.sh 'timeout --signal=TERM --kill-after=5 120 env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /localhome/local-rohing/v2/venv/bin/python -B -'
```

The script prepended S to `sys.path`, used source label
`INDEPENDENT_A4_COPY_REPLAY_NATIVE_CPU_20260914`, and executed the APIs/assertions
described above. The native command had **no errors**. An earlier path-discovery
command exited 1 because absent candidate Python paths and unrelated protected
`/tmp` directories were encountered; this did not involve preparation/model
execution, and the actual native interpreter path was found successfully.

All derived hashes below use sorted compact ASCII JSON via `source._json_bytes`;
mask/schedule hashes refer to in-memory receipts, not newly written files.

| Evidence | SHA-256 |
|---|---|
| S/organism_v6/outcome_action_replay.py | `5ae26d09b3face4256a884f8cdb5d38eeafd8b027592d04a88dfd327d89fbe35` |
| S/gpu/astra_stage2a_outcome_distill.py | `f1bf35071fd41ade767e27c0e4473aa0ae6015be2574b9dd03d25cfba12a22f6` |
| S/gpu/astra_stage2a_native_tokenizer_receipt.py | `de10c87a8903ac9d793c8d4b2f9c045691ea4e4d839b037069db16e14641733e` |
| R/RESULT.json | `d963c497e99c5fb023101b22f1305df7e266ed5bfae99b98ad6fc624f1256f98` |
| R/REQUEST.json | `b03f99a841c74069bb098f4290cc016333ed42e4727db84db0d5857aec887b6e` |
| R/EPISODES.jsonl | `872a8591316650c23313aded6e8d1936e0f55281ad102c27d1b4c88d53daf18b` |
| R/CALLS.jsonl | `0dca3eee6d66d7f79eb94ee77fa4626a6d40eea29cb3f3fb203f25dbe75ff55f` |
| R/DRAFT_TRAINING_ROWS.jsonl | `6f73927c0e617143f295aca994a9cdf4c8dea217866b643b66ecd03c6a8ac3db` |
| Original 30 rows | `59517b5f9c6922f97409084db45afda9e50ba0bac473285331327475ac58b3c5` |
| Compiled 12 copy rows | `adf4968038ca1e84bd3402803763be65701438ebf7526178f2f3240e994c0233` |
| Combined 42 rows | `c419e0135ed93fa47ea674056dca208677906d0b54576ff7cb416de98dc04e65` |
| Compiler metadata | `184f1b3505c909bc027b706350ecc9be2cbc239388b69ac497e80a755cfd947e` |
| Combined mask receipt | `f96decd0daffe501f8f3f346d07d82ccc871dc17c8a71dd991357700f3899e48` |
| Original-only mask receipt | `544bca178acb674a15e0cfe0a72db5004a5db8953dfa4b46d1f9160cf6e0b74b` |
| 256 index tuples | `f940e033fe4a6a69400f140a019a6b203992ed71e994d418f8808bfd16851491` |
| Official receipt | `e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019` |
| Official tokenizer.json | `c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539` |
| Restored native backend | `f884026e05f6dfffe68b72d580b588006d98b3bc0a128bb1ac425c76f7fc438c` |
