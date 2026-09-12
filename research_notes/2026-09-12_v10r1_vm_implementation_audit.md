# V10R1 VM implementation audit

Date: 2026-09-12 UTC

Status: fresh read-only implementation audit. The three builder-owned files
were read only through `bash gpu/nvl_ssh.sh`; this audit did not edit them,
prepare a real run, load a real tokenizer/model, or use a GPU.

Audited uncommitted VM bytes:

- `organism_v6/multikey_writer_gateway_simple.py` — SHA-256
  `2a77d928772c87db3f352c881042914fad2091aecf7fb9428e9d4de9ff01355a`
- `tests/test_multikey_writer_gateway_simple.py` — SHA-256
  `a39806b03b6b82b34cd6458763fab1fd6e8f7facb1d9d44d6b92868f403d8fed`
- `gpu/multikey_writer_gateway_simple.sh` — SHA-256
  `3994bf389e63ac790b3eb500c74a974ed57b88fd8fd02d494ae6fecc0ab33665`

  (The initially committed audit contained one extra `c` in this displayed
  digest. The correction is documentary; the launcher bytes were unchanged.)

## Verdict

**GO for CPU preparation. GO for bounded GPU execution under the standing
builder authorization in `AGENTS.md`. Not yet exact-scope/paper-closure
complete.**

No launch-blocking scientific-mechanics defect was found. The implementation
matches the central V9/V10/V10R1 contract: four clean-base fits; 128 rows and
256 optimizer steps per fit; context-masked supervision of only the exact
`ACT: a0\n`/`ACT: a1\n` continuation plus EOS; the real-tokenizer joint-stream
preflight before any model load; the fixed 1,504-request schedule; fresh
processes for every fit and state-by-operation load; strict ASCII parsing;
full-precision likelihood reduction; fixed denominators; declared gate
precedence; and fail-if-exists receipts, adapter-tree hashes, raw traces,
seals, and replay.

The remote CPU-only suite passed **47/47 tests in 8.820 seconds**. It used no
real tokenizer, model, or GPU.

The one closure defect is the review receipt. `prepare_real` writes
`mwg10r1_review_receipt.json` with status `NOT_AN_INDEPENDENT_APPROVAL`
(audited VM module lines 961–964), while `validate_prepared` checks only its
presence/hash and never rejects that status (lines 972–1004). V9 requires a
fresh implementation reviewer and a separate scientific advocate over the
same source, tests, manifest, and dry-run receipts
([V9 exact scope](../research_loop/changes/chg_20260911_multikey_writer_gateway_v9_simple/exact_scope.md#L195)).
The later standing builder authorization expressly removes that as an
*operational prelaunch gate* ([AGENTS.md](../AGENTS.md#L44)), so Astra may run
the bounded experiment. The result should not be described as fully
V9/V10/V10R1-closed until the two bound reviews exist or the evidence record
explicitly records the standing waiver.

## Contract trace

- Material generation and validation are at audited VM module lines 137–235:
  the two XOR-complement maps, 512 total training rows, 384 primary held
  condition-items, complete template crossing, and exact chance shortcut
  maxima. This matches the frozen geometry
  ([V9](../research_loop/changes/chg_20260911_multikey_writer_gateway_v9_simple/exact_scope.md#L24)).
- Joint tokenization and loss masks are at lines 252–283; the real tokenizer
  repeats them over all four fits and all scoring/generation surfaces before
  model load at lines 839–902. Training recomputes and hash-matches those
  encodings at lines 1132–1144. This matches the exact target and preflight
  requirements ([V9](../research_loop/changes/chg_20260911_multikey_writer_gateway_v9_simple/exact_scope.md#L77)).
- The fit is a clean base loaded inside each worker, rank 8/alpha 16/dropout
  .05 over all seven attention/MLP projections, AdamW at `3e-5`, batch one,
  two fixed passes, no packing/fallback, no skipped nonfinite batch, and
  exactly 256 recorded steps (lines 1072–1191). Four fits are scheduled in
  distinct processes at lines 1308–1343. This matches the frozen fit recipe
  ([V9](../research_loop/changes/chg_20260911_multikey_writer_gateway_v9_simple/exact_scope.md#L87)).
- Requests bind operation, model/tokenizer/run identity, adapter tree or OFF,
  prompt, candidates, seed, parameters, and token counts (lines 308–429).
  Counts are 384 primary generations, 256 oracle generations, 240 spill
  generations, 384 primary scores, and 240 spill scores = 1,504 (lines
  822–829). The executor makes five fresh generation and five fresh scoring
  loads in addition to the four fit processes (lines 1344–1364), and final
  validation requires 14 distinct worker PIDs (lines 1408–1482).
- Parsing at lines 238–249 implements ASCII-only outer trimming, no Unicode
  normalization, line-anchored exact-case multiple-`ACT:` counting, and
  U+00A0 rejection, matching V10R1
  ([V10R1](../research_loop/changes/chg_20260911_multikey_writer_gateway_v10r1_simple/exact_scope.md#L15)).
- Reduction at lines 431–556 implements stable two-candidate log-sum-exp,
  per-key even medians, generated BA/validity/strata, oracle, spill, native
  interface, and the exact six-label precedence in V9
  ([V9](../research_loop/changes/chg_20260911_multikey_writer_gateway_v9_simple/exact_scope.md#L107)).
- Run custody, local snapshot hashes, source hashes, stage receipts, deadline,
  raw token traces, adapter reload digests, final seal, and read-only replay
  are at lines 559–635 and 905–1506. A failure writes
  `NONREPORTABLE_ABORT` and no scientific label (lines 1382–1388).

## Nonblocking refinements / minimum remaining tests

1. Add a negative execution test for the review status if exact-scope closure
   is desired; alternatively bind the standing builder waiver explicitly and
   keep the scientific-advocate review separate from launch permission.
2. The fake tokenizer class named `Straddled` changes token zero's offset
   rather than constructing a token that literally crosses the context/target
   boundary (test lines 138–149). The implementation's boundary predicate is
   correct, but add the literal boundary-crossing regression.
3. Add an explicit assertion that the fixed material's complete tool plus
   one-character-neighbour identifier sets are disjoint across both roots.
   Current generation checks within-root neighbour uniqueness and cross-root
   tool uniqueness; canonical regeneration makes the frozen default material
   stable, so this is a defense-in-depth test rather than a current-data flaw.
4. Before GPU execution, require the actual `prepare` output to pass the local
   Qwen tokenizer preflight, all 47 CPU tests, snapshot/environment pins,
   protected-root containment, fresh output-root checks, and lease/GPU
   identity checks. Preserve the prepared directory unchanged; do not rescue
   or reuse a partially executed root.

## Claim boundary

Even a pass is only four supervised, seen-key conditional-policy carriage
instances. It is not retention, lived learning, DREAM, parenting,
generalization, connected memory, recurrence, reliability, or a whole-agent
result, exactly as V10R1 states
([V10R1](../research_loop/changes/chg_20260911_multikey_writer_gateway_v10r1_simple/exact_scope.md#L34)).
