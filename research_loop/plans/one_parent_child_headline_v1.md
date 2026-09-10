# One-parent/one-child headline protocol v1

Date: 2026-09-06

Status: **proposal only**. This document authorizes no implementation, task
generation, model/tokenizer call, adapter fit, GPU use, external access, or
scientific claim. It is the candidate input to the required architecture
deliberation and exact-byte human ratification workflow.

## 1. Question and scope

The paper asks one bounded question:

> Can one target-blind parent teach one child an evidence-responsive way of
> thinking that increases the benefit of that child's later personal
> Think--Dream--Sleep writes after the parent has disappeared?

There is no classroom, cohort, peer exchange, teacher ensemble, or population
learning mechanism. Independent roots are sealed replications of the same
one-parent/one-child protocol, not children learning from one another.

One treatment dyad contains exactly one parent and one parented child. The U
branch inside the same statistical root is an isolated counterfactual child
used only for causal estimation; it never observes, communicates with, or
exchanges state with the dyad.

The architecture contains one frozen child base model, one continuous
inference operation, one active per-life LoRA, one append-only causal ledger,
and three verbs:

- **THINK** changes the live trace by deliberating and making native typed
  tool calls.
- **DREAM** is the same model publishing a smaller, reversible successor
  conscious state when context pressure requires reconciliation.
- **SLEEP** has deterministic selection/render/gating around a seeded,
  receipt-bound LoRA optimization and transactional commit. It changes the one
  active LoRA; it is not another model or intelligence.

## 2. Causal object and public two-agent story

Each independent root begins from one pinned child checkpoint and creates two
isolated childhood branches:

```text
P childhood: own practice -> one parent process correction -> child applies
             -> public-world admission -> childhood LoRA write

U childhood: matched own practice -> no parent correction -> child self-reviews
             -> same public-world admission -> matched childhood LoRA write
```

Each childhood checkpoint is then byte-identically forked at deployment:

| childhood checkpoint | deployment writes off | deployment writes on |
|---|---|---|
| unparented, dose-matched practice-written | `U0` | `U1` |
| parented, dose-matched practice-written | `P0` | `P1` |

`U0` is not a pristine raw model. It is the dose-matched unparented control
needed to isolate parental information from nursery practice, optimizer
exposure, and self-generated training. A fifth **fit-free raw frozen
actor**, `R0`, receives the same deployment resource layer, including the
frozen `ACTIVE_TEXT_FIXED` updater in Section 11. The complete `R0` system is
therefore a **frozen-parameter active-memory reference**, not a raw or never-
learning system. The public two-agent figure is `P1` versus `R0`; parenting
causality comes only from the `P/U` factorial.

All five deployment services retain the same ordinary resources: child base,
tools, skills, files, the isolated evolving `ACTIVE_TEXT_FIXED` store, context
limit, clock, token budget, task opportunities, and public outcomes. Writes-
off means personal parametric writes off, not thought, dreaming, files, or
external-memory adaptation off.

## 3. Frozen parent recommendation

The confirmatory parent candidate is pinned
`Qwen/Qwen2.5-32B-Instruct@5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`
with greedy constrained decoding, no tools, network, repository, compiler
material, cross-child state, or deployment access. The child candidate is
`Qwen/Qwen2.5-7B-Instruct@a09a35458c702b33eeacc393d103063234e8bc28`
plus its one life-LoRA.

Codex- or Rohin-authored feedback may be used only on explicitly labeled
development children to improve the closed curriculum and interface. It is
never pooled with confirmation. A later Rohin-parented child is a valuable
registered mechanistic case study unless Rohin supplies the same blinded,
frozen protocol across every independent root.

Parent identity remains a human-ratification field. No parent may be called
before that identity and its exact policy bytes are ratified.

## 4. Minimal shared birth state

The byte-identical shared bootstrap contains only:

- public task objective and metric;
- offered typed tools and their effectful/prose boundary;
- generated-token budget and clock;
- common files plus the exact `ACTIVE_TEXT_FIXED` interface in Section 11; and
- a generic request to solve the task efficiently.

It must not command prediction, surprise handling, hypothesis discrimination,
belief scoping, diversification, recall, distillation, hill-climbing, or
single-factor mutation, and it must contain no example action. Those are
candidate treatment effects, not neutral instructions.

## 5. Target-blind nursery

Use two generated non-compiler families, disjoint from LLVM in ontology,
tools, actions, entities, and reward mechanics.

### 5.1 Nonce Codebreaker

A secret length-four code is drawn from six episode-nonce symbols with
repetition (`6^4=1296` hypotheses). `inspect_pattern` returns exact-position
and misplaced-symbol counts; `commit_pattern` submits a final code. Each
episode independently permutes symbols and tool handles. The harness can
score whether a child-chosen query separates two child-authored live
hypotheses without revealing the secret.

### 5.2 Nonce RuleShift

The child assigns cards with three nonce-valued attributes to three nonce
bins. Public feedback is correct/incorrect plus cumulative score. A hidden
rule from a finite registered family changes once after a registered trial;
at least one post-change result occurs before review. Every episode permutes
attributes, values, bins, rule, and change point.

Both generators require deterministic CPU audits for reset identity,
identifiability, answer collision, legal-action closure, process-predicate
computability, base-model headroom, and development-only action diversity
before any scientific instance is sealed.

## 6. Childhood schedule and correction surface

Use `J=3` childhood write cycles and four opportunities per cycle: two
Codebreaker and two RuleShift. Every opportunity contains one source attempt
and one fresh homologous application task. Thus each branch receives 12
review opportunities and 24 unique nursery task instances; the P branch has
at most 12 parent decisions. No successful child, correction, or write may be
replaced after inclusion.

The parent can select only one of three fixed process lessons, citing earlier
public event IDs:

1. `PREDICT_UPDATE`: make one falsifiable public prediction; after violation,
   identify and narrow one causal assumption before the next action.
2. `DISCRIMINATE`: retain two live explanations and choose a legal action,
   without being given it, whose public outcomes would separate them.
3. `SCOPE`: keep a belief local until distinct public tasks support promotion;
   narrow it after contrary evidence.

Otherwise it emits `NO_CORRECTION`. The parent output is a closed object with
`lesson_code`, earlier `evidence_event_ids`, fixed `template_version`, and
`answer_content: NONE`. It cannot free-write strategy, name an entity, choose
an action, or insert a number other than an evidence ID. The harness renders
the ratified lesson bytes.

The U child receives the same tasks, budgets, dream opportunities, fit count,
rank, optimizer ceiling, and common anchors. Parent slots are replaced with
presealed neutral role/token-matched inputs; U writes only its own supported
continuations and never receives P targets.

### 6.1 Disposition of conflicting source recommendations

| variable | transfer advisory | resource advisory | selected candidate | reason |
|---|---:|---:|---:|---|
| childhood write cycles | 3 | 4 | **3** | three parameter commits show compounding while reducing fit lifecycle cost |
| opportunities/cycle | 4 | 1 | **4** | twelve corrections provide actual teaching dose across both task families; four total corrections is too weak for the requested parenting test |
| maximum parent decisions | 12 | 4 | **12** | follows the selected teaching dose; `NO_CORRECTION` remains an observed decision |
| unique nursery tasks/branch | 24 | 8 | **24** | every correction is tested on a distinct homologous application task |
| deployment programs | 64 | 48 | **48** | preserves three write eras and four curve points while fitting the submission-critical resource envelope |
| maximum confirmation roots | 32 | 48 | **32** | the current lease cannot support a defensible 48-root path before the abstract; variance above the 32-root band stops the powered claim |

This is an explicit scientific/resource trade rather than an assertion that
the hybrid appeared in either source advisory. External deliberation may
reject it, but implementation may not silently change any selected byte.

## 7. Public-world admission

Eligibility and all three process predicates are bound before the parent
speaks. Parenting cannot create its own evaluation rule. P and U use the same
treatment-independent absolute row-admission law. For each P opportunity,
also fork a read-only neutral shadow from the same checkpoint and task state
before showing feedback. The shadow receives a frozen neutral continuation
and is never trained or visible to the parent. It diagnoses whether parenting
changed the child continuation; it is not a different P-only definition of a
learnable row.

A P or U child target is positive only if:

1. the pre-feedback trace satisfies the code-specific prospective trigger;
2. the complete native prompt/response/action/reset/outcome provenance chain
   is immutable;
3. the child's continuation satisfies at least one frozen process predicate,
   selected offline by the same fixed priority rule in P and U;
4. its same-budget public utility is within the frozen absolute task-family
   support/non-inferiority guard;
5. on a new homologous task, with parent absent, the child again satisfies the
   process predicate and utility guard; and
6. parent, restatement, and target pass the deterministic closed-schema,
   capability, namespace, and lexical answer/content firewall whose policy was
   semantically attacked before scientific traces existed.

For attribution only, a P correction is counted as `PARENT_SUPPORTED` when the
parent-selected code is prospectively eligible, its specific predicate passes,
and the neutral shadow fails it or loses by the registered discrete margin.
This tag is reported but does not change the absolute writer rule. U receives
no semantic lesson: after its frozen neutral self-review, the offline reducer
evaluates all pre-registered predicates in the same priority order.

Failed advice remains a rejected ledger event and supplies no positive label
unless the child's continuation independently clears the same absolute law
that applies to U; such a row is tagged `SELF_SUPPORTED`, never credited to
the parent.
The hidden task definition is available only to the offline admission reducer
after parent/child outputs are immutable and has no edge back into life.

The live content firewall is deterministic: closed schemas, capability roots,
task-namespace separation, and a ratified lexical denylist. Independent human
or model reviewers may attack the frozen parent policy and development
fixtures before scientific traces exist, but no semantic reviewer makes
per-row admission decisions inside SLEEP.

## 8. Conscious state and DREAM

THINK is an ordinary free model stream with a separate native typed-action
channel. Every generation is persisted before parsing with exact message JSON,
rendered bytes and IDs, raw assistant text, native tool envelope, generation
parameters/seed, parsed call, dispatch, reset identity, public result, score,
and causal offsets.

DREAM is learned context management, not a hard-coded summary. The child may
request `RECONCILE_CONTEXT`; the harness also requires it at a treatment-
neutral ratified token-pressure threshold. There is exactly one DREAM
opportunity per nursery review opportunity and one per 16-program deployment
era/service. An early request consumes and replaces that scheduled opportunity;
it never adds a call. There is no retry. A failed dream consumes the
opportunity and leaves the predecessor context active. The same model
publishes one typed `SUCCESSOR_STATE` containing working focus, scoped/statused beliefs with
ledger citations, open surprises, next plan, and recall handles. Goal, metric,
clock, budget, best public result, and tool state are immutable harness fields.

Each deployment era reserves the final ordinary continuation inside programs
16, 32, and 48. If that era's DREAM opportunity has not already been consumed,
the scheduled DREAM occurs immediately before this reserved continuation, and
that continuation is the post-reset support test. If an early DREAM consumed
the opportunity, its own next ordinary continuation is the support test and the
reserved continuation remains ordinary wake work. The reserved continuation is
inside the program's existing 12-call/2,048-generated-token allocation; it adds
no call, token, action, target slot, or probe exposure. Thus even the terminal
era's DREAM is followed by real non-probe life before the parent-free life ends.

Before old context/KV is dropped, the successor must pass schema/size,
evidence existence, open-surprise accounting, observation fidelity, legal
plan, omitted-fact restoration through a recall handle, and one legal
post-reset pre-outcome action. Failure preserves the predecessor pointer.
Every raw trace remains in the append-only ledger, so context deletion is
reversible. If a second overflow occurs after the era's opportunity is spent,
the harness performs one deterministic emergency reset to immutable fields,
the last validated successor, and ledger handles; the current task receives
the registered failure value and `CONTEXT_FAILURE`, and no bytes from that
fallback are trainable. This keeps the call ceiling closed without pretending
that emergency truncation is successful learned context management.

A syntactically valid successor is not automatically a positive target. Its
next ordinary post-reset continuation must also pass a prospectively frozen
process predicate and the environment-specific absolute support/non-inferiority
guard: the registered Codebreaker/RuleShift guard in childhood or the separate
CompilerGym guard in Section 11. This continuation is already inside
the task allocation; it does not create another model call or shadow.

## 9. SLEEP writer

SLEEP contains no inference intelligence. Its provenance closure, admission,
row rendering, and transactional gates are deterministic; they surround a
seeded, receipt-bound LoRA optimization whose reproducibility tolerance must
be established by the neutral writer canary. The compiler itself makes zero
language-model calls.

Only two child-generated target types exist:

- `THINK_TO_ACT`: the exact child pre-outcome assistant continuation and
  native typed tool-call envelope through EOS; and
- `DREAM_STATE`: the exact validated native `SUCCESSOR_STATE` response through
  EOS.

Parent text, lesson code, child restatement, task/tool results, outcomes,
scores, recalled ledger, old history, and prompts are masked inputs. Loss is
only on the complete child target suffix plus EOS. Zero labels, missing EOS,
target truncation, nonfinite loss, skipped batch, template mismatch, or target-
ID mismatch abort the entire candidate fit.

At most one earliest-ledger-order `THINK_TO_ACT` target and one earliest-
ledger-order `DREAM_STATE` target are eligible per opportunity. Each complete
target, including EOS, is at most 256 tokens; a longer target is rejected, not
truncated. Every scientific, rehearsal, and anchor response suffix, including
EOS, is at most 256 tokens; an overlength suffix is ineligible rather than
truncated. Every admitted target receives exactly four supervised-token
exposures per cumulative childhood fit with prospective scaffold fading:

| fit | parent text | child restatement | neutral cue | ordinary state |
|---|---:|---:|---:|---:|
| sleep 1 | 2 | 1 | 1 | 0 |
| sleep 2 | 1 | 1 | 1 | 1 |
| sleep 3/final childhood | 0 | 1 | 1 | 2 |

The response bytes remain identical across scaffold variants; only masked
conditioning changes. The final fit is predominantly parent-absent.

The writer uses a fixed prospective slot schedule. Every nursery opportunity
has at most one `THINK_TO_ACT` slot and one `DREAM_STATE` slot. Every deployment
program has at most one `THINK_TO_ACT` slot, and every 16-program era has at
most one `DREAM_STATE` slot. The earliest absolute-law-eligible ledger event of
the required type fills the slot. An empty slot is filled only with the common
presealed task-disjoint native rehearsal pool; invented success never fills it.

All accepted childhood slots remain in every later cumulative clean-base
rebuild. Deployment slots accumulate through the current cut. Every treatment
or rehearsal target receives exactly four supervised-token exposures. The
position schedule per branch is therefore:

```text
childhood sleep j: 4 * (8*j childhood target slots) + 20 anchors
                   = 52, 84, 116 positions for j=1,2,3
deployment cut k:  4 * (24 childhood + 16*k wake + k dream slots) + 20 anchors
                   = 184, 252, 320 positions for k=1,2,3
```

The same 20 anchor positions occur in every fit; deterministic rehearsal rows
fill any empty scientific slots so paired P/U writers have identical position,
slot-weight, and optimizer-step counts at the same cycle/cut. Loss is averaged
within each response suffix and then across slots, so variable child response
length does not grant a larger objective weight; actual labeled tokens remain
a reported resource rather than a causal dose claim. Formally, for optimizer
positions `p=1..P` with response-token suffix `Y_p`, including each repeated
exposure and anchor as its own fixed position,

```text
ell_p = -(1/|Y_p|) * sum_{y in Y_p} log p_theta(y | masked conditioning, y_<)
L = (1/P) * sum_{p=1..P} ell_p.
```

No token-, row-, target-type-, or treatment-dependent reweighting is allowed.
With target
suffixes capped at 256 tokens and complete sequences capped at 2,048, the
terminal writer is bounded by 320 optimizer positions, 81,920 labeled tokens,
and 655,360 attended tokens. Any target longer than 256 tokens is ineligible,
never truncated. If multiple events qualify for one slot, earliest immutable
ledger ordinal wins. Selection cannot use arm, parent-attribution tag, score
magnitude, probe value, or later behavior.

The target-blind rehearsal reservoir is sealed before root generation, is
large enough to supply every possible empty slot through the terminal
320-position schedule, and is bucketed by exact response-token length and
native target type. An empty scientific slot maps by `(cycle_or_cut,
target_type, slot_ordinal)` to one fixed rehearsal row and loss weight; it does
not sample based on treatment yield. Padding is reported separately and never
described as supported experience.

Every trained cell receives the same target-blind native anchor packet:
schema-valid disjoint tool calls, free deliberation, valid successor state,
recall after replacement, and clean stop. After every fit, strict typed
dispatch, action cardinality, dream/recall routing, and generic quality must
remain within frozen non-erasure margins. A failed candidate is quarantined
and the previous adapter remains active; the parser is never relaxed.

There is exactly one rank-8 all-layer life-LoRA (attention plus MLP, alpha 16,
dropout 0). Every checkpoint is a cumulative clean-base rebuild; adapters and
optimizers are never stacked. Rank 16 is a later diagnostic, not a rescue.

## 10. Treatment-neutral writer calibration and teachability gate

Before parenting targets exist, race exactly three learning rates
`{1e-6,1e-5,3e-5}` at the same four supervised-token exposures used by the
scientific scaffold ladder, on a parent-free, target-free native writer
packet with the terminal 320-position/81,920-label-token geometry. Select the
lowest passing learning rate. Passing requires increased native-suffix
likelihood plus preservation of strict action routing, typed-forced proposal
quality, dream/restoration, and generic behavior on a frozen 24-prompt panel;
duplicate the selected fit. No passing cell means writer NO-GO.

The calibration receipt must also show fit-start-to-hashed-checkpoint p95 at
most ten minutes and serving-shutdown-through-fresh-mount/canary p95 at most 15
minutes, with zero skipped/nonfinite updates. These are hard promotion gates,
not retry permissions.

Then run the bounded four-root teachability canary from the independent writer
advisory with this repaired calibration. It is capped at 18 small fits, 1,032 logical calls, and 528,384
generated tokens. Required cells are authentic parenting/fading, authentic
target-only conditioning, state-target derangement, independently generated
unparented self-experience, adapter-off, and pre-write checkpoint. Roots are
pre-parent eligible and cannot be selected or replaced on success. This canary
is a spending gate, not inferential evidence.

The 18-fit ceiling is four neutral calibration fits (three heat cells plus one
duplicate), eight fits across the first two technical roots, and six fits
across two gated expansion roots.

## 11. Deployment

After a fresh-process deletion audit removes the parent service, feedback,
restatements, nursery tasks/ledger/state, optimizer, rehearsal corpus, serving
cache, and every unapproved repository/compiler edge, deploy on CompilerGym:

- 48 unique wake programs per root, no within-life repeats;
- personal writes after programs 16, 32, and 48;
- eight sealed forward-transfer probe programs at entry and after each cut;
- no probe output, score, memory, or response re-enters life;
- equal generated-token allocations, with actions unmetered except a high
  fail-safe operation maximum of one native action envelope per ordinary
  continuation and therefore at most twelve dispatched actions/program; and
- counter-keyed common RNG opportunities rather than one shifting global RNG.

The per-program allocation is selected once on a development-only base-model
saturation curve as the smallest budget reaching at least 90% of its observed
within-program asymptote, with 2,048 generated tokens as the hard candidate
maximum. The selected byte value is sealed before spending-pilot identities.

### 11.1 Common strong active-text memory

Every service owns an isolated `ACTIVE_TEXT_FIXED` store. This is a common
deployment affordance and strong external-memory comparator, not DREAM, SLEEP,
a parent, or a shared store. It contains the unbounded append-only public
ledger plus an incrementally edited typed playbook. The complete field-level
schemas, legal delta/status transitions, canonical JSON bytes, semantic
relations, exact prompt/query/render bytes, BGE prefix and tokenization,
embedding cadence, actor insertion bytes, and once-only certificate law are
controlled by `research_loop/plans/active_text_fixed_contract_v1.md`. The
updater never writes unconstrained prose into the store: it chooses typed
scope, proposition, guidance, evidence, relation, and status fields, and a
deterministic renderer supplies actor-visible structure. A mismatch between
this summary and that contract blocks execution rather than permitting a local
interpretation.

After each of the 48 deployment programs, the pinned adapter-free child base
at the Section-3 revision makes at most two greedy, no-tool calls. `REFLECT` receives
only that service's public deployment trace through the current program and
identifies reusable successes, failures, contradictions, and scope changes in
at most 512 output tokens under the exact closed schema. Only when `REFLECT`
is valid, `CURATE` receives that accepted model-produced object and emits at
most four exact
`ADD | REVISE | LINK | SUPERSEDE | NOOP` deltas in at most 384 output tokens.
A complete emitted record is at most 256 tokens. The deterministic merger
checks canonical schema, identifier/source existence, chronology, exact prior
hashes, legal transitions, and the contract's public-event semantic table. It
never receives or judges hidden task truth. Malformed, semantically unsupported,
or overflowing outputs remain failed audit events, make no update, and cannot
exclude or replace a root. Before the second call, the merger constructs the
exact complete prescribed canonical `CURATE` object. If the required input
partitions do not fit, it records `INPUT_OVERFLOW`. Otherwise it simulates the
complete finalized store transition, including deterministic IDs, evidence
unions, links, sorting, provenance, hashes, array bounds, and final stored-
record token length; an impossible commit records
`TRANSITION_UNREPRESENTABLE`. Only then, if the exact response suffix plus one
pinned EOS token would exceed 384 pinned-tokenizer tokens, it records
`OUTPUT_UNREPRESENTABLE`. Any event skips `CURATE`, preserves and
scores the valid `REFLECT`, leaves memory unchanged, and forbids truncating or
dropping a prescribed delta, citation, link, or field.

Updater visibility is closed. It may receive current-service public assistant
messages, native actions, public outcomes, clock, and program-local score
events; deterministic retrievals from that same service's prior ledger and
playbook; and, for `CURATE`, its immediately preceding valid `REFLECT` object.
It never receives parent output, nursery material, rehearsal/anchor rows,
writer decisions, adapter parameters/logits, probes, future events, another
service/root, hidden compiler state, offline truth, reporter output, or a
semantic review. Every rendered byte range and source event ID is receipted.

`REFLECT` has a 10,240-input-token hard cap under the pinned child tokenizer:
4,096 fixed instruction/schema tokens, 256 goal/metric/clock tokens, 2,560
tokens for the typed current-program causal spine, 1,536 tokens for complete
raw assistant events, 1,024 tokens for prior retrieved documents, and 768
reserved template/boundary tokens. Required causal-spine events are rendered
chronologically; if they exceed their partition, the call records
`INPUT_OVERFLOW` and cannot update. Raw assistant events are admitted newest-
first as complete events and then rendered chronologically; retrieved records
or event blocks are admitted in frozen rank order. No event, block, or record
is truncated.
`CURATE` has a 6,144-input-token hard cap: 4,096 fixed instruction/schema, 512
for `REFLECT`, 1,280 for complete cited source events and currently related
records in the supporting contract's block-then-record canonical order, and
256 for state/boundaries. A required
item that cannot fit causes `INPUT_OVERFLOW` and no update. There is no whole-
store fallback. The exact prescribed-output representability preflight in the
supporting contract and its finalized-transition feasibility preflight are
equally mandatory. Token lengths are measured only at the separately
authorized pinned-tokenizer gate; failure is a hard no-call/no-update event,
not permission to change the 384-token ceiling, relax a stored-record bound,
or reduce the delta list.
Before any updater execution, the pinned-tokenizer receipt must show that the
complete system message, schema file, calibration line, operation header, and
fixed chat-template/boundary bytes fit their 4,096-token fixed partition. If
not, this protocol version is NO-GO: it may not borrow evidence capacity,
truncate or summarize the visible laws, or spend scientific roots.

Before every ordinary actor continuation, retrieval uses the public objective,
metric, normalized families of the last two native actions, and latest public
outcome class as the exact four-line query in the supporting contract. Exactly
one identical updater-side retrieval is made before `REFLECT`; `CURATE` makes
no retrieval query. Lexical ranking is Robertson--Sparck Jones BM25
with `k1=1.2`, `b=.75`, corpus-local document frequencies, and Unicode-NFKC
lowercase tokens matching `[a-z0-9_+.-]+`. Dense ranking applies
`BAAI/bge-small-en-v1.5@5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
with its pinned tokenizer, the literal query prefix
`Represent this sentence for searching relevant passages: ` (including the
final ASCII space), attention-
mask mean pooling, float32 L2 normalization, and exact CPU cosine dot products;
playbook records enter both rankings and raw ledger event blocks enter BM25.
Reciprocal-rank fusion uses `1/(60+r_lex)+1/(60+r_dense)`, with a missing rank
contributing zero and ties broken by immutable memory/event ID. One-hop links
are expanded seed-rank first and linked-ID lexicographically. Duplicates are
removed by ID. The packer returns at most four complete records/event blocks
and at most 1,024 tokens, skipping rather than truncating a nonfitting item;
no hit returns an empty block. Model/tokenizer/config file hashes and the
tokenization/index arithmetic implementation are sealed before any model call.
No approximate index or nondeterministic nearest-neighbor library is allowed.
The supporting contract binds right-truncation behavior under the 512-token BGE
limit, full-record actor return, 4,160 actor/probe plus 240 `REFLECT` query
embeddings/root, zero `CURATE` query embeddings, and at most 960 newly embedded
or re-embedded live records/root. Its whole-file and extracted literal-byte
hashes plus ten model-free instantiated golden fixtures must seal before the
strength gate.

The mechanism must earn the word *strong* on fixtures disjoint from both
scientific roots and updater development before spending roots. The updater,
merger, prompts, exact bytes, and thresholds freeze after development; a
separately seeded certificate set is then scored once. The actual two-call
updater must achieve: (i) 100% citation/source existence, at least .95
mechanically recomputed semantic/evidence-faithfulness precision, at least .85
macro-F1 over typed update/status operations, and at least .80 recall of
presealed reusable records on 100 add/support/contradiction/scope/link/
supersession cases; (ii) at least .95 recall@4 with 100% returned-citation
validity over 100 exact, linked, and contradicted-record queries using both
actual-updater and oracle stores; (iii) at least .05 task-value gain for actual
updater-produced memory over append-only raw-ledger search on 24 target-blind
programs, while retrieval stays within .05 of direct injection of the same
updater-produced relevant records; and (iv) at least .05 oracle-playbook gain
over an empty store to certify environmental headroom. All semantic values are
typed and mechanically derived from cited public fixture events under the
supporting contract; no free prose is admitted or scored. All outputs seal
before offline scoring, and scores never return to the updater. A failed
certificate cannot be repaired and rescored on the same cases: repair creates
a new version and newly sealed certificate set while retaining the failure.
Failure permits only the label `ACTIVE_TEXT_NOT_STRONG`; it forbids strong-
baseline language, saturation language, and scientific-root tuning.

`ACTIVE_TEXT_FIXED` is an ACE/ReMem-style functional comparator, not an exact
reproduction of ACE, ReMem, ReasoningBank, or MemoPilot. Because its on-policy
content is downstream of prior actions, comparisons against it are closed-loop
total effects, not carrier-only or equal-memory contrasts.

### 11.2 Deployment LoRA writer law

Deployment uses a frozen absolute writer law in every cell. A program's
`THINK_TO_ACT` slot is eligible only for the earliest complete native child
response that (a) states a numeric prediction before a schema-valid dispatched
action, and (b) either produces the first registered positive incumbent
improvement or follows a registered expectation violation with a native typed
`REVISION` object and then produces a nonnegative recovery under the public
score. `REVISION` contains exactly `violated_prediction_event_id`,
`prior_assumption_id`, `new_assumption_id`, and `next_action_family`.
Admission is mechanical: the event ID must name an earlier same-program
numeric prediction whose registered public result crossed the frozen surprise
threshold; the prior and new assumption IDs must both name child-authored,
pre-outcome scoped assumptions in the immutable ledger and must differ bytewise
after canonical ID normalization; `next_action_family` must equal the family
of the subsequently dispatched recovery action and differ from the violated
action's normalized family. Missing links, reused IDs, family equality, or
mismatch with the native dispatch rejects the row. The validator never judges
prose, meaning, or correctness and uses no LLM or regex classifier. The
response target ends before the result. A deployment
`DREAM_STATE` slot is eligible only if its successor passes every restoration
gate and the next ordinary continuation satisfies the same action law without
regressing beyond the frozen public non-inferiority margin. Exact rational
score thresholds are sealed from development-only data before the spending
pilot. All cells compute the same would-be slots; only P1/U1 fit them.

`P0/P1` share exact parented entry bytes; `U0/U1` share exact unparented entry
bytes. `R0` uses raw pinned actor weights with the same active-memory resource
layer. Frozen-parameter cells still THINK, DREAM, act, keep files and evolve
their isolated textual memory, and construct would-be sleep rows; only
personal parametric fitting/commit is disabled.

## 12. Endpoint, roots, and statistics

At cuts `t={0,16,32,48}`, let `V_{c,r}(t)` be root `r`'s mean best
nonnegative held-out IR instruction reduction over the same eight sealed
programs and `G_{c,r}(t)=V_{c,r}(t)-V_{c,r}(0)`. Define

```text
gAUC_r(c) = [2*G_{c,r}(16) + 2*G_{c,r}(32) + G_{c,r}(48)] / 6.
D_r = [gAUC_r(P1)-gAUC_r(P0)] - [gAUC_r(U1)-gAUC_r(U0)].
C_active,r = gAUC_r(P1)-gAUC_r(P0).
C_public,r = gAUC_r(P1)-gAUC_r(R0).
```

The independent unit is the separately raised root, not a task, checkpoint,
action, target, sample, or adapter fit. Fixed-sequence inference tests `D`,
then `C_active`, then `C_public`; a failed rung stops higher superiority claims
but does not erase a passing lower rung. Each passing contrast requires a
positive two-sided 95% root-level Student-t interval, a point estimate at least
the registered `0.05` SESOI, and no typed-routing/proposal-quality erasure.
`D` is the primary parenting-of-learning estimand. `C_active` is the total
effect of enabling deployment LoRA writes in a parented agent already equipped
with the same frozen active-text mechanism; it includes the legitimate
mediated path through different later experience and store contents.
`C_public` is the full-package comparison with the frozen-parameter active-
memory reference and isolates no single component. Store yield/content is
never a root eligibility, matching, regression, or stratification variable.

Run two development roots and four spending-pilot roots, all excluded from
confirmation. The spending pilot advances only with zero provenance/resource
parity failures, positive `D_r` in at least three of four roots, and
`mean(D)>0`; it never requires `mean(D)>=0.05` and is not pooled.

Prebind 32 confirmation roots. After the first 12, a blinded reducer releases
only covariance, missingness, and one-sided 80% upper bounds on the SDs of
`D`, `C_active`, and `C_public`. Stop at 20 only if all contrasts intended for
powered claims have SD upper bounds at most 0.075; continue to 32 if all are at
most 0.10. A contrast above 0.10 loses its powered superiority claim without
erasing lower fixed-sequence rungs. Effect directions and arm means remain
hidden until N is locked.

“Saturation” is conditional and always names `P0+ACTIVE_TEXT_FIXED`, this
CompilerGym distribution, 48 programs, and the registered update/read budget.
For each root define `s1_r=V_{P0,r}(32)-V_{P0,r}(16)` and
`s2_r=V_{P0,r}(48)-V_{P0,r}(32)`. The same eight probe identities are paired across all
cuts. The local-plateau sentence is allowed only if: both separate two-sided
95% root-level Student-t intervals for mean `s1` and `s2` lie wholly inside
`[-.05,.05]` (a conservative at-least-90% simultaneous rule); a presealed,
cognition-hidden 10,000-sequence fixed-seed compiler search reference is at
least .10 above mean `V_{P0,r}(48)`; the one-sided 95% lower bound for mean
`V_{P1,r}(48)-V_{P1,r}(32)` is positive; and the one-sided 95% lower bound for
mean `[V_{P1,r}(48)-V_{P1,r}(32)]-[V_{P0,r}(48)-V_{P0,r}(32)]` is positive with point estimate at
least .05. Any missing paired cut, failed condition, or inadequate precision
forbids the word; report curves and resource frontiers instead. No extra root
may be added to rescue saturation.

## 13. Resource envelope

With `J=3` childhood fits per P and U branch and `K=3` deployment fits per P1
and U1, the four-cell causal surface costs `2J+2K=12` fits/root. R0 adds no fit.
The writer/heat canary costs at most 18 fits. Thus complete fit ceilings are:

```text
N=20 confirmation: 18 + 12*(2 development + 4 pilot + 20) = 330 fits
N=32 confirmation: 18 + 12*(2 development + 4 pilot + 32) = 474 fits
```

The hard per-root inference manifest is:

| class | instances | calls/instance | calls | output tokens |
|---|---:|---:|---:|---:|
| P/U nursery source units plus application tasks | `2*3*4*2=48` | 12 | 576 | 73,728 |
| P/U review/restatement | 24 | 1 | 24 | 4,608 |
| P/U nursery DREAM | 24 | 1 | 24 | 9,216 |
| P parent correction | 12 | 1 | 12 | 3,072 |
| five-service deployment wake | `5*48=240` | 12 | 2,880 | 491,520 |
| five-service `ACTIVE_TEXT_FIXED` update | `5*48=240` | 2 | 480 | 215,040 |
| five-service deployment DREAM | `5*3=15` | 1 | 15 | 11,520 |
| five-service probes | `5*4*8=160` | 8 | 1,280 | 163,840 |
| **strong-active-text total** | | | **5,291** | **972,544** |

For a P source unit, the 12-call/1,536-token aggregate includes the initial
attempt (4 calls/512 tokens), corrected continuation (4/512), and same-
checkpoint neutral shadow (4/512); the
separate homologous application task receives its own 12-call aggregate. The
U source unit allocates 4/512 to the initial attempt and 4/512 to its neutral
self-review continuation; the remaining 4/512 shadow capacity is burned rather
than generated or exposed. Each nursery or deployment DREAM
has the one-opportunity/no-retry rule in Section 8. Thus early dream requests,
neutral shadows, and failed dreams cannot enlarge this table. Development-only
budget-saturation and policy-audit calls are reported outside scientific root
costs.

Including P/U childhood, four-cell deployment, repeated R0 reference, and the
common active-memory mechanism, the hard per-root generation envelope is at
most 5,291 logical calls and 972,544 generated output tokens. This includes
three treatment-neutral context-reconciliation calls and 96 active-memory
update calls for R0; fit-free does not mean inference-free or memory-static.
Across development, excluded pilot, and confirmation, the ceilings are
137,566 calls and 25,286,144 output tokens for `N=20`, or 201,058 calls and
36,956,672 output tokens for `N=32`, plus the separately bounded writer canary
of 1,032 calls and 528,384 output tokens.

At the maximum registered active-memory read envelope, actor continuations can
receive at most 2,949,120 deployment-wake plus 1,310,720 probe-return tokens,
or 4,259,840 returned input tokens/root. Updater calls add at most 3,932,160
input tokens/root, for a combined active-memory input ceiling of 8,192,000.
Exact dense work is bounded by at most 4,400 query embeddings and 960 changed
live-record embeddings/root. BM25 work is bounded by 3,840 inserts and 960
removals/root (including at most 2,880 raw causal blocks); CPU dot products,
raw/store/index bytes,
latency, and energy/wall time are receipted. The development strength gate is
separate and hard-capped before its own execution at 2,000 model calls and
400,000 generated output tokens; the 10,000-sequence headroom reference uses
no model calls and reports compiler evaluations and CPU time.

The staged `LEAFE_STYLE_FINAL` comparator is optional and strictly
**descriptive/exploratory**. It may execute only after the headline root count,
`D`, `C_active`, and `C_public` artifacts are immutable. It never enters the
blinded variance rule, fixed-sequence hierarchy, root-count choice, or a
powered claim, and the paper cannot say that the system beats LEAFE. It reuses
each root's `P0` history: one maximum-256-output-token frozen diagnosis and one
maximum-512-output-token frozen recovery call at the earliest registered
failure/surprise point per program, one rollback dispatch, and the same eight
terminal probes (eight calls and 1,024 aggregate generated tokens per probe).
Its clean-base rank-8 fit uses the same 24 childhood slots, 20 fixed anchors,
48 branch slots, deterministic rehearsal fills for failed branches, and three
rehearsal-filled deployment-DREAM slots, all under the same four-exposure/
response-loss law. It adds at most 160 calls, 45,056 output tokens, 48 rollback
dispatches, and one fit/root. The descriptive terminal quantity
`C_batch=V_P1(48)-V_LEAFE_STYLE_FINAL(48)` compares complete bounded systems,
not periodic versus terminal timing alone; it is neither an exact LEAFE
reproduction nor a matched-history carrier test.

Before `P0` advances past any registered failure/surprise candidate, the
harness seals a content-addressed, read-only branch snapshot containing the
exact child checkpoint, rendered context and ledger prefix, environment state,
active-text store and both index states, retrieval-query fields, clock/budget,
RNG counters, and source/config hashes at that historical point. The later
descriptive comparator selects the earliest registered branch ID but loads only
that snapshot; diagnosis, recovery, rollback dispatch, and retrieval cannot see
subsequent `P0` events or terminal store content. Snapshot bytes/storage and
deduplication are receipted; creating them uses no model call and cannot alter
the live service.

Each diagnosis input is capped at 8,192 child-tokenizer tokens: 1,024 fixed
instruction/schema, 512 objective/metric/clock, 4,096 complete chronological
causal-spine events, 1,024 active-text retrieval, 1,024 complete raw assistant
events, and 512 boundaries. Each recovery input is capped at 4,096: 512 fixed
instruction/schema, 2,048 complete failure-spine events, 256 diagnosis, 768
active-text retrieval, and 512 task state/boundaries. A required causal event
that does not fit produces `INPUT_OVERFLOW`, no diagnosis/recovery row, and the
predeclared rehearsal fill; optional raw/retrieved items pack newest-first or
frozen-rank-first as appropriate, are finally rendered chronologically, and
are skipped rather than truncated. Across 48 programs this adds at most
589,824 diagnosis/recovery input tokens. Its 96 diagnosis/recovery retrievals
plus 64 terminal-probe retrievals add at most 160 query embeddings and 151,552
returned active-text tokens/root; it reuses only the selected historical `P0`
snapshot and creates zero updater calls or new record embeddings.

With that optional comparator, the full ceiling becomes 5,451 calls,
1,017,600 output tokens, and 13 fits/root: 141,726 calls, 26,457,600 output
tokens, and 356 total fits including the writer canary for the `N=20` route;
or 207,138 calls, 38,668,800 output tokens, and 512 fits for `N=32`.
These optional totals are descriptive resource ceilings, not a prospective
sample-size or superiority commitment.

These are safety ceilings, not expected use. Every root reports actual input/
output tokens, calls, actions, rollback/environment dispatches, embedding and
retrieval work, persistent bytes, engine dispatches, wall time, occupied GPU
time, accepted/rejected rows, labeled tokens, and fits.

Before confirmation, require a measured all-in p95/root and a compute receipt
that satisfies the frozen lease inequality plus 20%/12-hour reserve. Under the
current September 14 lease, N=20 is the only conservative route. N=32 requires
an extension or replacement compute through at least September 16. Existing
exploratory v6 jobs are never preempted or counted as available capacity.

## 14. Mandatory diagnostics, staged after the headline is safe

- exact childhood/deployment adapter-off;
- authentic parent versus independently generated unparented self-experience;
- state-target no-fixed-point derangement;
- free native action versus typed-forced proposal quality;
- common `ACTIVE_TEXT_FIXED` development strength certificate and its
  longitudinal `C_active` contrast;
- optional descriptive-only bounded `LEAFE_STYLE_FINAL` complete-system comparator;
- same-corpus active-text carrier; and
- optional terminal linked-carrier assay only after the headline artifacts
  are immutable.

A same-target parent-text sham tests scaffold dependence, not whether
parenting generated better child behavior. Equality after scaffold fading is
desirable. Wrong-child advice is not guaranteed to be a null because a general
thinking lesson may legitimately transfer.

## 15. Claim ladder and fail meanings

The evidence supports only the highest passing rung:

1. native writer changes a parent-absent interface habit without erasure;
2. parenting changes a target-blind disposition after all parent text is gone;
3. positive `gAUC(U1)-gAUC(U0)` establishes bounded unparented deployment-
   write efficacy;
4. positive registered `D` establishes that this parent protocol improved the
   later benefit of personal writes;
5. after rung 4, positive `C_active` establishes that deployment writes add
   bounded closed-loop value to a parented agent already carrying the frozen
   strong active-text mechanism;
6. after rung 5, positive `C_public` establishes greater deployment gain for
   the full developmental package than the frozen-parameter active-memory
   reference; and
7. a separate terminal assay may localize carrier mechanism, while the staged
   batch comparator supports only its explicitly bounded complete-system
   contrast.

A higher P entry score alone is inherited competence. A failed interaction is
not rescued by P1 versus R0. No result here establishes general creativity,
novel compiler discovery, populations, unbounded self-improvement, or physical-
world invention. It also establishes no universal external-memory replacement,
equal-compute win, intrinsic saturation, or named-method superiority.

## 16. Implementation surfaces after ratification

The present `organism_v6` code is exploratory and cannot be promoted. A new
namespace must implement:

1. canonical hash-chained typed event ledger and role capability roots;
2. native tool/action and exact tokenizer/template provenance;
3. Codebreaker and RuleShift generators, neutral shadow, and frozen admission
   predicates;
4. parent policy service and content firewall;
5. reversible successor-state context manager;
6. response-only sleep compiler, exact masks/receipts, cumulative rank-8
   trainer, anchors, and transactional commit;
7. isolated `ACTIVE_TEXT_FIXED` stores, closed updater inputs, exact merger,
   pinned BM25/BGE retrieval, development strength gates, and receipts;
8. P/U childhood runner, deletion audit, P0/P1/U0/U1/R0 deployment runner;
9. unique CompilerGym splitter, common-counter RNG, token accounting, and
   sealed probes; and
10. blinded root-level reducer, fixed-sequence contrasts, conditional plateau
    reducer, and artifact/figure manifest.

Every implementation stage requires deterministic synthetic CPU fixtures,
source-distinct validators, fresh hostile review, and the separate pre-GPU
gate required by `AGENTS.md`.
