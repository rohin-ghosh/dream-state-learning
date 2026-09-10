# Fresh systems audit: v03r Paper-1 recurrence canary

**Status:** bounded, nonauthoritative engineering advisory.  It authorizes
nothing: no architecture change, implementation, model/provider/GPU call,
scientific run, or claim.  It does not amend the frozen Paper-1 goalposts or
the v2e contract.

## Bottom line

**Mostly yes, but not as one existing executable.**  About two thirds of the
canary's *control plane* is already composable: v03r supplies a paired,
goal-embargoed public life; `recurrent_text_organism.py` supplies the recurrent
phase barriers, one-step memory mutation, M0/M1 freezes, own/no/distractor
return allocation, fresh thinker reset, provenance, and deterministic write
views; `goal_conditioned_thinker.py` supplies a fail-closed typed reader and
adaptive operation machine; `lora_mem.py` supplies a deliberately small fresh
per-life LoRA installer/reader.

The missing pieces are precisely the model-facing joins and the final v03r
semantics.  Existing scientific adapters should not be wired together without
changes: their `V03RMechanicalSemanticAdmission` is an in-loop exact
route/effect verifier, and the only existing scientific thinker goal compiler
is a causal-join *probe* compiler, not the final counterfactual answer/action
compiler.  Reusing either as the headline condition would violate the frozen
no-exact-verifier and final-behavior boundaries.

Consequently this canary is plausible as a small staged composition project,
not a one-command experiment.  The first deliverable should be CPU-only
fixtures and artifact tests; the earliest model stage is text-only, and LoRA
comes only after that frozen text path works on both members of one DEV pair.

## Reusable pieces and their safe role

| Needed canary arrow | Existing composition | Safe reuse limit |
|---|---|---|
| paired public lifetime and final-goal embargo | `lands/v03r.py`; its tests establish identical passive twins, one differing public effect, local-window/edge-removal failure, pair scoring, and precheckpoint final-goal absence | Keep both twins as the scoring unit.  Do not expose `world`, `oracle()`, `reveal_final_goal(..., include_answer=True)`, latent bit, or scorer expectations to any model-facing object. |
| recurrent M0 -> THINK0 -> M1 schedule | `PublicLife`, `FrozenSchedule`, `_schedule_calls`, `_run_calls`, `_freeze_checkpoint_view`, `run_recurrent_text_experiment` | The stock fixture is 46 WAKE + 22 REACTIVATE + 16 target-blind sleep + 16 return sleeps per arm/life.  It provides strict fresh-state final THINK but does not itself make calls scientific. |
| target-blind local dream serialization | `scientific_dream_adapter.canonical_target_blind_request` | Its request bytes correctly exclude final goal, arm, donor, query key, checkpoint, and trigger routing metadata.  Keep this visibility boundary. |
| typed local proposal and provenance | `SemanticDecision`, `PremiseIdentity`, bounded memory checks, cyclic trace materialization | Existing decisions can represent local concepts/edges and derivation depth.  They lack a first-class model self-check/prediction/confidence artifact. |
| THINK0 request and non-evidentiary return coordinate | `goal_conditioned_thinker.ThinkerMachine`, `HardenedThinkerMachineAdapter`, `V03RPublicAgendaCompiler` | Reuse only for the operational causal-join probe; it deliberately has no final-goal vocabulary.  The `ScriptedRecurrencePolicy` is a ceiling/fixture, not adaptive evidence. |
| fresh final THINK1 state machine | `ThinkerMachine`, `HardenedThinkerMachineAdapter`, `ThinkerRequest(reset_id=...)` | The reset is real and the reader is auditable.  A new final-goal compiler, operation policy, and answer/action projection are still required. |
| deterministic memory write views | `DeterministicRealizationCompiler` / cyclic trace `realization_specs` and `touch_plans` | It is a good common view generator, but current checkpoints include both provisional and supported rows.  It does not export a byte-hashed common corpus. |
| per-life LoRA installation/read | `alchemy/lora_mem.py` | It can train and deterministically generate reads, but has no corpus manifest/hash, life-reset enforcement, query protocol, or transport/read-fidelity evaluator. |

## Exact missing interfaces

1. **Dream-provider bridge, not presently a `SemanticDreamerProtocol`.**
   `ScientificDreamAdapter.execute(request, scope, config)` returns a rich
   execution; the scheduler calls `dreamer.dream(request) -> SemanticDecision`.
   Add a thin bridge that derives one `ProviderCallScope` from the scheduler
   call position, invokes a fresh provider session, records the exact request,
   config, response, parser result, and returns `PASS` on strict rejection.
   The bridge must be run-local (no cross-life session/KV reuse) and must
   attach its immutable call artifact to the scheduler trace; current
   `_run_calls` records only a request and final decision.

2. **A target-blind model self-check schema/admission policy.**
   `parse_local_proposal` produces a proposal only.  The current admission
   class turns selected v03r concepts and `causal_join` edges into supported
   rows through exact structured route/effect matching.  That is useful CPU
   fixture infrastructure but forbidden cognitive-loop verification for the
   headline.  The canary instead needs a second, independently prompted model
   call over exactly the bounded proposal/premise view returning
   `SUPPORTED|CONTRADICTED|UNRESOLVED`, a bounded rationale, predicted visible
   record(s), and cited local handles.  Only `SUPPORTED` may set
   `mark_supported`; the other admitted proposals remain append-only
   provisional/contradicted (never silently deleted).  The model must not see
   a solver result, hidden counterfactual answer, final goal, or offline score.

3. **Self-check artifact retention and supported-corpus selector.**
   `SemanticDecision` only has `mark_supported`; `MemoryItemView` contains no
   confidence, prediction, or check record.  Add a sidecar keyed by
   `(call_hash, conclusion_semantic_hash)` and emit it in the final artifact,
   rather than widening the frozen semantic identity.  Add one deterministic
   corpus-export function that selects *only supported, non-superseded*
   semantic rows at M1, orders by semantic hash/form, expands the existing
   four write views, and emits a `corpus_sha256`, row hashes, and touch counts.
   Text and LoRA must consume this exact byte sequence; raw public episodes,
   THINK traces, final goal, and checker text are excluded.

4. **Final v03r goal compiler and answer/action projection.**
   `V03RPublicAgendaCompiler.compile()` intentionally returns `None` for the
   final goal, while `compile_goal()` always constructs a one-edge
   `causal_join` probe.  No current semantic vocabulary represents the
   remaining public role/source-calibration/workshop reasoning, no policy
   makes final-v03r typed operations, and no adapter projects a released
   thinker result to the v03r ratio/action.  This is the largest real gap.
   Build a final compiler from only `reveal_final_goal(skin)` plus the frozen
   M1 checkpoint, with a typed operation/read vocabulary for the public
   intermediate atoms.  Its scorer-side mapper may convert the returned public
   label to a ratio only after completion; it must be outside model-visible
   bytes.  Reuse `score_final_pairs` for private paired aggregation.

5. **Provider-backed adaptive thinker policy.**
   `HardenedThinkerMachineAdapter` accepts an `OperationPolicyProtocol`, but
   the supplied `ScriptedRecurrencePolicy` is explicitly a ceiling.  Add a
   provider-backed policy that receives only `ThinkerMachine.public_state()`,
   emits one strict JSON operation, uses a fresh session for each THINK0/THINK1
   invocation, and supplies actual tokenizer accounting.  The existing adapter
   already rejects malformed/invalid operations and forces a defer.

6. **Matched substrate readers plus life isolation.**
   Text can initially use the exact common rows with a deterministic typed
   reader.  `lora_mem.read` is unconstrained free generation; wrap it with the
   same typed query/cue protocol, exact read probes (canonical, reverse,
   paraphrase, partial cue), response parsing, and per-life adapter manifest.
   Reload a clean base and a newly trained adapter for every life/arm; never
   mount a twin or prior-life adapter.  The text and LoRA readers must expose
   identical item identities/provenance to THINK1.

## Risky reuse: do not mistake these for the desired canary

- **Mechanical admission is a verifier.**  `V03RMechanicalSemanticAdmission`
  reconstructs support from a route/effect connector.  It must remain an
  offline CPU oracle/fixture only; it cannot filter or promote headline
  dreamer output.
- **The gold dreamer already knows the desired local mechanism.**
  `V03RGoldSemanticDreamer` is valuable to prove schedule/trace plumbing, but
  its direct route/effect join is solution guidance and cannot be called a
  target-blind learned/self-checked dream.
- **The current "scientific" final thinker is not final behavior.**
  `V03RPublicAgendaCompiler` and `ScriptedRecurrencePolicy` solve/request the
  declared causal-join probe, then label themselves a recurrence-probe
  ceiling.  They do not answer the counterfactual goal.
- **Current text snapshots are an oracle reader.**
  `DeterministicTextSnapshotCompiler` hands every live row to the hardened
  reader.  It is appropriate for CPU contract tests, not evidence that text
  retrieval and LoRA retrieval are matched without an explicit common reader
  protocol.
- **`lora_mem.py` is a laboratory helper, not an experiment harness.**
  It does no split/life isolation, no corpus equality proof, no holdout read
  report, and its previous v02 runner trains on episodic rows in addition to
  dreamed statements.  Reusing that runner would break same-corpus attribution.
- **Do not inherit v2e's scale or scope.**  v2e is a proposal/closure contract
  with 514 shared DREAM calls plus up to 288 return-DREAM and 102 exploratory
  calls, and it intentionally forbids the final goal/LoRA/action.  Borrow its
  provider and artifact discipline only, not its experiment body.

## Ruthlessly small CPU-first boundary

Implement no benchmark change and no new model behavior in the first patch.
Limit the boundary to one aligned DEV collision pair and the already frozen
46-event v03r life.  Preserve the existing three return arms because their
matched budgets are the smallest credible attribution set:

```text
two collision twins, target hidden
  common per-twin prefix: 46 WAKE + 22 REACTIVATE + 16 target-blind SLEEP
  freeze M0; THINK0 emits zero/one typed REQUEST_DREAM
  per arm {NO_RETURN, OWN_RETURN, DISTRACTOR_RETURN}: 16 RETURN_SLEEP
  freeze supported-only M1 -> common-corpus manifest
  fresh THINK1 -> public final label/action -> offline paired score
```

CPU acceptance should use only deterministic scripted/pass/reject fake
providers and the existing gold fixtures.  It must prove: (a) no final marker
in all DREAM/M0/THINK0/M1 bytes; (b) model-check sidecars cannot affect premise
eligibility except through their declared status; (c) identical M1 export bytes
feed text and LoRA manifests; (d) each final thinker has a new reset/session
identifier; (e) twin/wrong-life corpus substitution changes only offline
diagnostic paths; (f) paired scorer expectations never enter artifacts; and
(g) masking the returned causal edge is an offline path-use test.  No GPU,
network, model download, or model inference belongs in this patch.

Only after those tests pass should a text-only provider canary be considered.
It should stop before LoRA unless OWN_RETURN beats both controls on M1 closure
and paired final behavior, with a correct depth-2 memory whose parent is an
earlier memory and with the required mask/twin ablation.  Only then install
one fresh MEMORY LoRA from the frozen, byte-identical supported corpus.

## Size and call-budget estimate

This is a bounded integration, but it is not a 30-line wrapper.

| Work item | New production LOC (estimate) | Existing code reused |
|---|---:|---|
| dream provider/session bridge + strict execution ledger | 70–110 | request serializer, provider boundary, scheduler |
| proposal-plus-self-check schema, parser, sidecar, admission | 110–160 | strict proposal parser and semantic decisions |
| supported-only common-corpus export + manifest | 60–90 | realization compiler / trace provenance |
| text and LoRA typed-reader wrappers + life manifests/read probes | 100–150 | `lora_mem`, hardened reader contracts |
| final v03r compiler, adaptive policy adapter, label/action projection | 170–260 | ThinkerMachine, hardened adapter, paired scorer |
| orchestration/tests (CPU only) | 220–350 | v03r and cyclic-contract tests |
| **Total** | **510–770 production+test LOC** | control-plane majority is composition |

At the existing smallest full scheduler budget, one collision pair has 168
prefix dream calls (2 × (46+22+16)) and 96 return dream calls
(3 arms × 2 twins × 16): **264 DREAM proposals**.  A separate model
self-check doubles that to **528 dream-side model calls**.  THINK0 is at most
24 operations (2 × 12); fresh THINK1 across three arms/two twins is at most
72 operations (6 × 12).  Thus text-only Stage 1 is bounded by **624 model
generations** (528 dream/check + 96 thinker), before retries; it needs no LoRA
training.  If checks are parsed in the same constrained generation as proposals
this falls to 360 calls, but that conflates proposal and independent
self-check, so it is not the recommended headline condition.

Stage 2 adds **six fresh LoRA trainings** if all three arms/two twins are
transported, plus up to 72 LoRA read generations under the same twelve-step
THINK1 budget.  For a ruthlessly small transport check, train only the two
OWN_RETURN twin adapters first: **two trainings plus at most 24 LoRA reads**;
the no/distractor text controls remain necessary for Stage 1 attribution.  The
actual GPU/token budget cannot be honestly estimated from the existing code:
`lora_mem.py` exposes rank/epochs/batch/max length but has no measured corpus
size or hardware throughput.  Measure those from the frozen manifest before
requesting a run.

## Decision boundary

The system is ready for a narrowly scoped implementation proposal, not for a
model or GPU experiment.  The proposal must explicitly choose the final-v03r
typed ontology and model self-check prompt/schema, then go through the required
architecture deliberation and human ratification path.  A positive CPU fixture
or text canary would demonstrate only lawful composition under the declared
boundary; Paper-1 promotion still requires the frozen multi-seed, multi-skin,
matched-control gates.
