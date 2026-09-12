# Clean-nursery integration fresh audit — 2026-09-12

Audit sealed at 2026-09-12T07:25:23Z. Read-only inspection of Astra's VM
checkout; no builder source, process, job, or node was changed. The VM HEAD at
the final test/hash capture was `7787085f714f85916b0be1ac46c87a1ea580421c`;
the files below were uncommitted.

## Verdict

**REWORK before any GPU run whose product will be called a clean nursery
ancestor.** The main chain is now substantially coherent, but one direct
runner/gate contract collision can reject an ordinary child output at the first
SLEEP, and no authenticated real-Qwen birth pin inventory presently exists.
Fixing the collision and supplying the pins would make a bounded, fixed-teacher
reasoning-nursery canary scientifically runnable. It would not yet close an
adaptive-parenting, reusable-lineage, or paper claim.

## Launch-blocking for a clean-lineage run

1. **The prompt-authorized `NOTE:` row is forbidden by the clean gate and
   lineage.** `bootstrap_reasoning_gym.txt:16` explicitly asks the child to use
   `NOTE:`. `batch_loop.py:17,101-106` recognizes it and appends ledger kind
   `note`. But `preschool_reasoning.py:749` permits only
   `episode_occurrence/act/note_after/thought/parent_turn`, and
   `life_lineage.py:481-483` independently rejects every other kind. The passing
   negative test `test_unknown_episode_end_and_literal_notes_remain_fail_closed`
   confirms that rejection; the eight runner fixtures emit ACT-only text and
   therefore miss the integration seam. A normal Qwen `NOTE:` can abort the
   first SLEEP. Preserve and provenance-bind this child-owned influence, or make
   the clean runner unable to emit the duplicate row, and add an end-to-end
   regression before launch.

2. **A complete birth-byte inventory is unavailable, fail-closed.** The VM has
   no clean birth-pin JSON or local Qwen snapshot, and the Builder's 07:17 UTC
   coordination entry says no validated pin file was produced. The node-local
   snapshot identifier
   `a09a35458c702b33eeacc393d103063234e8bc28` is useful local identity only; it
   is not by itself the complete runtime-file SHA256 map that `prepare_birth`
   requires. Remote Hugging Face API authentication is not necessary for this
   controlled comparison: a full hash inventory of the actual local snapshot,
   its self-identifying configs, and the exact bytes used by every arm is
   sufficient. The synthetic runner fixtures explicitly are not Qwen evidence.
   Thus no genuine clean run was launchable from the evidence audited here.

3. **For a lesson-versus-sham causal launch, tokenizer dose matching remains an
   explicit unmet prelaunch condition.** Each lesson receipt still states
   `token_budget_match="unverified; requires actual tokenizer before launch"`;
   the runner accepts it. This does not block a slot-only plumbing canary, but it
   blocks interpreting a present lesson/sham launch as a content-controlled
   parenting comparison.

## What is coherent once those gates close

- Fresh birth requires an empty life, a fixed Qwen model ID, exact config,
  tokenizer, index/shard and weight hashes, no loaded adapter, and no other
  influence; it copies the verified bytes into `lineage/birth/model` and makes
  that copy the actual backend/trainer model path.
- The clean CLI excludes dynamic parents, society/clone state, reflection,
  curricula, deployment-gym mixing, probe selection, neutral probes, inherited
  briefs and plasticity. Its only parent treatment is fixed `lesson` or active
  `sham`; the exact teacher turn and receipt enter the ledger, but never the
  corpus.
- Every admitted item is rebuilt from one earlier, occurrence-reserved ACT and
  one child `note_after`; action, outcome, displayed/authoritative score,
  occurrence, execution, generation identity, prompt/output hash, batch
  cardinality and ledger-prefix hash are checked. The strict verifier refuses
  to invent a measured zero after an exception. Compiler/deployment vocabulary,
  held-out reasoning families, quarantine strings and unknown influences fail
  closed.
- The enforced corpus is cumulative, unique, verbatim child text in the exact
  `Situation ... / My measured action record:` wrapper. Training starts from
  the copied frozen base, rank 8, with an explicit seed; label tensors mask the
  whole wrapper, boundary-crossing tokens and padding. The trainer receipt binds
  per-row source hashes, actual label counts, corpus/gate/previous-manifest
  hashes, metadata and saved LoRA bytes.
- A DONE checkpoint snapshots base ancestry, cumulative ledger, parent turns,
  admitted event rows, corpus, gate/trainer receipts, metadata and adapter
  bytes; later SLEEP records one predecessor and requires append-only ledger
  growth. The separate `adult_controls` helper can consume such a pinned child
  checkpoint without returning childhood notes/briefs/parent turns as adult
  context.

## Paper-closure defects (not reasons to suppress a disposable canary)

- The implemented parent is a fixed artifact lesson, not an adaptive parent.
  No neutral H1 transfer probe or running-versus-true-shadow adult integration
  exists in this clean runner; `adult_controls.py` explicitly remains a helper,
  not runner/GPU wiring.
- Candidate admission depends on a reasoning canary, but the manifest snapshots
  only the resulting `DONE` marker. It does not bind the canary IDs, prompts,
  outputs, rate, or decision receipt; the manifest misleadingly references the
  training-ledger sources for that selection artifact. This must close before
  the checkpoint is used as paper-grade ancestry.
- The compact gate receipt omits the gate-detail policy/source identity, and the
  runner immediately treats its own returned digest as the "external" expected
  gate pin. Later ancestry replay checks hashes and structural joins, but cannot
  independently reconstruct the semantic admission decision.
- Backend generation receipts describe configured model/adapter inputs, not
  authenticated in-memory state. No real-tokenizer, real-LoRA train/reload,
  multi-SLEEP, or adult-handoff run has yet been observed. Wall-clock text in
  `CLOCK` also prevents exact common-prompt pairing across causal arms.

## Nonblocking refinements

Close the ResourceWarnings for the bootstrap, life log and DONE marker; add a
real-tokenizer prefix-boundary fixture, a two-SLEEP runner fixture, a malformed
reasoning-answer continuation test, and explicit trainable-parameter/gradient
evidence. These improve robustness but do not replace the two launch blockers
above.

## Exact CPU evidence and file hashes

On the final bytes, this command passed **142/142** in 5.931 s without loading a
model, tokenizer, or GPU:

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -q tests.test_clean_nursery_runner tests.test_child_receipt_integration tests.test_preschool_reasoning tests.test_life_lineage`

Relevant SHA256 values:

```text
4b67a9d4178c7d937c9c56e3ec3b7acb67729f7b8b122303447b4d1d5653b2f9  organism_v6/run_life_v2.py
8b06637f59d97203806941808ac7ef3b0bdc467dfbbdc3c1a07669eb1699683b  organism_v6/preschool_reasoning.py
916276f3572e45e1f8e187c7a8aa1cb6ced3fde04e98b09c32665237b0168c5f  organism_v6/life_lineage.py
9e39b6b6816f00ce2a78476f16e784daf31d7b26c673cbcddaf6ab508cf09caf  organism_v6/train_adapter.py
821471f4ddd136f64c7151a5fa0a4b1c2cc0d5be00c9febb73d5b215dccb7605  organism_v6/batch_loop.py
9b2cf7521bc75fe995ffa05a117f61d12ded24395e8b315e384f58add846e1f1  organism_v6/bootstrap_reasoning_gym.txt
220071c8783ed4d608b04015c188e8b22fc5745c10f250c7fbd724dd854649ea  organism_v6/reasoning_gym_families.json
da9879537d33923c9702b1a5b3d63d6a2fcb396a64e110a886bd445c33e1c084  organism_v6/reasoning_gym_gym.py
68d5aabcf725efbc45f52ba6f4e0ac03a32a134f6aa8699003e054338c53878e  organism_v6/model_backend.py
ea598a67f4ce62d3792f551c6f46e8899a5b02af954d22b862b0e3f3346b0743  organism_v6/adult_controls.py
61554a2def97cdfa8524440787a9e37c37141b2925879f8233cdb4f4c3080476  tests/test_clean_nursery_runner.py
ee5142c395df329e396f43ba09e756b99df7bcc0205665844346b69b37d6a395  tests/test_child_receipt_integration.py
505682e22850defe0f844d9df44d6a567970f5dc6da71ef1778d824741e0be89  tests/test_preschool_reasoning.py
0f7c3d26287deda898a7b5541e6b1bfc04bade766b11df39dbae092cf87240da  tests/test_life_lineage.py
```
