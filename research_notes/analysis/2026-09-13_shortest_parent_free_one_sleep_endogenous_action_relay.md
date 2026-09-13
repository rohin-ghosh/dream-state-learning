# Shortest parent-free one-SLEEP endogenous action relay after Q0 DEV

**Date:** 2026-09-13 UTC  
**Status:** bounded design memo only. It changes no builder source, test, model,
adapter, job, GPU, benchmark result, or claim.

## Decision

If and only if the first valid Q0 development root ends in
`SUPERVISED_ONE_ROOT_XOR_BINDING_PASS`, freeze that exact pairwise writer
recipe and run one permanently excluded development relay on a fresh opaque
root.

Do **not** translate Q0 into M-core's `MemoryRow|MISS` interface. Q0 qualifies
native first-action branches (`ACT: -mem2reg` versus `ACT: -gvn`), whereas
candidate-free M-core requires a goal-blind model to generate an entire local
memory row without candidates. They are different carrier problems.

The immediate relay therefore stays end-to-end on the native action surface:

```text
child ACT -> public outcome -> child-authored two-mode action record
          -> copy/verify + fixed lexical replay -> one LoRA SLEEP
          -> sterile reset -> held first ACT
```

This is one shortest currently specified test of the project's missing
endogenous action-write edge. M-core
remains separately blocked on a future complete-row generative carrier gate;
neither a Q0 pass nor this relay may be used as that gate.

## 1. One fresh root and the source experience

Use the same finite surface shape as Q0, but no Q0 identifier, example,
adapter, response, error, or fitted weight:

- eight fresh opaque keys, two visible modes with identical one-token native
  shape, and the two native legal actions `-mem2reg` and `-gvn`;
- a presealed balanced map
  `correct(key, mode) = orientation(key) XOR mode`, with four keys of each
  orientation;
- four presealed key pairs, each joining opposite orientations; and
- source objects, eight training renderings, four held renderings, locality
  objects, a complete wrong-root key/alias/mode roster, and copy items
  generated disjointly before the first child call.

The source child is the pinned clean Qwen2.5-7B-Instruct base used by Q0, with
no Q0 adapter and no parent. Each key is an independent three-turn block:

1. On a new object in mode 0, the child emits exactly one legal `ACT:` and the
   world returns `SUCCESS` or `FAILURE`.
2. On a different object in mode 1, it again commits one `ACT:` before the
   public outcome.
3. With those two immutable execution receipts visible, the child emits
   `DREAM: NULL` or one complete record:

```text
DREAM: STORE
KEY: <visible key>
WHEN: <mode 0>  ACT: <child-authored supported future action>  EVIDENCE: <execution id>
WHEN: <mode 1>  ACT: <child-authored supported future action>  EVIDENCE: <execution id>
```

The public rule states only that exactly one of the two actions succeeds in
each presented state. Name the fields distinctly in every schema and receipt:
`EXECUTED_ACT` is what the child committed before the outcome, while
`SUPPORTED_FUTURE_ACT` is what the child later writes in the record. On
`SUCCESS`, the supported future action equals the executed action; on
`FAILURE`, it equals the other legal action. The harness never states the
resulting mapping. Explicit output grammar is allowed; the recent clarified
protocol control showed that grammar is an interface requirement, not
semantic help.

There are exactly **16 source action calls plus 8 record calls = 24 child
calls**. No retry, repaired action, filled record, extra exploration, parent,
teacher text, or outcome-selected regeneration is allowed.

## 2. The child-authored boundary

The immutable child-generation receipt is the semantic authorship boundary.
The admission checker may only:

- parse the closed grammar;
- join each citation to an earlier action and later public outcome in that
  same key block;
- verify that both modes occur once, both `SUPPORTED_FUTURE_ACT` strings are
  exact child record bytes, and each follows from its separately named
  `EXECUTED_ACT` plus public outcome and the public two-action law;
  and
- copy the record byte-for-byte or emit `NO_ADMISSION`.

It may not infer or insert an action, replace a citation, repair syntax,
paraphrase a belief, consult the hidden map, ask the child again, or select a
nicer record. The scientific scorer reconstructs world truth independently
from the pre-child root manifest; it never treats corpus agreement as truth.

For this first kill test, fitting opens only if all **8/8** records are
supported and admitted and all **16/16** child-written conditional action
lines are correct. Anything less is the reportable terminal
`ENDOGENOUS_FORMATION_SHORTAGE`; no writer fit is run. This strict boundary
avoids selecting a convenient subset or changing Q0's balanced optimizer
unit. It says the parent-free child failed to prepare this small complete
lesson, not that LoRA cannot learn it.

The root and its generation seed are fixed prospectively. A shortage is
terminal for this version: do not sample a replacement root. Consequently an
8/8 result is an existential excluded-DEV observation, not a formation-rate or
root-robustness estimate.

## 3. SLEEP dream compile and write

SLEEP receives only the eight admitted child records and their public
receipts. Raw source conversations, hidden map, scores, held items, future
answers, Q0 material, and audit-only state are absent from training inputs.

The compile step is intentionally minimal and mechanical:

1. For every child-written `(key, mode, ACT)` line, render the situation under
   the same eight predeclared lexical-view definitions selected by Q0, with
   only the fresh root's aliases substituted.
2. Copy the exact `SUPPORTED_FUTURE_ACT` branch authored in the child's record
   as the target. It need not equal the earlier executed action after a
   failure. The training prefix ends at the natural common assistant prefix
   `ACT: -`; no later target, suffix, padding, LF, or EOS enters the input.
3. Interleave distinct keys in the four-prompt opposite-orientation quartets
   presealed before the child acted.
4. Replay the 32-quartet order four times: 128 optimizer updates, 512 row
   presentations, and 32 presentations per `(key, mode)` relation.

This fixed-view replay is the bounded SLEEP dream. It changes expression and
exposure, not semantics. It does not establish a learned dreamer, learned
selection policy, connection building, or compression.

Both fitted arms inherit Q0's exact selected/frozen `P` recipe: frozen base,
alpha 16, dropout `.05`, seven projection families, AdamW at `3e-5`, identical
initial LoRA tensor/RNG receipts, pairwise common-prefix loss, first-quartet
FP64 directional canary, and uninterrupted updates. A Q0 `V` or unary
diagnostic never substitutes for this recipe.

## 4. Exact arms

All states fork from byte-identical clean base state:

| state | persistent write | purpose |
|---|---|---|
| `E_AUTH` | two-mode bindings exactly authored from lived outcomes | complete endogenous path |
| `E_SWAP` | swap the two mode tokens in every compiled input while preserving every child target byte | equal-dose complementary redirection |
| `E_OFF` | no personal fit | no-write floor |
| `E_SHADOW` | compile and create the same `E_AUTH` candidate, but do not mount it after reset | temporary-state/leak cut |

`E_AUTH` and `E_SWAP` are the only two fits. Before fitting, require each mode
alias to encode as exactly one token and prove that AUTH/SWAP have identical
per-row native length, target branch position, attention shape, quartet
collation, target-token multiset/order, action marginal, key exposure,
positions, update count, initialization, optimizer state, and dropout RNG
stream. Only the one matched mode-token identity may differ. The swap then
enforces `map_SWAP(key,m) = map_AUTH(key,1-m)`. It is a laboratory control,
not lived experience.

`E_SHADOW` reuses the already trained `E_AUTH` candidate but leaves it
unmounted; it does not require a third fit. Its model-visible request
projection and raw generation bytes must equal `E_OFF` under deterministic
item seeds. Audit traces are expected to differ because SHADOW records the
unmounted candidate and arm/process metadata separately. This tests whether
records, compiled rows, or process state leak into behavior when the weight
write is cut.

## 5. Sterile reset and later action readout

Preserve evidence in an audit-only namespace, but make it unreadable to every
evaluation process. For every state, start a fresh process with a fresh KV
cache and empty conversation/workspace. Mount only the pinned base and the
assigned adapter. No source transcript, record, corpus, ledger, retriever,
candidate action row, prior generation, fit label, score, or network channel
is visible. Reset again for every item, and show no feedback before the one
scored action.

Run the unchanged Q0-shaped panels on `E_OFF`, `E_AUTH`, and `E_SWAP`:

- 128 exact-rendering items (8 keys x 2 modes x 8 views);
- 64 held-rendering/new-object items (8 x 2 x 4);
- missing-mode 8, unsupported-mode 8, neighbor-ID 16, and wrong-root 64;
- eight native copy/interface items.

Run `E_SHADOW` on the 64 held items plus eight copy items. Score strict first
actions against the pre-child world map, never against the record. Also store
the two-action margins and absolute legal branch-token mass.

Before any fit, independently reconstruct all 296 prompts/state from the root
manifest and require exact denominators, disjoint prefix hashes, complete
wrong-root key/alias/mode material, Q0 legality/cell rosters, and byte-identical
AUTH/SWAP surfaces except for the registered mode-token bitmap.

## 6. Development pass and kill rules

This one root is an excluded development result, so it receives no population
confidence interval. It passes only as
`DEV_ENDOGENOUS_ONE_SLEEP_ACTION_RELAY_PASS` if all of the following hold:

1. Source/action chronology is complete, formation is 8/8 supported records,
   and every admitted semantic byte is child-authored.
2. Both first-quartet canaries pass. Each fit then completes exactly 128
   updates with finite losses, correct target counts, exact clean reload, and
   matching initialization/schedule receipts.
3. For **each** fitted map, Q0's gates hold unchanged: exact at least 116/128,
   at least 56/64 per action, validity at least 122/128; held at least 52/64,
   at least 24/32 per action, validity at least 61/64; no multiple actions;
   and the registered cell-coverage and signed-margin gates.
4. At least 112/128 exact and 48/64 held prompts are correct under both fitted
   adapters and flip to the complementary action. The held redirection score
   is at least `.40`:

   ```text
   B = .5 * [(BA(E_AUTH,AUTH)-BA(E_AUTH,SWAP))
           + (BA(E_SWAP,SWAP)-BA(E_SWAP,AUTH))]
   ```

5. `E_AUTH` improves held AUTH accuracy over `E_OFF` by at least `.10`, and
   `E_SWAP` improves held SWAP accuracy over the same OFF outputs by at least
   `.10`. Formatting alone cannot satisfy the complementary-map and per-action
   gates.
6. Q0's locality predicates hold separately for every fitted state: all four
   families meet the `.05` mean / `.10` itemwise probability bounds and their
   integer action-identity bounds; wrong-root complementary outputs are at
   most 3/64; native copy is 8/8.
7. `E_SHADOW` and `E_OFF` have identical model-visible request-projection
   hashes and raw held/copy outputs. Their audit traces remain distinct. Any
   model-visible difference is a reset/capability leak, not a model result.

Stop before fitting on prior exposure, malformed root balance, target-bearing
input, non-child target bytes, incomplete formation, hidden-map access by the
compiler, or unequal AUTH/SWAP tensors/work. Stop an arm after its first
canary miss. Preserve and label any nonfinite fit, wrong model/adapter,
incomplete denominator, stale cache, mutation, failed teardown, or state leak;
never retry or replace it based on outcome. A failure is localized as
formation, acquisition, held extraction, redirection, locality/interface, or
reset—not averaged into one score.

## 7. Isolation from Q0, birth, parenting, and confirmation

- Allocate and hash this fresh relay root before its first child output.
- Q0 DEV may select and freeze the writer recipe on root 1, but no Q0 target, output,
  adapter, root identifier, or error enters the relay.
- The relay is permanently `EXCLUDED_DEV`. Its artifacts, weights, prompts,
  errors, and outcomes may not tune Q0 repetitions, seed a clean birth or
  Level-2 child, update a parent, or count in a paper result.
- If it motivates an interface repair, version the repair and use a new
  excluded root. Only after the complete protocol freezes may newly generated
  opaque roots become confirmation units.
- Bind the prospective public model revision
  `Qwen/Qwen2.5-7B-Instruct@a09a35458c702b33eeacc393d103063234e8bc28`
  plus local model/tokenizer hashes.

This is the simple hygiene needed now; it does not require finishing the
deferred C11 guard package.

## 8. Exact cost ceiling

Maximum model work is:

- 24 source/record calls;
- 2 fits x 128 updates = **256 optimizer updates** and 1,024 natural-row
  training forwards;
- 3 x 296 = 888 short panel generations for OFF/AUTH/SWAP; and
- 72 shadow generations, for **984 total generation calls** including source.

Run serially on one A40 to avoid a device nuisance. The Q0 executor estimate
is 15--35 minutes for two fits; the extra 24 source and 72 shadow calls are
small relative to the common panels. Reserve at most **75 wall minutes = 1.25
A40-hours**, including model loads, audits, fit, all readouts, archive, and
verified release. Formation shortage stops after the 24 source calls and uses
zero fit time. No parent-service or second GPU is required.

## 9. What a pass would and would not prove

Q0 alone proves only **supplied writer carriage**: externally prepared target
branches can be installed selectively under its finite controls.

This relay adds the missing provenance edge. A pass shows, once, that a model
can act, observe the consequence, author the complete conditional action
lesson itself, have a nonsemantic compiler replay those bytes into the
Q0-selected LoRA write, and later change a held first action after every
temporary memory channel is removed. AUTH/SWAP redirection attributes the
behavior to the authored binding; OFF/SHADOW attributes persistence to the
weight write.

Under Rohin's vocabulary this is one bounded **learned** action relay. It is
not parenting, self-learning, a learned compiler, complete `MemoryRow|MISS`
generation, connected knowledge, traversal, expansion, multiple SLEEPs,
retention, lifetime improvement, compression, or superiority to strong text
memory. Those remain the subsequent M-core and L-core questions rather than
being smuggled into this small pass.

## Controlling artifacts

- `research_notes/analysis/2026-09-12_q0_pairwise_falsifier_implementation_closure_v2.md`
- `research_notes/analysis/2026-09-12_pairwise_binding_falsifier_adjudication.md`
- `research_notes/analysis/2026-09-13_q0_value_redteam.md`
- `research_notes/analysis/2026-09-12_minimal_decisive_h1_parent_dream_sleep_bridge_protocol.md`
- `research_notes/analysis/2026-09-12_candidate_free_two_sleep_zero_fit_closure_checklist.md`
- `research_notes/analysis/2026-09-12_h1_bridge_level0_adversarial_addendum.md`

Fresh independent red-team before commit required and this version resolves:
the executed-versus-supported-future-action distinction; one-token mode-shape
and dropout-work equality; a model-visible rather than audit-trace SHADOW
equality; and a complete wrong-root/locality material roster. The reviewer
confirmed the call/update arithmetic and Q0 threshold transcription.
