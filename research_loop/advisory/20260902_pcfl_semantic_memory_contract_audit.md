# PCFL-Compose semantic-memory contract audit

**Date:** 2026-09-02  
**Status:** fresh read-only scientific design audit. This advisory does not
ratify the proposal, authorize implementation, models, GPUs, training,
networking, publication, or a scientific claim.

## Executive ruling

**Do not ratify the current semantic-memory bytes.** The chronology and
truth-blind ownership language are directionally consistent with the bound
advisories, but `semantic_dsl.schema.json` is not a semantic DSL. Its durable
unit is an unconstrained natural-language `claim` string plus a four-way tag.
That is a byte-preserved note, not the model-emitted semantic AST required by
the model-owned revision protocol.

This creates a hard dilemma:

1. If Sleep and the reader treat `claim` as opaque bytes, the memory cannot be
   exactly truth-scored, structurally retrieved, subjected to law/factor cuts,
   or converted into declared semantics-preserving LoRA views.
2. If any later component interprets the prose well enough to do those things,
   that component supplies an unregistered natural-language semantic parser.
   If it uses the known PCFL family, hidden factors, targets, or a language
   model, it is an offline semantic oracle and owns part of the intelligence.

The string can *describe* the hidden operator law in English, so it is
extensionally unconstrained enough to contain the answer. It cannot express
that law with a closed, decidable, family-neutral denotation. Therefore the
proposal cannot presently substantiate its own claims of semantic
conservation, atomic-reader sufficiency, record truth/coverage, wrong-order or
decisive-factor causality, or later identical-corpus LoRA transport.

The repair is not to add a smarter prose parser. Replace the active `claim`
with a small closed typed equational AST over public surface tokens and finite
operators. Let the model author every symbol, binding, ordered composition,
and rule. Sleep may validate and serialize that AST but may not solve it.
Free text may remain as a noncausal audit annotation excluded from the corpus,
index, cuts, semantic scores, and future training views.

## 1. Bound requirements used in this audit

The four bound advisories jointly require more than syntactic JSON validity:

- `20260902_model_owned_dream_revision_protocol.md` requires the model to emit
  the complete semantic AST, Sleep to add zero semantic nodes or consequences,
  false well-formed ASTs to compile identically, and any future LoRA view to be
  one-to-one and semantics-preserving.
- `20260902_sparse_factor_graph_math_audit.md` requires a fixed atomic record
  grammar, an itemwise minimum-read certificate, explicit noncommutative
  operand order, and decision-changing per-record forks. It identifies a
  gauge-fixed D4 access requirement of eight candidate-stem items, four suffix
  items, and one order relation: 13 local semantic items.
- `20260902_pcfl_dream_loop_granularity_audit.md` requires `NOTICE`, `CONNECT`,
  and `REVISE` to have explicit premises, committed records to have an acyclic
  provenance path to public events, and Dream/Think reader-state transitions
  to be mechanically defined rather than recovered from prose.
- `20260902_pcfl_paper_adjudication.md` requires a preregistered general
  predictive-operator DSL, an interpretation-neutral parser, an
  orientation-deleted arm, exact wrong-order and decisive-factor cuts, and
  later byte-identical text/LoRA corpus comparisons.

The current proposal adopts these requirements in prose but does not encode
the semantic object needed to execute or test them.

## 2. End-to-end audit of the present memory object

| Required operation | What the current files provide | Ruling |
|---|---|---|
| Parse | JSON parses `kind`, `claim`, citations, and uncertainty. The interior of `claim` has no grammar. | Only envelope parsing is possible. Calling the result a semantic AST is false. |
| Truth-score | A/B tray predictions can be scored exactly. A prose rule, local relation, exception, or unresolved claim has no registered denotation. | Record truth, law identity, factor coverage, and semantic precision/recall are undefined without a second interpreter. |
| Retrieve | Sleep proposes indexes from “literal public entity tokens, literal relation words, and time IDs”; Think emits an arbitrary string query. Tokenization, relation-word recognition, collisions, pagination, and result order are unspecified. | Exact local access and the 4/13 minimum-read certificate cannot be established. |
| Causally cut | Whole-memory counterpart exchange is byte-defined. Deleting “the orientation record,” reversing its order, or replacing one decisive binding requires locating and editing a meaning inside prose. | Generic SELF wrong-order and factor cuts are not mechanically defined. Any post-hoc semantic editor is an oracle. |
| Train later to LoRA | The current scope correctly excludes LoRA. No canonical AST-to-view map exists. | Verbatim prose SFT would be possible, but reverse/paraphrase/partial-cue views and identical semantic transport are not defined. A new ratified contract is required. |
| Express the hidden law | Arbitrary English can say anything. No typed operator literal, symbol definition, variable, equality, inverse, ordered composition, or action-surface constructor exists. | Informal expressivity is unlimited; operational, truth-conditional expressivity is absent. |

These failures are linked, not independent implementation details. A single
closed denotational AST repairs all five while keeping the interpreter
mechanical and truth-blind in the public pipeline.

## 3. Specific schema defects

### 3.1 `memory_record.claim` is opaque prose

Lines 19--37 of `semantic_dsl.schema.json` define the entire purported
semantic record. `kind` is only one of `GENERAL_RULE`, `LOCAL_RELATION`,
`EXCEPTION`, or `UNRESOLVED`; `claim` is any nonempty string. The schema cannot
decide any of the following:

- whether a claim denotes an operator, an equality, a conditional rule, a
  prediction, a negation, or merely an explanation;
- whether two differently worded claims have the same meaning;
- whether a claim has one local binding or silently bundles all 13 bindings;
- where noncommutative operands occur or in which order they apply;
- which public surface tokens, events, or prior records are semantic operands;
- whether an exception overrides a particular rule;
- whether an `UNRESOLVED` record contains explicit alternatives; or
- which node an intervention or future training view must preserve.

Consequently, “canonicalize JSON field order without changing claim bytes or
operand order” in `experiment_spec.md` has no enforceable operand-order clause.
There are no operand nodes. “Exact-deduplicate byte-identical record ASTs” is
also inaccurate: the only semantic payload is a byte string, and records with
different IDs/citations are not byte-identical even if their claims match.

### 3.2 The declared atomicity rule cannot be checked without semantics

The prose bans “more than one local binding per record.” A natural-language
claim can encode many bindings, a full completion algorithm, or a compressed
action table in one sentence or encoded string. A lexical scanner cannot
distinguish one binding from several across paraphrases. Enforcing the rule
requires understanding the claim, which makes the parser cognitive; not
enforcing it invalidates record counts, byte-matched shams, the 13-item reader
lower bound, and claims about local retrieval.

The same problem affects the ban on a “target pair.” Checking a free string
against a private target manifest would give the sleeper private target
identity and make admission target-dependent. The safe contract is a
structured public-reference allowlist, not a private semantic denylist.

### 3.3 Cross-field state semantics are not represented by the schema

The `DREAM_STEP` branch permits every operation in either phase and requires
all fields while allowing contradictory combinations. For example, it accepts
in schema terms a Dream-1 `READ` containing a Dream-2 decision and records, a
`RETAIN` with zero or two parents, or `ABSTAIN` with active records and
predictions. The standalone `DREAM2` object likewise allows zero parent IDs for
`RETAIN`, zero predictions for an active decision, and records/predictions for
`ABSTAIN`. The prose says an external strict parser will reject such cases,
but that unversioned parser is then part of the actual language definition.

There is also a terminal-format ambiguity. The recurrent prompts require one
`DREAM_STEP` object, while their terminal descriptions say `COMMIT` emits
`DREAM1` and `RETAIN/REVISE/ABSTAIN` finish with a terminal package. The schema
defines both step and terminal object shapes but does not define the exact
state transition from one to the other or which bytes constitute the
model-owned terminal decision.

### 3.4 Provenance is a flat event list, not a semantic dependency graph

`memory_record.citations` accepts only event-like `E..`/`A..` IDs. It cannot
cite earlier model-authored notice/connection/record nodes. `NOTICE` and
`CONNECT` have no structured premise field, and `workspace` is another opaque
string. Therefore the proposal cannot machine-check:

- that `CONNECT` has at least two distinct premises;
- that a revised record depends on a superseded model node and new evidence;
- that every committed statement has an acyclic path to public events; or
- that Sleep preserved rather than reconstructed the derivation.

Citations can still establish origin, never truth, but their origin role must
be structurally testable.

### 3.5 Limits disagree in scientifically material ways

The current bytes contain at least these incompatible limits:

- `experiment_spec.md` says at most 15 records per candidate; the schema caps a
  candidate and terminal records at 13; the bound granularity audit specifies
  `R=13` and the math audit grounds the D4 reader certificate in 13 items.
- `experiment_spec.md` says a claim may be 512 characters; the schema uses
  JSON Schema `maxLength: 256`; the bound granularity audit says 256 **UTF-8
  bytes**. JSON Schema length is Unicode-code-point length, not UTF-8 bytes.
- `experiment_spec.md` permits a 12,288-byte package, whereas the bound
  granularity audit specifies 4,096 bytes.
- Candidate record IDs must be unique and prediction IDs must be exactly
  `A1,A2` or `B1,B2`, but the schema itself enforces neither uniqueness by ID
  nor exact request-ID set membership.

These discrepancies change semantic capacity and reader headroom. They cannot
be delegated to an implementation choice after ratification. The conservative
repair is `R=13`, 256 canonical UTF-8 bytes per compact semantic record, and
4,096 bytes per package, matching the bound granularity contract. If the new
structured representation cannot fit, change and justify all three limits in
one new deliberated contract and recertify the reader lower bound.

## 4. Prompt and reader audit

The generic prompts appropriately avoid the PCFL equations, orientation
family, hidden factors, and target paths. The class-informed equations are
clearly separated as a ceiling. Those are strengths.

However, the primary prompts ask for “standalone records” without giving a
closed record semantics. The schema offers only prose. Thus the model is never
asked to commit the exact operator program that downstream tests assume.
`generic_dream1.txt` and `generic_dream2.txt` need to receive the versioned AST
grammar and its public, family-neutral denotation. They should not receive a
factorized example or either PCFL equation.

`iterative_thinker.txt` currently asks a free-text semantic question, while
the reader is supposed to use literal tokens and return one atomic record.
This leaves substantial intelligence in the unspecified query parser and
result selector. “Literal relation words” is particularly unsafe: recognizing
that “combine,” “after,” “reverse,” and “acts first” denote the same relation
is semantic normalization. A deterministic lexical index may index exact
strings, but it cannot call them common relation words without a frozen public
lexicon that itself leaks the answer class.

The repair is a structured exact-match query with deterministic pagination.
For example:

```json
{
  "match": [{"field": "PUBLIC_TOKEN", "value": "u1"}],
  "statement_form": null,
  "cursor": 0
}
```

Allowed indexed fields should be only values obtained by syntax-tree
traversal: `PUBLIC_TOKEN`, eligible `PUBLIC_ACTION`, `RECORD_ID`,
`SYMBOL_ID`, and coarse `STATEMENT_FORM`. Posting lists should be ordered by
the SHA-256 of the unchanged canonical record bytes; `cursor` returns exactly
one item or `NOT_FOUND`. No embedding, paraphrase, stemming, relation
normalization, learned ranker, target-aware prefetch, or hidden linear scan is
permitted. The query bytes, examined postings, cursor state, and return bytes
must all be counted.

A generic structural query such as `statement_form=RULE` lets Think discover a
global combination rule without the index naming “orientation.” After reading
a rule, its model-authored `SYMBOL_ID`s provide exact keys for related
definitions. This is sufficient for bounded traversal and does not give the
reader the solution.

## 5. Exact family-neutral replacement

### 5.1 Design criterion

The primary language should be **family-neutral across factorized and
independent-table lives, but operator-explicit**. A predictive-operator DSL is
already allowed by the paper adjudication and the public task exposes stable
positional effects. The grammar may supply generic finite-operator algebra; it
must not supply “stem factor,” “suffix factor,” “orientation,” “gauge,” a
two-law menu, a sparse-tree path, or a completion equation.

The model must choose whether to introduce reusable functions, what their
arguments mean, their ground values, and the ordered expression connecting
them to actions. An independent-table hypothesis can instead bind whole
public actions directly. The grammar therefore affords the latent family
without naming or preferring it.

### 5.2 Closed sorts and terms

Use a versioned closed term algebra with these sorts:

```text
TOKEN, ACTION, OPERATOR, TRAY, BOOL
```

Permit only these term constructors in the active semantic corpus:

```text
PUBLIC_TOKEN(text)                       : TOKEN
VARIABLE(var_id, sort)                   : declared sort
ACTION_FROM_PARTS([TOKEN, ...])          : ACTION
PUBLIC_ACTION(event_id)                  : ACTION
EVENT_OPERATOR(event_id)                 : OPERATOR
PERMUTATION(image[0..5])                 : OPERATOR
CALL(symbol_id, [term, ...])             : declared result sort
OPERATOR_OF(action_term)                 : OPERATOR
INVERSE(operator_term)                   : OPERATOR
COMPOSE_APPLY_FIRST([operator_term, ...]) : OPERATOR
APPLY(operator_term, tray_term)           : TRAY
EQUAL(left, right)                        : BOOL
NOT_EQUAL(left, right)                    : BOOL
```

`PERMUTATION.image[input_slot]` must have exactly six unique integers in
`0..5`; its tray convention must be defined once and used by extraction,
Dream examples, scoring, and cuts. `COMPOSE_APPLY_FIRST.steps[0]` applies
first, then `steps[1]`, so operand order is data rather than prose.

`symbol_id`s are opaque model-authored identifiers. Every declaration includes
argument sorts and result sort. The grammar does not predeclare two unary
factor tables. A candidate may declare zero or more functions under the
record/node/byte caps.

### 5.3 Closed statement forms

Each active record contains exactly one of:

```text
DEFINE:     one ground CALL(symbol, args) equals one closed term
ASSERT:     one closed EQUAL or NOT_EQUAL proposition
RULE:       FORALL declared variables over public surface domains,
            one optional conjunction of structural guards, and one equation
EXCEPTION:  one structured scope plus one replacement equation and the exact
            RULE record_id it overrides
UNRESOLVED: two or more explicit alternative statement hashes, with no active
            assertion silently chosen
```

Every AST node has a stable model-emitted `node_id`. Each record separately
contains:

```json
{
  "record_id": "R00",
  "statement": {"form": "...", "node_id": "N00", "...": "..."},
  "provenance": {
    "event_ids": ["E00"],
    "record_ids": []
  },
  "uncertainty": "LOW"
}
```

`record_id`, provenance, and uncertainty are metadata and are excluded from
the semantic-statement hash. Exact deduplication is defined as equality of the
canonical `statement` AST; dedup may union provenance in a separate envelope
without pretending the original model bytes were identical. The audit ledger
retains both originals and the derivation of the compiled envelope.

No active free-text field participates in semantic identity. `explanation`
and `reason` may remain in proposal/trace artifacts, but they must be excluded
from active text memory, retrieval keys, cuts, semantic scores, and later LoRA
views. An optional `claim_text` pretty-print may be retained under the same
exclusion.

### 5.4 Why this can express the hidden operator structure

Without any factor-named primitive, a model could declare two opaque functions
from surface tokens to operators, emit one ground `DEFINE` per retained local
value, and author a `RULE` whose right-hand side is an ordered composition of
the two calls. Reversing the two `COMPOSE_APPLY_FIRST` steps expresses the
other law. The model may instead define one function from whole `ACTION` to
`OPERATOR`, which naturally represents observed independent-table entries but
does not complete unseen actions.

Thus the grammar supports:

- reusable part-conditioned operator bindings;
- a noncommutative global combination law;
- direct whole-action bindings;
- explicit exceptions and unresolved alternatives; and
- exact predictions through the already separate tray-prediction fields.

It does not tell the model that two part functions exist, which order is true,
that a gauge is needed, or that missing actions should be completed. Those
remain model-authored semantic choices. This is the required boundary between
an expressive interface and a supplied solution class.

## 6. Truth scoring without a semantic oracle

Freeze a small total interpreter for the closed AST before any model byte. The
interpreter performs only type checking, substitution of model-authored
`DEFINE`s, and the explicitly denoted finite operator operations. It must not
solve for missing definitions, choose a gauge, infer inverses not present in
the AST, complete an action table, rank hypotheses, or repair an undefined
term.

Use that interpreter in two separated ways:

1. **Public-pipeline use:** only syntax/type/reference/provenance validation
   and canonical serialization. Do not evaluate hidden truth or derive a new
   record. Sleep and the reader never receive interpreter-derived closures.
2. **Offline scoring use:** after the candidate/corpus/action hashes freeze,
   evaluate the candidate's denotation on declared public evidence, A/B
   predictions, and hidden holdouts, then compare the resulting operator/tray
   with the private world. The comparison result is terminal scorer data.

Score gauge-invariant denotation, not hidden generator factor names. A
model-defined local function binding can be valid only jointly with its
model-authored rule; an isolated factor value has no unique truth across
gauges. Report at least:

```text
well_typed(record)
evidence_consistent(candidate)
prospective_A/B_accuracy(candidate)
complete_operator_accuracy(candidate, offline only)
target_operator_coverage(candidate, offline only)
undefined_or_conflicting_term_rate(candidate)
```

If a record is a closed proposition, it may receive a record-level truth
value. For gauge-dependent `DEFINE` records, report joint-program consistency
and deletion/substitution sensitivity rather than a misleading absolute
“factor truth.” Missing definitions, ambiguous active alternatives, cycles,
or conflicting definitions are `UNDEFINED` and score wrong where a prediction
is required; the scorer never completes them.

This interpreter is not an oracle because the AST itself fixes the meaning.
Hidden truth enters only the final comparison. In contrast, mapping arbitrary
English to this AST after the model writes it would be an oracle and is
forbidden.

## 7. Exact causal cuts

The authentic corpus must freeze first. Define every cut as a registered AST
transformation that produces a separate isolated intervention corpus and an
edit receipt containing input hash, selector, edited node IDs, output hash,
and byte delta.

At minimum:

1. **Whole-memory counterpart:** replace the entire authentic canonical corpus
   with the predeclared counterpart-life corpus. This is already byte-defined.
2. **Order cut:** select by a preregistered structural pattern, not semantic
   prose: every `COMPOSE_APPLY_FIRST` node in the active universal
   `OPERATOR_OF(ACTION_FROM_PARTS(...))` rule, or a predeclared unique node
   class, and reverse its `steps`. Zero or multiple unexpected matches are a
   cut-assignment failure, never a human choice.
3. **Orientation deletion:** delete the same structurally selected global rule
   while preserving every other byte. Again, the selector is fixed before
   model output.
4. **Decisive binding substitution:** select a ground `DEFINE` by its structured
   public surface key and replace only its RHS operator node with the
   pre-certified alternate-world value. The private intervention builder may
   use the target/certifier manifest only after authentic evaluation objects
   freeze.
5. **Sham:** edit the same node type and matched canonical byte footprint using
   a pre-certified target-irrelevant substitution. Do not define a sham as a
   prose change that may accidentally alter meaning.

The intervention builder is intentionally truth-aware; it is a terminal
causal instrument, not part of organism cognition. `visibility_contract.md`
must name it as a separate private process. Neither its selectors, replacement
values, receipts, failure modes, nor timings may reach Dream, Sleep, the
authentic reader/Think branch, or any later authentic training corpus. Cut
branches may support dependence claims only; their accuracy is not evidence
that the authentic system inferred the edited value.

If SELF emits no AST matching a preregistered cut selector, report the cut as
unavailable/failed for that assigned life. Do not use a language model or
manual reading to find “what the model meant.” Oracle-schema arms can still
validate the cut machinery, but their successful cuts cannot substitute for a
missing generic SELF cut.

## 8. Visibility and taint repair

The current process separation correctly puts hidden factors, target paths,
and truth in `private_certifier`/`offline_scorer` and requires comparator
mutation invariance. Three additions are required:

1. **Public allowlist validation.** Sleep receives a registry of public event
   IDs and literal surface tokens, not a private list of targets. A semantic
   AST may reference only registry members, model-declared symbols, variables,
   and fixed operator literals. A ground `PUBLIC_ACTION` must be backed by an
   eligible cited public event or announced validation request. Generic
   `ACTION_FROM_PARTS` rules may use variables. This blocks direct target
   packets without giving Sleep target identity.
2. **Private intervention process.** Add `intervention_builder` after authentic
   corpus and target hashes. Its outputs flow only to explicitly labeled cut
   branches and terminal scoring. The authentic corpus/index hash must be
   checked before and after every intervention branch.
3. **Future trainer process.** The current change properly contains no trainer.
   Any later LoRA change must add a fresh process that sees only the selected
   canonical AST, registered mechanical views, public query keys, and training
   hyperparameters. It must be unable to open certifier/scorer/target/cut
   artifacts and must pass comparator-mutation and false-AST symmetry tests.

Do not treat lexical rejection of arbitrary free text as proof of this
firewall. Structured reference closure is the proof obligation.

## 9. Later LoRA transport contract

The current text-only proposal makes no LoRA claim and authorizes no training;
that boundary is correct. It is nevertheless not yet a valid source format for
the later “identical compiled corpus” experiment. The future separately
ratified stage should consume the same canonical AST bytes used by text memory
and generate views by a frozen total template function only.

Permissible examples include:

```text
RECALL_BY_ID(record_id)             -> exact canonical record bytes
RECALL_BY_PUBLIC_TOKEN(token,cursor)-> exact canonical posting record bytes
RECALL_SYMBOL(symbol_id,cursor)     -> exact canonical definition bytes
RECONSTRUCT_STATEMENT(canonical cue)-> exact missing AST field/record bytes
```

Forward, reverse, and partial-cue variants must be deterministic structural
templates whose outputs are literal subobjects of, or losslessly reconstruct,
the source AST. A claimed “paraphrase” view must be a registered syntactic
template over AST constructors; no external language model, embedding model,
human rewrite, thesaurus, hidden truth, completed compound, target question,
correct action, hard negative, or scorer label may generate it.

Every well-formed selected false AST must yield exactly the same number and
shape of views as a true AST of the same structure. The view manifest must map
each example to source candidate/decision/record/node IDs and record canonical
input/output hashes. Candidate-only, wrong-life, wrong-order, decisive-binding,
sham, direct-QA/raw-history, identical-text, recognition-assisted, and unaided
read controls remain necessary under the paper adjudication.

Training the raw prose string verbatim would test associative reproduction of
that string, not exact semantic transport. It cannot support reverse,
paraphrase, partial-cue, law-cut, or factor-cut claims unless those interfaces
are separately specified without semantic generation.

## 10. Required acceptance fixtures

Before implementation or model execution, add positive and negative fixtures
covering:

1. exact parse/canonical round-trip for every term and statement constructor;
2. rejection of undeclared symbols, wrong sorts, cyclic record provenance,
   duplicate IDs, illegal event/action references, invalid permutations, and
   operation/phase field contradictions;
3. byte-count boundaries under UTF-8, including multibyte Unicode if free audit
   annotations remain;
4. exact `A1,A2`/`B1,B2` set validation and active-versus-abstain cardinality;
5. one factorized-form program and one direct independent-table-form program
   expressed with the same grammar and parser;
6. two shape-identical true/false ASTs producing identical Sleep, index, and
   future-view behavior while only terminal truth diagnostics change;
7. deterministic query collision/pagination and no semantic-ranking behavior;
8. a 13-item oracle-schema D4 read trace plus every itemwise alternate-world
   decision fork under the same structured grammar;
9. structural orientation deletion, order reversal, decisive-binding
   substitution, and equal-footprint sham receipts; and
10. comparator/private-field mutation leaving authentic Dream, corpus, index,
    query returns, and action bytes bit-identical.

Fixtures may establish protocol fidelity only. They do not count as neural or
scientific results.

## 11. Disposition: must-fix versus optional

### Must fix before ratifying this text DEV

1. Replace active free-text `claim` with a closed, versioned, typed operator
   AST, or remove every semantic truth/coverage, 4/13 atomic-reader,
   orientation-deletion, wrong-order, decisive-factor, and semantic-causality
   gate. Given the proposal's purpose, replacement is the coherent choice.
2. Encode phase/op/terminal cross-field constraints and exact state transitions
   in conditional schemas plus a hash-bound parser specification. Define which
   exact model bytes are the terminal decision.
3. Add record-to-record premises and acyclic provenance; distinguish semantic
   statement hashes from provenance/epistemic metadata.
4. Reconcile `R`, per-record length unit, package byte cap, prediction-ID sets,
   and ID uniqueness across the schema, prompts, experiment spec, tests, and
   bound advisories. Recertify itemwise reader headroom after any change.
5. Replace free-text lexical retrieval with the exact structured query,
   syntax-derived postings, ordering, cursor, collision, and accounting
   contract.
6. Freeze the closed offline denotation/scoring interpreter and use
   gauge-invariant program/operator truth. Do not semantically parse prose.
7. Define cuts as reproducible AST edits with predeclared selectors, isolated
   private intervention provenance, failure behavior, and matched shams.
8. Update the generic Dream and Think prompts to require the new objects while
   keeping factor equations, two-law alternatives, gauges, target roles, and
   completion recipes absent. Keep the class-informed prompt as a ceiling.
9. Update `visibility_contract.md` with public reference allowlisting and a
   distinct terminal intervention-builder boundary.

Until all nine are disposed in new exact bytes, `T06`, `T09`, `T11`, `T12`,
`T18`, and `T19` cannot produce their claimed receipts. Stage 0 implementation
and Stage 1 model work should remain blocked.

### Must fix before any later LoRA stage

1. Freeze the canonical AST-to-training-view function and prove lossless source
   mapping, false-AST symmetry, and zero scorer/target/cut input.
2. Add trainer visibility, reset, optimizer, adapter, candidate/index, and
   corpus-hash contracts plus identical-text and direct-QA/raw controls.
3. Define recognition-assisted versus unaided read interfaces and evaluate
   exact AST recovery before action. Do not call model-generated paraphrases
   mechanical transport.
4. Require a new deliberation and SHA-bound human ratification. This audit does
   not alter the proposal's explicit ban on automatic LoRA promotion.

### Optional robustness improvements

- Keep an automatically rendered English gloss beside each AST for human
  inspection, clearly marked nonsemantic and never used by the organism.
- Add alpha-renaming diagnostics for model-declared symbol/variable IDs while
  preserving the actual authored IDs in the primary bytes.
- Version the canonicalization algorithm and include schema/interpreter/query
  engine version hashes in every corpus receipt.
- Report both canonical JSON and compact binary byte footprints, but select one
  preregistered representation for budgets and matching.
- Add metamorphic tests showing that record order, irrelevant audit prose, and
  offline scorer filenames cannot change postings or authentic actions.

## Bottom line

The proposal has the right ownership ambition: raw public outcomes reach a
fresh Dream-2, the model selects durable content, and truth remains terminal.
But byte-preserved prose is not enough to make that ambition auditable. It
either stays opaque, in which case the key semantic measurements and cuts do
not exist, or another component interprets it, in which case that component
becomes the unmeasured semantic intelligence.

A small model-authored equational operator AST is the family-neutral middle:
it can represent the hidden program without naming the PCFL factor family,
admits exact false-symmetric parsing and retrieval, supports mechanically
isolated causal cuts, and can later generate lossless LoRA views. The current
free-text schema should therefore be replaced before any implementation or
ratification.

No proposal/code file was edited, and no model, GPU, training, experiment, or
network call was performed.

The following digest binds the sorted `shasum -a 256` manifest of every file
in the audited change directory plus the four bound advisories named in the
commission (the advisory being written is not part of that source manifest).

**Audit source-manifest SHA-256:** `dbc357670bf35eb747902fd73145ee87677b8583bb7a74af93509572ceccf3a1`
