# 33 — GPU-loop constraints for semantic-world-v0 (Fable -> Codex handoff)

Written by the agent operating the G-series GPU loop. These are MEASURED
constraints from getting nonce-L0 from 0.28 to the 0.949 oracle ceiling
end-to-end (see alchemy/v2_out/mini_ledger.md for every cycle). The world
design decides whether the proven machinery plugs in or dies in parsing.

## 1. What the proven pipeline needs from the world (hard requirements)
1. EXECUTABLE ATOMIC CLAIMS. The dreamer's output only becomes memory
   after per-claim engine verification (Voyager rule). The world must be
   able to verify single-observation-sized claims ("the cow in candyland
   is blue", "X and Y ruin") — verify_claim(claim, evidence_ids) is
   exactly right; keep claims small. Family/abstraction claims get
   verified through their implied instances (spot-check pairs).
2. NAMEABLE ABSTRACTIONS. Every latent factor a solver needs must have a
   coinable handle ("the crimson-family", "the rotate-2 lands"). Reads
   through an adapter only work 1-hop: "Q: which family? A: <name>" then
   "Q: what does <name> do? A: <short answer>". 2-hop reads collapse
   inside adapters (measured: 0.25 vs 1.00 when flattened to 1-hop).
3. ATOMIC PROOF LEAVES. proof_for(goal) should decompose every D1-D3
   goal into leaves that are each expressible as ONE atomic QA line.
   The thinker resolves leaves as separate adapter reads and the CLEAN
   base composes them in context. If a D3 proof needs a leaf that can't
   be one QA line, the goal is unreachable by the current reader.
4. A CANONICAL CLAIM GRAMMAR. My absorb() stage regex-parses dreamed
   claims. Specify the exact claim surface forms in the world spec
   (few, rigid, one per line). Free-form dream prose is fine as
   scratch; the EMITTED claims must be grammar-conformant.
5. SHORT CANONICAL ANSWERS, NO NEGATIONS. Verbalized memories must use
   positive canonical phrases ("nothing happens", never "they do not
   form a product") — a negation cost us a full eval inversion
   (normalizer matched "product" inside "do not form a product").
6. SYMMETRIC RELATIONS NEED BOTH DIRECTIONS (or a declared canonical
   order). Adapters are order-sensitive: "A meets B" trained does NOT
   answer "B meets A" (measured).

## 2. Measured recipes (Qwen2.5-7B, bf16, LoRA rank 64, lr 2e-4)
- ~200 touches per fact for reliable storage (1.00 read-back);
  32 touches -> 0.58. touches = duplicates x epochs; we use x8 dup,
  25 epochs. Budget corpus size = verified_lines x 8.
- Relation/rule lines need ~3x the exposure of membership lines
  (upweight or they read back corrupted while memberships are perfect).
- Post-train sanity gate ALWAYS: one read; if gibberish, drop LR
  (ladder 2e-4 -> 1e-4 -> 5e-5). 5e-4 destroys the model.
- Train in a SUBPROCESS, separate from any vLLM process (in-process
  vLLM<->peft handoff corrupts state; cost us multiple nights).
- Read-only adapter protocol at eval: adapter mounted ONLY to emit the
  memory block; unmounted; clean base composes and answers.

## 3. Eval-design constraints (each of these burned us once)
- NEVER small max_tokens on eval/diagnostic calls (a 24-token cap
  produced an all-zero artifact and a false negative). Generous caps,
  parse the final answer.
- Balance eval sets per outcome kind and report per-kind accuracy +
  balanced mean. Majority-class priors made months of numbers fake
  (0.58 NOTHING-prior). Publish the prior as the floor line.
- Kind-level scoring must accept bare category answers ("PRODUCT" with
  no name). Exact-name scoring only means something if names are
  non-derivable from the question (use seeded nonce product names).
- The model CANNOT select the right rule from an in-context rulebook
  (0.28 measured) but applies a pre-resolved rule at 0.77-0.91. Do not
  design evals that require in-context rulebook selection; the thinker
  resolves first.
- Leak test both directions: names must not predict answers (their
  plan), AND the answer must not be derivable from the question string.

## 4. Dreamer facts worth knowing before designing supervision
- The dreamer's grouping instinct is real but noisy: it groups by
  surface co-occurrence (shared product names) unless told what
  "behave alike" means. Dense supervision for WHICH observations
  belong together (their plan) is the single highest-value signal.
- Degeneration loops happen (one token repeated 300x amplified into
  the corpus): any dream ingestion needs a repetition filter.
- COVERAGE-DRIVEN RE-DREAMING is the workhorse: one targeted round on
  "what's still unexplained" took coverage 0.54 -> 0.96 in every world
  tested. Design the supervision so "what is still unexplained" is
  queryable (their structural-coverage metric enables exactly this).
- Second-order inference works and matters: merging two clusters
  because a verified inter-cluster rule logically implies identity
  (ruin => same family) is the first "connection over memories" we
  have running. Blendyland-style meta-rules are the same shape.

## 5. Plug points (what I will connect when the spec lands)
lifetime -> chunked dreams -> claim absorb (grammar parse + verify)
-> claim graph -> daydream rounds (coverage-driven) -> merge inference
-> coined names -> atomic QA emission (measured exposure) -> LoRA
-> resolved atomic reads (canonical order, first-clause normalize)
-> clean-base composition -> D0-D3 eval.
Asks: (a) per-observation provenance ids on every rendered line,
(b) eval splits pre-balanced by depth AND kind, (c) a context-oracle
harness hook (same goals answerable from raw latent structure in
context — our ceiling gate before any training run).
