# Smallest exact executable PCFL core for M/L/C: fresh interpretation v1

Date: 2026-09-10

Status: **fresh-context, source-only recommendation; unbound and
non-authoritative**. This note changes no architecture, benchmark, protocol,
control, endpoint, child, lineage, model, adapter, resource plan, claim, or
release state. It authorizes no implementation, root/data generation,
model/provider call, training, LoRA/GPU operation, dispatch, promotion, or
claim. Every material choice remains subject to `AGENTS.md` deliberation,
exact-byte human ratification, scoped implementation, tests, independent
review, and a separate GPU/scientific gate.

## Source boundary

Only these sources were read:

- `AGENTS.md` —
  `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e`
- `research_notes/64_iclr_paper_core_and_benchmark_v2.md` —
  `23887c69ea8269586caa73e16ad1d240a5e88a71c2887e22894c96b5359875e8`
- `research_loop/advisory/20260909_full_objective_benchmark_minimality_synthesis_v1.md`
  — `59e4657ffbdf010f8e27472d0876b6695d84e1d0472079a7f44eea59a945e125`
- `research_loop/advisory/20260909_full_objective_benchmark_minimality_synthesis_fresh_attack_v1.md`
  — `8c6f35e87cf28271dae7119f6f7f3bc6e130ac807b4f4bfaa14e5a26c60b0d71`
- `research_loop/advisory/20260910_pcfl_implementation_state_and_minimum_path_fresh_audit_v1.md`
  — `0e78fe49b65b2644d504b98bbeef91b84f9a5f10e305a43815ef964f35334676`
- `research_loop/coordination/20260910_compilergym_bootstrap_quarantine.md`
  — `0394b08d1f08c5922236d149984bf795add68c9506eeb0863bff0c21b84bb4da`

No implementation or model/GPU work was performed.

## Ruling

The smallest honest target is one pure CPU kernel, one fail-closed lineage
guard, and three experiment shells:

```text
canonical objects -> sealed generator/certificates -> public phase machine
                  -> finite reader/carriers -> interventions
                  -> M root reducer | L paired-lineage reducer | C codec reducer
```

“Smallest” here means **irreducible for the intended claims**, not globally
optimal. The sources do not justify optimal sample sizes or a confirmation-
ready protocol. A reduced M without atoms/null/atomic retention,
`REACHOUT_OFF`, and a certified `ACTIVE_TEXT_FIXED` baseline is smaller, but it
cannot carry the full connection/expansion claim.

E0 remains a separate noncompensatory writer prerequisite. Parenting remains
the separate `P0/P1/U0/U1` entry-adjusted interaction; M/L/C do not replace it.

## 1. Exact kernel interface and objects

The CPU-only kernel exposes:

```text
canonical_bytes(object) -> bytes
generate_root(config, split, seed) -> SealedRoot | reject
certify_root(root) -> RootCertificate | reject
advance(EpisodeState, Command) -> EpisodeState + PublicEvent[] + PrivateReceipt
visible_view(PublicLedger, phase, carrier, interventions) -> FiniteView
compile_carrier(FiniteView, CarrierSpec) -> bytes + CompilerReceipt
reduce(ExperimentSpec, UnitReceipt[]) -> ExperimentReceipt | reject
preflight(authority, ancestry, domain, split, purpose) -> VerifiedContext | reject
```

Science mode has no ambient-directory lookup, inferred “latest” state,
permissive unknown fields, or defaults. Missing authority or configuration
rejects before directory creation, write, external call, or reservation.
Synthetic tests use a terminally ineligible `TEST_ONLY` trust zone.

Minimum canonical objects:

- `GeneratorConfig`: version; finite template set; parameter bounds and
  probabilities; split/seed law; action/outcome alphabets.
- `SealedRoot`: oracle states/transitions/outcomes; observation map; true
  relations; old bridges; twins/redirections; missing relation; separating
  action set; two ordinary goals; delayed old+new goal.
- `PublicEpisode`: opaque episode tag, phase, public state, allowed commands,
  append-only ledger, checkpoint. It exposes no seed or oracle/root hash.
- `PublicEvent`: ordered phase, action, public observation/outcome, public
  pre/post-state aliases, evidence provenance.
- `Atom`: normalized proposition citing prior public event IDs only.
- `Link`: normalized typed relation over public atom/state references with
  evidence and binding IDs.
- `TransitionRow`: `(public pre-state evidence, action, public outcome, public
  post-state evidence)`; the only new semantic SLEEP row.
- `Goal`: public start/success predicate plus private required-path certificate.
- `CarrierSpec`: `TEXT|LORA`, semantic arm, ordered row IDs, compiler/version,
  exposure/padding policy, source checkpoint.
- `InterventionSpec`: name, target IDs, `READ|DISPATCH|WRITE|ADAPTER` boundary,
  invariant set.
- `OpportunityTape`: frozen cumulative public opportunities and L cut vector.
- `Representation`: expanded, normalized-connected, or schema-residual,
  including encoder, lossless decoder, index/retriever, and accounting manifest.
- `UnitReceipt`/`ExperimentReceipt`: unit and nesting IDs, fixed denominator,
  failures, endpoint vector, resource counts, source/config/artifact hashes.

Canonical bytes must be one-to-one with meaning. A ratifiable choice is UTF-8
JSON with sorted keys, compact separators, no duplicate/unknown keys, no
NaN/infinity/floats, and fixed-scale integers or numerator/denominator pairs.
Every ID is SHA-256 over canonical payload plus meaning-defining schema and
generator/compiler version. The exact encoding remains a material ratification
choice; code may not silently choose it.

## 2. Generator contract

`generate_root(config, split, seed)` is total and deterministic. Split identity
is domain-separated from path/name aliases. DEV, reserve, and confirmation are
disjoint by construction. Rejection sampling, if ratified, has a fixed order
and cap. One frozen confirmation is used once per claim unless a prospective
multiplicity rule says otherwise.

Every emitted root certificate proves:

1. all state/action/outcome/event/evidence/goal/binding IDs are unique and
   references close;
2. no answer is available from one observation/atom;
3. goals A/B have the same public start and different certified required paths;
4. cutting each named bridge destroys or redirects its target solution without
   changing unrelated public facts;
5. the matched twin/redirection changes the intended binding/path/answer and
   leaves no accidental original shortcut;
6. one relation is absent from all admissible old evidence; pre-experiment
   candidate worlds remain unresolved; the registered action or complete tied
   set uniquely separates them through a public outcome;
7. after a grounded new write, the delayed goal requires both a named old
   relation and the new transition, with neither-cut shortcut;
8. atoms, linked, truthful-null, and deranged carriers use identical admitted
   evidence and the ratified matched-exposure law; derangement retains no
   claim-critical correct binding;
9. legal histories replay deterministically; reset is exact; branch clones do
   not mutate one another; and
10. public/compiler inputs contain no future goals, oracle path/answer, hidden
    relation, intervention label, split/seed clue, or target annotation.

A systematic certificate counterexample is a generator-version `NO_GO`, not a
root to discard.

L additionally consumes one outcome-independent cumulative opportunity tape.
No cut schedule defaults: the claim configuration must bind the exact tape,
plateau-anchor rule, and at least three later cuts. C emits prospectively
ordered increasing loads; loads remain repeated measures inside a root.

## 3. Visibility and M phase machine

The actor, controller, carrier compiler, and text baseline receive only
`visible_view` over the public ledger, current public goal, and allowed-action
catalog. The reader is a versioned phase allow-list, not a prompt convention.
Hidden/oracle state, future events/goals, intervention names, sibling ledgers,
private receipts, correct answers, and generator coordinates are absent.

Goal A and B are isolated clones of the same old checkpoint and cannot write
into each other or the acquisition trunk. SLEEP sees only grounded public
`TransitionRow`s in the native prompt/child-response envelope; raw THINK/DREAM
routes, predictions, sham rows, and hidden critiques are ineligible. The
delayed task follows a true context reset and sees only its declared carrier.

M's legal graph is:

```text
SEALED -> OLD_ACQUIRE -> OLD_COMPILE -> OLD_CHECKPOINT
  OLD_CHECKPOINT -> GOAL_A_PROBE -> GOAL_A_DONE
  OLD_CHECKPOINT -> GOAL_B_PROBE -> GOAL_B_DONE
  -> MISSING_DECLARE -> EXPERIMENT_SELECT -> EXPERIMENT_DISPATCH
  -> NEW_OUTCOME -> NEW_ROW_STAGED
  -> SLEEP_COMMIT | NO_WRITE_COMMIT | SHAM_WRITE_COMMIT
  -> DELAYED_RESET -> DELAYED_GOAL -> TERMINAL
```

Exactly one ordinary experiment is dispatched on the acquisition trunk. Only
its public outcome can ground the new row. Illegal skips/repeats/transitions
reject without mutation. `REACHOUT_OFF` is enforced in dispatch, not prose.
Read cuts delete the target semantic rows and every derived index entry.
Adapter treatments are verified by mounted-artifact hash.

Minimum claim-closing interventions:

| Treatment | Boundary | Alternative closed |
|---|---|---|
| `ATOMS_ONLY`, `LINK_NULL`, `LINK_DERANGED` | read | links add nothing; slots/format suffice; bindings need not be correct |
| `BRIDGE_CUT`, `BRIDGE_TWIN_REDIRECT` | read/root | path/bridge is unnecessary; surface cue rather than binding |
| `UNCERTAINTY_SHAM` | read | experiment choice ignores authentic uncertainty |
| `REACHOUT_OFF` | dispatch | acquisition used an undeclared external path |
| `NO_WRITE`, `SHAM_WRITE` | write | new semantic content is unnecessary; ritual alone suffices |
| `OLD_CUT` | read | delayed success does not require old knowledge |
| `ADAPTER_OFF`, `WRONG_ROOT` | adapter/read | behavior is not carrier-dependent or root-specific |
| `NEW_BINDING_SWAP`, `NO_SEMANTIC` | read/adapter | new binding is unnecessary; nonsemantic mechanics suffice |

Each intervention is deterministic, target-closed, idempotent, hash-receipted,
and preserves all declared non-target semantics/indexes. A three-build old/new
factorial is valid only after CPU proof that `OLD_CUT` is faithful,
old-plus-pad is exposure-matched, randomness is controlled, and no collateral
read/mask effect occurs; otherwise build every semantic cell. Unrun component
outcomes are not observed effects. Adverse zero-filling is valid only for a
preregistered gated-product estimand.

M's root vector keeps, without compensation:

```text
atomic_retention; linked-atoms; authentic-null; authentic-deranged
two valid differing goal paths; bridge-cut; twin-redirection
separating choice/information gain; authentic uncertainty-sham; reachout integrity
Y11, Y10, Y01, Y00; adapter-off; wrong-root; binding-swap; no-semantic; integrity
```

Here `Y11` is old available/new written, `Y10` old available/no-write, `Y01`
old cut/new written, and `Y00` both absent. Claim-gating joint necessity uses
adequate absolute `Y11`, `d_write=Y11-Y10`, and `d_old=Y11-Y01` with registered
margins. `Y11-Y10-Y01+Y00` is reported only as additive interaction; it neither
defines nor alone proves joint necessity.

## 4. M, L, and C shells and independent units

| Experiment | Independent unit | Repeated measures, never `N` | Required shell |
|---|---|---|---|
| M | environment root under one fixed parent-deleted child and frozen generator/RNG law | goals, paths, calls, samples, forks, checkpoints, interventions | paired root vector above; explicit-text same-semantics ceiling before LoRA |
| L | independently generated paired lineage | F/B branches, cuts, loads, tasks, probes, samples | common clean birth forks into isolated `F` full learner and singular certified `B=ACTIVE_TEXT_FIXED` |
| C | disjoint environment root under one fixed child | loads, formats, goals, probes, samples | three same-semantics codecs, repeated-load root reducer, complete byte/work accounting |

M roots start from byte-identical read-only child snapshots with isolated store,
process, RNG, episode, and artifact roots. Wrong-root therefore tests this fixed
child's experience specificity, not between-person specificity.

In L, each common parent-deleted birth forks before treatment. F and B have
separate processes/files/stores/RNG/corpora/memory/artifact heads and share
nothing afterward. Both replay the same opportunity tape and receive the same
public outcomes, update opportunities, ordinary tools/reachout, and generated-
token envelope. B has a frozen acting-model hash, versioned deterministic typed
memory policy, and faithful write/read/use and resource receipts.

At every L cut both arms run:

```text
INGEST -> UPDATE (F transactional SLEEP; B text-memory write)
       -> RETENTION_PROBES -> NEW_LOAD_PROBES -> CUT_RECEIPT
```

The L reducer has no defaults for pair count, cuts, failure values, baseline
plateau-equivalence margin, learner slope margin, slope-advantage margin,
retention floor, terminal practical margin, uncertainty/covariance,
multiplicity, or resource matching. Plateau is fixed-landmark or uses a valid
registered sequential/independent-selection rule. Release order is:

1. task headroom and B faithfulness/read/use;
2. B late slope equivalent to zero;
3. F late slope positive;
4. paired F-minus-B slope positive;
5. old competence retained; and
6. terminal F exceeds B by the practical margin.

One paired-lineage canary is plumbing, not evidence. M or parenting sample
sizes cannot be inherited by L.

C encodes the identical canonical semantic ledger as:

```text
EXPANDED_OBSERVATION
NORMALIZED_CONNECTED
SCHEMA_RESIDUAL_CONNECTED
```

Each has an exact lossless decoder. The receipt charges payload, schema/
codebook, decoder/compiler, index, retrieval metadata, prompt/interface,
candidate-scan state, all other retained mutable state, and retrieval/scan
work. Shared-code amortization must be explicit, never silently free. Endpoints
are exact semantic round-trip, functional path utility, false memories,
complete bytes, and work. Utility uncertainty is clustered by root.

The current physical boundary is fixed: an 80,792,096-byte rank-8 adapter needs
a denotationally equivalent expanded reference strictly above 161,584,192
bytes for rate `<0.50`, before other state is charged. Before a complete-state
crossover, C may claim text-interface semantic-code compression only. LoRA may
test transport, not physical compression.

## 5. Fail-closed lineage

Every snapshot manifest binds lineage/node ID and content hash, parent hash,
exact base/model/tokenizer bytes, mechanism fingerprint, writer and committed/
candidate corpus hashes, parent ledger/playbook hashes, canonical exposure set
`(domain, split, purpose)`, trust zone, promotion state, authority, and source/
launch/artifact receipts.

```text
CLEAN_SOURCE -> CLEAN_CHILD -> DEV_DESCENDANT | DISPOSABLE_FINAL
candidate -> PROMOTED_CLEAN | REJECTED_QUARANTINED
unknown/inconsistent/unhashed -> CONTAMINATED (terminal)
```

Parenting accepts only verified target-blind `CLEAN_CHILD`. Final evaluation
mounts clean child/parent state read-only and creates a distinct disposable
descendant; pre/post hashes must match. No descendant weight, adapter, row,
summary, DREAM/SLEEP product, parent observation, outcome, ranking, selection,
or performance-conditioned hyperparameter choice returns. Domain/path/file/
symlink/hardlink aliases cannot evade exposure. Promotion is atomic over child,
corpus, writer, and manifest; `DONE` or self-declared exposure is not trust.
CompilerGym-derived `R2_B_seed3`/seed-303 remains diagnostic-only.

## 6. CPU gates

Before model inference, one pure-CPU receipt must show zero failures for:

1. canonical golden bytes/hashes and malformed/unknown/version rejection;
2. deterministic generator replay, split disjointness, finite-template
   enumeration, per-root certificates, and root/twin uniqueness;
3. no-single-atom answer, different goal paths, necessary bridge/twin effects,
   missing-relation/separating-action identifiability, and no old/new shortcut;
4. exhaustive phase transitions, illegal-history no-mutation, exact reset,
   immutable fork/process/RNG/store isolation;
5. hidden-field byte noninterference and absence of future/oracle/seed/split/
   intervention/sibling/target/answer leakage;
6. grounded compilers, SLEEP eligibility, truthful null/valid derangement,
   matched exposure, atomic-retention scoreability;
7. intervention target closure/idempotence/non-target invariance, faithful
   `OLD_CUT`, dispatch-level `REACHOUT_OFF`, and artifact identity checks;
8. adversarial reducer fixtures proving roots/lineage pairs are the only units,
   failures stay adverse, and conditional/gated results cannot masquerade as
   population or observed component effects;
9. L branch isolation, identical tapes/outcomes/opportunities, frozen B model,
   deterministic memory, and complete resource receipts;
10. C byte-exact round trips, corrupt/extra-record rejection, same semantics,
    complete accounting, false-memory detection, and load-within-root nesting;
11. lineage negatives: missing/forged manifest; `DONE`-only adapter; rejected
    corpus; `R2_B_seed3`; final resumed in parenting; child/parent mutation;
    domain/path/symlink/hardlink alias; manifest/corpus mismatch; transitive
    target exposure; concurrent promotion race; and
12. complete authority/source/config/input/environment/command/artifact hashes,
    interruption safety, and permanent test-only ineligibility.

Any systematic counterexample is version-level `NO_GO`. CPU passage proves
software properties only. The next separately authorized gate is explicit-
text M using the same reader/semantics. No LoRA begins until text M and
separately ratified E0 both pass. Stagewise DEV is no-claim triage, not
confirmation inference.

## 7. Exact claim boundary

- **CPU only:** deterministic generation/certification, visibility, phase,
  intervention, lineage, codec, and reducer correctness; no learning claim.
- **Text M only:** the registered semantic relay is text-solvable and has
  headroom; no personal-LoRA, writer, lifetime, parenting, or compression claim.
- **Reduced M:** at most: conditional on one fixed parent-deleted child and
  registered roots, authentic rather than deranged old bindings affected
  goal-specific selection/traversal, and a controlled new write contributed to
  delayed old+new success under the executed interventions.
- **Claim-complete M:** only after E0 plus atoms/linked TEXT+LoRA, null,
  deranged, atomic retention, goals/bridge/twin, uncertainty/sham,
  `REACHOUT_OFF`, grounded write/no-write controls, old/new necessity, and
  adapter/root/binding attribution may one claim an observed and intervention-
  tested connection/traversal/expansion relay for this fixed child across the
  registered roots. It is not causal mediation, an internal-graph proof,
  population children, between-person specificity, or lifetime learning. Full
  E5/strong-baseline language additionally requires certified B.
- **L:** only the six ordered gates support continued improvement beyond this
  one comparator's registered local plateau on this task distribution,
  horizon, and resource policy—not intrinsic saturation, all text agents, or
  indefinite improvement.
- **C:** exact results may support text-interface semantic-code compression;
  LoRA may support transport. Physical adapter/full-agent compression requires
  a charged complete-state crossover.
- **Parenting/transfer:** M/L/C do not establish `(P1-P0)-(U1-U0)` or
  CompilerGym transfer. Disposable benchmark evidence cannot tune clean births.

## 8. Bytes still requiring ratification

The sources do not bind generator templates/cardinalities/probabilities/seeds/
splits; public vocabulary/renderers/prompts/tokenizer/exposure budgets; E0;
M counts/margins/hierarchy/stopping; the active-text algorithm; L cuts,
plateau/slope/retention/terminal rules, estimator and pair count; C loads,
codecs/margins/accounting; or authorized filenames/commands/environments.
Science constructors must reject while any field is unset.

## Bottom line

Ratify one compact CPU PCFL kernel plus lineage guard, then prove it
exhaustively, then run text-only M. Add LoRA only after E0, L only around a real
certified `ACTIVE_TEXT_FIXED`, and C as a disjoint same-semantics codec shell.
This is the smallest executable surface that supports all intended M/L/C
claims without treating a root as a life, a relay as compression, a directory
as ancestry, or a local text plateau as universal saturation.
