# PCFL-D0-EXACT-V2 world, controller, and split contract

Status: proposed exact D0 design bytes. This document and its referenced JSON files authorize nothing by themselves. They contain no model call, model weights, provider path, LoRA operation, GPU operation, scientific split opening, or scientific claim.

The controlling artifacts are:

- `world_manifest.json`: finite world, actions, source program, targets, twins, collision contract, and structural invalidation.
- `controller_manifest.json`: candidate catalog, generic reader, exact posterior and quotient, four CPU controllers, reachability proof, aggregation, and gates.
- `split_seed_manifest.json`: protocol hash, SHA-256 counter RNG, namespaces, split slots, ordered candidate streams, and no-replacement firewall.
- `golden/controller_cases.json`: exact rational, degenerate, collision, generic-reader, quantile, and gate fixtures.

If prose here conflicts with one of those JSON artifacts, the JSON artifact controls and the conflict blocks implementation until a newly reviewed successor repairs it.

## Frozen PCFL-13 world

Each sector has public binary traits `T0..T3` with public values `ZERO/ONE`; `T3` is immutable. The six opaque `PREPARATION_FAMILY` handles `P0000000..P0000005` are a permutation of `SET_T0_0`, `SET_T0_1`, `SET_T1_0`, `SET_T1_1`, `SET_T2_0`, and `SET_T2_1`. The four opaque `SITE_FAMILY` handles `S0000000..S0000003` are a permutation of `F0..F3`, whose fixed public semantics are the four note-47 predicates. The three opaque `ROUTE_FAMILY` handles `R0000000..R0000002` are a permutation of `G0..G2`, whose fixed public semantics are `T0=ONE`, `T1=ZERO`, and `T2=ONE`. The NodeRef kind distinguishes a family handle from an identically shaped fresh instance handle. Lexicographic permutation ranks give exactly `720*24*6=103,680` nonexception worlds.

World rank is `((preparation_rank*24)+site_rank)*6+route_rank`. Rank zero uses all three identity permutations. The two A4 exception families are mechanically absent from D0 source, targets, atoms, controllers, and scoring.

The fixed dagger involution maps `SET_T0_0<->SET_T1_0`, `SET_T0_1<->SET_T1_1`, leaves both `SET_T2_*` transforms, maps `F0<->F3`, leaves `F1,F2`, and maps `G0<->G2`, leaving `G1`. Public family-handle positions, skins, instance handles, target proposals, reset traits, order, and budgets never change. Applying dagger twice must reproduce the original world exactly.

Exactly one of `SURVEY`, `ASSAY`, `PREPARE`, `TRAVERSE`, `INTERVENE`, or `COMMIT` occurs at a step. Every parsed action costs one of six world actions. Route failure and intervention rejection are irreversible. Malformed, illegal, multi-action, post-terminal, or cap-exhausted behavior has value zero.

## Source program and structural targets

The source policy is exactly 32 complete repetitions of a fixed 49-record supercycle in this order: 24 balanced preparation trials, nine route separating trials, then 16 complete site-panel interventions. Each twin therefore executes the same 1,568 fresh-reset, one-action source episodes. Outcomes and token lengths never select, stop, skip, reorder, extend, or replace an action. Across the complete deck both twins have exactly 768 `PREPARED`, 224 `INTERVENTION_ACCEPTED`, 288 site-rejection terminal failures, 96 `TRAVERSE_PASSED`, and 192 route-rejection terminal failures. The final event must cross `2C=16,384` on both twins or the candidate is structurally rejected. There is no padding event.

At checkpoint `K`, old roots have `0<token_end<K/2`, third-block roots have `K/2<=token_end<3K/4`, and recent roots have `3K/4<=token_end<=K`. Thus at `2C` every old decisive root ends strictly before token 8,192 and lies outside the 8,192-token chronological non-memory surface. A2 needs distinct old preparation and recent site roots. A3 also needs a distinct third-block route root. If the exact rendered source prefix lacks one, the candidate is structurally rejected.

Each checkpoint has eight paired A2 and eight paired A3 targets. A2 exposes an ordered three-preparation kit; this yields the stated `6P3*4=480` target-local Bayes ceiling. Exactly one single preparation succeeds on each side, the twin answers differ, zero preparation and the other singles fail, and the minimal path is `PREPARE, INTERVENE, COMMIT`.

A3 exposes an ordered four-preparation kit and a route family revealed only by `SURVEY`; this yields `6P4*4*3=4,320` quotient states. Exactly one unordered pair succeeds on each side, neither singleton and no other pair works, both correct-pair application orders agree, and twin pairs are disjoint. The fixed public ontology plus state must entail one route-enabling transform and then a distinct site-enabling transform; reverse generic lookup of each transform must return a family present in the kit. This is structural reachability, never a controller-performance filter. The minimal path is `SURVEY`, two `PREPARE`s, `TRAVERSE`, `INTERVENE`, `COMMIT`.

Target proposals are shared by twins and accepted in increasing proposal-counter order using only structural rules. Every rejection and its complete rejection-code set is logged. A target counter or pair counter reaching 100,000 invalidates the protocol; it does not relax a rule or promote another seed.

## Complete twin collision

Before the first read or action, every accepted A2/A3 pair must collide on the complete public goal, initial state, assembled prompt, empty workspace, every budget, visible snapshot alias, catalog hash and incident-order identifier, reader serialization contract, error class, timing class, and process-visible allowlist. Each canonical byte string and their length-prefixed aggregate receives a left/right SHA-256 equality receipt.

Latent assignments, authentic eligible-atom membership, hidden snapshot hashes, scorer truth, and registered correct actions remain hidden and may differ. Correct A2 actions must differ; correct A3 pairs must be disjoint. A one-byte mismatch in any visible surface rejects the target before a controller runs.

## Accepted-visible-item Bayes-N

Bayes-N starts from exact mass `1/103680` on every legal nonexception world and `1/2` on each unobserved twin side. Its item likelihood is the exact rational probability that the frozen target-construction kernel emits the observed visible bytes as its first structurally accepted paired item. Proposal descriptors, prior accepted public tuples, target ordinal, side, handles, skins, and rejected proposals are marginalized.

Bayes-N is explicitly forbidden from conditioning on split, seed, world rank, twin side, target ordinal, other targets, proposal counter, rejection count, rejection codes, sampler rejection, generation timing, source life, eligible atoms, or any audit-only field. Thus two runs with identical accepted visible item bytes have exactly the same initial posterior even if their hidden rejection logs differ.

After a public action outcome, inconsistent hypotheses receive zero mass and the remainder is normalized using reduced arbitrary-precision rational arithmetic. Zero initial visible mass invalidates the generator. A zero-mass observed successor invalidates the replay. Neither case installs a uniform fallback, epsilon, approximate mass, or Monte Carlo repair.

The A2 quotient key is the three visible preparation assignments plus target site predicate. The A3 key is the four visible preparation assignments, site predicate, and surveyed-route requirement. Quotient mass is the sum of full-world posterior mass. Full and quotient values, policies, posterior updates, terminal scores, and lexicographic ties must agree at every reachable state. A positive-mass class that is not an exact bisimulation invalidates the quotient.

Bayes-N enumerates every legal action under the six-action horizon. Q values and Bellman residuals are exact fractions. Ties use the manifest action-kind order and then unsigned canonical JCS action bytes. An empty nonterminal action set has value zero.

## Three distinct exact-memory questions

The controllers are deliberately not interchangeable:

1. `HW-SOLVE` receives hidden mappings and establishes only that the target is solvable under six actions.
2. `ATOM-CEILING` receives the complete source-derived eligible atom set simultaneously and establishes only that those atoms contain enough information.
3. `AUTH-GEN` receives source-derived eligible atoms only through the generic one-atom reader, four memory slots, four active path edges, at most four queries, 18 total resolver operations including actions, and six sequential world actions. Only this controller bears the bounded authentic source-memory usability interpretation.

The common catalog has exactly 61 target-blind candidates: 36 `PREPARATION_TRANSFORM`, 16 `SITE_PREDICATE`, and nine `ROUTE_REQUIREMENT` atoms; exactly 13 are true in a world. `atom_id=candidate_id` is SHA-256 over the NFC-before-JCS semantic `{object,relation,subject}` projection without LF; durable JSONL appends LF afterward. Catalog order is frozen before worlds and targets. The reader orders forward before reverse incidence, suppresses item-global repeats, and returns only one `FOUND` atom or `NOT_FOUND`. Errors fail the item. Clearing a workspace slot never makes an atom returnable again.

Public state supplies the target-to-reusable family bridge: site family, inventory preparation families, and the route family after survey. The sole derived anchor is `MODEL_DERIVED_TRANSFORM`: after a site or route read, the controller may select one of the six public `TRANSFORM_TEMPLATE` enums from the returned `PREDICATE_TEMPLATE`/`ROUTE_REQUIREMENT` plus public state, citing those exact slots. Runtime checks syntax and citations but neither computes nor corrects the selection; a wrong transform consumes budget. Offline trace credit checks the entailment. No typed relation, direction, target-derived alias, candidate score, or answer-bearing reader join exists.

A2 queries site, derives the unique accepting transform from its predicate and current traits, then reverse-queries that transform to obtain the authentic preparation family. Its total is two queries, two path updates, and three actions: seven resolver operations. A3 surveys, queries site and route, derives the route-enabling and then site-enabling transform, and reverse-queries those transforms to obtain the two authentic preparation families. Its total is four queries, four path updates, and six actions: fourteen resolver operations. The exhaustive gate checks these traces for every accepted target on both sides at all three checkpoints, including exact source roots, derived-anchor citations and entailment, slots, edges, action citations, and remaining budgets. `OPEN-GEN` is separate: it must precommit its transform anchors before seeing any read, so it guesses them. A typed or manually injected favorable trace cannot repair failure.

## RNG, splits, and no replacement

The RNG domain root is SHA-256 of the UTF-8 bytes `PCFL-D0-EXACT-V2\n`, equal to `284acaf0f2569e4d984fcd8f17828f1ec4be3ee14791df8b0fcfe12341a60af5`. All randomness is SHA-256 counter mode with length-prefixed namespaces and labels, big-endian counters and words, and rejection sampling for unbiased bounded integers. Golden derivations in `split_seed_manifest.json` bind byte order and domain separation.

Independent namespaces are `pair_candidate`, `world`, `skin`, `twin`, `source`, `target`, `rejection`, `order`, `controller`, `model_call`, `statistics`, and `adapter`. The last three are dormant where applicable; `model_call` and `adapter` cannot execute in D0. The twin namespace supplies audit canaries only; dagger, not randomness, constructs the twin.

Split slots are exactly eight DEV, 64 CPU, six CAL, 16 CONF, and 16 ordered RESERVE pairs. DEV and CPU are the only openable D0 streams. CAL, CONF, and RESERVE derivations are committed but dormant and non-openable: D0 may validate their identifiers and literal golden bytes but cannot instantiate stream keys, RNG blocks, worlds, source, targets, or logs.

For each pair slot, candidate counters are tried in increasing order. The first candidate satisfying every frozen structural rule is permanent. Bayes, exact-memory, shortcut, resource, test, later model, or scientific performance is not a candidate input. A failed CPU gate retains all 64 pair IDs and all zero-valued failures, then invalidates the whole generator version. Reserve streams are never available to repair performance.

## CPU gates and edge conventions

CPU scoring uses only checkpoint 16,384. Within each twin, average eight A2 targets and eight A3 targets separately, then average the two kinds equally; average the two twins for one independent pair value. Missing, crashed, malformed, capped, or indeterminate items are zero. Deterministic controllers are not duplicated into pseudo-replication.

Across the 64 uncurated CPU pairs:

- Bayes-N mean must be at most `7/20`.
- Bayes-N empirical p90 is the 58th one-indexed value after exact rational sorting and must be at most `9/20`.
- Every accepted item under `HW-SOLVE` and `ATOM-CEILING` must have value one.
- `AUTH-GEN`, aliased as `A_exact` in gate formulas, must have mean at least `17/20` and gain over Bayes-N at least `3/10`.
- Every registered shortcut must have mean at most `7/20`.
- Each bad assignment must lose at least `max(3/20,G_exact/2)` versus `AUTH-GEN`.
- A nonpositive exact gain fails; no half-gain ratio is defined.

Golden cases bind exact posterior normalization, hidden-rejection noninterference, quotient aggregation, zero-mass dispositions, Bellman ties, the 58th-value p90 convention, boundary pass/fail arithmetic, repeat/discard behavior, paired A2/A3 generic traces, byte-collision failure, and separation of the three memory estimands.

## Claim firewall

A green D0 says only that the deterministic CPU reference world, streams, schemas, controller arithmetic, collision checker, reachability checker, and gates conform to these bytes. It is not evidence that DREAM discovers an atom, THINK composes with a model, a LoRA retains action value, a GPU pipeline is safe, or a scientific assay succeeds.

PCFL-13 contains only thirteen reusable mappings. It is fixed-deck and cannot establish scaling, continued lifetime acquisition, developmental improvement, continual or online learning, recurrent-sleep superiority, A4 revision, memory-improved evidence acquisition, an action-experience flywheel, autonomous causal discovery, external validity, LoRA superiority or efficiency, fixed-resource equivalence, or a learned THINK/DREAM policy. Future eligible wording remains comparator-qualified, resource-ledger-qualified, and limited to “operationally supported PCFL relations under registered interventions.” Note 48's PCFL-Stream ladder is not imported into this D0 design.
