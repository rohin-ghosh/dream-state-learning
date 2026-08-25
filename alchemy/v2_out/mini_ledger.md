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
