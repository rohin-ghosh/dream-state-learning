# L0 iteration ledger (overnight 2026-08-25/26)
Rule: every recalibration cites the result's decomposition + which design
principle drives the change. Bar: memory_think matches context player.

| run | config delta | context | rag | mem_plain | mem_think | diagnosis -> next |
|---|---|---|---|---|---|---|
| L0-a (50ep) | initial | kind .43 | .55 | .34 | .27 | ALL <= NOTHING-prior (.58); join-names echo question => both metrics contaminated. FIX INSTRUMENT: balanced eval, nonce names, per-kind, grouping-F1 |
| L0-b (200ep) | eps x4 | .24 | .57 | .54 | .54 | same contamination; context DEGRADES with length (lost-in-context redux) |
| L0-c1 (50ep, balanced) | fixed instrument | kind_bal .385 grpF1 .14 | .333 (NOTHING-spammer) | 0.0 GIBBERISH | 0.0 | 5e-4 recipe DESTROYED adapter (articulation = word salad); dreams good but group-lines unverified (12-member ruin groups, max legit 5). FIX: sanity gate + lr ladder, group verifier, behave-alike dream format |
| L0-c2 (50ep) | sanity gate + verified group dreams | .385/grpF1 .15 | .333 | .333 (NOTHING) | .359 grpF1 0 | adapter SURVIVES (gate works, 1e-4); mem_think ~ context parity BUT acc_product=0 for ALL arms every cycle => raw logs are a bad induction substrate for everyone. NEXT: organized-context + dreams-as-context arms |
| L0-c2 (200ep) | same | .333 (product-happy style) | .333 (NOTHING) | .282 | .333 (all-RUIN style) | every arm = a different answer-style at prior; dreams COLLAPSED 22->14 lines as log grew 4x (single-call dilution => needs chunked dreaming). Awaiting c3 decomposition |
| L0-c3 (50ep) | +organized-ctx +dreams-as-ctx | raw .0 prod | — | — | — | ORDERING: raw .00 < organized .15 < DREAMED .31 on product induction — dreaming adds value beyond organization (first positive!). Weights path still all-RUIN style. Gaps: dream coverage thin (22 lines); consolidation. NEXT: chunked multi-pass dreams + coverage metric |
| G2/G2b/G2c | oracle-in-weights + resolved reads + write-as-reads | oracle_resolved .77 (prod/ruin 1.0) | — | mounted dead | adapter_resolved .31 (prod .62) | CHAIN MAPPED: apply .77-.91 OK / rulebook-select .28 FAIL => thinker resolves; write-as-reads fixes storage (gate returns real members; prod 0->.62); remaining gap = read-answer accuracy. Dreamer inspect: degeneration line x300 amplified into corpus + behave-alike lines unverified => filters needed |
| G2d/e/f | read decomposition -> named abstractions -> full exposure | — | — | — | **G2f: 0.949 end-to-end, family-reads 1.00** | THE STACK PROVEN: coined names + atomic 1-hop facts + 200 touches + resolved reads + clean base = 0.95 through WEIGHTS (beats context oracle 0.77). Prior failures: 2-hop reads (rule collapse), exposure 32 (0.58 storage), rulebook-dump (selection fail). NEXT: real dreamer with name-coining + atomic emission = end-to-end L0 |

## G4 (real dreamer, thin prompt): FAILED 0.282 — grouping regression
- Dreamer coined families from PRODUCT NAMES ("mirtesine-family" = things
  that fused into mirtesine), not behavior: 2 families, 6 memberships,
  1 rule = 7 verified lines (G2f oracle had ~68). Wrong abstraction, so
  the adapter had almost nothing to say; reads hallucinated continuations
  ("...However, it's more commonly known as belo").
- LESSON: the thin one-shot "group and emit QA" prompt regressed from the
  proven run_mini behave-alike dreamer (0.967 coverage). Grouping and
  emission are different cognitive steps — don't fuse them.
- NEXT (G4b): stage-1 = proven behave-alike grouping dreamer (chunk+merge,
  union-find overlaps, majority-type verification); stage-2 = dreamer
  states each family-pair outcome FROM THE LOG (engine-verified, Voyager
  rule); mechanical atomic-QA emission (formatting isn't intelligence);
  read hygiene (regex family extraction, first-sentence truncation).

## G4b (staged dreamer, fresh grouping): 0.333 — my re-implemented dream
loop regressed (2 passes + lossy LLM merge -> 2 groups, coverage 0.29).
The proven run_mini dreamer accumulated raw chunk-dreams PLUS merge
output and asked for many guesses. Lesson: don't reimplement a proven
organ; call it.

## G4c (consume proven artifact, naive group parse): 0.41 — extraction
lost the structure. Union-find over noisy behave-alike lines chained a
17-name blob; majority-type filter then killed almost everything
(coverage 0.25). But focused-evidence pair dreams verified 3/3 — that
organ works.

## G4d design: VERIFIED-CLAIM GRAPH (running)
- The artifact's real payload is hundreds of PAIRWISE executable claims
  ("These ruin the mixture: quinune and druane, ..."). Engine-verify each
  (Voyager rule); verified RUIN pairs are same-family edges (same-type ->
  ruin is a world law); connected components = families exactly; inert
  family = >=3 verified-nothing partners and no ruin edge.
- Dreamer proposes, environment disposes, graph clustering is mechanical
  post-processing, names coined per component. Purity + coverage printed.

## G4e (daydreaming loop): DREAMER SOLVED, reads 90%, composition leak
- Re-dreaming on ungrouped ingredients: coverage 0.542 -> 0.917 in ONE
  round; 4 families, purity 1.0 each; 10/10 pair-rules verified (32 lines).
- Read diagnostic: memberships 21/24, rules 7/10. End-to-end 0.308 was a
  NARROW failure: the two PRODUCT rules are exactly the corrupted reads
  ("not a good idea", "bitter and worthless"), and acc_product keys on
  those two family pairs -> 0.0. Also raw adapter prose was passed into
  the composition prompt, misleading the clean base.
- G4f (running): rule lines upweighted x3 in corpus; thinker NORMALIZES
  rule reads to canonical phrases before composing memory.

## G4g: symmetrized rules + product-edge inference -> coverage 1.000,
purity 1.0 x4, product 1.0, ruin 1.0 — but nothing 0.0: the thinker's
normalizer checked the keyword "product" BEFORE "nothing", so the
adapter's correct read "nothing happens. they do not form a product."
was normalized to "they make a product". The memory was perfect; my
normalizer inverted it. (Negation blindness in keyword matching.)

## G4h: L0 CLOSED — real dreamer reaches the oracle ceiling
- Fix: normalize on FIRST CLAUSE, priority nothing > ruin > product.
- END-TO-END: kind_bal 0.949 (product 1.0, nothing 0.846, ruin 1.0),
  coverage 1.000, 10/10 rules — EQUAL to G2f's oracle-statement ceiling
  (0.949). Experience -> real dreamer -> weights -> reads -> behavior,
  no oracle anywhere in the write path.
- The verified pipeline: chunked behave-alike dreams -> executable
  pair-claims -> engine verification (Voyager rule) -> ruin-edge
  components -> DAYDREAMING rounds on uncovered items -> product-edge
  membership inference -> coined family names -> atomic QA emission
  (memberships x8, rules x24 exposure) -> rank-64 lr 2e-4 25-epoch LoRA
  -> atomic resolved reads (canonical order, first-clause normalized)
  -> clean base composes.
- Ceiling attribution ledger, G4->G4h: wrong abstraction (0.282), organ
  reimplementation (0.333), lossy parsing (0.41), coverage gap (0.256),
  rule under-exposure (0.513), read order + bare-PRODUCT parse (0.667),
  normalizer negation bug (-> 0.949). Every point named and fixed.

## G4i: REPLICATION across worlds (self-contained pipeline, fresh dreams)
- seed 1: kind_bal 0.804 (product 0.882, nothing 0.882, ruin 0.647)
- seed 2: kind_bal 0.872 (product 0.923, nothing 0.923, ruin 0.769)
- seed 0 (G4h): 0.949. Mean 0.875 across 3 worlds vs 0.33 balanced prior.
- Both replication seeds: coverage 0.958 (23/24), purity 1.0 across ALL
  families, daydreaming again the workhorse (0.50->0.96 in one round).
- Known residual, explains the ruin dips: one true type arrives as TWO
  disconnected components (e.g. fenov(3)+morrun(2)), so its same-type
  pairs read as cross-family. The engine-verified rule between the split
  halves is RUIN — which by the world's law implies they are ONE family.
  QUEUED: family-merge inference (ruin-rule between families => merge),
  a second-order dream. Expected to recover most of the remaining gap.

## G4j (merge via dreamed rules only): merge NEVER FIRED — evidence gap
- Seeds 1/2 still 5 families. The split halves (fenov(3)+morrun(2);
  corem(4)+nymira(2)) have NO witnessed combos between them in the life,
  and my pair-dream stage drops family pairs with zero retrieved
  evidence — so the ruin rule that would trigger the merge never gets
  dreamed. seed1 0.804 (unchanged), seed2 0.718 (vs 0.872 in G4i — same
  corpus shape; treat as run-to-run training variance, ~±0.08, since
  train_lora has no fixed shuffle seed).
- LESSON: second-order inference needs a path to evidence the first
  order never produced. The agent can MAKE evidence: act in the world.

## G4k: EXPERIMENT-RESOLUTION closes the gap — 3-world line 0.949/0.882/0.923
- For family pairs with no witnessed evidence, the agent runs ONE
  experiment (a world action, not an oracle read): combine representative
  members, observe, use the outcome as the rule. Both seeds:
  "[g4k] EXPERIMENT the fenov-family x the morrun-family -> ruin" =>
  "[g4k] MERGED f3 into f2" — the verified ruin between families implies
  same-family (world law), merge fires, 4 families restored.
- seed1: kind_bal 0.882 (product 0.824, nothing 0.941, ruin 0.882)
- seed2: kind_bal 0.923 (product 0.923, nothing 0.846, ruin 1.0)
- With seed0's 0.949 (G4h): mean 0.918 across 3 worlds, prior 0.33.
- This is the full loop Rohin described: daydream -> notice a gap ->
  act to fill it -> verify -> consolidate. Curiosity as a memory organ.

## G4k variance (n=3 full-pipeline reps per seed, fresh dreams each rep)
- seed1: 0.882 / 0.784 / 0.882  (mean 0.849, sd ~0.057)
- seed2: 0.923 / 0.923 / 0.769  (mean 0.872, sd ~0.089)
- STRUCTURE IS STABLE, TRANSPORT IS NOISY: every rep found the same
  families, fired the same experiment->merge, coverage 0.958, 10/10
  rules — all variance lives in LoRA training/reads, concentrated in
  acc_product (0.529-0.923). Next lever if we need tighter numbers:
  fixed training shuffle seed, or 2x rule exposure.
- 3-world headline with error bars: 0.949 (s0) / 0.849±0.06 (s1) /
  0.872±0.09 (s2); grand mean ~0.88 vs 0.33 prior.

## G5 (vividness x exposure, 24-fact load): COMPLETE — saturation regime
- nonce    8/24/64/200 touches -> 0.417 / 1.00 / 1.00 / 1.00
- vivid                        -> 0.250 / 1.00 / 1.00 / 1.00
- conflict                     -> 0.458 / 0.917 / 1.00 / 1.00
- At 24-fact load, EVERY skin saturates by ~24 touches — storage cost is
  LOAD-DEPENDENT (the 200-touch recipe was measured on ~450-line corpora).
  No skin separation detectable at saturation; conflict marginally slower
  (0.917@24). The discriminating regime is higher load: G5b (96 facts,
  conflict = color-word contradicts family) queued on GH200.

## G5b (96 facts/skin): storage is CHEAP and PRIOR-INDIFFERENT
- nonce    8/24/64/200 -> 0.500 / 1.00 / 1.00 / 1.00
- vivid                -> 0.312 / 1.00 / 1.00 / 1.00
- conflict             -> 0.333 / 1.00 / 1.00 / 1.00
- Even PRIOR-CONFLICTING bindings ("the crimson fox belongs to the
  azure-family") store perfectly at 24 touches under 96-fact load.
  Priors neither help nor hurt PURE STORAGE of atomic QA facts.
- IMPLICATION 1: the ~200-touch requirement measured in the G-series
  came from corpus HETEROGENEITY (mixed line forms, rules-vs-membership
  interference), not raw fact count. Exposure cost is format-mixture-
  driven. (Queued: mixed-format storage grid to locate the wall.)
- IMPLICATION 2 (sharpens the vividness thesis): if prior scaffolding
  matters, it is NOT at the storage layer — it must show up at the
  DREAMING/INDUCTION layer (priors helping the dreamer propose the right
  connections, Rohin's original "hallucinate properly within the
  container" intuition). Vividness experiments should target dream
  quality, not adapter storage. This is a cleaner claim for the paper.

## G4j seed0 (harvested late): 0.718, coverage 0.875 — the no-experiment
arm on seed 0 (vs 0.949 with G4h's full-coverage dreams). Confirms the
experiment-resolution stage is what protects coverage when dream
evidence has gaps.
