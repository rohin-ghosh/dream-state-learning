# PCFL implementation state and minimum path: fresh audit v1

Date: 2026-09-10

Status: **source-only implementation audit; no execution authority**. This
document records a read-only inspection and local CPU-only checks. It changes
no architecture, benchmark, protocol, endpoint, child, parent, lineage,
adapter, resource allocation, claim, or release state. It authorizes no code
change, model/tokenizer call, benchmark generation, training, LoRA operation,
GPU use, scientific dispatch, or claim. Any material successor remains subject
to the complete deliberation and execution path in `AGENTS.md:3-18`.

## Executive verdict

There is **no executable PCFL benchmark today**. The repository contains a
substantial and increasingly coherent source-level design for one PCFL family
and the distinct mechanism (`M`), longitudinal (`L`), and compression (`C`)
experiments. It does not contain a `pcfl_d0` package, root generator, PCFL
world, event compiler, finite reader, intervention runner, `M` reducer,
`ACTIVE_TEXT_FIXED` service, longitudinal `L` runner, or `C` codec/comparator
implementation.

The strongest PCFL-named executable today is a **byte-crossover accounting
instrument**, not a benchmark. Three adjacent CPU packages supply useful,
tested implementation patterns, but none may be relabeled as PCFL evidence:

1. `feltcraft_symbolic_kernel` closes symbolic graph/topology checks;
2. `rml_d0` supplies a deterministic typed world, targets/twins, controllers,
   certificates, and isolation patterns; and
3. `rml_stage_b` supplies a recurrent supplied-gold-action harness, but its own
   current artifact says that its GPU prerequisites and acceptance test have
   not passed.

The existing parenting and CompilerGym entry points also **do not enforce** the
clean-lineage rule in `research_notes/64_iclr_paper_core_and_benchmark_v2.md:
150-157`. They accept caller-chosen directories and source ledgers, infer
ancestry from mutable marker files, trust a self-declared exposure string, and
permit parenting to continue in the same life that plays CompilerGym. Missing
lineage provenance is accepted, not rejected. Therefore they cannot currently
prove one-way disposable final-gym descendants or fail closed on contamination.

The minimum high-information path is:

1. bind one compact successor contract for the current `M/L/C` benchmark and a
   fail-closed lineage guard;
2. implement and exhaustively test the CPU PCFL core and `M` reducer;
3. establish the explicit-text `M` ceiling before any PCFL LoRA run;
4. finish/certify E0 independently;
5. implement and certify the singular `ACTIVE_TEXT_FIXED` baseline before
   spending on `L`; and
6. do `C` CPU/text accounting in parallel, while treating LoRA only as semantic
   transport unless the physical byte crossover is actually exceeded.

## 1. Authority and supersession

### Current paper target

The current synthesis defines one PCFL generator shared by three experiments,
without pooling their scientific units or artifacts
(`research_notes/64_iclr_paper_core_and_benchmark_v2.md:23-26`):

| Experiment | Current source-level target | Independent unit |
|---|---|---|
| `M` | connection, different-goal traversal, uncertainty-directed expansion, grounded write, delayed old+new use with exact controls (`64:28-51`) | environment root conditional on one fixed child; within-root goals/paths/calls/checkpoints are repeated measures (`64:53-56`) |
| `L` | full learner versus certified evolving `ACTIVE_TEXT_FIXED`, with baseline plateau, positive learner late slope and advantage, retention, and terminal superiority (`64:58-80`) | separately raised paired child lineage (`64:82-84`) |
| `C` | expanded text versus normalized connected text versus schema-plus-residual, charged for full bytes and tested for fidelity/utility/false memory (`64:86-99`) | disjoint root conditional on one fixed child; loads are repeated measures (`64:101-102`) |

All of this remains source-only. The file explicitly authorizes no
implementation or execution (`64:5-8`). The benchmark-minimality synthesis has
the same unbound status
(`research_loop/advisory/20260909_full_objective_benchmark_minimality_synthesis_v1.md:5-10`).

### What is superseded or only directional

- `research_notes/58_one_child_pcfl_relay_v2_executable_contract.md` is a
  detailed generic relational-root contract, but it is prose, not executable
  software, and remains unratified.
- `research_notes/59_one_child_pcfl_relay_v3_execution_complete_architecture_proposal.md`
  uses “execution-complete” to describe resolved design choices; its status
  still denies implementation/execution authority. It is not a runnable
  package.
- `research_notes/60_one_child_pcfl_relay_v4_information_efficient_candidate.md`
  is a candidate resource schedule. Its historical `N=96, X>=47` belongs only
  to one fixed-child joint Bernoulli relay estimand, not to separate `M`
  components or `L`. The modular v4 authority repair explicitly demoted the E3
  and E6 sample/resource numbers to unbound candidates; the v5 audit passed
  only the repaired source labels/authority consistency.
- The old PCFL-13 proposal is a finite mechanism assay, not a lifetime
  benchmark. Its own cross-audit says all 13 relations carry only about 16.7
  bits and can saturate early, and separates the future PCFL-Stream and
  PCFL-Schema programs
  (`research_loop/changes/chg_20260901_pcfl_d0_exact_v2/cross_audit.md:80-99`).
- Current CompilerGym lives remain failure/safety and secondary-transfer
  evidence. The paper target itself says the supplied bootstrap strategy and
  non-identifiable relation graph prevent CompilerGym from carrying the clean
  connected-knowledge claim (`64:104-124`).

### The abandoned PCFL-D0 bundle is not an implementation starting gun

`research_loop/changes/chg_20260901_pcfl_d0_exact_v2/authority_manifest.json`
declares itself `proposed_not_effective` at lines 1-7. It names a future
`pcfl_d0/*.py` package and tests at lines 69-114, but that directory does not
exist. Its effectiveness requires a complete exact-byte authority chain at
lines 8-16; the required deliberation/ratification artifacts are enumerated at
lines 58-67 and are missing. Its cross-audit is explicitly **REWORK — not
ratifiable and not implementable** (`cross_audit.md:1-7`) and lists nine
blocking contract defects (`cross_audit.md:23-59`).

Do not implement that old bundle by filling in its advertised filenames. It
would spend engineering time on the superseded finite PCFL-13 surface without
delivering the current `M/L/C` target. A compact successor should instead bind
the present paper core, current control requirements, current independent
units, and the clean-lineage rule.

## 2. What exists and runs CPU-only today

All commands below were run from `/Users/rohing/dream-state` against the dirty
working tree inspected for this audit. No model, tokenizer, network, adapter,
or GPU operation was invoked.

| Component | What was actually exercised | Result | Scientific disposition |
|---|---|---|---|
| `feltcraft_symbolic_kernel` | `.venv/bin/python -m feltcraft_symbolic_kernel.run` | exit 0 in 6.19 s; 96 alignments, 48 graphs, 36,864 bridge cases, 73,728 bridge-deletion checks, zero bridge failures; 72 symbolic vectors and 9 tests passed | reusable graph/twin/bridge/reference-oracle pattern; **not PCFL** |
| `rml_d0` | `.venv/bin/python -m unittest discover -s rml_d0/tests -p 'test_*.py' -v` | exit 0 in 6.18 s; 16 tests passed; `rml_d0/stage_a_report.json` records `passed: true` | reusable canonical typed-world, schedule, target/twin, Bayes/controller, certificate and isolation patterns; **not PCFL** |
| `rml_stage_b` | plain Python invocation of all six functions in `rml_stage_b/tests/test_g1_cpu_preflight.py` because pytest is not installed | exit 0 in 16.0 s; 6 functions passed | reusable recurrent-machine/test patterns only; its current preflight artifact remains no-go |
| PCFL crossover receipt | `.venv/bin/python -m unittest research_loop/advisory/test_pcfl_crossover_receipt.py -v` | exit 0 in 0.033 s; 13 tests passed | validates safetensors layout/dimensions and byte arithmetic; **not a PCFL environment, carrier, or E3/C result** |

The `rml_stage_b` status is materially narrower than “CPU gate passed.” The
current artifact at
`artifacts/rml_g1_gold_action_fast_v1/cpu_preflight_summary.json:1` records
`acceptance_test_satisfied: false`, `gpu_prerequisite_satisfied: false`, and
`dispatch_authorized: false`; it identifies a P-ATOMS policy-contract
contradiction and missing/mismatched runtime, canary, review, and context
receipts. This is useful fail-closed machinery, not run-ready evidence.

Pytest is absent from both `.venv` and the system interpreter in this checkout.
The pytest command failures were dependency failures, not failing scientific
tests; the applicable suites were rerun through `unittest` or direct function
invocation as reported above.

### Negative executable inventory

The following read-only checks establish the current absence of the paper
objects:

```text
test -d pcfl_d0                         -> absent
rg -l 'ACTIVE_TEXT_FIXED' --glob '*.py' .
                                            -> no matches
rg -l 'EXPANDED_OBSERVATION|NORMALIZED_CONNECTED|SCHEMA_RESIDUAL_CONNECTED'
      --glob '*.py' .                    -> no matches
rg -l 'ATOM_PROPOSE|CAUSE_PROPOSE|USE_LINK|PREDICT_MAP' --glob '*.py' .
                                            -> no matches
```

Consequently **no actual PCFL root can be generated, traversed, intervened on,
reduced, or evaluated on CPU today**. The repository can run adjacent symbolic
or RML worlds and the physical-crossover accounting test only.

## 3. Executable gap by experiment

### `M`: no PCFL mechanism relay exists

Required but absent:

- canonical PCFL public event, atom, link, goal, action, outcome, and evidence
  identities;
- deterministic root generator with two same-start/different-path goals,
  bridge cuts, binding twins/redirections, missing relation and separating
  experiment;
- visibility-safe finite reader and explicit-text carrier;
- grounded compilers for atoms, authentic/deranged/null links, new transition,
  contrasts and interventions;
- complete phase machine from acquisition through delayed old+new reset;
- `REACHOUT_OFF`, sham uncertainty, old-row/new-row factorial, adapter-off,
  wrong-root and binding-swap runners;
- root-level reducer that cannot count paths, goals, samples, or checkpoints as
  independent roots; and
- receipts proving identity, visibility, necessary cuts and no shortcuts.

The current reduced `M` proposal is also scientifically incomplete. The fresh
attack requires atoms-only/truthful-null and atomic-retention objects for the
E2 connection claim and `REACHOUT_OFF` plus a certified active-text comparator
for the E5 acquisition claim
(`research_loop/advisory/20260909_full_objective_benchmark_minimality_synthesis_fresh_attack_v1.md:73-107,268-286`).

### `L`: a design exists; no baseline, runner, or inferential contract exists

The source-level two-arm topology is strong: within each independent root, one
parent-deleted birth forks into isolated `F` and `B` descendants, with separate
stores, files, RNG namespaces and processes
(`research_loop/advisory/20260909_e6_longitudinal_minimal_decisive_fresh_design_v1.md:110-129`).
It is explicitly a current execution NO-GO (`e6...v1.md:14-18`). Missing items
include:

- executable and certified `ACTIVE_TEXT_FIXED`;
- exact opportunity/load tape and seven registered cuts;
- paired lineage runner and root-level late-slope/retention/endpoint reducer;
- plateau equivalence margin, practical terminal margin, failure values,
  uncertainty and multiplicity hierarchy;
- E6-only DEV effect/covariance estimate and prospective root-count receipt;
  and
- measured all-in GPU-hour/resource bound.

The E6 design explicitly warns that neither `N=32` from the parenting
interaction nor `N=96, X>=47` from the fixed-child relay can be inherited
(`e6...v1.md:47-53`). Until the baseline and one-lineage end-to-end canary
exist, an `L` GPU estimate is speculation.

### `C`: arithmetic utility exists; representation experiment does not

The exact physical crossover is known: the observed rank-8 adapter is
80,792,096 bytes, so an expanded semantic reference must exceed 161,584,192
bytes for strict rate below 0.50 before other retained state is charged. The
paper core therefore correctly limits the near-term target to text-interface
semantic-code compression and treats LoRA as transport (`64:86-99`).

Absent are the three executable serializers/codecs, exact decoder/index/prompt/
candidate-scan accounting, denotational round-trip tests, false-memory and
functional-utility endpoints, disjoint-root repeated-load reducer and
uncertainty contract. The fresh review confirms that correct arithmetic alone
is not a `C` design
(`...full_objective...fresh_attack_v1.md:232-246`).

### E0: prerequisite, not supplied by the old lives

The current paper makes E0 noncompensatory: native prompt-to-child-response
training with response-only loss; cumulative rebuild from immutable birth;
candidate adapter/corpus transaction; raw-base and previous-child safety
comparators; atomic promote/reject; rejection quarantine; exact action/outcome
provenance; and source/launch/artifact receipts (`64:159-176`). The old R2/RP/
R3/R4 observations are explicitly failure/safety characterization only.

This audit did not recertify the separately evolving transactional writer
change. The minimum PCFL path must consume E0 only after its own ratification,
implementation tests, independent review and GPU gate pass; PCFL should not
silently treat “a trainer exists” as “E0 passed.”

## 4. Independent clean-lineage attack

### Required rule

The source-level scientific rule is unambiguous: any deployment/final benchmark
visit creates a one-way disposable descendant and **nothing**, including a
selection decision, returns (`64:150-157`). The CompilerGym quarantine makes
the operational threat model explicit: weights, adapters, rows, summaries,
DREAM/SLEEP products, parent observations, outcomes, rankings and
hyperparameter choices are all prohibited return channels
(`research_loop/coordination/20260910_compilergym_bootstrap_quarantine.md:9-28`).
A clean birth manifest must identify exact base, bootstrap sources, parent
history, mechanism and zero target exposure (`quarantine.md:30-40`).

### Current entry points fail open

1. **`classroom_round.py` trusts a directory, not an ancestry proof.** The CLI
   accepts arbitrary `--lineage` and creates the requested round directory
   before provenance validation (`organism_v6/classroom_round.py:147-171`).
   `resolve_snapshot` trusts only mutable `DONE`/`REJECTED` marker files and a
   path (`classroom_round.py:71-87`); it verifies no base, mechanism, corpus,
   parent, exposure, ancestry or content hash.
2. **The exposure claim is self-attested after training.** The sleep path loads
   every prior `round_*/corpus.json` it finds (`classroom_round.py:267-304`),
   including a corpus from a rejected round if the file remains. It then writes
   the literal string `gym_exposure="none (rule-game only)"` into a manifest
   (`classroom_round.py:316-325`). That string is neither derived from nor
   checked against source ancestry.
3. **The exam is not a disposable descendant boundary.** Candidate training,
   exam ledgers, promotion markers and parent state all share the same mutable
   lineage tree (`classroom_round.py:267-372`). There is no sealed canonical
   child mounted read-only, no distinct descendant trust zone, and no check that
   final-evaluation results cannot update a later corpus/playbook/selection.
4. **CompilerGym life and parenting can be the same continuing object.**
   `run_life_v2.py` accepts arbitrary `--life-dir`, creates/reuses it, selects
   CompilerGym programs, finds the latest adapter by path, sleeps back into the
   same life, and can enable `--parent-url` on that life
   (`organism_v6/run_life_v2.py:69-124,229-290`). No birth or exposure manifest
   is required. This permits exactly the contaminated “play gym, then continue
   parenting the canonical child” path that the quarantine forbids.
5. **Bootstrap ingestion is contamination-blind.** `bootstrap_corpus.py`
   accepts arbitrary `--ledgers`, reads them without a source manifest or hash
   check, and its own usage example names `R2_B_seed3`, now explicitly
   quarantined (`organism_v6/bootstrap_corpus.py:25-28,97-165`). The main output
   strips row provenance to only `q/a`; source path labels survive only in a
   sidecar and are not verified ancestry
   (`bootstrap_corpus.py:221-238`).
6. **The adaptive parent is not bound to a child snapshot.** `ParentLedger`
   creates and mutates a caller-chosen directory, and its playbook is rewritten
   in place from whatever rows arrived
   (`organism_v6/parent_backend.py:33-50,73-108`). No clean-child node hash or
   exposure registry prevents final-gym results from changing future teaching.
7. **No regression suite attacks these paths.** No current `organism_v6` test,
   spec or manifest test exercises missing provenance, target exposure,
   disposable descendants, read-only parents, or return-channel closure.

Verdict: the policy is good; enforcement is absent. These entry points cannot
currently fail closed. A caller can omit all provenance, label a contaminated
directory clean, reuse a contaminated child for parenting, or condition later
choices on final-gym results without any programmatic rejection.

### Minimum fail-closed behavior for a successor

This is a required property list, not implementation authority:

- Every child snapshot has a canonical immutable manifest binding lineage/node
  ID, node content hash, parent-node hash, exact base/model/tokenizer bytes,
  mechanism fingerprint, writer/corpus hashes, parent ledger/playbook snapshot,
  exposure set `(domain, split, purpose)`, trust zone and promotion state.
- Missing, unknown, unratified, inconsistent or unhashed ancestry is treated as
  contaminated and rejected **before directory creation, model/provider call,
  write, or GPU reservation**.
- Parenting/classroom commands accept only a verified `CLEAN_CHILD` node and
  reject a target deployment domain anywhere in its transitive ancestry.
- Final evaluation takes a clean snapshot read-only and atomically creates a
  distinct `DISPOSABLE_FINAL_GYM` descendant root. Canonical child and parent
  playbook are read-only; pre/post hashes must match.
- All descendant outputs are descendant-only. The registry must forbid their
  use as bootstrap/sleep/parent sources and forbid result-conditioned selection
  or hyperparameter updates after confirmation.
- Bootstrap and old-corpus ingestion accept only verified, target-disjoint
  sources. Rejected rounds and unknown source identities are not loadable.
- Domain/split/purpose identities are canonicalized so aliases, alternate paths
  and renamed files cannot bypass quarantine.
- Promotion is atomic over child, corpus, writer and manifest heads; no marker
  file alone establishes trust.

Required negative tests include: missing manifest; forged self-declared
`gym_exposure`; `DONE`-only adapter; rejected-round corpus; known
`R2_B_seed3`; resume a final descendant in parenting; final-output mutation of
canonical child; parent-playbook mutation; benchmark/domain alias; symlink,
hardlink and path alias; manifest/corpus hash mismatch; and concurrent/raced
promotion. Every case must reject before any model/provider/GPU boundary.

## 5. Minimum implementation path to paper-worthy `M/L/C`

The path below minimizes irreversible GPU spending. It is not a substitute for
the required material-change deliberation.

### Phase 0 — bind one compact successor (`0 GPU hours`)

Do not revive the old PCFL-D0 exact-v2 bundle piecemeal. Create one current
directive/delta/interpretation/critique/consensus/ratification bundle that binds:

- the paper-core `M/L/C` separation and maximum claims;
- canonical PCFL objects, generator law, finite-reader visibility, phase
  machine, controls, units and reducers;
- the missing atoms/null/atomic-retention and `REACHOUT_OFF` objects;
- the fail-closed lineage manifest/trust-zone state machine above;
- a DEV/confirmation identity policy and explicit “one frozen confirmation”
  rule; and
- exact allowed source/test files and CPU commands.

This is the highest-leverage governance work because current sources conflict
or remain candidates, and `AGENTS.md` forbids filling material scientific gaps
while coding.

### Phase 1 — CPU PCFL core plus lineage guard (`0 GPU hours`)

Implement a small new package around current semantics, reusing tested patterns
but not scientific identities from `rml_d0` and `feltcraft_symbolic_kernel`:

1. canonical types/renderers and stable evidence IDs;
2. deterministic root generator, theorem/certificate checker and split law;
3. public action/outcome phase machine and exact legal histories;
4. atom/link/new-transition compiler, explicit-text carriers and finite reader;
5. intervention engine and root-level `M` reducer;
6. `C` serializers, lossless decoders and complete byte accounting; and
7. shared lineage/provenance preflight and atomic promotion library.

CPU gates must prove exhaustive legality, identifiability, necessary path/bridge
cuts, twin/redirection effects, missing-relation necessity, separating-action
uniqueness or registered multiplicity, deterministic replay, intervention
closure, reducer nesting, round-trip codec fidelity, exact accounting and every
contamination negative test above.

### Phase 2 — explicit-text `M` DEV (`model inference; no LoRA`)

Run the smallest disjoint no-claim engineering screen first, then eight fixed
DEV roots only if the first stage clears. Use the exact same phase machine and
reader planned for LoRA. Establish:

- task headroom and explicit-text ceiling;
- atoms versus links versus deranged/null controls;
- two-goal different-path traversal;
- uncertainty versus truthful sham and `REACHOUT_OFF`;
- delayed old/new necessity; and
- stable root-level metric variance/call/token cost.

Stop if text cannot solve the relay: LoRA cannot rescue a nonfunctional world,
reader or controller. Treat stagewise continuation as engineering triage, not
as confirmatory inference; the fresh attack documents the selection-bias and
unpowered-threshold problem (`...full_objective...fresh_attack_v1.md:125-176`).

### Phase 3 — E0 and three-build `M` transport (`GPU only after separate gate`)

In parallel with Phase 2, complete E0 on its own native microassay. Once both
text `M` and E0 pass independently, use only text-positive DEV roots for a
budgeted transport diagnostic. The old/new factorial can use three physical
builds only if old-row read-time cuts are proven faithful and old+pad is
exposure matched; otherwise build all semantically distinct cells. Report
failed/unrun LoRA cells as a prespecified gated composite, never as observed
LoRA effects.

Only after this DEV estimates root-level effect/variance and exact GPU cost
should a fresh, frozen `M` confirmation root count and stopping rule be bound.

### Phase 4 — implement and certify `ACTIVE_TEXT_FIXED` (`0 training GPU`)

Before `L`, build the singular strong baseline promised by the paper:

- evolving typed text memory with the same public outcomes and update
  opportunities;
- same ordinary action/reachout tools and generated-token envelope;
- frozen acting model;
- faithful write/read/use receipts, deterministic memory-policy version and
  exact resource accounting; and
- an independently passing terminal-load/headroom/plateau-candidate canary.

No `L` claim is interpretable if this baseline is a prompt sketch rather than
an executable, certified competitor.

### Phase 5 — one-lineage `L` canary, then E6 DEV (`GPU estimate comes first`)

Run one paired clean birth through all seven cuts to validate isolation,
cumulative load, retention probes, failure handling, resource matching and
root-level reduction. It is plumbing, not evidence. Then run disjoint E6 DEV to
estimate the full paired covariance, plateau behavior and all-in cost. Only
that receipt can set independent lineage count, margins, uncertainty and
confirmation allocation. Do not transplant sample sizes from parenting or `M`.

### Phase 6 — `C` CPU/text result; LoRA is optional transport

`C` should not wait for `L`. Once the PCFL compiler and explicit-text relay
work, evaluate increasing loads for all three textual representations with
lossless round-trip, false-memory and path-utility measurements. Charge the
complete live representation and decoder/index/retrieval work. Use disjoint
roots and a repeated-load/root-level uncertainty method. Run LoRA only to ask
whether the same semantics transport; do not claim physical adapter
compression below the measured crossover.

## 6. Ranked work by information per engineering/GPU hour

| Rank | Work | Why it dominates | GPU cost |
|---:|---|---|---:|
| 1 | Ratify compact current PCFL-core + lineage-guard successor | removes contradictory/superseded authority and prevents every later result from being contaminated | 0 |
| 2 | Implement CPU generator/certificates/phase machine/interventions/reducer and exhaustive tests | falsifies world shortcuts and reducer errors before model noise; unlocks every experiment | 0 |
| 3 | Explicit-text `M` DEV, first 4 then at most 8 roots | fastest test that the actual relay is solvable and informative; provides effect/variance/cost | inference only |
| 4 | Finish E0 independently | the writer is a noncompensatory paper prerequisite, but should not consume PCFL training until text works | bounded assay |
| 5 | Implement/certify `ACTIVE_TEXT_FIXED` | required for both E5 attribution and the headline `L` comparison | inference only |
| 6 | Three-build `M` LoRA transport DEV | first justified PCFL training spend; attributes weight transport only after text and writer pass | small/bounded |
| 7 | `C` serializers + exact CPU/text rate–distortion | cheap independent paper result; no need to cross the physical LoRA threshold | 0 training |
| 8 | One-lineage seven-cut `L` canary and E6 DEV | highest central value but also highest cost; baseline, isolation and covariance must exist first | largest unknown |
| 9 | State-branching/scaled THINK sibling | valuable optional organ, but the paper explicitly allows the safe reference THINK if it misses its gate (`64:178-194`) | defer |

The practical critical path is therefore **CPU PCFL + clean lineage -> text M ->
E0/M transport**, while **ACTIVE_TEXT_FIXED** and **C serializers** proceed in
parallel. A long `L` launch before those gates has the worst information per GPU
hour: it can fail for benchmark, baseline, writer, lineage, estimator or
resource reasons that cheaper stages would already expose.

## 7. Exact next test commands after an authorized implementation

These are proposed interface-level acceptance commands, not presently runnable
and not execution authority:

```text
.venv/bin/python -B -m unittest discover -s pcfl_core/tests -p 'test_*.py' -v
.venv/bin/python -B -m pcfl_core.run_cpu_gate --suite full --receipt <fresh-dir>
.venv/bin/python -B -m pcfl_core.lineage_preflight --suite adversarial --receipt <fresh-dir>
.venv/bin/python -B -m pcfl_m.run_text_dev --roots <frozen-dev-root-list> --stage 1
.venv/bin/python -B -m pcfl_active_text.run_cpu_gate --suite full --receipt <fresh-dir>
.venv/bin/python -B -m pcfl_c.run_text_rate_distortion --roots <disjoint-root-list>
```

Every command should be accepted only after exact filenames, argv, inputs,
outputs, hashes and environments are ratified. The first three must be pure CPU
and fail before generating scientific identities if their authority or lineage
input is absent.

## Bottom line

The conceptual convergence is ahead of the implementation. Today there is a
clear paper benchmark target and several tested adjacent organs, but zero
executable PCFL experimental path. The most dangerous false shortcut is to
wire PCFL semantics directly into the permissive `organism_v6` life/classroom
scripts: those scripts do not enforce clean births or disposable descendants,
and they cannot support the required provenance claim.

The fastest honest route is not a large run. It is one ratified compact core,
one exhaustive CPU implementation, one text-only relay, and one fail-closed
lineage boundary. That sequence turns later GPU hours into interpretable
evidence rather than another diagnostic life.
