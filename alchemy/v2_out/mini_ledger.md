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

## SEMANTIC WORLD first LM contact: C0/C1a/C1b x 3 skins x 3 seeds + C2@s0
(floors: D0-D2 0.167, D3 0.333; one-word answer protocol, no CoT)
- C0 (full 69-obs lifetime in context): D0 0.67-1.0, D1 0.0-0.42 (often
  BELOW floor), D2 0.08-0.33, D3 0.0-0.5. The LM cannot induce the
  structure in-context even with the whole lifetime visible — the
  instrument's context-break holds against the strongest context arm.
- C1a (unresolved oracle leaves): D1/D2 0.33-0.42, D3 0.0-0.42. THE L0
  RULEBOOK WALL RECURS: the clean base cannot execute
  ADD_POSITION_AND_ROTATION_MOD_3_THEN_INDEX as an in-context program.
  (Pre-registered D2 trigger technically tripped — but see protocol
  confound below before redesign.)
- C1b (resolved D3): D3 jumps to 0.417-0.833. FIRST PRIOR-SCAFFOLDING
  EFFECT: resolved-D3 aligned mean ~0.69 (0.833/0.833/0.417) vs neutral
  ~0.50 vs conflicting ~0.53 — pigment union is prior knowledge in the
  aligned skin. Vividness matters exactly where G5b predicted: at the
  reasoning/dream layer, not storage.
- C2 (oracle corpus -> rank64 LoRA -> atomic reads -> clean base), s0:
  D0 0.92-1.0 (witnessed transport works), D1/D2/D3 ~= C1a levels.
  PARAMETRIC TRANSPORT IS NOT THE BOTTLENECK; composition is.
- PROTOCOL CONFOUND: goal questions demand "answer with exactly one
  color word" — suppresses reasoning (our burned-once eval trap).
  Think-then-FINAL rerun launched before any redesign conclusion.

## SEMANTIC WORLD, CoT protocol (think-then-FINAL), 3 skins x 3 seeds
- C1a_cot (UNRESOLVED leaves + CoT): D1 mean ~0.75, D2 mean ~0.72
  (vs ~0.35 one-word protocol) — THE D2 REDESIGN TRIGGER IS CLEARED;
  the composition wall was answer-suppression, the L0 eval trap again.
  D2 now sits in the L0 apply-resolved band (0.77-0.91).
- PRIOR SCAFFOLDING ACTS ON REASONING, NOT STORAGE: neutral (nonce)
  skin lags aligned/conflicting by ~20 pts on D1/D2 CoT (~0.55 vs
  ~0.80) with identical latent structure — real words track through a
  reasoning chain better than nonce tokens, EVEN when color words are
  deranged (conflicting ~= aligned). Complements G5b (storage is
  prior-indifferent). The vividness thesis is now precise.
- D3 IS THE TRUE WALL, and free-form CoT makes it WORSE: resolved-D3
  no-CoT hit 0.833 aligned; with CoT drops to ~0.35 — overthinking a
  one-hop prior lookup (pigment union; the additive-vs-pigment
  ambiguity Codex flagged). Next: c1c pairwise-blend-as-lookup protocol
  (running) + C2 under CoT compose (running).

## SEMANTIC WORLD c1c (pairwise-blend protocol) + C2-CoT + read diagnosis
- c1c (resolved + blend-two-at-a-time-as-lookup): D1 0.67-1.0, D2
  0.58-1.0 (aligned/conflicting ~0.9+, neutral ~0.65). D3 mean ~0.42
  (above 0.33 floor, not solved). The context read/composition protocol
  is essentially SOLVED for D0-D2; D3 needs chained-union reads.
- C2 under CoT COLLAPSED to floor (D1/D2 0.08-0.42) — worse than
  C2 one-word. Read diagnosis (lands_c2_diag): per-goal facts (position,
  rotation, palette) read back PERFECTLY from the adapter; the ONE
  corrupted read is the constant composite-procedure line
  (ADD_POSITION_AND_ROTATION_MOD_3... regenerates as prose at 600
  touches — answer FORM, not exposure; matches G5c relation-lag).
  Under CoT the poisoned procedure read derails the whole compose.
- FIX (architectural, thinker-side): RECOGNITION READS — the claim
  grammar defines a finite legal answer space per leaf kind; the thinker
  scores candidates under the adapter (argmax logprob) instead of
  generating. Reads become recognition, not generation. C2r running
  (reuses C2 adapters; candidate sets incl. distractors for constant
  leaves so the adapter must still discriminate).

## C2r: TRANSPORT PROVEN AT SEMANTIC-WORLD SCALE (the lands G2f moment)
- Recognition reads: fidelity 228/228 (100%) on ALL skins — argmax
  candidate scoring under the adapter fully repairs the read channel
  (incl. the composite procedure line and 20-candidate meta-parents).
- End-to-end through weights (rank-64 adapter, clean-base pairwise
  compose): aligned D1 0.833 D2 0.917 | neutral D1 0.75 D2 0.917 |
  conflicting D1 0.917 D2 1.0. Matches/exceeds the context ceiling
  (c1a_cot D2 ~0.72). D0 0.75-1.0 (slight pairwise-protocol overthink
  on lookups — protocol should be depth-adaptive).
- D3 still 0.167-0.25 in BOTH context and weights => cleanly a THINKER
  problem, not transport: parent colors are themselves D1/D2-grade
  inferences; one-shot compose can't recurse. Next: chained thinker
  (compute each parent via the D2 pipeline, then union).
- Milestone: the five-rule stack + recognition reads carries a
  6-land/3-role/2-palette/meta-land world through a LoRA at the
  context-oracle ceiling. C3 (real dreamer claims) is now the frontier.

## Chained-D3 (per-parent sub-compose then union): NO LIFT
- c2rc D3: aligned 0.167, conflicting 0.083, neutral 0.333 (D1/D2
  unchanged at 0.75-1.0). Free-form sub-generation loses the thread;
  D3 remains the open composition problem. Next candidate: fully
  mechanical thinker (recognition reads + thinker-computed arithmetic,
  clean base answers) — defensible: the thinker is an agent by design.

## C3 (real dreamer, raw prompts): informative failure -> C3b
- 303 proposed -> 9 verified, ALL trivial witnessed cells; zero verified
  equiv/relation/meta. Root cause (from verifier source): entailment
  runs a FactorSolver over ONLY the cited observations — a claim
  verifies only if the citations form a CONNECTED evidence subgraph.
  The dreamer cited 1-2 lines; everything died "unsupported".
- C3b: THE DREAMER USES THE THINKER (Rohin's morning point, verbatim):
  dreamer proposes claims off a mechanically tabulated experience view;
  a mechanical CITATION ASSEMBLER (BFS over the animal-land evidence
  graph) attaches the connecting evidence path; the verifier still
  solely gates truth; NO verifier reasons fed back into content
  (anti rejection-sampling). CPU test: ground-truth equiv claims verify
  through assembled paths. The honest question is now isolated:
  does the LLM propose the right abstractions?

## C3c emitter PROVEN by component oracle: gauge fit 1.000
- Oracle-dreamer test (correct equiv+cell+meta claims through the real
  assembler/verifier): the mechanical emitter recovers the ENTIRE
  coordinate system — 3 position classes, 6/6 land rotations, both
  palette orders — at fit 1.000 and emits the full C2-form corpus (71
  lines). Two bugs found on the way: (a) my gauge searched only palette
  ROTATIONS; the canonical secondary order is a REFLECTION of the
  alphabetical sort — arrangements must include both cyclic orders;
  (b) position-label permutations must be searched jointly (S3).
- Ground-truth check: color == palette[(role + rotation) mod 3] fits
  66/66 witnessed source cells — the law and canonical orders are as
  spec'd; every earlier failure was in MY model of the gauge.
- With the emitter proven, C3 reduces to exactly one question: does the
  LLM dreamer propose the right ANIMAL_EQUIV pairs + META parents?
  (Same-color-in-same-land heuristic now taught in the prompt.)
  Live C3c running.

## C3 CLOSED FOR THE NIGHT: real dreamer through weights, fully attributed
- Live dreamer: 6 verified equivs + 69 episodic cells + 1 land relation
  -> gauge fit 1.000 -> 63-line corpus -> rank-64 LoRA -> recognition
  reads (palette candidates must span all 6 gauge arrangements — eval
  bug found+fixed) -> clean-base compose:
  D0 0.75 | D1 0.500 | D2 0.500 | D3 0.0  (floors 0.167/0.333)
- 0.50 == the positioned-coverage ceiling exactly (dreamer connected
  9/15 animals => 6/12 eval animals positioned). The C2->C3 gap
  (0.92 -> 0.50) is now a PURE dreamer-coverage number; D3=0 is the
  missing meta-rule claim. Nothing unattributed remains in the ladder:
  C0 0.08 (in-context induction, by design) -> C1a 0.72 (protocol)
  -> C2 0.92 (transport proven) -> C3 0.50 (dreamer coverage).
- Dreamer capability is the measured frontier. Levers, in order:
  (1) deeper daydream rounds w/ explicit per-land color-match scans,
  (2) C5 reachout for genuinely missing evidence, (3) dreamer model
  scale (7B misses instructed scans), (4) meta-rule targeted dreaming.

## C3 ROUND 2 — REAL DREAMER REACHES THE ORACLE TRANSPORT CEILING (D2)
- Deeper daydreaming (6 rounds, explicit per-land color-match scan):
  verified equivs 6 -> 15; classes [5,4,5,1] = 14/15 animals positioned;
  gauge fit 1.000; 68-line corpus; read-plan coverage 201/228.
- END-TO-END THROUGH WEIGHTS: D0 0.75 | D1 0.667 | **D2 0.917** | D3 0.083
  — D2 EQUALS the oracle-corpus C2 ceiling (0.917). Experience -> real
  dreamer -> verified claims -> gauge-pinned corpus -> LoRA ->
  recognition reads -> clean-base composition, at the transport ceiling,
  on the prior-anchored world.
- The coverage->accuracy law, measured: equiv coverage 9/15 -> D2 0.50;
  14/15 -> D2 0.917. Dreamer coverage prices downstream capability
  almost linearly.
- Remaining, attributed: D3 0.083 (dreamer never proposes META_RULE —
  needs meta-targeted dreaming; then the union-composition protocol),
  D1 0.667 (residual coverage + protocol), D0 0.75 (pairwise-protocol
  overthink on lookups — make the thinker depth-adaptive).

## C3 SKIN FAN-OUT — the vividness thesis measured at the dream layer
Identical latent world (seed 0), identical machinery, only words differ:
- aligned:     equivs 15 -> 14/15 positioned | D1 0.75  D2 0.917 D3 0.0
- conflicting: equivs 11 -> 11/15 positioned | D1 0.75  D2 0.75  D3 0.167
- neutral:     equivs 13 -> 13/15 positioned | D1 0.583 D2 0.667 D3 0.083
(gauge fit 1.000 on all three; verification strictness identical)
- THE DISSOCIATION, complete: priors scaffold the DREAMER's connection-
  proposing (aligned finds most, nonce/deranged find less) and the
  composer's reasoning (earlier: -20pts nonce in CoT), while STORAGE is
  prior-indifferent (G5b: conflicting bindings store at 24 touches).
  Priors matter where intelligence happens, not where memory sits.
- D3 still open everywhere: no META_RULE claim has verified yet even
  with meta-targeted daydreams (7B doesn't land the parent-set blend
  hypothesis). Levers: dreamer model scale, reachout (C5), or richer
  meta evidence framing. This is tomorrow's first target.

## C3s DESIGN — the verifier leaves the loop (Rohin ruling, 2026-08-26)
- RULING: in-loop exact verification is "verifier cheating" — the
  FactorSolver is a hand-coded solution to this game's algebra, neither
  scalable nor learnable. The 0.917 C3 result is hereby relabeled the
  PERFECT-CHECKER CEILING (kept as a condition). Prompt scaffolding is
  allowed ("cheat a bit on the prompts, not on the verifier").
- C3s (running): one dream batch, verifier-free ->
  * NOGATE arm: every grammar-parsed claim becomes memory;
  * SELFCHECK arm: per-claim reflection pass (retrieve own evidence
    rows, model verdicts SUPPORTED/CONTRADICTED/UNRESOLVED); only
    SUPPORTED claims stored; false self-approved memories STAY and
    their downstream cost is measured;
  * DREAM DRIFT round: re-dream over the agent's OWN accepted claims
    aimed at higher-order connections (the meta rule), generically
    framed ("is this situation's outcome built from other situations'
    outcomes combined?");
  * FactorSolver scores every proposal OFFLINE (raw precision,
    self-check precision/recall) — feedback never reaches the dreamer;
  * both corpora -> LoRA -> recognition reads -> clean-base compose.
- Report: raw proposal precision, self-check verdict quality, false-
  memory rate in weights, D0-D3 per arm vs the 0.917 ceiling.
- Epistemic-state memory (provisional/supported/contradicted with
  reconsolidation) is the architecture target; v1 stores SUPPORTED only.

## C3s DECOMPOSITION (aligned s0) — self-check works; Blendyland died at the PARSER
Pipeline: 21 raw dream texts -> 100 grammar-parsed claims -> self-check
-> 41 accepted. Confusion matrix (verdict x offline truth):
  SUPPORTED  34T/7F  (precision 0.829)   | raw precision 0.61
  CONTRADICTED 11T/22F (mostly-right rejections)
  UNRESOLVED 13T/7F; recall of true claims 0.557 (conservative filter)
Per kind: cells 0.938 raw -> 1.00 accepted; equivs 0.40 raw -> 0.50
accepted (evidence view made cross-referencing hard — fixed with
side-by-side per-land alignment); land_relations 0.00 (dreamer cannot do
rotation-delta arithmetic; harmless — emitter v2 derives rotations from
cells+equivs and ignores relation claims).
- BLENDYLAND LOCATION: the dreamer DID propose
  "META_RULE | land=Blendyland | operator=PIGMENT_UNION |
   parents=Candyland, Mandyland, Dandyland" IN THE MAIN DREAM PASS —
  rejected by the grammar for SPACES AFTER COMMAS. Hypothesis formation
  is NOT the failure; emission formatting was. (Proposed parents also
  imperfect — true set is Candy/Dandy/Randy — so success@k measurement
  matters.) Fixes: tolerant syntactic normalization, top-3 ranked drift
  hypotheses (success@k), aligned equiv evidence. C3s v2 queued.
- Downstream: selfcheck arm D2 0.50 through weights (gauge 0.82) vs
  nogate gauge 0.35 (false memories wreck the coordinate system);
  perfect-gate ceiling 0.917. Labels per Codex: arms are perfect-gate /
  no-gate / self-check / self-check+targeted-drift; the mechanical
  episodic cell layer is DISCLOSED (this tests autonomous abstraction
  over a reliable episodic base, not autonomous extraction).

## FOUR-ARM LADDER v1 (aligned s0) — complete
| arm            | gauge | D0   | D1   | D2    | D3    |
| perfect-gate   | 1.000 | 0.75 | 0.75 | 0.917 | 0.0   |
| self-check     | 0.818 | 0.75 | 0.50 | 0.500 | 0.167 |
| no-gate        | 0.349 | 0.75 | 0.25 | 0.417 | 0.25  |
(floors D0-D2 0.167, D3 0.333; ceiling row = C3 round 2)
- Self-check beats no-gate most clearly on D1 (2x) and corpus integrity
  (gauge 0.82 vs 0.35); D2 gap modest at this coverage level — the
  recognition-read + compose path has some robustness to junk.
- The ceiling->self-check D2 gap (0.917 -> 0.50) decomposes into
  self-check's conservative recall (0.557) on true equivalences, i.e.
  COVERAGE again — same law as C3 rounds 1-2.
- C3s v2 (tolerant parser, aligned equiv evidence, top-3 drift) queued —
  expected to lift both coverage and the META_RULE survival.

## C3s v2 (tolerant parser + aligned equiv evidence): mixed — one fix, one regression
- META_RULE now survives: 4 emitted. success@4 = 0 for the exact parent
  set (all proposed Candy/Mandy/Dandy or a reorder; truth is
  Candy/Dandy/Randy). One FALSE meta (SUPPORTED by self-check) entered
  the corpus -> selfcheck2 D3 0.417: partially form-transfer/luck from a
  2/3-correct parent set. Hypothesis FAMILY is present at 7B; exact
  parent selection is not (matches Codex's correction: "the meta-rule
  operator form emerged in scratch, but the exact meta-rule did not").
- REGRESSION: the side-by-side equiv evidence view collapsed self-check
  recall — 40 equivs proposed, 1 accepted (false). Cause: most true
  pairs involve eval animals with NO shared land; the pairwise view
  shows "(not seen)" everywhere and the model rejects. Chain-entailed
  equivalences are invisible to a binary pairwise check. v1's full-row
  view accepted 6 (recall 0.557 overall).
- CONCLUSION: binary self-check has hit its ceiling. Next build is the
  epistemic-state loop (Codex design): SUPPORTED / PROVISIONAL /
  CONTRADICTED persist; UNRESOLVED becomes a re-dream queue with richer
  evidence, not a trash can; two-axis check (evidence x existing
  structure) with revision actions; consolidation weight from
  independent support, never repetition.

## C3e through weights + stream v1 — two lessons
- C3e (epistemic check): corpus improved (42 claims @0.833, gauge 0.867,
  8 connector promotions, drift parser fixed -> 12 proposals) but
  downstream UNCHANGED: D1 0.5 / D2 0.5 / D3 0.167. Lesson: WHICH
  animals get covered matters, not how many edges — the promotions
  didn't reach the uncovered eval animals. Coverage must be tracked
  per-entity, not per-claim.
- C3stream v1 (one-hop micro-dreams): nearly MUTE — 1 thought in 23
  episodes; the cautious "only if worth remembering" instruction made
  the 7B PASS everything. Finding: MICRO-DREAM PRODUCTION RATE is a
  first-class parameter (Rohin's "caring" dial) — too low reduces the
  system to pure episodic memory. Assertive-prompt + --reinforce +
  --sleep-grow arm queued (v2).

## STREAMING ARMS COMPLETE (aligned s0) — batch wins at toy lifetimes
| arm                        | thoughts | supported(prec) | D1   | D2    | D3    |
| batch epistemic (C3e)      | 104 prop | 42 (0.833)      | 0.50 | 0.500 | 0.167 |
| stream shy (v1)            | 1        | 1 (1.0)         | 0.25 | 0.333 | 0.333 |
| stream assertive+reinforce | 29       | 7 (0.571)       | 0.25 | 0.250 | 0.083 |
- Assertive streaming produced 29x more thoughts than shy but LOWER
  precision (0.571 vs batch 0.833) and NO depth>1 nodes — PARENTS never
  cited prior thoughts, so chains didn't form; per-episode views (one
  episode + 12 recency-cut retrieved memories) rarely contain the
  cross-land pairs equivalences need. Sleep-growth added nodes but not
  depth.
- HONEST FRAME: at 23 episodes / 69 observations the full lifetime fits
  one batch dream trivially — streaming CANNOT beat batch here and
  shouldn't be expected to. Streaming is the SCALING form of dreaming:
  its value condition is lifetime >> context window. Next streaming test
  belongs on a LONG-lifetime world (the "lifetime length" scaling axis),
  with entity-keyed (not recency-cut) retrieval and explicit
  thought-parent citation training in the prompt.
- Keep: the epistemic-state machinery, reinforcement rule, and sleep
  phases are validated mechanics; the micro-dream production/precision
  trade (shy 1.0@1 vs assertive 0.571@29) is the caring-dial measured.

## SUBSTRATE TRIO (same self-checked dream corpus, aligned s0)
- dump-all-in-context:      D0 0.833 D1 0.167 D2 0.083 D3 0.25  (floor!)
- LoRA + recognition reads: D0 0.75  D1 0.50  D2 0.50  D3 0.167
- retrieved-context (RAG):  running
- The in-context collapse is the L0 RULEBOOK-SELECTION WALL on our own
  dreamed memories: the model cannot select the right 4 lines from 65.
  Weights win via targeted resolution (recognition reads), not capacity.
  Claim shape: "memory's value is resolution, not storage."

## SUBSTRATE TRIO COMPLETE + protocol-isolation arm launched
- retrieved-context (entity-keyed RAG, ~28 lines): D0 1.0, D1 0.083,
  D2 0.083, D3 0.333 — AT FLOOR on composition, same as dump-all.
  Retrieval does not fix the selection wall.
- Rohin's framing, now empirical: "this isn't retrieval memory but a
  COMPLEX memory that includes retrieval among other systems" — naive
  retrieval memory is at floor; memory-as-SYSTEM (targeted resolution +
  epistemic curation + composition protocol, with retrieval inside)
  is what works (weights+recognition 0.50, perfect-gate 0.917).
- Final isolation arm running (--resolve): context + resolved reads
  (answer each atomic question FROM retrieved lines, then compose).
  If it recovers ~0.5 => the RESOLUTION PROTOCOL is the effect and
  substrate is secondary at this scale; if not => weights do real work.
  Either way the claim sharpens.

## D3 RELABELED: UNDERSPECIFIED (Codex audit, 500/500 seeds)
- Blendyland's role->color signature EQUALS some ordinary land in every
  seed: "copy land_X" and "pigment-union of X,Y,Z" fit all observations
  equally. Parent identifiability held only CONDITIONAL on knowing the
  operator (the solver assumes PIGMENT_UNION). Joint operator+parents
  discovery was never evidence-decidable.
- SECOND SHORTCUT (Codex follow-up): v0 observes one Blendyland anchor
  for EACH of the three animal roles. Once role equivalence is learned,
  every held-out D3 cell can copy the same-role target anchor without
  learning an operator or parents. Fixing signature collision alone
  would not have repaired D3.
- CONSEQUENCES: (a) all D3 numbers to date are relabeled "underspecified
  meta-induction diagnostic" — NOT model failure; the 7B proposing
  different parents was rational; (b) D3 scale/prompt searches PAUSED;
  (c) D0-D2 results unaffected (0.917 transport stands); (d) Rohin's
  instinct ("need more blend outcomes / better semantics") preceded the
  audit — v0.2 is now implemented on `semantic-world-v02`: 12
  independent target cases, queried role withheld, weighted-pigment
  outcomes outside source/demo families, variable parent sets (2-5),
  neutral-vocabulary grounding, target cases shuffled across names, and
  joint operator+parent identifiability passing 1000/1000 seeds.
- Substrate-arm caveat adopted: report all three read interfaces
  (prompt->direct; prompt->recognition->composer; LoRA->recognition->
  composer) + prompt-memory token count (65 lines is a small-memory
  ceiling; LoRA's claim is memory >> window).

## SUBSTRATE x PROTOCOL 2x2 COMPLETE — the protocol IS the memory intelligence
Same self-checked dream corpus (1086 memory tokens), aligned s0, D2:
|                     | direct answer | recognition reads -> compose |
| context             | 0.083         | 0.500                        |
| LoRA (weights)      | 0.167         | 0.500                        |
(context + generative resolved reads: 0.333 — recognition > generation)
- CONTEXT+RECOGNITION EQUALS LORA+RECOGNITION at small memory. The read
  protocol (targeted recognition resolution -> clean compose) is the
  dominant observed effect in this cell; the substrate is interchangeable
  while memory fits the window. Paper claim, sharpened: "the resolution protocol is the memory
  system's intelligence; parametric consolidation is the substrate that
  carries it beyond the context window" — LoRA's value condition is the
  same as streaming's: memory >> window (and persistence after the
  window is gone). Report mem-token counts everywhere.
- Mounted-LoRA direct D0 is 0.50 versus 0.75 after recognition reads and
  adapter unmount: the read-only adapter hygiene ablation is now complete.
- Also ctxrec D3 0.417 (best D3 yet; underspecified caveat applies).

## D2 LOCK-AND-REPLICATE (verifier-free self-check arm, through weights)
aligned s0 0.50 | s1 0.50 | s2 0.25 | neutral s0 0.333 | conflicting s0 0.583
- Above the 0.167 floor in 5/5 world-skin combos; mean ~0.43 vs ceiling
  0.917. The verifier-free signal replicates above floor, but is not yet
  robust enough to lock: accepted structural-equivalence precision varies
  sharply, and a few false edges contaminate whole latent classes. Overall
  self-check precision is cell-dominated and must be replaced by per-kind
  precision/recall + contamination blast radius. Also, C3e's first check
  currently passes `structure=(none yet)`; the intended evidence+accepted-
  LTM self-check is not implemented until claims are checked in waves.

## SEMANTIC WORLD V0.2 DEPTH CEILING — verifier-free branch/revisit works
- Repaired D3 remains jointly identifiable at 1000/1000 seeds; 1000 unique
  public fingerprints, 12 independent withheld-role target cases, floor .083.
- Clean aligned-s0 gates: full lifetime direct 0/12; one generic scaffold
  0/12; oracle-resolved leaves 9/12. The residual oracle errors are arithmetic
  or final label reads, not missing memory.
- Monolithic recurrence fails even with scale: 7B answer/parents 0/0; 32B
  .083/0. Long traces collapse roles, confuse role-identification lands with
  target parents, and then reinforce the malformed state.
- Successful controller (no exact verifier in loop): dream operator from public
  demonstrations; enumerate all 57 public source subsets (sizes 2-6); ask one
  atomic LLM proof leaf for each of the target's two observed roles; mechanically
  AND the two self-verdicts; revisit matching branch thoughts into a PARENTS
  memory; recognize query role atomically; retrieve only that role row at the
  dreamed parents; model writes an arithmetic component ledger; exact public
  workshop lookup converts the recipe to a label. FactorSolver/hidden truth is
  used only after commitment for scoring. Every prompt and branch is saved.
- SCALE under identical atomic controller, aligned s0:
  * 7B: true-branch recall .500, exact parents .500, 32 false MATCH branches,
    raw final .417.
  * 32B: true-branch recall 1.000, exact parents 1.000, 5 false MATCH branches,
    raw final .750.
  Scale helps only after proof state/read structure is legible.
- 32B development s0: exact parents 12/12; frozen ledger artifact 10/12
  (.833); post-hoc parser diagnostic 12/12 (NOT pooled).
- UNTOUCHED 32B replications under the frozen protocol:
  * s1: parents 12/12, roles 12/12, final 12/12; zero false matches.
  * s2: parents 11/12, roles 12/12, final 11/12; the one rejected true branch
    produces the one downstream miss. Thirty false matches concentrate in
    three targets, but revisit recovers the true parent set in two.
  * aggregate: parents/final 23/24 = .958, roles 24/24 = 1.000.
- CLAIM BOUNDARY: this is a frozen prompt/controller ceiling, not learned or
  efficient dreaming and not yet a LoRA result. Exhaustive 114 proof calls per
  target expose what computation works and generate trajectories for later
  amortization. Next: proposal-first top-k success@k/query-budget compression,
  stage ablations, more seeds/skins, then matched context-vs-LoRA transport.
- Full protocol and caveats: `research_notes/39_v02_branch_depth_results.md`.

## V0.2 ACCEPTED + MERGED (Fable); 32B top-k compression QUEUED
- Acceptance green: 1000-seed joint-identifiability sweep, v0 suite
  intact, compile clean. Merged to main.
- Standing results from the branch (Codex-run, 32B on the node):
  one-pass 0/12; oracle-resolved composer 9/12; EXHAUSTIVE verifier-free
  branch/revisit controller 23/24 exact parents + 23/24 answers on
  untouched aligned seeds 1-2 — the necessary computation EXISTS,
  labeled as a prompt/controller ceiling (57 subsets x 2 leaves each).
- NOW RUNNING (queued behind T1 thinker): proposal-first top-k
  compression on untouched seed 3, k=12, Qwen2.5-32B — success@1/2/4/8/12,
  revisit accuracy, exact token accounting. No prompt tuning on seed 3
  (dev = seed 0 only). Then: finish + recipe-recheck stages.
- Skin fan-out BLOCKED intentionally until model-generated RECIPE_GAUGE
  memory exists (the aligned-only source-cell reader would leak the
  gauge on neutral/conflicting).

## T1 ADAPTIVE THINKER (aligned s0, C3e memory): routing works, self-assessment doesn't
- D0 1.0 (vs 0.75 fixed-protocol) | D1 0.333 D2 0.333 D3 0.167
- ADAPTIVE COMPUTE CURVE measured: reads/goal 1.8 (D0) -> 4.7 (D1) ->
  4.3 (D2) -> 8.5 (D3); stages A7/B39/C2; 4 thought-nodes written.
- 7B SELF-ASSESSMENT OVERCONFIDENT: KNOW on 46/48 at 0.478 accuracy —
  the caring trigger under-fires; escalation rarely reaches the chain
  stage; ranges unused. Calibration is the thinker's weak organ (matches
  Rohin's "prompter not ready"). D1/D2 dip vs fixed protocol = stage-B
  prompt drift (protocol sensitivity again) — reconcile stage-B with the
  proven pairwise prompt verbatim next iteration.

## 32B TOP-K COMPRESSION (v0.2, untouched seed 3): THE AUTONOMY GAP, MEASURED
- proposal success@k FLAT at 0.25 for k=1,2,4,8,12 (3/12 targets);
  self-select 0.25; revisit 0.25; 180 proof leaves vs the exhaustive
  controller's 1368 (7.6x cheaper).
- Read: the exhaustive controller (all 57 subsets) hits 23/24; asked to
  PROPOSE a 12-candidate frontier, 32B reaches only 25% — and extra
  candidates beyond k=1 add NOTHING (frontier lacks diversity; correct
  sets aren't in its generative hypothesis space without enumeration).
  The gap between guided and autonomous hypothesis generation is now THE
  measured frontier ("can the model decide where to compute").
- No prompt tuning done on seed 3 (rule held). Failure-mode inspection
  on dev seed 0 is the permitted next step.

## TEMPORAL DREAMING, first pass (7B, aligned s0, recurrent arm)
- 32 micro-cycles -> 21 nodes, 0/12 targets, max depth 1 (no node ever
  cited another node), ~1.7k generated words total (outputs very short).
- 7B free-form micro-dreams neither chain nor discover v0.2 parents —
  consistent with the top-k result one level down. Independent + long
  arms running; probe requeued (PYTHONPATH launch bug, not a science
  result).

## TEMPORAL CADENCE TABLE COMPLETE (7B, aligned s0): uniform null, characterized
- recurrent 21 nodes / independent 32 / long 60 — ALL 0/12 parents,
  ALL depth 1. Node inspection: every dream correctly tags the OPERATOR
  FAMILY ("confluence/blending effect") for every target, but NEVER
  proposes candidate parent sets; the agenda mechanism goes unused (no
  open questions self-left). Same shape as the 32B top-k result one
  level up: pattern-class recognition is cheap, structural hypothesis
  GENERATION is the scarce operation. Scale row (32B recurrent, matched
  budget) launched on H100.

## 32B SCALE ROW (temporal recurrent): the near-miss regime
- 24 nodes, 0/12 exact, depth 1 — but 32B PROPOSES parent sets where 7B
  proposed none (3 attempts, all near-misses with real pigment
  reasoning: Fusionland proposed {Candy,Dandy,Randy} vs truth
  {Candy,Dandy} — one extra land from conflating per-animal
  attributions into supersets).
- THE AUTONOMY SPECTRUM, complete for v0.2 (aligned s0/untouched seeds):
  exhaustive verify (32B):        23/24
  top-k propose+verify (32B):      3/12 (flat in k)
  free recurrent dreams (32B):     0/12 (3 near-miss proposals)
  free recurrent dreams (7B):      0/12 (0 proposals)
- Reading: scale moves the failure from NO hypotheses to WRONG-BY-ONE
  hypotheses; what free dreaming lacks is the self-scheduled VERIFY step
  (predict both observed outcomes per candidate, prune) that the
  structured controller enforces. The next rung is not more scale — it
  is teaching/prompting the dream loop to verify its own proposals
  (which C3s self-check already does for simple claims).

## TOP-K AUDITS (Codex's four): headline SURVIVES, sharpened
- Cardinality: solved targets have parent sizes {2,3,5} (1/3 each at
  2/3/5, 0/3 at 4) — NOT a two-parent-demo extrapolation artifact.
- Frontier: valid proposals/target 0-12 (mean 7.5; one target got ZERO
  parseable candidates). When truth IS proposed: rank #1, verdict MATCH,
  3/3 — and false_match_count = 0 on all 12 targets. RANKING AND
  VERIFICATION ARE CLEAN; generation is the entire loss. Corrected
  claim: "recognizes a valid connection when localized; cannot reliably
  GENERATE it from global state."
- Cost: 205 queries, 275k in / 78k out tokens (exhaustive ref: 1368
  leaves) — full-token comparison to be added from notes/39.
- Same-world verification control (oracle-labeled true branch, 24
  leaves, seed 3): QUEUED next GPU slot.
- Temporal next: 32B recurrent + MANDATORY memory-parent citation
  interface (generic; makes recurrence usable) — launched.

## 32B + CITATION INTERFACE: DEPTH EMERGES (temporal row 5)
- max_depth over cycles: 1@1, 2@8, 3@16, 5@32 — the mandatory
  memory-parent citation interface activates recurrence; dreams now
  compound on prior dreams (vs flat depth 1 in all earlier arms).
  Targets still 0/12 (1 false set): depth grows but chains don't yet
  converge on true parents — the self-scheduled VERIFY step remains the
  missing organ. Mechanistic claim for the paper: recurrent depth is
  unlockable with a generic interface; correctness needs verification
  inside the dream loop.
- NOTE: all exhaustive-controller run artifacts (branch_records etc.)
  are TRAINING CURRICULUM for the loop adapter — never delete.

## TWO-TRACK GATE, FIRST PASS COMPLETE
- TRACK A (thinker question generation): plan coverage 0.44; own-plan
  accuracy D0 1.0 / D1-D3 0.25. The asking-the-right-questions organ is
  weak, quantified. Transcript at v2_out/probe_transcript_aligned_s0.txt
  for Rohin's manual pass.
- TRACK B (memory character, C3e adapter): exact 1.0 | paraphrase 1.0 |
  analogy 1.0 | reversed 0.33 | partial-cue 0.0. The store is an
  ASSOCIATIVE PATTERN, not a database: meaning-robust (paraphrase),
  relationally accessible (analogy), but DIRECTIONAL (reversal curse on
  our own memories) and FORMAT-ANCHORED (free-continuation cues fail).
  Validates recognition reads as the reader (in-format, in-direction by
  construction) and answers Rohin's similarity-waves question with data.
