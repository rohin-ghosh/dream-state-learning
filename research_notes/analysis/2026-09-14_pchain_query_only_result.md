# PCHAIN query-only result — 2026-09-14 07:36 UTC

**Query-JUNCTION acquires the supervised one-hop recall interface (32/32 versus copy-JUNCTION 0/32), but free two-hop trace and direct answers remain 0/16 each.** This is one DEV material root and learner seed 0, not general evidence of composition. One-hop query prompts now match training; these successes are not unseen-question generalization.

## Terminal evidence and comparison

Node2 roots: `/tmp/astra_pchain2_query_only_dev_20260914_attempt1` and `/tmp/astra_pchain2_free_endpoint_dev_20260914_attempt1`. Query fit reports `D1_TRAINING_COMPLETE`, 384 updates, 1,536 presentations, 40,560 target tokens; query readout reports `RAW_READOUT_COMPLETE`, 112 calls. Copy-JUNCTION has the same counts. Logged training-step seconds: query 139.280550, copy 147.966351 (not whole-job durations).

Compared artifacts retain identical recipe, seed, batch/dropout tape, assistant targets/token IDs, skill rows, initial-adapter hash, and retained-base hash. All five evaluation files are byte-identical. This is a fresh same-dose input-context comparison, not an extra dose. The unchanged CPU reducer was run locally on hash-verified snapshots; no tokenizer/model/GPU execution or new fitting occurred.

| Exact successes / designated n | BASE and LR0, each | Copy-LOCAL | Copy-JUNCTION | Query-JUNCTION |
|---|---:|---:|---:|---:|
| One-hop recall | 0/32 | 0/32 | 0/32 | **32/32** |
| Free two-hop trace | 0/16 | 0/16 | 0/16 | 0/16 |
| Free two-hop direct | not rostered | not rostered | 0/16 | 0/16 |
| Supplied-fact prompt trace | 0/16 | 16/16 | 16/16 | 16/16 |
| Empty-prompt trace | 0/16 | 0/16 | 0/16 | 0/16 |
| Canaries | not rostered | 16/16 | 16/16 | 16/16 |

Query one-hop is 16/16 first-hop and 16/16 second-hop; both were 0/16 for copy-JUNCTION. BASE/LR0 remain identical on all 80 common raw/token/termination outputs. All 112 query-JUNCTION records are valid RAW observations, with no missing/error/not-run records. **The combined report is mixed query-JUNCTION/copy-LOCAL**, not a matched query-only factorial comparison. DERANGED remains withheld/unobserved, not failed: its 80 designated slots remain missing, with redirection comparisons unavailable. No original-protocol/null-clearance claim or D2 recommendation is made.

## Actual traces

Examples are fixed indices (not selected for favorable outcomes); strings retain exact terminal LF. All displayed outputs have terminal EOT and are nontruncated.

- One-hop index 0 expects `MEMORY NEXT hfodjebfspiyrrli => blmdljisfypdpinu\n`. Copy emits `MEMORY NEXT hfodjebfspiyrrli is lqgkzncvtrrnelmu\n`; query emits the exact expected bytes.
- One-hop index 16 expects `MEMORY NEXT blmdljisfypdpinu => ymhvylkarrbfufdw\n`. Query emits this exact relation on the isolated second-hop probe.
- Free trace index 0, starting at `hfodjebfspiyrrli`, expects:

```text
MEMORY NEXT hfodjebfspiyrrli => blmdljisfypdpinu
MEMORY NEXT blmdljisfypdpinu => ymhvylkarrbfufdw
ANSWER ymhvylkarrbfufdw
```

Query-JUNCTION actually emits:

```text
MEMORY NEXT hfodjebfspiyrrli => blmdljisfypdpinu
MEMORY NEXT blmdljisfypdpinu => hrijdyrckzdyrckz
ANSWER hrijdyrckzdyrckz
```

- Free direct index 0 expects `ANSWER ymhvylkarrbfufdw\n`, but query emits `ANSWER hfodjebfspiyrrliexxgfpafxfypdpinu\n`.

Line-level annotation of all 16 free traces (not replacement scores): query has 3/16 exact first MEMORY lines, 0/16 exact second lines, and 0/16 exact ANSWER lines; copy has 0/16 for each. All 16 traces in each arm terminate and none truncate. Thus the failure is not merely LF/EOT rejection: individually recalled atoms do not reliably transfer to the two-hop output context in this run. The printed trace does not establish causal mediation.

## Artifacts, hashes, and executed reduction

Local root: `gpu_artifacts_local/astra_pchain2_query_only_reduce_20260914_attempt1`. Its `evidence/REMOTE_MANIFEST.json` records SHA-256/size verification for 43 copied files (1,048,241 payload bytes); no model/adapter weights were copied. `ANALYSIS.json` retains comparison checks and paired examples. `COPY_REDUCTION.json` is the separately rerun original comparison.

- Query raw JSONL: `026e4a8df7fbb57b8f67b2bf11e001f08da32a0e1600fe6f1861947428b7c9ee`
- Copy-JUNCTION raw JSONL: `3eb0dbbfccc804117b9863048c75d23247daeaf82df93a6e23768250e1af7b8a`
- Unchanged reducer: `954088a7be7453cfa6a4645ad355eef628d85d5c82a1b6ba19b1812d05dde2b8`
- `QUERY_MIXED_REDUCTION.json`: `5c79ca4b4b4467dd04ee2727d93d38b10e8f9fcb98ff18da5f0947048ddef6e8`
- `COPY_REDUCTION.json`: `9447f89b4e483f7550b3a88fa734a51adad9bc6cb6605a115b518324fc511f6f`

Executed from the local repository, using the captured node2 paths below:

```bash
DEST=gpu_artifacts_local/astra_pchain2_query_only_reduce_20260914_attempt1
Q="$DEST/evidence/astra_pchain2_query_only_dev_20260914_attempt1"
C="$DEST/evidence/astra_pchain2_free_endpoint_dev_20260914_attempt1"
PYTHONDONTWRITEBYTECODE=1 python3 -m gpu.astra_pchain2_free_reduce \
  --evaluation-dir "$Q/material/evaluation" --readouts-dir "$C/readouts" \
  --raw "ATOM-JUNCTION=$Q/readouts/ATOM-JUNCTION/raw_readouts.jsonl" \
  --output "$DEST/QUERY_MIXED_REDUCTION.json"
```

The copy comparison uses `$C/material/evaluation`, omits `--raw`, and writes `COPY_REDUCTION.json`. Existing files were not overwritten; subsequent snapshots require fresh output names.
