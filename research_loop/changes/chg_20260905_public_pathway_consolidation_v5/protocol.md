# PPC5 — standalone mechanism-core protocol

Status: proposal only. This file and the PPC5 `change.json` are the complete
normative architecture. PPC1–PPC4, Fable organisms, earlier notes, reviews, and
runs are evidence/provenance only; none supplies an inherited field, default,
permission, test, or claim. Later long-life, schema-compression, CompilerGym,
parenting, and population studies remain required program stages, but this
proposal authorizes and specifies only the mechanism core needed to earn them.

## 1. Scientific question and staged estimands

Can an otherwise fixed recurrent agent use SLEEP to consolidate its own public
action–outcome experience into an isolated READ-LoRA such that later cognition:

1. reads supported local experiential records;
2. adaptively traverses a prospectively decisive multi-record path;
3. improves a later action beyond strong endpoint, text, graph, RAG, context,
   reflection, direct-action, and batch-posttraining baselines;
4. benefits causally from DREAM reconciliation of a crowded working context;
   and
5. benefits causally when DREAM-selected public roots, rather than a matched
   mechanical selection, determine what SLEEP writes?

PPC5 has four ordered assays:

```text
D1A ABSORPTION: fixed corpus; can each substrate return the right local record?
D1B PATH USE: does recurrent adaptive traversal of local records cause action?
D1C DREAM CONTEXT: does publishing same-model reconciliation preserve useful
                   conscious state and improve later work at equal compute?
D1D DREAM→SLEEP: does authentic DREAM root selection improve the supported rows
                 written by SLEEP and the resulting later action?
```

PPC5 deliberately freezes THINK/ACT and excludes DECIDE, ACT, and DREAM targets
from LoRA training. Otherwise direct policy imitation can masquerade as acquired
experience or connected path use. The immediate successor tests learned public
cognition by training DECIDE rows while withholding final ACT targets. Passing
D1 is necessary but insufficient for learned thinking, continual lifetime
learning, learned lossy schemas, baseline saturation, or parenting. Those remain
required prospective successors. This is causal staging, not a reduced program
objective.

## 2. One model, three verbs, one learned life state

* THINK: one recurrent public operation over current world state, public
  workspace, typed memory returns, same-item outcomes, and logical budgets.
* DREAM: the same frozen model used by THINK selects and reconciles causally
  available working state. DREAM is provisional, reversible, and non-evidence.
* SLEEP: an offline model-assisted renderer plus a mechanical public-evidence
  gate. SLEEP alone trains/publishes the per-life LoRA.

There is no separately trained thinker, dreamer, planner, verifier, scorer, or
sleep policy. Raw experience remains in an append-only ledger. Removing content
from active context never deletes its ledger event. The only learned per-life
artifact is the LoRA; external text/graph stores are comparison treatments. D1
routes that LoRA through an isolated READ provider and never mounts it inside
THINK/DREAM/ACT. This is an identification intervention, not a claim that the
eventual deployed organism requires two models or two learned life states.

## 3. Private item roles and visibility

Before any model input exists, the harness assigns one private immutable role:

```text
ACQUIRE   public within-item outcomes; closed roots may become SLEEP candidates
PROBE     public within-item outcomes; complete item is writer-ineligible forever
STATIC    no model; construction/sealing only
```

The model-visible role string is always `WORK_ITEM`; acquisition and probe
prompt schemas, budgets, logical clocks, filenames, errors, IDs, and output
interfaces are byte-identical. The private role never reaches THINK, DREAM,
retrieval, training targets, or condition prompts. No role transition exists.

Only closed ACQUIRE events can enter a later source THINK/DREAM or SLEEP. PROBE
events and scores remain quarantined until audit and cannot modify any later
item, writer, threshold, or treatment. Same-item public action results may recur
within that item. Confirmatory effects are computed only on PROBE items.

The complete formal visibility product appears in `change.json`. Prompt builders
are allowlist-only. Counterfactual fixtures independently mutate every forbidden
class and require byte- and selection-identical outputs at the boundary.

## 4. Canonical bytes and private provenance

All public structures use canonical JSON: UTF-8, sorted keys, compact separators,
declared array order, and exactly one trailing LF. Every event records prestate,
input, output, parser, model, tokenizer, adapter, and next-state hashes.

Harness IDs match `^(it|br|sg|hy|ev|rec)-[0-9]{8}$`, allocate monotonically
after legal commit, contain no model substring, and remap freshly per probe.

The sealer creates `root_partition.v1`, an opaque equivalence partition used
only by SLEEP for dedup/root-union and by audit for splits/support. It contains
no answers, truth labels, scores, conditions, or target membership. THINK and
DREAM never see it. SLEEP can compare/union opaque hashes but cannot read
generator semantics. Mutating hidden generator labels while holding public
events and partition fixed must preserve all writer bytes and choices.

## 5. Exact THINK operation machine

Each call receives, in order:

```text
fixed birth/interface prompt
public goal and current environment state
logical clock and remaining call/read/action/dream/token budgets
active branch, ordered open subgoals, hypothesis events and statuses
opened record IDs, live prediction, unresolved surprises
immediately prior same-item public transition
complete repeat table and two latest normalized public error codes
```

It emits exactly one canonical object:

```json
{"contract":"ppc5.op.v1","op":"ENUM","args":{}}
```

Operations and exact arguments:

```text
OPEN_SUBGOAL  {parent_id}
QUERY         {query_type, subject_id, relation_id}
FOLLOW        {record_id}
HYPOTHESIZE   {record_ids, relation_template_id, predicted_outcome_id}
PREDICT       {direction, value_bin, action_id}
ACT           {action_id}
REVISE        {hypothesis_id, record_ids, predicted_outcome_id}
BACKTRACK     {}
REQUEST_DREAM {reason, record_ids}
DEFER         {reason}
STOP          {reason}
```

Additional/missing fields, unknown enums, unallocated IDs, closed-branch
references, and wrong types fail parse. One call produces at most one op. ACT
requires a live prediction bound to the same action and open ancestry.

Hypotheses are append-only events. Legal status events are:

```text
HYPOTHESIZE: absent -> PROVISIONAL
public supporting observation: PROVISIONAL -> ACTIVE
public contradiction: PROVISIONAL|ACTIVE -> CONTRADICTED
REVISE: PROVISIONAL|ACTIVE|CONTRADICTED -> SUPERSEDED plus new PROVISIONAL child
BACKTRACK/STOP: open PROVISIONAL|ACTIVE -> CLOSED without changing evidence
```

No in-place mutation, resurrection, or status downgrade exists. A branch is an
ordered tree. BACKTRACK closes its descendants then activates the most recently
opened still-open sibling, else parent, else STOP. Valid diamonds in citation
DAGs are accepted; directed cycles fail.

An operation fingerprint is SHA-256 of canonical `(prestate_hash, op, args)`.
Three equal fingerprints from unchanged state force DEFER(REPEAT_LIMIT). The
repeat table is model-visible. Every dispatched call consumes one call; QUERY
also consumes one read; ACT, including invalid action, consumes one action;
REQUEST_DREAM consumes one dream. Parse/illegal results are normalized and
consume the call; the third forces DEFER. No invisible retry exists. Provider
failure after dispatch yields MISSING_NO_RETRY; pre-dispatch integrity failure
yields INVALID_CELL.

## 6. Exact READ provider envelope

D1A uses one private candidate table for every provider. Each row is
`(candidate_id, subject_id, relation_id, object_id, public_record_bytes,
opaque_root_union_hash)`. Order is manifest-seeded and fixed. Each provider
examines exactly all `N` entries per query; candidate strings, tokenizer, work
count, and failure normalization match. The table contains no condition or
target label.

Request:

```json
{"contract":"ppc5.read.v1","query_type":"RELATION","subject_id":"ev-00000000","relation_id":"public_relation_id","candidate_table_hash":"64hex","candidate_count":64,"max_returns":1}
```

Conditional response schema:

```json
{"contract":"ppc5.read.v1","status":"FOUND|NOT_FOUND","record_id":"rec-00000000|null","subject_id":"ev-00000000|null","relation_id":"public_relation_id|null","object_id":"ev-00000000|null","root_union_hash":"64hex|null"}
```

Interface bytes are identical conditional on the provider's selected semantic
record; realized answers need not be equal. Rank, score, provider, condition,
latency, and index internals never appear. TEXT and GRAPH scan the same table.
READER_LORA forced-scores the same candidate object strings in an isolated
reader process; its adapter is never mounted during THINK/DREAM/ACT.

D1A and D1B use one byte-identical, unmodified, frozen base THINK/ACT policy in
every memory-substrate condition. No policy adapter is mounted. Direct-action
and trajectory LoRAs appear only as strong comparator conditions and cannot
support a reader-transport or connected-path claim.

## 7. DREAM as learned, reversible context management

REQUEST_DREAM can reference only visible records/hypotheses/surprises on the
active open branch. DREAM receives those records, full public ancestor closure,
and then most recent causal public events until the fixed allowance is full.
Mandatory closure never truncates; overflow consumes the call/dream and
publishes nothing.

The same model emits exactly one:

```json
{"contract":"ppc5.dream.v1","status":"PUBLISH","retain_record_ids":[],"retain_hypothesis_ids":[],"retain_subgoal_ids":[],"resolved_surprise_ids":[],"next_focus_relation_id":"public_relation_id"}
```

or `{"contract":"ppc5.dream.v1","status":"ABSTAIN"}`. DREAM cannot add new
semantic claims, actions, queries, records, evidence, support, or final answers.
PUBLISH appends a `DREAM_STATE` event and replaces only the active working-set
view; all source events remain recallable in the ledger. Resolved-surprise is a
workspace status, not an evidentiary status. Later contradiction appends a new
event; history is never rewritten.

D1C randomizes eligible context-pressure points within paired items:

* PUBLISH: generate and install the authentic DREAM_STATE.
* WITHHOLD: generate the identical dream call but discard its output; install a
  deterministic recency working set with the same record-count/token envelope.
* MISMATCH: install a cross-fitted DREAM_STATE from a paired unrelated item,
  matched in schema, counts, tokens, and pressure, with IDs remapped.

All arms pay the same call/dream/token budgets. Outcomes are: exact retention of
presealed decision-relevant state; calls/tokens/actions to next valid progress;
later action value; recovery after an injected contradiction; and unsupported
state use. DREAM value requires PUBLISH to beat both controls and lose its gain
when each retained decisive item is removed leave-one-out.

D1D clones the same closed acquisition lineage before SLEEP and charges every
branch the identical DREAM call, input, output, and token budget:

* DREAM_TO_SLEEP: the writer receives authentic DREAM-selected root IDs.
* PUBLISH_CUT: authentic DREAM output is quarantined; the writer receives a
  deterministic age/type/token/support-matched selection of eligible roots.
* PUBLISH_MISMATCH: the writer receives a presealed derangement of selected
  roots from a paired unrelated lineage, matched in count/type/token/support.

The evidence gate then regenerates READ rows from public roots in every branch;
DREAM bytes never become targets. D1D estimates whether model reconciliation
selects more useful experience to write, rather than whether an extra inference
call or extra context helps. Successful DREAM decisions may become typed DREAM
targets only in a later separately ratified learning study. Free-form dream
prose never trains.

## 8. SLEEP admission and row families

SLEEP operates only after an exact acquisition boundary over closed ACQUIRE
events. The current frozen model may propose restatements/groupings, but model
confidence and proposal bytes never create support. In PPC5 D1 the deterministic
writer admits only READ rows: directly witnessed local relation atoms with
public outcomes. DECIDE, ACT, and DREAM targets are forbidden in the PPC5
reader corpus.

Free-form hypotheses, rationales, agendas, summaries, imagined outcomes, scorer
labels, probe roots, future suffixes, target bytes, and abandoned/contradicted/
superseded branch targets are never loss-bearing. Retroactive admission rechecks
final branch/hypothesis status at the sleep boundary; a descendant cannot support
an ancestor. Root unions deduplicate restatements and repeated exposures.

Rows exactly match the runtime ppc5 READ interface and apply loss only to
canonical output tokens. The one-cycle reader adapter trains freshly from the
clean base under a later hash-bound recipe. Validation must pass before atomic
publication and cold reader-process remount; partial/non-finite/mismatch
preserves the previous adapter and records FAILED_SLEEP.

## 9. D1B local-path instrument and whole-path intervention

Each PCFL target is sealed with one unique minimal decisive path of length 2 or
3 over directly witnessed local atoms. There is no oracle-valid alternative
within the action/read/call budget. Target handles and combinations never occur
in acquisition, writer, or training bytes. The correct later action depends on
the composed path rather than any individual record or passive signature.

Whole-path credit requires:

1. authentic trace opens and cites every presealed edge in order before ACT;
2. leave-one-edge-out is executed for every decisive edge, not one chosen edge;
3. each edge removal and its binding twin changes the registered action/value
   direction under the same public target state;
4. the full authentic treatment beats every conjunctive bypass gate.

PATH_SHUFFLE uses manifest-seeded degree-preserving double-edge swaps within
root/outcome/degree/token strata, preserves node bytes and candidate work,
rejects cycles and surviving valid paths, and fails without fallback after
1,000 deterministic candidates.

Adaptive retrieval and recurrent THINK are distinct:

* ONE_SHOT_QUERY commits every query before any return, then permits later
  recurrent thought.
* OPEN_LOOP commits the complete operation/action sequence in one initial call
  before any return/outcome; the harness executes it with no more model calls.

## 10. Conditions and dose

D1B mandatory conditions, all derived from common sealed acquisition histories:

```text
BASE_AGENT, TARGET_STATE_ONLY, NATIVE_CONTEXT_THEN_TRUNCATION, FULL_CONTEXT,
RAW_RAG, REFLECTION_LESSON_TEXT, LINKED_TEXT, EXPLICIT_GRAPH,
ENDPOINT_LORA, DIRECT_ACTION_LORA, DIRECT_QA_LORA, RAW_BATCH_LORA,
READER_LORA, READER_ROOT_SHUFFLE, ONE_SHOT_QUERY, OPEN_LOOP,
ADAPTER_OFF_CANDIDATE_ONLY, WRONG_LIFE_ADAPTER
```

For substrate attribution, TEXT/GRAPH/READER_LORA share the byte-identical frozen
base THINK/ACT policy and ppc5.read.v1 envelope. READER_LORA and trained bundled
LoRA baselines receive the same total positive target tokens, effective touches,
active parameter bytes, optimizer/update count, clean-base rebuild, and
publication lifecycle. Direct-action and endpoint comparators receive matched
positive target-token dose but remain labeled policy-learning alternatives, not
memory substrates. No unsupported or loss-masked token counts as positive
exposure. Untrained substrates are not padded with fake training.

Common inference budgets match calls, reads, actions, input/output tokens,
decoding, logical clocks, candidate scans, error policy, and cold process/cache.
Primary cross-substrate view matches exact active retained bytes: inference
payload + required metadata/index + adapter tensors at declared dtype. Secondary
view reports construction, training FLOPs/time, optimizer/checkpoint/storage,
cache/KV, latency, and environment costs. LoRA-specific superiority additionally
requires beating strongest matched LINKED_TEXT and EXPLICIT_GRAPH treatment.

## 11. Exact contrasts and status

Before model execution a later run artifact must map every condition/contrast to
metric, direction, superiority/equivalence margin, threshold, ceiling,
multiplicity family, sample unit, missingness rule, and promotion consequence.
No unlisted comparison supports a claim.

Core gates:

```text
ABSORPTION: reader fidelity/false-memory/abstention under exact, reverse,
            paraphrase, and partial cues.
PATH: READER_LORA > max endpoint/direct-action/direct-QA/raw-batch/reflection/
      base/context/RAG; READER_LORA > ROOT_SHUFFLE, ONE_SHOT_QUERY, OPEN_LOOP;
      every edge cut and binding twin removes the registered action advantage;
      adapter-off and wrong-life remove the registered LoRA effect.
DREAM_CONTEXT: PUBLISH > WITHHOLD and MISMATCH on retained decisive state and
       downstream value; every retained decisive-item cut removes the benefit.
DREAM_SLEEP: DREAM_TO_SLEEP > PUBLISH_CUT and PUBLISH_MISMATCH on admitted-root
       utility, reader fidelity, whole-path action, and later value.
SUBSTRATE: frozen-policy LoRA value must beat matched TEXT and GRAPH before a
           LoRA-specific claim.
```

Independent lives are the sampling unit. Familywise alpha is .05 with Holm
correction, simultaneous 95% intervals, and raw life values. A positive effect
requires adjusted lower bound above zero and paired standardized effect >=.35.
Power simulation must be >=.80 for that threshold or the run is a pilot. Exact
life count, pilot hash/disjointness, equivalence margins, missingness threshold,
checkpoint map, and maximum extension live in a separate later `run_lock.json`;
any byte change requires fresh review and human run ratification.

Evidence states are disjoint: CONSTRUCTION_FAIL, RUN_INVALID, MISSING,
VALID_NULL, VALID_ADVERSE, VALID_POSITIVE. Audit failure is not scientific
falsification. Null/adverse valid results persist. Redesign after opening results
requires a new change ID, untouched targets, new seals, review, and ratification.

## 12. Successor ladder preserved by PPC5

PPC5 is the transport/path/context core. Its ordered successors remain:

```text
PPC6 TEACHABILITY: train typed DECIDE rows, exclude final ACT targets, and test
  whether held-out actions improve; compare endpoint/action/trajectory LoRA and
  shuffle operation order/outcome bindings. This is the first learned-THINK test.
PPC7 STREAM: repeated sleeps with new, old, and cross-era panels at at least
  three post-native checkpoints; test retention and continuing acquisition.
PPC8 SCHEMA: pre-confirmation DREAM commitments, later independent support,
  fresh-cohort composition utility at fixed bytes, and episodic-detail controls.
PPC9 FLYWHEEL: on-policy epistemic action, repeated mediation, utility-gym
  transfer, and improvement-versus-lifetime curves.
PPC10 PARENTING: transferable learning priors, wrong-parent controls, learning
  acceleration, autonomy, asymptote, outgrowability, and population inheritance.
```

The full Experience Models hypothesis is not earned by PPC5 alone. PPC5 answers
whether the central parametric experience pathway exists cleanly enough to make
those higher rungs scientifically interpretable.

## 13. Resets, operational tests, and authority

Every independent life cold-resets base/model process, adapter, corpus,
workspace, ledger, text/graph store, candidate table/index, KV/cache, RNG streams,
IDs, environment, filenames, and output directory. Mutation fixtures must prove
no life-1 byte changes any life-2 input before later authorized execution.

No-model preflight covers bytes, schemas, state transitions, roles, provenance,
writer admission, paths, shuffles/cuts/twins, candidate work, budgets, resource
accounting, resets, and scripted metric sensitivity. Two independently authored
static sealers compare exact manifests without model/behavioral claims.

Actual runtime perturbations of cache, batching, latency, provider faults,
candidate work, timeout, process state, publication, and condition-specific
survival are a separately registered future model execution; fixtures cannot
substitute for it.

Current ratification, if granted after fresh deliberation, authorizes only PPC5
contract implementation, deterministic CPU/no-model fixtures, and two static
no-model sealers. It authorizes no model call, canary, LoRA training, GPU run,
scientific result, long-life study, schema study, CompilerGym study, parenting,
or population experiment. Those require a later exact run lock, independent
review, and human ratification.
