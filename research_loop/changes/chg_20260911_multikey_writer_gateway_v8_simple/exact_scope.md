# Multi-key writer gateway V8 — simple joint-key scout

Status: proposal only. No implementation or execution authority.

V8 supersedes the unratified V7 proposal. V7 required only global and
within-stratum target balance; that geometry still admitted tool-only,
mode-only, and stratum-by-mode shortcuts. V8 changes only the mapping and its
CPU invariant so success requires the joint tool-by-mode key.

## Question

Can a rank-8 LoRA carry opposite supervised actions over an eight-tool by
two-mode interaction surface spanning sixteen seen keys, rather than
installing one global, tool-only, mode-only, or stratum-by-mode habit?

This is a writer-capacity scout. It uses deterministic verified rows because
child authorship is not part of this estimand. A pass licenses a later
child-authored source comparison; it does not itself test parenting, lived
experience, DREAM, or continual learning.

## Fixed design

- Two identity-, surface-, and seed-disjoint engineered roots.
- Eight opaque tools and two visible modes per root: sixteen keys. Each root
  partitions its tools into two precommitted four-tool strata.
- For each tool `t`, a precommitted orientation bit `b(t)` is assigned
  independently of identifier bytes. Each stratum contains exactly two tools
  with `b(t)=0` and two with `b(t)=1`.
- For mode index `j` in `{0,1}`, the positive mapping is
  `W+(t,m_j) = a[b(t) XOR j]`. The negative mapping is its exact row-wise
  complement: `W-(t,m_j) = a[1 XOR b(t) XOR j]`.
- Consequently, every tool maps its two modes to opposite actions and every
  stratum-by-mode cell is exactly 2/2 between `a0` and `a1`. Constant,
  tool-only, mode-only, stratum-only, and stratum-by-mode policies therefore
  have best possible balanced accuracy exactly 0.50 under either map.
- Eight training renderings per key. Context is loss-masked; the only target
  is the native continuation `ACT: a0` or `ACT: a1` plus EOS.
- `W+` and `W-` have identical contexts, item order, target lengths, exposure,
  optimizer steps, and seeds; only complementary targets differ.
- Four clean-base fits total: two roots times two maps. Qwen2.5-7B-Instruct,
  locally pinned; rank 8, alpha 16, dropout 0.05, all attention and MLP
  projections; learning rate `3e-5`, two epochs, batch size 1, maximum length
  2048, no packing or SVD initialization.
- Evaluation conditions are `OFF`, `W+`, and `W-`. Each sees four held
  phrasings per key with common condition-invariant seeds.
- Measurements: strict generated action, teacher-forced `a0`/`a1` log-odds,
  held-target NLL improvement over OFF, and an explicit-map OFF oracle.
- Four fixed spill families: selected tool with mode absent; selected tool
  with unsupported mode; unseen one-character-neighbour tool with valid mode;
  and an unrelated native-interface task.
- Missing, malformed, multiple, or extra-text ACT outputs are failures. No
  best-of-trajectory scoring exists.

## Decision rule

For each root, the writer passes only if all of the following hold:

1. The explicit-map oracle has strict accuracy at least 0.90.
2. Median held-target NLL gain over OFF is at least 0.50 nat for every key in
   both adapters, and the adapters' mean gains differ by at most 0.25 nat.
3. Own-map generated balanced accuracy is at least 0.80 for both adapters and
   generated accuracy is at least 0.75 in each stratum.
4. Teacher-forced direction is correct with margin at least 0.50 on at least
   12/16 keys, including at least 6/8 in each stratum, for both adapters. This
   is the predeclared directional threshold; the permitted claim does not say
   all sixteen keys bind individually.
5. Mirrored own-map versus opposite-map balanced-accuracy separation is at
   least 0.50, and mirrored gain over OFF is at least 0.20.
6. Strict native ACT validity is at least 0.95 overall and at least 0.875 in
   each stratum for both adapters; no primary output contains multiple ACTs;
   all fixed interface tasks pass.
7. For each adapter and each spill family, mean teacher-forced probability
   total-variation shift from OFF is at most 0.05 and the increase in legal-ACT
   emission rate over OFF is at most 0.05.

Both roots must pass. A missing root, retry with changed semantic bytes,
post-result retuning, pooling, replacement root, rank/dose change, or rescue
invalidates qualification. A canary or scientific failure is preserved as
the result.

Labels are `OPTIMIZATION_INCONCLUSIVE`, `ASSAY_INVALID`,
`INTERFACE_INVALID`, `BINDING_WITH_SPILL`, `MULTIKEY_BINDING_PASS`, and
`GATEWAY_NEGATIVE`, evaluated in that order where applicable.

## Simple hygiene

- One fail-if-exists, symlink-refusing run root outside every child, parent,
  CompilerGym, PCFL, and C11 tree. No saved child or parent state is read or
  written.
- Before fitting, one immutable manifest binds source-code bytes, local model
  and tokenizer revisions, templates, keys, strata, orientation bits,
  mappings, corpora, row order, target masks, seeds, recipe, evaluation
  prompts, reducers, and output root.
- Every deterministic row records root, stratum, tool, mode, orientation,
  rendering, map, target, and a derivation hash. Training inputs contain no
  explicit map, oracle answer, or evaluation output.
- Each fit starts from the exact clean base. An adapter receipt binds manifest,
  corpus, recipe, seed, and adapter-tree hashes.
- Model calls use only a run-local request cache keyed by the complete model,
  adapter/OFF, prompt or continuation bytes, seed, and decoding parameters.
  Mismatch or duplicate ambiguity aborts. No cross-run output cache is used.
- Outputs, including invalid and truncated outputs, remain in fixed
  denominators. Infrastructure retry may repeat only identical request bytes
  and seed while preserving the failed attempt.
- Atomic stage receipts and a final `SEALED.json` hash the manifest, rows,
  adapters, raw outputs, and report. Re-running the reducer must reproduce the
  report hash.
- One fresh independent implementation reviewer and one separate scientific
  advocate inspect the same implementation, tests, manifest, and dry-run
  receipts before a later execution request. An independent rejection cannot
  be overridden.

## Required CPU tests

1. Exact counts, disjoint roots, disjoint held surfaces, deterministic seeds,
   matched fit geometry, and exact row-wise `W-` complement.
2. For every tool, the two mode targets differ; each stratum has exactly two
   tools of each orientation; and every stratum-by-mode cell is exactly 2/2.
3. Exhaustively enumerate constant, tool-only, mode-only, stratum-only, and
   stratum-by-mode policy classes and require best balanced accuracy exactly
   0.50 under both maps. Include negative reducer fixtures for every shortcut
   family and one positive joint tool-orientation-by-mode fixture.
4. Target masking and a visibility assertion that map, oracle, and evaluation
   content never enter training inputs.
5. Strict parser tables, including missing, malformed, multiple, fenced,
   truncated, and extra-text outputs.
6. Path isolation, fail-if-exists, symlink refusal, hash mismatch,
   request-cache mismatch/duplicate refusal, adapter-load/hash verification,
   and atomic seal reproducibility.
7. Reducer fixtures for pass, no-learning, spill, oracle-invalid, and
   interface-invalid outcomes, with threshold equality cases.

## Resource and claim boundary

Implementation target: one experiment module, one focused CPU test file, and
one thin launcher. Expected implementation plus review: 4–8 hours. Scientific
execution is four fits with a hard predeclared cap of 3.0 A40-hours.

The strongest permitted pass statement is:

> Across two engineered roots, target-masked rank-8 adapters carried opposite
> supervised conditional native-action behavior over an eight-tool by
> two-mode interaction surface spanning sixteen seen keys, without detected
> spill or native-interface damage under the bound tests.

No result establishes lived experience, child authorship, outcome-based credit
assignment, reasoning-path learning, unseen-key generalization, retention,
parenting, continual learning, connected memory, recurrence, or the whole
organism. The full custody/visibility/security guard remains parked and is
finished and enforced only for the final paper-grade C11 run.
