# Existing contextual two-hop bridge options — 2026-09-14

Read-only code/evidence inspection; this memo is the only edited file. No project
imports, tests, tokenizer/model calls, fits, native execution or commits. Main
chooses the next task after the material control; no outcome from that control
is assumed here.

## Bottom line

**There is an existing contextual two-STEP action loop, but no drop-in two-hop
experienced-EVENT continuation.** Stage2A already demonstrates some complete
two-step routes on a different trained controller. Its public rows explicitly
label relevance to the final goal; that is narrower than inferring a path from
unlabelled experienced edges. PCHAIN2 already separates successful supplied-text
composition from failed free parametric composition. Neither closes the current
EVENT learner's path-selection gap, and neither warrants another weights-hop fit.

The current EVENT controller has at most three actor calls/two reads and **one
committed ROUTE**, then returns even on a wrong outcome:
`organism_v6/experienced_event_read_route.py:60`, `:136`. Its `public_task(fact)`
sets GOAL to that fact's immediate outcome (`:42`). More fundamentally,
`organism_v6/experienced_event_microloop.py:65` constructs two disconnected
source-node pairs; `_check_bank` at `:86` explicitly forbids any outcome being
a source node (`:101`). The existing A3 facts cannot simply be relabelled as a
two-hop graph while preserving their experience receipts.

## 1. Smallest existing action diagnostic: Stage2A contextual chains

Reusable entrypoints:

- `organism_v6/composition_birth_stage2a_held.py:634`: `build_chain_world(world,
  role_tokens)` returns the typed `ChainWorld`; `public_view(member)` at `:592`
  exposes the final-goal task, not the offline witness.
- `organism_v6/composition_birth_stage2a_rollout.py:78`: `run_chain(world, member,
  actor=..., count_context=..., counter_provenance=..., master=..., stage='D1')`.
  It keeps one conversation, exposes each actual STEP outcome as WORLD/CURRENT,
  and makes no oracle action or automatic READ. Up to29 actor calls are reserved
  per member; 256 generated tokens/call is an upper allowance, not a runtime
  estimate. `wire.Session.turn` in `composition_birth_stage2a.py:574` implements
  repeated STEP at `:640`; `rollout.py:145` appends the actual response.
- `organism_v6/composition_birth_stage2a_actor.py:92`: `ReadoutActor` accepts an
  already prepared model/tokenizer/device and returns the required
  `DecodeRequest -> Generation`; it does not initialize a new adapter.
- `organism_v6/composition_birth_stage2a_scoring.py:426`: `score_chain` preserves
  whole-chain checks, not just physical arrival. The full existing screen is
  `composition_birth_stage2a_screen_runtime.py:138`; the native usage pattern
  is `gpu/astra_stage2a_outcome_distill.py:349` (280 reservations, not a mandatory
  cost for a newly declared small chain-only diagnostic).

**Visibility boundary:** the initial GOAL stays final throughout. The harness
does not send a new intermediate GOAL after STEP. However ROUTE rows carry
`AT/FOR/QUERY`, and EVENT rows carry `AT/FOR/DID/GOT/RECOVER`; the public protocol
explicitly tells the actor to match FOR to GOAL (`composition_birth_stage2a.py:98`,
`:420`). Thus a first edge leading to a hub is already labelled as relevant to
the ultimate goal. This tests contextual lookup, action, outcome checking and
continuation with supplied relevance, not independently discovering that hub.
The solver `_chain_witness` (`composition_birth_stage2a_held.py:599`) is
evaluator-only: never use it to provide actor actions or intermediate goals.

**Parent compatibility / smallest seam:** the callback actor can wrap the
current already-loaded EVENT PEFT model without changing its weights. That is
not an existing current-parent launch binding: the EVENT identifiers/commands
are `E_/N_/P_`, READ EVENT/ROUTE, whereas Stage2A uses its allocated M2A namespace,
READ INDEX/RELATION, STEP/THINK/STOP and passive supplied service text. Failure
would conflate interface/skill transfer with planning. A small parent-bound,
zero-fit diagnostic entry would need custody/count/source bindings, not another
trainer or scorer. It must be named a supplied-context controller transfer
diagnostic, not own-memory two-hop learning. No such entry was implemented here.

Do not use Stage2A initialization to mount the current child implicitly:
`gpu/astra_stage2a_native_models.py:45` requires an unwrapped CPU base and creates
a fresh adapter. Its full checkpoint format (`composition_birth_stage2a_checkpoint.py:43`)
also includes optimizer/RNG/cursor/binding state, unlike an EVENT PEFT adapter
directory. `ReadoutActor` reuse avoids claiming those artifacts are interchangeable.

## 2. Closest learner-preserving path: EVENT callbacks, with explicit missing seams

Keep the existing EVENT reader, same adapter and exact receipt-grounded writing
format. `gpu/astra_experienced_event_microloop.py:114` provides `Engine`; its
readout loader at `:147` accepts local rank8/alpha16/dropout0.05 PEFT adapters
with the existing target modules, and `generate(messages)` at `:168` supplies
the current callback response. No model variant or loader framework is needed.
But the old CLI `gpu/astra_experienced_event_read_route.py:17` hard-pins an early
adapter hash and collection schema: it is not the current-child entrypoint.

Current parent-binding examples are `gpu/astra_fresh_reader_cycle.py:21`
(`load_parent`, fixed to terminal repaired SFT_SELECTED) and `:185` (AFTER loads
the specified training output and checks its state). They are patterns to reuse,
not permission to pass a later child through the earlier fixed parent contract.
Main must select the actual terminal parent and bind adapter files/live state,
base hash and collection/audit lineage explicitly; no adapter blending, swapping
between hops or loading a PCHAIN/Stage2A-trained controller into the child.

Three concrete gaps preclude a one-line bridge:

1. **Connected experienced source material:** the present bank validator forbids
   connected edges. A prospective topology/collection binding must generate
   actual receipts for linked nodes; do not change old GOT values or synthesize
   connecting facts from a held answer. The existing EVENT serialization is
   reusable, but the old four-fact bank contract is not that topology.
2. **Continuing action context:** `run_episode` ends at first ROUTE. A bounded
   continuation must keep the ultimate GOAL, expose the real reached node and
   only the permitted outgoing choices, and retain the conversation. Calling
   `public_task` on a handpicked second fact supplies its target. Calling two
   ordinary episodes with the correct intermediate GOAL demonstrates two
   harness-decomposed one-hop actions, not learned path selection.
3. **Audit/replay and retention binding:**
   `organism_v6/experienced_event_fresh_reader_audit.py:75` reconstructs the
   single-ROUTE controller, and `:81` requires four routes/32 collection rows.
   Its all-captured-read/source-valid-pointer policy is reusable, not its
   multi-step validation unchanged. `gpu/astra_fresh_reader_cycle.py:121` pins
   twelve old facts; the next parent's old-fact inventory must be bound rather
   than silently reusing that denominator. The existing writer's memory-count
   options are80/96 (`gpu/astra_selected_reader_repair_train.py:33`), not an
   arbitrary new-history interface.

This is the closest path to the requested eventual learning experiment, but
it is a small **new protocol/adapter contract**, not an already supported run.
No new fitting dose, automatic success filtering or new checkpoint authority
is proposed. Material collection, action, audit and later writing must reference
the same child's captured events; an audit source table must not leak into the
action prompt unless explicitly labelled as the supplied-context control.

## 3. Existing PCHAIN2 contextual ceiling: useful evidence, not an action bridge

`gpu/astra_pchain2_free_material.py:55` builds the exact contextual query:
AVAILABLE RELATIONS contains A->B and B->C, followed by “apply NEXT exactly
twice”; the model emits two MEMORY lines and ANSWER. This supplies both edges,
not a harness-issued intermediate action target, but has no environment STEP
or outcome feedback. `prepare_free_evaluation` at `:65` and the existing reducer
already support supplied/empty context and free-recall distinctions.

`gpu/astra_pchain2_native.py:376` has compatible rank8 readout configuration,
but its training branch at `:396` explicitly requires a fresh D1 adapter;
its manifests bind NEXT symbols/targets, not the experienced-EVENT parent or
collection. Do not call it a current-child continuation or restart it to
rediscover the already measured weights-only gap.

## Decisive existing evidence (not rerun)

| ID | Existing result and limit | Exact local source |
| --- | --- | --- |
| SEQ-211 | Query-JUNCTION recalls32/32 isolated atoms, free two-hop trace0/16 and direct0/16; supplied-fact trace16/16, empty0/16. Mixed query-JUNCTION/copy-LOCAL report, DERANGED unobserved; not a matched query factorial or current EVENT child. | `research_notes/analysis/2026-09-14_pchain_query_only_result.md`; `gpu_artifacts_local/astra_pchain2_query_only_reduce_20260914_attempt1/QUERY_MIXED_REDUCTION.json` (raw JSONL paths in `inputs`, retained under `evidence/`). |
| SEQ-203 | D2 strict chains0/8; one real two-STEP goal arrival fails immediate-STOP criterion. Preserve failure, not a reason to weaken scoring. | `research_notes/analysis/2026-09-14_d2_chain_failure_localization.md`; `gpu_artifacts_local/astra_stage2a_d2_preservation_20260914_attempt1/evidence/astra_stage2a_d2_20260914_attempt1/run/ATOM_LOCAL/`. |
| SEQ-220 | A4 outcome controller strict4/8 chains, five physical arrivals, CHECK4/4, CONTINUE0/4, canaries4/16. One normal two-step success (chain5), three recovery successes (3,6,7); copy mixture preserves those routes, canaries9/16. Existing contextual two-step execution, not reliable or unscaffolded path learning. | `research_notes/analysis/2026-09-14_a4_outcome_sft_first_result.md`, `2026-09-14_a4_copy_replay_comparison.md`; `gpu_artifacts_local/astra_a4_outcome_sft_first_result_20260914/evidence/astra_outcome_a4_20260914_attempt1/run/RESULT.json`, `FITTED/event-0245.json`; derived `ANALYSIS.json` in the capture root. |
| SEQ-245 | Both same-parent forks route4/4 after1/4, new recall4/4 after0/4, retain12/12; one terminal ROUTE per episode, not two hops. | `research_notes/analysis/2026-09-14_fresh_reader_cycle_first_result.md`; `gpu_artifacts_local/astra_fresh_reader_cycle_terminal_20260914_attempt2/extracted/SELECTED/after/RESULT.json` and sibling `new_task/OWN_PARAMETRIC_EPISODE_01.json` (other episodes retained). |

## Recommendation to Main: smallest decisive next bounded task

Do **not** commission another PCHAIN fit or rerun the full Stage2A screen just
to establish that two-step contextual execution exists. If Main wants only a
current-child procedural transfer diagnostic, option1 is the smallest existing
runtime, with the goal-relevance scaffold explicitly named.

For the actual EVENT-learning gap, the next bounded task should instead bind
option2's connected-world visibility and continuation/audit contract, source-only
first, with a fixed parent and no fit/launch in that task. Require final GOAL
only, no labelled “correct next edge” or witness actions, and a decision point
where the child must choose between source-supported paths. Do not call a
singleton offered route or an externally specified intermediate goal planning.
Then Main can choose a finite no-fit readout before any learning branch:
same tasks/current actor with parametric reader, reader-disabled and exact
supplied-record control; supplied text is external context, not parametric
recall. Bind prompt bytes, call/token/deadline caps and repeat policy before
execution; retain invalid routes, absent transitions and every actual read.
Report per-hop commitments, final-goal arrival and the declared full trajectory
criterion separately, plus original recall/retention/audit controls. A later
selected/uniform write must start from the same parent and keep failure-inclusive
source-valid choices; success would not by itself show superior selection,
autonomous scheduling, H1/H2 or independent-family transfer.

Inspection check: selected JSON headers/criteria and source definitions were
read without running their code. Existing analysis results are attributed above;
no completed tests or scientific reducers were repeated. No runtime estimate or
new scientific outcome is inferred. The six writing files were not touched.
