# PCFL M0-to-M-TEXT and M-TEXT-SUPPLIED exact contract repair — fresh v1

Date: 2026-09-10

Status: **source-only advisory; not ratified and not executable**. This file
authorizes no implementation, materialization, fixture/root/data generation,
CPU benchmark run, model/tokenizer execution, adapter or checkpoint work,
training, parenting, GPU use, resource acquisition, scientific claim,
confirmation, release, or submission. It is a proposed repair input for a new
`AGENTS.md` deliberation.

## 0. Ruling

The rejected v2 proposal had the right decomposition but did not freeze a
scientific instrument. The narrow successor should contain two separately
gated packages:

1. **M0-THIN**: a model-free finite PCFL world and public interface; and
2. **M-TEXT-SUPPLIED**: one frozen Qwen2.5-7B-Instruct policy using supplied,
   grounded, connected text through that interface.

M0 passage is software conformance only. M-TEXT passage may support only this
conditional claim:

> For one frozen model and one registered finite PCFL suite, changing only
> supplied grounded connections changed the model's ability to construct two
> goal-dependent paths, choose and use a separating experiment, and later use
> old plus newly observed information after a sterile reset.

It does **not** establish DREAM authorship, SLEEP, a write into weights, LoRA
transport, online learning, accumulation, compression, parenting, lifetime
improvement, population generalization, or a flywheel. Those remain later
packages.

This repair makes five substantive choices rather than leaving them for code:

- **No FeltCraft V7 dependency.** The PCFL V7 reuse map is the empty array.
  V7 may be cited as design history, but M0 source must not import, execute, or
  read V7 artifacts. This removes the unauthorized-successor and unproved-
  isomorphism problem.
- **No legal-action oracle.** The actor sees a fixed action catalog, not the
  subset that is correct at its current state.
- **Plan before acting.** For the path probes, memory reads close after the
  first world action. The actor must construct a path from supplied memory;
  it cannot query one atom after each transition and make links irrelevant.
- **Exact finite-suite inference.** The current 64-root single-topology
  universe is a deterministic census. Alias/order cells are repeated
  robustness cells, not independent samples. There are no p-values, bootstrap
  intervals, or population claims.
- **Two recurrence controls.** One deletes model-carried scratch while keeping
  repeated observation calls; the other makes a single equal-generated-budget
  phase plan before any outcome. This separates persistent thought-state from
  within-task observation feedback.

## 1. What must change in M0 before M-TEXT can be meaningful

The semantic proposal in
`20260910_pcfl_v2_minimal_exact_semantics_fresh_v1.md` is retained except for
the amendments below. These amendments are outcome-changing and therefore
must appear in successor change bytes, materialized goldens, and tests; they
must not be inserted during implementation.

### 1.1 Fixed public action catalog, not hidden legality

Replace `FiniteView.legal_actions` with:

```text
action_catalog: [public-action-id]
```

The field is a declared set, sorted lexicographically, and padded through the
outer `FiniteView` envelope. During `PROBE_A`, `PROBE_B`, and `DELAYED_GOAL`,
it contains all sixteen public relation aliases plus `FINISH` and `ABSTAIN`.
It is byte-identical across current nodes, goals, twin bits, carrier arms, and
correct answers within the same presentation root. During `UNCERTAINTY` it
contains all four public experiment aliases plus `ABSTAIN`. During `ACQUIRE`
it contains `COMMIT_0`, `COMMIT_1`, and `ABSTAIN`.

A relation action whose public alias does not denote an outgoing registered
atom at the current state is a syntactically valid but unsuccessful ordinary
action. It consumes one action slot, leaves the state unchanged, and emits a
fixed-size public event with:

```text
outcome:{kind:"NO_EFFECT",value:null}
```

It is not an `ILLEGAL_ACTION`, parser error, or private controller error. A
wrong `FINISH` is an ordinary terminal failure. This keeps correctness hidden
while allowing failure-inclusive behavior.

### 1.2 A path-planning read cut

Add the following public fields to `FiniteView`:

```text
reader_open: boolean
world_actions_taken: u8
```

At the beginning of each path phase, `reader_open=true`. The first accepted
relation `ACT`—successful or `NO_EFFECT`—sets `reader_open=false` before the
next view. Every later `READ` in that phase returns the ordinary fixed-size
`BLOCKED` envelope without touching an index. `FINISH` and `ABSTAIN` also
close the reader.

The actor therefore has at most eight reads to assemble a complete plan and
then at most four relation actions to execute it. The read cut resets at
`PROBE_FORK`, at the start of the other isolated probe, and at
`DELAYED_RESET`. It does not reopen after an unsuccessful action.

This cut is necessary for the connected-memory estimand. Without it, the
current-state anchor can retrieve one outgoing atom per step, so `ATOMS` can
solve the graph without connections.

### 1.3 Exact common-reader law

The common reader is the pure function:

```text
READ(carrier, anchor, cursor, reader_open, repeat_state)
    -> exactly one fixed-size MemoryReturn
```

It may read only those five arguments. It may not read goal identity, hidden
root state, twin bit, condition name, score, expected answer, future event,
model output other than the command, split, filename, device, runtime timing,
or a query generated outside the closed command.

An anchor is legal only when it is:

- the current public state alias;
- the released public goal start or target alias;
- a field of an already released `PublicEvent`; or
- an atom or link ID returned earlier in the same live branch.

For a public node alias, candidates are atoms whose `src` or `dst` equals the
alias. For an atom ID, candidates are that atom followed by links whose
`left` or `right` equals that ID. For a link ID, candidates are that link and
its two referenced atoms. Public-event anchors resolve only the public aliases
contained in that event. Candidate records are sorted by `(record_type,
semantic_id)` with `ATOM < LINK`; `cursor` selects an exact position in this
list. Out-of-range cursors return `NOT_FOUND`. No fuzzy search, embeddings,
goal-derived query builder, adaptive ranking, or hidden catalog is present.

The public response contains one atom slot and one link slot. Unused slots are
typed padded null records. `FOUND`, `NOT_FOUND`, and `BLOCKED` have the same
outer byte length. The repeat rule from the Stage-0 proposal remains public
and exact: the third consecutive identical command is `BLOCKED`; all counts,
fingerprints, block status, and reset reason appear in the next view.

### 1.4 Answer-neutral connection construction

Authentic `Link` records contain only two earlier public atom IDs and their
support-root IDs. They contain no goal, target, path rank, answer, action
recommendation, composite destination, score, condition, or scorer field.
Link identity is computed before goal release from the canonical IDs of the
two public atoms and support roots. Link order is semantic-ID order. The
producer cannot observe which of the two registered path-equivalence classes
the later thinker will use.

Checker-side semantic identities remain `hex64`, but the actor projection uses
fixed-width target-independent capability handles: the 26 atom slots are
`a00..a19` and the seven link slots are `l00..l06`, rotated by the registered
presentation transform before any condition is applied. A slot retains the
same public handle in AUTH, null, cut, and deranged carriers. Handles identify
only public slots; they do not encode semantic hashes, goals, paths, roots,
conditions, answers, or scores. This mapping is frozen before goal release and
is included in the paired-prefix certificate.

The Stage-0 authentic and deranged link sets are retained. They already match
left degree, right degree, slot count, identifier length, lexical schema, and
padding:

```text
AUTH:
  p0->p1, p2->p3, p1->p4, p3->p4, p4->p5, p4->p6

DERANGED:
  p0->p4, p2->p4, p1->p5, p3->p6, p4->p1, p4->p3
```

The deranged carrier must additionally match total UTF-8 bytes and tokenizer
length after the M-TEXT renderer. Stable slot handles ensure that both arms
contain the same handle multiset. Link slots render in slot order rather than
content-hash order, so DERANGED permutes only same-width handle values inside
the same six fixed templates. The M-TEXT preparation checker must prove exact
token-count equality. Failure invalidates preparation; there is no identifier
search, per-root padding choice, or favorable remapping.

For `READ`, `ACT`, and `FINISH`, `deps` is a lexicographically sorted set of at
most eight public capability handles returned earlier in the current branch.
The first executed path edge cites its atom. Every later edge cites its atom
and the authentic link joining it to the preceding edge. Unknown, duplicated,
future, sibling-branch, cut, or never-returned handles reject the response.

### 1.5 Distinguish a missing new connection from no persistent write

The old `NEW_CUT` masks only the reserved new link slot and leaves the newly
observed atom available. Retain it and add one separately named carrier cell:

```text
NO_PERSIST_NEW
```

In this cell the acquisition outcome is emitted normally, but after
`DELAYED_RESET` neither the new atom nor its new link is present in the
persistent carrier; their fixed slots are typed nulls. This is not attributed
to a learned writer. It is a supplied-text persistence intervention.

### 1.6 Exact reset sole-channel law

At `DELAYED_RESET`, destroy:

- all raw model messages and generated text;
- model-carried scratch, structured belief, and plan;
- all chat/KV/prefix/application cache entries;
- the prior model request/session handle;
- command, reader, and tool transcripts;
- branch workspaces and returned-ID capabilities;
- repeat fingerprints and counts;
- last-event and joined-probe renderings;
- environment state other than the immutable root and admitted persistent
  public evidence; and
- all timing, error, request-order, filename, and condition metadata.

Retain only the immutable old admitted carrier and, outside
`NO_PERSIST_NEW`, the admitted new atom/link carrier. Then start a fresh model
phase with empty scratch and a newly rendered `FiniteView`. The delayed goal
is revealed only in that new view. No raw acquisition outcome is rendered.
Thus the registered carrier is the sole permitted old-plus-new channel.

Any mutation that retains one forbidden object, or omits one declared retained
carrier object, fails `MTEXT-RESET-SOLE-CHANNEL` before scientific execution.

## 2. Frozen M0-to-M-TEXT handoff

M0 emits no prompt and invokes no tokenizer. It does emit a closed handoff
for a later, independently ratified renderer. The handoff is immutable and
read-only.

### 2.1 Handoff record

Each root/condition/phase checkpoint has exactly one JCS record:

```text
MTextHandoff := {
  v:1,
  semantic_contract_id:"PCFL-M0-MTEXT-HANDOFF-v1",
  stage0_manifest_sha256:hex64,
  transition_table_sha256:hex64,
  root_public_alias:opaque32,
  condition_public_alias:opaque32,
  phase:enum,
  public_checkpoint_sha256:hex64,
  finite_view_sha256:hex64,
  carrier_sha256:hex64,
  public_event_dag_sha256:hex64,
  action_catalog_sha256:hex64,
  reader_contract_sha256:hex64,
  reset_contract_sha256:hex64,
  endpoint_oracle_sha256:hex64,
  model_projection_contract_sha256:hex64
}
```

`root_public_alias` and `condition_public_alias` are artifact-routing aliases
only. They never enter model-visible bytes. Their opaque values are equal
length, uniformly formatted, and derived from the semantic manifest plus a
domain tag; neither contains `k`, `h`, split, arm, answer, goal, or expected
score in clear text. `endpoint_oracle_sha256` identifies checker-only truth;
the oracle bytes never cross the handoff projection.

### 2.2 Handoff bundle contents

For every registered checkpoint the frozen bundle contains:

- canonical semantic root specification;
- canonical `FiniteView` and public action catalog;
- canonical carrier slots for every registered intervention;
- pure-reader expected returns for every legal anchor/cursor/repeat state;
- join, repeat, reset, and taint-DAG certificates;
- path-equivalence classes and uncertainty truth in a checker-only directory;
- positive and expected-reject endpoint fixtures;
- the split roster and dispatch order in a controller-only directory; and
- exact pre/post semantic hashes for every transform.

The model projection allowlist is only: public prompt mode, canonical
`FiniteView`, previous permitted scratch within the same phase, and the fixed
response schema. All other handoff fields are controller/checker-only.

### 2.3 Materialization and independent checking

The successor ratification packet must contain the actual materialized bytes,
not a promise to generate them. Materialization has no RNG, seed search,
ranking, accept/reject loop, favorable-root selection, retry, replacement, or
model/tokenizer feedback.

Checker A may import the proposed M0 implementation. Checker B must:

- be separately authored from the mathematical tables in the ratified
  specification;
- import neither M0 nor the materializer;
- contain its own closed constants for paths, posteriors, transforms, phase
  transitions, and failure precedence;
- read only candidate canonical artifacts;
- recompute semantic identities and expected profiles independently; and
- reject a mutation corpus containing at least one mutation of every schema
  field, transition, path edge, support edge, carrier slot, reset field,
  expected endpoint, root membership, and manifest member.

Agreement of A and B on digests is described as reproducibility. Semantic
validation additionally requires B's independently derived invariants and
100% rejection of the mutation corpus. Their source files, runtime, input
manifests, output receipts, and hashes must be disjointly listed.

The V7 reuse manifest is exactly:

```json
{"v":1,"dependency":"FELTCRAFT_SYMBOLIC_KERNEL_V7","reused_primitives":[]}
```

Any runtime import, file read, subprocess, hash lookup, or copied golden from
V7 fails closed.

## 3. Fixed M-TEXT model and runtime boundary

### 3.1 Primary model

The proposed primary is the same frozen base intended for later LoRA relay:

```text
Qwen/Qwen2.5-7B-Instruct
revision a09a35458c702b33eeacc393d103063234e8bc28
dtype bfloat16
no adapter, no prefix, no learned memory, no parent
```

Before execution, a model manifest must enumerate SHA-256 and byte size for
every loaded config, tokenizer, vocabulary, chat-template, special-token,
weight-index, and safetensors shard. A missing, extra, symlink-resolved-
differently, or hash-mismatched file blocks execution. The model cache is
mounted read-only with `HF_HUB_OFFLINE=1` and equivalent network denial.

No 32B or provider model may be substituted in the same assay. A 32B ceiling,
if desired, is a separately named condition and cannot rescue or replace the
7B confirmation.

### 3.2 Runtime proposal

Bind the already observed environment, subject to a later real manifest:

```text
transformers 5.5.3
torch 2.13.0+cu130
vLLM 0.27.1
CUDA/driver 580.173.02
tensor_parallel_size 1
enable_prefix_caching false
dtype bfloat16
max_model_len 16384
```

All package wheels, Python executable, container/image, CUDA libraries,
driver, kernel, host class, runner source, parser source, controller source,
renderer source, and environment variables are hash-bound before a model
call. The concrete machine identity is recorded but is not model-visible.
Changing any listed model, tokenizer, prompt, parser, controller, runtime, or
hardware class after DEV forks the assay and consumes no confirmation roots
until separately approved.

### 3.3 Decoding

Scientific decoding is:

```text
do_sample=false
temperature=0.0
top_p=1.0
top_k=-1
min_p=0.0
num_beams=1
n=1
best_of=1
repetition_penalty=1.0
length_penalty=1.0
logprobs=none
custom_stop_strings=[]
stop_token_ids=[checkpoint EOS only]
skip_special_tokens=true
```

Greedy decoding makes the seed behaviorally irrelevant, but every request
still records integer seed `271828`. The tokenizer uses its bound chat
template with `tokenize=true`, `add_generation_prompt=true`, and no custom
BOS/EOS insertion. No prompt truncation is allowed.

Each recurrent response has at most 256 generated tokens and 2,048 decoded
UTF-8 bytes. A one-shot phase receives the exact sum of its corresponding
recurrent generated-token ceilings: 3,328 tokens for a 13-turn path phase and
1,024 tokens for the four-turn uncertainty/acquisition phase. Input is capped
at 8,192 tokens and 65,536 UTF-8 bytes; input plus output must be at most
16,384 tokens. Overflow or truncation is a cell failure, never an adaptive
cut.

### 3.4 Session, cache, isolation, and retries

- Every generation request contains exactly two messages: one `system` and
  one `user`. There is no provider conversation ID, assistant-history
  message, native tool role, or persisted KV state.
- Each request is rendered from current public state from scratch. Only the
  explicit permitted `prior_scratch` field may carry model-generated state
  across recurrent turns within one phase.
- Prefix caching, response caching, application retrieval caches, speculative
  decoding, fallback providers, adapters, quantization, and model hot-swaps
  are disabled.
- Controller state is new for every root/condition cell. The model engine may
  stay resident because it is local and stateless, but condition order is
  rotated prospectively and an order-reversal canary must yield byte-identical
  responses before confirmation.
- There is one model attempt per registered call. Parse failure, timeout after
  600 seconds, output overflow, invalid ID, or invalid command is a zero-valued
  policy outcome and is never retried.
- A failure before a request is durably marked `REQUEST_EMITTED` is a fatal
  infrastructure failure and produces no scientific receipt. After that mark,
  an ambiguous/incomplete call is a terminal zero for that cell. It is never
  repeated.
- A crashed run may resume only calls having no `REQUEST_EMITTED` receipt.
  Completed or ambiguous calls are immutable. No root or condition is
  replaced.
- Internal errors, filenames, request IDs, timings, exception text, GPU
  assignment, condition aliases, and split names never enter a later prompt.

Before DEV, four fixed non-scientific sentinel prompts are rendered and run
three times from fresh controller states and in reverse order. All decoded
bytes and token IDs must match. Failure blocks this deterministic assay; it
cannot be repaired by averaging stochastic repetitions.

## 4. Exact model-visible protocol

### 4.1 System prompt literal

The successor must bind the UTF-8/NFC bytes of this literal, including line
breaks and with no final newline:

```text
You are the acting policy in a finite world. The USER JSON is your complete public state. STEP atoms are observed transitions. An AUTH link says its left STEP can be followed by its right STEP; NULL, EMPTY, and REVOKED do not assert a connection. Use READ only with public anchors already present in the USER JSON or returned earlier in this phase. Before your first world action, construct a goal-directed path. After the first world action, memory reads are closed. PREDICT records describe experiment outcome counts. Choose an experiment that distinguishes the unknown target, update your belief from its public outcome, and commit only when supported. Use scratch only as temporary reasoning within this phase. Cite only returned public IDs in deps. For ACTOR_RESPONSE_V1 return exactly the keys v, scratch, belief, plan, and command. Belief has the one key target_bit with value UNKNOWN, 0, or 1. For PHASE_TAPE_V1 return exactly the keys v, scratch, initial_belief, plan, and commands. A command is exactly one of READ(v,op,anchor,cursor,deps), ACT(v,op,action_id,deps), FINISH(v,op,deps), or ABSTAIN(v,op,reason_code). Return exactly one JSON object, with no Markdown or extra text. Never invent an ID.
```

This is a coached use ceiling, not evidence that the model discovered the
algorithm. Every model condition receives the identical system prompt.

### 4.2 User message

The user message is JCS for this closed record and contains no surrounding
free text:

```text
ModelTurn := {
  v:1,
  mode:"RECURRENT"|"RECURRENT_SCRATCH_OFF"|"ONE_SHOT_TAPE",
  response_schema:"ACTOR_RESPONSE_V1"|"PHASE_TAPE_V1",
  static_context:null|[padded public records],
  view:FiniteView,
  prior_scratch:string
}
```

`prior_scratch` is NFC UTF-8, at most 1,024 bytes, and empty at every phase
start. In `RECURRENT`, it is exactly the prior accepted response's `scratch`.
In `RECURRENT_SCRATCH_OFF` and `ONE_SHOT_TAPE`, it is always empty. No raw
prior prompt, response, command, or tool transcript is inserted.

The model-visible bytes for each actual call are the exact two message bytes,
their bound chat-template rendering, and the resulting token-ID array. Every
one is stored in a private call receipt. Paired-prefix tests compare all three,
not only the underlying `FiniteView`.

`static_context` is null for the common-reader and matched intervention arms.
It contains only the explicitly defined raw-event or native-graph records in
the corresponding honest bypass arms. Its elements are closed padded public
records in semantic-ID order; no free prose is permitted.

`TARGET_ONLY_ANSWER_PRIOR_TAPE` uses this separate closed user schema, under
the identical system message and chat template:

```text
TargetOnlyTurn := {
  v:1,
  mode:"ONE_SHOT_TAPE",
  response_schema:"PHASE_TAPE_V1",
  phase:enum,
  goal:Goal,
  action_catalog:[public-action-id],
  budget:{reads_remaining:u8,actions_remaining:u8},
  static_context:null,
  prior_scratch:""
}
```

It is the registered pure target/answer-prior probe. It is not used as input
to another condition.

### 4.3 Recurrent response schema

After decoded leading and trailing ASCII whitespace is removed, the response
must be exactly one strict JSON object:

```text
ActorResponse := {
  v:1,
  scratch:string,
  belief:{target_bit:"UNKNOWN"|0|1},
  plan:[public-action-id],
  command:Command
}
```

`scratch` is NFC UTF-8 at most 1,024 bytes and may mention only public objects.
`plan` has at most four actions and every member must be in the current public
action catalog. Duplicate keys, unknown fields, NaN/infinity/floats, invalid
Unicode, invalid enums, nonpublic IDs, and trailing material reject. The
parser uses duplicate-detecting JSON, validates the closed schema, and
canonicalizes the accepted value to JCS for identity. Raw key order and
insignificant internal JSON whitespace do not reject; the exact decoded bytes
are still retained in the private call receipt.

The controller executes only `command`. `scratch`, `belief`, and `plan` are
ephemeral model outputs used for recurrence and separate diagnostics; they
are never public evidence, carrier rows, writer inputs, or scorer truth.

### 4.4 One-shot response schema

The phase-level comparator returns:

```text
PhaseTape := {
  v:1,
  scratch:string,
  initial_belief:{target_bit:"UNKNOWN"|0|1},
  plan:[public-action-id],
  commands:[Command]
}
```

The command list contains at most thirteen commands in a path phase and four in
the uncertainty/acquisition phase. It is generated before any command in that
phase executes. The controller applies it in order without another model
call. It never edits the tape or conditions later commands on observed
outcomes. The first syntactically invalid or state-inapplicable command ends
the cell adversely; unexecuted suffix commands do not become another chance.

### 4.5 Tool and observation envelope

There is no native provider tool API. The parsed `Command` is passed directly
to M0. M0 returns the next canonical `FiniteView`; that view appears only in
the next fresh two-message request. Model-visible semantic failures are only
ordinary `NO_EFFECT`, `MISS`, fixed `BLOCKED`/`NOT_FOUND`, and budget fields.
Parser, process, network, scorer, oracle, and controller errors end the cell
privately and are never rendered back to the model.

## 5. Recurrence intervention and equal-budget comparator

The active policy has four phase starts per root: `PROBE_A`, `PROBE_B`, the
combined `UNCERTAINTY/ACQUIRE` phase, and `DELAYED_GOAL`.

### 5.1 `AUTH_RECURRENT`

- path phases: at most 13 model turns, eight reads, four relation actions,
  and one terminal `FINISH` or `ABSTAIN` command;
- uncertainty/acquisition: at most four model turns, two world actions;
- scratch and structured belief/plan pass to the next turn in the same phase;
- public outcomes appear only through the next `FiniteView`; and
- all recurrent state is destroyed at phase boundaries and delayed reset.

### 5.2 `AUTH_SCRATCH_OFF`

This condition uses the identical model, prompt literal, calls, views,
reader/action budgets, and per-call generated-token ceiling. The controller
sets `prior_scratch=""` every turn and ignores prior `belief`/`plan` except for
diagnostic scoring. It still provides the next ordinary public outcome. This
isolates the value of explicit model-carried thought state from the value of
repeated environmental observation.

### 5.3 `AUTH_ONE_SHOT_TAPE`

This condition makes one call at the start of each phase. It receives the
same initial view and the same total generated-token ceiling as all possible
recurrent calls in that phase. It emits a static tape before seeing any
within-phase outcome. It has the same maximum eight reads and four actions,
and the same world semantics. This is the equal-generated-budget recurrence-
off comparator.

The comparison equalizes **available generated thought tokens**, memory/read
budget, and action budget. It deliberately does not pretend to equalize input
tokens or model-call overhead: recurrent execution rereads state. Actual
input/output tokens, calls, bytes, latency, and GPU work are reported. A
recurrence-necessity claim is allowed only if `AUTH_RECURRENT` beats both
controls under the prospective gate in section 9. Failure removes recurrence
language but does not automatically invalidate supplied-memory use.

## 6. Exact condition roster

All counterfactual conditions start from the same immutable public checkpoint
for their root and receive the same goal order, action/read budgets, model,
decoding, renderer, and output parser. Condition and intervention names never
enter model-visible bytes.

### 6.1 Matched carrier interventions

1. `AUTH_RECURRENT`: authentic atoms and connected links.
2. `ATOMS_RECURRENT`: identical atoms, all link slots typed null.
3. `TRUTHFUL_NULL_RECURRENT`: identical exposure with explicit truthful-null
   links.
4. `DERANGED_RECURRENT`: degree-, schema-, byte-, token-, and slot-matched
   noncomposable links.
5. `BRIDGE_CUT_RECURRENT`: authentic carrier with all links incident to the
   necessary bridge masked.
6. `TWIN_REDIRECT_RECURRENT`: only the registered terminal binding is swapped;
   a content-dependent policy must switch its decisive action.
7. `UNCERTAINTY_SHAM_RECURRENT`: truthful nuisance uncertainty replaces target
   uncertainty under an otherwise authentic carrier.
8. `REACHOUT_OFF_RECURRENT`: identical carrier, but link READ dispatch returns
   the normal fixed-size `BLOCKED` envelope.
9. `OLD_CUT_RECURRENT`: at delayed evaluation, old link slots are masked.
10. `NEW_CUT_RECURRENT`: at delayed evaluation, the new link slot is masked
    while its atom remains.
11. `NO_PERSIST_NEW_RECURRENT`: the acquisition event occurs but no new atom or
    link survives delayed reset.

These are the only cells used to identify connected-content causality. Any
unmatched byte/token exposure discovered before DEV must be repaired for all
conditions, not statistically adjusted.

### 6.2 Shortcut and answer-prior controls

12. `NO_MEMORY_RECURRENT`: current public state, goal, action catalog, ordinary
    outcomes, and recurrence remain; the reader always returns `BLOCKED` and
    no old ledger or carrier is supplied.
13. `TARGET_ONLY_ANSWER_PRIOR_TAPE`: one phase-level tape receives only the released goal,
    phase, fixed action catalog, and budgets in the same outer record. It sees
    no current-state history, events, memory, scratch, reader return, or later
    feedback.
14. `PASSIVE_SIGNATURE_RECURRENT`: the complete view and fixed-size memory
    envelope are present but contain condition-independent null payloads.

The two twin bits occur together for every presentation root, so target-only
commit priors are exactly balanced. A target-only or no-memory response never
becomes a retrieval agenda for another arm.

### 6.3 Honest bypass and ceiling baselines

15. `RAW_CONTEXT_RECURRENT`: the complete chronological public old event
    ledger is inserted as a fixed `static_context` array at each phase start;
    after acquisition, admitted public new events are appended. It contains no
    synthesized link. It persists across delayed reset as this baseline's
    declared external memory.
16. `RAG_RAW_RECURRENT`: documents are the same primitive public event rows.
    The query is constructed deterministically from the current public state,
    released goal start/target, and last public event aliases. Tokenization for
    retrieval is lowercase ASCII `[a-z0-9]+`; BM25 uses `k1=1.2`, `b=0.75`,
    document-frequency over the root-local corpus, top four, and semantic-ID
    tie order. The returned four fixed-size document slots replace the common
    memory envelope. No model-generated free-text query is allowed.
17. `NATIVE_GRAPH_RECURRENT`: the complete authentic atom/link adjacency list
    is inserted as static context before a goal; there is no reader. It is a
    labeled explicit-graph ceiling, not an equal-resource competitor.

All three are honest because they receive only the same ordinary public
evidence available to the supplied carrier, never checker truth. Their storage,
rendered bytes, tokens, index work, and calls are not matched and must be
reported. M-TEXT may claim a practical connected-memory advantage only if the
registered condition beats the strongest of these applicable textual
baselines; otherwise they remain successful alternative mechanisms.

### 6.4 Recurrence cells

18. `AUTH_SCRATCH_OFF`.
19. `AUTH_ONE_SHOT_TAPE`.

No condition outside this nineteen-cell roster may affect DEV selection or
confirmation claims. A later LoRA, adapter-off, wrong-life, capacity, or
training cell belongs to M-LORA and is forbidden here.

## 7. Anti-shortcut and bypass invariants

The following are pre-model conformance gates:

1. **Fully rendered twin prefix.** For identical command histories before a
   separating ordinary outcome, system bytes, user bytes, chat-template
   bytes, token IDs, action catalogs, tool returns, scratch initialization,
   and request settings are byte-identical across `h=0/1` twins.
2. **Target-only balance.** Across every split, each released goal, experiment
   alias, terminal action alias, presentation position, and answer bit has
   exact or difference-at-most-one balance. The pure target-only Bayes ceiling
   for `h` is exactly `1/2`.
3. **No answer-bearing row.** A static scan and exhaustive semantic oracle
   prove that no single visible memory row contains a complete registered
   path, goal answer, commit bit, preferred experiment, or future target.
4. **All-path equivalence.** The scorer accepts both registered minimum paths;
   it never demands the producer's or reference script's chosen path.
5. **All-path masking.** Dependence masking removes the union of the atoms and
   links in every successful equivalence class, not only the realized path.
6. **Binding twin.** With pre-read public bytes fixed, `TWIN_REDIRECT` changes
   the registered decisive action. An unchanged response is a shortcut.
7. **Matched corruption.** `DERANGED` matches atoms, degrees, slot count,
   schema, UTF-8 length, token length, retrieval exposure, action/read budget,
   and answer marginals.
8. **Query noninterference.** The common reader is mutated over goal, hidden
   bit, arm, score, oracle, split, filename, runtime, timing, catalog order,
   and padding. Every such mutation must either leave returns identical or
   fail closed before rendering.
9. **Join denial.** Injection of branch scratch, commands, retrieval traces,
   dependencies, correctness, failures, ordering, timing, or sibling handles
   into `GOALS_COMPLETE` must fail its closed schema.
10. **Reset denial.** Each prohibited reset survivor is injected separately;
    every mutation must be detected before delayed evaluation.
11. **Scorer noncausality.** Removing or corrupting scorer/oracle files cannot
    change any model input or action; it can only prevent a private receipt.
12. **Condition/order denial.** Changing the private condition dispatch order
    cannot change prompt bytes for a fixed semantic state. The preflight
    forward/reverse run must produce identical decoded output.

Failure of any invariant invalidates the instrument. It is not a negative
model result.

## 8. Separable endpoints

All endpoint fields are binary at one `(root, condition)` cell. None may
substitute for another. A composite is used only as an AND gate, never as an
averaged headline score.

### 8.1 Memory access and recall diagnostics

- `relevant_atom_returned`: at least one returned atom lies on a registered
  path for the released goal.
- `relevant_link_returned`: at least one returned authentic link lies on such
  a path.
- `public_id_reused`: a later command cites a returned public ID.

These diagnose the read path. They are not composition or task success.

### 8.2 Planning and execution

- `plan_valid`: in the last accepted response before the first relation ACT,
  `plan` equals the complete remaining action sequence of either registered
  minimum path from the current state to the released target.
- `first_action_correct`: the first relation ACT is the first edge of at least
  one registered minimum path.
- `plan_execution_consistent`: the executed successful action sequence is a
  prefix of the declared plan and reaches its target without `NO_EFFECT`.
- `answer_success`: terminal public state equals the released target and
  `FINISH` is issued there.
- `constructive_path`: every executed edge cites its corresponding returned
  atom and every adjacent pair cites an authentic returned link; dependency
  edges precede the command and form a valid acyclic public trace.

### 8.3 Changed-goal traversal

For one root, `two_goal_traversal=1` only if both isolated A and B probes have
`answer_success=constructive_path=1`, the two action sequences end through
their goal-specific terminal relations, and no branch-local object crosses
the join. Goal A and B are repeated measures inside the root.

### 8.4 Information and revision

- `separating_choice=1` iff the chosen experiment is in the registered
  target-separating set `{E0,E1}` after public alias inversion.
- `realized_information=1` iff the observed outcome leaves a singleton
  posterior over hidden target bit `h`.
- `belief_revision=1` iff the last pre-outcome structured belief is
  `UNKNOWN`, the first accepted post-outcome belief equals `h`, and the later
  commit uses that same value.
- `acquisition_success=1` iff a correct `COMMIT_h` emits the new ordinary atom.

Choosing an experiment, seeing information, revising a belief, and acquiring
the new atom remain separate.

### 8.5 Delayed old-plus-new use and retention

- `old_used=1` iff the delayed constructive trace cites at least one admitted
  old atom and one old authentic link.
- `new_used=1` iff it cites the newly admitted atom and new authentic link.
- `delayed_answer=1` iff it reaches and finishes at D after sterile reset.
- `delayed_integration=1` iff `old_used=new_used=delayed_answer=
  constructive_path=1`.
- `retention=1` iff both old path probes passed before acquisition and old
  evidence is still used in the delayed trace.

`OLD_CUT`, `NEW_CUT`, and `NO_PERSIST_NEW` must each independently destroy
`delayed_integration`; one cannot compensate for another.

### 8.6 Trace dependence

`trace_dependence=1` only if all-path masking invalidates or changes the
policy's registered constructive trace **and** the `TWIN_REDIRECT` carrier
changes the decisive goal-specific action to its registered twin-correct
action. Citations without these behavioral counterfactuals are decorative.

## 9. Root universe, splits, arithmetic, and confirmation

### 9.1 Registered universe and split

The universe remains all 64 algebraic roots `(k,h)`, `k=0..31`, `h in
{0,1}`. No root is generated, accepted, rejected, or selected using model
performance.

```text
DEV:          k=0..7,   both h values (16 roots)
CONFIRMATION: k=8..23,  both h values (32 roots)
RESERVE:      k=24..31, both h values (16 roots)
```

Every condition runs on every root assigned to its required phases. The two
twins for one `k` are always evaluated together. Carrier cells, goals, paths,
phases, calls, turns, reruns, and the 32 alias/order values are repeated
finite-suite cells, not independent scientific units. The whole confirmation
suite is one conditional fixed-model assay. The reserve is not a rescue set;
opening it requires a new bound replication decision.

The fixed topology means there is no topology-generalization claim. The
target-only, binding, mask, and carrier interventions identify content use
inside this topology. A future multi-topology benchmark is required before
claiming general memory generalization.

### 9.2 Reduction

For binary endpoint `e`, first form the twin-robust presentation-block value:

```text
b_e(k,c) = min(e(k,0,c), e(k,1,c))
```

The confirmation rate is the exact census:

```text
R_e(c) = sum_{k=8}^{23} b_e(k,c) / 16
```

The paired condition contrast is:

```text
D_e(c1,c0) = sum_{k=8}^{23}[b_e(k,c1)-b_e(k,c0)] / 16
```

No cell is dropped. Policy parse failure, timeout, invalid ID, abstention, bad
plan, wrong action, miss, or exhausted budget contributes zero to unfinished
endpoints. A malformed root, missing manifest member, controller/internal
error, or runtime mismatch invalidates the whole confirmation rather than
becoming a behavioral zero.

Because this is a deterministic census of one designed topology and one fixed
model, the uncertainty method is **none**: report exact numerators,
denominators, and paired differences; do not attach binomial, bootstrap, or
t-test intervals and do not call `16` an independent sample size. There is no
multiplicity correction because no null-hypothesis tests are performed. The
noncompensatory gates below are prospective software/scientific disposition
rules.

### 9.3 DEV gate

DEV may be inspected and may change the protocol only before confirmation
freeze. To proceed, all M0 and rendered-boundary invariants must pass, the CPU
reference controller must score one on every positive field, and the model
must satisfy:

```text
R_two_goal_traversal(AUTH_RECURRENT) >= 6/8
R_delayed_integration(AUTH_RECURRENT) >= 6/8
R_two_goal_traversal(NO_MEMORY_RECURRENT) <= 4/8
R_delayed_integration(NO_MEMORY_RECURRENT) <= 4/8
```

Failure means insufficient model headroom or benchmark necessity. Repairing
prompt, parser, budgets, or semantics consumes DEV and requires a new frozen
source/manifest before confirmation. DEV results are never paper evidence.

### 9.4 Confirmation gates

The bounded supplied-connected-memory claim requires every item below:

1. **Traversal absolute:** `R_two_goal_traversal(AUTH_RECURRENT) >= 12/16`.
2. **Traversal specificity:** AUTH exceeds each of `ATOMS`, `DERANGED`, and
   `BRIDGE_CUT` by at least `4/16` on two-goal traversal.
3. **Constructive dependence:** `R_trace_dependence(AUTH_RECURRENT) >= 12/16`
   and twin-invariant shortcut rate is at most `4/16`.
4. **Information:** AUTH has separating choice, realized information, belief
   revision, and acquisition success each at least `12/16`.
5. **Sham:** `UNCERTAINTY_SHAM` has target realized information, target belief
   revision, acquisition, and delayed integration each at most `4/16`, and
   AUTH exceeds it by at least `8/16` on acquisition.
6. **Delayed integration:** AUTH delayed integration is at least `12/16`;
   each of `OLD_CUT`, `NEW_CUT`, and `NO_PERSIST_NEW` is at most `4/16`; AUTH
   exceeds each by at least `8/16`.
7. **Shortcut bound:** `NO_MEMORY_RECURRENT`,
   `TARGET_ONLY_ANSWER_PRIOR_TAPE`, and
   `PASSIVE_SIGNATURE_RECURRENT` each have traversal and delayed integration
   at most `5/16`.
8. **No adverse task effect:** for `answer_success`, `plan_valid`, and
   retention, AUTH minus ATOMS is not below `-0.05`. With sixteen blocks, one
   net lost block is `-1/16=-0.0625` and therefore breaches this bound.

These conditions are an AND. There is no averaging across them.

The stronger **practical advantage over honest unstructured text memory** is
separate. It requires AUTH to exceed the root-wise strongest of `RAW_CONTEXT`
and `RAG_RAW` by at least `1/16=0.0625` on both two-goal traversal and delayed
integration, while satisfying the adverse bound on every other primary
endpoint. `NATIVE_GRAPH` is a labeled organized-graph ceiling, not a baseline
the bounded reader is expected to beat. If AUTH does not beat raw context and
RAG, report the strongest honest baseline and make no superiority claim.

The separate **recurrence-necessity** claim requires AUTH_RECURRENT to exceed
both AUTH_SCRATCH_OFF and AUTH_ONE_SHOT_TAPE by at least `4/16` on acquisition
success and delayed integration, with no endpoint below either comparator by
more than `0.05`. It is not required for the supplied-memory claim.

### 9.5 Confirmation seal and stopping

After DEV, freeze and hash:

- all source and executable bytes;
- complete M0 and M-TEXT manifests;
- root/split/condition/phase roster and dispatch order;
- model/tokenizer/chat template/runtime;
- prompts, response schemas, parser, reader, renderer, controller, scorer,
  reducer, and analysis;
- every resource ceiling and failure disposition; and
- an empty expected-receipt registry for all confirmation cells.

An independent implementation review and a separate author-side scientific
advocate review must both bind those hashes. Then a new exact human approval
must authorize model/tokenizer execution and GPU resources. Confirmation runs
all registered cells. There is no efficacy-based early stop, condition drop,
root omission, threshold change, or partial claim. The reducer refuses to
emit a confirmation aggregate until every expected receipt is terminal.

Raw per-call receipts may be written during execution, but confirmation
summaries and condition comparisons remain mechanically masked until the
registry is complete. A hard safety/resource halt produces `INCOMPLETE` and
no claim. Confirmation failure consumes the split. Reserve use or any protocol
change requires a newly deliberated and ratified replication; reserve cannot
overwrite the failed result.

### 9.6 Exact phase/call roster

For each executed root, the maximum recurrent calls are 13 for probe A, 13
for probe B, four for uncertainty/acquisition, and 13 for delayed evaluation,
for 43 total. The nineteen conditions execute these phases only:

| Conditions | Count | Calls per root each |
|---|---:|---:|
| AUTH, ATOMS, TRUTHFUL_NULL, DERANGED, NO_MEMORY, PASSIVE_SIGNATURE, RAW_CONTEXT, RAG_RAW, NATIVE_GRAPH, AUTH_SCRATCH_OFF | 10 | 43 |
| BRIDGE_CUT, TWIN_REDIRECT | 2 | 26 |
| UNCERTAINTY_SHAM | 1 | 17 |
| REACHOUT_OFF | 1 | 39 |
| OLD_CUT, NEW_CUT | 2 | 13 |
| NO_PERSIST_NEW | 1 | 17 |
| TARGET_ONLY_ANSWER_PRIOR_TAPE, AUTH_ONE_SHOT_TAPE | 2 | 4 |

Thus the scientific roster is exactly 589 model requests and 170,752 allowed
generated tokens per root. DEV plus confirmation contains 48 roots, hence
28,272 scientific requests and 8,196,096 allowed generated tokens. The
determinism preflight adds exactly 24 sentinel requests: four prompts, three
fresh-state repetitions in forward order, then three in reverse order. It adds
6,144 allowed generated tokens. Reserve roots are excluded from these totals.

## 10. Complete resource-factor ledger

The primary causal contrasts (`AUTH` versus matched carrier interventions)
must match every item in the exposure vector:

```text
atom slots; link slots; record bytes; rendered tokens; reader calls;
reader-return slots; read budget; action budget; per-turn output ceiling;
phase-turn ceiling; prompt schema; model; decoding; and session boundary
```

Every condition and baseline separately reports:

- stored raw-event, atom, link, index, and static-context UTF-8 bytes;
- corresponding tokenizer token counts;
- index-build CPU seconds and peak RSS;
- graph/materializer/checker CPU seconds and peak RSS;
- model calls attempted/completed/failed;
- input tokens, generated tokens allowed, generated tokens actually used;
- reader calls, documents/records returned, and returned bytes/tokens;
- successful, unsuccessful, and total world actions;
- controller/tool operations;
- GPU-seconds and A40-equivalent GPU-hours;
- wall-clock seconds;
- peak host RAM and device memory;
- stored artifact bytes; and
- external/provider cost, fixed at USD 0.00 for this local proposal.

This assay claims equal generated-token opportunity, read/action opportunity,
and exact carrier exposure only where stated. It does not claim equal total
compute across raw context, RAG, native graph, organized reader, and recurrent
versus one-shot execution.

Prospective hard ceilings for DEV plus confirmation are:

```text
8 A40-class GPUs concurrently
192 A40-equivalent GPU-hours total
48 hours wall time from first DEV model call through confirmation seal
28296 model requests
231800832 total input tokens
8202240 total allowed generated tokens
500 GiB stored artifacts
USD 0.00 external/provider spend
```

The preflight may lower these ceilings after exact roster arithmetic and a
first-call timing measurement; it may never raise them without new human
approval. Hitting a ceiling yields `INCOMPLETE`, never pruning.

## 11. Durable artifacts and receipts

Canonical future paths are:

```text
research_loop/changes/<successor_change_id>/frozen/spec/
research_loop/changes/<successor_change_id>/frozen/m0/
research_loop/changes/<successor_change_id>/frozen/mtext/
research_loop/changes/<successor_change_id>/frozen/goldens/
research_loop/changes/<successor_change_id>/receipts/preflight/
research_loop/changes/<successor_change_id>/receipts/dev/
research_loop/changes/<successor_change_id>/receipts/confirmation/
```

Every artifact is written to a same-filesystem temporary file, flushed,
`fsync`ed, reopened and hash-verified, then atomically renamed to its
content-addressed final name. Parent directories are `fsync`ed after rename.
Existing final paths are never overwritten; identical content is accepted
only after hash verification. A mismatched duplicate is fatal.

Each call receipt records pre-state hash, exact message/render/token hashes,
model/runtime identity, request-emitted marker, decoded-token and byte hashes,
parse result, command, post-state hash, resource counters, and terminal status.
It never stores hidden truth inside a model-visible object. Each root receipt
hashes its ordered call receipts and all condition endpoint fields. The split
receipt hashes the exact expected roster and all root receipts.

On restart, the runner trusts only atomically sealed receipts whose schemas,
hashes, source/runtime identities, and parent manifests verify. A temporary or
partial file is quarantined. A call marked emitted but lacking a sealed
response becomes terminal ambiguous failure and is not repeated. Output files
have fixed maximum sizes; exceeding one is fatal. Failure precedence is:

```text
MANIFEST/RUNTIME/SCHEMA/PRIVATE-LEAK/INTERNAL
  > REQUEST-AMBIGUOUS/TIMEOUT/OUTPUT-OVERFLOW/PARSE
  > POLICY ABSTAIN/BUDGET/NO_EFFECT/MISS
  > OK
```

The first category invalidates the assay; the second and third are zero-valued
behavioral outcomes once a request was emitted.

## 12. Correct gate order

The successor must use this order:

1. **Source specification review**: exact semantics, model-facing protocol,
   endpoints, roster, arithmetic, and prohibitions; no execution.
2. **Byte materialization proposal**: real M0/root/golden/source/runtime
   identities and two checker sources are present; no benchmark execution.
3. **Human implementation ratification**: exact allowed files and CPU tests.
4. **Scoped M0 implementation and CPU conformance**.
5. **Fresh independent implementation review plus separate scientific
   advocate**, bound to implemented bytes.
6. **Exact M-TEXT DEV execution authorization**: model/tokenizer/GPU limits
   only; no confirmation claim.
7. **DEV execution and gate**.
8. **Post-DEV freeze, independent review, and exact confirmation approval**.
9. **Confirmation execution**.
10. **Fresh evidence-to-claim review** before any claim, release, or M-LORA
    premise.

CPU conformance is therefore post-implementation and pre-model. M-TEXT causal
evidence is post-model-execution and pre-claim. No approval is inferred across
these stages.

## 13. Mandatory negative dispositions

- **Any M0, renderer, prefix, query, reset, provenance, parser, session,
  durability, or oracle-isolation failure:** instrument invalid; no model
  interpretation and no M-LORA dispatch.
- **DEV AUTH below headroom:** stop; the fixed 7B model cannot use this
  interface at required reliability, or the interface is not usable. Repair
  only in a newly frozen DEV sibling.
- **No-memory/target-only above shortcut bound:** benchmark not specific;
  narrow/redesign before confirmation.
- **AUTH passes tasks but matched link interventions do not reduce behavior:**
  supplied text may be useful, but connected structure is not identified;
  withdraw “connected” and block connected-memory premise for M-LORA.
- **AUTH changes behavior but lowers a primary endpoint by more than 0.05:**
  report causal but harmful memory; no benefit or advancement claim.
- **DERANGED performs like AUTH:** organization-specific interpretation fails;
  report atoms/format/use only.
- **TWIN or all-path masking fails:** citations are decorative or shortcut;
  no constructive-use claim.
- **Sham selects non-target information yet acquisition/delayed behavior does
  not fall:** informative-experiment mechanism fails.
- **`OLD_CUT`, `NEW_CUT`, or `NO_PERSIST_NEW` does not destroy delayed
  integration:** old-plus-new or sole-channel interpretation fails.
- **AUTH does not beat raw context/RAG/native graph:** retain the narrow causal
  supplied-memory result if its own gates pass; make no baseline-superiority,
  efficiency, compression, or saturation claim.
- **Scratch-off or one-shot matches AUTH:** remove the corresponding recurrence
  claim; do not treat this as failure of supplied connected text.
- **Confirmation misses any noncompensatory gate after DEV passage:** publish
  or record the null/negative, consume confirmation, and do not tune on it.
- **Confirmation incomplete or resource ceiling hit:** no scientific result;
  preserve receipts and seek a new exact completion decision without replacing
  completed/ambiguous cells.
- **M-TEXT passes:** it becomes only a same-semantics feasibility premise for
  later E0/G/M-LORA deliberation. It does not authorize those packages.

## 14. New acceptance-test registry required in a successor

The successor should retain repaired versions of the prior tests and add:

```text
M0-EXACT-BYTES-RATIFIABILITY
M0-INDEPENDENT-ORACLE-MUTATION
M0-ZERO-V7-DEPENDENCY
M0-ACTION-CATALOG-NONORACLE
M0-PLAN-BEFORE-ACTION-READ-CUT
M0-QUERY-AGENDA-LAUNDERING
M0-JOIN-ABANDONED-BRANCH
M0-PROVENANCE-DIAMOND-CYCLE
M0-REPEAT-POLICY-VISIBILITY
MTEXT-RENDERED-NONINTERFERENCE
MTEXT-PROMPT-SCHEMA-ROUNDTRIP
MTEXT-SESSION-CACHE-RETRY-STERILITY
MTEXT-RESET-SOLE-CHANNEL
MTEXT-PARENT-PATH-ANSWER-LAUNDERING
MTEXT-MATCHED-CONNECTIVITY-CORRUPTION
MTEXT-RECURRENCE-SCRATCH-ABLATION
MTEXT-RECURRENCE-EQUAL-BUDGET-TAPE
MTEXT-ENDPOINT-SEPARATION
MTEXT-TARGET-ONLY-ANSWER-PRIOR
MTEXT-RESOURCE-FACTORIAL
MTEXT-DEV-CONFIRMATION-DAG
MTEXT-NEGATIVE-DISPOSITION
```

The future online-learning chain remains a different test/package and must
not be smuggled into this registry.

## 15. Remaining irreducible human choices

Almost all math and protocol choices above are now proposed rather than sent
back to Rohin. Four choices remain genuinely human because they change the
scientific ambition, authority, or resource commitment:

1. **Fast conditional gate or broader benchmark.** Ratify the current one-
   topology, 64-root finite-census M-TEXT as a narrow mechanism prerequisite,
   or delay it to add multiple semantic topologies and earn a generalization
   claim. Recommendation: use this fast conditional gate now; require multiple
   topologies in the later PCFL-Stream confirmation.
2. **Primary fixed model.** Ratify the proposed unmodified Qwen2.5-7B-Instruct
   revision so M-TEXT is directly comparable to later 7B LoRA transport, or
   choose a stronger fixed ceiling model. Recommendation: 7B primary; any 32B
   result is separately labeled and cannot replace it.
3. **Exact execution/resource authority.** After source, materialization,
   implementation, CPU review, and DEV freeze, Rohin must separately approve
   the real model/tokenizer/GPU manifests and hard ceilings. General permission
   to use GPUs is not this exact scientific approval.
4. **Claim ceiling and negative-result commitment.** Ratify that even a full
   pass supports supplied-connected-text causal use only, and that failed
   confirmation is retained rather than repaired on reserve roots.

Everything else—root arithmetic, control roster, recurrence comparators,
endpoint separation, failure handling, and the `-0.05` adverse bound—can be
reviewed and attacked by the next fresh deliberation without requiring Rohin
to do the math.
