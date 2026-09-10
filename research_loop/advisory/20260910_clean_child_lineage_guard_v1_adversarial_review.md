# Clean-child lineage guard v1 — fresh adversarial source review

Date: 2026-09-10

Status: **source-only rejection/rework advisory**. This review authorizes no
implementation, model or tokenizer execution, corpus generation, training,
evaluation, GPU work, scientific claim, release, or transfer.

## Source boundary

This fresh-context review used only:

- `AGENTS.md`;
- `research_loop/advisory/20260910_clean_child_lineage_guard_v1.md`;
- `research_loop/coordination/20260910_compilergym_bootstrap_quarantine.md`;
- `research_loop/plans/adaptive_parent_development_v5_consensus.md`;
- `organism_v6/classroom_round.py`;
- `organism_v6/bootstrap_corpus.py`; and
- `organism_v6/run_life_v2.py`.

No other repository source, artifact, coordination record, local quarantine
marker, runtime state, or external fact was inspected. In particular, this
review cannot validate the guard's references to an unsupplied “clean-child
ruling,” Fable/Codex records, or authoritative-node files.

## Verdict

**Reject v1 as an implementation specification and as “non-material
enforcement.” Preserve the immediate CompilerGym contamination stop while the
guard is repaired and separately ratified.**

The proposal has the right high-level invariant for sealed CompilerGym data:
no result or derivative returns from a disposable final descendant to a clean
child or parent. But its three JSON objects do not enforce that invariant.
They record what a producer says it read; they do not constrain or observe
what the producer, remote parent, human, scheduler, or later selector actually
read. Several causal inputs are outside the taint union, the evaluation state
machine contradicts the developmental-exam exception, the content-addressed
schemas contain underspecified or mutable identities, and an atomic rename is
not compare-and-swap.

The proposal is also materially broader than the supplied rules. A universal
artifact registry, global information classes, all-decision receipts, a
release-group protocol, a human-information policy, and a new promotion/state
machine change visibility, acceptance tests, and scientific eligibility.
Under `AGENTS.md`, those exact choices need the durable deliberation and human
ratification path; calling them a “smallest implementation seam” does not make
them non-material.

## Blocking findings

### 1. A valid manifest can still be a lie

The artifact rule derives taint from declared `input_artifact_ids`
(`clean_child_lineage_guard_v1.md:102-135`). Nothing binds that list to the
producer's actual file reads, network requests, inherited process state,
remote-model session, environment, stdout, caches, or human-supplied prompt.
A producer can read a sealed result, omit that read, and emit a perfectly
self-consistent clean record. Recomputing hashes proves byte integrity, not a
complete causal history.

This is not hypothetical relative to the inspected entry points:

- `classroom_round.py:170-198` creates directories, resolves snapshots,
  constructs the task, loads the model, opens a lineage-global parent ledger,
  and calls a remote parent before any proposed guard exists;
- `bootstrap_corpus.py:155-205` reads arbitrary ledger paths and sends their
  contents to a remote author; and
- `run_life_v2.py:106-176` constructs CompilerGym, selects programs, scans the
  life directory, reuses cached probes, and infers prior state from names.

**Required repair:** separate provenance declaration from enforcement. Before
the first task/model/author byte is available, run the operation with a
capability-limited read set, a dedicated write root, no undeclared network,
and a bound remote-service/session policy. Record the actual opened inputs and
brokered requests in an execution receipt, then require the artifact record's
dependency closure to equal that receipt. Use the already-open immutable
objects for execution; do not hash a path and reopen it later. If this cannot
be enforced for a producer, its output is ineligible rather than clean.

### 2. Semantic and statistical feedback remain open

`SELECTION_RECEIPT` says which evidence was “inspected,” and the prose calls
human inspection an information flow (`clean_child_lineage_guard_v1.md:321-327`).
Neither statement prevents an omitted inspection or a decision conditioned on
score-correlated side information. Final information can return through:

- retry count, timing, process exit, exceptions, resource use, output size,
  filenames, missing files, or a root being scheduled at all;
- a human's memory, an unrecorded conversation, a remote parent's retained
  context, or a prompt/code edit made after viewing results;
- early stopping, candidate-set changes, root ordering, seed replacement, or
  selection of which summaries are produced; and
- an aggregate, paraphrase, label, or “clean” mechanism record whose declared
  inputs omit the tainted source.

The current runner demonstrates score-conditioned channels that must be
classified rather than hand-waved: cached probe results are accepted by name
(`run_life_v2.py:52-64`), probe results set the promotion floor
(`run_life_v2.py:166-188`), and prior paired probe gains change the learning
rate (`run_life_v2.py:191-207`). Logs also expose metrics. These may be valid
development-only feedback under a separately ratified scope; they cannot be
treated as clean merely because a receipt is present.

**Required repair:** prebind a complete decision DAG: candidate universe,
root/seed schedule, retry predicates, stopping rule, permitted aggregates,
recipients, release group, and every later decision scope. Run sealed finals
behind a blinded scheduler that exposes only preregistered infrastructure
status until release. Treat remote sessions, human access, logs, telemetry,
and schedule changes as explicit principals/channels. A provenance ledger is
necessary audit evidence, but it is not a substitute for access control.

### 3. The proposed taint closure is not transitive over its own schema

The equality rule unions the taints of `input_artifact_ids`, but
`evidence_ids` are a separate field (`clean_child_lineage_guard_v1.md:112-135`).
If an evidence event carries task/final exposure, the stated union does not
include it. The same hole applies to `source_bundle_sha256` and
`invocation_sha256`: they are opaque hashes, not dependency nodes whose
ancestry participates in the union.

Further breaks in the closure are:

- a head contains a mechanism ID but no required selection-receipt IDs, so the
  rule “absence of a receipt blocks sealing” is not bound into the head;
- a selector can name only the winner and omit rejected candidates, failures,
  excluded roots, or the stopping observation—negative information that can
  determine the result;
- `lineage_id`, `root_id`, policy IDs, transaction IDs, release groups, and
  partition IDs are bare strings with no authenticated records; and
- an output record can name the previous payloads without naming the exact
  previous head, policy, executable environment, parent session, and decision
  that caused the output.

`bootstrap_corpus.py` contains a concrete two-source loss: a contrast rendering
reads `e` and a randomly chosen `other` (`:199-203`), but the saved row records
only `e`'s `src` and `eid` (`:181-182`). The actual trainer input then removes
even those fields and writes only `q`/`a` (`:231-233`). No later graph walk can
recover that lost ancestry.

**Required repair:** use one typed dependency-edge model for artifacts,
evidence events, policy/config/code/environment identities, decisions, remote
requests, and prior heads. Every causal edge participates in a finite,
acyclic, fail-closed closure. Bind the exact selection and execution receipts
into the promoted head. Record the entire candidate/schedule set, including
failures and exclusions, not only the selected output.

### 4. “Clean” is global where eligibility is use-relative

The schema gives each artifact one `information_class`, says
`TASK_EXPOSED_DEV` can never become `CLEAN_ELIGIBLE`, and lets a clean head
accept only `CLEAN_ELIGIBLE` (`clean_child_lineage_guard_v1.md:119-135,
169-171`). At the same time, it defers whether development-only CompilerGym
aggregates may inform mechanism or hyperparameter choices. Those rules cannot
all hold: a development-exposed decision can be permitted for one prospective
scope while forbidden as personal experience for the child and forbidden for
a stronger claim.

There is a second direct contradiction. Every evaluation receipt has
`return_policy="DENY_ALL"`, and the state machine has no evaluation-to-clean
transition (`clean_child_lineage_guard_v1.md:190-226`). The v5 source instead
says a developmental clone's task experience never enters the child/SLEEP
corpus but preregistered aggregate skill/error codes may update the parent's
notebook (`adaptive_parent_development_v5_consensus.md:116-119`). V1 cannot
both enforce that exception and deny every return.

**Required repair:** make eligibility a relation among source domain,
partition, exposure role, destination/use, decision scope, and claim—not a
single global class. Keep sealed-final exposure as an absolute non-return
taint. If the developmental-exam exception is ratified, implement a narrow,
named declassifier whose exact code, input panel, output alphabet, destination
parent fields, budget, and one-time receipt are prebound. No free-form summary
or child update may pass through it.

### 5. Several identity/state fields are not implementable as written

The schemas need exact byte semantics before code can safely implement them:

- `artifact_id` hashes a “canonical-record-body,” while the record contains
  `artifact_id` and a `created_at_utc` field declared outside identity
  (`clean_child_lineage_guard_v1.md:102-123`). The excluded fields and canonical
  body are undefined; post-identity mutation is therefore ambiguous.
- `evaluation_fork_receipt` is content-hashed while `state` and
  `output_artifact_ids` must change from CREATED through terminal release
  (`:188-203`). Rewriting it destroys immutability; keeping its hash makes the
  later state unrepresentable.
- `head_sha256` “hash[es] all preceding fields” (`:174`) without an exact
  canonical exclusion rule for itself and without a signed/authorized registry
  head.
- a SHA-256 registry record authenticates no writer. An unauthorized producer
  can make a new, internally valid record that simply claims clean inputs.
- a directory tree manifest lacks exact path normalization, case/Unicode
  rules, metadata policy, race handling, and a guarantee that the bytes hashed
  are the bytes later consumed.
- “fresh” parent state is not defined by payload identity alone; freshness must
  bind the root/session and prove the remote parent did not retain state.

Most importantly, staging, `fsync`, and atomic rename do not provide
compare-and-swap (`:178-183`). Two writers can validate the same generation
and then sequentially rename different heads; the later rename silently wins.
Artifact, registry, and pointer durability can also split across a crash.

**Required repair:** specify canonical bytes and excluded envelope fields;
make every transition a new immutable event linked to its predecessor; define
an append-only, authorized registry; and use a real serialized conditional
update for the head. Bind all artifacts and the transaction journal durably
before the pointer changes. Define recovery for every crash boundary.

### 6. `parent_text_targeted` is an unauditable Boolean

V5 requires response-only loss: parent text may condition the child but must
be loss-masked (`adaptive_parent_development_v5_consensus.md:37,209`). A
caller-set Boolean cannot prove that property. Parent language can be copied,
lightly paraphrased, or statistically distilled into a child's restatement.
In `classroom_round.py:200-235`, a parent correction is supplied to the child,
and the child's restatement becomes a `kind="note"`; those notes are later
written as response targets (`:270-290`). That can be scientifically intended,
but its ancestry and mask boundary must be explicit.

**Required repair:** corpus rows must carry immutable source-span roles and a
tokenizer-bound loss mask. The compiler must derive the mask; callers cannot
assert it. The trainer must reject `q`/`a`-only rows and verify that no parent,
exam, final, harness outcome, or other forbidden span receives response loss.
Paraphrased child restatements retain the parent/evidence ancestry even when
their target tokens are permitted.

### 7. The registry is an uncounted fourth control plane

All three objects depend on resolving immutable records, evidence, policies,
domains, decision scopes, and authorized heads, but the registry's storage,
authorization, append-only semantics, recovery, replication, and lookup
consistency are absent. Therefore the design is not three control objects.
Its security property rests on an unspecified fourth system plus an
unspecified execution sandbox and release service.

**Required repair:** either specify and ratify those systems or reduce the
claim to tamper-evident bookkeeping. Do not claim fail-closed information-flow
enforcement until the registry, capability boundary, and release principal are
part of the exact reviewed bytes.

## Entry-point audit: required guard placement

The proposed phrase “call it directly from every entry point” is not a coverage
proof. Within the three inspected modules, the following checks must be
explicit and must fail before the listed operation. Lower-level modules and
other commands were outside this source boundary, so a complete repository
entry-point inventory remains separately required.

| Entry point | First irreversible or information-revealing operation | Required precondition and postcondition |
|---|---|---|
| `classroom_round.main` common path (`:170-172`) | Create round dir, resolve snapshot by markers, construct `RuleGame` | Validate authorized clean head, phase descriptor, domain/partition, exact snapshot, and isolated output capability before all three operations. |
| classroom live (`:177-261`) | Load child; open global parent ledger; expose hidden answer to remote parent; rewrite playbook | Bind child/parent/config/session and exact dispatch set; isolate branch writes; validate every evidence event; reducer alone may CAS the permitted notebook fields. |
| classroom sleep (`:270-324`) | Read receipts/ledgers/old corpora; write corpus; launch trainer | Require exact committed-head ancestry and row/span provenance; exclude rejected rounds; trainer independently verifies capability; corpus+adapter+optimizer+brief/state commit together or none do. |
| classroom exam (`:331-368`) | Load candidate and release probe tasks; rename adapter marker; write results in round root | Fork an exam receipt first; isolate results; apply the role-specific aggregate-return rule; promotion consumes the exact exam receipt and atomically binds the corpus. |
| `bootstrap_corpus.main` (`:155-205`) | Create output; read ledgers; select wins; contact author; select a second contrast episode | Validate all ledgers and output root before author access; record every selected and rejected episode plus both contrast sources; bind author model/session/request/response. |
| bootstrap serialization (`:228-238`) | Write path-only metadata and a `q`/`a` trainer corpus | Preserve dependency IDs, exposure roles, span provenance, recipe/config, author response IDs, and masks in the trainer-consumed artifact. A richer sidecar is not binding. |
| `run_life_v2.main` start (`:106-124`) | Create/reuse life dir; instantiate CompilerGym; enumerate programs; select latest adapter | Validate birth/head/role/descriptor and output namespace before gym construction; load only the head's exact adapter. |
| life resume/brief (`:126-164`) | Scan arbitrary sleep dirs, briefs, probes, and names | Read only artifacts reachable from the committed head and exact decision schedule; reject stale, extra, rejected, future, or unrecorded files. |
| probe/gate/plasticity (`:166-207`, `:294-303`) | Reuse cached metrics; select floor; change LR | Require descriptor+candidate+head hashes on every result; record the complete inspected set; permit feedback only for a ratified development scope; sealed-final results never enter. |
| sleep/parent/train/promote (`:231-291`) | Scan prior corpus; compile; update parent brief; launch trainer; rename marker | One transaction must bind exact evidence, previous head, corpus, adapter, optimizer, parent-state effects, briefs, gates, and decision. Rejection quarantines all candidate-derived outputs. |
| direct trainer/compiler/parent/model helper invocation | Bypass the three CLI wrappers | Each sensitive lower-level operation requires a one-use authorized execution capability and revalidates inputs. A wrapper-only check is insufficient. |

There is no distinct sealed-final runner in the inspected code. `run_life_v2`
mixes wake, CompilerGym probes, SLEEP, promotion, parent brief, and adaptive LR
in one persistent root. It must not be relabeled as a disposable final runner;
a separate authorized path with no clean return edge is required.

## Existing rule versus new material design

The supplied sources support retaining these immediate restrictions without
waiting for a new guard architecture:

- `R2_B_seed3`/seed 303 and its derivatives are ineligible for a later clean
  CompilerGym child, parent, bootstrap, selection, or from-scratch claim
  (`20260910_compilergym_bootstrap_quarantine.md:5-29`).
- A clean Stage-1 bootstrap is target-blind to the final gym, and the birth
  manifest identifies exact base, sources, parent history, mechanism, and
  exposure (`:32-40`).
- The final gym is visited only by one-way disposable descendants; the
  confirmatory experiment restarts from a sealed clean stage after mechanism
  and policy freeze (`:42-44`).

The v5 document is explicitly an “exact proposal for human ratification,” not
proof that ratification occurred (`adaptive_parent_development_v5_consensus.md:5-7`).
It supplies a coherent proposed basis for transaction rollback, immutable
parent configuration, developmental aggregate codes, root-local final
updates, and exact hashes, but this source-only review cannot call those bytes
ratified.

The following v1 choices are not compelled by the supplied quarantine note and
are material or at least require exact implementation adjudication:

- the universal registry and its artifact taxonomy;
- the global `information_class`/taint lattice and all unknown-input rules;
- the exact head and evaluation state machines;
- all-decision `SELECTION_RECEIPT`s and their eligible scopes;
- release groups, all-root barriers, retry behavior, and human-access policy;
- domain/partition identity and disjointness certificates;
- the blanket classification of all R2/R3/R4/RP/R_B/L_B and `lineage3_*`
  artifacts, which is not established by the supplied quarantine note; and
- the cross-lineage merge prohibition and sibling-fork semantics beyond the
  exact cases stated in v5.

Some of these may be prudent. Prudence is not prior ratification. They alter
information visibility, eligible evidence, acceptance tests, or the
scientific topology and must follow `AGENTS.md` before implementation.

## Minimum adequate re-scope

Do not implement the universal v1 system under a non-material-repair label. A
smaller first enforcement packet can be deliberated around four already
motivated boundaries:

1. an authenticated deny/quarantine registry for known CompilerGym-derived
   artifacts plus an exact clean-birth manifest;
2. one serialized accepted-state pointer binding the previous head, child
   adapter, cumulative provenance-preserving corpus, and any parent state;
3. a corpus/trainer contract with complete source edges and tokenizer-bound
   response masks; and
4. a separate disposable CompilerGym evaluation process with OS-enforced
   read/write isolation and an append-only, blinded release path.

If general use-relative IFC, remote-parent isolation, development-result
declassification, or human/scheduler blinding is desired, deliberate it as a
material second layer. The stronger design may be justified, but it must have
an honest system boundary and claim.

## Required adversarial tests before approval

Every denial must occur before task release, model/tokenizer/author loading,
or mutation of a clean/canonical root. Every test must assert the old head and
parent state remain byte-identical and that all attempted outputs are absent
or quarantined.

| ID | Attack | Required result |
|---|---|---|
| AR01 | Producer reads a tainted file but omits it from `input_artifact_ids`. | Capability/execution-closure mismatch denies output; a self-consistent manifest is insufficient. |
| AR02 | Producer reads tainted data through env, stdin, network, remote-session memory, cache, or an inherited file descriptor. | Undeclared channel is unavailable or makes output ineligible. |
| AR03 | Evidence event is final-tainted while all artifact inputs claim clean. | Evidence edge propagates final taint and denies return. |
| AR04 | Bootstrap contrast names only the primary episode and omits the randomly selected second episode. | Serialization fails before author output becomes eligible. |
| AR05 | Trainer receives the current `q`/`a`-only bootstrap corpus while provenance exists only in a sidecar. | Trainer rejects it. |
| AR06 | Parent text, paraphrase, harness outcome, or final summary is assigned response loss by a false `parent_text_targeted=false`. | Derived span mask disagrees; compile/train denied. |
| AR07 | A clean-looking mechanism is chosen after an unrecorded final result, failed candidate, early stop, or human inspection. | Missing execution/decision closure prevents head sealing. |
| AR08 | Retry/root/seed/schedule is changed using score, runtime, exit status, output size, or missing-file signal. | Blinded prebound scheduler denies the change and exposes no score-correlated detail. |
| AR09 | A preregistered developmental-exam aggregate updates exactly one allowed parent field. | Positive path succeeds through the named declassifier; raw rows/text cannot return. |
| AR10 | The same aggregate or any sealed-final aggregate targets child corpus, mechanism, prompt, LR, schedule, or an unapproved parent field. | Denied transitively. |
| AR11 | Two promoters race from the same generation. | Exactly one conditional update succeeds; the loser cannot overwrite it. |
| AR12 | Crash after each registry/artifact/journal/pointer durability boundary. | Recovery exposes either the exact old head or exact new head, never a mixed or unregistered head. |
| AR13 | Evaluation receipt changes state or output IDs without a new linked immutable event. | Mutation rejected; audit history remains complete. |
| AR14 | Payload changes between verification and model/trainer open, including symlink or rename swap. | Same immutable object is consumed or execution aborts. |
| AR15 | A stale `probe_gate` file/tag from another candidate or head is present. | Descriptor/candidate/head mismatch denies cache reuse. |
| AR16 | Rejected sleep corpus, adapter, optimizer, gate, waking brief, or parent brief is lexically newest. | None is reachable from resume, wake, compile, parent update, or selection. |
| AR17 | Domain/partition is relabeled or overlaps the final set under another ID. | Authenticated partition/disjointness proof fails closed. |
| AR18 | Direct trainer, compiler, parent updater, or evaluator is invoked without a one-use authorized capability. | It fails before reading protected inputs or writing outputs. |
| AR19 | Remote parent/author retains state across roots despite identical payload hashes. | Session-isolation proof fails; output is ineligible. |
| AR20 | Release visibility changes after final completion. | Report access may change; source artifact eligibility and every clean head remain unchanged. |

Positive tests must cover: clean target-blind evidence; a complete accepted
SLEEP transaction; rejection with exact rollback of corpus, adapter, parent,
and briefs; the narrow developmental aggregate return if ratified; and two
final roots reading one sealed snapshot while writing to distinct quarantine
roots.

## Disposition

Keep the known CompilerGym artifacts quarantined now. Before any guard
implementation, produce a new exact proposal that (1) defines the actual
enforcement boundary, (2) resolves the role-relative eligibility and
developmental-exam contradiction, (3) specifies immutable/authenticated
identity and real conditional promotion, (4) binds every relevant entry point,
and (5) clearly marks each new visibility/test/scientific choice for human
ratification. After implementation, `AGENTS.md` still requires fresh
independent review and an author-side scientific advocate before any GPU or
scientific-claim gate.
